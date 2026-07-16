from __future__ import annotations

import pandas as pd
import pytest

from frontend.charts.wafer_mapping import (
    has_spatial_coordinates,
    prepare_wafer_mapping,
    wafer_mapping_grid,
    wafer_mapping_summary,
)


def sample_cleaned() -> pd.DataFrame:
    rows = []
    seq = 1
    for lot_id in ("LOT-A", "LOT-B"):
        for wafer_id in (1, 2):
            for x in (-1, 0, 1):
                for y in (-1, 0, 1):
                    rows.append(
                        {
                            "Lot_ID": lot_id,
                            "Wafer_ID": wafer_id,
                            "X": x,
                            "Y": y,
                            "Seq": seq,
                            "Bin": 2 if (x, y) == (1, 1) else 1,
                            "BVDSS": 100 + x * 10 + y * 5,
                        }
                    )
                    seq += 1
    return pd.DataFrame(rows)


def test_bin_mapping_keeps_same_wafer_id_separate_across_lots() -> None:
    result = prepare_wafer_mapping(sample_cleaned(), pass_bin=1)
    summary = wafer_mapping_summary(result)

    assert summary["wafers"] == 4
    assert summary["judged"] == 36
    assert summary["fail"] == 4
    assert set(result.data["_Status_Code"]) == {1, 2}


def test_parameter_mapping_marks_low_and_high_spec_failures() -> None:
    result = prepare_wafer_mapping(
        sample_cleaned(),
        parameter="BVDSS",
        spec_info={"unit": "V", "limit_lower": 90, "limit_upper": 110},
    )

    assert (result.data["_Status_Code"] == 2).sum() == 4
    assert (result.data["_Status_Code"] == 3).sum() == 4
    assert wafer_mapping_summary(result)["fail"] == 8


def test_parameter_mapping_rejects_missing_or_reversed_spec() -> None:
    cleaned = sample_cleaned()

    with pytest.raises(ValueError, match="没有可用的 LSL/USL"):
        prepare_wafer_mapping(cleaned, parameter="BVDSS", spec_info={})

    with pytest.raises(ValueError, match="规格方向异常"):
        prepare_wafer_mapping(
            cleaned,
            parameter="BVDSS",
            spec_info={"limit_lower": 120, "limit_upper": 80},
        )


def test_one_sided_parameter_mapping_only_shows_applicable_fail_legend() -> None:
    result = prepare_wafer_mapping(
        sample_cleaned(),
        parameter="BVDSS",
        spec_info={"unit": "V", "limit_upper": 105},
    )
    figure = wafer_mapping_grid(result, columns=2)
    legend_names = {trace.name for trace in figure.data if trace.type == "scatter"}

    assert "低于 LSL" not in legend_names
    assert "高于 USL" in legend_names


def test_mapping_grid_renders_every_wafer_in_one_figure() -> None:
    result = prepare_wafer_mapping(sample_cleaned(), pass_bin=1)
    figure = wafer_mapping_grid(result, columns=2)

    heatmaps = [trace for trace in figure.data if trace.type == "heatmap"]
    assert len(heatmaps) == 4
    assert len(figure.layout.annotations) == 4
    assert all("NG 1 / 9" in annotation.text for annotation in figure.layout.annotations)


def test_coordinate_validation_rejects_non_spatial_xy() -> None:
    cleaned = sample_cleaned()
    cleaned["X"] = 0
    cleaned["Y"] = 0

    assert not has_spatial_coordinates(cleaned)
    assert has_spatial_coordinates(sample_cleaned())


def test_duplicate_coordinate_uses_fail_priority_and_is_reported() -> None:
    cleaned = sample_cleaned()
    duplicate = cleaned.iloc[[0]].copy()
    duplicate["Bin"] = 4
    duplicate["Seq"] = 999
    cleaned = pd.concat([cleaned, duplicate], ignore_index=True)

    result = prepare_wafer_mapping(cleaned, pass_bin=1)
    summary = wafer_mapping_summary(result)
    figure = wafer_mapping_grid(result, columns=2)

    assert summary["duplicate_coordinates"] == 1
    assert any("同坐标记录: 2" in str(cell) for row in figure.data[0].text for cell in row)
