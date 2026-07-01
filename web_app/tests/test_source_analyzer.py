from pathlib import Path

import pandas as pd

from web_app.source_analyzer import (
    analyze_source,
    calculate_yield,
    parameter_summary,
    source_fingerprint,
)


def write_minimal_huahong(path: Path) -> None:
    lines = [
        "Program name\tTEST.dll",
        "Lot number\tLOT-001-A-250101@202",
        "Wafer number\t01",
        "Operator\tTEST",
        "Date\t2026-07-01",
        "Comment\tSynthetic",
        "No.U\tX\tY\tBin\tPARAM1",
        "Unit\t\t\t\tV",
        "LimitU\t\t\t\t20",
        "LimitL\t\t\t\t0",
        "Bias1\t\t\t\t",
        "Bias2\t\t\t\t",
        "Bias3\t\t\t\t",
        "Bias4\t\t\t\t",
        "Data\t\t\t\t",
        "1\t0\t0\t1\t10",
        "2\t1\t0\t3\t11",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def test_raw_huahong_is_analyzed_without_intermediate_csv(tmp_path: Path) -> None:
    source = tmp_path / "PRODUCT_LOT-001@202"
    source.mkdir()
    write_minimal_huahong(source / "LOT-001_001.TXT")

    assert source_fingerprint(source)
    bundle = analyze_source(source, clean_outliers=False)
    assert bundle.source_kind == "huahong_raw"
    assert bundle.cleaned is not None and len(bundle.cleaned) == 2
    assert bundle.yield_data is not None
    assert bundle.yield_data.loc[0, "Gross_die"] == 2
    assert bundle.yield_data.loc[0, "Good_die"] == 1
    assert bundle.yield_data.loc[0, "Yield"] == 50.0
    assert bundle.yield_data.loc[0, "Bin3"] == 1
    assert bundle.spec is None
    assert not list(source.glob("*.csv"))


def test_generic_csv_gets_common_analysis(tmp_path: Path) -> None:
    source = tmp_path / "vendor_unknown.csv"
    pd.DataFrame(
        {
            "LOT_ID": ["L1", "L1", "L1"],
            "WAFER_ID": [1, 1, 1],
            "SOFT_BIN": [2, 2, 5],
            "VALUE": [10.0, 11.0, 12.0],
        }
    ).to_csv(source, index=False)
    bundle = analyze_source(source, clean_outliers=False)
    assert bundle.source_kind == "generic_table"
    assert bundle.cleaned is not None
    assert {"Lot_ID", "Wafer_ID", "Bin"}.issubset(bundle.cleaned.columns)
    result = calculate_yield(bundle.cleaned, pass_bin=2)
    assert result.loc[0, "Good_die"] == 2
    assert result.loc[0, "Bin5"] == 1
    stats = parameter_summary(bundle.cleaned)
    assert "VALUE" in stats["Parameter"].tolist()
