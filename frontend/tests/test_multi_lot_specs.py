from __future__ import annotations

import pandas as pd

from frontend.cp_dashboard_app import (
    available_parameters,
    get_spec_info,
    load_standard_dataset,
    scope_dataset_to_lot,
)


def _write_lion_spec(path, upper: float) -> None:
    pd.DataFrame(
        [
            ["Parameter", "TEST_NUM", "PARAM_A"],
            ["UNIT", "", "V"],
            ["LIMIT_LOW", "", 0.0],
            ["LIMIT_HIGH", "", upper],
        ]
    ).to_csv(path, index=False, header=False)


def test_cockpit_scopes_combined_run_to_matching_per_lot_spec(tmp_path) -> None:
    cleaned = pd.DataFrame(
        [
            {
                "Lot_ID": "F10001",
                "Wafer_ID": 1,
                "X": 0,
                "Y": 0,
                "Seq": 1,
                "Bin": 1,
                "SITE_NUM": 1,
                "PART_ID": 1,
                "CONT": True,
                "T_TIME": 1.0,
                "TEST_NUM": 1,
                "PARAM_A": 1.0,
            },
            {
                "Lot_ID": "F20002",
                "Wafer_ID": 1,
                "X": 0,
                "Y": 0,
                "Seq": 1,
                "Bin": 1,
                "SITE_NUM": 1,
                "PART_ID": 1,
                "CONT": True,
                "T_TIME": 1.0,
                "TEST_NUM": 1,
                "PARAM_A": 2.0,
            },
        ]
    )
    yield_df = pd.DataFrame(
        [
            {"Lot_ID": "F10001", "Wafer_ID": 1, "Yield": "100.00%"},
            {"Lot_ID": "F20002", "Wafer_ID": 1, "Yield": "100.00%"},
        ]
    )
    cleaned.to_csv(tmp_path / "F10001_cleaned_20260811_1000.csv", index=False)
    yield_df.to_csv(tmp_path / "F10001_yield_20260811_1000.csv", index=False)
    _write_lion_spec(tmp_path / "F10001_spec_20260811_1000.csv", 2.0)
    _write_lion_spec(tmp_path / "F20002_spec_20260811_1000.csv", 2.5)

    dataset = load_standard_dataset(str(tmp_path))

    assert set(dataset.specs) == {"F10001", "F20002"}
    scoped = scope_dataset_to_lot(dataset, "F20002")
    assert scoped.cleaned["Lot_ID"].unique().tolist() == ["F20002"]
    assert scoped.yield_df["Lot_ID"].unique().tolist() == ["F20002"]
    assert get_spec_info(scoped.spec, "PARAM_A")["limit_upper"] == 2.5
    assert available_parameters(scoped.cleaned) == []


def test_process_fields_are_not_reported_as_measurement_parameters() -> None:
    frame = pd.DataFrame(
        {
            "Lot_ID": ["F10001"] * 3,
            "Wafer_ID": [1] * 3,
            "X": [0, 1, 2],
            "Y": [0, 0, 0],
            "Seq": [1, 2, 3],
            "Bin": [1, 1, 1],
            "SITE_NUM": [1, 1, 1],
            "PART_ID": [1, 2, 3],
            "CONT": [True, True, True],
            "T_TIME": [1.0, 1.0, 1.0],
            "TEST_NUM": [1, 1, 1],
            "PARAM_A": [1.0, 2.0, 3.0],
        }
    )

    assert available_parameters(frame) == ["PARAM_A"]
