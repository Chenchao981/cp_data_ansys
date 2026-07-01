from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


ACCENT = "#23d5ff"
PURPLE = "#8b5cf6"
PINK = "#ff4ecd"
GREEN = "#35f2a1"
ORANGE = "#ffb347"
PLOT_BG = "rgba(8, 17, 33, 0.72)"


def style_figure(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=45, r=28, t=62, b=45),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BG,
        font=dict(family="Segoe UI, Microsoft YaHei, sans-serif", color="#dce8ff"),
        title_font=dict(size=18, color="#f3f7ff"),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.12),
        hoverlabel=dict(bgcolor="#111c34", font_color="#ffffff"),
    )
    fig.update_xaxes(gridcolor="rgba(114,137,179,0.14)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(114,137,179,0.14)", zeroline=False)
    return fig


def yield_trend(frame: pd.DataFrame) -> go.Figure:
    plot = frame.sort_values(["Lot_ID", "Wafer_ID"]).copy()
    fig = px.line(
        plot,
        x="Wafer_ID",
        y="Yield_Numeric",
        color="Lot_ID",
        markers=True,
        title="Wafer 良率脉冲",
        labels={"Yield_Numeric": "良率 (%)", "Wafer_ID": "Wafer", "Lot_ID": "Lot"},
        color_discrete_sequence=[ACCENT, PURPLE, PINK, GREEN, ORANGE],
    )
    fig.update_traces(line_width=2.6, marker_size=7)
    mean_value = plot["Yield_Numeric"].mean()
    fig.add_hline(
        y=mean_value,
        line_dash="dot",
        line_color=ORANGE,
        annotation_text=f"均值 {mean_value:.2f}%",
        annotation_font_color=ORANGE,
    )
    return style_figure(fig)


def yield_distribution(frame: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        frame,
        x="Yield_Numeric",
        color="Lot_ID",
        nbins=28,
        opacity=0.78,
        barmode="overlay",
        title="良率分布能谱",
        labels={"Yield_Numeric": "良率 (%)", "Lot_ID": "Lot"},
        color_discrete_sequence=[ACCENT, PURPLE, PINK, GREEN],
    )
    return style_figure(fig)


def lot_comparison(frame: pd.DataFrame) -> go.Figure:
    summary = frame.groupby("Lot_ID", as_index=False)["Yield_Numeric"].agg(["mean", "min", "max", "std"]).reset_index()
    summary["std"] = summary["std"].fillna(0)
    fig = go.Figure(
        go.Bar(
            x=summary["Lot_ID"],
            y=summary["mean"],
            error_y=dict(type="data", array=summary["std"]),
            marker=dict(color=summary["mean"], colorscale=[[0, PURPLE], [1, ACCENT]], line_width=0),
            text=summary["mean"].map(lambda value: f"{value:.2f}%"),
            textposition="outside",
            hovertemplate="Lot %{x}<br>均值 %{y:.3f}%<extra></extra>",
        )
    )
    fig.update_layout(title="Lot 良率对决", xaxis_title="Lot", yaxis_title="平均良率 (%)")
    return style_figure(fig)


def bin_failure_chart(totals: pd.Series) -> go.Figure:
    data = totals[totals > 0].sort_values(ascending=True)
    fig = go.Figure(
        go.Bar(
            x=data.values,
            y=data.index,
            orientation="h",
            marker=dict(color=data.values, colorscale=[[0, PURPLE], [0.55, PINK], [1, ORANGE]]),
            text=[f"{int(value):,}" for value in data.values],
            textposition="outside",
            hovertemplate="%{y}<br>失效数 %{x:,}<extra></extra>",
        )
    )
    fig.update_layout(title="Bin 失效能量排行", xaxis_title="失效 Die 数", yaxis_title="")
    return style_figure(fig)


def parameter_box(frame: pd.DataFrame, parameter: str) -> go.Figure:
    data = frame[[column for column in ("Lot_ID", "Wafer_ID", parameter) if column in frame.columns]].copy()
    data[parameter] = pd.to_numeric(data[parameter], errors="coerce")
    data = data.dropna(subset=[parameter])
    if len(data) > 30_000:
        data = data.sample(30_000, random_state=42)
    fig = px.box(
        data,
        x="Wafer_ID" if "Wafer_ID" in data.columns else None,
        y=parameter,
        color="Lot_ID" if "Lot_ID" in data.columns else None,
        points="outliers",
        title=f"{parameter} · Wafer 分布场",
        color_discrete_sequence=[ACCENT, PURPLE, PINK, GREEN, ORANGE],
    )
    return style_figure(fig, height=500)


def parameter_scatter(frame: pd.DataFrame, x_parameter: str, y_parameter: str) -> go.Figure:
    columns = [column for column in ("Lot_ID", "Wafer_ID", x_parameter, y_parameter) if column in frame.columns]
    data = frame[columns].copy()
    data[x_parameter] = pd.to_numeric(data[x_parameter], errors="coerce")
    data[y_parameter] = pd.to_numeric(data[y_parameter], errors="coerce")
    data = data.dropna(subset=[x_parameter, y_parameter])
    if len(data) > 20_000:
        data = data.sample(20_000, random_state=42)
    fig = px.scatter(
        data,
        x=x_parameter,
        y=y_parameter,
        color="Lot_ID" if "Lot_ID" in data.columns else None,
        hover_data=["Wafer_ID"] if "Wafer_ID" in data.columns else None,
        opacity=0.62,
        title=f"{x_parameter} × {y_parameter} · 参数关联",
        color_discrete_sequence=[ACCENT, PURPLE, PINK, GREEN, ORANGE],
        trendline=None,
    )
    fig.update_traces(marker=dict(size=6, line=dict(width=0)))
    return style_figure(fig, height=500)

