#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CP数据分析工具 - 自定义图表生成器
生成完整的CP测试数据分析报告，包括良率分析和参数统计

使用方法:
    python generate_custom_charts.py

输出目录:
    demo_output/generated_charts/
    ├── yield_chart_outputs/        # YieldChart 内置图表
    └── custom_plotly_express_charts/ # 自定义箱体图+散点图
"""

import sys
from pathlib import Path
import traceback

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from frontend.charts.yield_chart import YieldChart
    from frontend.charts.boxplot_chart import BoxplotChart
    print("✅ 成功导入图表模块")
except ImportError as e:
    print(f"❌ 导入图表模块失败: {e}")
    print("请确保 frontend/charts/ 目录下的模块文件存在")
    sys.exit(1)

def main():
    """主函数：生成完整的自定义图表分析"""
    print("🎨 CP数据分析工具 - 自定义图表生成器")
    print("=" * 60)
    
    # 数据目录配置 (可以修改为其他目录)
    data_input_dir = Path("output")          # 使用默认 output 目录
    # data_input_dir = Path("input_data")    # 或自定义目录
    
    base_output_dir = Path("demo_output/generated_charts")
    yield_output_dir = base_output_dir / "yield_chart_outputs"
    boxplot_output_dir = base_output_dir / "custom_plotly_express_charts"
    
    # 检查数据目录
    if not data_input_dir.exists():
        print(f"❌ 数据目录不存在: {data_input_dir}")
        print("请先运行数据清洗脚本生成数据文件")
        return False
    
    # 创建输出目录
    yield_output_dir.mkdir(parents=True, exist_ok=True)
    boxplot_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 数据输入目录: {data_input_dir.absolute()}")
    print(f"📁 良率图表输出: {yield_output_dir.absolute()}")
    print(f"📁 箱体图表输出: {boxplot_output_dir.absolute()}")
    
    total_success = True
    
    # ========== 第一部分：生成 YieldChart 内置图表 ==========
    print("\n" + "="*60)
    print("📈 第一部分：生成良率分析图表 (YieldChart)")
    print("="*60)
    
    try:
        # 创建良率图表分析器
        print("🔄 正在初始化良率图表分析器...")
        yield_chart = YieldChart(data_dir=data_input_dir)
        
        # 加载数据
        print("📊 正在加载良率数据...")
        success = yield_chart.load_data()
        if not success:
            print("❌ 良率数据加载失败")
            total_success = False
        else:
            print("✅ 良率数据加载成功")
            
            # 生成所有良率图表
            print("🎨 正在生成良率分析图表...")
            saved_files = yield_chart.save_all_charts(output_dir=yield_output_dir)
            
            if saved_files:
                print(f"✅ 成功生成 {len(saved_files)} 个良率图表:")
                for file_path in saved_files:
                    print(f"   📈 {file_path.name}")
            else:
                print("❌ 未生成任何良率图表")
                total_success = False
                
    except Exception as e:
        print(f"❌ 生成良率图表时发生错误: {e}")
        traceback.print_exc()
        total_success = False
    
    # ========== 第二部分：生成自定义 Plotly Express 图表 ==========
    print("\n" + "="*60)
    print("📦 第二部分：生成参数统计图表 (BoxplotChart)")
    print("="*60)
    
    try:
        # 创建箱体图分析器
        print("🔄 正在初始化箱体图分析器...")
        boxplot_chart = BoxplotChart(data_dir=data_input_dir)
        
        # 加载数据
        print("📊 正在加载参数数据...")
        success = boxplot_chart.load_data()
        if not success:
            print("❌ 参数数据加载失败")
            total_success = False
        else:
            print("✅ 参数数据加载成功")
            
            # 获取可用参数
            try:
                params = boxplot_chart.get_available_parameters()
                print(f"📋 发现 {len(params)} 个可分析参数")
                
                if params:
                    # 生成前几个参数的箱体图
                    max_charts = min(8, len(params))  # 最多生成8个图表
                    saved_files = []
                    
                    print(f"🎨 正在生成前 {max_charts} 个参数的箱体图...")
                    
                    for i, param in enumerate(params[:max_charts]):
                        try:
                            print(f"   📦 正在生成 {param} 的箱体图... ({i+1}/{max_charts})")
                            
                            # 生成箱体图
                            fig = boxplot_chart.get_chart(param)
                            if fig:
                                # 保存图表
                                file_path = boxplot_chart.save_chart(param, output_dir=boxplot_output_dir)
                                if file_path:
                                    saved_files.append(file_path)
                                    print(f"      ✅ 已保存: {file_path.name}")
                                else:
                                    print(f"      ❌ 保存失败: {param}")
                            else:
                                print(f"      ❌ 生成失败: {param}")
                                
                        except Exception as e:
                            print(f"      ❌ 处理参数 {param} 时出错: {e}")
                            continue
                    
                    if saved_files:
                        print(f"✅ 成功生成 {len(saved_files)} 个箱体图:")
                        for file_path in saved_files:
                            print(f"   📦 {file_path.name}")
                    else:
                        print("❌ 未生成任何箱体图")
                        total_success = False
                else:
                    print("❌ 没有找到可分析的参数")
                    total_success = False
                    
            except Exception as e:
                print(f"⚠️ 获取参数列表时出现错误: {e}")
                total_success = False
                
    except Exception as e:
        print(f"❌ 生成箱体图时发生错误: {e}")
        traceback.print_exc()
        total_success = False
    
    # ========== 总结 ==========
    print("\n" + "="*60)
    print("📊 生成结果总结")
    print("="*60)
    
    if total_success:
        print("🎉 所有图表生成完成！")
        print(f"\n📁 输出目录结构:")
        print(f"   {base_output_dir}/")
        print(f"   ├── yield_chart_outputs/        # YieldChart 内置图表")
        print(f"   └── custom_plotly_express_charts/ # 自定义箱体图+散点图")
        print(f"\n🌐 用浏览器打开HTML文件即可查看交互式图表")
        return True
    else:
        print("❌ 部分图表生成失败，请检查错误信息")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 自定义图表生成完成！")
        else:
            print("\n❌ 自定义图表生成失败，请检查错误信息")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断操作")
    except Exception as e:
        print(f"\n💥 程序异常退出: {e}")
        traceback.print_exc()
        sys.exit(1) 