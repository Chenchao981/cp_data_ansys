from __future__ import annotations

import pandas as pd
import pytest

from cp_data_processor.data_models.cp_data import CPLot, CPWafer
from cp_data_processor.validation.standard_lot import (
    StandardLotContractError,
    StandardLotValidator,
)


def make_valid_lot() -> CPLot:
    frame = pd.DataFrame(
        {"X": [0], "Y": [1], "Seq": [1], "Bin": [1], "VTH": [2.1]}
    )
    wafer = CPWafer(
        wafer_id="01",
        source_lot_id="LOT-A",
        file_path="sample.xlsx",
        chip_data=frame,
    )
    return CPLot(lot_id="LOT-A", wafers=[wafer], pass_bin=1)


def test_standard_lot_validator_accepts_complete_lot():
    assert StandardLotValidator().validate(make_valid_lot()) == []


def test_standard_lot_validator_rejects_missing_bin():
    lot = make_valid_lot()
    lot.wafers[0].chip_data = lot.wafers[0].chip_data.drop(columns=["Bin"])

    with pytest.raises(StandardLotContractError, match="missing standard fields"):
        StandardLotValidator().validate_or_raise(lot)
