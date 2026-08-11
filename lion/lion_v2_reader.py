"""Deterministic reader for the approved Lion format 2 export.

This reader deliberately accepts only the profiled OLE ``.xls`` structure.  It
does not fall back to filename-only detection or infer missing business rules.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from cp_data_processor.data_models.cp_data import CPLot, CPParameter, CPWafer
from cp_data_processor.readers.base_reader import BaseReader


LION_V2_FORMAT = "LION_V2"
LION_V2_PASS_BIN = 1
OLE_SIGNATURE = bytes.fromhex("d0cf11e0a1b11ae1")
EXPECTED_SHEETS = (
    "Summary information",
    "Statistics Information",
    "DUT_DATA",
)
FILE_NAME_PATTERN = re.compile(r"^(?P<lot>F[0-9]+)_(?P<wafer>[0-9]+)\.xls$")
SOURCE_PREFIX_COLUMNS = (
    "SITE_NUM",
    "DUT_NO",
    "PART_ID",
    "PASSFG",
    "SOFT_BIN",
    "T_TIME",
    "X_COORD",
    "Y_COORD",
    "TEST_NUM",
)
REQUIRED_SOURCE_COLUMNS = (
    "DUT_NO",
    "PART_ID",
    "PASSFG",
    "SOFT_BIN",
    "X_COORD",
    "Y_COORD",
    "TEST_NUM",
)
EXPECTED_PARAMETER_COUNT = 15


class LionV2FormatError(ValueError):
    """Raised when a file violates the approved Lion format 2 contract."""


class LionV2Reader(BaseReader):
    """Read the approved three-sheet Lion OLE ``.xls`` format."""

    def __init__(self, file_paths=None, pass_bin: int = LION_V2_PASS_BIN):
        super().__init__(file_paths or [], pass_bin)
        if pass_bin != LION_V2_PASS_BIN:
            raise LionV2FormatError(
                f"Lion format 2 requires pass_bin={LION_V2_PASS_BIN}, got {pass_bin}"
            )

    @staticmethod
    def _has_ole_signature(path: Path) -> bool:
        try:
            with path.open("rb") as handle:
                return handle.read(len(OLE_SIGNATURE)) == OLE_SIGNATURE
        except OSError:
            return False

    @classmethod
    def _inspect_workbook_structure(cls, path: Path) -> bool:
        workbook = pd.ExcelFile(path)
        if tuple(workbook.sheet_names) != EXPECTED_SHEETS:
            return False
        preview = pd.read_excel(
            workbook,
            sheet_name="DUT_DATA",
            header=None,
            nrows=5,
        )
        return cls.matches_approved_structure(preview)

    @classmethod
    def matches_approved_structure(cls, dut_preview: pd.DataFrame) -> bool:
        """Return whether a bounded DUT_DATA preview matches format 2."""

        if len(dut_preview) < 5:
            return False
        headers = cls._header_values(dut_preview.iloc[0])
        if len(headers) != len(set(headers)) or any(not name for name in headers):
            return False
        if tuple(headers[: len(SOURCE_PREFIX_COLUMNS)]) != SOURCE_PREFIX_COLUMNS:
            return False
        if len(headers) - len(SOURCE_PREFIX_COLUMNS) != EXPECTED_PARAMETER_COUNT:
            return False
        if not all(column in headers for column in REQUIRED_SOURCE_COLUMNS):
            return False
        if str(dut_preview.iloc[1, 0]).strip() != "Unit":
            return False
        if str(dut_preview.iloc[2, 0]).strip() != "LimitL":
            return False
        if str(dut_preview.iloc[3, 0]).strip() != "LimitU":
            return False
        return bool(dut_preview.iloc[4].isna().all())

    @classmethod
    def can_read(cls, file_path: str) -> bool:
        path = Path(file_path)
        if not path.is_file() or FILE_NAME_PATTERN.fullmatch(path.name) is None:
            return False
        if not cls._has_ole_signature(path):
            return False
        try:
            return cls._inspect_workbook_structure(path)
        except Exception:
            return False

    def read_file(self, file_path: str) -> CPLot:
        return LionV2Reader([file_path], pass_bin=self.pass_bin).read()

    def read(self) -> CPLot:
        if not self.file_paths:
            raise LionV2FormatError("No Lion format 2 files were provided")

        lot = CPLot(pass_bin=self.pass_bin)
        for file_path in self.file_paths:
            self._extract_from_file(file_path, lot)

        lot.update_counts()
        lot.combined_data = pd.concat(
            [wafer.chip_data for wafer in lot.wafers], ignore_index=True
        )
        lot.source_format = LION_V2_FORMAT
        return lot

    def _extract_from_file(self, file_path: str, lot: CPLot) -> None:
        path = Path(file_path)
        if not self.can_read(str(path)):
            raise LionV2FormatError(
                f"Unknown or unsupported Lion format 2 file: {path.name}"
            )

        workbook = pd.ExcelFile(path)
        summary_frame = pd.read_excel(
            workbook, sheet_name="Summary information", header=None
        )
        statistics_frame = pd.read_excel(
            workbook, sheet_name="Statistics Information", header=None
        )
        dut_frame = pd.read_excel(workbook, sheet_name="DUT_DATA", header=None)
        parsed = self.parse_frames(
            path,
            summary_frame=summary_frame,
            statistics_frame=statistics_frame,
            dut_frame=dut_frame,
        )
        self._merge_single_file_lot(lot, parsed)

    def parse_frames(
        self,
        file_path: str | Path,
        *,
        summary_frame: pd.DataFrame,
        statistics_frame: pd.DataFrame,
        dut_frame: pd.DataFrame,
    ) -> CPLot:
        """Parse already-loaded workbook frames using the production rules.

        Keeping frame parsing separate from Excel I/O makes every business rule
        directly testable with synthetic, non-customer data.
        """

        path = Path(file_path)
        match = FILE_NAME_PATTERN.fullmatch(path.name)
        if match is None:
            raise LionV2FormatError(f"Invalid Lion format 2 filename: {path.name}")
        if not self.matches_approved_structure(dut_frame.iloc[:5]):
            raise LionV2FormatError("DUT_DATA does not match the approved structure")

        summary_lines = self._single_column_lines(summary_frame)
        product = self._required_summary_value(summary_lines, "DUT Name")
        summary_lot = self._required_summary_value(summary_lines, "Lot Id")
        summary_wafer = self._required_summary_value(summary_lines, "WAFER_ID")
        directory_lot = path.parent.name
        filename_lot = match.group("lot")
        wafer_id = match.group("wafer")

        if re.fullmatch(r"F[0-9]+--", summary_lot) is None:
            raise LionV2FormatError(
                "Summary Lot Id must end with exactly the approved '--' filler"
            )
        normalized_summary_lot = summary_lot[:-2]
        if not directory_lot or directory_lot != filename_lot:
            raise LionV2FormatError(
                "Lot identity mismatch between directory and filename"
            )
        if normalized_summary_lot != directory_lot:
            raise LionV2FormatError(
                "Lot identity mismatch between directory and Summary information"
            )
        if not summary_wafer.isdigit() or int(summary_wafer) != int(wafer_id):
            raise LionV2FormatError(
                "Wafer identity mismatch between filename and Summary information"
            )

        headers = self._header_values(dut_frame.iloc[0])
        spec_data = dut_frame.iloc[1:4].copy()
        spec_data.columns = headers
        spec_data.index = ["UNIT", "LIMIT_LOW", "LIMIT_HIGH"]

        data = dut_frame.iloc[5:].copy()
        data.columns = headers
        if data.empty:
            raise LionV2FormatError("DUT_DATA contains no Die rows")
        if data.isna().all(axis=1).any():
            raise LionV2FormatError(
                "Unexpected blank row found inside the DUT_DATA Die region"
            )

        parameter_columns = headers[headers.index("TEST_NUM") + 1 :]
        data = self._normalize_die_data(data, parameter_columns)
        self._validate_die_rows(data)
        summary_data = self._validate_summary_counts(summary_lines, data)
        self._validate_statistics_sheet(statistics_frame)

        params = self._build_parameters(spec_data, parameter_columns)
        wafer = CPWafer(
            wafer_id=str(int(wafer_id)),
            file_path=str(path),
            source_lot_id=directory_lot,
            chip_count=len(data),
            seq=data["DUT_NO"].to_numpy(),
            bin=data["SOFT_BIN"].to_numpy(),
            x=data["X_COORD"].to_numpy(),
            y=data["Y_COORD"].to_numpy(),
            chip_data=data,
            yield_rate=summary_data["yield_rate"],
            pass_chips=summary_data["good_die"],
            fail_chips=summary_data["fail_die"],
        )
        wafer.spec_data = spec_data
        wafer.summary_data = summary_data

        parsed = CPLot(
            lot_id=directory_lot,
            product=product,
            wafer_count=1,
            wafers=[wafer],
            param_count=len(params),
            params=params,
            pass_bin=LION_V2_PASS_BIN,
            combined_data=data.copy(),
        )
        parsed.source_format = LION_V2_FORMAT
        return parsed

    @staticmethod
    def _header_values(row: pd.Series) -> list[str]:
        return ["" if pd.isna(value) else str(value).strip() for value in row]

    @staticmethod
    def _single_column_lines(frame: pd.DataFrame) -> list[str]:
        if frame.empty or frame.shape[1] != 1:
            raise LionV2FormatError("Expected a single-column information sheet")
        return [str(value).strip() for value in frame.iloc[:, 0].dropna()]

    @staticmethod
    def _required_summary_value(lines: Iterable[str], label: str) -> str:
        prefix = f"{label}:"
        matches = [line[len(prefix) :].strip() for line in lines if line.startswith(prefix)]
        if len(matches) != 1 or not matches[0]:
            raise LionV2FormatError(
                f"Summary information must contain exactly one non-empty {label}"
            )
        return matches[0]

    @staticmethod
    def _integer_series(frame: pd.DataFrame, column: str) -> pd.Series:
        values = pd.to_numeric(frame[column], errors="coerce")
        if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
            raise LionV2FormatError(f"{column} contains missing or non-numeric values")
        if not np.equal(values.to_numpy(), np.floor(values.to_numpy())).all():
            raise LionV2FormatError(f"{column} must contain integer values")
        return values.astype("int64")

    def _normalize_die_data(
        self, data: pd.DataFrame, parameter_columns: list[str]
    ) -> pd.DataFrame:
        normalized = data.reset_index(drop=True).copy()
        for column in (
            "SITE_NUM",
            "DUT_NO",
            "PART_ID",
            "SOFT_BIN",
            "X_COORD",
            "Y_COORD",
            "TEST_NUM",
        ):
            normalized[column] = self._integer_series(normalized, column)

        test_time = pd.to_numeric(normalized["T_TIME"], errors="coerce")
        if test_time.isna().any() or not np.isfinite(test_time.to_numpy()).all():
            raise LionV2FormatError("T_TIME contains missing or non-numeric values")
        normalized["T_TIME"] = test_time

        pass_values = normalized["PASSFG"]
        normalized_pass = pass_values.map(
            lambda value: value
            if isinstance(value, (bool, np.bool_))
            else str(value).strip().lower() in {"true", "1", "1.0"}
        )
        accepted_pass_text = pass_values.map(
            lambda value: isinstance(value, (bool, np.bool_))
            or str(value).strip().lower() in {"true", "false", "1", "0", "1.0", "0.0"}
        )
        if not accepted_pass_text.all():
            raise LionV2FormatError("PASSFG contains an unapproved marker")
        normalized["PASSFG"] = normalized_pass.astype(bool)

        for column in parameter_columns:
            source = normalized[column]
            numeric = pd.to_numeric(source, errors="coerce")
            nonblank = source.notna() & source.astype(str).str.strip().ne("")
            if (nonblank & numeric.isna()).any():
                raise LionV2FormatError(
                    f"Measurement {column} contains an unapproved text marker"
                )
            finite_values = numeric.dropna().to_numpy(dtype=float)
            if finite_values.size and not np.isfinite(finite_values).all():
                raise LionV2FormatError(
                    f"Measurement {column} contains a non-finite numeric value"
                )
            normalized[column] = numeric
        return normalized

    @staticmethod
    def _validate_die_rows(data: pd.DataFrame) -> None:
        if not data["DUT_NO"].equals(data["PART_ID"]):
            raise LionV2FormatError("DUT_NO and PART_ID do not match")
        if data["DUT_NO"].duplicated().any():
            raise LionV2FormatError("Duplicate Seq/DUT_NO found in one wafer")
        if data.duplicated(["X_COORD", "Y_COORD"]).any():
            raise LionV2FormatError("Duplicate X_COORD + Y_COORD found in one wafer")
        expected_pass = data["SOFT_BIN"].eq(LION_V2_PASS_BIN)
        if not expected_pass.equals(data["PASSFG"]):
            raise LionV2FormatError("PASSFG conflicts with SOFT_BIN and pass_bin=1")

    @staticmethod
    def _summary_integer(lines: list[str], label: str) -> int:
        pattern = re.compile(rf"^{re.escape(label)}:\s*([0-9]+)(?:\s|$)")
        matches = [int(match.group(1)) for line in lines if (match := pattern.match(line))]
        if len(matches) != 1:
            raise LionV2FormatError(f"Summary information must contain one {label} count")
        return matches[0]

    def _validate_summary_counts(
        self, lines: list[str], data: pd.DataFrame
    ) -> dict[str, object]:
        total = self._summary_integer(lines, "Total")
        passed = self._summary_integer(lines, "Pass")
        failed = self._summary_integer(lines, "Fail")
        actual_pass = int(data["SOFT_BIN"].eq(LION_V2_PASS_BIN).sum())
        if (total, passed, failed) != (len(data), actual_pass, len(data) - actual_pass):
            raise LionV2FormatError(
                "Summary Total/Pass/Fail does not reconcile to DUT_DATA"
            )
        if not any(line.startswith("SBin[1]") and "Pass__Default" in line for line in lines):
            raise LionV2FormatError("Summary does not declare SBin[1] Pass__Default")

        param_counts: dict[str, int] = {}
        pattern = re.compile(r"^SBin\[[0-9]+\]\s+(\w+)__AllFail\s+([0-9]+)")
        for line in lines:
            match = pattern.match(line)
            if match:
                param_counts[match.group(1)] = int(match.group(2))
        return {
            "gross_die": total,
            "good_die": passed,
            "fail_die": failed,
            "yield": f"{(passed / total * 100) if total else 0:.2f}%",
            "yield_rate": (passed / total * 100) if total else 0.0,
            "param_counts": param_counts,
        }

    @staticmethod
    def _validate_statistics_sheet(frame: pd.DataFrame) -> None:
        # The approved profile makes Statistics content a reconciliation-only,
        # optional signature.  Enforce only its observed one-column structure;
        # never use it to replace DUT_DATA values, Bin, units, or specifications.
        if frame.empty or frame.shape[1] != 1:
            raise LionV2FormatError(
                "Statistics Information must remain a one-column reconciliation sheet"
            )

    @staticmethod
    def _build_parameters(
        spec_data: pd.DataFrame, parameter_columns: list[str]
    ) -> list[CPParameter]:
        params: list[CPParameter] = []
        for column in parameter_columns:
            unit_value = spec_data.loc["UNIT", column]
            unit = None if pd.isna(unit_value) else str(unit_value).strip() or None
            lower = LionV2Reader._optional_numeric_spec(
                spec_data.loc["LIMIT_LOW", column], column, "LimitL"
            )
            upper = LionV2Reader._optional_numeric_spec(
                spec_data.loc["LIMIT_HIGH", column], column, "LimitU"
            )
            params.append(
                CPParameter(
                    id=column,
                    unit=unit,
                    sl=lower,
                    su=upper,
                )
            )
        return params

    @staticmethod
    def _optional_numeric_spec(value, parameter: str, row_name: str) -> float | None:
        if pd.isna(value) or not str(value).strip():
            return None
        numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.isna(numeric) or not np.isfinite(float(numeric)):
            raise LionV2FormatError(
                f"{row_name} for {parameter} is not a finite numeric specification"
            )
        return float(numeric)

    @staticmethod
    def _parameter_signature(params: list[CPParameter]) -> tuple:
        return tuple((p.id, p.unit, p.sl, p.su, tuple(p.test_cond)) for p in params)

    def _merge_single_file_lot(self, target: CPLot, source: CPLot) -> None:
        if not target.wafers:
            target.lot_id = source.lot_id
            target.product = source.product
            target.params = source.params
        else:
            if source.lot_id != target.lot_id:
                raise LionV2FormatError("One LionV2Reader instance cannot merge multiple lots")
            if source.product != target.product:
                raise LionV2FormatError("Product identity differs within one Lion lot")
            if self._parameter_signature(source.params) != self._parameter_signature(
                target.params
            ):
                raise LionV2FormatError("Specifications differ within one Lion lot")
        target.wafers.extend(source.wafers)


__all__ = [
    "LION_V2_FORMAT",
    "LION_V2_PASS_BIN",
    "LionV2FormatError",
    "LionV2Reader",
]
