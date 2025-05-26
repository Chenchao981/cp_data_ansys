#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析cleaned数据中的Lot_ID和Wafer_ID分布
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_lot_wafer_data():
    """分析Lot_ID和Wafer_ID的分布"""
    # 读取数据
    data_file = "output/FA54-5339-327A-250501@203_cleaned_20250523_153916.csv"
    df = pd.read_csv(data_file)
    
    print("=== 数据基本信息 ===")
    print(f"总行数: {len(df)}")
    print(f"列名: {list(df.columns)}")
    
    print("\n=== Lot_ID 分析 ===")
    unique_lots = df['Lot_ID'].unique()
    print(f"唯一Lot_ID数量: {len(unique_lots)}")
    print(f"Lot_ID列表: {unique_lots}")
    
    print("\n=== Wafer_ID 分析 ===")
    print(f"Wafer_ID范围: {df['Wafer_ID'].min()} ~ {df['Wafer_ID'].max()}")
    
    print("\n=== 每个Lot的Wafer分布 ===")
    lot_wafer_counts = df.groupby('Lot_ID')['Wafer_ID'].agg(['min', 'max', 'nunique'])
    print(lot_wafer_counts)
    
    print("\n=== 详细的Lot-Wafer对应关系 ===")
    for lot_id in unique_lots:
        lot_data = df[df['Lot_ID'] == lot_id]
        wafer_ids = sorted(lot_data['Wafer_ID'].unique())
        print(f"{lot_id}: Wafer {wafer_ids[0]} ~ {wafer_ids[-1]} (共{len(wafer_ids)}片)")
        print(f"  实际Wafer_ID: {wafer_ids}")
        
    print("\n=== 参数列表 ===")
    # 排除前几列的系统字段，显示测试参数
    param_columns = [col for col in df.columns if col not in ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y']]
    print(f"测试参数: {param_columns}")
    
    return df, unique_lots, param_columns

if __name__ == "__main__":
    analyze_lot_wafer_data() 