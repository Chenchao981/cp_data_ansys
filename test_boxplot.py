#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CP数据分析工具 - 箱体图测试脚本
生成参数分布统计、异常值检测等箱体图和散点图

使用方法:
    python test_boxplot.py

输出目录:
    demo_output/generated_charts/custom_plotly_express_charts/
"""

import sys
from pathlib import Path
import traceback

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from frontend.charts.boxplot_chart import BoxplotChart
    print("✅ 成功导入 BoxplotChart 模块")
except ImportError as e:
    print(f"❌ 导入 BoxplotChart 模块失败: {e}")
    print("请确保 frontend/charts/boxplot_chart.py 文件存在")
    sys.exit(1)

def main():
    """主函数：生成箱体图分析"""
    print("📦 CP数据分析工具 - 箱体图统计分析")
    print("=" * 50)
    
    # 数据目录配置
    data_dir = Path("output")
    output_dir = Path("demo_output/generated_charts/custom_plotly_express_charts")
    
    # 检查数据目录
    if not data_dir.exists():
        print(f"❌ 数据目录不存在: {data_dir}")
        print("请先运行数据清洗脚本生成数据文件")
        return False
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 数据目录: {data_dir.absolute()}")
    print(f"📁 输出目录: {output_dir.absolute()}")
    
    try:
        # 创建箱体图分析器
        print("\n🔄 正在初始化箱体图分析器...")
        chart = BoxplotChart(data_dir=data_dir)
        
        # 加载数据
        print("📊 正在加载数据...")
        success = chart.load_data()
        if not success:
            print("❌ 数据加载失败，请检查数据文件格式")
            return False
        
        print("✅ 数据加载成功")
        
        # 获取可用参数
        try:
            params = chart.get_available_parameters()
            print(f"📋 发现 {len(params)} 个可分析参数: {params}")
        except Exception as e:
            print(f"⚠️ 获取参数列表时出现警告: {e}")
            params = []
        
        if not params:
            print("❌ 没有找到可分析的参数")
            return False
        
        # 生成所有参数的箱体图
        max_charts = len(params)  # 生成所有参数的图表
        saved_files = []
        
        print(f"\n🎨 正在生成所有 {max_charts} 个参数的箱体图...")
        
        for i, param in enumerate(params):
            try:
                print(f"   📦 正在生成 {param} 的箱体图... ({i+1}/{max_charts})")
                
                # 生成箱体图
                fig = chart.get_chart(param)
                if fig:
                    # 保存图表
                    file_path = chart.save_chart(param, output_dir=output_dir)
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
            print(f"\n✅ 成功生成 {len(saved_files)} 个箱体图文件:")
            for file_path in saved_files:
                print(f"   📦 {file_path.name}")
            
            print(f"\n🌐 图表已保存到: {output_dir.absolute()}")
            print("💡 用浏览器打开HTML文件即可查看交互式箱体图")
            return True
        else:
            print("❌ 未生成任何图表文件")
            return False
            
    except Exception as e:
        print(f"❌ 生成箱体图时发生错误: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 箱体图测试完成！")
        else:
            print("\n❌ 箱体图测试失败，请检查错误信息")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断操作")
    except Exception as e:
        print(f"\n💥 程序异常退出: {e}")
        traceback.print_exc()
        sys.exit(1) 