#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Summary Chart 模块 - 合并所有参数的箱体图
基于BoxplotChart复用数据处理和图表生成逻辑，使用Plotly subplots垂直排列所有参数
新增：在最上方添加良率对比图
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# 导入BoxplotChart进行复用
import sys
sys.path.append(str(Path(__file__).parent.parent))
from boxplot_chart import BoxplotChart

# 导入JavaScript嵌入工具 - 使用兼容的导入方式
def get_embedded_plotly_js():
    """获取嵌入式Plotly.js内容"""
    try:
        # 尝试相对导入
        from ..js_embedder import get_embedded_plotly_js as _get_embedded_plotly_js
        return _get_embedded_plotly_js()
    except ImportError:
        try:
            # 尝试绝对导入
            current_dir = Path(__file__).parent.parent
            if str(current_dir) not in sys.path:
                sys.path.append(str(current_dir))
            from js_embedder import get_embedded_plotly_js as _get_embedded_plotly_js
            return _get_embedded_plotly_js()
        except ImportError:
            # 最后回退到CDN
            logger.warning("无法导入JavaScript嵌入工具，使用CDN模式")
            return 'https://unpkg.com/plotly.js@2.26.0/dist/plotly.min.js'

logger = logging.getLogger(__name__)

class SummaryChart:
    """合并箱体图类 - 将所有参数的箱体图合并到一个页面，顶部添加良率对比图"""
    
    def __init__(self, data_dir: str = "output"):
        """
        初始化合并箱体图
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        # 复用BoxplotChart的功能
        self.boxplot_chart = BoxplotChart(data_dir)
        
        # 良率数据
        self.yield_data = None
        
        # 合并图表的样式配置
        self.summary_config = {
            'subplot_height': 450,  # 每个参数子图的高度（包括良率图）
            'subplot_spacing': 0.02,  # 子图间距
            'title_font_size': 20,
            'subplot_title_font_size': 14,
            'shared_xaxis_title': "Wafer_ID / Lot_ID",
        }
        
        # 良率图表配色方案 - 与YieldChart保持一致
        self.yield_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
    def load_data(self) -> bool:
        """
        加载数据，复用BoxplotChart的数据加载逻辑，同时加载良率数据
        
        Returns:
            bool: 是否成功加载数据
        """
        # 加载箱体图数据
        boxplot_success = self.boxplot_chart.load_data()
        
        # 加载良率数据
        yield_success = self._load_yield_data()
        
        return boxplot_success and yield_success
    
    def _load_yield_data(self) -> bool:
        """
        加载良率数据
        
        Returns:
            bool: 是否成功加载良率数据
        """
        try:
            # 查找yield文件
            yield_files = list(self.data_dir.glob("*_yield_*.csv"))
            if not yield_files:
                logger.error("未找到yield数据文件")
                return False
            
            # 使用第一个找到的yield文件
            yield_file = yield_files[0]
            logger.info(f"加载良率数据文件: {yield_file}")
            
            # 读取yield数据
            self.yield_data = pd.read_csv(yield_file)
            
            # 数据预处理
            self._preprocess_yield_data()
            
            logger.info(f"良率数据加载成功，共 {len(self.yield_data)} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"加载良率数据失败: {e}")
            return False
    
    def _preprocess_yield_data(self):
        """预处理良率数据"""
        if self.yield_data is None:
            return
        
        # 过滤掉汇总行
        self.yield_data = self.yield_data[self.yield_data['Lot_ID'] != 'ALL'].copy()
        
        # 转换良率为数值格式
        if 'Yield' in self.yield_data.columns:
            self.yield_data['Yield_Numeric'] = self.yield_data['Yield'].str.rstrip('%').astype(float)
        
        # 提取真实的Lot_ID（去掉@后缀）
        def get_true_lot_id(raw_lot_id):
            if isinstance(raw_lot_id, str) and '@' in raw_lot_id:
                return raw_lot_id.split('@')[0]
            return raw_lot_id
        
        self.yield_data['Lot_Short'] = self.yield_data['Lot_ID'].apply(get_true_lot_id)
        
        # 按Lot_Short和Wafer_ID排序
        self.yield_data = self.yield_data.sort_values(['Lot_Short', 'Wafer_ID']).reset_index(drop=True)
        
        logger.info(f"良率数据预处理完成，识别到 {self.yield_data['Lot_Short'].nunique()} 个批次")
    
    def get_available_parameters(self) -> List[str]:
        """
        获取可用的测试参数列表
        
        Returns:
            List[str]: 参数列表
        """
        return self.boxplot_chart.get_available_parameters()
    
    def create_combined_chart(self) -> go.Figure:
        """
        创建合并的图表，顶部为良率对比图，下方为所有参数的箱体图垂直排列
        
        Returns:
            go.Figure: 合并的Plotly图表对象
        """
        if self.boxplot_chart.cleaned_data is None:
            logger.error("箱体图数据未加载，无法创建合并图表")
            return go.Figure()
        
        if self.yield_data is None:
            logger.error("良率数据未加载，无法创建合并图表")
            return go.Figure()
        
        # 获取所有可用参数
        parameters = self.get_available_parameters()
        if not parameters:
            logger.error("没有可用的测试参数")
            return go.Figure()
        
        logger.info(f"开始创建包含良率图和 {len(parameters)} 个参数的合并图表")
        
        # 创建子图布局 - 第一行为良率图，后续行为参数箱体图
        subplot_titles = ["📊 批次良率对比"]  # 良率图标题
        
        # 添加参数图标题
        for param in parameters:
            param_info = self.boxplot_chart.get_parameter_info(param)
            unit_str = f" [{param_info.get('unit', '')}]" if param_info.get('unit') else ""
            test_cond = f" @{param_info.get('test_condition', '')}" if param_info.get('test_condition') else ""
            subplot_titles.append(f"{param}{unit_str}{test_cond}")
        
        # 总行数 = 1（良率图）+ len(parameters)（参数图）
        total_rows = 1 + len(parameters)
        
        fig = make_subplots(
            rows=total_rows,
            cols=1,
            shared_xaxes=False,  # 不共享X轴，让每个子图都能显示自己的X轴标签
            vertical_spacing=self.summary_config['subplot_spacing'],
            subplot_titles=subplot_titles,
            specs=[[{"secondary_y": False}] for _ in range(total_rows)]  # 每个子图的规格
        )
        
        # 第一步：添加良率对比图（第1行）
        x_labels, lot_positions = self._add_yield_comparison_chart(fig, row=1)
        
        # 第二步：为每个参数生成箱体图数据并添加到对应的子图（从第2行开始）
        for i, param in enumerate(parameters, 2):  # 从第2行开始
            try:
                # 复用BoxplotChart的数据准备逻辑
                chart_data, current_x_labels, param_info, current_lot_positions = self.boxplot_chart.prepare_chart_data(param)
                
                # 确保X轴标签和批次位置与良率图一致
                if x_labels is None:
                    x_labels = current_x_labels
                    lot_positions = current_lot_positions
                
                if chart_data.empty:
                    # 添加空数据提示
                    fig.add_annotation(
                        text=f"参数 {param} 没有有效数据",
                        xref="paper", yref=f"y{i}",
                        x=0.5, y=0.5, showarrow=False,
                        font=dict(size=12),
                        row=i, col=1
                    )
                    continue
                
                # 添加箱体图和散点图到当前子图
                self._add_parameter_traces(fig, chart_data, param_info, i)
                
                # 添加上下限线
                self._add_limit_lines(fig, param_info, i)
                
            except Exception as e:
                logger.error(f"处理参数 {param} 时出错: {e}")
                continue
        
        # 设置整体布局
        self._configure_layout(fig, parameters, x_labels, lot_positions)
        
        logger.info(f"合并图表创建完成，包含良率图和 {len(parameters)} 个参数")
        return fig
    
    def _add_yield_comparison_chart(self, fig: go.Figure, row: int) -> Tuple[List[str], Dict]:
        """
        添加Wafer良率趋势图到指定行 - 使用Lion公司的改进版本
        
        Args:
            fig: Plotly图表对象
            row: 子图行号
            
        Returns:
            Tuple[List[str], Dict]: X轴标签和批次位置信息
        """
        if self.yield_data is None or self.yield_data.empty:
            logger.warning("良率数据为空，无法生成良率趋势图")
            return [], {}
        
        # 预处理数据 - 确保数据格式正确
        yield_data = self.yield_data.copy()
        
        # 转换yield为数值（去掉百分号等）
        if 'Yield' in yield_data.columns:
            # 如果有原始Yield列，转换为数值
            if 'Yield_Numeric' not in yield_data.columns:
                yield_data['Yield_Numeric'] = yield_data['Yield'].astype(str).str.rstrip('%').astype(float)
        elif 'Yield_Rate' in yield_data.columns:
            # 如果有Yield_Rate列，直接使用
            yield_data['Yield_Numeric'] = yield_data['Yield_Rate']
        else:
            logger.error("❌ 未找到良率数据列")
            return [], {}
        
        # 过滤掉汇总行
        yield_data = yield_data[yield_data['Lot_ID'] != 'ALL'].copy()
        
        # 按Lot_ID和Wafer_ID排序
        if 'Wafer_ID' in yield_data.columns:
            try:
                # 确保Wafer_ID为数值类型进行正确排序
                yield_data['Wafer_ID_Numeric'] = pd.to_numeric(yield_data['Wafer_ID'], errors='coerce')
                yield_data = yield_data.sort_values(['Lot_ID', 'Wafer_ID_Numeric'])
            except:
                # 如果转换失败，使用字符串排序
                yield_data = yield_data.sort_values(['Lot_ID', 'Wafer_ID'])
        
        logger.info(f"✅ 成功加载 {len(yield_data)} 个晶圆的良率数据")
        logger.info(f"📊 良率范围: {yield_data['Yield_Numeric'].min():.2f}% - {yield_data['Yield_Numeric'].max():.2f}%")
        
        # 按批次分组数据并在X轴方向展开
        lot_groups = yield_data.groupby('Lot_ID') if 'Lot_ID' in yield_data.columns else {'Unknown': yield_data}
        if not isinstance(lot_groups, dict):
            lot_groups = dict(list(lot_groups))
        
        # 定义批次颜色
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
        
        x_position = 1  # 全局X轴位置计数器
        x_labels = []   # X轴标签
        x_positions = []  # X轴位置
        lot_positions = {}  # 批次边界位置
        
        for i, (lot_id, lot_data) in enumerate(lot_groups.items()):
            color = colors[i % len(colors)]
            lot_start_pos = x_position
            
            # 确定该批次的wafer_id范围
            actual_wafer_ids = lot_data['Wafer_ID'].unique()
            min_wafer_id = min(actual_wafer_ids)
            max_wafer_id = max(actual_wafer_ids)
            
            # 为当前批次的每个wafer位置分配X轴位置（包括缺失的wafer）
            lot_x_positions = []
            lot_wafer_ids = []
            lot_yields = []
            
            # 记录批次位置信息
            lot_positions[lot_id] = {'start': x_position, 'wafers': [], 'end': 0}
            
            # 遍历完整的wafer_id范围
            for wafer_id in range(min_wafer_id, max_wafer_id + 1):
                # 添加X轴标签（显示wafer_id本身）
                x_labels.append(str(wafer_id))
                x_positions.append(x_position)
                
                # 为每个wafer位置添加垂直虚线
                fig.add_vline(
                    x=x_position,
                    line_dash="dot",
                    line_color='rgba(128, 128, 128, 0.3)',
                    line_width=1,
                    row=row, col=1
                )
                
                # 检查该wafer_id是否有数据
                wafer_data = lot_data[lot_data['Wafer_ID'] == wafer_id]
                if not wafer_data.empty:
                    # 有数据的wafer添加到图表中
                    lot_x_positions.append(x_position)
                    lot_wafer_ids.append(wafer_id)
                    lot_yields.append(wafer_data['Yield_Numeric'].iloc[0])
                
                # 记录wafer信息
                lot_positions[lot_id]['wafers'].append({
                    'wafer_id': wafer_id,
                    'x_position': x_position
                })
                
                x_position += 1
            
            lot_positions[lot_id]['end'] = x_position - 1
            
            # 为每个批次添加良率趋势线
            if lot_x_positions and lot_yields:
                fig.add_trace(go.Scatter(
                    x=lot_x_positions,
                    y=lot_yields,
                    mode='lines+markers',
                    name=f'批次 {lot_id}',
                    line=dict(color=color, width=3),
                    marker=dict(size=8, symbol='circle', color=color),
                    showlegend=True,
                    hovertemplate=f'<b>批次: {lot_id}</b><br>晶圆: %{{customdata}}<br>良率: %{{y:.2f}}%<extra></extra>',
                    customdata=lot_wafer_ids,
                    legendgroup=f"yield_{lot_id}"
                ), row=row, col=1)
            
            # 添加批次分隔线（除了最后一个批次）
            if i < len(lot_groups) - 1:
                fig.add_vline(
                    x=x_position - 0.5,
                    line_dash="solid",
                    line_color='rgba(0, 0, 0, 0.3)',
                    line_width=2,
                    row=row, col=1
                )
        
        # 添加整体平均线
        if 'Yield_Numeric' in yield_data.columns:
            overall_mean = yield_data['Yield_Numeric'].mean()
            fig.add_hline(
                y=overall_mean,
                line_dash="dash",
                line_color="#FF6347",
                line_width=2,
                annotation_text=f"平均良率: {overall_mean:.2f}%",
                annotation_position="top right",
                row=row, col=1
            )
        
        logger.info(f"✅ Wafer良率趋势图创建完成，共 {len(x_labels)} 个wafer位置")
        return x_labels, lot_positions
    
    def _add_parameter_traces(self, fig: go.Figure, chart_data: pd.DataFrame, param_info: Dict, row: int):
        """
        为指定参数添加箱体图和散点图轨迹 - 完全复用BoxplotChart的逻辑
        
        Args:
            fig: Plotly图表对象
            chart_data: 图表数据
            param_info: 参数信息
            row: 子图行号
        """
        # Material Design 配色方案 - 与BoxplotChart保持完全一致
        material_design_colors = [
            '#1976D2',  # Blue 700 - 主蓝色
            '#388E3C',  # Green 700 - 绿色
            '#F57C00',  # Orange 700 - 橙色
            '#7B1FA2',  # Purple 700 - 紫色
            '#D32F2F',  # Red 700 - 红色
            '#0097A7',  # Cyan 700 - 青色
            '#5D4037',  # Brown 700 - 棕色
            '#616161',  # Grey 700 - 灰色
            '#303F9F',  # Indigo 700 - 靛蓝
            '#E64A19'   # Deep Orange 700 - 深橙
        ]
        
        for i, lot_id_val in enumerate(chart_data['lot_id'].unique()): # lot_id 现在是 True_Lot_ID
            lot_data = chart_data[chart_data['lot_id'] == lot_id_val]
            color = material_design_colors[i % len(material_design_colors)]
            
            # 为散点添加抖动效果，提高可视化效果 - 与BoxplotChart完全一致
            np.random.seed(42)  # 设置随机种子确保一致性
            jitter = np.random.uniform(-self.boxplot_chart.chart_config['jitter_amount'], 
                                     self.boxplot_chart.chart_config['jitter_amount'], 
                                     len(lot_data))
            jittered_x = lot_data['x_position'] + jitter
            
            # 添加散点图 - 使用与BoxplotChart完全相同的配置
            fig.add_trace(go.Scatter(
                x=jittered_x,  # 使用抖动后的X坐标
                y=lot_data['value'],
                mode='markers',
                name=f'{lot_id_val}', # Legend name will be True_Lot_ID
                marker=dict(
                    size=self.boxplot_chart.chart_config['scatter_size'],
                    opacity=self.boxplot_chart.chart_config['scatter_opacity'],
                    color=color,
                    line=dict(width=0.5, color='white'),  # 更细的白色边框
                    symbol='circle'  # 明确指定圆形标记
                ),
                hovertemplate=f'<b>{lot_id_val}</b><br>' +
                             'Wafer: %{customdata[0]}<br>' +
                             f'{param_info.get("parameter", "")}: %{{y}}<br>' +
                             '<extra></extra>',
                customdata=[[row['wafer_id']] for _, row in lot_data.iterrows()],
                showlegend=False  # 在汇总图中不显示图例
            ), row=row, col=1)
            
            # 为每个wafer添加箱体图 - 使用与BoxplotChart完全相同的逻辑
            for wafer_id in lot_data['wafer_id'].unique():
                wafer_data = lot_data[lot_data['wafer_id'] == wafer_id]
                
                # 修改条件：支持单个数据点显示（显示为中位线）
                if len(wafer_data) >= 1:  # 改为>=1，支持单个数据点
                    x_pos = wafer_data['x_position'].iloc[0]
                    values = wafer_data['value'].values
                    
                    if len(values) == 1:
                        # 单个数据点：只显示中位线
                        single_value = values[0]
                        fig.add_trace(go.Scatter(
                            x=[x_pos - 0.2, x_pos + 0.2],  # 横线的起点和终点
                            y=[single_value, single_value],  # 水平线
                            mode='lines',
                            line=dict(color=color, width=3),
                            name=f'{lot_id_val}-W{wafer_id}-中位线',
                            showlegend=False,
                            hovertemplate=f'<b>单点中位线</b><br>' +
                                         f'Lot: {lot_id_val}<br>' +
                                         f'Wafer: {wafer_id}<br>' +
                                         f'{param_info.get("parameter", "")}: {single_value}<br>' +
                                         '<extra></extra>'
                        ), row=row, col=1)
                    else:
                        # 多个数据点：显示完整箱体图 - 与BoxplotChart完全相同的计算
                        # 计算标准箱体图统计量
                        Q1 = np.percentile(values, 25)  # 下四分位数 (25%分位点)
                        Q2 = np.percentile(values, 50)  # 中位数 (50%分位点)  
                        Q3 = np.percentile(values, 75)  # 上四分位数 (75%分位点)
                        IQR = Q3 - Q1  # 四分位距
                        
                        # 计算须线边界
                        lower_whisker = Q1 - 1.5 * IQR  # 下须
                        upper_whisker = Q3 + 1.5 * IQR  # 上须
                        
                        # 分离正常值和异常值
                        normal_mask = (values >= lower_whisker) & (values <= upper_whisker)
                        normal_values = values[normal_mask]
                        outlier_values = values[~normal_mask]
                        
                        # 须线的实际端点（数据中在须线范围内的最大/最小值）
                        if len(normal_values) > 0:
                            actual_lower_whisker = normal_values.min()
                            actual_upper_whisker = normal_values.max()
                        else:
                            # 如果没有正常值，须线就是Q1和Q3
                            actual_lower_whisker = Q1
                            actual_upper_whisker = Q3
                        
                        # 将十六进制颜色转换为RGB以便设置透明度
                        hex_color = color.lstrip('#')
                        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                        
                        # 创建自定义箱体图 - 使用与BoxplotChart完全相同的配置
                        fig.add_trace(go.Box(
                            x=[x_pos],  # X位置
                            name=f'{lot_id_val}-W{wafer_id}', # Box name also uses True_Lot_ID
                            marker=dict(
                                color=color,
                                line=dict(width=1.5, color=color)  # 箱体边框使用相同颜色
                            ),
                            fillcolor=f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.3)',  # 半透明填充
                            opacity=self.boxplot_chart.chart_config['box_opacity'],
                            showlegend=False,
                            width=0.6,
                            boxpoints=False,  # 不显示箱体图的点，避免与散点图重复
                            line=dict(width=1.5),  # 箱体线条宽度
                            # 使用预计算的统计量
                            q1=[Q1],
                            median=[Q2], 
                            q3=[Q3],
                            lowerfence=[actual_lower_whisker],
                            upperfence=[actual_upper_whisker]
                        ), row=row, col=1)
                        
                        # 单独添加异常值散点 - 与BoxplotChart完全相同
                        if len(outlier_values) > 0:
                            fig.add_trace(go.Scatter(
                                x=[x_pos] * len(outlier_values),
                                y=outlier_values,
                                mode='markers',
                                marker=dict(
                                    size=self.boxplot_chart.chart_config['scatter_size'],  # 与散点大小一致
                                    color=color,
                                    symbol='circle-open',  # 空心圆圈表示异常值
                                    line=dict(width=1, color=color)
                                ),
                                name=f'异常值-{lot_id_val}-W{wafer_id}',
                                showlegend=False,
                                hovertemplate=f'<b>异常值</b><br>' +
                                             f'Lot: {lot_id_val}<br>' +
                                             f'Wafer: {wafer_id}<br>' +
                                             f'{param_info.get("parameter", "")}: %{{y}}<br>' +
                                             '<extra></extra>'
                            ), row=row, col=1)
    
    def _add_limit_lines(self, fig: go.Figure, param_info: Dict, row: int):
        """
        添加参数的上下限线 - 与BoxplotChart完全一致
        
        Args:
            fig: Plotly图表对象
            param_info: 参数信息
            row: 子图行号
        """
        # 添加上限线 - 使用与BoxplotChart完全相同的配置
        if param_info.get('limit_upper') is not None:
            fig.add_hline(
                y=param_info['limit_upper'],
                line_dash="dash",
                line_color=self.boxplot_chart.chart_config['limit_line_color'],
                line_width=self.boxplot_chart.chart_config['limit_line_width'],
                annotation_text=f"USL: {param_info['limit_upper']}",
                row=row, col=1
            )
        
        # 添加下限线 - 使用与BoxplotChart完全相同的配置
        if param_info.get('limit_lower') is not None:
            fig.add_hline(
                y=param_info['limit_lower'],
                line_dash="dash",
                line_color=self.boxplot_chart.chart_config['limit_line_color'],
                line_width=self.boxplot_chart.chart_config['limit_line_width'],
                annotation_text=f"LSL: {param_info['limit_lower']}",
                row=row, col=1
            )
    
    def _configure_layout(self, fig: go.Figure, parameters: List[str], x_labels: List[str], lot_positions: Dict):
        """
        配置图表的整体布局
        
        Args:
            fig: Plotly图表对象
            parameters: 参数列表
            x_labels: X轴标签
            lot_positions: 批次位置信息
        """
        # 计算总高度 = 1（良率图）+ len(parameters)（参数图）
        total_height = (1 + len(parameters)) * self.summary_config['subplot_height']
        
        # 动态计算图表宽度 - 复用BoxplotChart的逻辑
        num_total_wafers = len(x_labels) if x_labels else 20
        calculated_width = num_total_wafers * self.boxplot_chart.chart_config['pixels_per_wafer']
        final_chart_width = max(self.boxplot_chart.chart_config['min_chart_width'], calculated_width)
        
        # 生成数据集名称用于标题
        dataset_name = self._extract_dataset_name()
        
        fig.update_layout(
            title=dict(
                text=f"📊 {dataset_name} - 良率分析与参数箱体图汇总",
                font_size=self.summary_config['title_font_size'],
                x=0.5
            ),
            width=final_chart_width,
            height=total_height,
            font_size=self.boxplot_chart.chart_config['font_size'],
            hovermode='closest',
            showlegend=True,  # 显示图例（良率图需要图例）
            # 启用滚动和缩放
            dragmode='pan'
        )
        
        # 配置X轴 - 每个子图都显示自己的X轴标签
        if x_labels:
            # 计算X轴范围 - 与BoxplotChart完全一致
            x_range_start = -0.5  # 从第一个wafer的左侧0.5个单位开始
            x_range_end = len(x_labels) - 0.5  # 到最后一个wafer的右侧0.5个单位结束
            
            # 总行数 = 1（良率图）+ len(parameters)（参数图）
            total_rows = 1 + len(parameters)
            
            # 为每个子图配置X轴
            for i in range(1, total_rows + 1):
                if i == 1:
                    # 第1行：良率图的X轴配置
                    fig.update_xaxes(
                        tickmode='array',
                        tickvals=list(range(len(x_labels))),
                        ticktext=x_labels,  # 显示wafer_id标签
                        tickangle=0,
                        range=[x_range_start, x_range_end],
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='rgba(211, 211, 211, 0.5)',
                        griddash='dash',
                        fixedrange=False,
                        showticklabels=True,
                        title_text="",  # 良率图不显示X轴标题
                        row=i, col=1
                    )
                else:
                    # 第2行及以后：参数图的X轴配置
                    fig.update_xaxes(
                        tickmode='array',
                        tickvals=list(range(len(x_labels))),
                        ticktext=x_labels,  # 直接使用数字格式的WAFER_ID标签（1, 2, 3...）
                        tickangle=0,
                        range=[x_range_start, x_range_end],  # 设置X轴显示范围，紧贴数据
                        showgrid=True,        # 显示X轴垂直网格线
                        gridwidth=1,          # 网格线宽度
                        gridcolor='rgba(211, 211, 211, 0.5)', # 网格线颜色 - 浅灰带50%透明度
                        griddash='dash',      # X轴网格线也使用虚线
                        fixedrange=False,
                        showticklabels=True,  # 每个子图都显示X轴标签
                        title_text="Wafer_ID" if i == total_rows else "",  # 只有最底部显示X轴标题
                        row=i, col=1
                    )
            
            # 添加Lot_ID的二级X轴标签 - 与BoxplotChart完全一致
            if lot_positions:
                for lot_id_text, pos_info in lot_positions.items():
                    mid_position = (pos_info['start'] + pos_info['end']) / 2
                    fig.add_annotation(
                        x=mid_position,
                        y=-0.15,  # 位置在最底部X轴下方 - 与BoxplotChart一致
                        text=str(lot_id_text),
                        showarrow=False,
                        xref="x",
                        yref="paper",
                        font=dict(size=10, color="blue")
                    )
        
        # 配置Y轴
        # 第1行：良率图的Y轴配置
        fig.update_yaxes(
            title_text="良率 (%)",
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(211, 211, 211, 0.5)',
            griddash='dash',
            range=[95, 101],  # 良率图的Y轴范围，与独立良率图保持一致
            row=1, col=1
        )
        
        # 第2行及以后：参数图的Y轴配置 - 与BoxplotChart完全一致
        for i, param in enumerate(parameters, 2):  # 从第2行开始
            param_info = self.boxplot_chart.get_parameter_info(param)
            unit_str = f" [{param_info.get('unit', '')}]" if param_info.get('unit') else ""
            
            # 设置Y轴更新参数 - 与BoxplotChart完全一致
            y_axis_updates = {
                'title_text': f"{param}{unit_str}",
                'showgrid': True,
                'gridwidth': 1,
                'gridcolor': 'rgba(211, 211, 211, 0.5)',  # 网格线颜色 - 浅灰带50%透明度
                'griddash': 'dash'
            }
            
            # 根据参数的上下限设置Y轴的显示范围 - 与BoxplotChart完全一致
            limit_l = param_info.get('limit_lower') # 已经是 float 或 None
            limit_u = param_info.get('limit_upper') # 已经是 float 或 None

            if limit_l is not None and limit_u is not None:
                # 确保 lsl 是较小值, usl 是较大值
                lsl = min(limit_l, limit_u)
                usl = max(limit_l, limit_u)
                
                current_span = usl - lsl
                
                if current_span == 0:  # 上下限相等
                    # 如果 limit_l 和 limit_u 相等, padding 为其绝对值的10%，如果为0则设为1.0
                    padding = abs(usl * 0.1) if usl != 0 else 1.0
                else:  # 上下限不同
                    padding = current_span * 0.1  # padding 为上下限差值的10%
                
                y_axis_updates['range'] = [lsl - padding, usl + padding]
            
            fig.update_yaxes(**y_axis_updates, row=i, col=1)
    
    def _extract_dataset_name(self) -> str:
        """
        从数据文件名中提取数据集名称
        
        Returns:
            str: 数据集名称
        """
        try:
            # 查找cleaned文件来提取数据集名称
            cleaned_files = list(self.data_dir.glob("*_cleaned_*.csv"))
            if cleaned_files:
                filename = cleaned_files[0].stem
                # 提取@符号前的部分作为数据集名称
                if '@' in filename:
                    return filename.split('@')[0]
                else:
                    # 如果没有@符号，提取_cleaned_前的部分
                    return filename.split('_cleaned_')[0]
            return "Unknown Dataset"
        except Exception as e:
            logger.warning(f"提取数据集名称失败: {e}")
            return "CP Data"
    
    def save_summary_chart(self, output_dir: str = "charts_output") -> Optional[Path]:
        """
        保存合并图表为HTML文件
        
        Args:
            output_dir: 输出目录
            
        Returns:
            Optional[Path]: 保存路径，如果失败则返回None
        """
        try:
            # 创建合并图表
            fig = self.create_combined_chart()
            
            if fig.data is None or len(fig.data) == 0:
                logger.error("无法保存图表：合并图表为空")
                return None
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            dataset_name = self._extract_dataset_name()
            filename = f"{dataset_name}_summary_chart.html"
            file_path = output_path / filename
            
            # 保存HTML文件 - 使用本地嵌入的Plotly.js，避免CDN加载失败
            fig.write_html(
                str(file_path),
                include_plotlyjs=get_embedded_plotly_js(),
                validate=False
            )
            
            logger.info(f"合并图表已保存: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"保存合并图表失败: {e}")
            return None


def test_summary_chart():
    """测试合并图表功能"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    chart = SummaryChart(data_dir="output")
    
    if chart.load_data():
        params = chart.get_available_parameters()
        print(f"可用参数: {params}")
        
        if params:
            # 测试保存合并图表
            saved_path = chart.save_summary_chart(output_dir="charts_output")
            if saved_path:
                print(f"合并图表已保存到: {saved_path}")
            else:
                print("保存合并图表失败")
        else:
            print("没有可用的参数进行测试")
    else:
        print("数据加载失败，无法进行测试")


if __name__ == "__main__":
    test_summary_chart() 