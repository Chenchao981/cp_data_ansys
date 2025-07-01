#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图表生成器 - 专业级分析工具
使用 YieldChart 和 Plotly Express 生成 CP 测试数据分析图表
支持良率分析、参数统计、箱体图等多种图表类型
"""

import logging
import sys
from pathlib import Path
import plotly.express as px
import pandas as pd

# 导入 YieldChart 类
from frontend.charts.yield_chart import YieldChart

# 导入JavaScript嵌入工具 - 使用兼容的导入方式
def get_embedded_plotly_js():
    """获取嵌入式Plotly.js内容"""
    try:
        # 尝试绝对导入
        from frontend.charts.js_embedder import get_embedded_plotly_js as _get_embedded_plotly_js
        return _get_embedded_plotly_js()
    except ImportError:
        try:
            # 尝试从当前目录导入
            current_dir = Path(__file__).parent / "frontend" / "charts"
            if str(current_dir) not in sys.path:
                sys.path.append(str(current_dir))
            from js_embedder import get_embedded_plotly_js as _get_embedded_plotly_js
            return _get_embedded_plotly_js()
        except ImportError:
            # 最后回退到CDN
            logger.warning("无法导入JavaScript嵌入工具，使用CDN模式")
            return 'https://unpkg.com/plotly.js@2.26.0/dist/plotly.min.js'

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    主函数：加载数据并生成所有类型的图表
    """
    # 1. 配置目录路径
    # 修改这里指向您的数据文件夹
    data_input_dir = Path("output")  # 默认使用 output 目录
    # data_input_dir = Path("input_data")  # 或自定义输入目录

    charts_output_dir = Path("demo_output/generated_charts")
    charts_output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"📂 数据输入目录: {data_input_dir.resolve()}")
    logger.info(f"📊 图表输出目录: {charts_output_dir.resolve()}")

    # 2. 初始化 YieldChart 并加载数据
    logger.info("🔄 初始化 YieldChart...")
    yield_analyzer = YieldChart(data_dir=str(data_input_dir))

    if not yield_analyzer.load_data():
        logger.error("❌ 数据加载失败，请检查数据文件是否存在且格式正确。")
        logger.info("💡 提示：确保目录中包含 *_yield_*.csv, *_spec_*.csv, *_cleaned_*.csv 文件")
        return

    logger.info("✅ 数据加载成功")

    # 3. 生成 YieldChart 内置图表
    logger.info("📈 开始生成 YieldChart 内置图表...")
    yield_output_dir = charts_output_dir / "yield_chart_outputs"
    saved_yield_charts = yield_analyzer.save_all_charts(output_dir=str(yield_output_dir))

    if saved_yield_charts:
        logger.info(f"✅ YieldChart 图表已保存到: {yield_output_dir}")
        for i, chart_path in enumerate(saved_yield_charts, 1):
            logger.info(f"  {i}. {chart_path.name}")
    else:
        logger.warning("⚠️ 未能保存任何 YieldChart 内置图表")

    # 4. 生成自定义 Plotly Express 图表
    # 尝试加载cleaned数据
    cleaned_df = None
    cleaned_files = [f for f in Path(data_input_dir).glob("*_cleaned_*.csv")]
    
    if cleaned_files:
        try:
            cleaned_file = cleaned_files[0]  # 使用第一个找到的cleaned文件
            cleaned_df = pd.read_csv(cleaned_file)
            logger.info(f"📄 加载清洗数据: {cleaned_file.name}")
        except Exception as e:
            logger.error(f"❌ 清洗数据加载失败: {e}")

    if cleaned_df is None or cleaned_df.empty:
        logger.warning("⚠️ Cleaned data 未加载或为空，跳过自定义图表生成")
    else:
        logger.info("📦 开始生成自定义箱体图和散点图...")
        generate_custom_plotly_charts(cleaned_df, yield_analyzer, charts_output_dir)

    logger.info("🎉 图表生成流程完成！")
    logger.info(f"📁 所有图表已保存到: {charts_output_dir}")

def generate_custom_plotly_charts(cleaned_df, yield_analyzer, output_base_dir):
    """
    生成自定义的 Plotly Express 图表
    """
    custom_output_dir = output_base_dir / "custom_plotly_express_charts"
    custom_output_dir.mkdir(parents=True, exist_ok=True)

    # 获取可用参数
    excluded_cols = ['LotID', 'WaferID', 'Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y', 'CONT']
    
    # 直接从cleaned CSV推断参数，因为YieldChart的参数来自yield文件，与cleaned文件不匹配
    plot_params = [
        col for col in cleaned_df.columns
        if col not in excluded_cols and cleaned_df[col].dtype in ['int64', 'float64']
    ]
    logger.info(f"📊 使用CSV推断参数列表")
    
    logger.info(f"🔍 CSV列名: {list(cleaned_df.columns)}")
    logger.info(f"📊 排除列表: {excluded_cols}")
    logger.info(f"📊 数值列: {[col for col in cleaned_df.columns if cleaned_df[col].dtype in ['int64', 'float64']]}")
    logger.info(f"📊 筛选后参数: {plot_params}")

    if not plot_params:
        logger.warning("⚠️ 未找到合适的数值参数，跳过自定义图表生成")
        return

    logger.info(f"🎯 将为以下 {len(plot_params)} 个参数生成图表: {plot_params}")

    # 提取批次信息用于分组
    if 'LotID' in cleaned_df.columns:
        cleaned_df['Short_Lot_ID'] = cleaned_df['LotID'].str.extract(r'(FA\d{2}-\d+)', expand=False).fillna('Unknown')
        color_group = 'Short_Lot_ID'
    elif 'Lot_ID' in cleaned_df.columns:
        cleaned_df['Short_Lot_ID'] = cleaned_df['Lot_ID'].str.extract(r'(FA\d{2}-\d+)', expand=False).fillna('Unknown')
        color_group = 'Short_Lot_ID'
    else:
        color_group = None

    # 为每个参数生成箱体图
    for i, param in enumerate(plot_params, 1):
        try:
            # 生成箱体图
            param_info = yield_analyzer.get_parameter_info(param)
            unit_str = f" ({param_info.get('unit', '')})" if param_info.get('unit') else ""

            fig_box = px.box(
                cleaned_df,
                y=param,
                color=color_group,
                title=f"📦 参数 {param}{unit_str} 箱体图 (按批次分组)",
                labels={param: f"{param}{unit_str}"},
                points="all"  # 显示所有数据点
            )

            # 美化图表
            fig_box.update_layout(
                height=600,
                font=dict(size=12),
                title_font_size=16,
                showlegend=True
            )

            box_filename = custom_output_dir / f"{param}_boxplot.html"
            # 使用本地嵌入的Plotly.js，避免CDN加载失败
            fig_box.write_html(
                str(box_filename),
                include_plotlyjs=get_embedded_plotly_js(),
                validate=False  # 跳过验证，提升速度
            )
            logger.info(f"  ✅ [{i}/{len(plot_params)}] 箱体图: {box_filename.name}")

        except Exception as e:
            logger.error(f"❌ 生成参数 {param} 箱体图失败: {e}")

    # 生成散点图矩阵（前几个参数）
    if len(plot_params) >= 2:
        try:
            # 选择前4个参数进行散点图分析
            scatter_params = plot_params[:min(4, len(plot_params))]

            for i in range(len(scatter_params)):
                for j in range(i+1, len(scatter_params)):
                    param1, param2 = scatter_params[i], scatter_params[j]

                    param1_info = yield_analyzer.get_parameter_info(param1)
                    param2_info = yield_analyzer.get_parameter_info(param2)

                    unit1 = f" ({param1_info.get('unit', '')})" if param1_info.get('unit') else ""
                    unit2 = f" ({param2_info.get('unit', '')})" if param2_info.get('unit') else ""

                    fig_scatter = px.scatter(
                        cleaned_df,
                        x=param1,
                        y=param2,
                        color=color_group,
                        title=f"🌈 参数相关性: {param1} vs {param2}",
                        labels={
                            param1: f"{param1}{unit1}",
                            param2: f"{param2}{unit2}"
                        },
                        hover_data=['WaferID'] if 'WaferID' in cleaned_df.columns else ['Wafer_ID'] if 'Wafer_ID' in cleaned_df.columns else None
                    )

                    # 美化图表
                    fig_scatter.update_layout(
                        height=600,
                        font=dict(size=12),
                        title_font_size=16
                    )

                    scatter_filename = custom_output_dir / f"{param1}_vs_{param2}_scatter.html"
                    # 使用本地嵌入的Plotly.js，避免CDN加载失败
                    fig_scatter.write_html(
                        str(scatter_filename),
                        include_plotlyjs=get_embedded_plotly_js(),
                        validate=False  # 跳过验证，提升速度
                    )
                    logger.info(f"  ✅ 散点图: {scatter_filename.name}")

        except Exception as e:
            logger.error(f"❌ 生成散点图失败: {e}")

    logger.info(f"📦 自定义图表已保存到: {custom_output_dir}")

if __name__ == "__main__":
    print("🔬 CP 数据分析工具 - 自定义图表生成器")
    print("=" * 50)
    main()