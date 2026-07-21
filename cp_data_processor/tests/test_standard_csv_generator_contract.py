from __future__ import annotations

import pandas as pd

from cp_data_processor.data_models.cp_data import CPLot, CPParameter, CPWafer
from cp_data_processor.processing.standard_csv_generator import StandardCSVGenerator


def make_lot(container_id: str, source_id: str, pass_bin: int, bins: list[int]) -> CPLot:
    frame = pd.DataFrame(
        {
            "X": list(range(len(bins))),
            "Y": [0] * len(bins),
            "Seq": list(range(1, len(bins) + 1)),
            "Bin": bins,
            "VTH": [1.0] * len(bins),
        }
    )
    wafer = CPWafer(
        wafer_id="01",
        source_lot_id=source_id,
        file_path=f"{source_id}.xlsx",
        chip_data=frame,
    )
    return CPLot(
        lot_id=container_id,
        wafers=[wafer],
        params=[CPParameter("VTH", "V", 0.0, 2.0)],
        pass_bin=pass_bin,
    )


def test_combined_csvs_preserve_source_lot_and_each_lot_pass_bin(tmp_path):
    lots = {
        "one": make_lot("RUN-1", "SOURCE-1", 2, [2, 1]),
        "two": make_lot("RUN-2", "SOURCE-2", 3, [3, 3]),
    }

    paths = StandardCSVGenerator().generate_combined_standard_csvs(
        lots, str(tmp_path), combined_name="combined"
    )

    cleaned = pd.read_csv(paths["cleaned"])
    yield_data = pd.read_csv(paths["yield"]).set_index("Lot_ID")
    assert set(cleaned["Lot_ID"]) == {"SOURCE-1", "SOURCE-2"}
    assert int(yield_data.loc["SOURCE-1", "Good_die"]) == 1
    assert int(yield_data.loc["SOURCE-2", "Good_die"]) == 2
