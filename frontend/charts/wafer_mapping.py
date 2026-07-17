#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Wafer Mapping 图表。

该模块只消费标准 cleaned/spec 数据：
- 综合 Bin Mapping：Bin == pass_bin 为良品，其余 Bin 为不良。
- 参数 Mapping：按所选参数的 LSL/USL 判定低超限、高超限。
- 所有 Lot/Wafer 在同一张 Plotly 小图矩阵中展示。

图表阶段不修正规格、不改变测试值；同一坐标存在复测记录时，Mapping
显示该坐标中优先级最高的不良状态，并在悬浮提示中显示记录数。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


BIN_STATUS_LABELS = {
    0: "Bin 未判定",
    1: "良品",
    2: "Bin 不良",
}

BIN_STATUS_COLORS = {
    0: "#697786",
    1: "#334a5f",
    2: "#e74c3c",
}

PARAMETER_STATUS_LABELS = {
    0: "无参数值",
    1: "规格内",
    2: "低于 LSL",
    3: "高于 USL",
}

PARAMETER_STATUS_COLORS = {
    0: "#697786",
    1: "#334a5f",
    2: "#f39c12",
    3: "#e74c3c",
}


@dataclass
class WaferMappingResult:
    """已完成不良判定、可直接绘图的 Mapping 数据。"""

    data: pd.DataFrame
    mode: str
    mapping_label: str
    status_labels: Dict[int, str]
    status_colors: Dict[int, str]
    unit: str = ""
    limit_lower: Optional[float] = None
    limit_upper: Optional[float] = None


def _numeric_or_none(value: object) -> Optional[float]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(numeric) else numeric


def _wafer_sort_key(value: object) -> Tuple[float, str]:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return (float(numeric) if pd.notna(numeric) else float("inf"), str(value))


def has_spatial_coordinates(cleaned: Optional[pd.DataFrame]) -> bool:
    """至少一片 Wafer 同时具有可变化的 X、Y 坐标时返回 True。"""
    if cleaned is None or not {"Wafer_ID", "X", "Y"}.issubset(cleaned.columns):
        return False

    columns = ["Wafer_ID", "X", "Y"]
    if "Lot_ID" in cleaned.columns:
        columns.insert(0, "Lot_ID")
    coords = cleaned[columns].copy()
    coords["X"] = pd.to_numeric(coords["X"], errors="coerce")
    coords["Y"] = pd.to_numeric(coords["Y"], errors="coerce")
    coords = coords.dropna(subset=["Wafer_ID", "X", "Y"])
    if coords.empty:
        return False

    group_columns = ["Wafer_ID"]
    if "Lot_ID" in coords.columns:
        group_columns.insert(0, "Lot_ID")
    variation = coords.groupby(group_columns, dropna=False).agg(x_count=("X", "nunique"), y_count=("Y", "nunique"))
    return bool(((variation["x_count"] > 1) & (variation["y_count"] > 1)).any())


def prepare_wafer_mapping(
    cleaned: pd.DataFrame,
    *,
    parameter: Optional[str] = None,
    spec_info: Optional[Dict[str, object]] = None,
    pass_bin: int = 1,
) -> WaferMappingResult:
    """按综合 Bin 或参数规格准备 Wafer Mapping 数据。"""
    required = {"Wafer_ID", "X", "Y"}
    if cleaned is None or not required.issubset(cleaned.columns):
        missing = sorted(required - set() if cleaned is None else required - set(cleaned.columns))
        raise ValueError(f"cleaned CSV 缺少 Wafer Mapping 字段：{', '.join(missing)}")

    base_columns = [c for c in ["Lot_ID", "Wafer_ID", "X", "Y", "Seq", "Bin"] if c in cleaned.columns]
    if parameter is not None and parameter not in cleaned.columns:
        raise ValueError(f"cleaned CSV 中不存在参数：{parameter}")
    if parameter is not None:
        base_columns.append(parameter)

    data = cleaned[base_columns].copy()
    if "Lot_ID" not in data.columns:
        data["Lot_ID"] = "Unknown_Lot"
    data["_Lot_Text"] = data["Lot_ID"].astype(str)
    data["_Wafer_Text"] = data["Wafer_ID"].astype(str)
    data["X"] = pd.to_numeric(data["X"], errors="coerce")
    data["Y"] = pd.to_numeric(data["Y"], errors="coerce")
    data["_Bin_Value"] = pd.to_numeric(data["Bin"], errors="coerce") if "Bin" in data.columns else np.nan
    data = data.dropna(subset=["Wafer_ID", "X", "Y"])

    if parameter is None:
        if "Bin" not in data.columns:
            raise ValueError("综合 Bin Mapping 需要 cleaned CSV 包含 Bin 字段。")
        data["_Mapping_Value"] = data["_Bin_Value"]
        data["_Status_Code"] = 0
        valid_bin = data["_Bin_Value"].notna()
        data.loc[valid_bin, "_Status_Code"] = 2
        data.loc[valid_bin & (data["_Bin_Value"] == int(pass_bin)), "_Status_Code"] = 1
        data["_Status_Code"] = data["_Status_Code"].astype(int)
        return WaferMappingResult(
            data=data,
            mode="bin",
            mapping_label=f"综合 Bin（Pass Bin={int(pass_bin)}）",
            status_labels=BIN_STATUS_LABELS.copy(),
            status_colors=BIN_STATUS_COLORS.copy(),
        )

    info = spec_info or {}
    lower = _numeric_or_none(info.get("limit_lower"))
    upper = _numeric_or_none(info.get("limit_upper"))
    if lower is None and upper is None:
        raise ValueError(f"参数 {parameter} 没有可用的 LSL/USL，无法判定不良 die。")
    if lower is not None and upper is not None and lower > upper:
        raise ValueError(
            f"参数 {parameter} 的规格方向异常：LSL={lower:g} 大于 USL={upper:g}。"
            "请先修正 spec CSV，前端不会自动交换规格。"
        )

    data["_Mapping_Value"] = pd.to_numeric(data[parameter], errors="coerce")
    data["_Status_Code"] = 0
    valid_value = data["_Mapping_Value"].notna()
    data.loc[valid_value, "_Status_Code"] = 1
    if lower is not None:
        data.loc[valid_value & (data["_Mapping_Value"] < lower), "_Status_Code"] = 2
    if upper is not None:
        data.loc[valid_value & (data["_Mapping_Value"] > upper), "_Status_Code"] = 3
    data["_Status_Code"] = data["_Status_Code"].astype(int)

    return WaferMappingResult(
        data=data,
        mode="parameter",
        mapping_label=parameter,
        status_labels=PARAMETER_STATUS_LABELS.copy(),
        status_colors=PARAMETER_STATUS_COLORS.copy(),
        unit=str(info.get("unit") or ""),
        limit_lower=lower,
        limit_upper=upper,
    )


def wafer_mapping_summary(result: WaferMappingResult) -> Dict[str, int]:
    """返回 Mapping 页面的关键计数。"""
    data = result.data
    if data.empty:
        return {"wafers": 0, "records": 0, "judged": 0, "fail": 0, "duplicate_coordinates": 0}

    wafer_keys = data[["_Lot_Text", "_Wafer_Text"]].drop_duplicates()
    judged = int((data["_Status_Code"] > 0).sum())
    fail = int((data["_Status_Code"] >= 2).sum())
    duplicate_coordinates = int(data.duplicated(["_Lot_Text", "_Wafer_Text", "X", "Y"]).sum())
    return {
        "wafers": len(wafer_keys),
        "records": len(data),
        "judged": judged,
        "fail": fail,
        "duplicate_coordinates": duplicate_coordinates,
    }


def _wafer_order(data: pd.DataFrame) -> List[Tuple[str, str]]:
    keys = data[["_Lot_Text", "_Wafer_Text"]].drop_duplicates()
    lots = sorted(keys["_Lot_Text"].astype(str).unique())
    ordered: List[Tuple[str, str]] = []
    for lot in lots:
        wafers = keys.loc[keys["_Lot_Text"] == lot, "_Wafer_Text"].astype(str).tolist()
        ordered.extend((lot, wafer) for wafer in sorted(wafers, key=_wafer_sort_key))
    return ordered


def wafer_mapping_wafer_keys(result: WaferMappingResult) -> List[Tuple[str, str]]:
    """返回按 Lot/Wafer 排序的唯一 Wafer 键，供前端范围选择。"""
    return _wafer_order(result.data) if not result.data.empty else []


def filter_wafer_mapping(
    result: WaferMappingResult,
    wafer_keys: Iterable[Tuple[str, str]],
) -> WaferMappingResult:
    """筛选要展示的 Lot/Wafer，同时保留原 Mapping 判定和规格。"""
    selected = {(str(lot), str(wafer)) for lot, wafer in wafer_keys}
    if not selected or result.data.empty:
        return replace(result, data=result.data.iloc[0:0].copy())

    key_index = pd.MultiIndex.from_arrays(
        [result.data["_Lot_Text"].astype(str), result.data["_Wafer_Text"].astype(str)]
    )
    return replace(result, data=result.data.loc[key_index.isin(selected)].copy())


def _discrete_colorscale(status_colors: Dict[int, str]) -> List[Tuple[float, str]]:
    codes = sorted(status_colors)
    count = len(codes)
    scale: List[Tuple[float, str]] = []
    for index, code in enumerate(codes):
        start = index / count
        end = (index + 1) / count
        scale.append((start, status_colors[code]))
        scale.append((end, status_colors[code]))
    return scale


def _collapse_coordinate_records(wafer_data: pd.DataFrame) -> pd.DataFrame:
    """同坐标复测时保留最高不良优先级记录，并附上复测次数。"""
    data = wafer_data.copy()
    if "Seq" in data.columns:
        data["_Seq_Sort"] = pd.to_numeric(data["Seq"], errors="coerce")
    else:
        data["_Seq_Sort"] = np.arange(len(data))
    counts = data.groupby(["X", "Y"], dropna=False).size().rename("_Coord_Count")
    selected = (
        data.sort_values(["_Status_Code", "_Seq_Sort"], na_position="first")
        .drop_duplicates(["X", "Y"], keep="last")
        .merge(counts, left_on=["X", "Y"], right_index=True, how="left")
    )
    return selected


def wafer_mapping_grid(
    result: WaferMappingResult,
    columns: int = 6,
    *,
    include_hover: bool = True,
) -> go.Figure:
    """把 Lot/Wafer 画成小图矩阵；轻量模式可关闭逐 die 悬浮数据。"""
    data = result.data
    wafer_order = _wafer_order(data) if not data.empty else []
    if not wafer_order:
        fig = go.Figure()
        fig.add_annotation(text="没有可绘制的 Wafer Mapping 数据", x=0.5, y=0.5, showarrow=False)
        return fig

    columns = max(1, min(int(columns), 8, len(wafer_order)))
    rows = int(math.ceil(len(wafer_order) / columns))
    titles: List[str] = []
    collapsed_by_wafer: Dict[Tuple[str, str], pd.DataFrame] = {}
    grouped = {
        (str(lot), str(wafer)): group
        for (lot, wafer), group in data.groupby(["_Lot_Text", "_Wafer_Text"], sort=False, dropna=False)
    }

    for lot, wafer in wafer_order:
        wafer_data = grouped[(lot, wafer)]
        collapsed = _collapse_coordinate_records(wafer_data)
        collapsed_by_wafer[(lot, wafer)] = collapsed
        judged = int((collapsed["_Status_Code"] > 0).sum())
        fail = int((collapsed["_Status_Code"] >= 2).sum())
        titles.append(f"{lot} / W{wafer}<br><span style='font-size:10px'>NG {fail:,} / {judged:,}</span>")

    fig = make_subplots(
        rows=rows,
        cols=columns,
        subplot_titles=titles,
        horizontal_spacing=0.018,
        vertical_spacing=min(0.06, 0.45 / max(rows, 1)),
    )
    colorscale = _discrete_colorscale(result.status_colors)
    status_codes = sorted(result.status_labels)
    zmin = min(status_codes) - 0.5
    zmax = max(status_codes) + 0.5

    for index, (lot, wafer) in enumerate(wafer_order):
        row = index // columns + 1
        col = index % columns + 1
        wafer_data = collapsed_by_wafer[(lot, wafer)]
        x_values = sorted(wafer_data["X"].dropna().unique())
        y_values = sorted(wafer_data["Y"].dropna().unique())
        if len(x_values) < 2 or len(y_values) < 2:
            fig.add_annotation(
                text="X/Y 坐标不可用",
                x=0.5,
                y=0.5,
                xref=f"x{index + 1} domain" if index else "x domain",
                yref=f"y{index + 1} domain" if index else "y domain",
                showarrow=False,
                font=dict(size=11, color="#f39c12"),
            )
            continue

        z = (
            wafer_data.pivot(index="Y", columns="X", values="_Status_Code")
            .reindex(index=y_values, columns=x_values)
            .to_numpy(dtype=float)
        )
        heatmap_options: Dict[str, object] = {}
        if include_hover:
            x_index = {value: pos for pos, value in enumerate(x_values)}
            y_index = {value: pos for pos, value in enumerate(y_values)}
            hover = np.full((len(y_values), len(x_values)), "", dtype=object)
            column_positions = {name: position for position, name in enumerate(wafer_data.columns)}
            for record in wafer_data.itertuples(index=False, name=None):
                x_value = record[column_positions["X"]]
                y_value = record[column_positions["Y"]]
                x_pos = x_index[x_value]
                y_pos = y_index[y_value]
                status_code = int(record[column_positions["_Status_Code"]])
                status_label = result.status_labels[status_code]
                bin_value = record[column_positions["_Bin_Value"]]
                mapping_value = record[column_positions["_Mapping_Value"]]
                count = int(record[column_positions["_Coord_Count"]])
                if result.mode == "parameter":
                    value_text = (
                        "N/A"
                        if pd.isna(mapping_value)
                        else f"{float(mapping_value):g}{(' ' + result.unit) if result.unit else ''}"
                    )
                    mapping_text = f"{result.mapping_label}: {value_text}<br>"
                else:
                    mapping_text = ""
                bin_text = "N/A" if pd.isna(bin_value) else f"{float(bin_value):g}"
                hover[y_pos, x_pos] = (
                    f"Lot: {lot}<br>Wafer: {wafer}<br>"
                    f"X: {x_value:g}, Y: {y_value:g}<br>"
                    f"Bin: {bin_text}<br>{mapping_text}状态: {status_label}<br>"
                    f"同坐标记录: {count}"
                )
            heatmap_options.update(text=hover, hovertemplate="%{text}<extra></extra>")
        else:
            heatmap_options["hoverinfo"] = "skip"

        fig.add_trace(
            go.Heatmap(
                x=x_values,
                y=y_values,
                z=z,
                hoverongaps=False,
                colorscale=colorscale,
                zmin=zmin,
                zmax=zmax,
                showscale=False,
                xgap=1,
                ygap=1,
                **heatmap_options,
            ),
            row=row,
            col=col,
        )

        x_min, x_max = min(x_values), max(x_values)
        y_min, y_max = min(y_values), max(y_values)
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2
        radius = max(x_max - x_min, y_max - y_min) / 2 + 0.8
        fig.add_shape(
            type="circle",
            x0=center_x - radius,
            x1=center_x + radius,
            y0=center_y - radius,
            y1=center_y + radius,
            line=dict(color="#7a8ba0", width=1),
            layer="above",
            row=row,
            col=col,
        )
        fig.update_xaxes(
            range=[center_x - radius - 0.5, center_x + radius + 0.5],
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            constrain="domain",
            row=row,
            col=col,
        )
        axis_name = "x" if index == 0 else f"x{index + 1}"
        fig.update_yaxes(
            range=[center_y - radius - 0.5, center_y + radius + 0.5],
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            scaleanchor=axis_name,
            scaleratio=1,
            constrain="domain",
            row=row,
            col=col,
        )

    legend_codes = status_codes.copy()
    if result.mode == "parameter" and result.limit_lower is None:
        legend_codes.remove(2)
    if result.mode == "parameter" and result.limit_upper is None:
        legend_codes.remove(3)
    for code in legend_codes:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(symbol="square", size=11, color=result.status_colors[code]),
                name=result.status_labels[code],
                showlegend=True,
                hoverinfo="skip",
            ),
            row=1,
            col=1,
        )

    spec_parts = []
    if result.limit_lower is not None:
        spec_parts.append(f"LSL={result.limit_lower:g}")
    if result.limit_upper is not None:
        spec_parts.append(f"USL={result.limit_upper:g}")
    embedded_unit = f"[{result.unit}]".lower() if result.unit else ""
    unit_text = "" if embedded_unit and embedded_unit in result.mapping_label.lower() else (f" [{result.unit}]" if result.unit else "")
    spec_text = f" · {' / '.join(spec_parts)}" if spec_parts else ""
    fig.update_layout(
        title=f"Wafer Mapping · {result.mapping_label}{unit_text}{spec_text}",
        height=max(600, rows * 225 + 190),
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="right", x=1),
        hovermode="closest",
    )
    return fig
