from __future__ import annotations

import pandas as pd

from frontend.charts.yield_chart import YieldChart


def test_yield_chart_accepts_dynamic_failure_bin_columns(tmp_path) -> None:
    yield_data = pd.DataFrame(
        [
            {
                "Lot_ID": "LOT-A",
                "Wafer_ID": 1,
                "Yield": "99.00%",
                "Bin1": 99,
                "Bin7": "1",
                "Bin10": 2,
            },
            {
                "Lot_ID": "LOT-A",
                "Wafer_ID": 2,
                "Yield": "100.00%",
                "Bin1": 100,
                "Bin7": "0",
                "Bin10": 0,
            },
            {
                "Lot_ID": "ALL",
                "Wafer_ID": "ALL",
                "Yield": "99.50%",
                "Bin1": 199,
                "Bin7": 1,
                "Bin10": 2,
            },
        ]
    )
    yield_data.to_csv(tmp_path / "LOT-A_yield_20260803_120000.csv", index=False)

    chart = YieldChart(tmp_path)

    assert chart.load_data() is True
    assert chart.wafer_data["Total_Failures"].tolist() == [3, 0]

    failure_chart = chart.all_charts_cache["failure_analysis"]
    assert list(failure_chart.data[0].labels) == ["Bin7", "Bin10"]
    assert list(failure_chart.data[0].values) == [1, 2]


def test_failure_bin_detection_excludes_pass_and_non_bin_columns() -> None:
    columns = ["Bin1", "bin 1", "Bin7", "bin 10", "BinFailure", "Yield"]

    assert YieldChart._get_failure_bin_columns(columns) == ["Bin7", "bin 10"]
