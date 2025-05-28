#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CP数据分析工具 - 良率图表演示脚本
快速生成良率趋势、批次对比、参数分析等交互式HTML图表

使用方法:
    python demo_yield_chart.py

输出目录:
    demo_output/all_charts/
"""

import sys
from pathlib import Path
import traceback

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from frontend.charts.yield_chart import YieldChart
    print("✅ 成功导入 YieldChart 模块")
except ImportError as e:
    print(f"❌ 导入 YieldChart 模块失败: {e}")
    print("请确保 frontend/charts/yield_chart.py 文件存在")
    sys.exit(1)

def main():
    """主函数：生成良率分析图表"""
    print("🔬 CP数据分析工具 - 良率图表演示")
    print("=" * 50)
    
    # 数据目录配置
    data_dir = Path("output")
    output_dir = Path("demo_output/all_charts")
    
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
        # 创建图表分析器
        print("\n🔄 正在初始化图表分析器...")
        chart = YieldChart(data_dir=data_dir)
        
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
            print(f"📋 发现 {len(params)} 个可分析参数: {params[:5]}{'...' if len(params) > 5 else ''}")
        except Exception as e:
            print(f"⚠️ 获取参数列表时出现警告: {e}")
            params = []
        
        # 生成所有图表
        print("\n🎨 正在生成图表...")
        saved_files = chart.save_all_charts(output_dir=output_dir)
        
        if saved_files:
            print(f"✅ 成功生成 {len(saved_files)} 个图表文件:")
            for file_path in saved_files:
                print(f"   📈 {file_path.name}")
            
            print(f"\n🌐 图表已保存到: {output_dir.absolute()}")
            print("💡 用浏览器打开HTML文件即可查看交互式图表")
            return True
        else:
            print("❌ 未生成任何图表文件")
            return False
            
    except Exception as e:
        print(f"❌ 生成图表时发生错误: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 演示完成！")
        else:
            print("\n❌ 演示失败，请检查错误信息")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断操作")
    except Exception as e:
        print(f"\n💥 程序异常退出: {e}")
        traceback.print_exc()
        sys.exit(1) 