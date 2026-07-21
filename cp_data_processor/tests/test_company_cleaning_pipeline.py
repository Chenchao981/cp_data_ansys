from __future__ import annotations

from pathlib import Path

import pandas as pd

from cp_data_processor.data_models.cp_data import CPLot, CPParameter, CPWafer
from cp_data_processor.processing.company_cleaning_pipeline import (
    CompanyCleaningPipeline,
    CompanyCleaningRequest,
)
from cp_data_processor.readers.base_reader import BaseReader
from cp_data_processor.readers.company_adapters.base_company_adapter import (
    BaseCompanyAdapter,
)


class SyntheticReader(BaseReader):
    def read(self) -> CPLot:
        frame = pd.DataFrame(
            {
                "X": [0, 1, 2],
                "Y": [0, 0, 0],
                "Seq": [1, 2, 3],
                "Bin": [2, 1, 2],
                "VTH": [1.0, 99.0, 3.0],
            }
        )
        wafer = CPWafer(
            wafer_id="01",
            source_lot_id="SOURCE-LOT",
            file_path=self.file_paths[0],
            chip_data=frame,
        )
        return CPLot(
            lot_id="RUN-LOT",
            wafers=[wafer],
            params=[CPParameter("VTH", "V", 0.0, 100.0)],
            pass_bin=self.pass_bin,
        )

    def _extract_from_file(self, file_path: str, lot: CPLot) -> None:
        raise NotImplementedError


class SyntheticAdapter(BaseCompanyAdapter):
    def __init__(self):
        super().__init__("SYN", {"field_mapping": {}, "unit_conversion": {}})

    def transform_to_standard_format(self, lot: CPLot) -> CPLot:
        return lot

    def get_field_mapping(self):
        return {}

    def can_process_file(self, file_path: str) -> bool:
        return Path(file_path).suffix == ".xlsx"


def test_pipeline_uses_explicit_pass_bin_and_source_lot(tmp_path):
    source = tmp_path / "sample.xlsx"
    source.touch()
    output = tmp_path / "output"
    pipeline = CompanyCleaningPipeline(SyntheticReader, SyntheticAdapter())

    result = pipeline.run(
        CompanyCleaningRequest(
            company_code="SYN",
            file_paths=[str(source)],
            output_dir=str(output),
            pass_bin=2,
        )
    )

    cleaned = pd.read_csv(result.csv_paths["cleaned"])
    yield_data = pd.read_csv(result.csv_paths["yield"])
    assert cleaned["Lot_ID"].tolist() == ["SOURCE-LOT"] * 3
    assert yield_data.loc[0, "Lot_ID"] == "SOURCE-LOT"
    assert int(yield_data.loc[0, "Good_die"]) == 2
    assert yield_data.loc[0, "Yield"] == "66.67%"
    assert float(yield_data.loc[0, "VTH"]) == 2.0
