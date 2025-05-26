#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
折线图模块 - 基于BaseChart架构
主要用于良率趋势分析，展示参数随位置/时间的变化
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from frontend.charts.base_chart import BaseChart

class LineChart(BaseChart):
    """折线图类 - 专门用于趋势分析"""
    
    def load_required_data(self):
        """加载折线图所需的数据"""
        # 尝试加载yield数据（良率趋势）
        self.data['yield'] = self.data_manager.get_data('yield', self.lot_id)
        
        # 如果没有yield数据，尝试从cleaned数据生成趋势
        if self.data['yield'] is None:
            cleaned_data = self.data_manager.get_data('cleaned', self.lot_id)
            if cleaned_data is not None:
                self.data['cleaned'] = cleaned_data
                return True
        
        return self.data['yield'] is not None
    
    def generate(self):
        """生成折线图"""
        # 加载数据
        if not self.load_required_data():
            print("无法加载所需数据")
            return False
        
        # 创建图表画布
        fig, ax = self._create_figure()
        
        if self.data['yield'] is not None:
            self._generate_yield_trend(ax)
        else:
            self._generate_parameter_trend(ax)
        
        # 应用通用样式
        self._add_grid()
        self._format_axes()
        
        return True
    
    def _generate_yield_trend(self, ax):
        """生成良率趋势图"""
        yield_data = self.data['yield']
        
        # 假设yield数据格式：Parameter, Yield, Count等列
        if 'Parameter' in yield_data.columns and len(yield_data.columns) >= 2:
            # 使用第二列作为Y值
            y_column = yield_data.columns[1]
            x_values = range(len(yield_data))
            y_values = yield_data[y_column]
            
            # 绘制折线图
            ax.plot(x_values, y_values, 
                   marker='o', markersize=6, linewidth=2,
                   color='#1f77b4', markerfacecolor='white', 
                   markeredgewidth=2, markeredgecolor='#1f77b4')
            
            # 设置标题和标签
            self._add_title_and_labels(
                title=f'良率趋势分析 - {self.lot_id}',
                xlabel='参数序号',
                ylabel=y_column
            )
            
        else:
            # 数据格式不标准，显示提示
            ax.text(0.5, 0.5, f'数据格式不支持', 
                   transform=ax.transAxes, ha='center', va='center',
                   fontsize=12, bbox=dict(boxstyle='round', facecolor='wheat'))
    
    def _generate_parameter_trend(self, ax):
        """基于cleaned数据生成参数趋势"""
        cleaned_data = self.data['cleaned']
        
        # 选择数值型列
        numeric_columns = cleaned_data.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_columns:
            ax.text(0.5, 0.5, '未找到数值型参数', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        # 选择前几个参数绘制趋势
        max_params = min(3, len(numeric_columns))
        selected_params = numeric_columns[:max_params]
        
        x_values = range(len(cleaned_data))
        
        # 绘制多个参数的趋势
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        for i, param in enumerate(selected_params):
            y_values = cleaned_data[param]
            ax.plot(x_values, y_values, 
                   label=param, color=colors[i % len(colors)],
                   linewidth=1.5, alpha=0.8)
        
        # 设置标题和标签
        self._add_title_and_labels(
            title=f'参数趋势分析 - {self.lot_id}',
            xlabel='测试点序号',
            ylabel='参数值'
        )
        
        # 添加图例
        self._add_legend()

# 快速测试
if __name__ == "__main__":
    from frontend.core.data_manager import DataManager
    
    print("测试折线图生成...")
    
    # 创建数据管理器
    dm = DataManager(data_source="auto", cache_enabled=True, data_dir="output")
    
    # 创建折线图
    line_chart = LineChart(
        data_manager=dm,
        lot_id="FA54-5339-327A-250501@203"
    )
    
    # 生成图表
    try:
        success = line_chart.generate()
        if success:
            print("折线图生成成功！")
            
            # 保存图表
            save_path = line_chart.save(".", "line_chart_test.png")
            if save_path:
                print(f"保存位置: {save_path}")
            
            # 显示数据信息
            info = line_chart.get_data_info()
            print(f"数据信息: {info}")
            
        else:
            print("图表生成失败")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc() 