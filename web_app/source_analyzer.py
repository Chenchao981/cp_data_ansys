from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import redirect_stdout
import io
from pathlib import Path
import re
from typing import Iterable

import numpy as np
import pandas as pd

from cp_data_processor.readers.dcp_reader import DCPReader
from cp_data_processor.readers.jt_reader import JTReader
from guoyu.guoyu_reader import GuoyuFRDReader
from lion.lion_reader import LionExcelReader
from web_app.data_service import DataBundle, load_bundle, parameter_columns, read_csv_compatible


SUPPORTED_SUFFIXES = {".txt", ".dcp", ".csv", ".xlsx", ".xls"}
BASE_COLUMNS = ["Lot_ID", "Wafer_ID", "Seq", "Bin", "X", "Y"]


def source_files(source: str | Path) -> list[Path]:
    path = Path(source).expanduser().resolve()
    if path.is_file():
        return [path] if path.suffix.lower() in SUPPORTED_SUFFIXES else []
    if not path.is_dir():
        return []
    return sorted(
        (item for item in path.iterdir() if item.is_file() and item.suffix.lower() in SUPPORTED_SUFFIXES),
        key=lambda item: item.name,
    )


def source_fingerprint(source: str | Path) -> tuple[tuple[str, int, int], ...]:
    return tuple((str(path), path.stat().st_mtime_ns, path.stat().st_size) for path in source_files(source))


def _excel_sheets(path: Path) -> set[str]:
    try:
        with pd.ExcelFile(path) as workbook:
            return set(workbook.sheet_names)
    except Exception:
        return set()


def _looks_like_huahong(path: Path) -> bool:
    if path.suffix.lower() not in {".txt", ".dcp"}:
        return False
    try:
        lines = path.read_bytes()[:32_768].decode("utf-8", errors="replace").splitlines()
    except OSError:
        return False
    if len(lines) < 16:
        return False
    metadata = "\n".join(lines[:3]).lower()
    header = lines[6].lower() if len(lines) > 6 else ""
    return all(label in metadata for label in ("program name", "lot number", "wafer number")) and "bin" in header


def _standardize_aliases(frame: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "lotid": "Lot_ID",
        "lot_id": "Lot_ID",
        "lot": "Lot_ID",
        "waferid": "Wafer_ID",
        "wafer_id": "Wafer_ID",
        "wafer": "Wafer_ID",
        "soft_bin": "Bin",
        "softbin": "Bin",
        "hardbin": "Bin",
        "bin#": "Bin",
        "x_coord": "X",
        "xcoord": "X",
        "y_coord": "Y",
        "ycoord": "Y",
        "dut_no": "Seq",
        "part_index": "Seq",
        "serial#": "Seq",
    }
    rename: dict[object, str] = {}
    occupied = set(frame.columns)
    for column in frame.columns:
        normalized = str(column).strip().lower()
        target = aliases.get(normalized)
        if target and target not in occupied:
            rename[column] = target
            occupied.add(target)
    return frame.rename(columns=rename)


def _lot_to_frame(lot) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for wafer in lot.wafers:
        if wafer.chip_data is None or wafer.chip_data.empty:
            continue
        frame = _standardize_aliases(wafer.chip_data.copy())
        if "Lot_ID" not in frame.columns:
            frame["Lot_ID"] = wafer.source_lot_id or lot.lot_id
        if "Wafer_ID" not in frame.columns:
            frame["Wafer_ID"] = wafer.wafer_id
        for name, values in (("Seq", wafer.seq), ("Bin", wafer.bin), ("X", wafer.x), ("Y", wafer.y)):
            if name not in frame.columns and values is not None and len(values) == len(frame):
                frame[name] = values
        frame = frame.drop(columns=["No.U", "LotID", "WaferID"], errors="ignore")
        ordered = [name for name in BASE_COLUMNS if name in frame.columns]
        frame = frame[ordered + [name for name in frame.columns if name not in ordered]]
        frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _params_to_spec(lot) -> pd.DataFrame | None:
    records = []
    for parameter in getattr(lot, "params", []):
        if parameter.id == "No.U":
            continue
        if any(value is not None for value in (parameter.unit, parameter.sl, parameter.su)):
            records.append(
                {
                    "Parameter": parameter.id,
                    "Unit": parameter.unit,
                    "LimitL": parameter.sl,
                    "LimitU": parameter.su,
                    "TestCond": "; ".join(parameter.test_cond or []),
                }
            )
    return pd.DataFrame(records) if records else None


def _folder_identity(path: Path, fallback_lot: str) -> tuple[str | None, str]:
    folder = path if path.is_dir() else path.parent
    name = folder.name
    match = re.match(r"(?P<product>[^_]+)_(?P<lot>[^@]+)@", name)
    return (match.group("product"), match.group("lot")) if match else (None, fallback_lot)


class SourceAdapter(ABC):
    name = "Unknown"
    source_kind = "unknown"
    trustworthy_spec = True

    @abstractmethod
    def can_load(self, files: list[Path]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def load(self, source: Path, files: list[Path]):
        raise NotImplementedError


class GuoyuAdapter(SourceAdapter):
    name = "Guoyu FRD"
    source_kind = "guoyu_raw"

    def can_load(self, files: list[Path]) -> bool:
        excel = [path for path in files if path.suffix.lower() in {".xlsx", ".xls"}]
        return bool(excel and GuoyuFRDReader().can_read(str(excel[0])))

    def load(self, source: Path, files: list[Path]):
        excel = [str(path) for path in files if path.suffix.lower() in {".xlsx", ".xls"}]
        lot_id = source.name if source.is_dir() else None
        return GuoyuFRDReader(excel, pass_bin=1, lot_id=lot_id).read()


class LionAdapter(SourceAdapter):
    name = "Lion"
    source_kind = "lion_raw"

    def can_load(self, files: list[Path]) -> bool:
        excel = [path for path in files if path.suffix.lower() in {".xlsx", ".xls"}]
        return bool(excel and {name.lower() for name in _excel_sheets(excel[0])} >= {"dut_data", "summary_information"})

    def load(self, source: Path, files: list[Path]):
        excel = [str(path) for path in files if path.suffix.lower() in {".xlsx", ".xls"}]
        return LionExcelReader(excel, pass_bin=1).read()


class JetechAdapter(SourceAdapter):
    name = "Jetech"
    source_kind = "jetech_raw"

    def can_load(self, files: list[Path]) -> bool:
        excel = [path for path in files if path.suffix.lower() in {".xlsx", ".xls"}]
        if not excel:
            return False
        sheets = {name.lower() for name in _excel_sheets(excel[0])}
        return "dut_data" in sheets and "summary information" in sheets

    def load(self, source: Path, files: list[Path]):
        excel = [str(path) for path in files if path.suffix.lower() in {".xlsx", ".xls"}]
        return JTReader(excel, pass_bin=1).read()


class HuaHongAdapter(SourceAdapter):
    name = "HuaHong DCP"
    source_kind = "huahong_raw"
    trustworthy_spec = False

    def can_load(self, files: list[Path]) -> bool:
        text_files = [path for path in files if path.suffix.lower() in {".txt", ".dcp"}]
        return bool(text_files and _looks_like_huahong(text_files[0]))

    def load(self, source: Path, files: list[Path]):
        text_files = [str(path) for path in files if path.suffix.lower() in {".txt", ".dcp"}]
        lot = DCPReader(text_files, pass_bin=1).read()
        product, lot_id = _folder_identity(source, lot.lot_id)
        lot.lot_id = lot_id
        if product:
            lot.product = product
        return lot


class StandardCSVAdapter(SourceAdapter):
    name = "Standard CSV"
    source_kind = "standard_csv"

    def can_load(self, files: list[Path]) -> bool:
        names = [path.name.lower() for path in files]
        return any("_cleaned_" in name and name.endswith(".csv") for name in names)

    def load(self, source: Path, files: list[Path]):
        return load_bundle(source if source.is_dir() else source.parent)


class GenericTableAdapter(SourceAdapter):
    name = "Generic Table"
    source_kind = "generic_table"
    trustworthy_spec = False

    def can_load(self, files: list[Path]) -> bool:
        return any(path.suffix.lower() in {".csv", ".xlsx", ".xls"} for path in files)

    def load(self, source: Path, files: list[Path]):
        frames: list[pd.DataFrame] = []
        table_files = [path for path in files if path.suffix.lower() in {".csv", ".xlsx", ".xls"}]
        for index, path in enumerate(table_files, start=1):
            frame = read_csv_compatible(path) if path.suffix.lower() == ".csv" else pd.read_excel(path, sheet_name=0)
            frame = _standardize_aliases(frame)
            if "Lot_ID" not in frame.columns:
                frame["Lot_ID"] = path.stem
            if "Wafer_ID" not in frame.columns:
                match = re.search(r"(?:_|-)(\d+)$", path.stem)
                frame["Wafer_ID"] = match.group(1) if match else str(index)
            if "Seq" not in frame.columns:
                frame["Seq"] = np.arange(1, len(frame) + 1)
            frames.append(frame)
        return pd.concat(frames, ignore_index=True, sort=False)


ADAPTERS: tuple[SourceAdapter, ...] = (
    GuoyuAdapter(),
    LionAdapter(),
    JetechAdapter(),
    HuaHongAdapter(),
    StandardCSVAdapter(),
    GenericTableAdapter(),
)


def _clean_iqr(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    cleaned = frame.copy()
    replacements = 0
    for column in parameter_columns(cleaned):
        numeric = pd.to_numeric(cleaned[column], errors="coerce")
        valid = numeric.dropna()
        if len(valid) < 4:
            cleaned[column] = numeric
            continue
        q1, q3 = valid.quantile([0.25, 0.75])
        iqr = q3 - q1
        if pd.isna(iqr) or iqr <= 0:
            cleaned[column] = numeric
            continue
        outliers = (numeric < q1 - 1.5 * iqr) | (numeric > q3 + 1.5 * iqr)
        replacements += int(outliers.sum())
        cleaned[column] = numeric.mask(outliers)
    return cleaned, replacements


def calculate_yield(frame: pd.DataFrame, pass_bin: int) -> pd.DataFrame:
    if not {"Lot_ID", "Wafer_ID", "Bin"}.issubset(frame.columns):
        return pd.DataFrame()
    data = frame[["Lot_ID", "Wafer_ID", "Bin"]].copy()
    data["Bin"] = pd.to_numeric(data["Bin"], errors="coerce")
    records: list[dict[str, object]] = []
    for (lot_id, wafer_id), group in data.groupby(["Lot_ID", "Wafer_ID"], dropna=False, sort=True):
        gross = len(group)
        good = int((group["Bin"] == pass_bin).sum())
        record: dict[str, object] = {
            "Lot_ID": str(lot_id),
            "Wafer_ID": str(wafer_id),
            "Gross_die": gross,
            "Good_die": good,
            "Yield": good / gross * 100 if gross else np.nan,
        }
        for bin_value, count in group["Bin"].dropna().value_counts().items():
            if bin_value == pass_bin:
                continue
            label = int(bin_value) if float(bin_value).is_integer() else bin_value
            record[f"Bin{label}"] = int(count)
        records.append(record)
    result = pd.DataFrame(records)
    bin_columns = [column for column in result.columns if column.startswith("Bin")]
    if bin_columns:
        result[bin_columns] = result[bin_columns].fillna(0).astype(int)
    return result


def parameter_summary(frame: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for column in parameter_columns(frame):
        values = pd.to_numeric(frame[column], errors="coerce")
        valid = values.dropna()
        if valid.empty:
            continue
        records.append(
            {
                "Parameter": column,
                "Count": int(valid.count()),
                "Missing": int(values.isna().sum()),
                "Mean": valid.mean(),
                "Std": valid.std(),
                "Min": valid.min(),
                "Median": valid.median(),
                "Max": valid.max(),
            }
        )
    return pd.DataFrame(records)


def analyze_source(source: str | Path, clean_outliers: bool = True) -> DataBundle:
    source_path = Path(source).expanduser().resolve()
    files = source_files(source_path)
    if not files:
        raise ValueError("所选位置没有找到支持的 TXT、CSV 或 Excel 文件。")

    adapter = next((candidate for candidate in ADAPTERS if candidate.can_load(files)), None)
    if adapter is None:
        raise ValueError("暂时无法识别该原始格式；请先选择单个表格文件查看内容。")

    capture = io.StringIO()
    with redirect_stdout(capture):
        loaded = adapter.load(source_path, files)

    if isinstance(loaded, DataBundle):
        loaded.metadata.update({"adapter": adapter.name, "source_file_count": len(files)})
        return loaded

    if isinstance(loaded, pd.DataFrame):
        raw_frame = loaded
        pass_bin = 1
        spec = None
        product = None
        lot_id = None
    else:
        raw_frame = _lot_to_frame(loaded)
        pass_bin = int(loaded.pass_bin if loaded.pass_bin is not None else 1)
        spec = _params_to_spec(loaded) if adapter.trustworthy_spec else None
        product = getattr(loaded, "product", None)
        lot_id = getattr(loaded, "lot_id", None)

    if raw_frame.empty:
        raise ValueError(f"{adapter.name} 适配器没有读取到有效 Die 数据。")
    cleaned, replacements = _clean_iqr(raw_frame) if clean_outliers else (raw_frame.copy(), 0)
    yield_data = calculate_yield(cleaned, pass_bin=pass_bin)
    return DataBundle(
        directory=source_path if source_path.is_dir() else source_path.parent,
        files={},
        cleaned=cleaned,
        yield_data=yield_data,
        spec=spec,
        source_kind=adapter.source_kind,
        metadata={
            "adapter": adapter.name,
            "company": adapter.name,
            "product": product,
            "lot_id": lot_id,
            "pass_bin": pass_bin,
            "source_file_count": len(files),
            "raw_rows": len(raw_frame),
            "cleaned_rows": len(cleaned),
            "outlier_replacements": replacements,
            "clean_outliers": clean_outliers,
            "parameter_count": len(parameter_columns(cleaned)),
        },
    )
