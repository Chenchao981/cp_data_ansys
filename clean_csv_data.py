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

def clean_csv_data(input_file, output_file=None):
    """
    清洗CSV数据，按照指定顺序重排字段：
    Wafer, Seq, Bin, X, Y, CONT, [其他参数]
    
    Args:
        input_file: 输入CSV文件路径
        output_file: 输出CSV文件路径（如果不指定，则自动生成）
    
    Returns:
        str: 输出文件路径
    """
    print(f"开始处理文件: {input_file}")
    
    # 读取CSV文件，注意忽略索引列
    try:
        df = pd.read_csv(input_file, index_col=0)
        print(f"成功读取CSV文件，形状: {df.shape}")
    except Exception as e:
        print(f"读取文件时出错: {str(e)}")
        return None
    
    # 创建序号列（Seq）
    df['Seq'] = df.index + 1
    
    # 确保必需的列存在
    # Ensure 'WaferID' is present (it should be from the parsing script)
    # Ensure 'CONT' is present, if not, add it with a default value (e.g., 0 or NaN)
    required_base_cols = ['WaferID', 'Bin', 'X', 'Y'] # CONT is handled specially if missing
    for col in required_base_cols:
        if col not in df.columns:
            if col == 'WaferID':
                # This case should ideally not happen if input CSV is correct
                print(f"Warning: Column 'WaferID' not found, adding with default value 1.")
                df['WaferID'] = 1 
            else:
                print(f"Warning: Column '{col}' not found, adding with default value 0.")
                df[col] = 0
                
    if 'CONT' not in df.columns:
        print(f"Warning: Column 'CONT' not found, adding with default value 0.")
        df['CONT'] = 0 # Default value for CONT if missing
    
    # No longer renaming WaferID to Wafer. We want 'WaferID'.
    # if 'WaferID' in df.columns:
    #     df = df.rename(columns={'WaferID': 'Wafer'})
    
    # 确定列的新顺序
    fixed_columns = ['WaferID', 'Seq', 'Bin', 'X', 'Y', 'CONT']
    
    # 获取其他所有列（除了固定列）并按字母排序
    other_columns = sorted([col for col in df.columns if col not in fixed_columns])
    
    # 新的列顺序
    new_column_order = fixed_columns + other_columns
    
    # 重排列
    df = df[new_column_order]
    
    # 生成输出文件路径（如果未指定）
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        basename = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"{basename}_cleaned_{timestamp}.csv"
    
    # 保存到CSV文件
    df.to_csv(output_file, index=False)
    print(f"数据清洗完成，已保存到: {output_file}")
    
    return output_file

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CSV数据清洗工具 - 重排字段顺序')
    parser.add_argument('input_file', help='输入CSV文件路径')
    parser.add_argument('-o', '--output_file', help='输出CSV文件路径（可选）')
    
    args = parser.parse_args()
    
    # 处理文件
    clean_csv_data(args.input_file, args.output_file)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        # 如果没有命令行参数，使用默认文件
        input_file = "output/FA53_20250513_164637.csv"
        clean_csv_data(input_file) 