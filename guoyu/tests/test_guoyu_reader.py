from pathlib import Path

import pandas as pd
import pytest

from guoyu.guoyu_reader import GuoyuFRDReader, parse_engineering_value


def test_parse_engineering_value():
    assert parse_engineering_value("01.02mV", "mV") == pytest.approx(1.02)
    assert parse_engineering_value("700.0pA", "nA") == pytest.approx(0.7)
    assert parse_engineering_value("434.4m", "V") == pytest.approx(0.4344)
    assert pd.isna(parse_engineering_value("F Over", "nA"))


def test_sample_batch_contract():
    sample_dir = Path(__file__).parents[2] / "data" / "257375"
    files = sorted(sample_dir.glob("*.xls"))
    if len(files) != 2:
        pytest.skip("本地未提供国宇 257375 脱敏样例")

    lot = GuoyuFRDReader([str(path) for path in files], lot_id="257375").read()

    assert lot.lot_id == "257375"
    assert lot.pass_bin == 1
    assert [wafer.wafer_id for wafer in lot.wafers] == ["1", "2"]
    assert [wafer.chip_count for wafer in lot.wafers] == [3266, 3266]
    assert [wafer.pass_chips for wafer in lot.wafers] == [3244, 3252]
    assert len(lot.combined_data) == 6532
    assert lot.combined_data["Bin"].value_counts().to_dict() == {1: 6496, 2: 36}
    assert lot.combined_data.iloc[0]["CONT2[mV]"] == pytest.approx(1.02)
    assert lot.combined_data.iloc[0]["IR_665V_1[nA]"] == pytest.approx(1.7)
    assert all(
        pd.api.types.is_numeric_dtype(lot.combined_data[column])
        for column in [
            "CONT2[mV]",
            "IR_665V_1[nA]",
            "VZ1[V]",
            "VZ2[V]",
            "DELTA[V]",
            "VF[V]",
            "IR_665V_2[nA]",
        ]
    )
    assert lot.params[0].unit == "mV"
    assert lot.params[0].su == pytest.approx(20.0)


def test_unit_row_is_not_exported_as_die():
    sample_file = (
        Path(__file__).parents[2]
        / "data"
        / "DT8U65AS"
        / "25B103"
        / "EDS"
        / "01#-759.xls"
    )
    if not sample_file.exists():
        pytest.skip("本地未提供国宇 DT8U65AS 三层目录样例")

    lot = GuoyuFRDReader([str(sample_file)], lot_id="25B103").read()

    assert len(lot.combined_data) == 3266
    assert lot.combined_data["Seq"].notna().all()
    assert len(lot.combined_data) == lot.wafers[0].pass_chips + lot.wafers[0].fail_chips
    assert lot.combined_data["Bin"].value_counts().to_dict() == {1: 3226, 2: 39, 4: 1}
