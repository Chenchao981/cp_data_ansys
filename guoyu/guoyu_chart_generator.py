"""基于国宇标准 CSV 生成离线 Plotly 分析图。"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
import plotly.express as px

from frontend.charts.js_embedder import get_embedded_plotly_js


BASIC_COLUMNS = {"Lot_ID", "Wafer_ID", "X", "Y", "Seq", "Bin"}


def generate_guoyu_charts(data_dir: str) -> List[str]:
    data_path = Path(data_dir)
    cleaned_file = next(iter(sorted(data_path.glob("*_cleaned_*.csv"))), None)
    yield_file = next(iter(sorted(data_path.glob("*_yield_*.csv"))), None)
    spec_file = next(iter(sorted(data_path.glob("*_spec_*.csv"))), None)
    if not cleaned_file or not yield_file or not spec_file:
        raise ValueError("生成国宇图表需要 cleaned、yield、spec 三类标准 CSV")

    cleaned = pd.read_csv(cleaned_file)
    yield_data = pd.read_csv(yield_file)
    spec = pd.read_csv(spec_file).set_index("Parameter")
    plotly_js = get_embedded_plotly_js()
    output_files: List[str] = []

    yield_data["Yield_Numeric"] = (
        yield_data["Yield"].astype(str).str.rstrip("%").astype(float)
    )
    yield_fig = px.line(
        yield_data,
        x="Wafer_ID",
        y="Yield_Numeric",
        markers=True,
        title=f"{cleaned_file.stem.split('_cleaned_')[0]} - Wafer 良率趋势",
        labels={"Yield_Numeric": "Yield (%)", "Wafer_ID": "Wafer ID"},
    )
    yield_fig.update_yaxes(range=[95, 100.5])
    yield_path = data_path / "guoyu_yield_trend.html"
    yield_fig.write_html(str(yield_path), include_plotlyjs=plotly_js, validate=False)
    output_files.append(str(yield_path))

    parameters = [
        column
        for column in cleaned.columns
        if column not in BASIC_COLUMNS and pd.api.types.is_numeric_dtype(cleaned[column])
    ]
    for parameter in parameters:
        fig = px.box(
            cleaned,
            x="Wafer_ID",
            y=parameter,
            points="outliers",
            color="Wafer_ID",
            title=f"{parameter} 分布",
        )
        if parameter in spec.index:
            lower = spec.loc[parameter, "LimitL"]
            upper = spec.loc[parameter, "LimitU"]
            if pd.notna(lower):
                fig.add_hline(y=float(lower), line_dash="dash", line_color="red")
            if pd.notna(upper):
                fig.add_hline(y=float(upper), line_dash="dash", line_color="red")
            fig.update_yaxes(title=parameter)
        output_path = data_path / f"guoyu_{parameter}_boxplot.html"
        fig.write_html(str(output_path), include_plotlyjs=plotly_js, validate=False)
        output_files.append(str(output_path))

    return output_files
