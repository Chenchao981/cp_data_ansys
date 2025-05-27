#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
良率图表模块 - 基于Plotly实现
完全复制BoxplotChart架构：预生成缓存、HTML输出、批量保存
支持多种良率分析图表：趋势图、对比图、分布图、失效分析
新增：基于参数的折线图，参考箱体图布局方式
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

class YieldChart:
    """良率图表类 - 生成多种yield分析图表"""
    
    def __init__(self, data_dir: str = "output"):
        """
        初始化良率图表
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.yield_data = None
        self.spec_data = None  # 新增spec数据支持
        self.cleaned_data = None  # 新增cleaned数据支持
        self.all_charts_cache: Dict[str, go.Figure] = {}  # 图表缓存
        
        # 图表样式配置
        self.chart_config = {
            'height': 600,
            'font_size': 12,
            'title_font_size': 16,
            'colors': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'],
            'trend_line_color': '#FF0000',
            'mean_line_color': '#FF6347',
            'std_line_color': '#FFA500',
            'min_chart_width': 1200,  # 最小图表宽度
            'pixels_per_wafer': 40,   # 每个wafer在X轴上分配的像素
        }
        
        # 支持的图表类型
        self.chart_types = [
            'wafer_trend',      # Wafer良率趋势图
            'lot_comparison',   # 批次对比图  
            'yield_distribution', # 良率分布直方图
            'failure_analysis'  # 失效类型分析饼图
        ]
        
        # 新增：参数折线图类型（动态生成）
        self.parameter_chart_types = []
        
    def load_data(self) -> bool:
        """
        加载yield数据、spec数据和cleaned数据，并预生成所有图表。
        
        Returns:
            bool: 是否成功加载数据和生成图表
        """
        try:
            # 1. 加载yield数据
            yield_files = list(self.data_dir.glob("*_yield_*.csv"))
            if not yield_files:
                logger.error(f"在 {self.data_dir} 中未找到yield数据文件")
                return False
            
            yield_file = yield_files[0]
            self.yield_data = pd.read_csv(yield_file)
            logger.info(f"加载yield数据: {yield_file.name}")
            
            # 2. 加载spec数据
            spec_files = list(self.data_dir.glob("*_spec_*.csv"))
            if spec_files:
                spec_file = spec_files[0]
                self.spec_data = pd.read_csv(spec_file)
                logger.info(f"加载spec数据: {spec_file.name}")
            else:
                logger.warning("未找到spec数据文件，参数折线图功能将受限")
            
            # 3. 加载cleaned数据
            cleaned_files = list(self.data_dir.glob("*_cleaned_*.csv"))
            if cleaned_files:
                cleaned_file = cleaned_files[0]
                self.cleaned_data = pd.read_csv(cleaned_file)
                logger.info(f"加载cleaned数据: {cleaned_file.name}")
            else:
                logger.warning("未找到cleaned数据文件，参数折线图功能将受限")
            
            # 数据预处理
            self._preprocess_data()
            
            # 获取可用参数并生成参数图表类型
            self._setup_parameter_charts()
            
            # 数据加载成功后，预生成并缓存所有图表
            self._populate_charts_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"数据加载或图表预生成失败: {e}")
            self.yield_data = None
            self.spec_data = None
            self.cleaned_data = None
            self.all_charts_cache = {}
            return False
    
    def _preprocess_data(self):
        """预处理yield数据"""
        if self.yield_data is None:
            return
        
        # 过滤掉汇总行
        self.wafer_data = self.yield_data[self.yield_data['Lot_ID'] != 'ALL'].copy()
        self.summary_data = self.yield_data[self.yield_data['Lot_ID'] == 'ALL'].copy()
        
        # 转换yield为数值
        if 'Yield' in self.wafer_data.columns:
            self.wafer_data['Yield_Numeric'] = self.wafer_data['Yield'].str.rstrip('%').astype(float)
        
        # 提取批次简称
        self.wafer_data['Lot_Short'] = self.wafer_data['Lot_ID'].str.extract(r'(FA54-\d+)')
        
        # 计算失效总数
        failure_columns = ['Bin3', 'Bin4', 'Bin6', 'Bin7', 'Bin8', 'Bin9']
        self.wafer_data['Total_Failures'] = self.wafer_data[failure_columns].sum(axis=1)
        
        logger.info(f"预处理完成: {len(self.wafer_data)} 个wafer, {self.wafer_data['Lot_Short'].nunique()} 个批次")
    
    def _setup_parameter_charts(self):
        """设置参数图表类型"""
        if self.spec_data is None or self.cleaned_data is None:
            logger.warning("缺少spec或cleaned数据，无法生成参数折线图")
            return
        
        # 获取可用参数
        exclude_cols = ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y']
        available_params = [col for col in self.cleaned_data.columns if col not in exclude_cols]
        
        # 过滤在spec中存在的参数
        if 'Parameter' in self.spec_data.columns:
            spec_params = self.spec_data.columns[1:].tolist()  # 排除第一列'Parameter'
            available_params = [param for param in available_params if param in spec_params]
        
        self.parameter_chart_types = [f"param_{param}" for param in available_params]
        logger.info(f"设置参数图表类型: {len(self.parameter_chart_types)} 个参数")
    
    def get_available_chart_types(self) -> List[str]:
        """
        获取可用的图表类型列表
        
        Returns:
            List[str]: 图表类型列表
        """
        return self.chart_types.copy() + self.parameter_chart_types.copy()
    
    def get_available_parameters(self) -> List[str]:
        """
        获取可用的测试参数列表
        
        Returns:
            List[str]: 参数列表
        """
        if self.cleaned_data is None:
            return []
        
        exclude_cols = ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y']
        params = [col for col in self.cleaned_data.columns if col not in exclude_cols]
        
        # 过滤在spec中存在的参数
        if self.spec_data is not None and 'Parameter' in self.spec_data.columns:
            spec_params = self.spec_data.columns[1:].tolist()
            params = [param for param in params if param in spec_params]
        
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
            if parameter not in self.spec_data.columns:
                logger.warning(f"参数 {parameter} 不在spec数据中")
                return {}
            
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
    
    def generate_chart_title(self, chart_type: str) -> str:
        """
        生成图表标题
        
        Args:
            chart_type: 图表类型
            
        Returns:
            str: 图表标题
        """
        # 处理参数图表
        if chart_type.startswith('param_'):
            parameter = chart_type[6:]  # 移除'param_'前缀
            param_info = self.get_parameter_info(parameter)
            
            # 构建标题：参数+[单位]+@测试条件+_yield_line_chart
            title_parts = [parameter]
            
            if param_info.get('unit'):
                title_parts.append(f"[{param_info['unit']}]")
            
            if param_info.get('test_condition'):
                title_parts.append(f"@{param_info['test_condition']}")
                
            title_parts.append("_yield_line_chart")
            
            return "".join(title_parts)
        
        # 处理基础图表类型
        title_map = {
            'wafer_trend': 'Wafer良率趋势分析_yield_chart',
            'lot_comparison': '批次良率对比分析_yield_chart',
            'yield_distribution': '良率分布统计_yield_chart',
            'failure_analysis': '失效类型分析_yield_chart'
        }
        
        return title_map.get(chart_type, f'{chart_type}_yield_chart')
    
    def prepare_parameter_chart_data(self, parameter: str) -> Tuple[pd.DataFrame, List[str], Dict, Dict]:
        """
        准备参数图表数据，按Lot_ID分组并生成X轴标签
        
        Args:
            parameter: 参数名
            
        Returns:
            Tuple[DataFrame, List[str], Dict, Dict]: (图表数据, X轴标签, 参数信息, 批次位置信息)
        """
        if self.cleaned_data is None:
            return pd.DataFrame(), [], {}, {}
        
        # 获取参数信息
        param_info = self.get_parameter_info(parameter)
        
        # 过滤包含该参数的数据
        param_data = self.cleaned_data[['Lot_ID', 'Wafer_ID', parameter]].copy()
        param_data = param_data.dropna(subset=[parameter])
        
        if param_data.empty:
            return pd.DataFrame(), [], param_info, {}
        
        # 提取批次简称
        def get_true_lot_id(raw_lot_id):
            """提取真实的批次ID"""
            if pd.isna(raw_lot_id):
                return "Unknown"
            lot_str = str(raw_lot_id)
            if "FA54-" in lot_str:
                parts = lot_str.split("FA54-")
                if len(parts) > 1:
                    fa_part = parts[1]
                    if "-" in fa_part:
                        return f"FA54-{fa_part.split('-')[0]}"
            return lot_str
        
        param_data['True_Lot_ID'] = param_data['Lot_ID'].apply(get_true_lot_id)
        
        # 按批次分组并计算位置
        lot_positions = {}
        x_labels = []
        current_pos = 0
        
        for lot_id in param_data['True_Lot_ID'].unique():
            lot_data = param_data[param_data['True_Lot_ID'] == lot_id]
            wafer_count = len(lot_data)
            
            lot_positions[lot_id] = {
                'start': current_pos,
                'end': current_pos + wafer_count - 1,
                'center': current_pos + wafer_count / 2 - 0.5
            }
            
            # 添加wafer标签
            for _, row in lot_data.iterrows():
                x_labels.append(f"W{row['Wafer_ID']}")
            
            current_pos += wafer_count
        
        # 准备图表数据
        chart_data = param_data.copy()
        chart_data['x_position'] = range(len(chart_data))
        chart_data['lot_id'] = chart_data['True_Lot_ID']
        chart_data['wafer_id'] = chart_data['Wafer_ID']
        chart_data['value'] = chart_data[parameter]
        
        return chart_data, x_labels, param_info, lot_positions
    
    def _create_parameter_line_chart(self, parameter: str) -> go.Figure:
        """创建参数折线图，参考箱体图布局"""
        fig = go.Figure()
        
        if self.cleaned_data is None:
            return fig
        
        # 准备数据
        chart_data, x_labels, param_info, lot_positions = self.prepare_parameter_chart_data(parameter)
        
        if chart_data.empty:
            return fig
        
        # 计算图表宽度
        total_wafers = len(chart_data)
        chart_width = max(self.chart_config['min_chart_width'], 
                         total_wafers * self.chart_config['pixels_per_wafer'])
        
        # 按批次绘制折线
        colors = self.chart_config['colors']
        for i, (lot_id, pos_info) in enumerate(lot_positions.items()):
            lot_data = chart_data[chart_data['lot_id'] == lot_id]
            
            fig.add_trace(go.Scatter(
                x=lot_data['x_position'],
                y=lot_data['value'],
                mode='lines+markers',
                name=lot_id,
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=4, symbol='circle'),
                hovertemplate=f'<b>{lot_id}</b><br>Wafer: W%{{customdata}}<br>{parameter}: %{{y}}<extra></extra>',
                customdata=lot_data['wafer_id']
            ))
        
        # 添加规格限制线
        if param_info.get('limit_upper') is not None:
            fig.add_hline(
                y=param_info['limit_upper'],
                line_dash="dash",
                line_color=self.chart_config['trend_line_color'],
                line_width=self.chart_config.get('limit_line_width', 2),
                annotation_text=f"上限: {param_info['limit_upper']}"
            )
        
        if param_info.get('limit_lower') is not None:
            fig.add_hline(
                y=param_info['limit_lower'],
                line_dash="dash",
                line_color=self.chart_config['trend_line_color'],
                line_width=self.chart_config.get('limit_line_width', 2),
                annotation_text=f"下限: {param_info['limit_lower']}"
            )
        
        # 设置Y轴范围
        y_min = chart_data['value'].min()
        y_max = chart_data['value'].max()
        y_range = y_max - y_min
        
        if param_info.get('limit_lower') is not None:
            y_min = min(y_min, param_info['limit_lower'])
        if param_info.get('limit_upper') is not None:
            y_max = max(y_max, param_info['limit_upper'])
        
        # 添加一些边距
        margin = y_range * 0.1 if y_range > 0 else 1
        y_min -= margin
        y_max += margin
        
        # 更新布局 - 双层X轴
        fig.update_layout(
            title=f"📈 {parameter} 良率折线图",
            xaxis=dict(
                title="Wafer编号",
                tickmode='array',
                tickvals=list(range(len(x_labels))),
                ticktext=x_labels,
                tickangle=45,
                range=[-0.5, len(x_labels) - 0.5]
            ),
            yaxis=dict(
                title=f"{parameter} [{param_info.get('unit', '')}]",
                range=[y_min, y_max]
            ),
            width=chart_width,
            height=self.chart_config['height'],
            font=dict(size=self.chart_config['font_size']),
            title_font_size=self.chart_config['title_font_size'],
            hovermode='x unified'
        )
        
        # 添加批次标注（下层X轴）
        for lot_id, pos_info in lot_positions.items():
            fig.add_annotation(
                x=pos_info['center'],
                y=-0.15,
                text=str(lot_id),
                showarrow=False,
                xref="x",
                yref="paper",
                font=dict(size=10, color="blue")
            )
        
        return fig

    def _create_wafer_trend_chart(self) -> go.Figure:
        """创建Wafer良率趋势图"""
        fig = go.Figure()
        
        if self.wafer_data is None or self.wafer_data.empty:
            return fig
        
        lots = self.wafer_data['Lot_Short'].unique()
        colors = self.chart_config['colors']
        
        for i, lot in enumerate(lots):
            lot_data = self.wafer_data[self.wafer_data['Lot_Short'] == lot].sort_values('Wafer_ID')
            
            fig.add_trace(go.Scatter(
                x=lot_data['Wafer_ID'],
                y=lot_data['Yield_Numeric'],
                mode='lines+markers',
                name=lot,
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=8, symbol='circle'),
                hovertemplate=f'<b>{lot}</b><br>Wafer: %{{x}}<br>良率: %{{y:.2f}}%<extra></extra>'
            ))
        
        # 添加平均线
        overall_mean = self.wafer_data['Yield_Numeric'].mean()
        fig.add_hline(
            y=overall_mean, 
            line_dash="dash", 
            line_color=self.chart_config['mean_line_color'],
            annotation_text=f"平均良率: {overall_mean:.2f}%"
        )
        
        fig.update_layout(
            title="📈 Wafer良率趋势分析",
            xaxis_title="Wafer编号",
            yaxis_title="良率 (%)",
            yaxis=dict(range=[95, 101]),
            hovermode='x unified',
            height=self.chart_config['height'],
            font=dict(size=self.chart_config['font_size']),
            title_font_size=self.chart_config['title_font_size']
        )
        
        return fig
    
    def _create_lot_comparison_chart(self) -> go.Figure:
        """创建批次对比图"""
        fig = go.Figure()
        
        if self.wafer_data is None or self.wafer_data.empty:
            return fig
        
        lot_stats = self.wafer_data.groupby('Lot_Short')['Yield_Numeric'].agg([
            'mean', 'std', 'min', 'max', 'count'
        ]).reset_index()
        
        colors = self.chart_config['colors']
        
        # 柱状图
        fig.add_trace(go.Bar(
            x=lot_stats['Lot_Short'],
            y=lot_stats['mean'],
            error_y=dict(type='data', array=lot_stats['std']),
            name='平均良率',
            marker_color=colors[:len(lot_stats)],
            hovertemplate='<b>%{x}</b><br>平均良率: %{y:.2f}%<br>标准差: %{error_y.array:.2f}%<extra></extra>'
        ))
        
        # 添加数据标签
        for i, row in lot_stats.iterrows():
            fig.add_annotation(
                x=row['Lot_Short'],
                y=row['mean'] + row['std'] + 0.2,
                text=f"{row['mean']:.2f}%<br>({int(row['count'])} wafers)",
                showarrow=False,
                font=dict(size=self.chart_config['font_size'])
            )
        
        fig.update_layout(
            title="📊 批次良率对比",
            xaxis_title="批次",
            yaxis_title="平均良率 (%)",
            yaxis=dict(range=[96, 100]),
            height=self.chart_config['height'],
            font=dict(size=self.chart_config['font_size']),
            title_font_size=self.chart_config['title_font_size']
        )
        
        return fig
    
    def _create_yield_distribution_chart(self) -> go.Figure:
        """创建良率分布图"""
        fig = go.Figure()
        
        if self.wafer_data is None or self.wafer_data.empty:
            return fig
        
        # 直方图
        fig.add_trace(go.Histogram(
            x=self.wafer_data['Yield_Numeric'],
            nbinsx=20,
            name='良率分布',
            marker_color='skyblue',
            opacity=0.7
        ))
        
        # 添加统计线
        mean_yield = self.wafer_data['Yield_Numeric'].mean()
        std_yield = self.wafer_data['Yield_Numeric'].std()
        
        fig.add_vline(
            x=mean_yield, 
            line_dash="dash", 
            line_color=self.chart_config['mean_line_color'],
            annotation_text=f"平均: {mean_yield:.2f}%"
        )
        fig.add_vline(
            x=mean_yield + std_yield, 
            line_dash="dot", 
            line_color=self.chart_config['std_line_color'],
            annotation_text=f"+1σ: {mean_yield + std_yield:.2f}%"
        )
        fig.add_vline(
            x=mean_yield - std_yield, 
            line_dash="dot", 
            line_color=self.chart_config['std_line_color'],
            annotation_text=f"-1σ: {mean_yield - std_yield:.2f}%"
        )
        
        fig.update_layout(
            title="📊 良率分布直方图",
            xaxis_title="良率 (%)",
            yaxis_title="Wafer数量",
            height=self.chart_config['height'],
            font=dict(size=self.chart_config['font_size']),
            title_font_size=self.chart_config['title_font_size']
        )
        
        return fig
    
    def _create_failure_analysis_chart(self) -> go.Figure:
        """创建失效类型分析图"""
        fig = go.Figure()
        
        if self.wafer_data is None or self.wafer_data.empty:
            return fig
        
        failure_columns = ['Bin3', 'Bin4', 'Bin6', 'Bin7', 'Bin8', 'Bin9']
        failure_totals = self.wafer_data[failure_columns].sum()
        
        # 过滤掉为0的bin
        failure_totals = failure_totals[failure_totals > 0]
        
        if len(failure_totals) == 0:
            # 如果没有失效数据，显示提示
            fig.add_annotation(
                x=0.5, y=0.5,
                text="当前数据无失效芯片",
                showarrow=False,
                font=dict(size=20),
                xref="paper", yref="paper"
            )
        else:
            fig.add_trace(go.Pie(
                labels=failure_totals.index,
                values=failure_totals.values,
                hole=0.4,
                hovertemplate='<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>'
            ))
            
            fig.update_layout(
                annotations=[dict(
                    text='失效分析', 
                    x=0.5, y=0.5, 
                    font_size=20, 
                    showarrow=False
                )]
            )
        
        fig.update_layout(
            title="🔍 失效类型分布",
            height=self.chart_config['height'],
            font=dict(size=self.chart_config['font_size']),
            title_font_size=self.chart_config['title_font_size']
        )
        
        return fig
    
    def _populate_charts_cache(self):
        """
        生成所有图表并存入缓存。
        """
        if self.yield_data is None:
            logger.warning("数据未加载，无法生成图表缓存。")
            return

        self.all_charts_cache = {}  # 清空旧缓存
        
        # 基础图表生成器
        chart_generators = {
            'wafer_trend': self._create_wafer_trend_chart,
            'lot_comparison': self._create_lot_comparison_chart,
            'yield_distribution': self._create_yield_distribution_chart,
            'failure_analysis': self._create_failure_analysis_chart
        }
        
        # 生成基础图表
        for chart_type, generator in chart_generators.items():
            try:
                chart_fig = generator()
                self.all_charts_cache[chart_type] = chart_fig
                logger.info(f"已生成并缓存 {chart_type} 图表")
            except Exception as e:
                logger.error(f"生成 {chart_type} 图表并缓存失败: {e}")
        
        # 生成参数图表
        available_params = self.get_available_parameters()
        for param in available_params:
            chart_type = f"param_{param}"
            try:
                chart_fig = self._create_parameter_line_chart(param)
                self.all_charts_cache[chart_type] = chart_fig
                logger.info(f"已生成并缓存参数 {param} 的折线图")
            except Exception as e:
                logger.error(f"生成参数 {param} 的折线图并缓存失败: {e}")
        
        logger.info(f"已成功缓存 {len(self.all_charts_cache)} 个图表。")

    def get_chart(self, chart_type: str) -> Optional[go.Figure]:
        """
        从缓存中获取指定类型的图表。

        Args:
            chart_type: 图表类型

        Returns:
            Optional[go.Figure]: Plotly图表对象，如果未找到则返回None。
        """
        chart = self.all_charts_cache.get(chart_type)
        if chart is None:
            logger.warning(f"缓存中未找到 {chart_type} 图表。可能需要先加载数据。")
        return chart

    def get_all_cached_charts(self) -> Dict[str, go.Figure]:
        """
        获取所有已缓存的图表。

        Returns:
            Dict[str, go.Figure]: 图表类型 -> 图表对象的字典。
        """
        return self.all_charts_cache

    def generate_all_charts(self) -> Dict[str, go.Figure]:
        """
        确保所有图表已生成并缓存，然后返回缓存的图表。
        
        Returns:
            Dict[str, go.Figure]: 图表类型->图表对象的字典
        """
        if not self.all_charts_cache and self.yield_data is not None:
            logger.info("缓存为空，尝试重新填充图表缓存。")
            self._populate_charts_cache()
        elif self.yield_data is None:
            logger.warning("数据未加载，无法生成图表。")
            return {}
            
        return self.all_charts_cache
    
    def save_chart(self, chart_type: str, output_dir: str = "charts_output") -> Optional[Path]:
        """
        保存指定类型的图表为HTML文件（从缓存获取）。
        
        Args:
            chart_type: 图表类型
            output_dir: 输出目录
            
        Returns:
            Optional[Path]: 保存路径，如果失败则返回None。
        """
        try:
            figure_to_save = self.get_chart(chart_type)
            
            if figure_to_save is None:
                logger.error(f"无法保存图表：未找到 {chart_type} 的缓存图表。")
                return None
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            title = self.generate_chart_title(chart_type)
            filename = f"{title}.html"
            file_path = output_path / filename
            
            figure_to_save.write_html(str(file_path))
            logger.info(f"图表已保存: {file_path}")
            
            return file_path
            
        except Exception as e:
            logger.error(f"保存 {chart_type} 图表失败: {e}")
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

        logger.info(f"开始批量保存 {len(self.all_charts_cache)} 个图表到目录: {output_dir}")

        for chart_type, figure in self.all_charts_cache.items():
            try:
                title = self.generate_chart_title(chart_type)
                filename = f"{title}.html"
                file_path = output_path / filename
                
                figure.write_html(str(file_path))
                logger.info(f"图表 '{chart_type}' 已保存: {file_path}")
                saved_paths.append(file_path)
            except Exception as e:
                logger.error(f"保存 {chart_type} 图表失败: {e}")
        
        logger.info(f"批量保存完成，共成功保存 {len(saved_paths)} 个图表。")
        return saved_paths 