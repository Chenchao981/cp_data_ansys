from __future__ import annotations

from statistics import NormalDist

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from web_app.charts import ACCENT, GREEN, ORANGE, PINK, PURPLE, style_figure


PALETTE = [ACCENT, PURPLE, PINK, GREEN, ORANGE]


def _numeric(frame: pd.DataFrame, parameter: str) -> pd.Series:
    return pd.to_numeric(frame[parameter], errors="coerce")


def sampled(frame: pd.DataFrame, limit: int, seed: int = 42) -> pd.DataFrame:
    return frame.sample(limit, random_state=seed) if len(frame) > limit else frame


def bin_pareto(totals: pd.Series) -> go.Figure:
    values = totals[totals > 0].sort_values(ascending=False)
    cumulative = values.cumsum() / values.sum() * 100 if values.sum() else values
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=values.index,
            y=values.values,
            name="Fail Die",
            marker=dict(color=values.values, colorscale=[[0, PURPLE], [1, PINK]]),
            text=[f"{int(value):,}" for value in values],
            textposition="outside",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=values.index,
            y=cumulative.values,
            name="累计占比",
            mode="lines+markers",
            line=dict(color=ORANGE, width=3),
            marker=dict(size=8),
        ),
        secondary_y=True,
    )
    fig.add_hline(y=80, line_dash="dot", line_color=GREEN, secondary_y=True)
    fig.update_layout(title="Bin 失效 Pareto · 关键少数")
    fig.update_yaxes(title_text="Fail Die", secondary_y=False)
    fig.update_yaxes(title_text="累计占比 (%)", range=[0, 105], secondary_y=True)
    return style_figure(fig, height=470)


def wafer_map(frame: pd.DataFrame, wafer_id: str, value_column: str, pass_bin: int = 1) -> go.Figure:
    wafer = frame.loc[frame["Wafer_ID"].astype(str) == str(wafer_id)].copy()
    if value_column == "Bin":
        wafer["Bin_Status"] = np.where(
            pd.to_numeric(wafer["Bin"], errors="coerce") == pass_bin,
            f"Pass (Bin {pass_bin})",
            "Fail " + wafer["Bin"].astype(str),
        )
        fig = px.scatter(
            wafer,
            x="X",
            y="Y",
            color="Bin_Status",
            symbol="Bin_Status",
            title=f"Wafer {wafer_id} · Bin Map",
            color_discrete_sequence=[GREEN, PINK, ORANGE, PURPLE, ACCENT],
            hover_data=[column for column in ("Seq", "Bin") if column in wafer.columns],
        )
    else:
        wafer[value_column] = _numeric(wafer, value_column)
        fig = px.scatter(
            wafer,
            x="X",
            y="Y",
            color=value_column,
            title=f"Wafer {wafer_id} · {value_column} Spatial Map",
            color_continuous_scale="Turbo",
            hover_data=[column for column in ("Seq", "Bin") if column in wafer.columns],
        )
    fig.update_traces(marker=dict(size=8, symbol="square", line=dict(width=0)))
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return style_figure(fig, height=650)


def parameter_distribution(
    frame: pd.DataFrame,
    parameter: str,
    lsl: float | None = None,
    usl: float | None = None,
) -> go.Figure:
    data = frame[[column for column in ("Lot_ID", parameter) if column in frame.columns]].copy()
    data[parameter] = _numeric(data, parameter)
    data = data.dropna(subset=[parameter])
    fig = px.histogram(
        sampled(data, 50_000),
        x=parameter,
        color="Lot_ID" if "Lot_ID" in data.columns else None,
        marginal="box",
        nbins=60,
        opacity=0.72,
        barmode="overlay",
        histnorm="probability density",
        title=f"{parameter} · 分布与边际箱体图",
        color_discrete_sequence=PALETTE,
    )
    if lsl is not None:
        fig.add_vline(x=lsl, line_color=PINK, line_dash="dash", annotation_text=f"LSL {lsl:g}")
    if usl is not None:
        fig.add_vline(x=usl, line_color=PINK, line_dash="dash", annotation_text=f"USL {usl:g}")
    return style_figure(fig, height=520)


def violin_distribution(frame: pd.DataFrame, parameter: str) -> go.Figure:
    data = frame[[column for column in ("Lot_ID", "Wafer_ID", parameter) if column in frame.columns]].copy()
    data[parameter] = _numeric(data, parameter)
    data = sampled(data.dropna(subset=[parameter]), 30_000)
    fig = px.violin(
        data,
        x="Wafer_ID" if "Wafer_ID" in data.columns else "Lot_ID",
        y=parameter,
        color="Lot_ID" if "Lot_ID" in data.columns else None,
        box=True,
        points=False,
        title=f"{parameter} · Wafer Violin",
        color_discrete_sequence=PALETTE,
    )
    return style_figure(fig, height=500)


def ecdf_chart(frame: pd.DataFrame, parameter: str) -> go.Figure:
    data = frame[[column for column in ("Lot_ID", parameter) if column in frame.columns]].copy()
    data[parameter] = _numeric(data, parameter)
    data = sampled(data.dropna(subset=[parameter]), 40_000)
    fig = px.ecdf(
        data,
        x=parameter,
        color="Lot_ID" if "Lot_ID" in data.columns else None,
        markers=False,
        title=f"{parameter} · ECDF 累积分布",
        color_discrete_sequence=PALETTE,
    )
    fig.update_yaxes(title="累计概率")
    return style_figure(fig)


def qq_chart(frame: pd.DataFrame, parameter: str) -> go.Figure:
    values = _numeric(frame, parameter).dropna().sort_values().to_numpy()
    if not len(values):
        fig = go.Figure()
        fig.add_annotation(text="当前筛选范围没有有效数值", showarrow=False)
        fig.update_layout(title=f"{parameter} · Normal Q-Q")
        return style_figure(fig)
    if len(values) > 10_000:
        indices = np.linspace(0, len(values) - 1, 10_000, dtype=int)
        values = values[indices]
    probabilities = (np.arange(1, len(values) + 1) - 0.5) / len(values)
    theoretical = np.array([NormalDist().inv_cdf(float(probability)) for probability in probabilities])
    slope, intercept = np.polyfit(theoretical, values, 1) if len(values) >= 2 else (1.0, 0.0)
    fig = go.Figure()
    fig.add_trace(go.Scattergl(x=theoretical, y=values, mode="markers", marker=dict(color=ACCENT, size=5), name="样本"))
    fig.add_trace(
        go.Scatter(
            x=[theoretical.min(), theoretical.max()],
            y=[slope * theoretical.min() + intercept, slope * theoretical.max() + intercept],
            mode="lines",
            line=dict(color=PINK, dash="dash"),
            name="正态参考线",
        )
    )
    fig.update_layout(title=f"{parameter} · Normal Q-Q", xaxis_title="理论正态分位数", yaxis_title="样本分位数")
    return style_figure(fig)


def correlation_heatmap(frame: pd.DataFrame, parameters: list[str]) -> go.Figure:
    numeric = frame[parameters].apply(pd.to_numeric, errors="coerce")
    correlation = numeric.corr()
    fig = go.Figure(
        go.Heatmap(
            z=correlation.values,
            x=correlation.columns,
            y=correlation.index,
            zmin=-1,
            zmax=1,
            colorscale="RdBu_r",
            text=np.round(correlation.values, 3),
            texttemplate="%{text}",
            hovertemplate="%{y} × %{x}<br>r=%{z:.4f}<extra></extra>",
        )
    )
    fig.update_layout(title="参数相关性 Heatmap")
    return style_figure(fig, height=600)


def scatter_matrix(frame: pd.DataFrame, parameters: list[str], color_column: str | None = "Lot_ID") -> go.Figure:
    columns = parameters + ([color_column] if color_column and color_column in frame.columns else [])
    data = sampled(frame[columns].copy(), 4_000)
    for parameter in parameters:
        data[parameter] = _numeric(data, parameter)
    fig = px.scatter_matrix(
        data,
        dimensions=parameters,
        color=color_column if color_column in data.columns else None,
        title="多参数 Scatter Matrix",
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(diagonal_visible=False, showupperhalf=False, marker=dict(size=3, opacity=0.45))
    return style_figure(fig, height=760)


def scatter_3d(frame: pd.DataFrame, x: str, y: str, z: str) -> go.Figure:
    columns = [column for column in ("Lot_ID", "Wafer_ID", x, y, z) if column in frame.columns]
    data = sampled(frame[columns].copy(), 8_000)
    for parameter in (x, y, z):
        data[parameter] = _numeric(data, parameter)
    data = data.dropna(subset=[x, y, z])
    fig = px.scatter_3d(
        data,
        x=x,
        y=y,
        z=z,
        color="Lot_ID" if "Lot_ID" in data.columns else None,
        hover_data=["Wafer_ID"] if "Wafer_ID" in data.columns else None,
        opacity=0.55,
        title=f"3D 参数空间 · {x} × {y} × {z}",
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(marker=dict(size=3))
    return style_figure(fig, height=650)


def sequence_scatter(frame: pd.DataFrame, parameter: str, wafer_id: str | None = None) -> go.Figure:
    data = frame.copy()
    if wafer_id is not None and "Wafer_ID" in data.columns:
        data = data.loc[data["Wafer_ID"].astype(str) == str(wafer_id)]
    data[parameter] = _numeric(data, parameter)
    data["Seq"] = pd.to_numeric(data["Seq"], errors="coerce")
    data = sampled(data.dropna(subset=["Seq", parameter]), 20_000)
    fig = px.scatter(
        data,
        x="Seq",
        y=parameter,
        color="Wafer_ID" if wafer_id is None and "Wafer_ID" in data.columns else None,
        trendline=None,
        opacity=0.55,
        title=f"{parameter} · Test Sequence Run Chart" + (f" · Wafer {wafer_id}" if wafer_id else ""),
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(marker=dict(size=5))
    return style_figure(fig, height=500)


def wafer_mean_control_chart(frame: pd.DataFrame, parameter: str) -> go.Figure:
    data = frame[["Lot_ID", "Wafer_ID", parameter]].copy()
    data[parameter] = _numeric(data, parameter)
    summary = data.groupby(["Lot_ID", "Wafer_ID"], as_index=False)[parameter].agg(["mean", "std", "count"]).reset_index()
    center = summary["mean"].mean()
    sigma = summary["mean"].std(ddof=1)
    if not np.isfinite(sigma):
        sigma = 0.0
    ucl = center + 3 * sigma
    lcl = center - 3 * sigma
    summary["Wafer_Label"] = summary["Lot_ID"].astype(str) + " / " + summary["Wafer_ID"].astype(str)
    summary["Out_of_Control"] = (summary["mean"] > ucl) | (summary["mean"] < lcl)
    colors = np.where(summary["Out_of_Control"], PINK, ACCENT)
    fig = go.Figure(
        go.Scatter(
            x=summary["Wafer_Label"],
            y=summary["mean"],
            mode="lines+markers",
            marker=dict(color=colors, size=9),
            line=dict(color=ACCENT, width=2),
            text=summary["count"],
            hovertemplate="%{x}<br>Mean=%{y:.6g}<br>N=%{text}<extra></extra>",
        )
    )
    for value, label, color in ((center, "CL", GREEN), (ucl, "UCL", PINK), (lcl, "LCL", PINK)):
        fig.add_hline(y=value, line_dash="dash", line_color=color, annotation_text=f"{label} {value:.5g}")
    fig.update_layout(title=f"{parameter} · Wafer Mean SPC 3σ", xaxis_title="Lot / Wafer", yaxis_title="Wafer Mean")
    return style_figure(fig, height=520)


def capability_metrics(
    frame: pd.DataFrame,
    parameter: str,
    lsl: float | None,
    usl: float | None,
) -> dict[str, float | int | None]:
    values = _numeric(frame, parameter).dropna()
    mean = float(values.mean()) if not values.empty else np.nan
    overall_sigma = float(values.std(ddof=1)) if len(values) > 1 else np.nan
    within_sigma = np.nan
    if "Wafer_ID" in frame.columns:
        temp = frame[["Wafer_ID", parameter]].copy()
        temp[parameter] = _numeric(temp, parameter)
        groups = [group[parameter].dropna() for _, group in temp.groupby("Wafer_ID")]
        numerator = sum((len(group) - 1) * group.var(ddof=1) for group in groups if len(group) > 1)
        denominator = sum(len(group) - 1 for group in groups if len(group) > 1)
        within_sigma = float(np.sqrt(numerator / denominator)) if denominator else np.nan

    def potential(sigma: float) -> float | None:
        if not np.isfinite(sigma) or sigma <= 0 or lsl is None or usl is None:
            return None
        return (usl - lsl) / (6 * sigma)

    def centered(sigma: float) -> float | None:
        if not np.isfinite(sigma) or sigma <= 0:
            return None
        distances = []
        if usl is not None:
            distances.append((usl - mean) / (3 * sigma))
        if lsl is not None:
            distances.append((mean - lsl) / (3 * sigma))
        return min(distances) if distances else None

    return {
        "Count": int(len(values)),
        "Mean": mean,
        "Within Sigma": within_sigma,
        "Overall Sigma": overall_sigma,
        "Cp": potential(within_sigma),
        "Cpk": centered(within_sigma),
        "Pp": potential(overall_sigma),
        "Ppk": centered(overall_sigma),
    }
