"""Create bounded, sanitized structural profiles of CP source samples."""

from __future__ import annotations

import csv
import hashlib
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SUPPORTED_SUFFIXES = {".csv", ".dcp", ".etxt", ".txt", ".tsv", ".xls", ".xlsx"}
ENCODINGS = ("utf-8-sig", "gb18030", "utf-16", "latin1")
OOXML_SIGNATURE = b"PK\x03\x04"
OLE_SIGNATURE = bytes.fromhex("d0cf11e0a1b11ae1")


def discover_files(inputs: Iterable[str], max_files: int = 20) -> list[Path]:
    files: list[Path] = []
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            files.append(path)
        elif path.is_dir():
            files.extend(
                candidate
                for candidate in sorted(path.rglob("*"))
                if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_SUFFIXES
            )
        else:
            raise FileNotFoundError(f"unsupported or missing input: {path}")
    unique = list(dict.fromkeys(files))
    if not unique:
        raise ValueError("no supported CP sample files were found")
    return unique[:max_files]


def _sha256_prefix(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:16]


def _classify_cell(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "blank"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "numeric"
    text = str(value).strip()
    if not text:
        return "blank"
    try:
        float(text.replace(",", ""))
        return "numeric"
    except ValueError:
        return "text"


def _sanitize_cell(value: Any) -> str:
    kind = _classify_cell(value)
    if kind == "blank":
        return ""
    if kind == "numeric":
        return "<NUM>"
    text = re.sub(r"\s+", " ", str(value).strip())
    text = re.sub(r"(?<![A-Za-z])\d{4,}(?![A-Za-z])", "<ID>", text)
    return text[:80]


def _sanitize_filename(path: Path) -> str:
    stem = re.sub(r"\d{3,}", "<N>", path.stem)
    return f"{stem[:80]}{path.suffix.lower()}"


def _summarize_rows(rows: list[list[Any]], max_columns: int) -> dict[str, Any]:
    bounded = [row[:max_columns] for row in rows]
    profiles = []
    for index, row in enumerate(bounded):
        kinds = Counter(_classify_cell(value) for value in row)
        profiles.append(
            {
                "row_index_zero_based": index,
                "nonempty": len(row) - kinds["blank"],
                "text_cells": kinds["text"],
                "numeric_cells": kinds["numeric"],
            }
        )
    candidates = sorted(
        profiles,
        key=lambda item: (item["text_cells"], item["nonempty"]),
        reverse=True,
    )[:5]
    return {
        "header_candidates": candidates,
        "sanitized_preview": [[_sanitize_cell(value) for value in row] for row in bounded],
    }


def _profile_text(path: Path, row_limit: int, column_limit: int) -> dict[str, Any]:
    raw = path.read_bytes()[:1024 * 1024]
    text = ""
    encoding = "binary-or-unknown"
    for candidate in ENCODINGS:
        try:
            text = raw.decode(candidate)
            encoding = candidate
            break
        except UnicodeDecodeError:
            continue
    sample = text[:65536]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="\t,;|")
        delimiter = dialect.delimiter
        rows = list(csv.reader(sample.splitlines(), dialect))[:row_limit]
    except csv.Error:
        delimiter = "whitespace"
        rows = [re.split(r"\s+", line.strip()) for line in sample.splitlines()[:row_limit]]
    return {
        "kind": "text",
        "encoding": encoding,
        "delimiter": delimiter,
        "structure": _summarize_rows(rows, column_limit),
    }


def _profile_excel(path: Path, row_limit: int, column_limit: int) -> dict[str, Any]:
    import pandas as pd

    try:
        workbook = pd.ExcelFile(path)
    except Exception as exc:
        return {"kind": "excel", "error": f"{type(exc).__name__}: {exc}"}
    sheets = []
    for sheet_name in workbook.sheet_names[:20]:
        try:
            frame = pd.read_excel(
                workbook,
                sheet_name=sheet_name,
                header=None,
                nrows=row_limit,
            ).iloc[:, :column_limit]
            rows = frame.where(frame.notna(), None).values.tolist()
            sheets.append(
                {
                    "name": str(sheet_name),
                    "preview_rows": int(len(frame)),
                    "preview_columns": int(len(frame.columns)),
                    "structure": _summarize_rows(rows, column_limit),
                }
            )
        except Exception as exc:
            sheets.append({"name": str(sheet_name), "error": f"{type(exc).__name__}: {exc}"})
    return {
        "kind": "excel",
        "sheet_names": [str(name) for name in workbook.sheet_names],
        "sheets": sheets,
    }


def _profile_file(path: Path, row_limit: int, column_limit: int) -> dict[str, Any]:
    with path.open("rb") as handle:
        signature = handle.read(16)
    is_excel = signature.startswith(OOXML_SIGNATURE) or signature.startswith(OLE_SIGNATURE)
    content = (
        _profile_excel(path, row_limit, column_limit)
        if is_excel
        else _profile_text(path, row_limit, column_limit)
    )
    return {
        "sanitized_name": _sanitize_filename(path),
        "suffix": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
        "signature_hex": signature.hex(),
        "sha256_prefix": _sha256_prefix(path),
        "content": content,
    }


def build_sample_profile(
    inputs: Iterable[str],
    *,
    max_files: int = 20,
    preview_rows: int = 30,
    preview_columns: int = 80,
) -> dict[str, Any]:
    files = discover_files(inputs, max_files=max_files)
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "privacy_note": "Numeric cells and long numeric identifiers are masked.",
        "file_count": len(files),
        "files": [
            _profile_file(path, preview_rows, preview_columns) for path in files
        ],
    }
