#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试箱体图组件功能
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from frontend.charts.boxplot_chart import BoxplotChart

def test_boxplot_functionality():
    """测试箱体图的各项功能"""
    print("🧪 开始测试箱体图组件...")
    
    # 1. 初始化
    chart = BoxplotChart(data_dir="output")
    
    # 2. 加载数据
    print("\n📊 测试数据加载...")
    if chart.load_data():
        print("✅ 数据加载成功")
        
        # 检查数据基本信息
        if chart.cleaned_data is not None:
            print(f"   📈 Cleaned数据行数: {len(chart.cleaned_data):,}")
            print(f"   📦 批次数: {chart.cleaned_data['Lot_ID'].nunique()}")
            print(f"   🔬 晶圆数: {chart.cleaned_data['Wafer_ID'].nunique()}")
        
        if chart.spec_data is not None:
            print(f"   📋 Spec数据列数: {len(chart.spec_data.columns)}")
    else:
        print("❌ 数据加载失败")
        return False
    
    # 3. 获取可用参数
    print("\n🔬 测试参数获取...")
    params = chart.get_available_parameters()
    print(f"✅ 找到 {len(params)} 个测试参数: {params}")
    
    # 4. 测试参数信息获取
    if params:
        print(f"\n📋 测试参数信息获取（以 {params[0]} 为例）...")
        param_info = chart.get_parameter_info(params[0])
        print(f"   参数: {param_info.get('parameter', 'N/A')}")
        print(f"   单位: {param_info.get('unit', 'N/A')}")
        print(f"   上限: {param_info.get('limit_upper', 'N/A')}")
        print(f"   下限: {param_info.get('limit_lower', 'N/A')}")
        print(f"   测试条件: {param_info.get('test_condition', 'N/A')}")
    
    # 5. 测试标题生成
    if params:
        print(f"\n🏷️ 测试标题生成...")
        title = chart.generate_chart_title(params[0])
        print(f"✅ 生成标题: {title}")
    
    # 6. 测试数据准备
    if params:
        print(f"\n📊 测试数据准备...")
        try:
            chart_data, x_labels, param_info, lot_positions = chart.prepare_chart_data(params[0])
            print(f"✅ 数据准备成功")
            print(f"   数据点数: {len(chart_data)}")
            print(f"   X轴标签数: {len(x_labels)}")
            print(f"   批次数: {len(lot_positions)}")
            
            # 显示批次位置信息
            for lot_id, pos_info in lot_positions.items():
                print(f"   {lot_id}: 位置 {pos_info['start']} ~ {pos_info['end']}")
        except Exception as e:
            print(f"❌ 数据准备失败: {e}")
    
    # 7. 测试图表生成
    if params:
        print(f"\n🎨 测试图表生成...")
        try:
            fig = chart.get_chart(params[0])
            if fig:
                print(f"✅ {params[0]} 图表获取成功")
                
                # 检查图表属性
                print(f"   数据轨迹数: {len(fig.data)}")
                print(f"   图表标题: {fig.layout.title.text if fig.layout.title else 'N/A'}")
            else:
                print(f"❌ {params[0]} 图表获取失败")
        except Exception as e:
            print(f"❌ 图表获取失败: {e}")
    
    # 8. 测试保存功能
    if params:
        print(f"\n💾 测试图表保存...")
        try:
            saved_path = chart.save_chart(params[0], output_dir="test_charts")
            if saved_path and saved_path.exists():
                print(f"✅ 图表已保存到: {saved_path}")
                print(f"   文件大小: {saved_path.stat().st_size:,} 字节")
            else:
                print("❌ 图表保存失败")
        except Exception as e:
            print(f"❌ 保存失败: {e}")
    
    print("\n🎉 测试完成！")
    return True

def test_specific_parameter():
    """测试特定参数的详细信息"""
    print("\n🔍 详细测试 BVDSS1 参数...")
    
    chart = BoxplotChart(data_dir="output")
    if not chart.load_data():
        print("❌ 数据加载失败")
        return
    
    # 测试BVDSS1参数（如果存在）
    params = chart.get_available_parameters()
    if 'BVDSS1' in params:
        param = 'BVDSS1'
        print(f"\n📊 分析 {param} 参数...")
        
        # 参数信息
        param_info = chart.get_parameter_info(param)
        print(f"   单位: {param_info.get('unit', 'N/A')}")
        print(f"   上限: {param_info.get('limit_upper', 'N/A')}")
        print(f"   下限: {param_info.get('limit_lower', 'N/A')}")
        print(f"   测试条件: {param_info.get('test_condition', 'N/A')}")
        
        # 数据分布
        chart_data, x_labels, _, lot_positions = chart.prepare_chart_data(param)
        print(f"   总数据点: {len(chart_data)}")
        print(f"   批次信息:")
        
        for lot_id, pos_info in lot_positions.items():
            lot_data = chart_data[chart_data['lot_id'] == lot_id]
            wafer_count = len(lot_data['wafer_id'].unique())
            value_range = f"{lot_data['value'].min():.2f} ~ {lot_data['value'].max():.2f}"
            print(f"     {lot_id}: {wafer_count}片晶圆, 范围 {value_range}")
        
        # 从缓存获取图表
        fig = chart.get_chart(param)
        if fig:
            print(f"   成功获取参数 {param} 的图表")
            
            # 保存图表
            saved_path = chart.save_chart(param, output_dir="test_charts")
            print(f"   图表已保存: {saved_path}")
            
            # 标题
            title = chart.generate_chart_title(param)
            print(f"   图表标题: {title}")
        else:
            print(f"   未能获取参数 {param} 的图表")
    else:
        print("❌ 未找到 BVDSS1 参数")

if __name__ == "__main__":
    print("🧪 箱体图组件功能测试")
    print("=" * 50)
    
    try:
        # 基础功能测试
        test_boxplot_functionality()
        
        # 特定参数测试
        test_specific_parameter()
        
        print("\n✅ 所有测试完成！")
        print("💡 提示: Streamlit应用可能正在 http://localhost:8504 运行")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc() 