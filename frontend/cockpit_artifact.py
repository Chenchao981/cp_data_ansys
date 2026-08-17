"""Portable, validated CP Cockpit artifact files.

The artifact is a ZIP container with a ``.cpcockpit`` extension. It stores
the standard cleaned/yield/spec CSV inputs used by the dashboard; it never
stores or reparses vendor raw data.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


ARTIFACT_FORMAT = "nce-cp-cockpit"
ARTIFACT_VERSION = 1
MANIFEST_NAME = "manifest.json"
ALLOWED_ROLES = {"cleaned", "yield", "spec"}
MAX_DATA_FILES = 64
MAX_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024


class CockpitArtifactError(ValueError):
    """Raised when a Cockpit artifact is invalid or unsafe."""


@dataclass(frozen=True)
class ArtifactSource:
    role: str
    original_name: str
    content: bytes


@dataclass(frozen=True)
class CockpitArtifact:
    files: tuple[ArtifactSource, ...]
    created_at: str

    def files_for_role(self, role: str) -> tuple[ArtifactSource, ...]:
        return tuple(item for item in self.files if item.role == role)


def _safe_original_name(name: str) -> str:
    clean_name = Path(str(name)).name
    if not clean_name or clean_name in {".", ".."} or clean_name != str(name):
        raise CockpitArtifactError(f"非法数据文件名: {name}")
    if not clean_name.lower().endswith(".csv"):
        raise CockpitArtifactError(f"Cockpit 包只允许标准 CSV: {clean_name}")
    return clean_name


def _validate_sources(sources: Sequence[ArtifactSource]) -> None:
    if not sources:
        raise CockpitArtifactError("没有可保存的标准 CSV")
    if len(sources) > MAX_DATA_FILES:
        raise CockpitArtifactError(f"数据文件数量超过上限: {len(sources)} > {MAX_DATA_FILES}")

    seen_names: set[str] = set()
    role_counts = {role: 0 for role in ALLOWED_ROLES}
    for source in sources:
        if not isinstance(source.role, str) or source.role not in ALLOWED_ROLES:
            raise CockpitArtifactError(f"未知数据角色: {source.role}")
        name = _safe_original_name(source.original_name)
        lowered = name.casefold()
        if lowered in seen_names:
            raise CockpitArtifactError(f"数据文件名重复: {name}")
        seen_names.add(lowered)
        role_counts[source.role] += 1
        if not isinstance(source.content, bytes):
            raise CockpitArtifactError(f"数据内容必须为 bytes: {name}")

    if role_counts["cleaned"] > 1 or role_counts["yield"] > 1:
        raise CockpitArtifactError("每个 Cockpit 包最多包含一份 cleaned 和一份 yield CSV")
    if role_counts["cleaned"] == 0 and role_counts["yield"] == 0:
        raise CockpitArtifactError("Cockpit 包至少需要 cleaned 或 yield CSV")


def sources_from_paths(
    cleaned_path: Path | None,
    yield_path: Path | None,
    spec_paths: Iterable[Path],
) -> tuple[ArtifactSource, ...]:
    """Read the exact standard CSV bytes selected by the dashboard."""

    sources: list[ArtifactSource] = []
    for role, paths in (
        ("cleaned", [cleaned_path] if cleaned_path else []),
        ("yield", [yield_path] if yield_path else []),
        ("spec", list(spec_paths)),
    ):
        for path in paths:
            resolved = Path(path)
            sources.append(
                ArtifactSource(
                    role=role,
                    original_name=resolved.name,
                    content=resolved.read_bytes(),
                )
            )
    _validate_sources(sources)
    return tuple(sources)


def build_cockpit_artifact(sources: Sequence[ArtifactSource]) -> bytes:
    """Build a portable Cockpit artifact."""

    _validate_sources(sources)
    created_at = datetime.now(timezone.utc).isoformat()
    manifest_files = []
    for source in sources:
        archive_name = f"data/{source.original_name}"
        manifest_files.append(
            {
                "role": source.role,
                "archive_name": archive_name,
                "original_name": source.original_name,
                "size": len(source.content),
                "sha256": hashlib.sha256(source.content).hexdigest(),
            }
        )
    manifest = {
        "format": ARTIFACT_FORMAT,
        "version": ARTIFACT_VERSION,
        "created_at": created_at,
        "files": manifest_files,
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            MANIFEST_NAME,
            json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
        )
        for source in sources:
            archive.writestr(f"data/{source.original_name}", source.content)
    return buffer.getvalue()


def _validate_archive_name(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise CockpitArtifactError(f"Cockpit 包含不安全路径: {name}")


def read_cockpit_artifact(content: bytes) -> CockpitArtifact:
    """Validate and load an artifact without extracting files to disk."""

    try:
        archive = zipfile.ZipFile(io.BytesIO(content), "r")
    except (zipfile.BadZipFile, TypeError) as exc:
        raise CockpitArtifactError("不是有效的 .cpcockpit 文件") from exc

    with archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise CockpitArtifactError("Cockpit 包含重复条目")
        for name in names:
            _validate_archive_name(name)
        total_size = sum(info.file_size for info in archive.infolist())
        if total_size > MAX_UNCOMPRESSED_BYTES:
            raise CockpitArtifactError("Cockpit 文件解压后超过 1 GB 安全上限")
        if MANIFEST_NAME not in names:
            raise CockpitArtifactError("Cockpit 包缺少 manifest.json")
        try:
            manifest = json.loads(archive.read(MANIFEST_NAME).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
            raise CockpitArtifactError("Cockpit 清单无法读取") from exc

        if manifest.get("format") != ARTIFACT_FORMAT:
            raise CockpitArtifactError("不是受支持的 CP Cockpit 文件")
        if manifest.get("version") != ARTIFACT_VERSION:
            raise CockpitArtifactError(
                f"不支持的 Cockpit 文件版本: {manifest.get('version')}"
            )
        manifest_files = manifest.get("files")
        if not isinstance(manifest_files, list):
            raise CockpitArtifactError("Cockpit 清单缺少 files 列表")

        sources: list[ArtifactSource] = []
        declared_names = {MANIFEST_NAME}
        for item in manifest_files:
            if not isinstance(item, dict):
                raise CockpitArtifactError("Cockpit 文件清单条目无效")
            role = item.get("role")
            original_name = _safe_original_name(item.get("original_name", ""))
            archive_name = item.get("archive_name")
            expected_name = f"data/{original_name}"
            if archive_name != expected_name:
                raise CockpitArtifactError(f"Cockpit 数据路径与文件名不一致: {original_name}")
            if archive_name not in names:
                raise CockpitArtifactError(f"Cockpit 包缺少数据文件: {original_name}")
            declared_names.add(archive_name)
            try:
                file_content = archive.read(archive_name)
            except zipfile.BadZipFile as exc:
                raise CockpitArtifactError(
                    f"Cockpit 数据文件已损坏: {original_name}"
                ) from exc
            if item.get("size") != len(file_content):
                raise CockpitArtifactError(f"Cockpit 数据文件大小校验失败: {original_name}")
            actual_hash = hashlib.sha256(file_content).hexdigest()
            if item.get("sha256") != actual_hash:
                raise CockpitArtifactError(f"Cockpit 数据文件完整性校验失败: {original_name}")
            sources.append(ArtifactSource(role, original_name, file_content))

        unexpected = set(names) - declared_names
        if unexpected:
            raise CockpitArtifactError(
                "Cockpit 包包含清单外文件: " + ", ".join(sorted(unexpected))
            )
        _validate_sources(sources)
        return CockpitArtifact(
            files=tuple(sources),
            created_at=str(manifest.get("created_at") or ""),
        )
