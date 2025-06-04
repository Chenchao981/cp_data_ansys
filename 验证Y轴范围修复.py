#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证Y轴范围修复效果
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from frontend.charts.summary_chart.summary_chart import SummaryChart

def verify_y_axis_fix():
    """验证Y轴范围修复效果"""
    print("🔍 验证Y轴范围修复效果...")
    
    # 创建SummaryChart实例
    chart = SummaryChart(data_dir="output")
    
    if not chart.load_data():
        print("❌ 数据加载失败")
        return
    
    # 获取IGSSR1参数信息
    param_info = chart.boxplot_chart.get_parameter_info('IGSSR1')
    
    print(f"📊 IGSSR1参数信息:")
    print(f"   - 参数名: IGSSR1")
    print(f"   - 单位: {param_info.get('unit', 'N/A')}")
    print(f"   - 上限 (LimitU): {param_info.get('limit_upper')}")
    print(f"   - 下限 (LimitL): {param_info.get('limit_lower')}")
    
    # 计算Y轴范围
    limit_l = param_info.get('limit_lower')
    limit_u = param_info.get('limit_upper')
    
    if limit_l is not None and limit_u is not None:
        lsl = min(limit_l, limit_u)
        usl = max(limit_l, limit_u)
        current_span = usl - lsl
        
        if current_span == 0:
            padding = abs(usl * 0.1) if usl != 0 else 1.0
        else:
            padding = current_span * 0.1
        
        y_min = lsl - padding
        y_max = usl + padding
        
        print(f"📏 计算的Y轴范围:")
        print(f"   - Y轴最小值: {y_min:.2e}")
        print(f"   - Y轴最大值: {y_max:.2e}")
        print(f"   - 范围跨度: {y_max - y_min:.2e}")
        
        # 检查实际数据范围
        cleaned_data = chart.boxplot_chart.cleaned_data
        igssr1_data = cleaned_data['IGSSR1'].dropna()
        
        print(f"📈 实际数据范围:")
        print(f"   - 数据最小值: {igssr1_data.min():.2e}")
        print(f"   - 数据最大值: {igssr1_data.max():.2e}")
        print(f"   - 数据中位数: {igssr1_data.median():.2e}")
        
        # 验证数据是否在Y轴范围内
        if igssr1_data.min() >= y_min and igssr1_data.max() <= y_max:
            print("✅ 数据完全在Y轴范围内")
        else:
            print("⚠️  数据超出Y轴范围")
            
        # 验证上下限线是否在范围内
        if limit_l >= y_min and limit_u <= y_max:
            print("✅ 上下限线在Y轴范围内")
        else:
            print("⚠️  上下限线超出Y轴范围")
            
    else:
        print("❌ 无法获取参数限制信息")

if __name__ == "__main__":
    verify_y_axis_fix() 