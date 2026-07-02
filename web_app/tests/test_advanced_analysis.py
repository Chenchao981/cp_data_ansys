import pandas as pd

from web_app.advanced_charts import (
    bin_pareto,
    capability_metrics,
    correlation_heatmap,
    qq_chart,
    strongest_parameter_pairs,
    wafer_map,
)
from web_app.charts import parameter_wafer_chart


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Lot_ID": ["L1"] * 8,
            "Wafer_ID": ["01"] * 4 + ["02"] * 4,
            "Seq": list(range(1, 9)),
            "Bin": [1, 1, 1, 3, 1, 1, 3, 3],
            "X": [0, 1, 0, 1, 0, 1, 0, 1],
            "Y": [0, 0, 1, 1, 0, 0, 1, 1],
            "P1": [9.8, 10.0, 10.1, 10.2, 9.9, 10.0, 10.1, 10.3],
            "P2": [20.1, 20.0, 19.9, 19.8, 20.2, 20.1, 20.0, 19.9],
        }
    )


def test_capability_metrics_calculate_cp_cpk_pp_ppk() -> None:
    metrics = capability_metrics(sample_frame(), "P1", lsl=9.0, usl=11.0)
    assert metrics["Count"] == 8
    assert metrics["Cp"] is not None and metrics["Cp"] > 0
    assert metrics["Cpk"] is not None and metrics["Cpk"] > 0
    assert metrics["Pp"] is not None and metrics["Pp"] > 0
    assert metrics["Ppk"] is not None and metrics["Ppk"] > 0


def test_advanced_figures_preserve_source_rows() -> None:
    frame = sample_frame()
    original = frame.copy(deep=True)
    map_figure = wafer_map(frame, "01", "Bin", pass_bin=1)
    heatmap = correlation_heatmap(frame, ["P1", "P2"])
    pareto = bin_pareto(pd.Series({"Bin3": 3, "Bin8": 1}))
    assert len(map_figure.data) >= 1
    assert len(heatmap.data) == 1
    assert len(pareto.data) == 2
    pd.testing.assert_frame_equal(frame, original)


def test_empty_qq_and_zero_sigma_capability_are_safe() -> None:
    empty_figure = qq_chart(pd.DataFrame({"P1": [None, None]}), "P1")
    metrics = capability_metrics(
        pd.DataFrame({"Wafer_ID": ["01", "01"], "P1": [10.0, 10.0]}),
        "P1",
        lsl=9.0,
        usl=11.0,
    )
    assert len(empty_figure.layout.annotations) == 1
    assert metrics["Cp"] is None
    assert metrics["Cpk"] is None


def test_parameter_wafer_chart_uses_fixed_wafer_axis_and_spec_lines() -> None:
    frame = sample_frame()
    original = frame.copy(deep=True)
    figure = parameter_wafer_chart(
        frame,
        "P1",
        {"Unit": "V", "LimitL": 9.0, "LimitU": 11.0, "Target": 10.0},
    )
    assert figure.layout.xaxis.title.text == "Wafer_ID"
    assert figure.layout.yaxis.title.text == "P1 [V]"
    assert list(figure.layout.xaxis.ticktext) == ["01", "02"]
    assert list(figure.layout.xaxis.range) == [-0.5, 1.5]
    assert list(figure.layout.yaxis.range) == [8.8, 11.2]
    assert len(figure.layout.shapes) == 3
    assert {trace.type for trace in figure.data} == {"box", "scattergl"}
    pd.testing.assert_frame_equal(frame, original)


def test_strongest_parameter_pairs_are_automatic() -> None:
    pairs = strongest_parameter_pairs(sample_frame(), ["P1", "P2"], limit=6)
    assert len(pairs) == 1
    assert pairs[0][:2] == ("P1", "P2")


def test_parameter_wafer_chart_marks_iqr_outliers_with_open_circles() -> None:
    frame = pd.DataFrame(
        {
            "Lot_ID": ["L1@202"] * 10,
            "Wafer_ID": ["01"] * 10,
            "P1": [1.0] * 9 + [10.0],
        }
    )
    figure = parameter_wafer_chart(frame, "P1")
    open_circle_traces = [
        trace for trace in figure.data if trace.type == "scattergl" and trace.marker.symbol == "circle-open"
    ]
    assert len(open_circle_traces) == 1
    assert list(open_circle_traces[0].y) == [10.0]
