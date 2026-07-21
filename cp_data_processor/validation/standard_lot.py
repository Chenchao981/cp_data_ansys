"""Validate a :class:`CPLot` before standard CSV generation.

The validator is intentionally company-neutral. Company-specific parsing and
unit rules belong in Readers and Adapters; this module only enforces the stable
handoff contract used by CSV generators and charts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import pandas as pd

from cp_data_processor.data_models.cp_data import CPLot


@dataclass(frozen=True)
class ContractIssue:
    """One machine-readable contract finding."""

    code: str
    message: str
    location: str = "lot"
    severity: str = "error"


class StandardLotContractError(ValueError):
    """Raised when a lot cannot safely enter the standard output pipeline."""

    def __init__(self, issues: Sequence[ContractIssue]):
        self.issues = tuple(issues)
        details = "; ".join(
            f"{issue.location}: {issue.message}" for issue in self.issues
        )
        super().__init__(f"Standard CP contract validation failed: {details}")


class StandardLotValidator:
    """Validate stable fields and traceability for a standard CP lot."""

    DEFAULT_REQUIRED_CHIP_FIELDS = ("X", "Y", "Seq", "Bin")

    def __init__(self, required_chip_fields: Iterable[str] | None = None):
        self.required_chip_fields = tuple(
            required_chip_fields or self.DEFAULT_REQUIRED_CHIP_FIELDS
        )

    def validate(self, lot: CPLot | None) -> list[ContractIssue]:
        issues: list[ContractIssue] = []
        if lot is None:
            return [ContractIssue("lot.missing", "CPLot object is missing")]

        if not str(lot.lot_id or "").strip():
            issues.append(ContractIssue("lot.id_missing", "lot_id is required"))
        if lot.pass_bin is None:
            issues.append(
                ContractIssue("lot.pass_bin_missing", "pass_bin must be explicit")
            )
        if not lot.wafers:
            issues.append(ContractIssue("lot.wafers_missing", "at least one wafer is required"))
            return issues

        seen_wafer_keys: set[tuple[str, str]] = set()
        for index, wafer in enumerate(lot.wafers):
            location = f"wafers[{index}]"
            wafer_id = str(wafer.wafer_id or "").strip()
            source_lot_id = str(wafer.source_lot_id or lot.lot_id or "").strip()

            if not wafer_id:
                issues.append(
                    ContractIssue("wafer.id_missing", "wafer_id is required", location)
                )
            if not source_lot_id:
                issues.append(
                    ContractIssue(
                        "wafer.source_lot_missing",
                        "source_lot_id is required for row-level traceability",
                        location,
                    )
                )
            if not str(wafer.file_path or "").strip():
                issues.append(
                    ContractIssue(
                        "wafer.file_path_missing",
                        "file_path is required for source traceability",
                        location,
                    )
                )

            wafer_key = (source_lot_id, wafer_id)
            if wafer_key in seen_wafer_keys:
                issues.append(
                    ContractIssue(
                        "wafer.duplicate_identity",
                        f"duplicate Lot_ID + Wafer_ID identity {wafer_key!r}",
                        location,
                    )
                )
            seen_wafer_keys.add(wafer_key)

            frame = wafer.chip_data
            if frame is None or frame.empty:
                issues.append(
                    ContractIssue("wafer.data_missing", "chip_data is empty", location)
                )
                continue
            if not isinstance(frame, pd.DataFrame):
                issues.append(
                    ContractIssue(
                        "wafer.data_type",
                        "chip_data must be a pandas DataFrame",
                        location,
                    )
                )
                continue

            duplicate_columns = frame.columns[frame.columns.duplicated()].tolist()
            if duplicate_columns:
                issues.append(
                    ContractIssue(
                        "wafer.duplicate_columns",
                        f"duplicate columns are not allowed: {duplicate_columns}",
                        location,
                    )
                )

            missing_fields = [
                field for field in self.required_chip_fields if field not in frame.columns
            ]
            if missing_fields:
                issues.append(
                    ContractIssue(
                        "wafer.standard_fields_missing",
                        f"missing standard fields: {missing_fields}",
                        location,
                    )
                )
            if "Bin" in frame.columns and frame["Bin"].isna().any():
                issues.append(
                    ContractIssue(
                        "wafer.bin_missing_values",
                        "Bin contains missing values",
                        location,
                    )
                )

        return issues

    def validate_or_raise(self, lot: CPLot | None) -> None:
        issues = [issue for issue in self.validate(lot) if issue.severity == "error"]
        if issues:
            raise StandardLotContractError(issues)
