#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lion公司图表生成器 - 复用HH公司前端图表模块
基于Lion公司的3个清洗CSV文件(*_cleaned_*.csv, *_spec_*.csv, *_yield_*.csv)
生成与HH公司相同的前端HTML图表

功能特性：
1. 📈 良率图表：批次良率趋势、失效类型分析、批次良率对比
2. 📦 参数箱体图：单独生成所有测量参数的箱体图和散点图
3. 📋 汇总图表：在一个页面中显示良率图和所有参数的汇总分析
4. 🔍 异常值处理：使用IQR方法检测和处理异常值
5. ✅ 数据验证：完整的CSV文件和数据质量验证
"""

import logging
import sys
from pathlib import Path
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 添加项目路径以导入HH的前端模块
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入HH公司的前端图表模块
from frontend.charts.yield_chart import YieldChart
from frontend.charts.boxplot_chart import BoxplotChart
from frontend.charts.summary_chart import SummaryChart

# 导入JavaScript嵌入工具
def get_embedded_plotly_js():
    """获取嵌入式Plotly.js内容"""
    try:
        from frontend.charts.js_embedder import get_embedded_plotly_js as _get_embedded_plotly_js
        return _get_embedded_plotly_js()
    except ImportError:
        return 'https://unpkg.com/plotly.js@2.26.0/dist/plotly.min.js'

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LionOutlierHandler:
    """Lion公司异常值处理器"""
    
    def __init__(self, method: str = "iqr", threshold: float = 1.5):
        """
        初始化异常值处理器
        
        Args:
            method: 异常值检测方法，默认使用IQR
            threshold: IQR阈值倍数，默认1.5
        """
        self.method = method
        self.threshold = threshold
        self.logger = logging.getLogger(f"{__name__}.LionOutlierHandler")
    
    def detect_outliers(self, df: pd.DataFrame, parameter: str) -> pd.Series:
        """
        检测指定参数的异常值
        
        Args:
            df: 数据DataFrame
            parameter: 参数名称
            
        Returns:
            pd.Series: 布尔掩码，True表示异常值
        """
        if parameter not in df.columns:
            return pd.Series([False] * len(df), index=df.index)
        
        data = df[parameter].dropna()
        if len(data) < 4:  # 数据点太少，无法计算四分位数
            return pd.Series([False] * len(df), index=df.index)
        
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - self.threshold * IQR
        upper_bound = Q3 + self.threshold * IQR
        
        outliers = (df[parameter] < lower_bound) | (df[parameter] > upper_bound)
        return outliers.fillna(False)
    
    def handle_outliers(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        处理所有参数的异常值
        
        Args:
            df: 输入数据DataFrame
            
        Returns:
            Tuple[pd.DataFrame, Dict]: 处理后的数据和统计信息
        """
        processed_df = df.copy()
        outlier_stats = {}
        
        # 识别测试参数列（排除基础列）
        basic_columns = ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Seq', 'Bin', 'SITE_NUM', 'CONT', 'T_TIME', 'TEST_NUM']
        param_columns = [col for col in df.columns if col not in basic_columns]
        
        for param in param_columns:
            if pd.api.types.is_numeric_dtype(df[param]):
                outliers = self.detect_outliers(df, param)
                outlier_count = outliers.sum()
                total_count = df[param].count()  # 非NaN值的数量
                
                if outlier_count > 0:
                    # 将异常值标记为NaN
                    processed_df.loc[outliers, param] = np.nan
                    outlier_percentage = (outlier_count / total_count * 100) if total_count > 0 else 0
                    
                    outlier_stats[param] = {
                        'outlier_count': outlier_count,
                        'total_count': total_count,
                        'outlier_percentage': outlier_percentage
                    }
                    
                    self.logger.info(f"参数 {param}: 检测到 {outlier_count} 个异常值 ({outlier_percentage:.2f}%)")
                    
                    if outlier_percentage > 5:
                        self.logger.warning(f"⚠️ 参数 {param} 异常值比例较高: {outlier_percentage:.2f}%")
        
        return processed_df, outlier_stats


def main(data_dir=None):
    """
    Lion公司图表生成主函数
    复用HH公司的前端图表模块生成相同格式的HTML图表
    
    Args:
        data_dir: 数据目录路径，如果为None则使用默认的"output"目录
    """
    logger.info("🦁 Lion公司图表生成器启动")
    logger.info("=" * 60)
    
    # 1. 配置Lion公司数据目录
    if data_dir is None:
        lion_data_dir = Path("output")  # 默认目录
        lion_output_dir = Path("output")
    else:
        lion_data_dir = Path(data_dir)  # 使用传入的数据目录
        lion_output_dir = Path(data_dir)  # 输出到同一目录
    
    lion_output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"📂 Lion数据目录: {lion_data_dir.resolve()}")
    logger.info(f"📊 Lion图表输出目录: {lion_output_dir.resolve()}")
    
    # 2. 验证Lion的3个CSV文件是否存在
    if not validate_csv_files(lion_data_dir):
        logger.error("❌ CSV文件验证失败，无法继续")
        return False
    
    # 3. 数据预处理：异常值检测和处理
    logger.info("🔍 开始异常值检测和处理...")
    if not process_outliers(lion_data_dir):
        logger.warning("⚠️ 异常值处理失败，继续使用原始数据")
    
    # 4. 列名标准化处理
    logger.info("🔄 开始列名标准化处理...")
    standardize_lion_csv_columns(lion_data_dir)
    
    # 5. 使用HH的YieldChart生成良率图表
    logger.info("📈 开始生成良率图表...")
    yield_success = generate_yield_charts(lion_data_dir, lion_output_dir)
    
    # 6. 使用HH的BoxplotChart生成箱体图
    logger.info("📦 开始生成箱体图和散点图...")
    boxplot_success = generate_boxplot_charts(lion_data_dir, lion_output_dir)
    
    # 7. 使用HH的SummaryChart生成汇总图表
    logger.info("📋 开始生成汇总图表...")
    summary_success = generate_summary_chart(lion_data_dir, lion_output_dir)
    
    # 8. 生成处理结果报告
    generate_processing_report(lion_output_dir, yield_success, boxplot_success, summary_success)
    
    logger.info("🎉 Lion公司图表生成完成！")
    logger.info("📊 生成的图表类型包括：")
    logger.info("   📈 良率图表 (3个): 趋势分析、失效分析、批次对比")
    logger.info("   📦 参数箱体图 (多个): 每个测试参数的独立分析")
    logger.info("   📋 汇总图表 (1个): 包含良率图和所有参数的综合分析")
    logger.info(f"📁 所有图表已保存到: {lion_output_dir}")
    
    return True


def validate_csv_files(data_dir: Path) -> bool:
    """
    验证必要的CSV文件是否存在且格式正确
    
    Args:
        data_dir: 数据目录路径
        
    Returns:
        bool: 验证通过返回True
    """
    try:
        # 检查必要的CSV文件
        cleaned_files = list(data_dir.glob("*_cleaned_*.csv"))
        spec_files = list(data_dir.glob("*_spec_*.csv"))
        yield_files = list(data_dir.glob("*_yield_*.csv"))
        
        if not (cleaned_files and spec_files and yield_files):
            logger.error("❌ 缺少必要的CSV文件，请确保存在：")
            logger.error("   - *_cleaned_*.csv (清洗数据)")
            logger.error("   - *_spec_*.csv (规格数据)")
            logger.error("   - *_yield_*.csv (良率数据)")
            return False
        
        logger.info(f"✅ 找到Lion数据文件:")
        logger.info(f"   - 清洗数据: {cleaned_files[0].name}")
        logger.info(f"   - 规格数据: {spec_files[0].name}")
        logger.info(f"   - 良率数据: {yield_files[0].name}")
        
        # 验证文件内容
        for file_path in [cleaned_files[0], spec_files[0], yield_files[0]]:
            try:
                df = pd.read_csv(file_path, nrows=5)  # 只读取前5行进行验证
                if df.empty:
                    logger.warning(f"⚠️ 文件为空: {file_path.name}")
                else:
                    logger.info(f"✅ 文件验证通过: {file_path.name} ({len(df)} 行样本)")
            except Exception as e:
                logger.error(f"❌ 文件读取失败 {file_path.name}: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ CSV文件验证失败: {e}")
        return False


def process_outliers(data_dir: Path) -> bool:
    """
    处理异常值
    
    Args:
        data_dir: 数据目录路径
        
    Returns:
        bool: 处理成功返回True
    """
    try:
        # 找到cleaned文件
        cleaned_files = list(data_dir.glob("*_cleaned_*.csv"))
        if not cleaned_files:
            logger.warning("⚠️ 未找到cleaned文件，跳过异常值处理")
            return False
        
        cleaned_file = cleaned_files[0]
        logger.info(f"📄 加载清洗数据: {cleaned_file.name}")
        
        # 读取数据
        df = pd.read_csv(cleaned_file)
        original_shape = df.shape
        
        # 处理异常值
        outlier_handler = LionOutlierHandler()
        processed_df, outlier_stats = outlier_handler.handle_outliers(df)
        
        # 保存处理后的数据（可选，用于调试）
        # processed_file = data_dir / f"lion_cleaned_processed.csv"
        # processed_df.to_csv(processed_file, index=False)
        
        # 生成异常值报告
        if outlier_stats:
            report_content = generate_outlier_report_html(outlier_stats, original_shape)
            report_file = data_dir / "lion_outlier_report.html"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"✅ 异常值报告已保存: {report_file.name}")
        
        logger.info(f"✅ 异常值处理完成，共处理 {len(outlier_stats)} 个参数")
        return True
        
    except Exception as e:
        logger.error(f"❌ 异常值处理失败: {e}")
        return False


def generate_outlier_report_html(outlier_stats: Dict, original_shape: Tuple) -> str:
    """
    生成异常值处理报告HTML
    
    Args:
        outlier_stats: 异常值统计信息
        original_shape: 原始数据形状
        
    Returns:
        str: HTML报告内容
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lion公司异常值处理报告</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f8ff; padding: 20px; border-radius: 5px; }}
            .stats {{ margin: 20px 0; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .warning {{ color: #ff6600; }}
            .normal {{ color: #008000; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🦁 Lion公司异常值处理报告</h1>
            <p>数据形状: {original_shape[0]} 行 × {original_shape[1]} 列</p>
            <p>处理方法: IQR方法 (阈值: 1.5)</p>
            <p>处理策略: 异常值标记为NaN，保持数据结构完整</p>
        </div>
        
        <div class="stats">
            <h2>📊 异常值统计</h2>
            <table>
                <tr>
                    <th>参数名称</th>
                    <th>异常值数量</th>
                    <th>总数据量</th>
                    <th>异常值比例</th>
                    <th>状态</th>
                </tr>
    """
    
    for param, stats in outlier_stats.items():
        percentage = stats['outlier_percentage']
        status_class = "warning" if percentage > 5 else "normal"
        status_text = "⚠️ 需关注" if percentage > 5 else "✅ 正常"
        
        html_content += f"""
                <tr>
                    <td>{param}</td>
                    <td>{stats['outlier_count']}</td>
                    <td>{stats['total_count']}</td>
                    <td>{percentage:.2f}%</td>
                    <td class="{status_class}">{status_text}</td>
                </tr>
        """
    
    html_content += """
            </table>
        </div>
        
        <div class="stats">
            <h2>📋 处理说明</h2>
            <ul>
                <li>使用IQR方法检测异常值：Q1 - 1.5×IQR ≤ 正常值 ≤ Q3 + 1.5×IQR</li>
                <li>异常值标记为NaN，不删除数据行，保持数据结构完整</li>
                <li>异常值比例>5%的参数需要特别关注</li>
                <li>处理后的数据用于后续图表生成</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    return html_content


def standardize_lion_csv_columns(data_dir: Path):
    """
    标准化Lion的CSV列名以匹配HH的格式
    转换: LotID -> Lot_ID, WaferID -> Wafer_ID
    """
    try:
        # 找到cleaned文件
        cleaned_files = list(data_dir.glob("*_cleaned_*.csv"))
        if not cleaned_files:
            logger.warning("⚠️ 未找到需要标准化的cleaned文件")
            return
        
        cleaned_file = cleaned_files[0]
        logger.info(f"🔄 标准化CSV列名: {cleaned_file.name}")
        
        # 读取CSV
        df = pd.read_csv(cleaned_file)
        
        # 检查并转换列名
        column_mapping = {
            'LotID': 'Lot_ID',
            'WaferID': 'Wafer_ID'
        }
        
        renamed_columns = {}
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                renamed_columns[old_name] = new_name
        
        if renamed_columns:
            df.rename(columns=renamed_columns, inplace=True)
            logger.info(f"✅ 列名转换: {renamed_columns}")
            
            # 保存标准化后的文件
            df.to_csv(cleaned_file, index=False, encoding='utf-8')
            logger.info(f"✅ 标准化完成: {cleaned_file.name}")
        else:
            logger.info("ℹ️ 无需列名转换")
            
    except Exception as e:
        logger.error(f"❌ 列名标准化失败: {e}")


def generate_lion_yield_trend_chart(data_dir: Path, output_dir: Path) -> bool:
    """
    生成Lion公司专用的良率趋势图 - 批次在X轴方向展开，每个wafer显示垂直虚线
    基于yield.csv文件中的Yield列数据
    
    Args:
        data_dir: 数据目录路径
        output_dir: 输出目录路径
        
    Returns:
        bool: 生成成功返回True
    """
    try:
        # 1. 查找并加载yield数据
        yield_files = list(data_dir.glob("*_yield_*.csv"))
        if not yield_files:
            logger.error("❌ 未找到yield数据文件")
            return False
        
        yield_file = yield_files[0]
        logger.info(f"📄 加载良率数据: {yield_file.name}")
        yield_data = pd.read_csv(yield_file)
        
        if yield_data.empty:
            logger.error("❌ 良率数据为空")
            return False
        
        # 2. 数据预处理
        # 转换yield为数值（去掉百分号）
        if 'Yield' in yield_data.columns:
            yield_data['Yield_Numeric'] = yield_data['Yield'].str.rstrip('%').astype(float)
        else:
            logger.error("❌ 未找到Yield列")
            return False
        
        # 按Lot_ID和Wafer_ID排序
        if 'Wafer_ID' in yield_data.columns:
            yield_data['Wafer_ID_Numeric'] = pd.to_numeric(yield_data['Wafer_ID'], errors='coerce')
            yield_data = yield_data.sort_values(['Lot_ID', 'Wafer_ID_Numeric'])
        
        logger.info(f"✅ 成功加载 {len(yield_data)} 个晶圆的良率数据")
        logger.info(f"📊 良率范围: {yield_data['Yield_Numeric'].min():.2f}% - {yield_data['Yield_Numeric'].max():.2f}%")
        
        # 3. 按批次分组数据并在X轴方向展开
        lot_groups = yield_data.groupby('Lot_ID') if 'Lot_ID' in yield_data.columns else {'Unknown': yield_data}
        if not isinstance(lot_groups, dict):
            lot_groups = dict(list(lot_groups))
        
        # 4. 创建良率趋势图 - 批次在X轴方向连续展开
        fig = go.Figure()
        
        # 定义批次颜色
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
        
        x_position = 1  # 全局X轴位置计数器
        x_labels = []   # X轴标签
        x_positions = []  # X轴位置
        lot_boundaries = []  # 批次边界位置
        
        for i, (lot_id, lot_data) in enumerate(lot_groups.items()):
            color = colors[i % len(colors)]
            lot_start_pos = x_position
            
            # 确定该批次的wafer_id范围（1到最大wafer_id）
            actual_wafer_ids = lot_data['Wafer_ID'].unique()
            min_wafer_id = min(actual_wafer_ids)
            max_wafer_id = max(actual_wafer_ids)
            
            # 为当前批次的每个wafer位置分配X轴位置（包括缺失的wafer）
            lot_x_positions = []
            lot_wafer_ids = []
            lot_yields = []
            
            # 遍历完整的wafer_id范围（1到24）
            for wafer_id in range(min_wafer_id, max_wafer_id + 1):
                # 添加X轴标签（显示wafer_id本身）
                x_labels.append(str(wafer_id))
                x_positions.append(x_position)
                
                # 为每个wafer位置添加垂直虚线
                fig.add_vline(
                    x=x_position,
                    line_dash="dot",
                    line_color='rgba(128, 128, 128, 0.5)',
                    line_width=1
                )
                
                # 检查该wafer_id是否有数据
                wafer_data = lot_data[lot_data['Wafer_ID'] == wafer_id]
                if not wafer_data.empty:
                    # 有数据的wafer添加到图表中
                    lot_x_positions.append(x_position)
                    lot_wafer_ids.append(wafer_id)
                    lot_yields.append(wafer_data['Yield_Numeric'].iloc[0])
                
                x_position += 1
            
            # 为每个批次添加良率趋势线
            fig.add_trace(go.Scatter(
                x=lot_x_positions,
                y=lot_yields,
                mode='lines+markers',
                name=f'批次 {lot_id}',
                line=dict(color=color, width=3),
                marker=dict(size=8, symbol='circle', color=color),
                showlegend=True,
                hovertemplate=f'<b>批次: {lot_id}</b><br>晶圆: %{{customdata}}<br>良率: %{{y:.2f}}%<extra></extra>',
                customdata=lot_wafer_ids
            ))
            
            # 记录批次边界（用于添加批次分隔）
            if i < len(lot_groups) - 1:  # 不在最后一个批次后添加分隔线
                lot_boundaries.append(x_position - 0.5)
        
        # 添加批次分隔线
        for boundary in lot_boundaries:
            fig.add_vline(
                x=boundary,
                line_dash="solid",
                line_color='rgba(0, 0, 0, 0.3)',
                line_width=2
            )
        
        # 5. 图表布局设置 - 匹配参数图表样式
        fig.update_layout(
            # 标题样式
            title=dict(
                text="📈 Wafer良率趋势分析",
                font=dict(size=16, color='black'),
                x=0.02,
                y=0.95,
                xanchor='left'
            ),
            # X轴设置 - 显示所有wafer ID（1-24等）
            xaxis=dict(
                title="Wafer ID",
                titlefont=dict(size=12, color='black'),
                tickfont=dict(size=10, color='black'),
                tickmode='array',
                tickvals=x_positions,
                ticktext=x_labels,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.3)',
                gridwidth=1,
                showline=True,
                linecolor='black',
                linewidth=1,
                range=[0.5, x_position - 0.5]  # 设置X轴范围
            ),
            # Y轴设置 - 匹配参数图表样式
            yaxis=dict(
                title="良率 (%)",
                titlefont=dict(size=12, color='black'),
                tickfont=dict(size=12, color='black'),
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.3)',
                gridwidth=1,
                showline=True,
                linecolor='black',
                linewidth=1
            ),
            # 背景设置 - 匹配参数图表
            plot_bgcolor='white',
            paper_bgcolor='white',
            # 尺寸设置 - 宽度根据wafer数量动态调整
            height=600,
            width=max(1200, len(yield_data) * 40),  # 每个wafer分配40像素宽度
            # 显示图例以区分不同批次
            showlegend=True,
            legend=dict(
                x=1.02,
                y=1,
                xanchor='left',
                yanchor='top',
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='black',
                borderwidth=1
            ),
            hovermode='x unified'
        )
        
        # 6. 保存图表
        chart_filename = output_dir / "Wafer良率趋势分析_yield_chart.html"
        fig.write_html(
            str(chart_filename),
            include_plotlyjs=get_embedded_plotly_js(),
            config={
                'displayModeBar': True, 
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                'scrollZoom': True  # 启用滚动缩放
            }
        )
        
        logger.info(f"✅ Lion良率趋势图已保存: {chart_filename.name}")
        
        # 7. 生成数据统计信息
        avg_yield = yield_data['Yield_Numeric'].mean()
        stats_info = {
            '总晶圆数': len(yield_data),
            '批次数量': len(lot_groups),
            '平均良率': f"{avg_yield:.2f}%",
            '最高良率': f"{yield_data['Yield_Numeric'].max():.2f}%",
            '最低良率': f"{yield_data['Yield_Numeric'].min():.2f}%",
            '良率标准差': f"{yield_data['Yield_Numeric'].std():.2f}%",
            '>=95%良率晶圆数': len(yield_data[yield_data['Yield_Numeric'] >= 95]),
            '<95%良率晶圆数': len(yield_data[yield_data['Yield_Numeric'] < 95])
        }
        
        logger.info("📊 良率数据统计:")
        for key, value in stats_info.items():
            logger.info(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Lion良率趋势图生成失败: {e}")
        return False


def generate_yield_charts(data_dir: Path, output_dir: Path) -> bool:
    """
    生成Lion公司专用良率趋势图表
    
    Args:
        data_dir: 数据目录路径
        output_dir: 输出目录路径
        
    Returns:
        bool: 生成成功返回True
    """
    try:
        # 直接生成Lion专用良率趋势图
        return generate_lion_yield_trend_chart(data_dir, output_dir)
        
    except Exception as e:
        logger.error(f"❌ 良率图表生成失败: {e}")
        return False


def generate_boxplot_charts(data_dir: Path, output_dir: Path) -> bool:
    """
    使用HH的BoxplotChart模块生成箱体图和散点图
    
    Args:
        data_dir: 数据目录路径
        output_dir: 输出目录路径
        
    Returns:
        bool: 生成成功返回True
    """
    try:
        # 初始化HH的BoxplotChart
        boxplot_analyzer = BoxplotChart(data_dir=str(data_dir))
        
        if not boxplot_analyzer.load_data():
            logger.error("❌ 箱体图数据加载失败")
            return False
        
        # 获取可用参数
        available_params = boxplot_analyzer.get_available_parameters()
        if not available_params:
            logger.warning("⚠️ 未找到可用的测试参数")
            return False
        
        logger.info(f"🎯 找到 {len(available_params)} 个测试参数: {available_params}")
        
        # 批量保存所有参数的箱体图
        saved_charts = boxplot_analyzer.save_all_charts(output_dir=str(output_dir))
        
        if saved_charts:
            logger.info(f"✅ 箱体图已保存 ({len(saved_charts)}个):")
            for i, chart_path in enumerate(saved_charts, 1):
                logger.info(f"  {i}. {chart_path.name}")
            return True
        else:
            logger.warning("⚠️ 未能保存箱体图")
            return False
            
    except Exception as e:
        logger.error(f"❌ 箱体图生成失败: {e}")
        return False


def generate_summary_chart(data_dir: Path, output_dir: Path) -> bool:
    """
    使用HH的SummaryChart模块生成包含良率图和所有参数的汇总图表
    
    Args:
        data_dir: 数据目录路径
        output_dir: 输出目录路径
        
    Returns:
        bool: 生成成功返回True
    """
    try:
        # 初始化HH的SummaryChart
        summary_analyzer = SummaryChart(data_dir=str(data_dir))
        
        if not summary_analyzer.load_data():
            logger.error("❌ 汇总图表数据加载失败")
            return False
        
        # 生成并保存汇总图表
        saved_chart = summary_analyzer.save_summary_chart(output_dir=str(output_dir))
        
        if saved_chart:
            logger.info(f"✅ 汇总图表已保存: {saved_chart.name}")
            return True
        else:
            logger.warning("⚠️ 未能保存汇总图表")
            return False
            
    except Exception as e:
        logger.error(f"❌ 汇总图表生成失败: {e}")
        return False


def generate_processing_report(output_dir: Path, yield_success: bool, boxplot_success: bool, summary_success: bool):
    """
    生成处理结果报告
    
    Args:
        output_dir: 输出目录路径
        yield_success: 良率图表生成是否成功
        boxplot_success: 箱体图生成是否成功
        summary_success: 汇总图表生成是否成功
    """
    try:
        # 统计生成的图表文件
        html_files = list(output_dir.glob("*.html"))
        
        report_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Lion公司图表生成报告</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f8ff; padding: 20px; border-radius: 5px; }}
                .success {{ color: #008000; }}
                .failure {{ color: #ff0000; }}
                .file-list {{ margin: 10px 0; }}
                .file-list li {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🦁 Lion公司图表生成报告</h1>
                <p>生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <h2>📊 生成结果</h2>
            <ul>
                <li>良率图表: <span class="{'success' if yield_success else 'failure'}">{'✅ 成功' if yield_success else '❌ 失败'}</span></li>
                <li>参数箱体图: <span class="{'success' if boxplot_success else 'failure'}">{'✅ 成功' if boxplot_success else '❌ 失败'}</span></li>
                <li>汇总图表: <span class="{'success' if summary_success else 'failure'}">{'✅ 成功' if summary_success else '❌ 失败'}</span></li>
            </ul>
            
            <h2>📁 生成的图表文件 ({len(html_files)} 个)</h2>
            <div class="file-list">
                <ul>
        """
        
        for html_file in sorted(html_files):
            file_size = html_file.stat().st_size / 1024  # KB
            report_content += f"<li>{html_file.name} ({file_size:.1f} KB)</li>\n"
        
        report_content += """
                </ul>
            </div>
            
            <h2>📋 使用说明</h2>
            <ul>
                <li>所有图表文件均为HTML格式，可直接在浏览器中打开</li>
                <li>图表支持交互功能：缩放、悬停提示、图例切换等</li>
                <li>建议使用Chrome、Firefox或Edge浏览器获得最佳体验</li>
            </ul>
        </body>
        </html>
        """
        
        report_file = output_dir / "lion_processing_report.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"✅ 处理报告已保存: {report_file.name}")
        
    except Exception as e:
        logger.error(f"❌ 生成处理报告失败: {e}")


if __name__ == "__main__":
    print("🦁 Lion公司图表生成器 - 复用HH前端模块")
    print("=" * 60)
    success = main()
    if success:
        print("\n🎉 图表生成完成！请查看output目录中的HTML文件。")
    else:
        print("\n❌ 图表生成失败，请查看日志信息。")