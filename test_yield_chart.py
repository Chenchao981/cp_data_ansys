#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试良率图表组件功能
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from frontend.charts.yield_chart import YieldChart

def test_yield_chart_functionality():
    """测试良率图表的各项功能"""
    print("🧪 开始测试良率图表组件...")
    
    # 1. 初始化
    chart = YieldChart(data_dir="output")
    
    # 2. 加载数据
    print("\n📊 测试数据加载...")
    if chart.load_data():
        print("✅ 数据加载成功")
        
        # 检查数据基本信息
        if chart.yield_data is not None:
            print(f"   📈 原始yield数据行数: {len(chart.yield_data):,}")
            print(f"   📦 Wafer数据行数: {len(chart.wafer_data):,}")
            print(f"   🔬 批次数: {chart.wafer_data['Lot_Short'].nunique()}")
            print(f"   📋 汇总数据行数: {len(chart.summary_data):,}")
        
        if chart.spec_data is not None:
            print(f"   📋 Spec数据列数: {len(chart.spec_data.columns)}")
        
        if chart.cleaned_data is not None:
            print(f"   🧹 Cleaned数据行数: {len(chart.cleaned_data):,}")
    else:
        print("❌ 数据加载失败")
        return False
    
    # 3. 获取可用图表类型
    print("\n🔬 测试图表类型获取...")
    chart_types = chart.get_available_chart_types()
    print(f"✅ 找到 {len(chart_types)} 种图表类型: {chart_types}")
    
    # 4. 获取可用参数
    print("\n🔬 测试参数获取...")
    params = chart.get_available_parameters()
    print(f"✅ 找到 {len(params)} 个测试参数: {params}")
    
    # 5. 测试参数信息获取
    if params:
        print(f"\n📋 测试参数信息获取（以 {params[0]} 为例）...")
        param_info = chart.get_parameter_info(params[0])
        print(f"   参数: {param_info.get('parameter', 'N/A')}")
        print(f"   单位: {param_info.get('unit', 'N/A')}")
        print(f"   上限: {param_info.get('limit_upper', 'N/A')}")
        print(f"   下限: {param_info.get('limit_lower', 'N/A')}")
        print(f"   测试条件: {param_info.get('test_condition', 'N/A')}")
    
    # 6. 测试标题生成
    print(f"\n🏷️ 测试标题生成...")
    for chart_type in chart_types[:5]:  # 只测试前5个
        title = chart.generate_chart_title(chart_type)
        print(f"   {chart_type}: {title}")
    
    # 7. 测试参数数据准备
    if params:
        print(f"\n📊 测试参数数据准备（以 {params[0]} 为例）...")
        try:
            chart_data, x_labels, param_info, lot_positions = chart.prepare_parameter_chart_data(params[0])
            print(f"✅ 数据准备成功")
            print(f"   数据点数: {len(chart_data)}")
            print(f"   X轴标签数: {len(x_labels)}")
            print(f"   批次数: {len(lot_positions)}")
            
            # 显示批次位置信息
            for lot_id, pos_info in lot_positions.items():
                print(f"   {lot_id}: 位置 {pos_info['start']} ~ {pos_info['end']}")
        except Exception as e:
            print(f"❌ 数据准备失败: {e}")
    
    # 8. 测试单个图表生成
    print(f"\n🎨 测试单个图表生成...")
    for chart_type in chart_types[:3]:  # 只测试前3个
        try:
            fig = chart.get_chart(chart_type)
            if fig:
                print(f"✅ {chart_type} 图表生成成功")
                
                # 检查图表属性
                print(f"   数据轨迹数: {len(fig.data)}")
                print(f"   图表标题: {fig.layout.title.text if fig.layout.title else 'N/A'}")
            else:
                print(f"❌ {chart_type} 图表生成失败")
        except Exception as e:
            print(f"❌ {chart_type} 图表生成失败: {e}")
    
    # 9. 测试保存功能
    print(f"\n💾 测试图表保存...")
    for chart_type in chart_types[:3]:  # 只测试前3个
        try:
            saved_path = chart.save_chart(chart_type, output_dir="test_charts/yield")
            if saved_path and saved_path.exists():
                print(f"✅ {chart_type} 图表已保存到: {saved_path}")
                print(f"   文件大小: {saved_path.stat().st_size:,} 字节")
            else:
                print(f"❌ {chart_type} 图表保存失败")
        except Exception as e:
            print(f"❌ {chart_type} 保存失败: {e}")
    
    # 10. 测试批量保存
    print(f"\n📦 测试批量保存...")
    try:
        saved_paths = chart.save_all_charts(output_dir="test_charts/yield_batch")
        if saved_paths:
            print(f"✅ 批量保存成功，共保存 {len(saved_paths)} 个图表")
            for path in saved_paths[:5]:  # 只显示前5个
                print(f"   - {path.name} ({path.stat().st_size:,} 字节)")
            if len(saved_paths) > 5:
                print(f"   ... 还有 {len(saved_paths) - 5} 个图表")
        else:
            print("❌ 批量保存失败")
    except Exception as e:
        print(f"❌ 批量保存失败: {e}")
    
    print("\n🎉 测试完成！")
    return True

def test_parameter_charts():
    """专门测试参数折线图功能"""
    print("\n🔍 专门测试参数折线图功能...")
    
    chart = YieldChart(data_dir="output")
    if not chart.load_data():
        print("❌ 数据加载失败")
        return
    
    params = chart.get_available_parameters()
    if not params:
        print("❌ 没有可用的参数")
        return
    
    # 测试前3个参数
    test_params = params[:3]
    print(f"📊 测试参数: {test_params}")
    
    for param in test_params:
        print(f"\n🔬 测试参数 {param}...")
        
        # 参数信息
        param_info = chart.get_parameter_info(param)
        print(f"   单位: {param_info.get('unit', 'N/A')}")
        print(f"   上限: {param_info.get('limit_upper', 'N/A')}")
        print(f"   下限: {param_info.get('limit_lower', 'N/A')}")
        print(f"   测试条件: {param_info.get('test_condition', 'N/A')}")
        
        # 数据准备
        chart_data, x_labels, _, lot_positions = chart.prepare_parameter_chart_data(param)
        print(f"   总数据点: {len(chart_data)}")
        print(f"   批次信息:")
        
        for lot_id, pos_info in lot_positions.items():
            lot_data = chart_data[chart_data['lot_id'] == lot_id]
            wafer_count = len(lot_data['wafer_id'].unique())
            if len(lot_data) > 0:
                value_range = f"{lot_data['value'].min():.2e} ~ {lot_data['value'].max():.2e}"
                print(f"     {lot_id}: {wafer_count}片晶圆, 范围 {value_range}")
        
        # 生成并保存图表
        chart_type = f"param_{param}"
        fig = chart.get_chart(chart_type)
        if fig:
            saved_path = chart.save_chart(chart_type, output_dir="test_charts/yield_detailed")
            print(f"   图表已保存: {saved_path}")
            
            # 标题
            title = chart.generate_chart_title(chart_type)
            print(f"   图表标题: {title}")
        else:
            print(f"   ❌ 图表生成失败")

def test_specific_chart_details():
    """测试特定图表的详细信息"""
    print("\n🔍 详细测试各图表类型...")
    
    chart = YieldChart(data_dir="output")
    if not chart.load_data():
        print("❌ 数据加载失败")
        return
    
    chart_types = chart.get_available_chart_types()
    
    # 只测试基础图表类型
    basic_chart_types = [ct for ct in chart_types if not ct.startswith('param_')]
    
    for chart_type in basic_chart_types:
        print(f"\n📊 分析 {chart_type} 图表...")
        
        try:
            fig = chart.get_chart(chart_type)
            if fig:
                # 分析图表内容
                print(f"   图表类型: {type(fig).__name__}")
                print(f"   数据轨迹数: {len(fig.data)}")
                
                # 检查不同类型图表的特定属性
                if chart_type == 'wafer_trend':
                    lots = chart.wafer_data['Lot_Short'].unique()
                    print(f"   批次数: {len(lots)}")
                    print(f"   批次列表: {list(lots)}")
                    
                elif chart_type == 'lot_comparison':
                    lot_stats = chart.wafer_data.groupby('Lot_Short')['Yield_Numeric'].agg(['mean', 'count']).reset_index()
                    print(f"   批次统计:")
                    for _, row in lot_stats.iterrows():
                        print(f"     {row['Lot_Short']}: 平均{row['mean']:.2f}%, {int(row['count'])}片")
                        
                elif chart_type == 'yield_distribution':
                    mean_yield = chart.wafer_data['Yield_Numeric'].mean()
                    std_yield = chart.wafer_data['Yield_Numeric'].std()
                    print(f"   良率统计: 平均{mean_yield:.2f}%, 标准差{std_yield:.2f}%")
                    
                elif chart_type == 'failure_analysis':
                    failure_columns = ['Bin3', 'Bin4', 'Bin6', 'Bin7', 'Bin8', 'Bin9']
                    failure_totals = chart.wafer_data[failure_columns].sum()
                    failure_totals = failure_totals[failure_totals > 0]
                    print(f"   失效类型数: {len(failure_totals)}")
                    if len(failure_totals) > 0:
                        print(f"   失效分布: {dict(failure_totals)}")
                
                # 保存图表
                saved_path = chart.save_chart(chart_type, output_dir="test_charts/yield_detailed")
                print(f"   图表已保存: {saved_path}")
                
            else:
                print(f"❌ 无法获取 {chart_type} 图表")
                
        except Exception as e:
            print(f"❌ 分析 {chart_type} 失败: {e}")

def test_data_analysis():
    """测试数据分析功能"""
    print("\n📈 数据分析测试...")
    
    chart = YieldChart(data_dir="output")
    if not chart.load_data():
        print("❌ 数据加载失败")
        return
    
    # 分析wafer数据
    print(f"\n📊 Wafer数据分析:")
    print(f"   总Wafer数: {len(chart.wafer_data)}")
    print(f"   批次数: {chart.wafer_data['Lot_Short'].nunique()}")
    print(f"   良率范围: {chart.wafer_data['Yield_Numeric'].min():.2f}% ~ {chart.wafer_data['Yield_Numeric'].max():.2f}%")
    print(f"   平均良率: {chart.wafer_data['Yield_Numeric'].mean():.2f}%")
    print(f"   良率标准差: {chart.wafer_data['Yield_Numeric'].std():.2f}%")
    
    # 分析失效数据
    failure_columns = ['Bin3', 'Bin4', 'Bin6', 'Bin7', 'Bin8', 'Bin9']
    total_failures = chart.wafer_data[failure_columns].sum().sum()
    total_chips = chart.wafer_data['Total'].sum()
    
    print(f"\n🔍 失效分析:")
    print(f"   总芯片数: {total_chips:,}")
    print(f"   总失效数: {total_failures:,}")
    print(f"   总良率: {((total_chips - total_failures) / total_chips * 100):.2f}%")
    
    # 分析参数数据
    if chart.cleaned_data is not None:
        params = chart.get_available_parameters()
        print(f"\n🔬 参数数据分析:")
        print(f"   可用参数数: {len(params)}")
        print(f"   Cleaned数据行数: {len(chart.cleaned_data):,}")
        print(f"   参数列表: {params[:5]}{'...' if len(params) > 5 else ''}")
    
    # 各批次统计
    print(f"\n📦 各批次统计:")
    lot_stats = chart.wafer_data.groupby('Lot_Short').agg({
        'Yield_Numeric': ['mean', 'std', 'count'],
        'Total': 'sum'
    }).round(2)
    
    for lot in lot_stats.index:
        mean_yield = lot_stats.loc[lot, ('Yield_Numeric', 'mean')]
        std_yield = lot_stats.loc[lot, ('Yield_Numeric', 'std')]
        wafer_count = int(lot_stats.loc[lot, ('Yield_Numeric', 'count')])
        total_chips = int(lot_stats.loc[lot, ('Total', 'sum')])
        
        print(f"   {lot}: 平均{mean_yield:.2f}%±{std_yield:.2f}%, {wafer_count}片, {total_chips:,}芯片")

if __name__ == "__main__":
    print("🧪 良率图表组件功能测试")
    print("=" * 50)
    
    try:
        # 基础功能测试
        test_yield_chart_functionality()
        
        # 参数图表专项测试
        test_parameter_charts()
        
        # 特定图表测试
        test_specific_chart_details()
        
        # 数据分析测试
        test_data_analysis()
        
        print("\n✅ 所有测试完成！")
        print("💡 提示: 生成的HTML图表可在浏览器中直接打开查看")
        print("📊 参数折线图已支持双层X轴和规格限制线")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc() 