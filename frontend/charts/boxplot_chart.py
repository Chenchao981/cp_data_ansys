#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
箱体图+散点图组合图表 - 基于Plotly实现
完全复制BVDSS1样式：箱体图+散点图叠加、双层X轴、上下限线、统计信息
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class BoxplotChart:
    """箱体图+散点图组合图表类"""
    
    def __init__(self, data_dir: str = "output"):
        """
        初始化箱体图
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.cleaned_data = None
        self.spec_data = None
        self.all_charts_cache: Dict[str, go.Figure] = {} # 新增图表缓存
        
        # 图表样式配置
        self.chart_config = {
            'min_chart_width': 1200, # 最小图表宽度
            'pixels_per_wafer': 40,  # 每个wafer在X轴上分配的像素
            'height': 600,
            'scatter_size': 2,  # 散点大小从3改为2
            'scatter_opacity': 0.7,
            'box_opacity': 0.7,
            'limit_line_color': '#FF0000',  # 红色虚线
            'limit_line_width': 2,
            'font_size': 12,
            'title_font_size': 16,
            'jitter_amount': 0.15  # 散点抖动幅度
        }
        
    def load_data(self) -> bool:
        """
        加载cleaned数据和spec数据，并预生成所有图表。
        
        Returns:
            bool: 是否成功加载数据和生成图表
        """
        try:
            # 查找cleaned文件
            cleaned_files = list(self.data_dir.glob("*_cleaned_*.csv"))
            if not cleaned_files:
                logger.error(f"在 {self.data_dir} 中未找到cleaned数据文件")
                return False
            
            # 使用第一个找到的cleaned文件
            cleaned_file = cleaned_files[0]
            self.cleaned_data = pd.read_csv(cleaned_file)
            logger.info(f"加载cleaned数据: {cleaned_file.name}")
            
            # 记录加载的cleaned_data的总行数
            if self.cleaned_data is not None:
                logger.info(f"[DATA_CHECK] Total rows in loaded self.cleaned_data: {len(self.cleaned_data)}")
            
            # 查找spec文件
            spec_files = list(self.data_dir.glob("*_spec_*.csv"))
            if not spec_files:
                logger.error(f"在 {self.data_dir} 中未找到spec数据文件")
                return False
            
            # 使用第一个找到的spec文件
            spec_file = spec_files[0]
            self.spec_data = pd.read_csv(spec_file)
            logger.info(f"加载spec数据: {spec_file.name}")

            # 数据加载成功后，预生成并缓存所有图表
            self._populate_charts_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"数据加载或图表预生成失败: {e}")
            self.cleaned_data = None #确保状态一致性
            self.spec_data = None
            self.all_charts_cache = {}
            return False
    
    def get_available_parameters(self) -> List[str]:
        """
        获取可用的测试参数列表
        
        Returns:
            List[str]: 参数列表
        """
        if self.cleaned_data is None:
            return []
        
        # 排除系统字段，返回测试参数
        exclude_cols = ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y']
        params = [col for col in self.cleaned_data.columns if col not in exclude_cols]
        return params
    
    def get_parameter_info(self, parameter: str) -> Dict:
        """
        获取参数的详细信息（单位、上下限、测试条件）
        
        Args:
            parameter: 参数名
            
        Returns:
            Dict: 参数信息字典
        """
        if self.spec_data is None:
            return {}
        
        try:
            # 查找参数列
            if parameter not in self.spec_data.columns:
                logger.warning(f"参数 {parameter} 不在spec数据中")
                return {}
            
            param_col = self.spec_data[parameter]
            
            # 提取信息 - 根据行名称查找
            unit_row = self.spec_data[self.spec_data.iloc[:, 0] == 'Unit']
            limitu_row = self.spec_data[self.spec_data.iloc[:, 0] == 'LimitU']
            limitl_row = self.spec_data[self.spec_data.iloc[:, 0] == 'LimitL']
            testcond_row = self.spec_data[self.spec_data.iloc[:, 0] == 'TestCond:']
            
            info = {
                'parameter': parameter,
                'unit': unit_row[parameter].iloc[0] if len(unit_row) > 0 and parameter in unit_row.columns else '',
                'limit_upper': limitu_row[parameter].iloc[0] if len(limitu_row) > 0 and parameter in limitu_row.columns else None,
                'limit_lower': limitl_row[parameter].iloc[0] if len(limitl_row) > 0 and parameter in limitl_row.columns else None,
                'test_condition': testcond_row[parameter].iloc[0] if len(testcond_row) > 0 and parameter in testcond_row.columns else ''
            }
            
            # 处理数值类型的限制值
            try:
                if info['limit_upper'] is not None and str(info['limit_upper']).strip():
                    info['limit_upper'] = float(info['limit_upper'])
                else:
                    info['limit_upper'] = None
                    
                if info['limit_lower'] is not None and str(info['limit_lower']).strip():
                    info['limit_lower'] = float(info['limit_lower'])
                else:
                    info['limit_lower'] = None
            except (ValueError, TypeError):
                logger.warning(f"参数 {parameter} 的限制值转换失败")
                info['limit_upper'] = None
                info['limit_lower'] = None
            
            return info
            
        except Exception as e:
            logger.error(f"获取参数 {parameter} 信息失败: {e}")
            return {}
    
    def generate_chart_title(self, parameter: str) -> str:
        """
        生成图表标题，格式：参数名[单位]@测试条件_boxplot_chart
        
        Args:
            parameter: 参数名
            
        Returns:
            str: 图表标题
        """
        param_info = self.get_parameter_info(parameter)
        
        # 构建标题
        title_parts = [parameter]
        
        if param_info.get('unit'):
            title_parts.append(f"[{param_info['unit']}]")
        
        if param_info.get('test_condition'):
            title_parts.append(f"@{param_info['test_condition']}")
            
        title_parts.append("_boxplot_chart")
        
        return "".join(title_parts)
    
    def prepare_chart_data(self, parameter: str) -> Tuple[pd.DataFrame, List[str], Dict, Dict]:
        """
        准备图表数据，按Lot_ID分组并生成X轴标签
        
        Args:
            parameter: 参数名
            
        Returns:
            Tuple[DataFrame, List[str], Dict, Dict]: (图表数据, X轴标签, 参数信息, 批次位置信息)
        """
        if self.cleaned_data is None:
            return pd.DataFrame(), [], {}, {}
        
        # 获取参数信息
        param_info = self.get_parameter_info(parameter)
        
        # 过滤有效数据（非空且为数值）
        logger.info(f"[DATA_CHECK] Processing parameter: '{parameter}'")
        if self.cleaned_data is None:
            logger.error("[DATA_CHECK] self.cleaned_data is None. Cannot proceed.")
            return pd.DataFrame(), [], param_info, {}

        # 1. 初始时，该参数列有多少非NaN值
        initial_not_null_count = self.cleaned_data[parameter].notna().sum()
        logger.info(f"[DATA_CHECK] '{parameter}' - Initial non-NaN count in self.cleaned_data: {initial_not_null_count}")

        valid_data_step1 = self.cleaned_data.dropna(subset=[parameter])
        logger.info(f"[DATA_CHECK] '{parameter}' - Rows after self.cleaned_data.dropna(subset=['{parameter}']): {len(valid_data_step1)}")
        
        valid_data = valid_data_step1[pd.to_numeric(valid_data_step1[parameter], errors='coerce').notna()].copy() 
        logger.info(f"[DATA_CHECK] '{parameter}' - Rows after pd.to_numeric filtering (final valid_data): {len(valid_data)}")
        
        if valid_data.empty:
            logger.warning(f"参数 {parameter} 没有有效数据 após filtragem completa") # Added more context to warning
            return pd.DataFrame(), [], param_info, {}

        # 定义提取真实Lot ID的函数 - 使用策略2以识别更多批次
        def get_true_lot_id(raw_lot_id):
            """提取真实Lot ID - 只去掉@后面的部分，保留更多批次信息"""
            if isinstance(raw_lot_id, str) and '@' in raw_lot_id:
                return raw_lot_id.split('@')[0]
            return raw_lot_id

        # 应用函数提取真实Lot ID，并覆盖原始Lot_ID列或创建新列后使用新列
        # 为了最小化其他代码部分的更改，我们将直接修改 'Lot_ID' 列，或者确保所有后续都用 'True_Lot_ID'
        # 这里我们选择创建一个'True_Lot_ID'列并在后续使用它
        valid_data['True_Lot_ID'] = valid_data['Lot_ID'].apply(get_true_lot_id)

        # 调试：打印提取到的唯一真实Lot_ID
        unique_true_lots = valid_data['True_Lot_ID'].unique()
        logger.info(f"[DEBUG] Unique True_Lot_IDs extracted: {unique_true_lots}")
        logger.info(f"[DEBUG] Number of unique True_Lot_IDs: {len(unique_true_lots)}")
        
        # 按True_Lot_ID和Wafer_ID排序
        valid_data = valid_data.sort_values(['True_Lot_ID', 'Wafer_ID'])

        # 针对用户查询：检查BVDSS1参数，第一个批次的第一个晶圆的数据点数量 (MOVED HERE)
        if parameter == 'BVDSS1':
            if not valid_data.empty and 'True_Lot_ID' in valid_data.columns and 'Wafer_ID' in valid_data.columns:
                # unique_true_lots_for_bvdss1 已经基于排序后的 valid_data 的 True_Lot_ID 列
                # 因此 unique_true_lots_for_bvdss1[0] 就是排序后的第一个 True_Lot_ID
                first_lot_id_for_bvdss1 = unique_true_lots[0] # unique_true_lots is already available and correct
                data_for_first_lot_bvdss1 = valid_data[valid_data['True_Lot_ID'] == first_lot_id_for_bvdss1]
                
                if not data_for_first_lot_bvdss1.empty:
                    # Wafer_ID 已经和 True_Lot_ID 一起排序了，所以第一个 wafer 就是 data_for_first_lot_bvdss1['Wafer_ID'].unique()[0]
                    # 不过为了保险，还是取 unique 再排序选第一个
                    unique_wafers_in_first_lot_bvdss1 = data_for_first_lot_bvdss1['Wafer_ID'].unique()
                    sorted_wafers = sorted(list(unique_wafers_in_first_lot_bvdss1))
                    if len(sorted_wafers) > 0:
                        first_wafer_id_for_bvdss1 = sorted_wafers[0]
                        
                        specific_wafer_data = data_for_first_lot_bvdss1[
                            data_for_first_lot_bvdss1['Wafer_ID'] == first_wafer_id_for_bvdss1
                        ]
                        point_count = len(specific_wafer_data)
                        points_values = specific_wafer_data[parameter].tolist() if parameter in specific_wafer_data else []
                        
                        logger.info(f"[USER_QUERY_CHECK - BVDSS1] First True_Lot ID (after sort): {first_lot_id_for_bvdss1}")
                        logger.info(f"[USER_QUERY_CHECK - BVDSS1] First Wafer ID in this Lot (after sort): {first_wafer_id_for_bvdss1}")
                        logger.info(f"[USER_QUERY_CHECK - BVDSS1] Number of data points for this wafer: {point_count}")
                        logger.info(f"[USER_QUERY_CHECK - BVDSS1] Values for '{parameter}': {points_values}")
            else:
                logger.info(f"[USER_QUERY_CHECK - BVDSS1] Could not perform detailed check; valid_data for BVDSS1 is empty or crucial columns missing.")
        
        # 生成X轴位置和标签
        chart_data = []
        x_labels = []
        x_position = 0
        lot_positions = {} # 使用True_Lot_ID作为键
        
        # 按True_Lot_ID分组处理
        for true_lot_id_val in valid_data['True_Lot_ID'].unique():
            lot_data = valid_data[valid_data['True_Lot_ID'] == true_lot_id_val]
            lot_positions[true_lot_id_val] = {'start': x_position, 'wafers': []}
            
            # 为每个wafer分配X轴位置
            for wafer_id in sorted(lot_data['Wafer_ID'].unique()):
                wafer_data = lot_data[lot_data['Wafer_ID'] == wafer_id]
                
                # 添加该wafer的所有数据点
                for _, row in wafer_data.iterrows():
                    chart_data.append({
                        'x_position': x_position,
                        'value': float(row[parameter]),
                        'lot_id': true_lot_id_val,  # 使用True_Lot_ID
                        'wafer_id': wafer_id,
                        'x_label': str(wafer_id)
                    })
                
                # 记录wafer信息
                lot_positions[true_lot_id_val]['wafers'].append({
                    'wafer_id': wafer_id,
                    'x_position': x_position
                })
                
                x_labels.append(str(wafer_id))
                x_position += 1
            
            lot_positions[true_lot_id_val]['end'] = x_position - 1
        
        chart_df = pd.DataFrame(chart_data)
        logger.info(f"[DATA_CHECK] '{parameter}' - Total scatter points prepared in chart_df: {len(chart_df)}")
        
        return chart_df, x_labels, param_info, lot_positions
    
    def _create_boxplot_scatter_chart(self, parameter: str) -> go.Figure: # 重命名并设为内部方法
        """
        创建箱体图+散点图组合图表
        
        Args:
            parameter: 参数名
            
        Returns:
            go.Figure: Plotly图表对象
        """
        # 准备数据
        chart_data, x_labels, param_info, lot_positions = self.prepare_chart_data(parameter)
        
        if chart_data.empty:
            # 创建空图表
            fig = go.Figure()
            fig.add_annotation(
                text=f"参数 {parameter} 没有有效数据",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # 创建图表
        fig = go.Figure()
        
        # Material Design 配色方案 - 现代且专业
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
            
            # 为散点添加抖动效果，提高可视化效果
            np.random.seed(42)  # 设置随机种子确保一致性
            jitter = np.random.uniform(-self.chart_config['jitter_amount'], 
                                     self.chart_config['jitter_amount'], 
                                     len(lot_data))
            jittered_x = lot_data['x_position'] + jitter
            
            # 添加散点图 - 使用更现代的样式和抖动效果
            fig.add_trace(go.Scatter(
                x=jittered_x,  # 使用抖动后的X坐标
                y=lot_data['value'],
                mode='markers',
                name=f'{lot_id_val}', # Legend name will be True_Lot_ID
                marker=dict(
                    size=self.chart_config['scatter_size'],
                    opacity=self.chart_config['scatter_opacity'],
                    color=color,
                    line=dict(width=0.5, color='white'),  # 更细的白色边框
                    symbol='circle'  # 明确指定圆形标记
                ),
                hovertemplate=f'<b>{lot_id_val}</b><br>' +
                             'Wafer: %{customdata[0]}<br>' +
                             f'{parameter}: %{{y}}<br>' +
                             '<extra></extra>',
                customdata=[[row['wafer_id']] for _, row in lot_data.iterrows()]
            ))
            
            # 为每个wafer添加箱体图 - 使用标准四分位数方法和自定义异常值检测
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
                                         f'{parameter}: {single_value}<br>' +
                                         '<extra></extra>'
                        ))
                    else:
                        # 多个数据点：显示完整箱体图
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
                        
                        # 创建自定义箱体图 - 使用预计算的统计量
                        fig.add_trace(go.Box(
                            x=[x_pos],  # X位置
                            name=f'{lot_id_val}-W{wafer_id}', # Box name also uses True_Lot_ID
                            marker=dict(
                                color=color,
                                line=dict(width=1.5, color=color)  # 箱体边框使用相同颜色
                            ),
                            fillcolor=f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.3)',  # 半透明填充
                            opacity=self.chart_config['box_opacity'],
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
                        ))
                        
                        # 单独添加异常值散点 - 大小与散点一致
                        if len(outlier_values) > 0:
                            fig.add_trace(go.Scatter(
                                x=[x_pos] * len(outlier_values),
                                y=outlier_values,
                                mode='markers',
                                marker=dict(
                                    size=self.chart_config['scatter_size'],  # 与散点大小一致
                                    color=color,
                                    symbol='circle-open',  # 空心圆圈表示异常值
                                    line=dict(width=1, color=color)
                                ),
                                name=f'异常值-{lot_id_val}-W{wafer_id}',
                                showlegend=False,
                                hovertemplate=f'<b>异常值</b><br>' +
                                             f'Lot: {lot_id_val}<br>' +
                                             f'Wafer: {wafer_id}<br>' +
                                             f'{parameter}: %{{y}}<br>' +
                                             '<extra></extra>'
                            ))
        
        # 添加上下限线
        if param_info.get('limit_upper') is not None:
            fig.add_hline(
                y=param_info['limit_upper'],
                line_dash="dash",
                line_color=self.chart_config['limit_line_color'],
                line_width=self.chart_config['limit_line_width'],
                annotation_text=f"USL: {param_info['limit_upper']}"
            )
        
        if param_info.get('limit_lower') is not None:
            fig.add_hline(
                y=param_info['limit_lower'],
                line_dash="dash", 
                line_color=self.chart_config['limit_line_color'],
                line_width=self.chart_config['limit_line_width'],
                annotation_text=f"LSL: {param_info['limit_lower']}"
            )
        
        # 设置布局
        title = self.generate_chart_title(parameter)
        
        # 动态计算图表宽度
        num_total_wafers = len(x_labels)
        calculated_width = num_total_wafers * self.chart_config['pixels_per_wafer']
        final_chart_width = max(self.chart_config['min_chart_width'], calculated_width)
        
        fig.update_layout(
            title=dict(
                text=title,
                font_size=self.chart_config['title_font_size'],
                x=0.5
            ),
            xaxis_title="Wafer_ID",
            yaxis_title=f"{parameter} [{param_info.get('unit', '')}]",
            width=final_chart_width, # 使用动态计算的宽度
            height=self.chart_config['height'],
            font_size=self.chart_config['font_size'],
            hovermode='closest',
            showlegend=False,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # 设置X轴刻度和标签，并添加网格线
        fig.update_xaxes(
            tickmode='array',
            tickvals=list(range(len(x_labels))),
            ticktext=x_labels,
            tickangle=0,
            showgrid=True,        # 显示X轴垂直网格线
            gridwidth=1,          # 网格线宽度
            gridcolor='rgba(211, 211, 211, 0.5)', # 网格线颜色 - 浅灰带50%透明度
            griddash='dash'       # X轴网格线也使用虚线
        )

        # 设置Y轴，并添加虚线网格线，并根据上下限调整显示范围
        y_axis_updates = {
            'showgrid': True,
            'gridwidth': 1,
            'gridcolor': 'rgba(211, 211, 211, 0.5)',  # 网格线颜色 - 浅灰带50%透明度
            'griddash': 'dash'
        }
        
        # 根据参数的上下限设置Y轴的显示范围
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
            
        fig.update_yaxes(**y_axis_updates)
        
        # 添加Lot_ID的二级X轴标签（通过annotation实现）
        for lot_id_text, pos_info in lot_positions.items(): # lot_positions is keyed by True_Lot_ID
            mid_position = (pos_info['start'] + pos_info['end']) / 2
            fig.add_annotation(
                x=mid_position,
                y=-0.15,  # 位置在主X轴下方
                text=str(lot_id_text), # Text for annotation is True_Lot_ID
                showarrow=False,
                xref="x",
                yref="paper",
                font=dict(size=10, color="blue")
            )
        
        return fig
    
    def _create_boxplot_chart(self, parameter: str) -> go.Figure:
        """
        创建箱体图+散点图组合图表
        
        Args:
            parameter: 参数名
            
        Returns:
            go.Figure: Plotly图表对象
        """
        # 准备数据
        chart_data, x_labels, param_info, lot_positions = self.prepare_chart_data(parameter)
        
        if chart_data.empty:
            # 创建空图表
            fig = go.Figure()
            fig.add_annotation(
                text=f"参数 {parameter} 没有有效数据",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # 创建图表
        fig = go.Figure()
        
        # Material Design 配色方案 - 现代且专业
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
            
            # 为散点添加抖动效果，提高可视化效果
            np.random.seed(42)  # 设置随机种子确保一致性
            jitter = np.random.uniform(-self.chart_config['jitter_amount'], 
                                     self.chart_config['jitter_amount'], 
                                     len(lot_data))
            jittered_x = lot_data['x_position'] + jitter
            
            # 添加散点图 - 使用更现代的样式和抖动效果
            fig.add_trace(go.Scatter(
                x=jittered_x,  # 使用抖动后的X坐标
                y=lot_data['value'],
                mode='markers',
                name=f'{lot_id_val}', # Legend name will be True_Lot_ID
                marker=dict(
                    size=self.chart_config['scatter_size'],
                    opacity=self.chart_config['scatter_opacity'],
                    color=color,
                    line=dict(width=0.5, color='white'),  # 更细的白色边框
                    symbol='circle'  # 明确指定圆形标记
                ),
                hovertemplate=f'<b>{lot_id_val}</b><br>' +
                             'Wafer: %{customdata[0]}<br>' +
                             f'{parameter}: %{{y}}<br>' +
                             '<extra></extra>',
                customdata=[[row['wafer_id']] for _, row in lot_data.iterrows()]
            ))
            
            # 为每个wafer添加箱体图 - 使用标准四分位数方法和自定义异常值检测
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
                                         f'{parameter}: {single_value}<br>' +
                                         '<extra></extra>'
                        ))
                    else:
                        # 多个数据点：显示完整箱体图
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
                        
                        # 创建自定义箱体图 - 使用预计算的统计量
                        fig.add_trace(go.Box(
                            x=[x_pos],  # X位置
                            name=f'{lot_id_val}-W{wafer_id}', # Box name also uses True_Lot_ID
                            marker=dict(
                                color=color,
                                line=dict(width=1.5, color=color)  # 箱体边框使用相同颜色
                            ),
                            fillcolor=f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.3)',  # 半透明填充
                            opacity=self.chart_config['box_opacity'],
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
                        ))
                        
                        # 单独添加异常值散点 - 大小与散点一致
                        if len(outlier_values) > 0:
                            fig.add_trace(go.Scatter(
                                x=[x_pos] * len(outlier_values),
                                y=outlier_values,
                                mode='markers',
                                marker=dict(
                                    size=self.chart_config['scatter_size'],  # 与散点大小一致
                                    color=color,
                                    symbol='circle-open',  # 空心圆圈表示异常值
                                    line=dict(width=1, color=color)
                                ),
                                name=f'异常值-{lot_id_val}-W{wafer_id}',
                                showlegend=False,
                                hovertemplate=f'<b>异常值</b><br>' +
                                             f'Lot: {lot_id_val}<br>' +
                                             f'Wafer: {wafer_id}<br>' +
                                             f'{parameter}: %{{y}}<br>' +
                                             '<extra></extra>'
                            ))
        
        # 添加上下限线
        if param_info.get('limit_upper') is not None:
            fig.add_hline(
                y=param_info['limit_upper'],
                line_dash="dash",
                line_color=self.chart_config['limit_line_color'],
                line_width=self.chart_config['limit_line_width'],
                annotation_text=f"USL: {param_info['limit_upper']}"
            )
        
        if param_info.get('limit_lower') is not None:
            fig.add_hline(
                y=param_info['limit_lower'],
                line_dash="dash", 
                line_color=self.chart_config['limit_line_color'],
                line_width=self.chart_config['limit_line_width'],
                annotation_text=f"LSL: {param_info['limit_lower']}"
            )
        
        # 设置布局
        title = self.generate_chart_title(parameter)
        
        # 动态计算图表宽度
        num_total_wafers = len(x_labels)
        calculated_width = num_total_wafers * self.chart_config['pixels_per_wafer']
        final_chart_width = max(self.chart_config['min_chart_width'], calculated_width)
        
        fig.update_layout(
            title=dict(
                text=title,
                font_size=self.chart_config['title_font_size'],
                x=0.5
            ),
            xaxis_title="Wafer_ID",
            yaxis_title=f"{parameter} [{param_info.get('unit', '')}]",
            width=final_chart_width, # 使用动态计算的宽度
            height=self.chart_config['height'],
            font_size=self.chart_config['font_size'],
            hovermode='closest',
            showlegend=False,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # 设置X轴刻度和标签，并添加网格线
        # 计算X轴的实际数据范围，消除两端空白
        x_range_start = -0.5  # 从第一个wafer的左侧0.5个单位开始
        x_range_end = len(x_labels) - 0.5  # 到最后一个wafer的右侧0.5个单位结束
        
        fig.update_xaxes(
            tickmode='array',
            tickvals=list(range(len(x_labels))),
            ticktext=x_labels,
            tickangle=0,
            range=[x_range_start, x_range_end],  # 设置X轴显示范围，紧贴数据
            showgrid=True,        # 显示X轴垂直网格线
            gridwidth=1,          # 网格线宽度
            gridcolor='rgba(211, 211, 211, 0.5)', # 网格线颜色 - 浅灰带50%透明度
            griddash='dash'       # X轴网格线也使用虚线
        )

        # 设置Y轴，并添加虚线网格线，并根据上下限调整显示范围
        y_axis_updates = {
            'showgrid': True,
            'gridwidth': 1,
            'gridcolor': 'rgba(211, 211, 211, 0.5)',  # 网格线颜色 - 浅灰带50%透明度
            'griddash': 'dash'
        }
        
        # 根据参数的上下限设置Y轴的显示范围
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
            
        fig.update_yaxes(**y_axis_updates)
        
        # 添加Lot_ID的二级X轴标签（通过annotation实现）
        for lot_id_text, pos_info in lot_positions.items(): # lot_positions is keyed by True_Lot_ID
            mid_position = (pos_info['start'] + pos_info['end']) / 2
            fig.add_annotation(
                x=mid_position,
                y=-0.15,  # 位置在主X轴下方
                text=str(lot_id_text), # Text for annotation is True_Lot_ID
                showarrow=False,
                xref="x",
                yref="paper",
                font=dict(size=10, color="blue")
            )
        
        return fig
    
    def _populate_charts_cache(self):
        """填充图表缓存"""
        if self.cleaned_data is None or self.spec_data is None:
            logger.error("数据未完全加载，无法生成图表。")
            return
        
        # 性能优化：减少详细日志，只显示开始信息
        available_params = self.get_available_parameters()
        logger.info(f"开始生成 {len(available_params)} 个箱体图表...")
        
        success_count = 0
        for param in available_params:
            try:
                chart_fig = self._create_boxplot_chart(param)
                if chart_fig is not None:
                    self.all_charts_cache[param] = chart_fig
                    success_count += 1
            except Exception as e:
                logger.error(f"生成参数 {param} 的图表失败: {e}")
        
        # 性能优化：只输出摘要信息
        logger.info(f"箱体图表生成完成: {success_count}/{len(available_params)} 个成功")

    def get_chart(self, parameter: str) -> Optional[go.Figure]:
        """
        从缓存中获取指定参数的图表。

        Args:
            parameter: 参数名

        Returns:
            Optional[go.Figure]: Plotly图表对象，如果未找到则返回None。
        """
        chart = self.all_charts_cache.get(parameter)
        if chart is None:
            logger.warning(f"缓存中未找到参数 {parameter} 的图表。可能需要先加载数据。")
        return chart

    def get_all_cached_charts(self) -> Dict[str, go.Figure]:
        """
        获取所有已缓存的图表。

        Returns:
            Dict[str, go.Figure]: 参数名 -> 图表对象的字典。
        """
        return self.all_charts_cache

    def generate_all_parameter_charts(self) -> Dict[str, go.Figure]: # 此方法现在主要用于确保缓存填充并返回
        """
        确保所有参数的图表已生成并缓存，然后返回缓存的图表。
        
        Returns:
            Dict[str, go.Figure]: 参数名->图表对象的字典
        """
        if not self.all_charts_cache and (self.cleaned_data is not None and self.spec_data is not None):
            logger.info("缓存为空，尝试重新填充图表缓存。")
            self._populate_charts_cache()
        elif self.cleaned_data is None or self.spec_data is None:
            logger.warning("数据未加载，无法生成图表。")
            return {}
            
        return self.all_charts_cache
    
    def save_chart(self, parameter: str, output_dir: str = "charts_output") -> Optional[Path]:
        """
        保存指定参数的图表为HTML文件（从缓存获取）。
        
        Args:
            parameter: 参数名
            output_dir: 输出目录
            
        Returns:
            Optional[Path]: 保存路径，如果失败则返回None。
        """
        try:
            figure_to_save = self.get_chart(parameter)
            
            if figure_to_save is None:
                logger.error(f"无法保存图表：未找到参数 {parameter} 的缓存图表。")
                return None
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            title = self.generate_chart_title(parameter)
            filename = f"{title}.html" # 保持原文件名格式
            file_path = output_path / filename
            
            # 使用unpkg CDN减小文件大小，保留完整工具栏功能
            figure_to_save.write_html(
                str(file_path),
                include_plotlyjs='https://unpkg.com/plotly.js@2.26.0/dist/plotly.min.js',
                validate=False  # 跳过验证，提升速度
            )
            logger.info(f"图表已保存: {file_path}")
            
            return file_path
            
        except Exception as e:
            logger.error(f"保存参数 {parameter} 的图表失败: {e}")
            return None

    def save_all_charts(self, output_dir: str = "charts_output") -> List[Path]:
        """
        批量保存所有缓存的图表为HTML文件。

        Args:
            output_dir: 输出目录。

        Returns:
            List[Path]: 成功保存的图表文件路径列表。
        """
        saved_paths: List[Path] = []
        if not self.all_charts_cache:
            logger.warning("图表缓存为空，没有图表可以保存。请先加载数据。")
            return saved_paths

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 性能优化：减少详细日志，只显示开始和结束
        logger.info(f"开始批量保存 {len(self.all_charts_cache)} 个箱体图表...")

        success_count = 0
        for parameter, figure in self.all_charts_cache.items():
            try:
                title = self.generate_chart_title(parameter)
                filename = f"{title}.html"
                file_path = output_path / filename
                
                # 使用unpkg CDN减小文件大小，保留完整工具栏功能
                figure.write_html(
                    str(file_path),
                    include_plotlyjs='https://unpkg.com/plotly.js@2.26.0/dist/plotly.min.js',
                    validate=False  # 跳过验证，提升速度
                )
                saved_paths.append(file_path)
                success_count += 1
            except Exception as e:
                logger.error(f"保存参数 {parameter} 的图表失败: {e}")
        
        # 性能优化：只输出摘要信息
        logger.info(f"箱体图表保存完成: {success_count}/{len(self.all_charts_cache)} 个成功")
        return saved_paths


def test_boxplot_chart():
    """测试箱体图表功能"""
    # chart = BoxplotChart() # 使用默认 "output" 目录
    # 假设测试数据在项目根目录下的 "data/NCETSG7120BAA_FA54-5339@203" 类似的结构中
    # 为了测试，我们可能需要指向一个包含 _cleaned_ 和 _spec_ 文件的特定目录
    # 这里我们假设 "output" 目录是 setup 好的，或者测试前会准备好。
    # 如果要测试实际数据目录，可以这样做：
    # chart = BoxplotChart(data_dir="data/NCETSG7120BAA_FA54-5339@203")
    
    # 使用默认 "output" 文件夹，确保里面有测试用的 _cleaned_ 和 _spec_ 文件
    chart = BoxplotChart(data_dir="output") 
    
    if chart.load_data(): # load_data 现在也会预缓存图表
        params = chart.get_available_parameters()
        print(f"可用参数: {params}")
        
        if params:
            test_param = params[0]
            
            # 从缓存获取图表
            fig = chart.get_chart(test_param)
            if fig:
                print(f"成功从缓存获取参数 {test_param} 的图表")
                # fig.show() # 可选：在交互环境中显示图表
            else:
                print(f"未能从缓存获取参数 {test_param} 的图表")
                return

            # 测试保存单个图表
            saved_single_path = chart.save_chart(test_param, output_dir="test_charts_output/single")
            if saved_single_path:
                print(f"单个图表已保存到: {saved_single_path}")

            # 测试批量保存所有图表
            print("\n开始测试批量保存所有图表...")
            saved_all_paths = chart.save_all_charts(output_dir="test_charts_output/all_cached")
            if saved_all_paths:
                print(f"已批量保存 {len(saved_all_paths)} 个图表到: test_charts_output/all_cached")
            else:
                print("批量保存图表失败或没有图表可保存。")

        else:
            print("没有可用的参数进行测试。")
    else:
        print("数据加载失败，无法进行测试。")


if __name__ == "__main__":
    # 配置日志记录，方便调试
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    test_boxplot_chart() 