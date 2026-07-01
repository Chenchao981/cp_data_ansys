from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable

import pandas as pd


FILE_PATTERNS = {
    "cleaned": "*_cleaned_*.csv",
    "yield": "*_yield_*.csv",
    "spec": "*_spec_*.csv",
}

BASE_COLUMNS = {
    "Lot_ID",
    "Wafer_ID",
    "X",
    "Y",
    "Seq",
    "Bin",
    "CONT",
    "SITE_NUM",
    "T_TIME",
}


@dataclass(frozen=True)
class DataBundle:
    directory: Path
    files: dict[str, Path]
    cleaned: pd.DataFrame | None
    yield_data: pd.DataFrame | None
    spec: pd.DataFrame | None
    source_kind: str = "standard_csv"
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not any(df is not None for df in (self.cleaned, self.yield_data, self.spec))


def _latest_file(paths: Iterable[Path]) -> Path | None:
    candidates = list(paths)
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime_ns, path.name))


def discover_standard_files(directory: str | Path) -> dict[str, Path]:
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"数据目录不存在：{root}")

    files: dict[str, Path] = {}
    for kind, pattern in FILE_PATTERNS.items():
        latest = _latest_file(root.glob(pattern))
        if latest is not None:
            files[kind] = latest
    return files


def read_csv_compatible(path: Path) -> pd.DataFrame:
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return pd.read_csv(path, low_memory=False)


def excel_sheet_names(path: str | Path) -> list[str]:
    source = Path(path)
    if source.suffix.lower() not in {".xlsx", ".xls"}:
        return []
    with pd.ExcelFile(source) as workbook:
        return list(workbook.sheet_names)


def read_table_file(path: str | Path, sheet_name: str | int = 0) -> pd.DataFrame:
    source = Path(path).expanduser().resolve()
    suffix = source.suffix.lower()
    if suffix == ".csv":
        return read_csv_compatible(source)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(source, sheet_name=sheet_name)
    raise ValueError(f"暂不支持预览该文件类型：{suffix or '无扩展名'}")


def load_bundle(directory: str | Path) -> DataBundle:
    root = Path(directory).expanduser().resolve()
    files = discover_standard_files(root)
    frames = {kind: read_csv_compatible(path) for kind, path in files.items()}
    return DataBundle(
        directory=root,
        files=files,
        cleaned=frames.get("cleaned"),
        yield_data=frames.get("yield"),
        spec=frames.get("spec"),
        source_kind="standard_csv",
        metadata={"adapter": "Standard CSV", "file_count": len(files)},
    )


def normalize_yield_percent(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip()
    has_percent = text.str.endswith("%", na=False)
    numeric = pd.to_numeric(text.str.rstrip("%"), errors="coerce")
    fractional = (~has_percent) & numeric.between(0, 1, inclusive="both")
    return numeric.where(~fractional, numeric * 100)


def wafer_yield_data(frame: pd.DataFrame | None) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    required = {"Lot_ID", "Wafer_ID", "Yield"}
    if not required.issubset(frame.columns):
        return pd.DataFrame()
    result = frame.loc[frame["Lot_ID"].astype(str).str.upper() != "ALL"].copy()
    result["Yield_Numeric"] = normalize_yield_percent(result["Yield"])
    return result.dropna(subset=["Yield_Numeric"])


def first_existing_column(frame: pd.DataFrame | None, names: Iterable[str]) -> str | None:
    if frame is None:
        return None
    return next((name for name in names if name in frame.columns), None)


def dynamic_bin_columns(frame: pd.DataFrame | None) -> list[str]:
    if frame is None:
        return []
    pattern = re.compile(r"^bin(?:[_\s-]?\d+|[_\s-]?.+)$", re.IGNORECASE)
    columns = [str(column) for column in frame.columns if str(column) != "Bin" and pattern.match(str(column))]
    return [column for column in columns if pd.to_numeric(frame[column], errors="coerce").notna().any()]


def parameter_columns(frame: pd.DataFrame | None) -> list[str]:
    if frame is None:
        return []
    parameters: list[str] = []
    for column in frame.columns:
        if column in BASE_COLUMNS:
            continue
        numeric = pd.to_numeric(frame[column], errors="coerce")
        if numeric.notna().any():
            parameters.append(str(column))
    return parameters


def parameter_spec(spec: pd.DataFrame | None, parameter: str) -> dict[str, object]:
    if spec is None or spec.empty:
        return {}

    if "Parameter" in spec.columns:
        rows = spec.loc[spec["Parameter"].astype(str) == parameter]
        if rows.empty:
            return {}
        row = rows.iloc[0]
        return {
            key: row[key]
            for key in ("Unit", "LimitL", "LimitU", "LSL", "USL", "Target", "TestCond")
            if key in row.index and pd.notna(row[key])
        }

    first_column = spec.columns[0]
    if parameter not in spec.columns:
        return {}
    result: dict[str, object] = {}
    aliases = {
        "unit": "Unit",
        "limitl": "LimitL",
        "lsl": "LSL",
        "limitu": "LimitU",
        "usl": "USL",
        "target": "Target",
        "testcond:": "TestCond",
        "testcond": "TestCond",
    }
    for _, row in spec.iterrows():
        label = str(row[first_column]).strip().lower()
        if label in aliases and pd.notna(row[parameter]):
            result[aliases[label]] = row[parameter]
    return result


def filter_by_lot_and_wafer(
    frame: pd.DataFrame | None,
    lots: list[str] | None = None,
    wafers: list[str] | None = None,
) -> pd.DataFrame:
    if frame is None:
        return pd.DataFrame()
    result = frame.copy()
    if lots and "Lot_ID" in result.columns:
        result = result[result["Lot_ID"].astype(str).isin(lots)]
    if wafers and "Wafer_ID" in result.columns:
        result = result[result["Wafer_ID"].astype(str).isin(wafers)]
    return result
