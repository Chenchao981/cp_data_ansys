#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 Summary Chart 功能的简单脚本
"""

from frontend.charts.summary_chart import SummaryChart
import logging

def main():
    """主测试函数"""
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🚀 开始测试 Summary Chart 功能")
    print("=" * 50)
    
    # 初始化
    chart = SummaryChart(data_dir="output")
    
    # 加载数据
    print("📂 正在加载数据...")
    if chart.load_data():
        print("✅ 数据加载成功！")
        
        # 显示可用参数
        params = chart.get_available_parameters()
        print(f"📊 发现 {len(params)} 个测试参数:")
        for i, param in enumerate(params, 1):
            param_info = chart.boxplot_chart.get_parameter_info(param)
            unit = param_info.get('unit', '')
            unit_str = f" [{unit}]" if unit else ""
            print(f"  {i:2d}. {param}{unit_str}")
        
        # 生成合并图表
        print("\n🎨 正在生成合并图表...")
        saved_path = chart.save_summary_chart(output_dir="charts_output")
        
        if saved_path:
            print(f"✅ 合并图表生成成功！")
            print(f"📁 保存位置: {saved_path}")
            print(f"📏 文件大小: {saved_path.stat().st_size / 1024 / 1024:.1f} MB")
            
            # 显示功能特性
            print("\n🎯 功能特性:")
            print("  • 所有参数垂直排列在一个页面")
            print("  • X轴对齐，支持水平滑动查看不同批次")
            print("  • Y轴滚动查看不同参数")
            print("  • 保留箱体图、散点图、上下限线等完整功能")
            print("  • 复用BoxplotChart的配色和样式")
            
            print(f"\n🌐 请在浏览器中打开: {saved_path.absolute()}")
            
        else:
            print("❌ 合并图表生成失败")
            
    else:
        print("❌ 数据加载失败，请检查 output 目录中的数据文件")
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")

if __name__ == "__main__":
    main() 