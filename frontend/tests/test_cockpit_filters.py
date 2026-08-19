from __future__ import annotations

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

import frontend.cp_dashboard_app as cockpit_app
from frontend.cp_dashboard_app import (
    StandardDataset,
    active_artifact_status_html,
    dataset_lot_ids,
    dataset_wafer_keys,
    filter_standard_dataset,
    wafer_key_label,
)


def test_file_status_is_compact_and_rendered_after_draw_control() -> None:
    html = active_artifact_status_html("FA54-5339_Cockpit & 1.zip")
    assert "font-size:.78rem" in html
    assert "FA54-5339_Cockpit &amp; 1.zip" in html

    source = Path(cockpit_app.__file__).read_text(encoding="utf-8")
    assert source.index('key="draw_analysis_charts"') < source.index("render_file_status(dataset)")


def _dataset() -> StandardDataset:
    cleaned = pd.DataFrame(
        [
            {"Lot_ID": "LOT-A", "Wafer_ID": 1, "X": 0, "Y": 0, "Seq": 1, "Bin": 1, "P1": 1.0},
            {"Lot_ID": "LOT-A", "Wafer_ID": 2, "X": 1, "Y": 0, "Seq": 2, "Bin": 2, "P1": 2.0},
            {"Lot_ID": "LOT-B", "Wafer_ID": 1, "X": 0, "Y": 1, "Seq": 1, "Bin": 1, "P1": 3.0},
            {"Lot_ID": "LOT-B", "Wafer_ID": 3, "X": 1, "Y": 1, "Seq": 2, "Bin": 1, "P1": 4.0},
        ]
    )
    yield_df = pd.DataFrame(
        [
            {"Lot_ID": "LOT-A", "Wafer_ID": 1, "Yield": "100.00%"},
            {"Lot_ID": "LOT-A", "Wafer_ID": 2, "Yield": "50.00%"},
            {"Lot_ID": "LOT-B", "Wafer_ID": 1, "Yield": "100.00%"},
            {"Lot_ID": "LOT-B", "Wafer_ID": 3, "Yield": "100.00%"},
            {"Lot_ID": "ALL", "Wafer_ID": "ALL", "Yield": "87.50%"},
        ]
    )
    return StandardDataset(
        data_dir=Path("output"),
        cleaned_path=None,
        yield_path=None,
        spec_path=None,
        cleaned=cleaned,
        yield_df=yield_df,
        spec=None,
    )


def test_filter_options_use_lot_and_wafer_composite_key() -> None:
    dataset = _dataset()

    assert dataset_lot_ids(dataset) == ["LOT-A", "LOT-B"]
    assert dataset_wafer_keys(dataset) == [
        ("LOT-A", "1"),
        ("LOT-A", "2"),
        ("LOT-B", "1"),
        ("LOT-B", "3"),
    ]
    assert wafer_key_label(("LOT-B", "1")) == "LOT-B / W1"


def test_filter_dataset_supports_one_or_multiple_lots_and_wafers() -> None:
    dataset = _dataset()

    filtered = filter_standard_dataset(
        dataset,
        selected_lots=["LOT-A", "LOT-B"],
        selected_wafers=[("LOT-A", "1"), ("LOT-B", "3")],
    )

    assert list(zip(filtered.cleaned["Lot_ID"], filtered.cleaned["Wafer_ID"])) == [
        ("LOT-A", 1),
        ("LOT-B", 3),
    ]
    assert list(zip(filtered.yield_df["Lot_ID"], filtered.yield_df["Wafer_ID"])) == [
        ("LOT-A", 1),
        ("LOT-B", 3),
    ]
    assert len(dataset.cleaned) == 4
    assert len(dataset.yield_df) == 5


def test_cockpit_filter_controls_default_to_all(tmp_path, monkeypatch) -> None:
    dataset = _dataset()
    dataset.cleaned.to_csv(tmp_path / "LOT-A_cleaned_20260818_1000.csv", index=False)
    dataset.yield_df.to_csv(tmp_path / "LOT-A_yield_20260818_1000.csv", index=False)
    pd.DataFrame(
        [{"Parameter": "P1", "Unit": "V", "LimitL": 0.0, "LimitU": 5.0}]
    ).to_csv(tmp_path / "LOT-A_spec_20260818_1000.csv", index=False)
    monkeypatch.setenv("CP_COCKPIT_DATA_DIR", str(tmp_path))

    app = AppTest.from_file("frontend/cp_dashboard_app.py").run(timeout=20)
    select_all = {widget.label: widget for widget in app.checkbox}

    assert select_all["全选批次"].value is True
    assert select_all["全选片号"].value is True
    assert select_all["全选参数"].value is True
    assert len(app.multiselect) == 0
    assert any("首次打开不会自动生成全部图表" in message.value for message in app.info)
    assert not app.exception

    select_all["全选批次"].set_value(False)
    app.run(timeout=20)
    filters = {widget.label: widget for widget in app.multiselect}
    assert filters["筛选批次"].value == ["LOT-A"]
    assert filters["筛选批次"].options == ["LOT-A", "LOT-B"]

    filters["筛选批次"].set_value(["LOT-B"])
    app.run(timeout=20)
    filters = {widget.label: widget for widget in app.multiselect}

    assert filters["筛选批次"].value == ["LOT-B"]
    assert len(filters) == 1
    assert not app.exception

    buttons = {button.label: button for button in app.button}
    buttons["🎨 绘制图形"].click()
    app.run(timeout=20)

    assert not any("首次打开不会自动生成全部图表" in message.value for message in app.info)
    assert len(app.tabs) == 11
    assert not app.exception

    select_all = {widget.label: widget for widget in app.checkbox}
    select_all["全选批次"].set_value(True)
    app.run(timeout=20)

    assert any("筛选条件已修改" in message.value for message in app.info)
    assert len(app.tabs) == 0
    assert not app.exception
