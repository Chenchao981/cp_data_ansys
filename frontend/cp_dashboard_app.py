#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP 数据分析 Cockpit 前端。

数据边界：
- 前端只读取本项目清洗后的标准 CSV：cleaned / yield / spec。
- 不在前端重新解析 HH、JT、Lion、国宇等原始厂商文件。
- 图表阶段不修改原始测试值，只做展示、筛选、统计和抽样。
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.charts.wafer_mapping import (
    filter_wafer_mapping,
    has_spatial_coordinates,
    prepare_wafer_mapping,
    wafer_mapping_grid,
    wafer_mapping_wafer_keys,
    wafer_mapping_summary,
)


BASE_COLUMNS = {
    "Lot_ID",
    "Wafer_ID",
    "X",
    "Y",
    "Seq",
    "Bin",
    "CONT",
    "SITE_NUM",
    "T_TIME",
    "Gross_die",
    "Good_die",
    "Pass_die",
    "Fail_die",
    "Yield",
    "Yield_Rate",
    "Total",
    "Pass",
    "Fail",
}

PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "#0f1923",
        "plot_bgcolor": "#142231",
        "font": {"color": "#c8d6e5", "family": "Segoe UI, Microsoft YaHei, sans-serif"},
        "colorway": ["#4dabf7", "#2ecc71", "#f39c12", "#e74c3c", "#9b59b6", "#1abc9c"],
        "xaxis": {
            "gridcolor": "#2a3a4a",
            "linecolor": "#3a4b5c",
            "tickcolor": "#3a4b5c",
            "zerolinecolor": "#2a3a4a",
        },
        "yaxis": {
            "gridcolor": "#2a3a4a",
            "linecolor": "#3a4b5c",
            "tickcolor": "#3a4b5c",
            "zerolinecolor": "#2a3a4a",
        },
    }
}

PLOTLY_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": False,
}


@dataclass
class StandardDataset:
    data_dir: Path
    cleaned_path: Optional[Path]
    yield_path: Optional[Path]
    spec_path: Optional[Path]
    cleaned: Optional[pd.DataFrame]
    yield_df: Optional[pd.DataFrame]
    spec: Optional[pd.DataFrame]


def inject_cockpit_theme() -> None:
    """注入 CP Cockpit 深色分析界面样式。"""

    st.markdown(
        """
<style>
:root {
  --vt-bg:#0f1923;
  --vt-surface:#1a2735;
  --vt-surface-2:#142231;
  --vt-border:#2a3a4a;
  --vt-text:#c8d6e5;
  --vt-muted:#7a8ba0;
  --vt-accent:#4dabf7;
  --vt-good:#2ecc71;
  --vt-fail:#e74c3c;
  --vt-warn:#f39c12;
}
.stApp {
  background: var(--vt-bg);
  color: var(--vt-text);
  font-family: 'Segoe UI','Microsoft YaHei',sans-serif;
}
html, body, [data-testid="stAppViewContainer"] {
  background: var(--vt-bg);
}
header[data-testid="stHeader"] {
  background: rgba(15,25,35,.96);
  border-bottom: 1px solid var(--vt-border);
  backdrop-filter: blur(12px);
}
[data-testid="stDecoration"] { display: none; }
[data-testid="stToolbar"] { background: transparent; }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #111d29 0%, #0f1923 100%);
  border-right: 1px solid var(--vt-border);
}
[data-testid="stSidebar"] * { color: var(--vt-text); }
h1, h2, h3, h4, h5, h6 { color: var(--vt-text); letter-spacing: .2px; }
.stMarkdown p, [data-testid="stCaptionContainer"] { color: var(--vt-muted); }
.block-container { padding-top: 1.6rem; max-width: 1500px; }
.vt-hero {
  background: radial-gradient(circle at top left, rgba(77,171,247,.20), transparent 32%),
              linear-gradient(135deg, #172636 0%, #0f1923 100%);
  border: 1px solid var(--vt-border);
  border-radius: 16px;
  padding: 22px 24px;
  margin-bottom: 16px;
  box-shadow: 0 16px 44px rgba(0,0,0,.22);
}
.vt-hero h1 { margin: 0 0 6px 0; font-size: 1.65rem; }
.vt-hero p { margin: 0; color: var(--vt-muted); font-size: .92rem; }
.vt-card {
  background: var(--vt-surface);
  border: 1px solid var(--vt-border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 12px;
}
.vt-card-title {
  color: var(--vt-muted);
  font-size: .78rem;
  margin-bottom: 8px;
}
.vt-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
  gap: 10px;
  margin: 12px 0 18px 0;
}
.vt-stat {
  background: var(--vt-surface);
  border: 1px solid var(--vt-border);
  border-radius: 10px;
  padding: 13px 14px;
}
.vt-label {
  color: var(--vt-muted);
  font-size: .72rem;
  margin-bottom: 6px;
}
.vt-value {
  color: var(--vt-text);
  font-size: 1.25rem;
  font-weight: 750;
}
.vt-good { color: var(--vt-good); }
.vt-fail { color: var(--vt-fail); }
.vt-accent { color: var(--vt-accent); }
.vt-warn { color: var(--vt-warn); }
.vt-bin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
  gap: 8px;
}
.vt-bin-item {
  background: var(--vt-surface);
  border: 1px solid var(--vt-border);
  border-radius: 10px;
  padding: 10px 12px;
}
.vt-bin-item .vt-bid { color: var(--vt-muted); font-size: .68rem; }
.vt-bin-item .vt-bcnt { color: var(--vt-text); font-size: 1.18rem; font-weight: 750; }
.vt-bin-item .vt-blbl { color: var(--vt-muted); font-size: .68rem; }
.stButton > button, .stDownloadButton > button {
  background: rgba(77,171,247,.14);
  color: var(--vt-text);
  border: 1px solid var(--vt-accent);
  border-radius: 8px;
  font-weight: 650;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  background: var(--vt-accent);
  color: #06111c;
  border: 1px solid var(--vt-accent);
}
[data-baseweb="input"],
[data-baseweb="base-input"],
[data-baseweb="select"] > div {
  background: var(--vt-surface) !important;
  border-color: var(--vt-border) !important;
  color: var(--vt-text) !important;
}
.stTextInput input, .stNumberInput input {
  background: var(--vt-surface) !important;
  color: var(--vt-text) !important;
  -webkit-text-fill-color: var(--vt-text) !important;
}
[data-testid="stNumberInput"] button {
  background: var(--vt-surface-2) !important;
  color: var(--vt-text) !important;
  border-color: var(--vt-border) !important;
}
[data-testid="stMetric"] {
  background: var(--vt-surface);
  border: 1px solid var(--vt-border);
  border-radius: 10px;
  padding: 10px 12px;
}
[data-testid="stMetricLabel"] p { color: var(--vt-muted) !important; }
[data-testid="stMetricValue"] { color: var(--vt-text) !important; }
[data-baseweb="tab-list"] { gap: 6px; flex-wrap: wrap; }
[data-baseweb="tab-highlight"] { display: none; }
[data-baseweb="tab"] {
  background: var(--vt-surface);
  border: 1px solid var(--vt-border);
  border-radius: 999px;
  color: var(--vt-muted);
  padding: 5px 14px;
}
[aria-selected="true"][data-baseweb="tab"] {
  background: rgba(77,171,247,.18);
  color: var(--vt-accent);
  border-color: var(--vt-accent);
}
.stDataFrame, [data-testid="stDataFrame"] {
  border: 1px solid var(--vt-border);
  border-radius: 10px;
}
.stPlotlyChart, [data-testid="stPlotlyChart"] {
  background: var(--vt-surface);
  border: 1px solid var(--vt-border);
  border-radius: 14px;
  box-sizing: border-box;
  padding: 8px;
  margin-bottom: 14px;
  overflow: hidden;
  box-shadow: 0 12px 30px rgba(0,0,0,.18);
}
.stPlotlyChart .modebar,
[data-testid="stPlotlyChart"] .modebar { background: transparent !important; }
</style>
        """,
        unsafe_allow_html=True,
    )


def latest_file(data_dir: Path, patterns: Iterable[str]) -> Optional[Path]:
    files: List[Path] = []
    for pattern in patterns:
        files.extend(data_dir.glob(pattern))
    if not files and data_dir.exists():
        for pattern in patterns:
            files.extend(data_dir.rglob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def read_csv_safely(path: Optional[Path]) -> Optional[pd.DataFrame]:
    if path is None:
        return None
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_standard_dataset(data_dir_text: str) -> StandardDataset:
    data_dir = Path(data_dir_text).expanduser()
    cleaned_path = latest_file(data_dir, ("*_cleaned_*.csv", "*cleaned*.csv"))
    yield_path = latest_file(data_dir, ("*_yield_*.csv", "*yield*.csv"))
    spec_path = latest_file(data_dir, ("*_spec_*.csv", "*spec*.csv"))
    return StandardDataset(
        data_dir=data_dir,
        cleaned_path=cleaned_path,
        yield_path=yield_path,
        spec_path=spec_path,
        cleaned=read_csv_safely(cleaned_path),
        yield_df=read_csv_safely(yield_path),
        spec=read_csv_safely(spec_path),
    )


def to_numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace("%", "", regex=False), errors="coerce")


def normalize_yield_data(yield_df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    if yield_df is None or yield_df.empty:
        return None
    df = yield_df.copy()
    if "Lot_ID" in df.columns:
        df = df[df["Lot_ID"].astype(str).str.upper() != "ALL"].copy()
    if "Wafer_ID" in df.columns:
        df = df[~df["Wafer_ID"].astype(str).str.upper().isin(["ALL", "TOTAL"])].copy()

    if "Yield" in df.columns:
        df["Yield_Numeric"] = to_numeric_series(df["Yield"])
    elif "Yield_Rate" in df.columns:
        df["Yield_Numeric"] = to_numeric_series(df["Yield_Rate"])
    elif {"Good_die", "Gross_die"}.issubset(df.columns):
        gross = to_numeric_series(df["Gross_die"]).replace(0, np.nan)
        df["Yield_Numeric"] = to_numeric_series(df["Good_die"]) / gross * 100
    elif {"Pass", "Total"}.issubset(df.columns):
        total = to_numeric_series(df["Total"]).replace(0, np.nan)
        df["Yield_Numeric"] = to_numeric_series(df["Pass"]) / total * 100
    else:
        df["Yield_Numeric"] = np.nan

    if "Lot_ID" not in df.columns:
        df["Lot_ID"] = "Unknown_Lot"
    if "Wafer_ID" not in df.columns:
        df["Wafer_ID"] = np.arange(1, len(df) + 1).astype(str)

    df["Lot_Short"] = df["Lot_ID"].astype(str).str.split("@", n=1).str[0]
    df["Wafer_ID"] = df["Wafer_ID"].astype(str)
    df["_Wafer_Sort"] = pd.to_numeric(df["Wafer_ID"], errors="coerce")
    df = df.sort_values(["Lot_Short", "_Wafer_Sort", "Wafer_ID"], na_position="last")
    return df


def available_parameters(cleaned: Optional[pd.DataFrame]) -> List[str]:
    if cleaned is None or cleaned.empty:
        return []
    params = []
    for col in cleaned.columns:
        if col in BASE_COLUMNS:
            continue
        numeric = pd.to_numeric(cleaned[col], errors="coerce")
        if numeric.notna().sum() >= 3:
            params.append(col)
    return params


def get_spec_info(spec: Optional[pd.DataFrame], parameter: str) -> Dict[str, object]:
    info: Dict[str, object] = {
        "parameter": parameter,
        "unit": "",
        "limit_lower": None,
        "limit_upper": None,
        "test_condition": "",
    }
    if spec is None or spec.empty:
        return info

    def first_existing(row: pd.Series, names: Iterable[str]) -> object:
        lower_map = {str(c).lower(): c for c in row.index}
        for name in names:
            col = lower_map.get(name.lower())
            if col is not None:
                return row[col]
        return None

    # 逐参数行布局：Parameter, Unit, LimitL/LimitU...
    parameter_cols = [c for c in spec.columns if str(c).lower() in {"parameter", "param", "item", "test_item"}]
    if parameter_cols:
        pcol = parameter_cols[0]
        matched = spec[spec[pcol].astype(str) == parameter]
        if not matched.empty:
            row = matched.iloc[0]
            info["unit"] = first_existing(row, ("Unit", "UNIT", "Units")) or ""
            info["limit_lower"] = first_existing(row, ("LimitL", "LSL", "Lower", "Low", "SL"))
            info["limit_upper"] = first_existing(row, ("LimitU", "USL", "Upper", "High", "SU"))
            info["test_condition"] = first_existing(row, ("TestCond", "TestCond:", "Condition")) or ""
            return normalize_spec_info(info)

    # 矩阵布局：首列为 Unit / LimitL / LimitU，参数名为列。
    if parameter in spec.columns:
        first_col = spec.columns[0]
        label = spec[first_col].astype(str).str.strip().str.lower()
        lookup = dict(zip(label, spec[parameter]))
        info["unit"] = lookup.get("unit", lookup.get("units", ""))
        info["limit_lower"] = lookup.get("limitl", lookup.get("lsl", lookup.get("limit_low")))
        info["limit_upper"] = lookup.get("limitu", lookup.get("usl", lookup.get("limit_high")))
        info["test_condition"] = lookup.get("testcond:", lookup.get("testcond", ""))
        return normalize_spec_info(info)

    return info


def normalize_spec_info(info: Dict[str, object]) -> Dict[str, object]:
    for key in ("limit_lower", "limit_upper"):
        value = info.get(key)
        try:
            value_float = float(value)
            info[key] = None if math.isnan(value_float) else value_float
        except (TypeError, ValueError):
            info[key] = None
    return info


def get_default_data_dir() -> str:
    """从 GUI 传入的 URL 参数或环境变量取得默认数据目录。"""
    query_value = None
    try:
        query_value = st.query_params.get("data_dir")
    except Exception:
        query_value = None
    if isinstance(query_value, list):
        query_value = query_value[0] if query_value else None
    return str(query_value or os.environ.get("CP_COCKPIT_DATA_DIR") or "output")


def wafer_sort_key(value: object) -> Tuple[float, str]:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return (float(numeric) if pd.notna(numeric) else 999999.0, str(value))


def true_lot_id(value: object) -> str:
    """与 Huahong 箱体图保持一致：Lot_ID 中 @ 后为来源后缀，展示时取真实批次。"""
    text = str(value)
    return text.split("@", 1)[0] if "@" in text else text


def sample_dataframe(df: pd.DataFrame, max_points: int) -> pd.DataFrame:
    if len(df) > max_points:
        return df.sample(max_points, random_state=42)
    return df


def prepare_wafer_axis(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[object], List[str], List[str]]:
    """按 Huahong 箱体图的 X 轴方式准备 Lot/Wafer 顺序和位置。"""
    data = df.copy()
    if "Lot_ID" not in data.columns:
        data["Lot_ID"] = "Lot"
    if "Wafer_ID" not in data.columns:
        data["Wafer_ID"] = np.arange(1, len(data) + 1).astype(str)

    data["Lot_Short"] = data["Lot_ID"].map(true_lot_id)
    data["Wafer_Text"] = data["Wafer_ID"].astype(str)
    wafer_order_df = (
        data[["Lot_Short", "Wafer_Text"]]
        .drop_duplicates()
        .assign(_wafer_sort=lambda x: pd.to_numeric(x["Wafer_Text"], errors="coerce"))
        .sort_values(["Lot_Short", "_wafer_sort", "Wafer_Text"], na_position="last")
        .reset_index(drop=True)
    )
    wafer_order_df["x_position"] = np.arange(len(wafer_order_df))
    data = data.merge(wafer_order_df[["Lot_Short", "Wafer_Text", "x_position"]], on=["Lot_Short", "Wafer_Text"], how="left")
    tick_vals = wafer_order_df["x_position"].tolist()
    tick_text = wafer_order_df["Wafer_Text"].astype(str).tolist()
    lot_order = wafer_order_df["Lot_Short"].drop_duplicates().astype(str).tolist()
    return data, tick_vals, tick_text, lot_order


def cleaned_with_zone(cleaned: Optional[pd.DataFrame], pass_bin: int) -> pd.DataFrame:
    """基于每片 Wafer 的 X/Y 相对中心半径划分 Center/Mid/Edge。"""
    if cleaned is None or not {"Wafer_ID", "X", "Y", "Bin"}.issubset(cleaned.columns):
        return pd.DataFrame()

    df = cleaned[["Lot_ID", "Wafer_ID", "X", "Y", "Bin"]].copy()
    df["X"] = pd.to_numeric(df["X"], errors="coerce")
    df["Y"] = pd.to_numeric(df["Y"], errors="coerce")
    df["Bin"] = pd.to_numeric(df["Bin"], errors="coerce")
    df = df.dropna(subset=["Wafer_ID", "X", "Y", "Bin"])
    if df.empty:
        return df

    df["_cx"] = df.groupby("Wafer_ID")["X"].transform("median")
    df["_cy"] = df.groupby("Wafer_ID")["Y"].transform("median")
    df["_radius"] = np.sqrt((df["X"] - df["_cx"]) ** 2 + (df["Y"] - df["_cy"]) ** 2)
    max_radius = df.groupby("Wafer_ID")["_radius"].transform("max").replace(0, np.nan)
    df["_radius_norm"] = (df["_radius"] / max_radius).fillna(0)
    df["Zone"] = pd.cut(
        df["_radius_norm"],
        bins=[-0.001, 0.33, 0.66, float("inf")],
        labels=["Center", "Mid", "Edge"],
    ).astype(str)
    df["Pass"] = df["Bin"] == pass_bin
    return df


def dataset_summary(dataset: StandardDataset, pass_bin: int) -> Dict[str, object]:
    cleaned = dataset.cleaned
    ydf = normalize_yield_data(dataset.yield_df)
    params = available_parameters(cleaned)
    total_die = len(cleaned) if cleaned is not None else 0
    pass_die = 0
    fail_die = 0
    bin_counts = pd.Series(dtype="int64")

    if cleaned is not None and "Bin" in cleaned.columns:
        bins = pd.to_numeric(cleaned["Bin"], errors="coerce")
        pass_die = int((bins == pass_bin).sum())
        fail_die = int(bins.notna().sum() - pass_die)
        bin_counts = bins.dropna().astype(int).value_counts().sort_index()
    elif ydf is not None:
        bin_cols = [c for c in ydf.columns if str(c).lower().startswith("bin")]
        if bin_cols:
            bin_counts = ydf[bin_cols].apply(pd.to_numeric, errors="coerce").fillna(0).sum().astype(int)
            bin_counts.index = [int(str(c).replace("Bin", "").replace("bin", "")) for c in bin_counts.index]
            bin_counts = bin_counts.sort_index()
            pass_die = int(bin_counts.get(pass_bin, 0))
            fail_die = int(bin_counts.sum() - pass_die)
            total_die = int(bin_counts.sum())

    lots = cleaned["Lot_ID"].nunique() if cleaned is not None and "Lot_ID" in cleaned.columns else (ydf["Lot_ID"].nunique() if ydf is not None else 0)
    wafers = cleaned["Wafer_ID"].nunique() if cleaned is not None and "Wafer_ID" in cleaned.columns else (ydf["Wafer_ID"].nunique() if ydf is not None else 0)
    avg_yield = float(ydf["Yield_Numeric"].mean()) if ydf is not None and ydf["Yield_Numeric"].notna().any() else (pass_die / total_die * 100 if total_die else np.nan)

    return {
        "total_die": total_die,
        "pass_die": pass_die,
        "fail_die": fail_die,
        "avg_yield": avg_yield,
        "lots": lots,
        "wafers": wafers,
        "params": len(params),
        "bin_counts": bin_counts,
    }


def render_hero() -> None:
    st.markdown(
        """
<div class="vt-hero">
  <h1>📊 CP 数据分析 Cockpit</h1>
  <p>CP 交互分析前端 · 复用 cleaned / yield / spec 标准 CSV · 服务研发、质量和工艺分析</p>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_cards(summary: Dict[str, object]) -> None:
    avg_yield = summary["avg_yield"]
    avg_yield_text = "--" if pd.isna(avg_yield) else f"{avg_yield:.2f}%"
    cards = [
        ("总测试数", f"{int(summary['total_die']):,}", "vt-accent"),
        ("平均良率", avg_yield_text, "vt-good" if not pd.isna(avg_yield) and avg_yield >= 98 else "vt-warn"),
        ("良品", f"{int(summary['pass_die']):,}", "vt-good"),
        ("失效", f"{int(summary['fail_die']):,}", "vt-fail"),
        ("批次", str(summary["lots"]), ""),
        ("Wafer", str(summary["wafers"]), ""),
        ("参数", str(summary["params"]), ""),
    ]
    html = '<div class="vt-stats">'
    for label, value, klass in cards:
        html += f'<div class="vt-stat"><div class="vt-label">{label}</div><div class="vt-value {klass}">{value}</div></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_file_status(dataset: StandardDataset) -> None:
    rows = [
        ("cleaned", dataset.cleaned_path),
        ("yield", dataset.yield_path),
        ("spec", dataset.spec_path),
    ]
    html = '<div class="vt-card"><div class="vt-card-title">📂 当前加载文件</div>'
    for name, path in rows:
        status = path.name if path else "未找到"
        color = "var(--vt-good)" if path else "var(--vt-fail)"
        html += f'<div style="font-size:.78rem;margin:4px 0;color:{color}">{name}: {status}</div>'
    html += "</div>"
    st.sidebar.markdown(html, unsafe_allow_html=True)


def render_bin_grid(bin_counts: pd.Series, total: int) -> None:
    if bin_counts.empty:
        st.info("当前数据没有可用的 Bin 统计。")
        return
    html = '<div class="vt-bin-grid">'
    for bin_id, count in bin_counts.items():
        count_int = int(count)
        rate = count_int / total * 100 if total else 0
        color = "#2ecc71" if int(bin_id) == 1 else "#e74c3c"
        html += (
            f'<div class="vt-bin-item" style="border-left:3px solid {color}">'
            f'<div class="vt-bid">BIN {bin_id}</div>'
            f'<div class="vt-bcnt">{count_int:,}</div>'
            f'<div class="vt-blbl">{rate:.2f}%</div>'
            "</div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def style_figure(fig: go.Figure, height: int = 520) -> go.Figure:
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="#1a2735",
        plot_bgcolor="#142231",
        font=dict(color="#c8d6e5", family="Segoe UI, Microsoft YaHei, sans-serif"),
        title=dict(font=dict(color="#e6eef7", size=17), x=0.02, xanchor="left"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="#2a3a4a",
            font=dict(color="#c8d6e5"),
        ),
        hoverlabel=dict(bgcolor="#203040", bordercolor="#4dabf7", font_color="#e6eef7"),
        modebar=dict(bgcolor="rgba(0,0,0,0)", color="#7a8ba0", activecolor="#4dabf7"),
        height=height,
        margin=dict(l=54, r=32, t=64, b=56),
    )
    fig.update_xaxes(
        color="#9fb0c3",
        gridcolor="#2a3a4a",
        linecolor="#3a4b5c",
        zerolinecolor="#2a3a4a",
    )
    fig.update_yaxes(
        color="#9fb0c3",
        gridcolor="#2a3a4a",
        linecolor="#3a4b5c",
        zerolinecolor="#2a3a4a",
    )
    return fig


def render_plotly_chart(fig: go.Figure) -> None:
    """保持 Plotly 自定义深色主题，避免 Streamlit 默认主题覆盖图表背景。"""
    st.plotly_chart(
        fig,
        use_container_width=True,
        theme=None,
        config=PLOTLY_CONFIG,
    )


def yield_trend_chart(yield_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if yield_df is None or yield_df.empty:
        return style_figure(fig)

    x_position = 0
    tick_vals: List[int] = []
    tick_text: List[str] = []
    for lot_id in yield_df["Lot_Short"].dropna().unique():
        lot_data = yield_df[yield_df["Lot_Short"] == lot_id].copy()
        xs = list(range(x_position, x_position + len(lot_data)))
        x_position += len(lot_data)
        tick_vals.extend(xs)
        tick_text.extend(lot_data["Wafer_ID"].astype(str).tolist())
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=lot_data["Yield_Numeric"],
                mode="lines+markers",
                name=str(lot_id),
                line=dict(width=3),
                marker=dict(size=8),
                customdata=lot_data[["Lot_ID", "Wafer_ID"]].astype(str).values,
                hovertemplate="<b>%{customdata[0]}</b><br>Wafer: %{customdata[1]}<br>良率: %{y:.2f}%<extra></extra>",
            )
        )

    mean_value = yield_df["Yield_Numeric"].mean()
    if not pd.isna(mean_value):
        fig.add_hline(y=mean_value, line_dash="dash", line_color="#e74c3c", annotation_text=f"平均 {mean_value:.2f}%")
    fig.update_layout(title="📈 Wafer 良率趋势", xaxis_title="Wafer 编号", yaxis_title="良率 (%)", hovermode="x unified")
    fig.update_xaxes(tickmode="array", tickvals=tick_vals, ticktext=tick_text)
    return style_figure(fig)


def bin_pareto_chart(bin_counts: pd.Series) -> go.Figure:
    fig = go.Figure()
    if bin_counts.empty:
        return style_figure(fig)
    bins = [f"Bin {b}" for b in bin_counts.index]
    values = bin_counts.values
    colors = ["#2ecc71" if int(b) == 1 else "#e74c3c" for b in bin_counts.index]
    fig.add_trace(go.Bar(x=bins, y=values, marker_color=colors, name="数量"))
    fig.update_layout(title="🎯 Bin 分布", xaxis_title="Bin", yaxis_title="Die 数量")
    return style_figure(fig)


def failure_pareto_chart(bin_counts: pd.Series, pass_bin: int) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fail_counts = bin_counts[bin_counts.index.astype(int) != int(pass_bin)] if not bin_counts.empty else pd.Series(dtype="int64")
    fail_counts = fail_counts[fail_counts > 0].sort_values(ascending=False)
    if fail_counts.empty:
        return style_figure(go.Figure())

    labels = [f"Bin {b}" for b in fail_counts.index]
    values = fail_counts.values
    cumulative = np.cumsum(values) / values.sum() * 100
    fig.add_trace(
        go.Bar(x=labels, y=values, name="失效数量", marker_color="#e74c3c"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=labels, y=cumulative, name="累计占比", mode="lines+markers", line=dict(color="#4dabf7", width=3)),
        secondary_y=True,
    )
    fig.update_layout(title="📋 失效 Bin Pareto", xaxis_title="失效 Bin")
    fig.update_yaxes(title_text="Die 数量", secondary_y=False)
    fig.update_yaxes(title_text="累计占比 (%)", range=[0, 105], secondary_y=True)
    return style_figure(fig)


def parameter_boxplot(cleaned: pd.DataFrame, parameter: str, spec_info: Dict[str, object]) -> go.Figure:
    fig = go.Figure()
    if cleaned is None or parameter not in cleaned.columns:
        return style_figure(fig)

    base_cols = [c for c in ["Lot_ID", "Wafer_ID"] if c in cleaned.columns]
    df = cleaned[base_cols + [parameter]].copy()
    df[parameter] = pd.to_numeric(df[parameter], errors="coerce")
    df = df.dropna(subset=[parameter])
    if df.empty:
        return style_figure(fig)

    df, tick_vals, tick_text, lot_order = prepare_wafer_axis(df)
    palette = ["#4dabf7", "#2ecc71", "#f39c12", "#9b59b6", "#e67e22", "#1abc9c", "#e74c3c", "#95a5a6"]
    shown_lots = set()

    for (lot_id, wafer_id), wafer_data in df.groupby(["Lot_Short", "Wafer_Text"], sort=False):
        values = wafer_data[parameter].dropna().to_numpy(dtype=float)
        if len(values) == 0:
            continue
        x_pos = wafer_data["x_position"].iloc[0]
        q1 = float(np.percentile(values, 25))
        median = float(np.percentile(values, 50))
        q3 = float(np.percentile(values, 75))
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        normal_values = values[(values >= lower_bound) & (values <= upper_bound)]
        lower_fence = float(normal_values.min()) if len(normal_values) else q1
        upper_fence = float(normal_values.max()) if len(normal_values) else q3
        color = palette[lot_order.index(str(lot_id)) % len(palette)] if str(lot_id) in lot_order else palette[0]
        showlegend = str(lot_id) not in shown_lots
        shown_lots.add(str(lot_id))
        fig.add_trace(
            go.Box(
                x=[x_pos],
                q1=[q1],
                median=[median],
                q3=[q3],
                lowerfence=[lower_fence],
                upperfence=[upper_fence],
                name=str(lot_id),
                showlegend=showlegend,
                boxpoints=False,
                width=0.6,
                marker=dict(color=color),
                line=dict(color=color, width=1.5),
                customdata=[[str(lot_id), str(wafer_id), len(values), values.min(), values.max()]],
                hovertemplate=(
                    "Lot: %{customdata[0]}<br>"
                    "Wafer: %{customdata[1]}<br>"
                    "Count: %{customdata[2]:,}<br>"
                    "Min: %{customdata[3]:g}<br>"
                    "Q1: %{q1:g}<br>"
                    "Median: %{median:g}<br>"
                    "Q3: %{q3:g}<br>"
                    "Max: %{customdata[4]:g}<extra></extra>"
                ),
            )
        )

    lower = spec_info.get("limit_lower")
    upper = spec_info.get("limit_upper")
    if lower is not None:
        fig.add_hline(y=lower, line_dash="dash", line_color="#e74c3c", annotation_text=f"LSL {lower:g}")
    if upper is not None:
        fig.add_hline(y=upper, line_dash="dash", line_color="#e74c3c", annotation_text=f"USL {upper:g}")
    unit = f" [{spec_info.get('unit')}]" if spec_info.get("unit") else ""
    fig.update_layout(
        title=f"📊 {parameter}{unit} BoxPlot",
        xaxis_title="Wafer_ID",
        yaxis_title=f"{parameter}{unit}",
        showlegend=len(lot_order) > 1,
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=tick_vals,
        ticktext=tick_text,
        range=[-0.5, max(len(tick_vals) - 0.5, 0.5)],
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(211, 211, 211, 0.5)",
        griddash="dash",
    )
    y_axis_updates = {
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(211, 211, 211, 0.5)",
        "griddash": "dash",
    }
    if lower is not None and upper is not None:
        lsl = min(float(lower), float(upper))
        usl = max(float(lower), float(upper))
        span = usl - lsl
        padding = abs(usl * 0.1) if span == 0 and usl != 0 else (1.0 if span == 0 else span * 0.1)
        y_axis_updates["range"] = [lsl - padding, usl + padding]
    fig.update_yaxes(**y_axis_updates)
    return style_figure(fig, height=560)


def parameter_scatter_chart(cleaned: pd.DataFrame, parameter: str, spec_info: Dict[str, object], max_points: int) -> go.Figure:
    fig = go.Figure()
    if cleaned is None or parameter not in cleaned.columns:
        return style_figure(fig)

    base_cols = [c for c in ["Lot_ID", "Wafer_ID"] if c in cleaned.columns]
    cols = base_cols + [parameter]
    if "Bin" in cleaned.columns:
        cols.append("Bin")
    df = cleaned[cols].copy()
    df[parameter] = pd.to_numeric(df[parameter], errors="coerce")
    df = df.dropna(subset=[parameter])
    if df.empty:
        return style_figure(fig)

    df, tick_vals, tick_text, lot_order = prepare_wafer_axis(df)
    plot_df = sample_dataframe(df, max_points)
    rng = np.random.default_rng(42)
    palette = ["#4dabf7", "#2ecc71", "#f39c12", "#9b59b6", "#e67e22", "#1abc9c", "#e74c3c", "#95a5a6"]

    for lot_id in lot_order:
        lot_data = plot_df[plot_df["Lot_Short"].astype(str) == str(lot_id)].copy()
        if lot_data.empty:
            continue
        jitter = rng.uniform(-0.16, 0.16, len(lot_data))
        bin_values = lot_data["Bin"].astype(str).values if "Bin" in lot_data.columns else np.array([""] * len(lot_data))
        color = palette[lot_order.index(str(lot_id)) % len(palette)]
        # 此页面会同时渲染所有参数。Scattergl 每张图都会占用浏览器 WebGL
        # 上下文，参数较多时后面的图会只剩标题/图例而没有点。这里使用 SVG
        # Scatter，配合上方的固定上限抽样，保证整页图表稳定显示。
        fig.add_trace(
            go.Scatter(
                x=lot_data["x_position"].to_numpy(dtype=float) + jitter,
                y=lot_data[parameter],
                mode="markers",
                name=str(lot_id),
                marker=dict(size=4, opacity=0.62, color=color, line=dict(width=0)),
                customdata=np.column_stack([lot_data["Wafer_Text"].astype(str).values, bin_values]),
                hovertemplate=(
                    f"Lot: {lot_id}<br>"
                    "Wafer: %{customdata[0]}<br>"
                    "Bin: %{customdata[1]}<br>"
                    f"{parameter}: %{{y:g}}<extra></extra>"
                ),
            )
        )

    lower = spec_info.get("limit_lower")
    upper = spec_info.get("limit_upper")
    if lower is not None:
        fig.add_hline(y=lower, line_dash="dash", line_color="#e74c3c", annotation_text=f"LSL {lower:g}")
    if upper is not None:
        fig.add_hline(y=upper, line_dash="dash", line_color="#e74c3c", annotation_text=f"USL {upper:g}")
    unit = f" [{spec_info.get('unit')}]" if spec_info.get("unit") else ""
    fig.update_layout(
        title=f"🔵 {parameter}{unit} Wafer 散点图",
        xaxis_title="Wafer_ID",
        yaxis_title=f"{parameter}{unit}",
        showlegend=len(lot_order) > 1,
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=tick_vals,
        ticktext=tick_text,
        range=[-0.5, max(len(tick_vals) - 0.5, 0.5)],
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(211, 211, 211, 0.5)",
        griddash="dash",
    )
    y_axis_updates = {
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(211, 211, 211, 0.5)",
        "griddash": "dash",
    }
    if lower is not None and upper is not None:
        lsl = min(float(lower), float(upper))
        usl = max(float(lower), float(upper))
        span = usl - lsl
        padding = abs(usl * 0.1) if span == 0 and usl != 0 else (1.0 if span == 0 else span * 0.1)
        y_axis_updates["range"] = [lsl - padding, usl + padding]
    fig.update_yaxes(**y_axis_updates)
    return style_figure(fig, height=560)


def zone_yield_chart(cleaned: Optional[pd.DataFrame], pass_bin: int) -> go.Figure:
    zone_df = cleaned_with_zone(cleaned, pass_bin)
    fig = go.Figure()
    if zone_df.empty:
        return style_figure(fig)

    zone_order = ["Center", "Mid", "Edge"]
    grouped = zone_df.groupby("Zone", observed=False).agg(total=("Bin", "size"), passed=("Pass", "sum")).reindex(zone_order)
    grouped["yield"] = grouped["passed"] / grouped["total"].replace(0, np.nan) * 100
    fig.add_trace(
        go.Bar(
            x=grouped.index,
            y=grouped["yield"],
            marker_color=["#2ecc71", "#f39c12", "#e74c3c"],
            customdata=grouped[["total", "passed"]].fillna(0).astype(int).values,
            hovertemplate="区域: %{x}<br>良率: %{y:.2f}%<br>总数: %{customdata[0]:,}<br>良品: %{customdata[1]:,}<extra></extra>",
        )
    )
    fig.update_layout(title="🎯 Center / Mid / Edge 区域良率", xaxis_title="Wafer 区域", yaxis_title="良率 (%)")
    return style_figure(fig)


def zone_fail_bin_chart(cleaned: Optional[pd.DataFrame], pass_bin: int) -> go.Figure:
    zone_df = cleaned_with_zone(cleaned, pass_bin)
    fig = go.Figure()
    if zone_df.empty:
        return style_figure(fig)

    fail_df = zone_df[zone_df["Bin"] != pass_bin].copy()
    if fail_df.empty:
        return style_figure(fig)
    pivot = pd.pivot_table(fail_df, index="Zone", columns="Bin", values="X", aggfunc="count", fill_value=0)
    pivot = pivot.reindex(["Center", "Mid", "Edge"]).fillna(0)
    for bin_id in pivot.columns:
        fig.add_trace(go.Bar(x=pivot.index, y=pivot[bin_id], name=f"Bin {int(bin_id)}"))
    fig.update_layout(title="🔬 分区域失效 Bin 结构", xaxis_title="Wafer 区域", yaxis_title="失效 Die 数量", barmode="stack")
    return style_figure(fig)


def zone_parameter_boxplot(cleaned: Optional[pd.DataFrame], parameter: str, pass_bin: int, max_points: int) -> go.Figure:
    zone_df = cleaned_with_zone(cleaned, pass_bin)
    fig = go.Figure()
    if cleaned is None or zone_df.empty or parameter not in cleaned.columns:
        return style_figure(fig)

    values = pd.to_numeric(cleaned.loc[zone_df.index, parameter], errors="coerce")
    plot_df = zone_df.assign(value=values).dropna(subset=["value"])
    plot_df = sample_dataframe(plot_df, max_points)
    for zone in ["Center", "Mid", "Edge"]:
        sub = plot_df[plot_df["Zone"] == zone]
        if sub.empty:
            continue
        fig.add_trace(go.Box(y=sub["value"], name=zone, boxpoints="outliers", marker=dict(size=3)))
    fig.update_layout(title=f"📊 区域参数分布：{parameter}", xaxis_title="Wafer 区域", yaxis_title=parameter)
    return style_figure(fig)


def wafer_summary_table(cleaned: Optional[pd.DataFrame], spec: Optional[pd.DataFrame], params: List[str]) -> pd.DataFrame:
    if cleaned is None or "Wafer_ID" not in cleaned.columns or not params:
        return pd.DataFrame()

    wafers = sorted(cleaned["Wafer_ID"].astype(str).dropna().unique(), key=wafer_sort_key)
    rows = []
    for param in params:
        if param not in cleaned.columns:
            continue
        spec_info = get_spec_info(spec, param)
        lower = spec_info.get("limit_lower")
        upper = spec_info.get("limit_upper")
        spec_text = ""
        if lower is not None or upper is not None:
            spec_text = f"{'' if lower is None else f'{lower:g}'} ~ {'' if upper is None else f'{upper:g}'}"
        per_wafer = {}
        for wafer in wafers:
            vals = pd.to_numeric(cleaned.loc[cleaned["Wafer_ID"].astype(str) == wafer, param], errors="coerce").dropna()
            if len(vals) < 1:
                per_wafer[wafer] = None
                continue
            median = vals.median()
            mad = (vals - median).abs().median()
            per_wafer[wafer] = {
                "Avg.": vals.mean(),
                "Std": vals.std(),
                "Median": median,
                "RobustStd": mad * 1.4826,
            }
        for stat_name in ["Avg.", "Std", "Median", "RobustStd"]:
            row = {"Item": param, "Spec": spec_text, "Stat": stat_name}
            for wafer in wafers:
                wafer_stats = per_wafer.get(wafer)
                value = np.nan if wafer_stats is None else wafer_stats.get(stat_name, np.nan)
                row[f"{wafer}#"] = value
            rows.append(row)
    return pd.DataFrame(rows)


def failure_overlay_chart(cleaned: Optional[pd.DataFrame], pass_bin: int, wafer_id: str, max_points: int) -> go.Figure:
    fig = go.Figure()
    if cleaned is None or not {"Wafer_ID", "X", "Y", "Bin"}.issubset(cleaned.columns):
        return style_figure(fig)

    df = cleaned[["Lot_ID", "Wafer_ID", "X", "Y", "Bin"]].copy()
    df["X"] = pd.to_numeric(df["X"], errors="coerce")
    df["Y"] = pd.to_numeric(df["Y"], errors="coerce")
    df["Bin"] = pd.to_numeric(df["Bin"], errors="coerce")
    df = df.dropna(subset=["Wafer_ID", "X", "Y", "Bin"])
    if wafer_id != "全部 Wafer":
        df = df[df["Wafer_ID"].astype(str) == wafer_id]
    df = df[df["Bin"] != pass_bin]
    if df.empty:
        return style_figure(fig)
    df = sample_dataframe(df, max_points)
    fig.add_trace(
        go.Scattergl(
            x=df["X"],
            y=df["Y"],
            mode="markers",
            marker=dict(color=df["Bin"], colorscale="Turbo", size=7, opacity=0.78, colorbar=dict(title="Fail Bin")),
            text=df["Lot_ID"].astype(str),
            customdata=df[["Wafer_ID", "Bin"]].astype(str).values,
            hovertemplate="Lot: %{text}<br>Wafer: %{customdata[0]}<br>Bin: %{customdata[1]}<br>X=%{x}, Y=%{y}<extra></extra>",
        )
    )
    fig.update_layout(title=f"🔍 失效点位叠加：{wafer_id}", xaxis_title="X", yaxis_title="Y")
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return style_figure(fig, height=620)


def cpk_table(cleaned: pd.DataFrame, spec: Optional[pd.DataFrame], params: List[str]) -> pd.DataFrame:
    rows = []
    if cleaned is None:
        return pd.DataFrame()
    for param in params:
        vals = pd.to_numeric(cleaned[param], errors="coerce").dropna()
        if len(vals) < 2:
            continue
        info = get_spec_info(spec, param)
        std = vals.std()
        lower = info.get("limit_lower")
        upper = info.get("limit_upper")
        cpk = np.nan
        if std and std > 0 and lower is not None and upper is not None:
            cpk = min((vals.mean() - float(lower)) / (3 * std), (float(upper) - vals.mean()) / (3 * std))
        rows.append(
            {
                "参数": param,
                "单位": info.get("unit", ""),
                "样本数": len(vals),
                "均值": vals.mean(),
                "标准差": std,
                "LSL": lower,
                "USL": upper,
                "Cpk": cpk,
                "低于LSL": int((vals < lower).sum()) if lower is not None else np.nan,
                "高于USL": int((vals > upper).sum()) if upper is not None else np.nan,
            }
        )
    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("Cpk", na_position="last")
    return result


def main() -> None:
    st.set_page_config(page_title="CP 数据分析 Cockpit", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
    inject_cockpit_theme()
    render_hero()

    st.sidebar.markdown("### ⚙️ 分析表单")
    default_data_dir = get_default_data_dir()
    if st.session_state.get("_default_data_dir") != default_data_dir:
        st.session_state["_default_data_dir"] = default_data_dir
        st.session_state["cp_data_dir"] = default_data_dir
    data_dir = st.sidebar.text_input(
        "标准 CSV 输出目录",
        key="cp_data_dir",
        help="目录内应包含 *_cleaned_*.csv、*_yield_*.csv、*_spec_*.csv",
    )
    pass_bin = int(st.sidebar.number_input("Pass Bin", min_value=0, max_value=999, value=1, step=1))
    max_points = int(st.sidebar.slider("单张散点图最大样本数", 1000, 50000, 8000, step=1000))
    reload_clicked = st.sidebar.button("🔄 重新加载数据", type="primary")
    if reload_clicked:
        load_standard_dataset.clear()

    dataset = load_standard_dataset(data_dir)
    render_file_status(dataset)

    if dataset.cleaned is None and dataset.yield_df is None:
        st.warning("未找到可分析的标准 CSV。请先用 CP 清洗流程生成 cleaned / yield / spec 文件。")
        st.stop()

    summary = dataset_summary(dataset, pass_bin=pass_bin)
    params = available_parameters(dataset.cleaned)
    yield_df = normalize_yield_data(dataset.yield_df)
    render_metric_cards(summary)

    tabs = st.tabs([
        "🎯 BIN总览",
        "📋 Pareto",
        "📈 良率趋势",
        "📊 参数BoxPlot",
        "🔵 散点相关",
        "🗺️ Wafer Mapping",
        "🎯 区域分析",
        "🔍 失效叠加",
        "📊 Wafer Summary",
        "⚠ Cpk/超限",
        "💾 数据表",
    ])

    with tabs[0]:
        st.markdown("#### Bin 结构")
        render_bin_grid(summary["bin_counts"], int(summary["total_die"]))
        render_plotly_chart(bin_pareto_chart(summary["bin_counts"]))

    with tabs[1]:
        st.markdown("#### 失效 Pareto")
        st.caption("排除 Pass Bin 后，按失效数量从高到低排序，用于质量部门快速抓主因。")
        render_plotly_chart(failure_pareto_chart(summary["bin_counts"], pass_bin=pass_bin))

    with tabs[2]:
        if yield_df is None:
            st.info("当前目录没有 yield CSV，无法展示 wafer 级良率趋势。")
        else:
            render_plotly_chart(yield_trend_chart(yield_df))
            st.dataframe(yield_df.drop(columns=["_Wafer_Sort"], errors="ignore"), use_container_width=True)

    with tabs[3]:
        if not params:
            st.info("cleaned CSV 中没有识别到数值测试参数。")
        else:
            st.caption("按 Huahong 箱体图的轴逻辑展示：X 轴为 Lot/Wafer 顺序，刻度显示 Wafer_ID；Y 轴为参数值。这里只显示箱线图，不叠加原始散点。")
            for parameter in params:
                spec_info = get_spec_info(dataset.spec, parameter)
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("参数", parameter)
                col2.metric("单位", spec_info.get("unit") or "N/A")
                col3.metric("LSL", "N/A" if spec_info.get("limit_lower") is None else f"{spec_info['limit_lower']:g}")
                col4.metric("USL", "N/A" if spec_info.get("limit_upper") is None else f"{spec_info['limit_upper']:g}")
                render_plotly_chart(parameter_boxplot(dataset.cleaned, parameter, spec_info))

    with tabs[4]:
        if not params:
            st.info("cleaned CSV 中没有识别到数值测试参数。")
        else:
            st.caption("按 Huahong/BoxPlot 的轴逻辑展示：X 轴为 Lot/Wafer 顺序，刻度显示 Wafer_ID；Y 轴为参数值。每个参数生成一张散点图。")
            for parameter in params:
                render_plotly_chart(
                    parameter_scatter_chart(
                        dataset.cleaned,
                        parameter,
                        get_spec_info(dataset.spec, parameter),
                        max_points=max_points,
                    ),
                )

    with tabs[5]:
        cleaned = dataset.cleaned
        if cleaned is None or not {"Wafer_ID", "X", "Y"}.issubset(cleaned.columns):
            st.info("当前 cleaned CSV 缺少 Wafer_ID/X/Y，无法绘制 Wafer Mapping。")
        elif not has_spatial_coordinates(cleaned):
            st.warning(
                "当前 cleaned CSV 的 X/Y 没有形成二维坐标（例如全部为 0），无法生成真实 Wafer Mapping。"
                "请回到 Reader / Adapter 检查晶圆坐标来源。"
            )
        else:
            st.caption(
                "晶圆厂常用 Mapping 视图：每个方格代表一个 die。可一次查看全部 Lot/Wafer 的同一参数，"
                "也可选择 1～25 片查看逐 die 详情。综合 Bin 高亮 Bin 不良；测试参数按 LSL/USL 高亮超限 die。"
            )
            map_col1, map_col2 = st.columns([2, 2])
            mapping_choice = map_col1.selectbox("选择 Mapping 项目", ["综合 Bin"] + params, key="wafer_mapping_item")
            display_mode = map_col2.radio(
                "展示范围",
                ["全部 Wafer 总览", "选择 Wafer 详看"],
                horizontal=True,
                key="wafer_mapping_display_mode",
            )
            mapping_parameter = None if mapping_choice == "综合 Bin" else mapping_choice
            mapping_spec = get_spec_info(dataset.spec, mapping_parameter) if mapping_parameter else None
            try:
                mapping_result = prepare_wafer_mapping(
                    cleaned,
                    parameter=mapping_parameter,
                    spec_info=mapping_spec,
                    pass_bin=pass_bin,
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                wafer_keys = wafer_mapping_wafer_keys(mapping_result)
                selected_result = mapping_result
                include_hover = False
                if display_mode == "选择 Wafer 详看":
                    wafer_labels = [f"{lot} / W{wafer}" for lot, wafer in wafer_keys]
                    label_to_key = dict(zip(wafer_labels, wafer_keys))
                    selected_labels = st.multiselect(
                        "选择 Wafer（最多 25 片）",
                        wafer_labels,
                        default=wafer_labels[: min(25, len(wafer_labels))],
                        key="wafer_mapping_selected_wafers",
                        max_selections=25,
                    )
                    selected_result = filter_wafer_mapping(
                        mapping_result,
                        [label_to_key[label] for label in selected_labels],
                    )
                    include_hover = True
                    st.caption("详看模式已启用逐 die 悬浮详情，可查看坐标、Bin、参数值和复测次数。")
                else:
                    st.caption(
                        f"当前共 {len(wafer_keys):,} 片，已启用轻量总览：保留全部 die 着色，关闭逐 die 悬浮详情。"
                        "如需查看具体数值，请切换到“选择 Wafer 详看”。"
                    )

                selected_count = wafer_mapping_summary(selected_result)["wafers"]
                default_columns = 8 if display_mode == "全部 Wafer 总览" and selected_count > 25 else 6
                mapping_columns = int(
                    st.slider(
                        "每行 Wafer 数",
                        2,
                        8,
                        min(default_columns, max(2, selected_count)),
                        key=f"wafer_mapping_columns_{'all' if display_mode == '全部 Wafer 总览' else 'detail'}",
                    )
                )
                mapping_stats = wafer_mapping_summary(selected_result)
                stat1, stat2, stat3, stat4 = st.columns(4)
                stat1.metric("当前展示 Wafer", f"{mapping_stats['wafers']:,}")
                stat2.metric("有效判定 die", f"{mapping_stats['judged']:,}")
                stat3.metric("不良 die", f"{mapping_stats['fail']:,}")
                fail_rate = mapping_stats["fail"] / mapping_stats["judged"] * 100 if mapping_stats["judged"] else 0
                stat4.metric("不良占比", f"{fail_rate:.2f}%")
                if mapping_stats["duplicate_coordinates"]:
                    duplicate_hint = (
                        "同一坐标按最高不良优先级展示，悬浮可查看该坐标记录数。"
                        if include_hover
                        else "同一坐标按最高不良优先级展示；切换到详看模式可查看复测记录数。"
                    )
                    st.caption(
                        f"检测到 {mapping_stats['duplicate_coordinates']:,} 条同 Lot/Wafer/X/Y 的复测记录；"
                        f"{duplicate_hint}"
                    )
                mapping_fig = wafer_mapping_grid(
                    selected_result,
                    columns=mapping_columns,
                    include_hover=include_hover,
                )
                mapping_fig = style_figure(mapping_fig, height=int(mapping_fig.layout.height))
                mapping_fig.update_layout(
                    margin=dict(l=36, r=28, t=140, b=36),
                    legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="right", x=1),
                )
                render_plotly_chart(mapping_fig)

    with tabs[6]:
        cleaned = dataset.cleaned
        if cleaned is None or not {"Wafer_ID", "X", "Y", "Bin"}.issubset(cleaned.columns):
            st.info("区域分析需要 cleaned CSV 包含 Wafer_ID、X、Y、Bin。")
        else:
            st.caption("区域按每片 Wafer 的相对半径划分：Center 0-33%，Mid 33-66%，Edge 66-100%。")
            render_plotly_chart(zone_yield_chart(cleaned, pass_bin=pass_bin))
            render_plotly_chart(zone_fail_bin_chart(cleaned, pass_bin=pass_bin))
            if params:
                zone_param = st.selectbox("区域参数分布", params, key="zone_param")
                render_plotly_chart(zone_parameter_boxplot(cleaned, zone_param, pass_bin=pass_bin, max_points=max_points))

    with tabs[7]:
        cleaned = dataset.cleaned
        if cleaned is None or not {"Wafer_ID", "X", "Y", "Bin"}.issubset(cleaned.columns):
            st.info("失效叠加需要 cleaned CSV 包含 Wafer_ID、X、Y、Bin。")
        else:
            wafers = sorted(cleaned["Wafer_ID"].astype(str).dropna().unique(), key=wafer_sort_key)
            overlay_wafer = st.selectbox("选择叠加范围", ["全部 Wafer"] + wafers, key="overlay_wafer")
            render_plotly_chart(failure_overlay_chart(cleaned, pass_bin=pass_bin, wafer_id=overlay_wafer, max_points=max_points))

    with tabs[8]:
        if not params:
            st.info("没有可生成 Wafer Summary 的参数。")
        else:
            selected_params = st.multiselect("选择参数", params, default=params[: min(8, len(params))], key="wsum_params")
            wsum_df = wafer_summary_table(dataset.cleaned, dataset.spec, selected_params)
            if wsum_df.empty:
                st.info("当前数据无法生成 Wafer Summary。")
            else:
                st.dataframe(wsum_df, use_container_width=True)
                csv = wsum_df.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("⬇ 导出 Wafer Summary", data=csv, file_name="cp_wafer_summary.csv", mime="text/csv")

    with tabs[9]:
        if not params:
            st.info("没有可计算 Cpk 的参数。")
        else:
            cpk_df = cpk_table(dataset.cleaned, dataset.spec, params)
            if cpk_df.empty:
                st.info("spec 信息不足或参数数据不足，暂无法计算 Cpk。")
            else:
                st.dataframe(cpk_df, use_container_width=True)
                csv = cpk_df.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("⬇ 导出 Cpk/超限表", data=csv, file_name="cp_cpk_limit_summary.csv", mime="text/csv")

    with tabs[10]:
        view = st.radio("选择数据表", ["cleaned", "yield", "spec"], horizontal=True)
        table = {"cleaned": dataset.cleaned, "yield": dataset.yield_df, "spec": dataset.spec}[view]
        if table is None:
            st.info(f"未找到 {view} CSV。")
        else:
            st.dataframe(table.head(5000), use_container_width=True)
            st.caption("为保持前端流畅，页面预览最多显示前 5000 行；下载/原始文件仍保留完整数据。")


if __name__ == "__main__":
    main()
