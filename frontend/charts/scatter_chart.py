#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
散点图模块 - 基于BaseChart架构
用于参数关联分析，显示两个或多个参数之间的相关性
支持规格限制可视化和数据点状态标示
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import Optional, List, Tuple, Dict, Any
import seaborn as sns
from scipy import stats
import logging

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from frontend.charts.base_chart import BaseChart

logger = logging.getLogger(__name__)

class ScatterChart(BaseChart):
    """散点图类 - 专门用于参数关联分析"""
    
    def __init__(self, data_manager, lot_id: Optional[str] = None, 
                 x_param: str = None, y_param: str = None, **params):
        """
        初始化散点图
        
        Args:
            data_manager: 数据管理器实例
            lot_id (str): 批次ID
            x_param (str): X轴参数名
            y_param (str): Y轴参数名
            **params: 其他图表参数
        """
        super().__init__(data_manager, lot_id, **params)
        
        self.x_param = x_param
        self.y_param = y_param
        
        # 散点图特有配置
        self.point_size = params.get('point_size', 30)
        self.point_alpha = params.get('point_alpha', 0.7)
        self.show_spec_limits = params.get('show_spec_limits', True)
        self.show_trend_line = params.get('show_trend_line', True)
        self.show_correlation = params.get('show_correlation', True)
        
        # 颜色配置
        self.colors = {
            'pass': '#2E8B57',      # 合格点：海绿色
            'fail': '#DC143C',      # 不合格点：深红色
            'spec_area': '#87CEEB', # 规格区域：天蓝色
            'trend_line': '#FF6347' # 趋势线：番茄色
        }
        
        logger.info(f"ScatterChart初始化 - 批次: {lot_id}, X: {x_param}, Y: {y_param}")
    
    def load_required_data(self) -> bool:
        """加载散点图所需的数据"""
        try:
            # 加载cleaned数据
            cleaned_data = self.data_manager.get_data('cleaned', self.lot_id)
            if cleaned_data is None:
                logger.error(f"无法加载cleaned数据 - 批次: {self.lot_id}")
                return False
            
            self.data['cleaned'] = cleaned_data
            logger.info(f"已加载cleaned数据: {cleaned_data.shape}")
            
            # 加载spec规格数据（可选）
            try:
                spec_data = self.data_manager.get_data('spec', self.lot_id)
                if spec_data is not None:
                    self.data['spec'] = spec_data
                    logger.info(f"已加载spec数据: {spec_data.shape}")
                else:
                    logger.warning("未找到spec数据，将不显示规格限制")
            except Exception as e:
                logger.warning(f"加载spec数据失败: {e}")
            
            # 自动选择参数（如果未指定）
            if not self.x_param or not self.y_param:
                self._auto_select_parameters()
            
            return True
            
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            return False
    
    def _auto_select_parameters(self):
        """自动选择合适的X和Y参数"""
        cleaned_data = self.data['cleaned']
        
        # 获取数值型列
        numeric_columns = cleaned_data.select_dtypes(include=[np.number]).columns.tolist()
        
        # 排除坐标列
        excluded_cols = ['DieX', 'DieY', 'X', 'Y', 'x', 'y', 'WaferID', 'LotID']
        numeric_columns = [col for col in numeric_columns 
                          if not any(excl.lower() in col.lower() for excl in excluded_cols)]
        
        if len(numeric_columns) >= 2:
            if not self.x_param:
                self.x_param = numeric_columns[0]
            if not self.y_param:
                self.y_param = numeric_columns[1] if numeric_columns[1] != self.x_param else numeric_columns[0]
        
        logger.info(f"自动选择参数 - X: {self.x_param}, Y: {self.y_param}")
    
    def get_available_parameters(self) -> List[str]:
        """获取可用的参数列表"""
        if 'cleaned' not in self.data:
            return []
        
        cleaned_data = self.data['cleaned']
        numeric_columns = cleaned_data.select_dtypes(include=[np.number]).columns.tolist()
        
        # 排除坐标列
        excluded_cols = ['DieX', 'DieY', 'X', 'Y', 'x', 'y', 'WaferID', 'LotID']
        filtered_columns = [col for col in numeric_columns 
                           if not any(excl.lower() in col.lower() for excl in excluded_cols)]
        
        return filtered_columns
    
    def generate(self) -> bool:
        """生成散点图"""
        try:
            # 加载数据
            if not self.load_required_data():
                return False
            
            # 验证参数
            if not self._validate_parameters():
                return False
            
            # 创建图表画布
            fig, ax = self._create_figure()
            
            # 准备数据
            plot_data = self._prepare_plot_data()
            if plot_data is None:
                return False
            
            # 绘制规格限制区域（如果有spec数据）
            if self.show_spec_limits and 'spec' in self.data:
                self._draw_spec_limits(ax)
            
            # 绘制散点图
            self._draw_scatter_points(ax, plot_data)
            
            # 绘制趋势线（可选）
            if self.show_trend_line:
                self._draw_trend_line(ax, plot_data)
            
            # 添加相关性信息（可选）
            if self.show_correlation:
                self._add_correlation_info(ax, plot_data)
            
            # 设置标题和标签
            self._add_title_and_labels(
                title=f'参数关联分析: {self.x_param} vs {self.y_param}',
                xlabel=f'{self.x_param}',
                ylabel=f'{self.y_param}'
            )
            
            # 添加图例
            self._add_custom_legend(ax)
            
            # 应用通用样式
            self._add_grid()
            self._format_axes()
            
            logger.info("散点图生成成功")
            return True
            
        except Exception as e:
            logger.error(f"生成散点图失败: {e}")
            return False
    
    def _validate_parameters(self) -> bool:
        """验证参数有效性"""
        if not self.x_param or not self.y_param:
            logger.error("X轴或Y轴参数未指定")
            return False
        
        cleaned_data = self.data['cleaned']
        
        if self.x_param not in cleaned_data.columns:
            logger.error(f"X轴参数 '{self.x_param}' 不存在于数据中")
            return False
        
        if self.y_param not in cleaned_data.columns:
            logger.error(f"Y轴参数 '{self.y_param}' 不存在于数据中")
            return False
        
        return True
    
    def _prepare_plot_data(self) -> Optional[pd.DataFrame]:
        """准备绘图数据"""
        try:
            cleaned_data = self.data['cleaned'].copy()
            
            # 提取X和Y数据
            x_data = pd.to_numeric(cleaned_data[self.x_param], errors='coerce')
            y_data = pd.to_numeric(cleaned_data[self.y_param], errors='coerce')
            
            # 创建绘图数据框
            plot_data = pd.DataFrame({
                'x': x_data,
                'y': y_data
            })
            
            # 移除缺失值
            plot_data = plot_data.dropna()
            
            if len(plot_data) == 0:
                logger.error("没有有效的数据点")
                return None
            
            # 添加合格性状态（如果有spec数据）
            if 'spec' in self.data:
                plot_data['status'] = self._determine_pass_fail_status(plot_data)
            else:
                plot_data['status'] = 'unknown'
            
            logger.info(f"准备了 {len(plot_data)} 个数据点")
            return plot_data
            
        except Exception as e:
            logger.error(f"准备绘图数据失败: {e}")
            return None
    
    def _determine_pass_fail_status(self, plot_data: pd.DataFrame) -> List[str]:
        """确定数据点的合格性状态"""
        spec_data = self.data['spec']
        status_list = []
        
        for _, row in plot_data.iterrows():
            x_pass = self._check_spec_compliance(row['x'], self.x_param, spec_data)
            y_pass = self._check_spec_compliance(row['y'], self.y_param, spec_data)
            
            if x_pass and y_pass:
                status_list.append('pass')
            else:
                status_list.append('fail')
        
        return status_list
    
    def _check_spec_compliance(self, value: float, param_name: str, spec_data: pd.DataFrame) -> bool:
        """检查单个参数是否符合规格"""
        try:
            param_spec = spec_data[spec_data['Parameter'] == param_name]
            if len(param_spec) == 0:
                return True  # 如果没有规格，默认为合格
            
            lsl = param_spec['LSL'].iloc[0] if 'LSL' in param_spec.columns else float('-inf')
            usl = param_spec['USL'].iloc[0] if 'USL' in param_spec.columns else float('inf')
            
            return lsl <= value <= usl
            
        except Exception:
            return True  # 出错时默认为合格
    
    def _draw_spec_limits(self, ax):
        """绘制规格限制区域"""
        try:
            spec_data = self.data['spec']
            
            # 获取X轴参数规格
            x_spec = spec_data[spec_data['Parameter'] == self.x_param]
            # 获取Y轴参数规格
            y_spec = spec_data[spec_data['Parameter'] == self.y_param]
            
            if len(x_spec) > 0 and len(y_spec) > 0:
                x_lsl = x_spec['LSL'].iloc[0] if 'LSL' in x_spec.columns else None
                x_usl = x_spec['USL'].iloc[0] if 'USL' in x_spec.columns else None
                y_lsl = y_spec['LSL'].iloc[0] if 'LSL' in y_spec.columns else None
                y_usl = y_spec['USL'].iloc[0] if 'USL' in y_spec.columns else None
                
                # 绘制规格区域矩形
                if all(v is not None for v in [x_lsl, x_usl, y_lsl, y_usl]):
                    rect = plt.Rectangle(
                        (x_lsl, y_lsl), x_usl - x_lsl, y_usl - y_lsl,
                        linewidth=2, edgecolor=self.colors['spec_area'],
                        facecolor=self.colors['spec_area'], alpha=0.2,
                        label='规格范围'
                    )
                    ax.add_patch(rect)
                    
                    logger.info(f"已绘制规格限制区域: X[{x_lsl}, {x_usl}], Y[{y_lsl}, {y_usl}]")
                
        except Exception as e:
            logger.warning(f"绘制规格限制失败: {e}")
    
    def _draw_scatter_points(self, ax, plot_data: pd.DataFrame):
        """绘制散点"""
        try:
            # 按状态分组绘制
            if 'status' in plot_data.columns and 'pass' in plot_data['status'].values:
                # 先绘制不合格点（在下层）
                fail_data = plot_data[plot_data['status'] == 'fail']
                if len(fail_data) > 0:
                    ax.scatter(fail_data['x'], fail_data['y'], 
                             c=self.colors['fail'], s=self.point_size, 
                             alpha=self.point_alpha, label='不合格', 
                             edgecolors='white', linewidth=0.5)
                
                # 再绘制合格点（在上层）
                pass_data = plot_data[plot_data['status'] == 'pass']
                if len(pass_data) > 0:
                    ax.scatter(pass_data['x'], pass_data['y'], 
                             c=self.colors['pass'], s=self.point_size, 
                             alpha=self.point_alpha, label='合格',
                             edgecolors='white', linewidth=0.5)
            else:
                # 没有状态信息，统一绘制
                ax.scatter(plot_data['x'], plot_data['y'], 
                         c=self.colors['pass'], s=self.point_size, 
                         alpha=self.point_alpha, label='数据点',
                         edgecolors='white', linewidth=0.5)
            
            logger.info(f"已绘制 {len(plot_data)} 个散点")
            
        except Exception as e:
            logger.error(f"绘制散点失败: {e}")
    
    def _draw_trend_line(self, ax, plot_data: pd.DataFrame):
        """绘制趋势线"""
        try:
            if len(plot_data) < 2:
                return
            
            x_data = plot_data['x'].values
            y_data = plot_data['y'].values
            
            # 线性回归
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
            
            # 计算趋势线点
            x_min, x_max = ax.get_xlim()
            trend_x = np.array([x_min, x_max])
            trend_y = slope * trend_x + intercept
            
            # 绘制趋势线
            ax.plot(trend_x, trend_y, color=self.colors['trend_line'], 
                   linewidth=2, linestyle='--', alpha=0.8, label='趋势线')
            
            logger.info(f"已绘制趋势线: R² = {r_value**2:.3f}")
            
        except Exception as e:
            logger.warning(f"绘制趋势线失败: {e}")
    
    def _add_correlation_info(self, ax, plot_data: pd.DataFrame):
        """添加相关性信息"""
        try:
            if len(plot_data) < 2:
                return
            
            x_data = plot_data['x'].values
            y_data = plot_data['y'].values
            
            # 计算相关系数
            correlation = np.corrcoef(x_data, y_data)[0, 1]
            
            # 在图表右上角显示相关性信息
            info_text = f'相关系数: {correlation:.3f}'
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            logger.info(f"相关系数: {correlation:.3f}")
            
        except Exception as e:
            logger.warning(f"添加相关性信息失败: {e}")
    
    def _add_custom_legend(self, ax):
        """添加自定义图例"""
        try:
            # 获取现有的图例句柄
            handles, labels = ax.get_legend_handles_labels()
            
            if handles:
                ax.legend(handles, labels, loc='upper right', 
                         frameon=True, fancybox=True, shadow=True)
            
        except Exception as e:
            logger.warning(f"添加图例失败: {e}")
    
    def update_parameters(self, x_param: str, y_param: str) -> bool:
        """更新X和Y轴参数"""
        self.x_param = x_param
        self.y_param = y_param
        logger.info(f"参数已更新 - X: {x_param}, Y: {y_param}")
        return True
    
    def get_correlation_matrix(self) -> Optional[pd.DataFrame]:
        """获取所有参数的相关性矩阵"""
        try:
            if 'cleaned' not in self.data:
                return None
            
            cleaned_data = self.data['cleaned']
            numeric_columns = self.get_available_parameters()
            
            if len(numeric_columns) < 2:
                return None
            
            correlation_matrix = cleaned_data[numeric_columns].corr()
            return correlation_matrix
            
        except Exception as e:
            logger.error(f"计算相关性矩阵失败: {e}")
            return None


# 快速测试
if __name__ == "__main__":
    print("测试散点图生成...")
    
    # 创建测试数据
    import tempfile
    import os
    
    # 模拟数据管理器
    class MockDataManager:
        def get_data(self, data_type, lot_id=None, **kwargs):
            if data_type == 'cleaned':
                # 模拟cleaned数据
                np.random.seed(42)
                n_points = 100
                data = {
                    'LotID': [lot_id] * n_points,
                    'Parameter1': np.random.normal(12, 2, n_points),
                    'Parameter2': np.random.normal(8, 1, n_points),
                    'Parameter3': np.random.normal(15, 3, n_points)
                }
                return pd.DataFrame(data)
            
            elif data_type == 'spec':
                # 模拟spec数据
                spec_data = {
                    'Parameter': ['Parameter1', 'Parameter2', 'Parameter3'],
                    'LSL': [8, 6, 10],
                    'USL': [16, 10, 20],
                    'Target': [12, 8, 15],
                    'Unit': ['mA', 'V', 'Ohm']
                }
                return pd.DataFrame(spec_data)
            
            return None
    
    try:
        # 创建数据管理器
        dm = MockDataManager()
        
        # 创建散点图
        scatter_chart = ScatterChart(
            data_manager=dm,
            lot_id="TEST_LOT",
            x_param="Parameter1",
            y_param="Parameter2"
        )
        
        # 生成图表
        success = scatter_chart.generate()
        if success:
            print("散点图生成成功！")
            
            # 保存图表
            save_path = scatter_chart.save(".", "scatter_chart_test.png")
            if save_path:
                print(f"保存位置: {save_path}")
            
            # 显示可用参数
            params = scatter_chart.get_available_parameters()
            print(f"可用参数: {params}")
            
            # 显示相关性矩阵
            corr_matrix = scatter_chart.get_correlation_matrix()
            if corr_matrix is not None:
                print("相关性矩阵:")
                print(corr_matrix.round(3))
            
        else:
            print("图表生成失败")
        
        # 关闭图表
        scatter_chart.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc() 