#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YieldChart使用演示 - 简洁版
快速展示如何使用YieldChart生成良率分析HTML图表
详细测试请运行: python test_yield_chart.py
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from frontend.charts.yield_chart import YieldChart

def main():
    """简洁的演示函数"""
    print("🏭 YieldChart使用演示")
    print("=" * 40)
    
    # 1. 创建YieldChart实例并加载数据
    print("📊 初始化并加载数据...")
    chart = YieldChart(data_dir="output")
    
    if not chart.load_data():
        print("❌ 数据加载失败，请检查output目录中是否有数据文件")
        return
    
    print("✅ 数据加载成功！")
    
    # 2. 显示基本信息
    print(f"   - Wafer数: {len(chart.wafer_data)}")
    print(f"   - 批次数: {chart.wafer_data['Lot_Short'].nunique()}")
    print(f"   - 平均良率: {chart.wafer_data['Yield_Numeric'].mean():.2f}%")
    
    # 显示可用图表
    chart_types = chart.get_available_chart_types()
    basic_charts = [ct for ct in chart_types if not ct.startswith('param_')]
    param_charts = [ct for ct in chart_types if ct.startswith('param_')]
    
    print(f"\n🎨 可用图表:")
    print(f"   📊 基础图表: {len(basic_charts)} 种")
    print(f"   🔬 参数图表: {len(param_charts)} 种")
    
    # 3. 批量生成所有图表
    print(f"\n📦 批量生成图表...")
    saved_paths = chart.save_all_charts(output_dir="demo_output")
    
    if saved_paths:
        print(f"✅ 成功生成 {len(saved_paths)} 个图表")
        print(f"📁 保存位置: demo_output/")
        print(f"💡 可在浏览器中打开HTML文件查看")
        
        # 显示几个示例文件
        print(f"\n📋 生成的图表文件:")
        for i, path in enumerate(saved_paths[:5]):
            print(f"   {i+1}. {path.name}")
        if len(saved_paths) > 5:
            print(f"   ... 还有 {len(saved_paths) - 5} 个图表")
            
    else:
        print("❌ 图表生成失败")

if __name__ == "__main__":
    try:
        main()
        print(f"\n🎉 演示完成！")
        print(f"💡 提示:")
        print(f"   - 运行 'python test_yield_chart.py' 查看详细测试")
        print(f"   - 所有图表都支持交互式操作")
        print(f"   - 参数折线图支持双层X轴和规格限制线")
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc() 