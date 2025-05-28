#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
综合分析演示脚本
展示YieldChart和BoxplotChart的所有核心功能
基于你的具体数据文件：yield.csv, spec.csv, cleaned.csv
"""

import sys
from pathlib import Path
import traceback

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主函数：展示完整的CP数据分析流程"""
    
    print("🔬 CP数据综合分析演示")
    print("=" * 60)
    print("📋 分析内容：")
    print("   1️⃣ YieldChart - 批次良率分析")
    print("      • 批次良率折线图")
    print("      • 失效类型分析") 
    print("      • 批次良率对比")
    print("   2️⃣ BoxplotChart - 参数统计分析")
    print("      • 异常值处理后的数据分析")
    print("      • X轴双层显示 (Wafer编号 + 批次信息)")
    print("      • 箱体图+散点图组合")
    print("=" * 60)
    
    # 配置路径
    data_input_dir = "output"
    yield_output_dir = "demo_output/comprehensive_analysis/yield_charts"
    boxplot_output_dir = "demo_output/comprehensive_analysis/boxplot_charts"
    
    print(f"📁 数据目录: {Path(data_input_dir).absolute()}")
    print(f"📁 良率图表输出: {Path(yield_output_dir).absolute()}")
    print(f"📁 箱体图输出: {Path(boxplot_output_dir).absolute()}")
    print()
    
    total_success = True
    
    # ========== 第一部分：YieldChart 良率分析 ==========
    print("🎯 第一部分：良率分析 (YieldChart)")
    print("-" * 40)
    
    try:
        from frontend.charts.yield_chart import YieldChart
        
        print("🔄 正在初始化良率图表分析器...")
        yield_chart = YieldChart(data_dir=data_input_dir)
        
        print("📊 正在加载良率数据...")
        success = yield_chart.load_data()
        if not success:
            print("❌ 良率数据加载失败")
            total_success = False
        else:
            print("✅ 良率数据加载成功")
            
            # 显示数据概览
            if yield_chart.wafer_data is not None:
                wafer_count = len(yield_chart.wafer_data)
                lot_count = yield_chart.wafer_data['Lot_Short'].nunique()
                avg_yield = yield_chart.wafer_data['Yield_Numeric'].mean()
                print(f"📋 数据概览: {wafer_count} 个wafer, {lot_count} 个批次, 平均良率 {avg_yield:.2f}%")
            
            # 生成核心良率图表
            print("\n🎨 正在生成核心良率图表...")
            core_charts = ['wafer_trend', 'lot_comparison', 'failure_analysis']
            
            saved_files = []
            for chart_type in core_charts:
                try:
                    file_path = yield_chart.save_chart(chart_type, output_dir=yield_output_dir)
                    if file_path:
                        saved_files.append(file_path)
                        chart_name = {
                            'wafer_trend': '批次良率折线图',
                            'lot_comparison': '批次良率对比',
                            'failure_analysis': '失效类型分析'
                        }.get(chart_type, chart_type)
                        print(f"   ✅ {chart_name}: {file_path.name}")
                    else:
                        print(f"   ❌ {chart_type} 生成失败")
                        total_success = False
                except Exception as e:
                    print(f"   ❌ {chart_type} 生成异常: {e}")
                    total_success = False
            
            print(f"\n📈 良率分析完成，共生成 {len(saved_files)} 个图表")
                
    except Exception as e:
        print(f"❌ 良率分析模块异常: {e}")
        traceback.print_exc()
        total_success = False
    
    # ========== 第二部分：BoxplotChart 参数统计分析 ==========
    print("\n🎯 第二部分：参数统计分析 (BoxplotChart)")
    print("-" * 40)
    
    try:
        from frontend.charts.boxplot_chart import BoxplotChart
        
        print("🔄 正在初始化箱体图分析器...")
        boxplot_chart = BoxplotChart(data_dir=data_input_dir)
        
        print("📊 正在加载参数数据...")
        success = boxplot_chart.load_data()
        if not success:
            print("❌ 参数数据加载失败")
            total_success = False
        else:
            print("✅ 参数数据加载成功")
            
            # 显示数据概览
            if boxplot_chart.cleaned_data is not None:
                record_count = len(boxplot_chart.cleaned_data)
                lot_count = boxplot_chart.cleaned_data['Lot_ID'].nunique()
                wafer_count = boxplot_chart.cleaned_data['Wafer_ID'].nunique()
                print(f"📋 数据概览: {record_count:,} 条记录, {lot_count} 个批次, {wafer_count} 个wafer")
            
            # 获取可用参数
            available_params = boxplot_chart.get_available_parameters()
            print(f"📋 发现 {len(available_params)} 个可分析参数: {available_params}")
            
            # 生成所有参数的箱体图
            print(f"\n🎨 正在生成所有 {len(available_params)} 个参数的箱体图...")
            demo_params = available_params  # 生成所有参数
            
            saved_files = []
            for i, param in enumerate(demo_params, 1):
                try:
                    print(f"   📦 正在生成 {param} 的箱体图... ({i}/{len(demo_params)})")
                    file_path = boxplot_chart.save_chart(param, output_dir=boxplot_output_dir)
                    if file_path:
                        saved_files.append(file_path)
                        print(f"      ✅ 已保存: {file_path.name}")
                    else:
                        print(f"      ❌ {param} 生成失败")
                        total_success = False
                except Exception as e:
                    print(f"      ❌ {param} 生成异常: {e}")
                    total_success = False
            
            print(f"\n📦 参数统计分析完成，共生成 {len(saved_files)} 个箱体图")
            
            # 显示箱体图特色功能
            print("\n🌟 箱体图特色功能:")
            print("   • X轴双层显示: 上层显示Wafer编号(W1,W2...), 下层显示批次信息")
            print("   • 异常值检测: 自动识别和标注异常数据点")
            print("   • 规格限制线: 显示参数的上下限规格线")
            print("   • 交互式悬停: 鼠标悬停显示详细信息")
                
    except Exception as e:
        print(f"❌ 参数统计分析模块异常: {e}")
        traceback.print_exc()
        total_success = False
    
    # ========== 总结 ==========
    print("\n" + "=" * 60)
    if total_success:
        print("🎉 综合分析演示完成！")
        print("\n📂 生成的图表文件:")
        print(f"   📈 良率图表: {yield_output_dir}/")
        print(f"   📦 箱体图表: {boxplot_output_dir}/")
        print("\n💡 使用说明:")
        print("   1. 用现代浏览器打开HTML文件查看交互式图表")
        print("   2. 图表支持缩放、平移、悬停等交互操作")
        print("   3. 可以点击图例控制数据系列的显示/隐藏")
    else:
        print("⚠️  演示过程中遇到一些问题，请检查上述错误信息")
    
    print("\n🔗 相关文件:")
    print("   • demo_yield_chart.py - 单独的良率图表演示")
    print("   • test_boxplot.py - 单独的箱体图演示") 
    print("   • generate_custom_charts.py - 完整的图表生成器")

if __name__ == "__main__":
    main() 