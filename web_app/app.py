from __future__ import annotations

from html import escape
import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from web_app.charts import (
    bin_failure_chart,
    lot_comparison,
    parameter_box,
    parameter_scatter,
    yield_distribution,
    yield_trend,
)
from web_app.data_service import (
    DataBundle,
    dynamic_bin_columns,
    excel_sheet_names,
    filter_by_lot_and_wafer,
    first_existing_column,
    load_bundle,
    parameter_columns,
    parameter_spec,
    read_table_file,
    wafer_yield_data,
)
from web_app.native_picker import pick_folder, pick_table_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = os.environ.get("CP_DATA_DIR", str(PROJECT_ROOT / "output"))
PLOT_CONFIG = {"displaylogo": False, "scrollZoom": True, "responsive": True}


st.set_page_config(
    page_title="NCE CP Data Cockpit",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root { --cyan:#23d5ff; --purple:#8b5cf6; --panel:rgba(10,22,43,.78); }
        .stApp {
          background:
            radial-gradient(circle at 18% 8%, rgba(35,213,255,.13), transparent 28%),
            radial-gradient(circle at 86% 4%, rgba(139,92,246,.16), transparent 30%),
            linear-gradient(145deg, #050a14 0%, #081225 47%, #050913 100%);
          color: #e9f2ff;
        }
        [data-testid="stSidebar"] {
          background: linear-gradient(180deg, rgba(8,18,37,.98), rgba(6,12,25,.98));
          border-right: 1px solid rgba(74,184,255,.18);
        }
        [data-testid="stHeader"] { background: rgba(5,10,20,.72); }
        .block-container { max-width: 1500px; padding-top: 1.4rem; padding-bottom: 3rem; }
        .hero {
          position: relative; overflow: hidden; padding: 28px 32px; margin: 0 0 18px 0;
          border: 1px solid rgba(77,205,255,.25); border-radius: 22px;
          background: linear-gradient(115deg, rgba(12,31,59,.94), rgba(20,17,53,.86));
          box-shadow: 0 18px 60px rgba(0,0,0,.35), inset 0 1px rgba(255,255,255,.04);
        }
        .hero:after { content:""; position:absolute; width:360px; height:360px; right:-90px; top:-200px;
          border-radius:50%; background:radial-gradient(circle, rgba(35,213,255,.35), transparent 66%); }
        .hero-kicker { color:#5ce6ff; font-size:.78rem; font-weight:700; letter-spacing:.2em; }
        .hero h1 { margin:.35rem 0 .25rem; font-size:2.15rem; color:#f6fbff; letter-spacing:-.02em; }
        .hero p { color:#9eb4d2; margin:0; font-size:1rem; overflow-wrap:anywhere; }
        .status-dot { display:inline-block; width:8px; height:8px; margin-right:7px; border-radius:50%;
          background:#35f2a1; box-shadow:0 0 14px #35f2a1; }
        .metric-card { padding:18px 18px 16px; min-height:112px; border-radius:18px;
          border:1px solid rgba(91,172,255,.18); background:linear-gradient(145deg, rgba(15,32,59,.88), rgba(10,20,40,.82));
          box-shadow:0 12px 30px rgba(0,0,0,.24); }
        .metric-label { color:#8298b8; font-size:.77rem; letter-spacing:.08em; text-transform:uppercase; }
        .metric-value { margin-top:8px; color:#f2f7ff; font-size:1.72rem; font-weight:750; }
        .metric-note { margin-top:4px; color:#35d9ff; font-size:.76rem; }
        [data-testid="stTabs"] button { font-weight:650; }
        [data-testid="stDataFrame"] { border:1px solid rgba(83,174,255,.18); border-radius:14px; overflow:hidden; }
        .stButton>button, .stDownloadButton>button { border-radius:12px; border:1px solid rgba(63,211,255,.35);
          background:linear-gradient(120deg, rgba(19,111,170,.88), rgba(100,54,190,.84)); color:white; }
        .stButton>button:hover, .stDownloadButton>button:hover { border-color:#63e5ff; box-shadow:0 0 20px rgba(35,213,255,.22); }
        div[data-testid="stExpander"] { border-color:rgba(86,168,255,.18); background:rgba(8,18,36,.54); }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def cached_bundle(path: str, fingerprint: tuple[tuple[str, int, int], ...]) -> DataBundle:
    del fingerprint
    return load_bundle(path)


def directory_fingerprint(path: str) -> tuple[tuple[str, int, int], ...]:
    root = Path(path).expanduser()
    if not root.is_dir():
        return ()
    return tuple(sorted((item.name, item.stat().st_mtime_ns, item.stat().st_size) for item in root.glob("*.csv")))


@st.cache_data(show_spinner=False)
def cached_table_preview(path: str, sheet_name: str | int, modified_ns: int, size: int) -> pd.DataFrame:
    del modified_ns, size
    return read_table_file(path, sheet_name=sheet_name)


@st.cache_data(show_spinner=False)
def cached_sheet_names(path: str, modified_ns: int, size: int) -> list[str]:
    del modified_ns, size
    return excel_sheet_names(path)


def metric_card(label: str, value: object, note: str) -> None:
    st.markdown(
        f"<div class='metric-card'><div class='metric-label'>{escape(str(label))}</div>"
        f"<div class='metric-value'>{escape(str(value))}</div>"
        f"<div class='metric-note'>{escape(str(note))}</div></div>",
        unsafe_allow_html=True,
    )


def csv_download(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8-sig")


def html_report(figures: list[go.Figure], title: str) -> bytes:
    fragments: list[str] = []
    for index, figure in enumerate(figures):
        fragments.append(figure.to_html(full_html=False, include_plotlyjs=True if index == 0 else False))
    document = f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>
    <title>{escape(title)}</title><style>body{{background:#07101f;color:#eaf2ff;font-family:Segoe UI,Microsoft YaHei,sans-serif;margin:28px}}
    h1{{color:#55ddff}} .chart{{margin:20px 0}}</style></head><body><h1>{escape(title)}</h1>{''.join(fragments)}</body></html>"""
    return document.encode("utf-8")


def sidebar() -> str:
    st.sidebar.markdown("## ⚡ CP Cockpit")
    st.sidebar.caption("LOCAL ANALYTICS · 数据仅在本机")
    path = st.sidebar.text_input("数据目录", value=st.session_state.get("data_path", DEFAULT_DATA_DIR))
    browse_columns = st.sidebar.columns(2)
    with browse_columns[0]:
        if st.button("📁 选择文件夹", use_container_width=True):
            selected_folder = pick_folder(path if Path(path).is_dir() else None)
            if selected_folder:
                st.session_state["data_path"] = selected_folder
                st.session_state.pop("preview_file", None)
                st.cache_data.clear()
                st.rerun()
    with browse_columns[1]:
        if st.button("📄 选择文件", use_container_width=True):
            selected_file = pick_table_file(path if Path(path).is_dir() else None)
            if selected_file:
                st.session_state["preview_file"] = selected_file
                st.session_state["data_path"] = str(Path(selected_file).parent)
                st.cache_data.clear()
                st.rerun()
    if st.sidebar.button("扫描并加载", use_container_width=True):
        st.session_state["data_path"] = path
        st.cache_data.clear()
    preview_file = st.session_state.get("preview_file")
    if preview_file:
        st.sidebar.caption(f"当前文件 · {Path(preview_file).name}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**文件契约**")
    st.sidebar.caption("`*_cleaned_*.csv`  · Die 明细")
    st.sidebar.caption("`*_yield_*.csv`  · Wafer 良率")
    st.sidebar.caption("`*_spec_*.csv`  · 参数规格")
    st.sidebar.markdown("---")
    st.sidebar.caption("Web MVP v0.1 · codex/web")
    return st.session_state.get("data_path", path)


def selected_file_preview(path: str, key_prefix: str) -> pd.DataFrame | None:
    source = Path(path)
    if not source.is_file():
        st.warning(f"选中的文件已不存在：{source}")
        return None
    try:
        stat = source.stat()
        sheet_name: str | int = 0
        if source.suffix.lower() in {".xlsx", ".xls"}:
            sheet_names = cached_sheet_names(str(source), stat.st_mtime_ns, stat.st_size)
            sheet_name = st.selectbox("Excel 工作表", sheet_names, key=f"{key_prefix}_sheet")
        frame = cached_table_preview(str(source), sheet_name, stat.st_mtime_ns, stat.st_size)
    except Exception as exc:
        st.error(f"表格预览失败：{exc}")
        return None

    row_limit = st.select_slider(
        "预览行数",
        options=[100, 300, 500, 1000, 3000],
        value=500,
        key=f"{key_prefix}_rows",
    )
    st.caption(f"{source.name} · {len(frame):,} 行 × {len(frame.columns):,} 列")
    st.dataframe(frame.head(row_limit), use_container_width=True, height=520)
    st.download_button(
        "下载预览内容 CSV",
        data=csv_download(frame),
        file_name=f"{source.stem}_preview.csv",
        mime="text/csv",
        key=f"{key_prefix}_download",
    )
    return frame


def show_standalone_file(path: str) -> None:
    st.markdown(
        """<div class='hero'><div class='hero-kicker'><span class='status-dot'></span>MANUAL FILE PREVIEW</div>
        <h1>表格文件预览</h1><p>当前文件不是标准分析输出，先展示原始表格内容，不执行良率或规格计算。</p></div>""",
        unsafe_allow_html=True,
    )
    selected_file_preview(path, "standalone")


def show_empty_state(path: str, message: str | None = None) -> None:
    st.markdown(
        """<div class='hero'><div class='hero-kicker'>READY FOR SIGNAL</div>
        <h1>CP Data Cockpit</h1><p>选择一个包含 cleaned、yield、spec CSV 的输出目录，启动晶圆数据分析。</p></div>""",
        unsafe_allow_html=True,
    )
    if message:
        st.error(message)
    else:
        st.info(f"当前等待目录：{path}")
    st.markdown("### 第一版能力")
    cols = st.columns(4)
    for column, (title, detail) in zip(
        cols,
        [
            ("数据预览", "三类 CSV、筛选与下载"),
            ("良率洞察", "Wafer 趋势、Lot 对比、分布"),
            ("失效结构", "动态识别全部 Bin 列"),
            ("参数分析", "箱体分布与双参数散点"),
        ],
    ):
        with column:
            metric_card(title, "ONLINE", detail)


def main() -> None:
    inject_theme()
    data_path = sidebar()
    preview_file = st.session_state.get("preview_file")
    fingerprint = directory_fingerprint(data_path)
    if not fingerprint:
        if preview_file:
            show_standalone_file(preview_file)
        else:
            show_empty_state(data_path)
        return

    try:
        bundle = cached_bundle(data_path, fingerprint)
    except Exception as exc:
        show_empty_state(data_path, f"数据加载失败：{exc}")
        return
    if bundle.is_empty:
        show_empty_state(data_path, "目录中没有找到符合命名契约的 CSV 文件。")
        return

    st.sidebar.success(f"已加载 {len(bundle.files)} 类标准文件")
    for kind, file_path in bundle.files.items():
        st.sidebar.caption(f"{kind.upper()} · {file_path.name}")

    cleaned = bundle.cleaned if bundle.cleaned is not None else pd.DataFrame()
    yield_frame = wafer_yield_data(bundle.yield_data)
    lots_source = cleaned if "Lot_ID" in cleaned.columns else yield_frame
    lots = sorted(lots_source.get("Lot_ID", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    selected_lots = st.sidebar.multiselect("Lot 筛选", lots, default=lots)
    wafer_source = filter_by_lot_and_wafer(lots_source, selected_lots)
    wafers = sorted(wafer_source.get("Wafer_ID", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    selected_wafers = st.sidebar.multiselect("Wafer 筛选", wafers, default=wafers)

    cleaned_filtered = filter_by_lot_and_wafer(cleaned, selected_lots, selected_wafers)
    yield_filtered = filter_by_lot_and_wafer(yield_frame, selected_lots, selected_wafers)

    st.markdown(
        f"""<div class='hero'><div class='hero-kicker'><span class='status-dot'></span>LIVE DATA LINK</div>
        <h1>CP Data Cockpit</h1><p>{escape(str(bundle.directory))} · 标准数据已接入，可交互探索</p></div>""",
        unsafe_allow_html=True,
    )

    gross_column = first_existing_column(yield_filtered, ("Gross_die", "Total"))
    good_column = first_existing_column(yield_filtered, ("Good_die", "Pass"))
    avg_yield = yield_filtered["Yield_Numeric"].mean() if not yield_filtered.empty else float("nan")
    gross = pd.to_numeric(yield_filtered[gross_column], errors="coerce").sum() if gross_column else len(cleaned_filtered)
    good = pd.to_numeric(yield_filtered[good_column], errors="coerce").sum() if good_column else None
    lot_count = cleaned_filtered["Lot_ID"].nunique() if "Lot_ID" in cleaned_filtered.columns else len(selected_lots)
    wafer_count = cleaned_filtered["Wafer_ID"].nunique() if "Wafer_ID" in cleaned_filtered.columns else len(selected_wafers)

    metrics = [
        ("Lot 数", f"{lot_count:,}", "当前筛选范围"),
        ("Wafer 数", f"{wafer_count:,}", "唯一晶圆"),
        ("Gross Die", f"{int(gross):,}", gross_column or "来自 cleaned 行数"),
        ("Good Die", f"{int(good):,}" if good is not None else "—", good_column or "当前文件未提供"),
        ("平均良率", f"{avg_yield:.2f}%" if pd.notna(avg_yield) else "—", "Wafer 加权前均值"),
    ]
    for row_metrics in (metrics[:3], metrics[3:]):
        metric_columns = st.columns(len(row_metrics))
        for column, metric in zip(metric_columns, row_metrics):
            with column:
                metric_card(*metric)

    tabs = st.tabs(["驾驶舱", "数据预览", "良率分析", "Bin 失效", "参数实验室", "报告导出"])
    report_figures: list[go.Figure] = []

    with tabs[0]:
        st.markdown("### 信号总览")
        if not yield_filtered.empty:
            left, right = st.columns([1.55, 1])
            trend = yield_trend(yield_filtered)
            comparison = lot_comparison(yield_filtered)
            report_figures.extend([trend, comparison])
            with left:
                st.plotly_chart(trend, use_container_width=True, config=PLOT_CONFIG)
            with right:
                st.plotly_chart(comparison, use_container_width=True, config=PLOT_CONFIG)
        else:
            st.warning("缺少可用 yield 数据，驾驶舱暂不显示良率图。")

    with tabs[1]:
        st.markdown("### 标准数据透视")
        available = {"cleaned": bundle.cleaned, "yield": bundle.yield_data, "spec": bundle.spec}
        available = {name: frame for name, frame in available.items() if frame is not None}
        preview_options = list(available)
        if preview_file:
            preview_options.insert(0, "手动选择文件")
        selected_kind = st.radio("数据类型", preview_options, horizontal=True)
        if selected_kind == "手动选择文件":
            selected_file_preview(preview_file, "contract_file")
        else:
            preview = available[selected_kind]
            if selected_kind != "spec":
                preview = filter_by_lot_and_wafer(preview, selected_lots, selected_wafers)
            limit = st.select_slider("预览行数", options=[100, 300, 500, 1000, 3000], value=500)
            st.caption(f"共 {len(preview):,} 行 × {len(preview.columns):,} 列；当前显示前 {min(limit, len(preview)):,} 行")
            st.dataframe(preview.head(limit), use_container_width=True, height=520)
            st.download_button(
                "下载当前筛选 CSV",
                data=csv_download(preview),
                file_name=f"{selected_kind}_filtered.csv",
                mime="text/csv",
            )

    with tabs[2]:
        st.markdown("### 良率信号分析")
        if yield_filtered.empty:
            st.warning("yield CSV 缺少 Lot_ID、Wafer_ID 或 Yield，无法生成分析。")
        else:
            first, second = st.columns(2)
            distribution = yield_distribution(yield_filtered)
            comparison = lot_comparison(yield_filtered)
            report_figures.extend([distribution, comparison])
            with first:
                st.plotly_chart(distribution, use_container_width=True, config=PLOT_CONFIG)
            with second:
                st.plotly_chart(comparison, use_container_width=True, config=PLOT_CONFIG)

    with tabs[3]:
        st.markdown("### Bin 失效结构")
        bin_columns = dynamic_bin_columns(yield_filtered)
        if not bin_columns:
            st.warning("当前 yield 数据没有可识别的动态 Bin 计数列。")
        else:
            totals = yield_filtered[bin_columns].apply(pd.to_numeric, errors="coerce").sum().sort_values(ascending=False)
            chart = bin_failure_chart(totals)
            report_figures.append(chart)
            left, right = st.columns([1.45, 1])
            with left:
                st.plotly_chart(chart, use_container_width=True, config=PLOT_CONFIG)
            with right:
                st.markdown("#### 失效排行")
                ranking = totals.rename("Fail_Die").rename_axis("Bin").reset_index()
                ranking["占比"] = ranking["Fail_Die"] / ranking["Fail_Die"].sum()
                st.dataframe(ranking, use_container_width=True, hide_index=True)

    with tabs[4]:
        st.markdown("### 参数实验室")
        parameters = parameter_columns(cleaned_filtered)
        if not parameters:
            st.warning("cleaned CSV 中没有可分析的数值参数。")
        else:
            box_parameter = st.selectbox("分布参数", parameters)
            spec_info = parameter_spec(bundle.spec, box_parameter)
            if spec_info:
                st.caption("规格信息 · " + " · ".join(f"{key}: {value}" for key, value in spec_info.items()))
            box_fig = parameter_box(cleaned_filtered, box_parameter)
            report_figures.append(box_fig)
            st.plotly_chart(box_fig, use_container_width=True, config=PLOT_CONFIG)
            st.markdown("#### 双参数关联")
            cols = st.columns(2)
            with cols[0]:
                x_parameter = st.selectbox("X 参数", parameters, index=0)
            with cols[1]:
                y_parameter = st.selectbox("Y 参数", parameters, index=min(1, len(parameters) - 1))
            if x_parameter == y_parameter:
                st.info("请选择两个不同参数查看相关性。")
            else:
                scatter_fig = parameter_scatter(cleaned_filtered, x_parameter, y_parameter)
                report_figures.append(scatter_fig)
                st.plotly_chart(scatter_fig, use_container_width=True, config=PLOT_CONFIG)

    with tabs[5]:
        st.markdown("### 离线报告")
        st.write("将当前筛选条件下已经生成的图表合并为一个可离线打开的 HTML 文件。")
        if report_figures:
            st.download_button(
                "生成并下载 HTML 报告",
                data=html_report(report_figures, "CP Data Cockpit Report"),
                file_name="cp_data_cockpit_report.html",
                mime="text/html",
            )
        else:
            st.info("当前数据不足，尚未生成可导出的图表。")


if __name__ == "__main__":
    main()
