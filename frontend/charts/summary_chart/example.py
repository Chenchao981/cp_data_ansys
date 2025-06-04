#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Summary Chart 使用示例
演示如何使用SummaryChart类生成合并的箱体图
"""

from summary_chart import SummaryChart
import logging

def example_basic_usage():
    """基本使用示例"""
    print("📊 基本使用示例")
    print("-" * 30)
    
    # 初始化
    chart = SummaryChart(data_dir="../../../output")  # 相对于example.py的路径
    
    # 加载数据
    if chart.load_data():
        print("✅ 数据加载成功")
        
        # 获取参数列表
        params = chart.get_available_parameters()
        print(f"📋 可用参数: {len(params)} 个")
        
        # 生成合并图表
        saved_path = chart.save_summary_chart(output_dir="../../../charts_output")
        if saved_path:
            print(f"💾 图表已保存: {saved_path}")
        else:
            print("❌ 图表保存失败")
    else:
        print("❌ 数据加载失败")

def example_custom_config():
    """自定义配置示例"""
    print("\n🎨 自定义配置示例")
    print("-" * 30)
    
    # 初始化并自定义配置
    chart = SummaryChart(data_dir="../../../output")
    
    # 修改样式配置
    chart.summary_config.update({
        'subplot_height': 500,  # 增加子图高度
        'subplot_spacing': 0.03,  # 增加子图间距
        'title_font_size': 24,  # 增大标题字体
    })
    
    if chart.load_data():
        print("✅ 数据加载成功，使用自定义配置")
        
        # 生成图表
        saved_path = chart.save_summary_chart(output_dir="../../../charts_output")
        if saved_path:
            print(f"💾 自定义图表已保存: {saved_path}")

def example_parameter_info():
    """参数信息查看示例"""
    print("\n🔍 参数信息查看示例")
    print("-" * 30)
    
    chart = SummaryChart(data_dir="../../../output")
    
    if chart.load_data():
        params = chart.get_available_parameters()
        
        print("📋 详细参数信息:")
        for param in params[:3]:  # 只显示前3个参数
            info = chart.boxplot_chart.get_parameter_info(param)
            print(f"  • {param}:")
            print(f"    单位: {info.get('unit', 'N/A')}")
            print(f"    上限: {info.get('limit_upper', 'N/A')}")
            print(f"    下限: {info.get('limit_lower', 'N/A')}")
            print(f"    测试条件: {info.get('test_condition', 'N/A')}")

def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(level=logging.WARNING)  # 减少日志输出
    
    print("🚀 Summary Chart 使用示例")
    print("=" * 50)
    
    # 运行示例
    example_basic_usage()
    example_custom_config()
    example_parameter_info()
    
    print("\n" + "=" * 50)
    print("✨ 示例运行完成")
    print("\n💡 提示:")
    print("  • 生成的HTML文件可以在浏览器中打开")
    print("  • 支持Y轴滚动查看不同参数")
    print("  • 支持X轴滑动查看不同批次")
    print("  • 所有参数的X轴完全对齐")

if __name__ == "__main__":
    main() 