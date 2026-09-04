from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from lion.lion_reader import LionExcelReader, LionV1FormatError
from lion_batch_processor import (
    LION_V1_FORMAT,
    create_batch_lot,
    detect_lion_format,
    generate_lion_run_csvs,
    process_lion_batch_files,
)


FIXED_COLUMNS = [
    "SITE_NUM",
    "PART_INDEX",
    "PASSFG",
    "SOFT_BIN",
    "T_TIME",
    "X_COORD",
    "Y_COORD",
    "TEST_NUM",
]


def _write_lion_v1(
    root: Path,
    lot_id: str,
    wafer_id: int,
    specs: list[tuple[str, str, float, float]],
    *,
    conflict_text: str | None = None,
    duplicate_coordinate: bool = False,
) -> Path:
    lot_dir = root / lot_id
    lot_dir.mkdir(parents=True, exist_ok=True)
    path = lot_dir / f"{lot_id}_{wafer_id}.xlsx"

    summary_rows = [f"row-{index}" for index in range(24)]
    summary_rows[0] = "STS8200 StationA"
    summary_rows[4] = "Program:Z:\\F0098\\F0098.pgs"
    summary_rows[7] = f"Lot Id:{lot_id}--"
    summary_rows[10] = "DUT Name:F0098A1"
    summary_rows[12] = f"WAFER_ID:{wafer_id}"
    summary_rows[20] = "Total: 2"
    summary_rows[21] = "Pass: 1   50.00%"
    summary_rows[22] = "Fail: 1   50.00%"

    columns = FIXED_COLUMNS + [item[0] for item in specs]
    unit_row = ["UNIT", None, None, None, None, None, None, None]
    unit_row += [item[1] for item in specs]
    low_row = ["LIMIT_LOW", None, None, None, None, None, None, None]
    low_row += [item[2] for item in specs]
    high_row = ["LIMIT_HIGH", None, None, None, None, None, None, None]
    high_row += [item[3] for item in specs]

    first_xy = (0, 0)
    second_xy = first_xy if duplicate_coordinate else (1, 0)
    row1 = [1, 1, 1, 1, 1.0, *first_xy, len(specs)]
    row1 += [float(index + 1) for index in range(len(specs))]
    row2 = [1, 2, 0, 7, 1.0, *second_xy, len(specs)]
    row2 += [float(index + 2) for index in range(len(specs))]
    if conflict_text is not None:
        row2[len(FIXED_COLUMNS)] = conflict_text

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(summary_rows).to_excel(
            writer,
            sheet_name="summary_information",
            index=False,
            header=False,
        )
        pd.DataFrame(
            [unit_row, low_row, high_row, row1, row2],
            columns=columns,
        ).to_excel(writer, sheet_name="dut_data", index=False)
    return path


def test_dynamic_parameter_add_remove_merges_union_and_outputs_nulls(tmp_path):
    first = _write_lion_v1(
        tmp_path,
        "F10001",
        1,
        [("PARAM_A", "V", 0.0, 5.0), ("COMMON", "uA", 0.0, 1.0)],
    )
    second = _write_lion_v1(
        tmp_path,
        "F10001",
        2,
        [("COMMON", "uA", 0.0, 1.0), ("PARAM_B", "mV", -1.0, 2.0)],
    )

    assert detect_lion_format(str(first)) == LION_V1_FORMAT
    lots = process_lion_batch_files([str(first), str(second)])
    batch = create_batch_lot(lots)

    assert [parameter.id for parameter in batch.params] == [
        "TEST_NUM",
        "PARAM_A",
        "COMMON",
        "PARAM_B",
    ]
    assert batch.wafers[0].file_path == str(first)
    assert batch.wafers[0].source_lot_id == "F10001"

    outputs = generate_lion_run_csvs([batch], str(tmp_path / "output"))
    cleaned = pd.read_csv(outputs["cleaned"])
    spec = pd.read_csv(outputs["spec"], header=None)

    assert len(cleaned) == 4
    assert cleaned.loc[cleaned["Wafer_ID"] == 1, "PARAM_B"].isna().all()
    assert cleaned.loc[cleaned["Wafer_ID"] == 2, "PARAM_A"].isna().all()
    assert spec.iloc[0].tolist() == [
        "Parameter",
        "TEST_NUM",
        "PARAM_A",
        "COMMON",
        "PARAM_B",
    ]
    assert float(spec.iloc[2, 4]) == -1.0


def test_dynamic_parameter_same_name_spec_conflict_names_both_files(tmp_path):
    first = _write_lion_v1(
        tmp_path,
        "F10001",
        1,
        [("COMMON", "uA", 0.0, 1.0)],
    )
    second = _write_lion_v1(
        tmp_path,
        "F10001",
        2,
        [("COMMON", "uA", 0.0, 2.0)],
    )
    lots = process_lion_batch_files([str(first), str(second)])

    with pytest.raises(ValueError, match=r"COMMON 规格冲突.*F10001_1.xlsx.*F10001_2.xlsx"):
        create_batch_lot(lots)


def test_multi_lot_v1_keeps_conflicting_specs_isolated_per_lot(tmp_path):
    first = _write_lion_v1(
        tmp_path,
        "F10001",
        1,
        [("VF1", "V", 1.0, 1.2), ("PARAM_A", "uA", 0.0, 1.0)],
    )
    second = _write_lion_v1(
        tmp_path,
        "F20002",
        1,
        [("VF1", "V", 0.5, 1.3), ("PARAM_B", "mV", -1.0, 2.0)],
    )
    first_batch = create_batch_lot(process_lion_batch_files([str(first)]))
    second_batch = create_batch_lot(process_lion_batch_files([str(second)]))

    outputs = generate_lion_run_csvs(
        [first_batch, second_batch],
        str(tmp_path / "output"),
    )

    assert "spec" not in outputs
    assert set(outputs["specs"]) == {"F10001", "F20002"}
    cleaned = pd.read_csv(outputs["cleaned"])
    yield_df = pd.read_csv(outputs["yield"])
    assert set(cleaned["Lot_ID"].astype(str)) == {"F10001", "F20002"}
    assert set(yield_df["Lot_ID"].astype(str)) == {"F10001", "F20002"}
    assert cleaned.loc[cleaned["Lot_ID"] == "F10001", "PARAM_B"].isna().all()
    assert cleaned.loc[cleaned["Lot_ID"] == "F20002", "PARAM_A"].isna().all()

    specs = {
        lot_id: pd.read_csv(path, header=None)
        for lot_id, path in outputs["specs"].items()
    }
    first_vf1 = specs["F10001"].columns[specs["F10001"].iloc[0] == "VF1"][0]
    second_vf1 = specs["F20002"].columns[specs["F20002"].iloc[0] == "VF1"][0]
    assert float(specs["F10001"].iloc[2, first_vf1]) == 1.0
    assert float(specs["F10001"].iloc[3, first_vf1]) == 1.2
    assert float(specs["F20002"].iloc[2, second_vf1]) == 0.5
    assert float(specs["F20002"].iloc[3, second_vf1]) == 1.3


def test_dynamic_parameter_rejects_nonnumeric_text_and_duplicate_die(tmp_path):
    invalid = _write_lion_v1(
        tmp_path / "invalid",
        "F10001",
        1,
        [("PARAM_A", "V", 0.0, 5.0)],
        conflict_text="OVER",
    )
    with pytest.raises(LionV1FormatError, match="未批准的非数值内容"):
        LionExcelReader().read_file(str(invalid))

    duplicate = _write_lion_v1(
        tmp_path / "duplicate",
        "F10001",
        1,
        [("PARAM_A", "V", 0.0, 5.0)],
        duplicate_coordinate=True,
    )
    with pytest.raises(LionV1FormatError, match="重复 X_COORD"):
        LionExcelReader().read_file(str(duplicate))
