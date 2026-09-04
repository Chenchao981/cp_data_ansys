import pandas as pd

from frontend.charts.boxplot_chart import BoxplotChart


def test_boxplot_excludes_optional_process_columns_from_measurements():
    chart = BoxplotChart()
    chart.cleaned_data = pd.DataFrame(
        {
            "Lot_ID": ["L1"],
            "Wafer_ID": [1],
            "X": [0],
            "Y": [0],
            "Seq": [1],
            "Bin": [1],
            "CONT": [1],
            "SITE_NUM": [1],
            "PART_ID": [1],
            "T_TIME": [0.1],
            "TEST_NUM": [2],
            "VTH": [1.5],
        }
    )

    assert chart.get_available_parameters() == ["VTH"]
