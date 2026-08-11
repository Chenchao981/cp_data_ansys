"""Approved source-to-standard mapping for Lion format 2."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

from cp_data_processor.data_models.cp_data import CPLot, CPWafer
from cp_data_processor.readers.company_adapters.base_company_adapter import (
    BaseCompanyAdapter,
)
from lion.lion_v2_reader import LION_V2_FORMAT, LION_V2_PASS_BIN, LionV2Reader


LION_V2_CONFIG = {
    "name": "立昂微（格式 2）",
    "supported_formats": [LION_V2_FORMAT],
    "default_format": LION_V2_FORMAT,
    "version": "2.0.0",
    "field_mapping": {
        "DUT_NO": "Seq",
        "SOFT_BIN": "Bin",
        "X_COORD": "X",
        "Y_COORD": "Y",
        "PASSFG": "CONT",
    },
    "unit_conversion": {},
}


class LionV2Adapter(BaseCompanyAdapter):
    """Map Lion format 2 source fields without changing values or units."""

    PROCESS_FIELDS = ("SITE_NUM", "PART_ID", "CONT", "T_TIME", "TEST_NUM")

    def __init__(self):
        super().__init__(LION_V2_FORMAT, LION_V2_CONFIG)

    def transform_to_standard_format(self, lot: CPLot) -> CPLot:
        if not self.validate_data_format(lot):
            raise ValueError("Lion format 2 source lot has no usable wafer data")
        if lot.pass_bin != LION_V2_PASS_BIN:
            raise ValueError("Lion format 2 pass_bin must be 1")

        standardized_wafers: list[CPWafer] = []
        all_frames: list[pd.DataFrame] = []
        for source_wafer in lot.wafers:
            source = source_wafer.chip_data
            if source is None:
                raise ValueError(f"Wafer {source_wafer.wafer_id} has no chip data")
            mapped = self.apply_field_mapping(source.copy())
            required = ["X", "Y", "Seq", "Bin"]
            missing = [column for column in required if column not in mapped.columns]
            if missing:
                raise ValueError(f"Lion format 2 standard fields missing: {missing}")

            mapped.insert(0, "Wafer_ID", source_wafer.wafer_id)
            mapped.insert(0, "Lot_ID", source_wafer.source_lot_id or lot.lot_id)
            if mapped.duplicated(["X", "Y"]).any() or mapped["Seq"].duplicated().any():
                raise ValueError("Lion format 2 duplicate Die detected after mapping")

            parameter_names = [parameter.id for parameter in lot.params]
            ordered = ["Lot_ID", "Wafer_ID", "X", "Y", "Seq", "Bin"]
            ordered += [field for field in self.PROCESS_FIELDS if field in mapped.columns]
            ordered += parameter_names
            unexpected = [column for column in mapped.columns if column not in ordered]
            if unexpected:
                raise ValueError(
                    f"Lion format 2 contains unmapped source fields: {unexpected}"
                )
            mapped = mapped[ordered]

            total = len(mapped)
            good = int(mapped["Bin"].eq(LION_V2_PASS_BIN).sum())
            wafer = CPWafer(
                wafer_id=source_wafer.wafer_id,
                file_path=source_wafer.file_path,
                source_lot_id=source_wafer.source_lot_id,
                chip_count=total,
                seq=mapped["Seq"].to_numpy(),
                bin=mapped["Bin"].to_numpy(),
                x=mapped["X"].to_numpy(),
                y=mapped["Y"].to_numpy(),
                chip_data=mapped,
                yield_rate=(good / total * 100) if total else 0.0,
                pass_chips=good,
                fail_chips=total - good,
            )
            if hasattr(source_wafer, "spec_data"):
                wafer.spec_data = source_wafer.spec_data.copy()
            if hasattr(source_wafer, "summary_data"):
                wafer.summary_data = dict(source_wafer.summary_data)
            standardized_wafers.append(wafer)
            all_frames.append(mapped)

        result = CPLot(
            lot_id=lot.lot_id,
            product=lot.product,
            wafer_count=len(standardized_wafers),
            wafers=standardized_wafers,
            param_count=len(lot.params),
            params=lot.params,
            pass_bin=LION_V2_PASS_BIN,
            combined_data=pd.concat(all_frames, ignore_index=True),
        )
        result.source_format = LION_V2_FORMAT
        return result

    def get_field_mapping(self) -> Dict[str, str]:
        return dict(self.field_mapping)

    def can_process_file(self, file_path: str) -> bool:
        return Path(file_path).is_file() and LionV2Reader.can_read(file_path)


__all__ = ["LION_V2_CONFIG", "LionV2Adapter"]
