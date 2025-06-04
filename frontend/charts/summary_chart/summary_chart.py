#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Summary Chart 模块 - 合并所有参数的箱体图
基于BoxplotChart复用数据处理和图表生成逻辑，使用Plotly subplots垂直排列所有参数
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

logger = logging.getLogger(__name__)

class SummaryChart:
    """合并箱体图类 - 将所有参数的箱体图合并到一个页面"""
    
    def __init__(self, data_dir: str = "output"):
        """
        初始化合并箱体图
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        # 复用BoxplotChart的功能
        self.boxplot_chart = BoxplotChart(data_dir)
        
        # 合并图表的样式配置
        self.summary_config = {
            'subplot_height': 450,  # 每个参数子图的高度
            'subplot_spacing': 0.02,  # 子图间距
            'title_font_size': 20,
            'subplot_title_font_size': 14,
            'shared_xaxis_title': "Wafer_ID / Lot_ID",
        }
        
    def load_data(self) -> bool:
        """
        加载数据，复用BoxplotChart的数据加载逻辑
        
        Returns:
            bool: 是否成功加载数据
        """
        return self.boxplot_chart.load_data()
    
    def get_available_parameters(self) -> List[str]:
        """
        获取可用的测试参数列表
        
        Returns:
            List[str]: 参数列表
        """
        return self.boxplot_chart.get_available_parameters()
    
    def create_combined_chart(self) -> go.Figure:
        """
        创建合并的箱体图，所有参数垂直排列
        
        Returns:
            go.Figure: 合并的Plotly图表对象
        """
        if self.boxplot_chart.cleaned_data is None:
            logger.error("数据未加载，无法创建合并图表")
            return go.Figure()
        
        # 获取所有可用参数
        parameters = self.get_available_parameters()
        if not parameters:
            logger.error("没有可用的测试参数")
            return go.Figure()
        
        logger.info(f"开始创建包含 {len(parameters)} 个参数的合并图表")
        
        # 创建子图布局 - 垂直排列，共享X轴
        subplot_titles = []
        for param in parameters:
            param_info = self.boxplot_chart.get_parameter_info(param)
            unit_str = f" [{param_info.get('unit', '')}]" if param_info.get('unit') else ""
            test_cond = f" @{param_info.get('test_condition', '')}" if param_info.get('test_condition') else ""
            subplot_titles.append(f"{param}{unit_str}{test_cond}")
        
        fig = make_subplots(
            rows=len(parameters),
            cols=1,
            shared_xaxes=False,  # 不共享X轴，让每个子图都能显示自己的X轴标签
            vertical_spacing=self.summary_config['subplot_spacing'],
            subplot_titles=subplot_titles,
            specs=[[{"secondary_y": False}] for _ in parameters]  # 每个子图的规格
        )
        
        # 为每个参数生成箱体图数据并添加到对应的子图
        x_labels = None  # 用于确保所有子图使用相同的X轴标签
        lot_positions = None  # 批次位置信息
        
        for i, param in enumerate(parameters, 1):
            try:
                # 复用BoxplotChart的数据准备逻辑
                chart_data, current_x_labels, param_info, current_lot_positions = self.boxplot_chart.prepare_chart_data(param)
                
                # 第一个参数时保存X轴标签和批次位置，后续参数复用
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
        
        logger.info(f"合并图表创建完成，包含 {len(parameters)} 个参数")
        return fig
    
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
        # 计算总高度
        total_height = len(parameters) * self.summary_config['subplot_height']
        
        # 动态计算图表宽度 - 复用BoxplotChart的逻辑
        num_total_wafers = len(x_labels) if x_labels else 20
        calculated_width = num_total_wafers * self.boxplot_chart.chart_config['pixels_per_wafer']
        final_chart_width = max(self.boxplot_chart.chart_config['min_chart_width'], calculated_width)
        
        # 生成数据集名称用于标题
        dataset_name = self._extract_dataset_name()
        
        fig.update_layout(
            title=dict(
                text=f"📊 {dataset_name} - 所有参数箱体图汇总",
                font_size=self.summary_config['title_font_size'],
                x=0.5
            ),
            width=final_chart_width,
            height=total_height,
            font_size=self.boxplot_chart.chart_config['font_size'],
            hovermode='closest',
            showlegend=False,
            # 启用滚动和缩放
            dragmode='pan'
        )
        
        # 配置X轴 - 每个子图都显示自己的X轴标签
        if x_labels:
            # 计算X轴范围 - 与BoxplotChart完全一致
            x_range_start = -0.5  # 从第一个wafer的左侧0.5个单位开始
            x_range_end = len(x_labels) - 0.5  # 到最后一个wafer的右侧0.5个单位结束
            
            # 直接使用数字格式的x_labels（1, 2, 3...），与单个箱体图保持一致
            
            # 为每个子图配置X轴，让每个参数都显示wafer_id标签
            for i in range(1, len(parameters) + 1):
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
                    title_text="Wafer_ID" if i == len(parameters) else "",  # 只有最底部显示X轴标题
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
        
        # 配置Y轴标签和范围 - 与BoxplotChart完全一致
        for i, param in enumerate(parameters, 1):
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
            
            # 保存HTML文件
            fig.write_html(
                str(file_path),
                include_plotlyjs='https://unpkg.com/plotly.js@2.26.0/dist/plotly.min.js',
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