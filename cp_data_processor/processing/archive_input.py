"""Safely prepare vendor data from folders or one or more ZIP archives."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import shutil
from tempfile import TemporaryDirectory
from typing import Callable, Iterator, Sequence
from zipfile import BadZipFile, ZipFile


ProgressCallback = Callable[[str], None]
CommonRootPredicate = Callable[[str], bool]


class ArchiveInputError(ValueError):
    """Raised when a selected ZIP input cannot be prepared safely."""


@dataclass(frozen=True)
class PreparedArchiveInput:
    """A temporary or original directory ready for an existing processor."""

    directory: Path
    data_files: tuple[Path, ...]
    archives: tuple[Path, ...]
    is_temporary: bool
    batch_directories: tuple[Path, ...]


def normalize_input_paths(
    input_paths: str | Path | Sequence[str | Path],
) -> tuple[Path, ...]:
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
        raise ArchiveInputError("未选择数据文件夹或ZIP文件")

    return tuple(normalized)


def discover_zip_archives(
    input_paths: str | Path | Sequence[str | Path],
) -> tuple[Path, ...]:
    """Return selected ZIP files, including ZIPs directly stored in folders."""

    archives: list[Path] = []
    for path in normalize_input_paths(input_paths):
        if not path.exists():
            raise ArchiveInputError(f"输入路径不存在: {path}")

        if path.is_file():
            if path.suffix.casefold() != ".zip":
                raise ArchiveInputError(f"不支持的输入文件类型（仅支持ZIP）: {path.name}")
            archives.append(path)
            continue

        if not path.is_dir():
            raise ArchiveInputError(f"输入路径不是文件夹或ZIP文件: {path}")

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


def normalize_suffixes(allowed_suffixes: Sequence[str]) -> frozenset[str]:
    """Normalize configured source extensions to lowercase dotted suffixes."""

    suffixes = frozenset(
        suffix.casefold() if suffix.startswith(".") else f".{suffix.casefold()}"
        for suffix in allowed_suffixes
    )
    if not suffixes:
        raise ValueError("allowed_suffixes 不能为空")
    return suffixes


def discover_source_files(
    directory: Path,
    allowed_suffixes: Sequence[str],
) -> tuple[Path, ...]:
    """Find configured source files below a directory."""

    suffixes = normalize_suffixes(allowed_suffixes)
    return tuple(
        sorted(
            (
                path
                for path in directory.rglob("*")
                if path.is_file()
                and path.suffix.casefold() in suffixes
                and not path.name.startswith("~$")
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
        raise ArchiveInputError(f"ZIP包含不安全路径: {member_name}")
    return parts


def _is_symlink(info) -> bool:
    file_type = (info.external_attr >> 16) & 0o170000
    return file_type == 0o120000


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
    safe_name = _safe_component(file_name, "source_data.bin")
    candidate = directory / safe_name
    index = 2
    while candidate.exists():
        candidate = directory / f"{Path(safe_name).stem}_{index}{Path(safe_name).suffix}"
        index += 1
    return candidate


def _select_data_members(zip_file: ZipFile, suffixes: frozenset[str], source_label: str):
    selected = []
    for info in zip_file.infolist():
        if info.is_dir():
            continue
        parts = _member_parts(info.filename)
        if Path(parts[-1]).suffix.casefold() not in suffixes:
            continue
        if parts[-1].startswith("~$"):
            continue
        if _is_symlink(info):
            raise ArchiveInputError(f"ZIP中的{source_label}文件不能是符号链接: {info.filename}")
        if info.flag_bits & 0x1:
            raise ArchiveInputError(f"ZIP已加密，无法读取: {zip_file.filename}")
        selected.append((info, parts))
    return selected


def _group_flat_members(
    archive: Path,
    parsed_members,
    prefer_common_root: CommonRootPredicate | None,
):
    all_nested = all(len(parts) >= 2 for _, parts in parsed_members)
    top_level_names = {parts[0] for _, parts in parsed_members if len(parts) >= 2}

    if all_nested and len(top_level_names) > 1:
        return {
            top_level: [item for item in parsed_members if item[1][0] == top_level]
            for top_level in sorted(top_level_names, key=str.casefold)
        }

    if all_nested and len(top_level_names) == 1:
        top_level = next(iter(top_level_names))
        if prefer_common_root and prefer_common_root(top_level):
            return {top_level: parsed_members}

    return {archive.stem: parsed_members}


def _extract_flat_archive(
    zip_file: ZipFile,
    archive: Path,
    staging_root: Path,
    parsed_members,
    prefer_common_root: CommonRootPredicate | None,
) -> tuple[list[Path], list[Path]]:
    batch_directories: list[Path] = []
    extracted_files: list[Path] = []

    for group_name, grouped_members in _group_flat_members(
        archive, parsed_members, prefer_common_root
    ).items():
        batch_directory = _unique_directory(
            staging_root,
            _safe_component(group_name, "ZIP_Batch"),
        )
        batch_directories.append(batch_directory)

        for info, parts in grouped_members:
            target = _unique_file(batch_directory, parts[-1])
            with zip_file.open(info) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination)
            extracted_files.append(target)

    return batch_directories, extracted_files


def _extract_preserved_archive(
    zip_file: ZipFile,
    archive: Path,
    staging_root: Path,
    parsed_members,
) -> tuple[list[Path], list[Path]]:
    archive_directory = _unique_directory(
        staging_root,
        _safe_component(archive.stem, "ZIP_Batch"),
    )
    all_nested = all(len(parts) >= 2 for _, parts in parsed_members)
    top_level_names = {parts[0] for _, parts in parsed_members if len(parts) >= 2}
    common_root = next(iter(top_level_names)) if len(top_level_names) == 1 else None
    second_level_names = {
        parts[1]
        for _, parts in parsed_members
        if len(parts) >= 3
    }
    common_root_is_product_wrapper = bool(second_level_names) and not all(
        name.upper().startswith("EDS") for name in second_level_names
    )
    strip_common_root = bool(
        all_nested
        and common_root
        and (
            common_root.casefold() == archive.stem.casefold()
            or common_root_is_product_wrapper
        )
    )
    extracted_files: list[Path] = []

    for info, parts in parsed_members:
        relative_parts = parts[1:] if strip_common_root else parts
        safe_parts = [
            _safe_component(part, "data")
            for part in relative_parts
        ]
        target_directory = archive_directory.joinpath(*safe_parts[:-1])
        target_directory.mkdir(parents=True, exist_ok=True)
        target = _unique_file(target_directory, safe_parts[-1])
        with zip_file.open(info) as source, target.open("wb") as destination:
            shutil.copyfileobj(source, destination)
        extracted_files.append(target)

    return [archive_directory], extracted_files


def _extract_archive(
    archive: Path,
    staging_root: Path,
    suffixes: frozenset[str],
    source_label: str,
    preserve_member_paths: bool,
    prefer_common_root: CommonRootPredicate | None,
) -> tuple[list[Path], list[Path]]:
    try:
        with ZipFile(archive) as zip_file:
            parsed_members = _select_data_members(zip_file, suffixes, source_label)
            if not parsed_members:
                raise ArchiveInputError(
                    f"ZIP中未找到{source_label}文件: {archive.name}"
                )

            if preserve_member_paths:
                return _extract_preserved_archive(
                    zip_file, archive, staging_root, parsed_members
                )
            return _extract_flat_archive(
                zip_file,
                archive,
                staging_root,
                parsed_members,
                prefer_common_root,
            )
    except BadZipFile as exc:
        raise ArchiveInputError(f"ZIP文件损坏或格式无效: {archive.name}") from exc
    except OSError as exc:
        raise ArchiveInputError(f"读取ZIP失败 {archive.name}: {exc}") from exc


@contextmanager
def prepare_archive_input(
    input_paths: str | Path | Sequence[str | Path],
    *,
    allowed_suffixes: Sequence[str],
    source_label: str,
    progress: ProgressCallback | None = None,
    preserve_member_paths: bool = False,
    prefer_common_root: CommonRootPredicate | None = None,
    temporary_prefix: str = "cp_vendor_zip_",
) -> Iterator[PreparedArchiveInput]:
    """Prepare direct-folder or ZIP input without changing vendor processors."""

    suffixes = normalize_suffixes(allowed_suffixes)
    paths = normalize_input_paths(input_paths)
    archives = discover_zip_archives(paths)

    if not archives:
        if len(paths) != 1 or not paths[0].is_dir():
            raise ArchiveInputError("请选择一个数据文件夹，或选择一个/多个ZIP文件")
        data_files = discover_source_files(paths[0], suffixes)
        if not data_files:
            raise ArchiveInputError(
                f"所选文件夹中未找到{source_label}文件或ZIP文件"
            )
        if progress:
            progress(f"使用原始数据文件夹，发现 {len(data_files)} 个{source_label}候选文件")
        yield PreparedArchiveInput(
            paths[0], data_files, (), False, (paths[0],)
        )
        return

    loose_data_files = tuple(
        data_file
        for path in paths
        if path.is_dir()
        for data_file in discover_source_files(path, suffixes)
    )
    if loose_data_files:
        raise ArchiveInputError(
            f"所选文件夹同时包含已解压的{source_label}文件和ZIP文件。"
            "为避免重复处理，请选择纯数据文件夹或只包含ZIP的文件夹。"
        )

    if progress:
        progress(f"发现 {len(archives)} 个ZIP文件，正在准备临时解压目录...")

    with TemporaryDirectory(prefix=temporary_prefix) as temporary_directory:
        staging_root = Path(temporary_directory)
        batch_directories: list[Path] = []
        extracted_files: list[Path] = []

        for index, archive in enumerate(archives, start=1):
            if progress:
                progress(f"正在解压ZIP ({index}/{len(archives)}): {archive.name}")
            archive_batches, archive_files = _extract_archive(
                archive,
                staging_root,
                suffixes,
                source_label,
                preserve_member_paths,
                prefer_common_root,
            )
            batch_directories.extend(archive_batches)
            extracted_files.extend(archive_files)

        processing_directory = (
            batch_directories[0]
            if len(batch_directories) == 1
            else staging_root
        )
        if progress:
            progress(
                f"ZIP准备完成：{len(batch_directories)} 个输入批次，"
                f"{len(extracted_files)} 个{source_label}候选文件"
            )

        yield PreparedArchiveInput(
            processing_directory,
            tuple(extracted_files),
            archives,
            True,
            tuple(batch_directories),
        )
