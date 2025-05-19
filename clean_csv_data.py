#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSV数据清洗工具 - 重排字段顺序
"""

import os
import sys
import pandas as pd
import argparse
from datetime import datetime
from typing import Optional

def clean_csv_data(data_df: pd.DataFrame, output_dir: str, base_filename_part: str) -> Optional[str]:
    """
    清洗DataFrame数据，按照指定顺序重排字段，并保存到CSV。
    Lot_ID, Wafer_ID, Seq, Bin, X, Y, CONT, [优先参数], [其他参数]
    (No.U 列将被移除)
    
    Args:
        data_df: 输入的Pandas DataFrame
        output_dir: 输出目录路径
        base_filename_part: 用于构建输出文件名的基础部分 (如 Lot_ID)
    
    Returns:
        str: 输出文件路径, 或 None 如果失败或无数据.
    """
    if not isinstance(data_df, pd.DataFrame):
        print("输入不是有效的Pandas DataFrame。")
        return None
        
    if data_df.empty:
        print("输入的DataFrame为空，不进行保存。")
        return None

    df = data_df.copy()
    print(f"开始处理传入的DataFrame，原始形状: {df.shape}")
    
    # 移除可能存在的 'Unnamed: 0' 列
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    
    # 确保 Seq 列存在 (通常由上游处理，但保留作为健壮性检查)
    if 'Seq' not in df.columns:
        print("Warning: Column 'Seq' not found in DataFrame, adding default index-based sequence.")
        df['Seq'] = df.index + 1 if df.index.is_numeric() else range(1, len(df) + 1)
    
    # 显式移除 No.U 列（如果仍然存在）
    if 'No.U' in df.columns:
        df = df.drop(columns=['No.U'])
    
    # 验证关键列是否存在 (这些列应由调用者在DataFrame中提供)
    essential_cols_from_dcp = ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y', 'CONT']
    missing_cols = [col for col in essential_cols_from_dcp if col not in df.columns]
    if missing_cols:
        print(f"Critical Error: Columns {missing_cols} are missing in the DataFrame passed to clean_csv_data. These should be provided by the caller.")
        return None 
            
    # 列重排逻辑
    fixed_columns = ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y', 'CONT']
    # 获取 df 中实际存在的列，再进行排序和筛选
    current_df_columns = df.columns.tolist()
    
    other_columns = sorted([col for col in current_df_columns if col not in fixed_columns])
    
    new_column_order = fixed_columns.copy()
    # 确保 fixed_columns 中的列实际存在于 df 中，避免KeyError
    new_column_order = [col for col in new_column_order if col in current_df_columns]

    priority_params = ['IGSS0', 'IGSS1', 'IGSSR1', 'VTH', 'BVDSS1', 'BVDSS2', 'IDSS1', 'IDSS2', 'IGSS2', 'IGSSR2']
    for param in priority_params:
        if param in current_df_columns and param not in new_column_order:
            new_column_order.append(param)
    
    for col in other_columns: # other_columns 已经是从 current_df_columns 筛选和排序得到的
        if col not in new_column_order: # 确保不重复添加
            new_column_order.append(col)
    
    # 最终列顺序应该是 df 中实际存在的列，并按照 new_column_order 排序
    # 有些列可能在 new_column_order 中但不在 df.columns 中（例如，如果原始df就没有某些优先参数）
    final_columns = [col for col in new_column_order if col in current_df_columns]
    
    try:
        df = df[final_columns]
    except KeyError as e:
        print(f"Error during column reordering: {e}. Columns in df: {current_df_columns}. Attempted order: {final_columns}")
        return None

    # 格式化数值型数据
    for col in df.columns:
        if df[col].dtype in ['float64', 'float32']:
            df[col] = df[col].apply(lambda x: format_number(x))
    
    # 生成输出文件路径
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cleaned_filename = f"{base_filename_part}_cleaned_{timestamp}.csv"
    # 确保 output_dir 存在
    os.makedirs(output_dir, exist_ok=True)
    output_filepath = os.path.join(output_dir, cleaned_filename)
    
    try:
        df.to_csv(output_filepath, index=False)
        print(f"数据清洗完成，已保存到: {output_filepath}")
        return output_filepath
    except Exception as e:
        print(f"保存清洗后的CSV时出错: {str(e)}")
        return None

def format_number(value):
    """
    根据数值大小选择适当的格式
    """
    if pd.isna(value):
        return ""
    
    try:
        # 检查是否是接近0的小数，需要科学计数法
        if abs(value) < 0.0001 and value != 0:
            return f"{value:.2e}"
        # VTH, RDSON1 等通常保留2-3位小数
        elif abs(value) < 10 and value != 0:
            return f"{value:.2f}"
        # 其他普通数字
        else:
            return f"{value:.3g}"
    except:
        # 如果有任何格式化错误，返回原始值
        return value

def main():
    parser = argparse.ArgumentParser(description='CSV数据清洗工具 - (DataFrame input mode for testing)')
    parser.add_argument('-od', '--output_dir_test', help='Output directory for test', default="test_output_clean_csv")
    parser.add_argument('-bfn', '--base_filename_test', help='Base filename part for test', default="TEST_LOT_DF")
    
    args = parser.parse_args()

    sample_input_data = {
        'Lot_ID': ['TEST_LOT_DF'] * 5, 'Wafer_ID': ['W_DF_1'] * 5, 
        'Seq': range(1,6), 'Bin': [1,2,1,3,1],
        'X': [10,11,12,13,14], 'Y': [20,21,22,23,24], 'CONT': ['TypeA']*5, 
        'No.U': [101,102,103,104,105], # No.U 应该被移除
        'IGSS0': [0.1, 0.2, 0.15, 0.18, 0.12], 
        'VTH': [3.0, 3.1, 2.9, 3.05, 3.12],
        'ParamX': [10.0, 10.1, 10.2, 10.3, 10.4],
        'ParamA': [1,2,3,4,5]
    }
    test_df = pd.DataFrame(sample_input_data)
    
    print(f"独立测试: 使用示例DataFrame...")
    output_path = clean_csv_data(test_df, args.output_dir_test, args.base_filename_test)
    if output_path:
        print(f"独立测试成功，输出到: {output_path}")
    else:
        print(f"独立测试失败。")

if __name__ == "__main__":
    print("clean_csv_data.py - DataFrame input mode test.")
    main() 