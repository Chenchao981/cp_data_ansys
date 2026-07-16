"""Prepare HuaHong DCP input from folders or one or more ZIP archives."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import shutil
from tempfile import TemporaryDirectory
from typing import Callable, Iterator, Sequence
from zipfile import BadZipFile, ZipFile


DATA_FILE_SUFFIXES = {".txt", ".dcp"}
ProgressCallback = Callable[[str], None]


class ZipInputError(ValueError):
    """Raised when a selected ZIP input cannot be prepared safely."""


@dataclass(frozen=True)
class PreparedDCPInput:
    """A directory shape accepted by ``clean_dcp_data.process_directory``."""

    directory: Path
    data_files: tuple[Path, ...]
    archives: tuple[Path, ...]
    is_temporary: bool


def normalize_input_paths(input_paths: str | Path | Sequence[str | Path]) -> tuple[Path, ...]:
    """Normalize a single source or a GUI multi-selection into unique paths."""

    if isinstance(input_paths, (str, Path)):
        raw_paths = [input_paths]
    else:
        raw_paths = list(input_paths)

    normalized: list[Path] = []
    seen: set[str] = set()
    for raw_path in raw_paths:
        text = str(raw_path).strip().strip('"')
        if not text:
            continue
        path = Path(text).expanduser()
        key = str(path.resolve(strict=False)).casefold()
        if key not in seen:
            seen.add(key)
            normalized.append(path)

    if not normalized:
        raise ZipInputError("未选择华虹数据文件夹或ZIP文件")

    return tuple(normalized)


def discover_zip_archives(input_paths: str | Path | Sequence[str | Path]) -> tuple[Path, ...]:
    """Return selected ZIP files, including ZIPs directly stored in folders."""

    archives: list[Path] = []
    for path in normalize_input_paths(input_paths):
        if not path.exists():
            raise ZipInputError(f"输入路径不存在: {path}")

        if path.is_file():
            if path.suffix.casefold() != ".zip":
                raise ZipInputError(f"不支持的输入文件类型（仅支持ZIP）: {path.name}")
            archives.append(path)
            continue

        if not path.is_dir():
            raise ZipInputError(f"输入路径不是文件夹或ZIP文件: {path}")

        archives.extend(
            candidate
            for candidate in path.iterdir()
            if candidate.is_file() and candidate.suffix.casefold() == ".zip"
        )

    unique_archives: list[Path] = []
    seen: set[str] = set()
    for archive in sorted(archives, key=lambda item: str(item).casefold()):
        key = str(archive.resolve()).casefold()
        if key not in seen:
            seen.add(key)
            unique_archives.append(archive)
    return tuple(unique_archives)


def discover_data_files(directory: Path) -> tuple[Path, ...]:
    """Find candidate DCP/TXT files below a directory."""

    return tuple(
        sorted(
            (
                path
                for path in directory.rglob("*")
                if path.is_file() and path.suffix.casefold() in DATA_FILE_SUFFIXES
            ),
            key=lambda item: str(item).casefold(),
        )
    )


def _member_parts(member_name: str) -> tuple[str, ...]:
    normalized_name = member_name.replace("\\", "/")
    member_path = PurePosixPath(normalized_name)
    parts = tuple(part for part in member_path.parts if part not in ("", "."))

    if (
        not parts
        or normalized_name.startswith("/")
        or re.match(r"^[A-Za-z]:", normalized_name)
        or ".." in parts
    ):
        raise ZipInputError(f"ZIP包含不安全路径: {member_name}")
    return parts


def _is_symlink(info) -> bool:
    file_type = (info.external_attr >> 16) & 0o170000
    return file_type == 0o120000


def _looks_like_hh_batch_name(name: str) -> bool:
    underscore_pos = name.find("_")
    at_pos = name.find("@", underscore_pos + 1)
    return underscore_pos > 0 and at_pos > underscore_pos + 1


def _safe_component(name: str, fallback: str) -> str:
    safe_name = re.sub(r'[<>:"/\\|?*]', "_", name).strip(" .")
    return safe_name or fallback


def _unique_directory(parent: Path, preferred_name: str) -> Path:
    candidate = parent / preferred_name
    index = 2
    while candidate.exists():
        candidate = parent / f"{preferred_name}_{index}"
        index += 1
    candidate.mkdir(parents=True)
    return candidate


def _unique_file(directory: Path, file_name: str) -> Path:
    safe_name = _safe_component(file_name, "dcp_data.txt")
    candidate = directory / safe_name
    index = 2
    while candidate.exists():
        candidate = directory / f"{Path(safe_name).stem}_{index}{Path(safe_name).suffix}"
        index += 1
    return candidate


def _group_archive_members(archive: Path, members) -> dict[str, list[tuple[object, tuple[str, ...]]]]:
    parsed_members = [(info, _member_parts(info.filename)) for info in members]
    all_nested = all(len(parts) >= 2 for _, parts in parsed_members)
    top_level_names = {parts[0] for _, parts in parsed_members if len(parts) >= 2}

    if all_nested and len(top_level_names) > 1:
        return {
            top_level: [item for item in parsed_members if item[1][0] == top_level]
            for top_level in sorted(top_level_names, key=str.casefold)
        }

    if all_nested and len(top_level_names) == 1:
        top_level = next(iter(top_level_names))
        if _looks_like_hh_batch_name(top_level):
            return {top_level: parsed_members}

    return {archive.stem: parsed_members}


def _extract_archive(archive: Path, staging_root: Path) -> tuple[list[Path], list[Path]]:
    try:
        with ZipFile(archive) as zip_file:
            data_members = []
            for info in zip_file.infolist():
                if info.is_dir():
                    continue
                parts = _member_parts(info.filename)
                if Path(parts[-1]).suffix.casefold() not in DATA_FILE_SUFFIXES:
                    continue
                if _is_symlink(info):
                    raise ZipInputError(f"ZIP中的DCP文件不能是符号链接: {info.filename}")
                if info.flag_bits & 0x1:
                    raise ZipInputError(f"ZIP已加密，无法读取: {archive.name}")
                data_members.append(info)

            if not data_members:
                raise ZipInputError(f"ZIP中未找到华虹DCP/TXT文件: {archive.name}")

            batch_directories: list[Path] = []
            extracted_files: list[Path] = []
            for group_name, grouped_members in _group_archive_members(archive, data_members).items():
                safe_group_name = _safe_component(group_name, "HH_ZIP_Batch")
                batch_directory = _unique_directory(staging_root, safe_group_name)
                batch_directories.append(batch_directory)

                for info, parts in grouped_members:
                    target = _unique_file(batch_directory, parts[-1])
                    with zip_file.open(info) as source, target.open("wb") as destination:
                        shutil.copyfileobj(source, destination)
                    extracted_files.append(target)

            return batch_directories, extracted_files
    except BadZipFile as exc:
        raise ZipInputError(f"ZIP文件损坏或格式无效: {archive.name}") from exc
    except OSError as exc:
        raise ZipInputError(f"读取ZIP失败 {archive.name}: {exc}") from exc


@contextmanager
def prepare_dcp_input(
    input_paths: str | Path | Sequence[str | Path],
    progress: ProgressCallback | None = None,
) -> Iterator[PreparedDCPInput]:
    """Prepare a direct folder or ZIP selection for the existing HH processor.

    A folder without ZIP files is passed through unchanged. ZIP archives are
    normalized into a temporary one-level (single batch) or two-level
    (multiple batch) directory so the established HH processor can consume
    them without changing its data-cleaning contract.
    """

    paths = normalize_input_paths(input_paths)
    archives = discover_zip_archives(paths)

    if not archives:
        if len(paths) != 1 or not paths[0].is_dir():
            raise ZipInputError("请选择一个数据文件夹，或选择一个/多个ZIP文件")
        data_files = discover_data_files(paths[0])
        if not data_files:
            raise ZipInputError("所选文件夹中未找到华虹DCP/TXT文件或ZIP文件")
        if progress:
            progress(f"使用原始数据文件夹，发现 {len(data_files)} 个DCP/TXT候选文件")
        yield PreparedDCPInput(paths[0], data_files, (), False)
        return

    loose_data_files = tuple(
        data_file
        for path in paths
        if path.is_dir()
        for data_file in discover_data_files(path)
    )
    if loose_data_files:
        raise ZipInputError(
            "所选文件夹同时包含已解压的DCP/TXT和ZIP文件。"
            "为避免重复处理，请选择纯数据文件夹或只包含ZIP的文件夹。"
        )

    if progress:
        progress(f"发现 {len(archives)} 个ZIP文件，正在准备临时解压目录...")

    with TemporaryDirectory(prefix="cp_hh_zip_") as temporary_directory:
        staging_root = Path(temporary_directory)
        batch_directories: list[Path] = []
        extracted_files: list[Path] = []

        for index, archive in enumerate(archives, start=1):
            if progress:
                progress(f"正在解压ZIP ({index}/{len(archives)}): {archive.name}")
            archive_batches, archive_files = _extract_archive(archive, staging_root)
            batch_directories.extend(archive_batches)
            extracted_files.extend(archive_files)

        processing_directory = batch_directories[0] if len(batch_directories) == 1 else staging_root
        if progress:
            progress(
                f"ZIP准备完成：{len(batch_directories)} 个批次，"
                f"{len(extracted_files)} 个DCP/TXT候选文件"
            )

        yield PreparedDCPInput(
            processing_directory,
            tuple(extracted_files),
            archives,
            True,
        )
