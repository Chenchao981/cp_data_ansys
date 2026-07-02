from __future__ import annotations

import numpy as np
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


def parameter_wafer_chart(
    frame: pd.DataFrame,
    parameter: str,
    spec: dict[str, object] | None = None,
    points_per_wafer: int = 120,
) -> go.Figure:
    """按华虹参数图规则生成 Wafer 箱体 + 散点图。"""
    required = [column for column in ("Lot_ID", "Wafer_ID", parameter) if column in frame.columns]
    data = frame[required].copy()
    data[parameter] = pd.to_numeric(data[parameter], errors="coerce")
    data = data.dropna(subset=[parameter])
    if data.empty or "Wafer_ID" not in data.columns:
        fig = go.Figure()
        fig.add_annotation(text=f"参数 {parameter} 没有有效 Wafer 数据", showarrow=False)
        return style_figure(fig, height=500)

    if "Lot_ID" not in data.columns:
        data["Lot_ID"] = "ALL"
    data["Lot_ID"] = data["Lot_ID"].astype(str).str.split("@", n=1).str[0]
    data["Wafer_ID"] = data["Wafer_ID"].astype(str)
    groups = list(data.groupby(["Lot_ID", "Wafer_ID"], sort=True))
    position = {key: index for index, (key, _) in enumerate(groups)}
    lot_count = data["Lot_ID"].nunique()
    labels = [wafer if lot_count == 1 else f"{lot} / W{wafer}" for (lot, wafer), _ in groups]
    fig = go.Figure()

    for lot_index, (lot_id, lot_data) in enumerate(data.groupby("Lot_ID", sort=True)):
        color = [ACCENT, PURPLE, PINK, GREEN, ORANGE][lot_index % 5]
        lot_groups = list(lot_data.groupby("Wafer_ID", sort=True))
        q1: list[float] = []
        median: list[float] = []
        q3: list[float] = []
        lower: list[float] = []
        upper: list[float] = []
        box_x: list[int] = []
        scatter_x: list[float] = []
        scatter_y: list[float] = []
        scatter_wafer: list[str] = []
        outlier_x: list[float] = []
        outlier_y: list[float] = []
        outlier_wafer: list[str] = []

        for wafer_id, wafer_data in lot_groups:
            values = wafer_data[parameter].to_numpy(dtype=float)
            first, middle, third = np.percentile(values, [25, 50, 75])
            iqr = third - first
            normal = values[(values >= first - 1.5 * iqr) & (values <= third + 1.5 * iqr)]
            outliers = values[(values < first - 1.5 * iqr) | (values > third + 1.5 * iqr)]
            box_x.append(position[(lot_id, wafer_id)])
            q1.append(float(first))
            median.append(float(middle))
            q3.append(float(third))
            lower.append(float(normal.min()) if len(normal) else float(first))
            upper.append(float(normal.max()) if len(normal) else float(third))

            sorted_values = np.sort(normal)
            if len(sorted_values) > points_per_wafer:
                indices = np.linspace(0, len(sorted_values) - 1, points_per_wafer, dtype=int)
                shown = sorted_values[indices]
            else:
                shown = sorted_values
            rng = np.random.default_rng(position[(lot_id, wafer_id)] + 42)
            scatter_x.extend(position[(lot_id, wafer_id)] + rng.uniform(-0.2, 0.2, len(shown)))
            scatter_y.extend(shown.tolist())
            scatter_wafer.extend([wafer_id] * len(shown))
            outlier_x.extend([position[(lot_id, wafer_id)]] * len(outliers))
            outlier_y.extend(outliers.tolist())
            outlier_wafer.extend([wafer_id] * len(outliers))

        fig.add_trace(
            go.Box(
                x=box_x,
                q1=q1,
                median=median,
                q3=q3,
                lowerfence=lower,
                upperfence=upper,
                name=lot_id,
                legendgroup=lot_id,
                boxpoints=False,
                width=0.58,
                fillcolor=color,
                opacity=0.34,
                line=dict(color=color, width=2),
                hovertemplate=f"Lot {lot_id}<br>Q1 %{{q1:.6g}}<br>Median %{{median:.6g}}<br>Q3 %{{q3:.6g}}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scattergl(
                x=scatter_x,
                y=scatter_y,
                customdata=scatter_wafer,
                mode="markers",
                name=f"{lot_id} Die",
                legendgroup=lot_id,
                showlegend=False,
                marker=dict(color=color, size=4, opacity=0.42),
                hovertemplate=f"Lot {lot_id}<br>Wafer %{{customdata}}<br>{parameter} %{{y:.6g}}<extra></extra>",
            )
        )
        if outlier_y:
            fig.add_trace(
                go.Scattergl(
                    x=outlier_x,
                    y=outlier_y,
                    customdata=outlier_wafer,
                    mode="markers",
                    name=f"{lot_id} 异常值",
                    legendgroup=lot_id,
                    showlegend=False,
                    marker=dict(color=color, size=6, symbol="circle-open", line=dict(color=color, width=1.2)),
                    hovertemplate=f"异常值<br>Lot {lot_id}<br>Wafer %{{customdata}}<br>{parameter} %{{y:.6g}}<extra></extra>",
                )
            )

    spec = spec or {}
    unit = str(spec.get("Unit", "")).strip()
    test_condition = str(spec.get("TestCond", "")).strip()
    limits: dict[str, float] = {}
    for keys, label in ((('LimitL', 'LSL'), 'LSL'), (('LimitU', 'USL'), 'USL')):
        raw = next((spec[key] for key in keys if key in spec), None)
        value = pd.to_numeric(pd.Series([raw]), errors="coerce").iloc[0]
        if pd.notna(value):
            limits[label] = float(value)
            fig.add_hline(y=float(value), line_dash="dash", line_color=PINK, annotation_text=f"{label} {value:g}")
    target = pd.to_numeric(pd.Series([spec.get("Target")]), errors="coerce").iloc[0]
    if pd.notna(target):
        fig.add_hline(y=float(target), line_dash="dot", line_color=GREEN, annotation_text=f"Target {target:g}")

    title = f"{parameter}{f' [{unit}]' if unit else ''}{f' · {test_condition}' if test_condition else ''}"
    fig.update_layout(title=title, xaxis_title="Wafer_ID", yaxis_title=f"{parameter}{f' [{unit}]' if unit else ''}")
    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(len(labels))),
        ticktext=labels,
        tickangle=0,
        range=[-0.5, len(labels) - 0.5],
    )
    if "LSL" in limits and "USL" in limits:
        lower_limit, upper_limit = sorted((limits["LSL"], limits["USL"]))
        span = upper_limit - lower_limit
        padding = span * 0.1 if span else abs(upper_limit) * 0.1 or 1.0
        fig.update_yaxes(range=[lower_limit - padding, upper_limit + padding])
    return style_figure(fig, height=520)


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
