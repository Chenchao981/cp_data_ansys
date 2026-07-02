from __future__ import annotations

from html import escape
import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from web_app.advanced_charts import (
    bin_pareto,
    capability_metrics,
    correlation_heatmap,
    ecdf_chart,
    parameter_distribution,
    qq_chart,
    scatter_3d,
    scatter_matrix,
    sequence_scatter,
    strongest_parameter_pairs,
    violin_distribution,
    wafer_map,
    wafer_mean_control_chart,
)
from web_app.charts import (
    bin_failure_chart,
    lot_comparison,
    parameter_scatter,
    parameter_wafer_chart,
    yield_distribution,
    yield_trend,
)
from web_app.data_service import (
    DataBundle,
    dynamic_bin_columns,
    excel_sheet_names,
    filter_by_lot_and_wafer,
    first_existing_column,
    parameter_columns,
    parameter_spec,
    read_table_file,
    wafer_yield_data,
)
from web_app.native_picker import pick_folder, pick_table_file
from web_app.source_analyzer import analyze_source, parameter_summary, source_fingerprint


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
def cached_bundle(
    source: str,
    fingerprint: tuple[tuple[str, int, int], ...],
    clean_outliers: bool,
) -> DataBundle:
    del fingerprint
    return analyze_source(source, clean_outliers=clean_outliers)


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


def optional_float(value: object) -> float | None:
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def html_report(
    figures: list[go.Figure],
    title: str,
    metadata: dict[str, object] | None = None,
    yield_frame: pd.DataFrame | None = None,
    parameter_stats: pd.DataFrame | None = None,
) -> bytes:
    fragments: list[str] = []
    for index, figure in enumerate(figures):
        fragments.append(figure.to_html(full_html=False, include_plotlyjs=True if index == 0 else False))
    metadata_html = ""
    if metadata:
        rows = "".join(
            f"<tr><th>{escape(str(key))}</th><td>{escape(str(value))}</td></tr>"
            for key, value in metadata.items()
            if value is not None and key not in {"source_names"}
        )
        metadata_html = f"<h2>数据来源与处理口径</h2><table>{rows}</table>"
    yield_html = ""
    if yield_frame is not None and not yield_frame.empty:
        yield_html = "<h2>Wafer 良率摘要</h2>" + yield_frame.to_html(index=False, border=0)
    stats_html = ""
    if parameter_stats is not None and not parameter_stats.empty:
        stats_html = "<h2>参数统计摘要</h2>" + parameter_stats.to_html(index=False, border=0)
    document = f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>
    <title>{escape(title)}</title><style>body{{background:#07101f;color:#eaf2ff;font-family:Segoe UI,Microsoft YaHei,sans-serif;margin:28px}}
    h1{{color:#55ddff}} h2{{color:#a9eaff;margin-top:32px}} table{{border-collapse:collapse;width:100%;margin:14px 0 28px}}
    th,td{{border:1px solid #28405f;padding:7px 10px;text-align:left}} th{{background:#102642;color:#5ce6ff}}
    tr:nth-child(even){{background:#0b1a30}} .chart{{margin:20px 0}}</style></head><body><h1>{escape(title)}</h1>
    {metadata_html}{yield_html}{stats_html}{''.join(fragments)}</body></html>"""
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
        st.session_state.pop("preview_file", None)
        st.cache_data.clear()
    preview_file = st.session_state.get("preview_file")
    if preview_file:
        st.sidebar.caption(f"当前文件 · {Path(preview_file).name}")
    st.sidebar.markdown("---")
    st.sidebar.selectbox(
        "测量值清洗",
        ["IQR 异常值清洗", "保留原始测量值"],
        key="cleaning_mode",
        help="只处理数值参数，不改变 Bin、坐标和源文件。",
    )
    st.sidebar.markdown("**自动识别输入**")
    st.sidebar.caption("HH DCP/TXT · JT/Lion/国宇 Excel")
    st.sidebar.caption("通用 CSV/Excel · 标准分析 CSV")
    st.sidebar.markdown("---")
    st.sidebar.caption("Raw Analytics v0.3 · codex/web")
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
        <h1>表格文件预览</h1><p>当前文件作为通用表格读取；能识别 Lot、Wafer、Bin 时自动生成完整分析。</p></div>""",
        unsafe_allow_html=True,
    )
    selected_file_preview(path, "standalone")


def show_empty_state(path: str, message: str | None = None) -> None:
    st.markdown(
        """<div class='hero'><div class='hero-kicker'>READY FOR SIGNAL</div>
        <h1>CP Raw Data Analyzer</h1><p>选择原始 CP 数据文件夹或文件，系统自动识别格式、清洗并生成分析。</p></div>""",
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
            ("原始读取", "TXT、CSV、Excel 自动识别"),
            ("良率洞察", "Wafer 趋势、Lot 对比、分布"),
            ("失效结构", "动态识别全部 Bin 列"),
            ("参数全览", "每个参数自动生成 Wafer 箱体与 Die 散点"),
        ],
    ):
        with column:
            metric_card(title, "ONLINE", detail)


def main() -> None:
    inject_theme()
    data_path = sidebar()
    preview_file = st.session_state.get("preview_file")
    analysis_source = preview_file if preview_file and Path(preview_file).is_file() else data_path
    fingerprint = source_fingerprint(analysis_source)
    if not fingerprint:
        show_empty_state(analysis_source, "所选位置没有找到支持的 TXT、DCP、CSV 或 Excel 文件。")
        return

    try:
        clean_outliers = st.session_state.get("cleaning_mode", "IQR 异常值清洗") == "IQR 异常值清洗"
        with st.spinner("正在识别格式、读取并分析原始数据…"):
            bundle = cached_bundle(analysis_source, fingerprint, clean_outliers)
    except Exception as exc:
        show_empty_state(analysis_source, f"原始数据分析失败：{exc}")
        return
    if bundle.is_empty:
        show_empty_state(analysis_source, "适配器没有读取到可分析的数据。")
        return

    st.sidebar.success(f"已识别：{bundle.metadata.get('adapter', bundle.source_kind)}")
    st.sidebar.caption(f"源文件 · {bundle.metadata.get('source_file_count', bundle.metadata.get('file_count', 0))} 个")
    if bundle.metadata.get("pass_bin") is not None:
        st.sidebar.caption(f"Pass Bin · {bundle.metadata['pass_bin']}")

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
    parameter_stats = parameter_summary(cleaned_filtered)

    st.markdown(
        f"""<div class='hero'><div class='hero-kicker'><span class='status-dot'></span>LIVE DATA LINK</div>
        <h1>CP Raw Data Analyzer</h1><p>{escape(str(analysis_source))} · 原始数据已读取并完成内存分析</p></div>""",
        unsafe_allow_html=True,
    )
    st.caption(
        f"适配器：{bundle.metadata.get('adapter', 'Unknown')} · "
        f"源数据 {bundle.metadata.get('raw_rows', len(cleaned)):,} 行 · "
        f"参数 {bundle.metadata.get('parameter_count', len(parameter_columns(cleaned))):,} 个 · "
        f"IQR 替换 {bundle.metadata.get('outlier_replacements', 0):,} 个异常测量值 · "
        "分析结果仅在内存中生成，不要求 yield/spec 中间文件"
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

    parameters = parameter_columns(cleaned_filtered)
    tabs = st.tabs(
        ["驾驶舱", "数据预览", "良率与失效", "Wafer Map", "参数全览", "分布与能力", "参数相关", "SPC 趋势", "报告导出"]
    )
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
        st.markdown("### 内存数据透视")
        available = {"清洗后 Die 明细": bundle.cleaned, "实时良率统计": bundle.yield_data, "内存规格": bundle.spec}
        available = {name: frame for name, frame in available.items() if frame is not None}
        preview_options = list(available)
        if preview_file:
            preview_options.insert(0, "手动选择文件")
        selected_kind = st.radio("数据类型", preview_options, horizontal=True)
        if selected_kind == "手动选择文件":
            selected_file_preview(preview_file, "contract_file")
        else:
            preview = available[selected_kind]
            if selected_kind != "内存规格":
                preview = filter_by_lot_and_wafer(preview, selected_lots, selected_wafers)
            limit = st.select_slider("预览行数", options=[100, 300, 500, 1000, 3000], value=500)
            st.caption(f"共 {len(preview):,} 行 × {len(preview.columns):,} 列；当前显示前 {min(limit, len(preview)):,} 行")
            st.dataframe(preview.head(limit), use_container_width=True, height=520)
            st.download_button(
                "下载当前筛选 CSV",
                data=csv_download(preview),
                file_name="cp_analysis_filtered.csv",
                mime="text/csv",
            )

    with tabs[2]:
        st.markdown("### 良率与失效结构")
        if yield_filtered.empty:
            st.warning("原始数据中没有可识别的 Lot_ID、Wafer_ID、Bin，无法生成良率分析。")
        else:
            first, second = st.columns(2)
            distribution = yield_distribution(yield_filtered)
            comparison = lot_comparison(yield_filtered)
            report_figures.extend([distribution, comparison])
            with first:
                st.plotly_chart(distribution, use_container_width=True, config=PLOT_CONFIG)
            with second:
                st.plotly_chart(comparison, use_container_width=True, config=PLOT_CONFIG)
        bin_columns = dynamic_bin_columns(yield_filtered)
        if not bin_columns:
            st.info("当前数据没有可识别的失效 Bin 计数。")
        else:
            totals = yield_filtered[bin_columns].apply(pd.to_numeric, errors="coerce").sum().sort_values(ascending=False)
            chart = bin_failure_chart(totals)
            pareto = bin_pareto(totals)
            report_figures.extend([chart, pareto])
            left, right = st.columns(2)
            with left:
                st.plotly_chart(chart, use_container_width=True, config=PLOT_CONFIG)
            with right:
                st.plotly_chart(pareto, use_container_width=True, config=PLOT_CONFIG)
            ranking = totals.rename("Fail_Die").rename_axis("Bin").reset_index()
            ranking["占比"] = ranking["Fail_Die"] / ranking["Fail_Die"].sum()
            with st.expander("Bin 失效明细", expanded=False):
                st.dataframe(ranking, use_container_width=True, hide_index=True)

    with tabs[3]:
        st.markdown("### Wafer 空间分布")
        if not {"Wafer_ID", "X", "Y"}.issubset(cleaned_filtered.columns):
            st.warning("原始数据没有 Wafer_ID、X、Y，无法生成 Wafer Map。")
        elif cleaned_filtered["X"].nunique() < 2 or cleaned_filtered["Y"].nunique() < 2:
            st.warning("当前坐标没有有效空间变化，Wafer Map 不具备位置分析意义。")
        else:
            wafer_options = sorted(cleaned_filtered["Wafer_ID"].dropna().astype(str).unique().tolist())
            map_columns = ["Bin"] + parameters
            controls = st.columns(2)
            with controls[0]:
                map_wafer = st.selectbox("Wafer", wafer_options, key="map_wafer")
            with controls[1]:
                map_value = st.selectbox("着色字段", map_columns, key="map_value")
            map_fig = wafer_map(
                cleaned_filtered,
                map_wafer,
                map_value,
                pass_bin=int(bundle.metadata.get("pass_bin", 1)),
            )
            report_figures.append(map_fig)
            st.plotly_chart(map_fig, use_container_width=True, config=PLOT_CONFIG)

    with tabs[4]:
        st.markdown("### 全参数 Wafer 分布")
        st.caption("沿用华虹参数图规则：X 轴固定为 Lot → Wafer_ID，Y 轴固定为当前参数；箱体来自全部有效 Die，散点仅做等分位抽样。")
        if not parameters:
            st.warning("没有可分析的数值参数。")
        else:
            for index, parameter in enumerate(parameters):
                spec_info = parameter_spec(bundle.spec, parameter)
                chart = parameter_wafer_chart(cleaned_filtered, parameter, spec_info)
                report_figures.append(chart)
                st.plotly_chart(chart, use_container_width=True, config=PLOT_CONFIG, key=f"parameter_gallery_{index}")

    with tabs[5]:
        st.markdown("### 参数分布与制程能力")
        if not parameters:
            st.warning("没有可分析的数值参数。")
        else:
            distribution_parameter = st.selectbox("分析参数", parameters, key="distribution_parameter")
            spec_info = parameter_spec(bundle.spec, distribution_parameter)
            default_lsl = spec_info.get("LimitL", spec_info.get("LSL", "")) if spec_info else ""
            default_usl = spec_info.get("LimitU", spec_info.get("USL", "")) if spec_info else ""
            limits = st.columns(2)
            with limits[0]:
                lsl_text = st.text_input("LSL（可留空）", value=str(default_lsl) if default_lsl != "" else "")
            with limits[1]:
                usl_text = st.text_input("USL（可留空）", value=str(default_usl) if default_usl != "" else "")
            lsl, usl = optional_float(lsl_text), optional_float(usl_text)
            if lsl is None and usl is None:
                st.caption("未提供规格：展示分布统计，但不计算 Cp/Cpk/Pp/Ppk。")
            capability = capability_metrics(cleaned_filtered, distribution_parameter, lsl, usl)
            capability_columns = st.columns(4)
            for column, name in zip(capability_columns, ("Cp", "Cpk", "Pp", "Ppk")):
                value = capability[name]
                with column:
                    st.metric(name, "—" if value is None or pd.isna(value) else f"{value:.3f}")
            histogram = parameter_distribution(cleaned_filtered, distribution_parameter, lsl, usl)
            violin = violin_distribution(cleaned_filtered, distribution_parameter)
            qq = qq_chart(cleaned_filtered, distribution_parameter)
            ecdf = ecdf_chart(cleaned_filtered, distribution_parameter)
            report_figures.extend([histogram, violin, qq, ecdf])
            left, right = st.columns(2)
            with left:
                st.plotly_chart(histogram, use_container_width=True, config=PLOT_CONFIG)
                st.plotly_chart(qq, use_container_width=True, config=PLOT_CONFIG)
            with right:
                st.plotly_chart(violin, use_container_width=True, config=PLOT_CONFIG)
                st.plotly_chart(ecdf, use_container_width=True, config=PLOT_CONFIG)
            with st.expander("能力计算明细", expanded=False):
                st.json(capability)

    with tabs[6]:
        st.markdown("### 自动参数相关分析")
        if len(parameters) < 2:
            st.warning("至少需要两个数值参数。")
        else:
            st.caption("系统按绝对 Pearson 相关系数自动挑选最强参数对，不需要设置 X/Y。")
            heatmap = correlation_heatmap(cleaned_filtered, parameters)
            matrix_parameters = parameters[: min(5, len(parameters))]
            matrix = scatter_matrix(cleaned_filtered, matrix_parameters)
            report_figures.extend([heatmap, matrix])
            overview = st.columns(2)
            with overview[0]:
                st.plotly_chart(heatmap, use_container_width=True, config=PLOT_CONFIG)
            with overview[1]:
                st.plotly_chart(matrix, use_container_width=True, config=PLOT_CONFIG)

            correlation_pairs = strongest_parameter_pairs(cleaned_filtered, parameters, limit=6)
            if correlation_pairs:
                st.markdown("#### 高相关参数散点")
                pair_columns = st.columns(2)
                for index, (x_parameter, y_parameter, correlation) in enumerate(correlation_pairs):
                    scatter_fig = parameter_scatter(cleaned_filtered, x_parameter, y_parameter)
                    scatter_fig.update_layout(title=f"{x_parameter} × {y_parameter} · r={correlation:.3f}")
                    report_figures.append(scatter_fig)
                    with pair_columns[index % 2]:
                        st.plotly_chart(scatter_fig, use_container_width=True, config=PLOT_CONFIG, key=f"auto_pair_{index}")
            if len(parameters) >= 3:
                automatic_3d = []
                for left, right, _ in correlation_pairs:
                    for parameter in (left, right):
                        if parameter not in automatic_3d:
                            automatic_3d.append(parameter)
                automatic_3d.extend(parameter for parameter in parameters if parameter not in automatic_3d)
                x3, y3, z3 = automatic_3d[:3]
                chart_3d = scatter_3d(cleaned_filtered, x3, y3, z3)
                report_figures.append(chart_3d)
                st.plotly_chart(chart_3d, use_container_width=True, config=PLOT_CONFIG)

    with tabs[7]:
        st.markdown("### SPC 与测试顺序趋势")
        if not parameters:
            st.warning("没有可分析的数值参数。")
        else:
            spc_parameter = st.selectbox("SPC 参数", parameters, key="spc_parameter")
            spc_chart = wafer_mean_control_chart(cleaned_filtered, spc_parameter)
            report_figures.append(spc_chart)
            st.plotly_chart(spc_chart, use_container_width=True, config=PLOT_CONFIG)
            if "Seq" in cleaned_filtered.columns:
                sequence_wafer_options = ["全部 Wafer"] + sorted(
                    cleaned_filtered["Wafer_ID"].dropna().astype(str).unique().tolist()
                )
                sequence_wafer = st.selectbox("Run Chart Wafer", sequence_wafer_options)
                sequence_fig = sequence_scatter(
                    cleaned_filtered,
                    spc_parameter,
                    None if sequence_wafer == "全部 Wafer" else sequence_wafer,
                )
                report_figures.append(sequence_fig)
                st.plotly_chart(sequence_fig, use_container_width=True, config=PLOT_CONFIG)
            st.caption("控制界限按当前筛选范围内的 Wafer 均值 ±3σ 计算；用于过程监控，不替代正式控制计划判异规则。")

    with tabs[8]:
        st.markdown("### 离线报告")
        st.write("汇总当前筛选条件下的良率、失效、分布、能力、散点、Wafer Map 和 SPC 图表。")
        with st.expander("参数统计摘要", expanded=True):
            st.dataframe(parameter_stats, use_container_width=True, hide_index=True, height=420)
        if report_figures:
            st.download_button(
                "生成并下载 HTML 报告",
                data=html_report(
                    report_figures,
                    "CP Raw Data Analysis Report",
                    metadata=bundle.metadata,
                    yield_frame=yield_filtered,
                    parameter_stats=parameter_stats,
                ),
                file_name="cp_data_cockpit_report.html",
                mime="text/html",
            )
        else:
            st.info("当前数据不足，尚未生成可导出的图表。")


if __name__ == "__main__":
    main()
