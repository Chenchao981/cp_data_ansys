from pathlib import Path

import pandas as pd

from web_app.data_service import (
    discover_standard_files,
    dynamic_bin_columns,
    load_bundle,
    normalize_yield_percent,
    parameter_columns,
    parameter_spec,
    wafer_yield_data,
)


def write_contract_files(directory: Path) -> None:
    pd.DataFrame(
        {
            "Lot_ID": ["LOT-A", "LOT-A", "LOT-B"],
            "Wafer_ID": ["01", "02", "01"],
            "X": [1, 2, 3],
            "Y": [1, 2, 3],
            "Seq": [1, 2, 3],
            "Bin": [1, 3, 1],
            "VTH[V]": [2.1, 2.2, 2.3],
        }
    ).to_csv(directory / "LOT_cleaned_20260701_1200.csv", index=False)
    pd.DataFrame(
        {
            "Lot_ID": ["LOT-A", "LOT-A", "LOT-B", "ALL"],
            "Wafer_ID": ["01", "02", "01", "ALL"],
            "Gross_die": [100, 100, 100, 300],
            "Good_die": [99, 98, 97, 294],
            "Yield": ["99%", "0.98", 97, "98%"],
            "Bin3": [1, 2, 3, 6],
            "Bin_8": [0, 0, 1, 1],
        }
    ).to_csv(directory / "LOT_yield_20260701_1200.csv", index=False)
    pd.DataFrame(
        {
            "Parameter": ["VTH[V]"],
            "Unit": ["V"],
            "LimitL": [1.5],
            "LimitU": [3.0],
        }
    ).to_csv(directory / "LOT_spec_20260701_1200.csv", index=False)


def test_load_bundle_and_contract_helpers(tmp_path: Path) -> None:
    write_contract_files(tmp_path)
    files = discover_standard_files(tmp_path)
    assert set(files) == {"cleaned", "yield", "spec"}

    bundle = load_bundle(tmp_path)
    assert bundle.cleaned is not None
    assert parameter_columns(bundle.cleaned) == ["VTH[V]"]
    assert dynamic_bin_columns(bundle.yield_data) == ["Bin3", "Bin_8"]
    assert parameter_spec(bundle.spec, "VTH[V]")["Unit"] == "V"


def test_yield_normalization_handles_percent_and_fraction(tmp_path: Path) -> None:
    write_contract_files(tmp_path)
    bundle = load_bundle(tmp_path)
    wafer_data = wafer_yield_data(bundle.yield_data)
    assert wafer_data["Yield_Numeric"].tolist() == [99.0, 98.0, 97.0]
    assert normalize_yield_percent(pd.Series(["99.5%", 0.975, 97])).tolist() == [99.5, 97.5, 97.0]

