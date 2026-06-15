"""扬州国宇 JUNO DTS-2000 FRD Excel 数据读取器。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

from cp_data_processor.data_models.cp_data import CPLot, CPParameter, CPWafer
from cp_data_processor.readers.base_reader import BaseReader


PARAMETER_DEFINITIONS = [
    ("CONT2[mV]", "mV"),
    ("IR_665V_1[nA]", "nA"),
    ("VZ1[V]", "V"),
    ("VZ2[V]", "V"),
    ("DELTA[V]", "V"),
    ("VF[V]", "V"),
    ("IR_665V_2[nA]", "nA"),
]
PARAMETER_NAMES = [name for name, _unit in PARAMETER_DEFINITIONS]
PARAMETER_UNITS = dict(PARAMETER_DEFINITIONS)
ENGINEERING_FACTORS = {
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "m": 1e-3,
    "": 1.0,
    "k": 1e3,
    "M": 1e6,
}
UNIT_FACTORS = {"V": 1.0, "A": 1.0, "s": 1.0}


def parse_engineering_value(value, target_unit: str) -> float:
    """把 1.2nA、700pA、20mV 等字符串转换为指定工程单位的数值。"""
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        return float(value)

    text = str(value).strip()
    match = re.fullmatch(
        r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*([pnumkM]?)([VAs]?)",
        text,
    )
    if not match:
        return np.nan

    number = float(match.group(1))
    prefix = match.group(2)
    base_unit = match.group(3)
    target_match = re.fullmatch(r"([pnumkM]?)([VAs]?)", target_unit)
    if not target_match:
        raise ValueError(f"不支持的目标单位: {target_unit}")

    target_prefix, target_base_unit = target_match.groups()
    if base_unit and target_base_unit and base_unit != target_base_unit:
        raise ValueError(f"单位不匹配: {text} -> {target_unit}")

    base_value = number * ENGINEERING_FACTORS[prefix] * UNIT_FACTORS.get(base_unit, 1.0)
    target_factor = ENGINEERING_FACTORS[target_prefix] * UNIT_FACTORS.get(target_base_unit, 1.0)
    return base_value / target_factor


class GuoyuFRDReader(BaseReader):
    """读取一个批次目录下的一片或多片国宇 FRD Excel 文件。"""

    def __init__(self, file_paths=None, pass_bin: int = 1, lot_id: Optional[str] = None):
        super().__init__(file_paths or [], pass_bin)
        self.explicit_lot_id = lot_id

    def can_read(self, file_path: str) -> bool:
        try:
            path = Path(file_path)
            if path.suffix.lower() not in {".xls", ".xlsx"}:
                return False
            raw = pd.read_excel(path, sheet_name=0, header=None, nrows=31)
            return (
                str(raw.iloc[0, 0]).startswith("JUNO Test System")
                and raw.iloc[:, 0].astype(str).eq("WaferID").any()
                and raw.iloc[:, 0].astype(str).eq("Serial#").any()
            )
        except Exception:
            return False

    def read(self) -> CPLot:
        if not self.file_paths:
            raise ValueError("没有指定国宇 FRD 数据文件")

        lot_id = self.explicit_lot_id or self._read_file_lot_name(self.file_paths[0])
        lot = CPLot(lot_id=lot_id, product="FRD", pass_bin=self.pass_bin)
        for file_path in sorted(self.file_paths):
            self._extract_from_file(file_path, lot)

        lot.params = self._build_parameters(lot.wafers[0].spec_data)
        lot.update_counts()
        lot.combined_data = pd.concat(
            [wafer.chip_data for wafer in lot.wafers], ignore_index=True
        )
        return lot

    @classmethod
    def _read_file_lot_name(cls, file_path: str) -> str:
        raw = pd.read_excel(file_path, sheet_name=0, header=None, nrows=20)
        return str(cls._metadata_value(raw, "LotName")).strip()

    def read_file(self, file_path: str) -> CPLot:
        return GuoyuFRDReader(
            [file_path], pass_bin=self.pass_bin, lot_id=self.explicit_lot_id
        ).read()

    def _extract_from_file(self, file_path: str, lot: CPLot) -> None:
        raw = pd.read_excel(file_path, sheet_name=0, header=None)
        header_rows = raw.index[raw.iloc[:, 0].astype(str).eq("Serial#")].tolist()
        if not header_rows:
            raise ValueError(f"未找到 Serial# 数据表头: {file_path}")
        header_row = header_rows[0]

        wafer_id = str(int(float(self._metadata_value(raw, "WaferID"))))
        chip_count = int(float(self._metadata_value(raw, "Devices")))
        pass_count = int(float(self._metadata_value(raw, "Pass")))
        fail_count = int(float(self._metadata_value(raw, "Fail")))

        source_headers = raw.iloc[header_row].tolist()
        data = raw.iloc[header_row + 1 :].copy()
        valid_die_rows = data.iloc[:, 0].astype(str).str.fullmatch(r"[PF]\d+", na=False)
        data = data.loc[valid_die_rows].copy()
        if len(data) != chip_count:
            raise ValueError(
                f"有效 Die 行数与 Devices 不一致: {file_path} "
                f"(有效行={len(data)}, Devices={chip_count})"
            )
        data.columns = range(data.shape[1])
        chip_data = pd.DataFrame(
            {
                "Lot_ID": lot.lot_id,
                "Wafer_ID": int(wafer_id),
                "Seq": data.iloc[:, 0].map(self._parse_seq),
                "Bin": pd.to_numeric(data.iloc[:, 1], errors="coerce"),
                "X": pd.to_numeric(data.iloc[:, 2], errors="coerce"),
                "Y": pd.to_numeric(data.iloc[:, 3], errors="coerce"),
            }
        )
        for offset, name in enumerate(PARAMETER_NAMES, start=4):
            chip_data[name] = data.iloc[:, offset].map(
                lambda value, unit=PARAMETER_UNITS[name]: parse_engineering_value(value, unit)
            )

        bin_counts = chip_data["Bin"].value_counts()
        actual_pass_count = int(bin_counts.get(lot.pass_bin, 0))
        actual_fail_count = int(chip_data["Bin"].notna().sum() - actual_pass_count)
        if actual_pass_count != pass_count or actual_fail_count != fail_count:
            raise ValueError(
                f"Bin 统计与文件摘要不一致: {file_path} "
                f"(Bin Pass/Fail={actual_pass_count}/{actual_fail_count}, "
                f"摘要 Pass/Fail={pass_count}/{fail_count})"
            )

        spec_data = self._extract_spec(raw, header_row)
        summary_data = {
            "gross_die": chip_count,
            "good_die": pass_count,
            "yield": f"{pass_count / chip_count * 100:.2f}%",
            "Bin2": fail_count,
        }
        wafer = CPWafer(
            wafer_id=wafer_id,
            file_path=str(file_path),
            source_lot_id=lot.lot_id,
            chip_count=chip_count,
            seq=chip_data["Seq"].to_numpy(),
            bin=chip_data["Bin"].to_numpy(),
            x=chip_data["X"].to_numpy(),
            y=chip_data["Y"].to_numpy(),
            chip_data=chip_data,
            yield_rate=pass_count / chip_count * 100,
            pass_chips=pass_count,
            fail_chips=fail_count,
        )
        wafer.spec_data = spec_data
        wafer.summary_data = summary_data
        wafer.source_headers = source_headers
        lot.wafers.append(wafer)

    @staticmethod
    def _metadata_value(raw: pd.DataFrame, label: str):
        rows = raw.index[raw.iloc[:, 0].astype(str).eq(label)].tolist()
        if not rows:
            raise ValueError(f"缺少元数据字段: {label}")
        values = raw.iloc[rows[0], 1:].dropna()
        if values.empty:
            raise ValueError(f"元数据字段没有值: {label}")
        return values.iloc[0]

    @staticmethod
    def _parse_seq(value) -> float:
        match = re.search(r"(\d+)", str(value))
        return float(match.group(1)) if match else np.nan

    def _extract_spec(self, raw: pd.DataFrame, header_row: int) -> pd.DataFrame:
        spec = {}
        for name, offset in zip(PARAMETER_NAMES, range(4, 11)):
            spec[name] = {
                "Unit": PARAMETER_UNITS[name],
                "LimitL": parse_engineering_value(raw.iloc[header_row - 7, offset], PARAMETER_UNITS[name]),
                "LimitU": parse_engineering_value(raw.iloc[header_row - 6, offset], PARAMETER_UNITS[name]),
                "TestCond": self._join_conditions(raw, header_row, offset),
            }
        return pd.DataFrame(spec)

    @staticmethod
    def _join_conditions(raw: pd.DataFrame, header_row: int, column: int) -> str:
        values = raw.iloc[header_row - 10 : header_row - 7, column].dropna()
        return "; ".join(str(value).strip() for value in values if str(value).strip())

    @staticmethod
    def _build_parameters(spec_data: pd.DataFrame) -> List[CPParameter]:
        params = []
        for name in PARAMETER_NAMES:
            params.append(
                CPParameter(
                    id=name,
                    unit=spec_data.loc["Unit", name],
                    sl=spec_data.loc["LimitL", name],
                    su=spec_data.loc["LimitU", name],
                    test_cond=[spec_data.loc["TestCond", name]],
                )
            )
        return params

    def get_supported_formats(self) -> List[str]:
        return ["GUOYU_FRD_EXCEL"]

    def get_format_description(self) -> str:
        return "扬州国宇 JUNO DTS-2000 FRD Excel 格式"
