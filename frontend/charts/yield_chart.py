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
        # 移除spec_data和cleaned_data，不再需要
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
        }
        
        # 支持的图表类型 - 只保留3个核心图表
        self.chart_types = [
            'wafer_trend',      # Wafer良率趋势图
            'lot_comparison',   # 批次对比图  
            'failure_analysis'  # 失效类型分析饼图
        ]
        
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
            
            # 数据预处理
            self._preprocess_data()
            
            # 数据加载成功后，预生成并缓存所有图表
            self._populate_charts_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"数据加载或图表预生成失败: {e}")
            self.yield_data = None
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
        
        # 提取批次简称（通用方式处理各种批次格式）
        # 方案1：直接使用Lot_ID作为批次名称（最简单可靠）
        self.wafer_data['Lot_Short'] = self.wafer_data['Lot_ID']
        
        # 方案2：如果需要简化显示，可以提取批次的核心部分（去掉后缀）
        # 例如：FA55-4307-327A-250501@203 -> FA55-4307-327A-250501
        # 或者：C11200-325A-250502@203 -> C11200-325A-250502
        # self.wafer_data['Lot_Short'] = self.wafer_data['Lot_ID'].str.split('@').str[0]
        
        # 计算失效总数
        failure_columns = ['Bin3', 'Bin4', 'Bin6', 'Bin7', 'Bin8', 'Bin9']
        self.wafer_data['Total_Failures'] = self.wafer_data[failure_columns].sum(axis=1)
        
        logger.info(f"预处理完成: {len(self.wafer_data)} 个wafer, {self.wafer_data['Lot_Short'].nunique()} 个批次")
    
    def get_available_chart_types(self) -> List[str]:
        """
        获取可用的图表类型列表
        
        Returns:
            List[str]: 图表类型列表
        """
        return self.chart_types.copy()
    
    def get_available_parameters(self) -> List[str]:
        """
        获取可用的测试参数列表
        
        Returns:
            List[str]: 参数列表
        """
        if self.yield_data is None:
            return []
        
        exclude_cols = ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y']
        params = [col for col in self.yield_data.columns if col not in exclude_cols]
        
        return params
    
    def get_parameter_info(self, parameter: str) -> Dict:
        """
        获取参数的详细信息（单位、上下限、测试条件）
        
        Args:
            parameter: 参数名
            
        Returns:
            Dict: 参数信息字典
        """
        if self.yield_data is None:
            return {}
        
        try:
            if parameter not in self.yield_data.columns:
                logger.warning(f"参数 {parameter} 不在yield数据中")
                return {}
            
            # 提取信息 - 根据行名称查找
            unit_row = self.yield_data[self.yield_data.iloc[:, 0] == 'Unit']
            limitu_row = self.yield_data[self.yield_data.iloc[:, 0] == 'LimitU']
            limitl_row = self.yield_data[self.yield_data.iloc[:, 0] == 'LimitL']
            testcond_row = self.yield_data[self.yield_data.iloc[:, 0] == 'TestCond:']
            
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
        # 处理基础图表类型
        title_map = {
            'wafer_trend': 'Wafer良率趋势分析_yield_chart',
            'lot_comparison': '批次良率对比分析_yield_chart',
            'failure_analysis': '失效类型分析_yield_chart'
        }
        
        return title_map.get(chart_type, f'{chart_type}_yield_chart')
    
    def _create_wafer_trend_chart(self) -> go.Figure:
        """创建Wafer良率趋势图"""
        fig = go.Figure()
        
        if self.wafer_data is None or self.wafer_data.empty:
            return fig
        
        lots = self.wafer_data['Lot_Short'].unique()
        colors = self.chart_config['colors']
        
        for i, lot in enumerate(lots):
            lot_data = self.wafer_data[self.wafer_data['Lot_Short'] == lot].copy()
            
            # 将Wafer_ID转换为数值类型，用于X轴定位
            lot_data['Wafer_Num'] = pd.to_numeric(lot_data['Wafer_ID'], errors='coerce')
            
            # 过滤掉无法转换的数据并按Wafer编号排序
            lot_data = lot_data.dropna(subset=['Wafer_Num']).sort_values('Wafer_Num')
            
            if not lot_data.empty:
                fig.add_trace(go.Scatter(
                    x=lot_data['Wafer_Num'],  # 使用数值化的Wafer编号
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
            xaxis=dict(
                range=[0.5, 25.5],  # 固定X轴范围为1~25
                tick0=1,            # 起始刻度
                dtick=1,            # 刻度间隔
                tickmode='linear'   # 线性刻度模式
            ),
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
        
        # 为每个批次创建单独的柱状图trace，以便显示图例
        for i, row in lot_stats.iterrows():
            fig.add_trace(go.Bar(
                x=[i+1],  # 使用数字索引作为X轴位置
                y=[row['mean']],
                error_y=dict(type='data', array=[row['std']]),
                name=row['Lot_Short'],  # 批次名称作为图例
                marker_color=colors[i % len(colors)],
                hovertemplate=f'<b>{row["Lot_Short"]}</b><br>平均良率: %{{y:.2f}}%<br>标准差: {row["std"]:.2f}%<br>Wafer数: {int(row["count"])}<extra></extra>',
                showlegend=True  # 显示图例
            ))
            
            # 添加数据标签
            fig.add_annotation(
                x=i+1,
                y=row['mean'] + row['std'] + 0.2,
                text=f"{row['mean']:.2f}%<br>({int(row['count'])} wafers)",
                showarrow=False,
                font=dict(size=self.chart_config['font_size'])
            )
        
        fig.update_layout(
            title="📊 批次良率对比",
            xaxis_title="批次序号",
            yaxis_title="平均良率 (%)",
            xaxis=dict(
                showticklabels=False,  # 隐藏X轴刻度标签
                range=[0.5, len(lot_stats) + 0.5]  # 设置X轴范围
            ),
            yaxis=dict(range=[96, 100]),
            height=self.chart_config['height'],
            font=dict(size=self.chart_config['font_size']),
            title_font_size=self.chart_config['title_font_size'],
            legend=dict(
                orientation="v",  # 垂直图例
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
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
        
        # 基础图表生成器 - 只保留3个核心图表
        chart_generators = {
            'wafer_trend': self._create_wafer_trend_chart,
            'lot_comparison': self._create_lot_comparison_chart,
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