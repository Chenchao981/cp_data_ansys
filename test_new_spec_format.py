#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试新的JT spec文件列格式输出

模拟生成期望的spec格式
"""

import pandas as pd
import sys
from pathlib import Path

# 模拟CPParameter类
class MockCPParameter:
    def __init__(self, id, unit=None, sl=None, su=None):
        self.id = id
        self.unit = unit
        self.sl = sl
        self.su = su

def create_spec_dataframe_new_format(params):
    """
    新的列格式spec生成逻辑（测试版本）
    """
    if not params:
        return pd.DataFrame()

    # 构建列格式的数据
    data = {}
    
    # 第一列为行标识（去掉Parameter行）
    data['Parameter'] = ['Unit', 'LimitL', 'LimitU']
    
    # 为每个参数添加一列
    for param in params:
        param_data = [
            param.unit if param.unit is not None else "",  # 单位
            param.sl if param.sl is not None else "",  # 下限
            param.su if param.su is not None else ""   # 上限
        ]
        data[param.id] = param_data
    
    # 创建DataFrame
    spec_df = pd.DataFrame(data)
    
    return spec_df

def main():
    """主函数：测试新格式"""
    
    print("🧪 测试新的JT spec文件列格式")
    print("-" * 50)
    
    # 模拟JT参数数据（基于您提供的信息）
    mock_params = [
        MockCPParameter("TEST_NUM", None, None, None),
        MockCPParameter("UIS_KELVIN", "V", -1, 1),
        MockCPParameter("UIS_BVDSS", "V", 20.00, 80.00),
        MockCPParameter("UIS_ID17", "A", 16.500, 17.500),
        MockCPParameter("UIS_E", "mJ", None, None),
        MockCPParameter("CONT1", "V", -0.500, 0.500),
        MockCPParameter("VTH0.25", "V", 2.0000, 4.0000),
        MockCPParameter("VTH1", "V", 2.0000, 4.0000),
        MockCPParameter("BVDSS0.25", "V", 42.000, None),
        MockCPParameter("BVDSS1", "V", 42.000, None),
        MockCPParameter("IDSS40", "nA", 0.000, 200.000),
        MockCPParameter("IGSS25", "nA", 0.000, 200.000),
        MockCPParameter("ISGS25", "nA", -200.000, 0.000),
        MockCPParameter("IGSS20", "nA", 0.000, 100.000),
        MockCPParameter("ISGS20", "nA", -100.000, 0.000),
        MockCPParameter("RDSON1", "mOhm", 0.000, 0.950),
        MockCPParameter("VFSD", "V", 0.000, 1.200),
        MockCPParameter("IDSS35", "nA", 0.000, 100.000),
        MockCPParameter("IGSS10", "nA", 0.000, 100.000),
        MockCPParameter("ISGS10", "nA", -100.000, 0.000),
        MockCPParameter("VTH2 0.25", "V", 2.0000, 4.0000),
        MockCPParameter("DELTA-BV", "", -1.00, 1.00),
        MockCPParameter("DELTA-VTH", "", 0.00, 0.50),
    ]
    
    print(f"📊 模拟参数数量: {len(mock_params)}")
    
    # 生成新格式的spec DataFrame
    spec_df = create_spec_dataframe_new_format(mock_params)
    
    print(f"✅ 生成列格式spec DataFrame: {spec_df.shape}")
    
    # 显示结果
    print("\n📋 新格式spec文件预览:")
    print("=" * 100)
    
    # 设置pandas显示选项以便查看完整输出
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 10)
    
    print(spec_df.to_string(index=False))
    
    # 保存到文件
    output_file = "output/FA44-4149_spec_new_format_test.csv"
    spec_df.to_csv(output_file, index=False)
    print(f"\n💾 已保存到文件: {output_file}")
    
    # 显示期望格式对比
    print("\n📝 期望的格式示例:")
    print("Parameter,TEST_NUM,UIS_KELVIN,UIS_BVDSS,UIS_ID17,UIS_E,CONT1,...")
    print("Unit,,V,V,A,mJ,V,...")
    print("LimitL,,-1,20.00,16.500,,-0.500,...")
    print("LimitU,,1,80.00,17.500,,0.500,...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())