"""Windows runtime paths shared by the GUI and packaged processors.

Program files are replaceable under ``D:\\CPDataAnalysis``.  Raw CP data,
generated outputs, logs, and user configuration live under ``D:\\CPData``
by default so an application upgrade never needs to touch business data.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict


COMPANY_FOLDERS = {
    "hh": "HH",
    "huahong": "HH",
    "jt": "JT",
    "jetech": "JT",
    "lion": "Lion",
    "guoyu": "Guoyu",
}


def get_data_root() -> Path:
    """Return the persistent business-data root."""
    configured = os.environ.get("CP_DATA_ROOT")
    if configured:
        return Path(configured).expanduser()
    if os.name == "nt":
        return Path(r"D:\CPData")
    return Path.home() / "CPData"


def get_raw_root() -> Path:
    return get_data_root() / "raw"


def get_output_root() -> Path:
    return get_data_root() / "output"


def get_log_dir() -> Path:
    configured = os.environ.get("CP_LOG_DIR")
    return Path(configured).expanduser() if configured else get_data_root() / "logs"


def get_config_dir() -> Path:
    configured = os.environ.get("CP_CONFIG_DIR")
    return Path(configured).expanduser() if configured else get_data_root() / "config"


def _company_folder(company: str) -> str:
    key = company.strip().lower()
    if key not in COMPANY_FOLDERS:
        raise ValueError(f"Unsupported CP company: {company}")
    return COMPANY_FOLDERS[key]


def get_company_raw_dir(company: str) -> Path:
    return get_raw_root() / _company_folder(company)


def get_company_output_dir(company: str) -> Path:
    return get_output_root() / _company_folder(company)


def ensure_data_directories() -> Dict[str, Path]:
    """Create the stable directory layout and return the created paths."""
    paths: Dict[str, Path] = {
        "root": get_data_root(),
        "raw": get_raw_root(),
        "output": get_output_root(),
        "logs": get_log_dir(),
        "config": get_config_dir(),
    }
    for folder in sorted(set(COMPANY_FOLDERS.values())):
        paths[f"raw_{folder.lower()}"] = paths["raw"] / folder
        paths[f"output_{folder.lower()}"] = paths["output"] / folder

    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def configure_application_logging(prefix: str = "cp_data_analysis") -> Path:
    """Configure one rotating UTF-8 application log outside the program tree."""
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{prefix}_{datetime.now():%Y%m%d}.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    managed_handler = next(
        (
            handler
            for handler in root_logger.handlers
            if getattr(handler, "_cp_data_managed_log", False)
        ),
        None,
    )
    if managed_handler is None:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        file_handler._cp_data_managed_log = True  # type: ignore[attr-defined]
        root_logger.addHandler(file_handler)
    else:
        log_path = Path(managed_handler.baseFilename)

    has_console_handler = any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.FileHandler)
        for handler in root_logger.handlers
    )
    if not has_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    return log_path
