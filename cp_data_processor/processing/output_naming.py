"""Shared output-folder naming for all CP vendor workflows."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re


INVALID_WINDOWS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


class OutputNamingError(ValueError):
    """Raised when a real first lot ID cannot be used for output naming."""


def sanitize_lot_id(lot_id: object) -> str:
    """Return a Windows-safe lot ID without replacing it with a company name."""

    raw_lot_id = str(lot_id or "").strip()
    if not raw_lot_id:
        raise OutputNamingError("无法识别首个真实批次号，未创建输出文件夹")

    safe_lot_id = INVALID_WINDOWS_CHARS.sub("_", raw_lot_id).strip(" .")
    if not safe_lot_id:
        raise OutputNamingError("首个批次号不包含可用于文件夹命名的字符")
    if safe_lot_id.upper() in WINDOWS_RESERVED_NAMES:
        safe_lot_id = f"_{safe_lot_id}"
    return safe_lot_id


def build_output_folder_name(
    first_lot_id: object,
    *,
    serial: str | None = None,
    now: datetime | None = None,
) -> str:
    """Build ``<first lot ID>_YYYYMMDD_HHMMSS`` for one processing run."""

    safe_lot_id = sanitize_lot_id(first_lot_id)
    run_serial = serial or (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    safe_serial = INVALID_WINDOWS_CHARS.sub("_", str(run_serial).strip()).strip(" .")
    if not safe_serial:
        raise OutputNamingError("输出流水号不能为空")
    return f"{safe_lot_id}_{safe_serial}"


def create_output_run_dir(
    output_parent: str | Path,
    first_lot_id: object,
    *,
    serial: str | None = None,
    now: datetime | None = None,
) -> Path:
    """Create a collision-safe run directory using the shared naming contract."""

    parent = Path(output_parent).expanduser()
    parent.mkdir(parents=True, exist_ok=True)
    base_name = build_output_folder_name(first_lot_id, serial=serial, now=now)

    index = 0
    while True:
        suffix = "" if index == 0 else f"_{index:03d}"
        candidate = parent / f"{base_name}{suffix}"
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            index += 1
