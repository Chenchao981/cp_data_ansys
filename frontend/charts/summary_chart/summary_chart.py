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
            logger.info(f"📁 在目录 {self.data_dir} 中搜索yield文件...")
            logger.info(f"🔍 找到的yield文件: {[f.name for f in yield_files]}")
            
            if not yield_files:
                # 列出目录中的所有CSV文件以供调试
                all_csv_files = list(self.data_dir.glob("*.csv"))
                logger.error(f"❌ 未找到yield数据文件")
                logger.error(f"📄 目录中的所有CSV文件: {[f.name for f in all_csv_files]}")
                return False
            
            # 使用第一个找到的yield文件
            yield_file = yield_files[0]
            logger.info(f"📊 加载良率数据文件: {yield_file.name}")
            
            # 读取yield数据
            self.yield_data = pd.read_csv(yield_file)
            logger.info(f"📋 yield文件列名: {list(self.yield_data.columns)}")
            logger.info(f"📈 yield文件数据形状: {self.yield_data.shape}")
            
            # 检查必要的列是否存在
            required_cols = ['Wafer_ID']
            missing_cols = [col for col in required_cols if col not in self.yield_data.columns]
            if missing_cols:
                logger.error(f"❌ yield文件缺少必要列: {missing_cols}")
                return False
            
            # 数据预处理
            self._preprocess_yield_data()
            
            logger.info(f"✅ 良率数据加载成功，共 {len(self.yield_data)} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"❌ 加载良率数据失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    def _preprocess_yield_data(self):
        """预处理良率数据"""
        if self.yield_data is None:
            return
        
        logger.info(f"🔄 开始预处理良率数据...")
        logger.info(f"📊 原始数据列: {list(self.yield_data.columns)}")
        
        # 检查是否有Lot_ID列，如果没有则尝试从其他列推断
        if 'Lot_ID' not in self.yield_data.columns:
            logger.warning("⚠️ yield数据中没有Lot_ID列，尝试推断...")
            
            # 方法1：从Product_Name列中提取Lot_ID
            if 'Product_Name' in self.yield_data.columns:
                # 假设Product_Name包含完整的批次信息
                logger.info("📦 尝试从Product_Name列提取Lot_ID...")
                # 这里可以根据实际数据格式调整
                self.yield_data['Lot_ID'] = self.yield_data['Product_Name']
            else:
                # 方法2：创建一个默认的Lot_ID
                logger.info("🏷️ 创建默认的Lot_ID...")
                self.yield_data['Lot_ID'] = 'Unknown_Lot'
        
        # 过滤掉汇总行
        if 'Lot_ID' in self.yield_data.columns:
            original_len = len(self.yield_data)
            self.yield_data = self.yield_data[self.yield_data['Lot_ID'] != 'ALL'].copy()
            self.yield_data = self.yield_data[self.yield_data['Wafer_ID'] != 'ALL'].copy()
            self.yield_data = self.yield_data[self.yield_data['Wafer_ID'] != 'Total'].copy()
            filtered_len = len(self.yield_data)
            logger.info(f"🗂️ 过滤汇总行: {original_len} -> {filtered_len} 条记录")
        
        # 转换良率为数值格式
        if 'Yield' in self.yield_data.columns:
            logger.info("📈 转换Yield列为数值格式...")
            self.yield_data['Yield_Numeric'] = self.yield_data['Yield'].str.rstrip('%').astype(float)
        elif 'Yield_Rate' in self.yield_data.columns:
            logger.info("📈 使用Yield_Rate列...")
            self.yield_data['Yield_Numeric'] = self.yield_data['Yield_Rate']
        else:
            logger.warning("⚠️ 未找到良率列，使用默认值100%")
            self.yield_data['Yield_Numeric'] = 100.0
        
        # 确保Wafer_ID是字符串格式
        if 'Wafer_ID' in self.yield_data.columns:
            self.yield_data['Wafer_ID'] = self.yield_data['Wafer_ID'].astype(str)
        
        # 提取真实的Lot_ID（去掉@后缀）
        def get_true_lot_id(raw_lot_id):
            if isinstance(raw_lot_id, str) and '@' in raw_lot_id:
                return raw_lot_id.split('@')[0]
            return raw_lot_id
        
        if 'Lot_ID' in self.yield_data.columns:
            self.yield_data['Lot_Short'] = self.yield_data['Lot_ID'].apply(get_true_lot_id)
            
            # 按Lot_Short和Wafer_ID排序
            self.yield_data = self.yield_data.sort_values(['Lot_Short', 'Wafer_ID']).reset_index(drop=True)
            
            unique_lots = self.yield_data['Lot_Short'].nunique()
            unique_wafers = self.yield_data['Wafer_ID'].nunique()
            logger.info(f"✅ 良率数据预处理完成，识别到 {unique_lots} 个批次，{unique_wafers} 个晶圆")
        else:
            logger.warning("⚠️ 无法处理Lot_ID信息")
    
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
        try:
            logger.info("🎨 开始创建合并图表...")
            
            if self.boxplot_chart.cleaned_data is None:
                logger.error("❌ 箱体图数据未加载，无法创建合并图表")
                return go.Figure()
            
            if self.yield_data is None:
                logger.error("❌ 良率数据未加载，无法创建合并图表")
                return go.Figure()
            
            # 获取所有可用参数
            parameters = self.get_available_parameters()
            if not parameters:
                logger.error("❌ 没有可用的测试参数")
                return go.Figure()
            
            logger.info(f"📊 开始创建包含良率图和 {len(parameters)} 个参数的合并图表")
            logger.info(f"🎯 可用参数列表: {parameters}")
            
            # 创建子图布局 - 第一行为良率图，后续行为参数箱体图
            subplot_titles = ["📊 批次良率对比"]  # 良率图标题
            
            # 添加参数图标题
            logger.info("🏷️ 生成子图标题...")
            try:
                for param in parameters:
                    param_info = self.boxplot_chart.get_parameter_info(param)
                    unit_str = f" [{param_info.get('unit', '')}]" if param_info.get('unit') else ""
                    test_cond = f" @{param_info.get('test_condition', '')}" if param_info.get('test_condition') else ""
                    subplot_titles.append(f"{param}{unit_str}{test_cond}")
            except Exception as e:
                logger.error(f"❌ 生成子图标题时出错: {e}")
                # 使用简化标题
                for param in parameters:
                    subplot_titles.append(f"{param}")
            
            # 总行数 = 1（良率图）+ len(parameters)（参数图）
            total_rows = 1 + len(parameters)
            logger.info(f"📏 子图布局: {total_rows} 行 x 1 列")
            
            # 创建子图布局
            logger.info("🔧 创建Plotly子图布局...")
            try:
                fig = make_subplots(
                    rows=total_rows,
                    cols=1,
                    shared_xaxes=False,  # 不共享X轴，让每个子图都能显示自己的X轴标签
                    vertical_spacing=self.summary_config['subplot_spacing'],
                    subplot_titles=subplot_titles,
                    specs=[[{"secondary_y": False}] for _ in range(total_rows)]  # 每个子图的规格
                )
                logger.info("✅ 子图布局创建成功")
            except Exception as e:
                logger.error(f"❌ 创建子图布局失败: {e}")
                return go.Figure()
            
            # 第一步：添加良率对比图（第1行）
            logger.info("📈 添加良率对比图...")
            try:
                x_labels, lot_positions = self._add_yield_comparison_chart(fig, row=1)
                logger.info(f"✅ 良率图添加成功，X轴标签数: {len(x_labels) if x_labels else 0}")
            except Exception as e:
                logger.error(f"❌ 添加良率图失败: {e}")
                x_labels, lot_positions = [], {}
            
            # 第二步：为每个参数生成箱体图数据并添加到对应的子图（从第2行开始）
            logger.info("📦 开始添加参数箱体图...")
            successful_params = 0
            
            for i, param in enumerate(parameters, 2):  # 从第2行开始
                try:
                    logger.info(f"🔄 处理参数 {param} (第{i-1}/{len(parameters)}个)...")
                    
                    # 复用BoxplotChart的数据准备逻辑
                    chart_data, current_x_labels, param_info, current_lot_positions = self.boxplot_chart.prepare_chart_data(param)
                    
                    # 确保X轴标签和批次位置与良率图一致
                    if x_labels is None:
                        x_labels = current_x_labels
                        lot_positions = current_lot_positions
                    
                    if chart_data.empty:
                        logger.warning(f"⚠️ 参数 {param} 没有有效数据，添加空数据提示")
                        # 添加空数据提示
                        try:
                            fig.add_annotation(
                                text=f"参数 {param} 没有有效数据",
                                xref="paper", yref=f"y{i}",
                                x=0.5, y=0.5, showarrow=False,
                                font=dict(size=12),
                                row=i, col=1
                            )
                        except Exception as e:
                            logger.error(f"❌ 添加空数据提示失败: {e}")
                        continue
                    
                    logger.info(f"📊 参数 {param} 数据准备完成，数据量: {len(chart_data)}")
                    
                    # 添加箱体图和散点图到当前子图
                    self._add_parameter_traces(fig, chart_data, param_info, i)
                    
                    # 添加上下限线
                    self._add_limit_lines(fig, param_info, i)
                    
                    successful_params += 1
                    logger.info(f"✅ 参数 {param} 处理完成")
                    
                except Exception as e:
                    logger.error(f"❌ 处理参数 {param} 时出错: {e}")
                    import traceback
                    logger.error(f"详细错误: {traceback.format_exc()}")
                    continue
            
            logger.info(f"📊 参数处理完成: {successful_params}/{len(parameters)} 个参数成功")
            
            # 设置整体布局
            logger.info("🎨 配置整体布局...")
            try:
                self._configure_layout(fig, parameters, x_labels, lot_positions)
                logger.info("✅ 布局配置完成")
            except Exception as e:
                logger.error(f"❌ 配置布局失败: {e}")
                # 继续使用基本布局
            
            logger.info(f"🎉 合并图表创建完成！包含良率图和 {successful_params} 个参数")
            return fig
            
        except Exception as e:
            logger.error(f"❌ 创建合并图表过程中出现严重错误: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return go.Figure()
    
    def _add_yield_comparison_chart(self, fig: go.Figure, row: int) -> Tuple[List[str], Dict]:
        """
        添加Wafer良率趋势图到指定行 - 使用Lion公司的改进版本
        
        Args:
            fig: Plotly图表对象
            row: 子图行号
            
        Returns:
            Tuple[List[str], Dict]: X轴标签和批次位置信息
        """
        try:
            logger.info("📈 开始添加良率对比图...")
            
            if self.yield_data is None or self.yield_data.empty:
                logger.warning("⚠️ 良率数据为空，无法生成良率趋势图")
                return [], {}
            
            logger.info(f"📊 良率数据状态: {len(self.yield_data)} 行数据")
            logger.info(f"📋 良率数据列: {list(self.yield_data.columns)}")
        except Exception as e:
            logger.error(f"❌ 良率图初始检查失败: {e}")
            return [], {}
        
        try:
            # 预处理数据 - 确保数据格式正确
            logger.info("🔄 预处理良率数据...")
            yield_data = self.yield_data.copy()
            
            # 转换yield为数值（去掉百分号等）
            logger.info("📊 检查和转换良率数值...")
            if 'Yield' in yield_data.columns:
                logger.info("📈 找到Yield列，转换为数值格式...")
                try:
                    if 'Yield_Numeric' not in yield_data.columns:
                        yield_data['Yield_Numeric'] = yield_data['Yield'].astype(str).str.rstrip('%').astype(float)
                    logger.info("✅ Yield列转换成功")
                except Exception as e:
                    logger.error(f"❌ Yield列转换失败: {e}")
                    yield_data['Yield_Numeric'] = 100.0  # 使用默认值
            elif 'Yield_Rate' in yield_data.columns:
                logger.info("📈 找到Yield_Rate列，直接使用...")
                yield_data['Yield_Numeric'] = yield_data['Yield_Rate']
            else:
                logger.warning("⚠️ 未找到良率数据列，使用默认值100%")
                yield_data['Yield_Numeric'] = 100.0
            
            # 过滤掉汇总行
            logger.info("🗂️ 过滤汇总行...")
            original_len = len(yield_data)
            if 'Lot_ID' in yield_data.columns:
                yield_data = yield_data[yield_data['Lot_ID'] != 'ALL'].copy()
            if 'Wafer_ID' in yield_data.columns:
                yield_data = yield_data[yield_data['Wafer_ID'] != 'ALL'].copy()
                yield_data = yield_data[yield_data['Wafer_ID'] != 'Total'].copy()
            logger.info(f"📊 过滤后数据: {original_len} -> {len(yield_data)} 行")
            
            if yield_data.empty:
                logger.warning("⚠️ 过滤后的良率数据为空")
                return [], {}
            
            # 按Lot_ID和Wafer_ID排序
            logger.info("🔄 排序良率数据...")
            if 'Wafer_ID' in yield_data.columns:
                try:
                    # 确保Wafer_ID为数值类型进行正确排序
                    yield_data['Wafer_ID_Numeric'] = pd.to_numeric(yield_data['Wafer_ID'], errors='coerce')
                    if 'Lot_ID' in yield_data.columns:
                        yield_data = yield_data.sort_values(['Lot_ID', 'Wafer_ID_Numeric'])
                    else:
                        yield_data = yield_data.sort_values(['Wafer_ID_Numeric'])
                    logger.info("✅ 数据排序成功（数值型）")
                except Exception as e:
                    logger.warning(f"⚠️ 数值排序失败，使用字符串排序: {e}")
                    # 如果转换失败，使用字符串排序
                    if 'Lot_ID' in yield_data.columns:
                        yield_data = yield_data.sort_values(['Lot_ID', 'Wafer_ID'])
                    else:
                        yield_data = yield_data.sort_values(['Wafer_ID'])
            
            logger.info(f"✅ 良率数据预处理完成: {len(yield_data)} 个晶圆")
            
            # 检查数值范围
            try:
                min_yield = yield_data['Yield_Numeric'].min()
                max_yield = yield_data['Yield_Numeric'].max()
                logger.info(f"📊 良率范围: {min_yield:.2f}% - {max_yield:.2f}%")
            except Exception as e:
                logger.warning(f"⚠️ 无法计算良率范围: {e}")
            
            # 按批次分组数据
            logger.info("📊 按批次分组数据...")
            try:
                if 'Lot_ID' in yield_data.columns:
                    lot_groups = dict(list(yield_data.groupby('Lot_ID')))
                    logger.info(f"📦 找到 {len(lot_groups)} 个批次: {list(lot_groups.keys())}")
                else:
                    lot_groups = {'Unknown': yield_data}
                    logger.info("📦 使用默认批次名称")
            except Exception as e:
                logger.error(f"❌ 批次分组失败: {e}")
                lot_groups = {'Unknown': yield_data}
            
            # 简化良率图绘制 - 避免复杂的处理导致错误
            logger.info("🎨 绘制简化良率图...")
            
            # 定义批次颜色
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
            
            x_position = 1
            x_labels = []
            lot_positions = {}
            
            try:
                for i, (lot_id, lot_data) in enumerate(lot_groups.items()):
                    logger.info(f"🔄 处理批次 {lot_id}: {len(lot_data)} 个晶圆")
                    color = colors[i % len(colors)]
                    
                    # 简化处理 - 直接按顺序绘制每个wafer
                    lot_x_positions = []
                    lot_yields = []
                    lot_wafer_ids = []
                    
                    for _, wafer_row in lot_data.iterrows():
                        wafer_id = wafer_row.get('Wafer_ID', f'W{x_position}')
                        yield_value = wafer_row.get('Yield_Numeric', 100.0)
                        
                        x_labels.append(str(wafer_id))
                        lot_x_positions.append(x_position)
                        lot_yields.append(yield_value)
                        lot_wafer_ids.append(wafer_id)
                        
                        x_position += 1
                    
                    # 记录批次位置
                    lot_positions[lot_id] = {
                        'start': lot_x_positions[0] if lot_x_positions else x_position,
                        'end': lot_x_positions[-1] if lot_x_positions else x_position,
                        'wafers': [{'wafer_id': wid, 'x_position': xpos} 
                                 for wid, xpos in zip(lot_wafer_ids, lot_x_positions)]
                    }
                    
                    # 添加良率趋势线
                    if lot_x_positions and lot_yields:
                        try:
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
                            logger.info(f"✅ 批次 {lot_id} 趋势线添加成功")
                        except Exception as e:
                            logger.error(f"❌ 添加批次 {lot_id} 趋势线失败: {e}")
                
                # 添加平均线
                try:
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
                        logger.info(f"✅ 平均线添加成功: {overall_mean:.2f}%")
                except Exception as e:
                    logger.warning(f"⚠️ 添加平均线失败: {e}")
                
                logger.info(f"🎉 良率图创建完成，共 {len(x_labels)} 个wafer位置")
                return x_labels, lot_positions
                
            except Exception as e:
                logger.error(f"❌ 绘制良率图失败: {e}")
                import traceback
                logger.error(f"详细错误: {traceback.format_exc()}")
                return [], {}
                
        except Exception as e:
            logger.error(f"❌ 良率图处理过程中出现严重错误: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return [], {}
    
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
            logger.info(f"🎨 开始创建汇总图表...")
            
            # 检查数据状态
            if self.boxplot_chart.cleaned_data is None:
                logger.error("❌ 箱体图数据未加载")
                return None
                
            if self.yield_data is None:
                logger.error("❌ 良率数据未加载")
                return None
            
            logger.info(f"📊 数据状态检查通过:")
            logger.info(f"   - 箱体图数据: {len(self.boxplot_chart.cleaned_data)} 行")
            logger.info(f"   - 良率数据: {len(self.yield_data)} 行")
            
            # 检查可用参数
            available_params = self.get_available_parameters()
            logger.info(f"🎯 可用参数: {len(available_params)} 个 - {available_params}")
            
            # 创建合并图表
            fig = self.create_combined_chart()
            
            if fig.data is None or len(fig.data) == 0:
                logger.error("❌ 无法保存图表：合并图表为空")
                logger.error("可能的原因:")
                logger.error("  1. 数据预处理失败")
                logger.error("  2. 参数提取失败") 
                logger.error("  3. 图表创建过程中出现异常")
                return None
            
            logger.info(f"✅ 图表创建成功，包含 {len(fig.data)} 个数据轨迹")
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            dataset_name = self._extract_dataset_name()
            filename = f"{dataset_name}_summary_chart.html"
            file_path = output_path / filename
            
            logger.info(f"💾 正在保存图表到: {file_path}")
            
            # 保存HTML文件 - 使用本地嵌入的Plotly.js，避免CDN加载失败
            fig.write_html(
                str(file_path),
                include_plotlyjs=get_embedded_plotly_js(),
                validate=False
            )
            
            logger.info(f"🎉 汇总图表已成功保存: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"❌ 保存汇总图表失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
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