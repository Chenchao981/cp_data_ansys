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

# 导入JavaScript嵌入工具 - 使用兼容的导入方式
def get_embedded_plotly_js():
    """获取嵌入式Plotly.js内容"""
    try:
        # 尝试相对导入
        from .js_embedder import get_embedded_plotly_js as _get_embedded_plotly_js
        return _get_embedded_plotly_js()
    except ImportError:
        try:
            # 尝试绝对导入
            current_dir = Path(__file__).parent
            if str(current_dir) not in sys.path:
                sys.path.append(str(current_dir))
            from js_embedder import get_embedded_plotly_js as _get_embedded_plotly_js
            return _get_embedded_plotly_js()
        except ImportError:
            # 最后回退到CDN
            logger.warning("无法导入JavaScript嵌入工具，使用CDN模式")
            return 'https://unpkg.com/plotly.js@2.26.0/dist/plotly.min.js'

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
        
        logger.info(f"原始数据行数: {len(self.yield_data)}")
        logger.info(f"过滤后wafer数据行数: {len(self.wafer_data)}")
        logger.info(f"原始Lot_ID唯一值: {self.wafer_data['Lot_ID'].unique()}")
        
        # 转换yield为数值
        if 'Yield' in self.wafer_data.columns:
            self.wafer_data['Yield_Numeric'] = self.wafer_data['Yield'].str.rstrip('%').astype(float)
        
        # 改进True_Lot_ID提取逻辑 - 使用策略2以识别更多批次
        def get_true_lot_id(raw_lot_id):
            """提取真实Lot ID - 只去掉@后面的部分，保留更多批次信息"""
            if isinstance(raw_lot_id, str) and '@' in raw_lot_id:
                return raw_lot_id.split('@')[0]
            return raw_lot_id
        
        # 应用函数提取真实Lot ID
        self.wafer_data['True_Lot_ID'] = self.wafer_data['Lot_ID'].apply(get_true_lot_id)
        
        logger.info(f"提取的True_Lot_ID唯一值: {self.wafer_data['True_Lot_ID'].unique()}")
        logger.info(f"每个True_Lot_ID的数据量: {self.wafer_data['True_Lot_ID'].value_counts().to_dict()}")
        
        # 按True_Lot_ID和Wafer_ID排序 - 确保与箱体图相同的排序
        self.wafer_data = self.wafer_data.sort_values(['True_Lot_ID', 'Wafer_ID'])
        
        # 保持Lot_Short用于向后兼容，但现在使用True_Lot_ID
        self.wafer_data['Lot_Short'] = self.wafer_data['True_Lot_ID']
        
        # 计算失效总数
        failure_columns = ['Bin3', 'Bin4', 'Bin6', 'Bin7', 'Bin8', 'Bin9']
        self.wafer_data['Total_Failures'] = self.wafer_data[failure_columns].sum(axis=1)
        
        # 调试信息
        unique_true_lots = self.wafer_data['True_Lot_ID'].unique()
        logger.info(f"预处理完成: {len(self.wafer_data)} 个wafer, {len(unique_true_lots)} 个批次")
        logger.info(f"最终True_Lot_IDs: {list(unique_true_lots)}")
        
        # 检查每个批次的Wafer数量
        for lot_id in unique_true_lots:
            lot_wafers = self.wafer_data[self.wafer_data['True_Lot_ID'] == lot_id]['Wafer_ID'].unique()
            logger.info(f"批次 {lot_id}: {len(lot_wafers)} 个Wafer ({min(lot_wafers)}-{max(lot_wafers)})")
    
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
            
            # 提取信息 - 根据行名称查找，支持多种格式
            unit_row = self.yield_data[self.yield_data.iloc[:, 0] == 'Unit']
            if unit_row.empty:
                unit_row = self.yield_data[self.yield_data.iloc[:, 0] == 'UNIT']
            
            # 支持多种上限格式：LimitU, LIMIT_HIGH
            limitu_row = self.yield_data[self.yield_data.iloc[:, 0] == 'LimitU']
            if limitu_row.empty:
                limitu_row = self.yield_data[self.yield_data.iloc[:, 0] == 'LIMIT_HIGH']
            
            # 支持多种下限格式：LimitL, LIMIT_LOW
            limitl_row = self.yield_data[self.yield_data.iloc[:, 0] == 'LimitL']
            if limitl_row.empty:
                limitl_row = self.yield_data[self.yield_data.iloc[:, 0] == 'LIMIT_LOW']
            
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
        """创建Wafer良率趋势图 - 采用与箱体图相同的X轴布局"""
        fig = go.Figure()
        
        if self.wafer_data is None or self.wafer_data.empty:
            return fig
        
        # 参考boxplot_chart.py的prepare_chart_data方法，生成X轴位置和标签
        chart_data = []
        x_labels = []
        x_position = 0
        lot_positions = {}  # 记录每个Lot在X轴上的位置范围
        
        # 使用Lot_Short作为分组键，确保与箱体图一致
        # 按Lot_Short分组处理，保持与箱体图相同的排序
        for lot_id_val in self.wafer_data['Lot_Short'].unique():
            lot_data = self.wafer_data[self.wafer_data['Lot_Short'] == lot_id_val]
            lot_positions[lot_id_val] = {'start': x_position, 'wafers': []}
            
            # 为每个wafer分配X轴位置 - 修复排序问题
            wafer_ids = lot_data['Wafer_ID'].unique()
            # 将Wafer_ID转换为数值进行排序，然后转回字符串
            try:
                wafer_ids_numeric = [int(w) for w in wafer_ids]
                wafer_ids_sorted = [str(w) for w in sorted(wafer_ids_numeric)]
            except ValueError:
                # 如果转换失败，使用字符串排序
                wafer_ids_sorted = sorted(wafer_ids)
            
            for wafer_id in wafer_ids_sorted:
                wafer_data = lot_data[lot_data['Wafer_ID'] == wafer_id]
                
                # 只取第一行数据，避免重复
                if not wafer_data.empty:
                    row = wafer_data.iloc[0]
                    chart_data.append({
                        'x_position': x_position,
                        'yield_value': row['Yield_Numeric'],
                        'lot_id': lot_id_val,
                        'wafer_id': wafer_id,
                        'x_label': str(wafer_id)
                    })
                
                # 记录wafer信息
                lot_positions[lot_id_val]['wafers'].append({
                    'wafer_id': wafer_id,
                    'x_position': x_position
                })
                
                x_labels.append(str(wafer_id))
                x_position += 1
            
            lot_positions[lot_id_val]['end'] = x_position - 1
        
        chart_df = pd.DataFrame(chart_data)
        logger.info(f"Wafer良率趋势图 - 准备的数据点总数: {len(chart_df)}")
        if chart_df.empty:
            logger.warning("图表数据为空，无法生成趋势图")
            return fig
        
        unique_lots_in_chart_df = chart_df['lot_id'].unique()
        logger.info(f"识别到批次数量: {len(unique_lots_in_chart_df)}, 批次列表: {list(unique_lots_in_chart_df)}")

        # 为每个Lot创建趋势线
        colors = self.chart_config['colors']
        for i, lot_id_val in enumerate(unique_lots_in_chart_df):
            lot_data = chart_df[chart_df['lot_id'] == lot_id_val].copy()
            
            # 按X轴位置排序，确保趋势线正确连接
            lot_data = lot_data.sort_values('x_position')
            
            color = colors[i % len(colors)]
            logger.info(f"正在绘制批次 {lot_id_val}: {len(lot_data)} 个数据点")
            
            if lot_data.empty:
                logger.warning(f"批次 {lot_id_val} 数据为空，跳过绘制")
                continue
            
            nan_yield_count = lot_data['yield_value'].isnull().sum()
            if nan_yield_count > 0:
                logger.warning(f"批次 {lot_id_val} 有 {nan_yield_count} NaN yield_values out of {len(lot_data)} points.")
            if nan_yield_count == len(lot_data) and len(lot_data) > 0:
                logger.warning(f"批次 {lot_id_val} 所有 yield_values 都是 NaN. 趋势线可能不可见。")
            
            min_yield = lot_data['yield_value'].min()
            max_yield = lot_data['yield_value'].max()
            logger.info(f"批次 {lot_id_val}: Yield_Numeric Min={min_yield}, Max={max_yield}. (Fixed Y-axis: [95, 101])")

            if pd.notna(min_yield) and pd.notna(max_yield):
                if not (max_yield >= 95 and min_yield <= 101):
                     logger.warning(f"批次 {lot_id_val} 所有有效 yield_values ({min_yield}, {max_yield}) 似乎超出 Y-axis 范围 [95, 101]。趋势线可能不可见或被剪切。")
            elif nan_yield_count != len(lot_data):
                 logger.error(f"批次 {lot_id_val} 混合 NaN 和有效数据，但 min/max 无法确定。这应该是意外的。")
            
            # 添加趋势线
            fig.add_trace(go.Scatter(
                x=lot_data['x_position'],
                y=lot_data['yield_value'],
                mode='lines+markers',
                name=lot_id_val,
                line=dict(color=color, width=3),
                marker=dict(size=8, symbol='circle', color=color),
                hovertemplate=f'<b>{lot_id_val}</b><br>' +
                             'Wafer: %{customdata[0]}<br>' +
                             '良率: %{y:.2f}%<br>' +
                             '<extra></extra>',
                customdata=[[row['wafer_id']] for _, row in lot_data.iterrows()]
            ))
        
        # 添加平均线
        overall_mean = self.wafer_data['Yield_Numeric'].mean()
        fig.add_hline(
            y=overall_mean, 
            line_dash="dash", 
            line_color=self.chart_config['mean_line_color'],
            annotation_text=f"平均良率: {overall_mean:.2f}%"
        )
        
        # 计算合适的图表宽度 - 确保每个数据点有足够空间
        total_wafers = len(x_labels)
        # 每个wafer分配40像素宽度，最小1200像素
        chart_width = max(1200, total_wafers * 40)
        
        # 参考箱体图的X轴设置方式 - 确保显示所有数据点
        # 计算X轴的实际数据范围，消除两端空白
        x_range_start = -0.5  # 从第一个wafer的左侧0.5个单位开始
        x_range_end = len(x_labels) - 0.5  # 到最后一个wafer的右侧0.5个单位结束
        
        # 添加Lot_ID的二级X轴标签（参考箱体图的annotation实现）
        for lot_id_text, pos_info in lot_positions.items():
            mid_position = (pos_info['start'] + pos_info['end']) / 2
            fig.add_annotation(
                x=mid_position,
                y=-0.15,  # 位置在主X轴下方
                text=str(lot_id_text),
                showarrow=False,
                xref="x",
                yref="paper",
                font=dict(size=10, color="blue")
            )
        
        fig.update_layout(
            title="📈 Wafer良率趋势分析",
            xaxis_title="Wafer编号",
            yaxis_title="良率 (%)",
            yaxis=dict(range=[95, 101]),
            hovermode='x unified',
            # 设置图表尺寸以支持滚动
            width=chart_width,
            height=self.chart_config['height'],
            font=dict(size=self.chart_config['font_size']),
            title_font_size=self.chart_config['title_font_size'],
            # 启用滚动和缩放
            dragmode='pan',  # 默认为平移模式
            # X轴配置 - 完全参考箱体图的样式和设置
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(len(x_labels))),
                ticktext=x_labels,
                tickangle=0,
                title="Wafer编号",
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(211, 211, 211, 0.3)',
                range=[x_range_start, x_range_end],  # 设置X轴显示范围，紧贴数据，确保所有数据点可见
                fixedrange=False,  # 允许X轴缩放和平移
                rangeslider=dict(visible=False)  # 不显示范围滑块
            )
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
        """创建失效类型分析图 - 动态检测yield数据中的Bin列"""
        fig = go.Figure()
        
        if self.wafer_data is None or self.wafer_data.empty:
            logger.warning("❌ wafer_data为空，无法创建失效分析图")
            return fig
        
        logger.info("🔍 开始创建失效类型分析图...")
        logger.info(f"📊 wafer_data列名: {list(self.wafer_data.columns)}")
        
        # 动态检测所有Bin列（除了Bin1 = Pass）
        bin_columns = [col for col in self.wafer_data.columns if col.startswith('Bin') and col != 'Bin1']
        logger.info(f"🎯 检测到的失效Bin列: {bin_columns}")
        
        if not bin_columns:
            logger.warning("⚠️ 未找到失效Bin列，尝试其他格式...")
            # 尝试检测其他可能的列名格式
            bin_columns = [col for col in self.wafer_data.columns 
                          if col.lower().startswith('bin') and col.lower() != 'bin1']
            logger.info(f"🔄 其他格式的Bin列: {bin_columns}")
        
        if not bin_columns:
            logger.warning("⚠️ 仍未找到失效Bin列，显示无失效数据提示")
            # 如果没有失效数据，显示提示
            fig.add_annotation(
                x=0.5, y=0.5,
                text="当前数据无失效芯片或Bin数据",
                showarrow=False,
                font=dict(size=20),
                xref="paper", yref="paper"
            )
        else:
            try:
                # 计算各失效类型的总数
                failure_totals = self.wafer_data[bin_columns].sum()
                logger.info(f"📈 失效统计: {failure_totals.to_dict()}")
                
                # 过滤掉为0的bin
                failure_totals = failure_totals[failure_totals > 0]
                
                if len(failure_totals) == 0:
                    logger.info("ℹ️ 所有失效Bin数值为0，显示无失效提示")
                    fig.add_annotation(
                        x=0.5, y=0.5,
                        text="当前数据无失效芯片",
                        showarrow=False,
                        font=dict(size=20),
                        xref="paper", yref="paper"
                    )
                else:
                    logger.info(f"🥧 生成失效分析饼图，包含 {len(failure_totals)} 种失效类型")
                    
                    # 创建饼图
                    fig.add_trace(go.Pie(
                        labels=failure_totals.index,
                        values=failure_totals.values,
                        hole=0.4,
                        hovertemplate='<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>',
                        textinfo='label+percent',
                        textposition='auto'
                    ))
                    
                    # 添加中心文字
                    fig.update_layout(
                        annotations=[dict(
                            text='失效分析', 
                            x=0.5, y=0.5, 
                            font_size=20, 
                            showarrow=False
                        )]
                    )
                    
                    logger.info("✅ 失效分析饼图创建成功")
                    
            except Exception as e:
                logger.error(f"❌ 创建失效分析饼图时出错: {e}")
                fig.add_annotation(
                    x=0.5, y=0.5,
                    text=f"失效分析数据处理错误: {str(e)}",
                    showarrow=False,
                    font=dict(size=14),
                    xref="paper", yref="paper"
                )
        
        fig.update_layout(
            title="🔍 失效类型分布",
            height=self.chart_config['height'],
            font=dict(size=self.chart_config['font_size']),
            title_font_size=self.chart_config['title_font_size']
        )
        
        return fig
    
    def _populate_charts_cache(self):
        """填充图表缓存"""
        if self.yield_data is None:
            logger.error("数据未加载，无法生成图表。")
            return
        
        # 性能优化：减少详细日志，只显示开始信息
        chart_types = ['wafer_trend', 'lot_comparison', 'failure_analysis']
        logger.info(f"开始生成 {len(chart_types)} 个良率图表...")
        
        success_count = 0
        for chart_type in chart_types:
            try:
                if chart_type == 'wafer_trend':
                    self.all_charts_cache[chart_type] = self._create_wafer_trend_chart()
                elif chart_type == 'lot_comparison':
                    self.all_charts_cache[chart_type] = self._create_lot_comparison_chart()
                elif chart_type == 'failure_analysis':
                    self.all_charts_cache[chart_type] = self._create_failure_analysis_chart()
                success_count += 1
            except Exception as e:
                logger.error(f"生成 {chart_type} 图表失败: {e}")
        
        # 性能优化：只输出摘要信息
        logger.info(f"良率图表生成完成: {success_count}/{len(chart_types)} 个成功")

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
            
            # 使用本地嵌入的Plotly.js，避免CDN加载失败
            figure_to_save.write_html(
                str(file_path),
                include_plotlyjs=get_embedded_plotly_js(),
                validate=False  # 跳过验证，提升速度
            )
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

        # 性能优化：减少详细日志，只显示开始和结束
        logger.info(f"开始批量保存 {len(self.all_charts_cache)} 个良率图表...")

        success_count = 0
        for chart_type, figure in self.all_charts_cache.items():
            try:
                title = self.generate_chart_title(chart_type)
                filename = f"{title}.html"
                file_path = output_path / filename
                
                # 使用本地嵌入的Plotly.js，避免CDN加载失败
                figure.write_html(
                    str(file_path),
                    include_plotlyjs=get_embedded_plotly_js(),
                    validate=False  # 跳过验证，提升速度
                )
                saved_paths.append(file_path)
                success_count += 1
            except Exception as e:
                logger.error(f"保存 {chart_type} 图表失败: {e}")
        
        # 性能优化：只输出摘要信息
        logger.info(f"良率图表保存完成: {success_count}/{len(self.all_charts_cache)} 个成功")
        return saved_paths 