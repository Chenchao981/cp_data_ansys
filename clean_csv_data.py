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
    Lot_ID, Wafer_ID, Seq, Bin, X, Y, CONT, [优先参数], [其他参数]
    
    Args:
        input_file: 输入CSV文件路径
        output_file: 输出CSV文件路径（如果不指定，则自动生成）
    
    Returns:
        str: 输出文件路径
    """
    print(f"开始处理文件: {input_file}")
    
    # 读取CSV文件
    try:
        df = pd.read_csv(input_file)
        print(f"成功读取CSV文件，形状: {df.shape}")
        print(f"Debug: df.columns after initial read: {df.columns.tolist()}") # DEBUG
    except Exception as e:
        print(f"读取文件时出错: {str(e)}")
        return None
    
    # 移除可能存在的 'Unnamed: 0' 列，如果它是由之前的索引写入产生的
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
        print(f"Debug: Dropped 'Unnamed: 0' column. New columns: {df.columns.tolist()}") # DEBUG

    # 创建或确保序号列（Seq）存在
    if 'Seq' not in df.columns:
        df['Seq'] = df.index + 1 if df.index.is_numeric() else range(1, len(df) + 1)
    
    # 确保必需的列存在
    required_base_cols = ['Bin', 'X', 'Y', 'No.U'] 
    for col in required_base_cols:
        if col not in df.columns:
            print(f"Warning: Column '{col}' not found, adding with default value 0 or 1.")
            if col == 'No.U':
                df[col] = 1  # 默认值为1
            else:
                df[col] = 0  # 默认值为0
                
    if 'CONT' not in df.columns:
        print(f"Warning: Column 'CONT' not found, adding with default value (blank).")
        df['CONT'] = ""  # 默认值为空字符串
    
    # 确保 Lot_ID 列存在 (通常由 clean_dcp_data.py 提供)
    if 'Lot_ID' not in df.columns:
        print(f"Warning: Column 'Lot_ID' not found, attempting to extract from filename or defaulting.")
        # 尝试从文件名提取，或设置默认值
        filename_parts = os.path.basename(input_file).split('_')
        df['Lot_ID'] = filename_parts[0] if filename_parts else "Unknown_Lot"

    # 重命名旧的Wafer列为Wafer_ID（如果存在且Wafer_ID不存在）
    if 'Wafer' in df.columns and 'Wafer_ID' not in df.columns:
        df = df.rename(columns={'Wafer': 'Wafer_ID'})
    # 确保Wafer_ID列存在
    elif 'Wafer_ID' not in df.columns and df.index.name == 'WaferID': # 兼容旧的WaferID索引名
        df = df.reset_index()
        df = df.rename(columns={'WaferID': 'Wafer_ID'})
    elif 'Wafer_ID' not in df.columns:
        print("Warning: Wafer_ID column not found, trying to extract from file name.")
        filename = os.path.basename(input_file)
        # 尝试从文件名提取，例如 FA53-5465-305A-250303@203_001_someotherpart.csv -> 001
        # 这部分逻辑可能需要根据实际文件名格式调整
        wafer_id_from_filename = "Unknown_Wafer"
        parts = filename.split('_')
        if len(parts) > 1 and '@' in parts[0]: # 假设格式如 Lot@Wafer_...
            lot_wafer_part = parts[0].split('@')
            if len(lot_wafer_part) > 1:
                wafer_id_from_filename = lot_wafer_part[1]
        elif len(parts) > 1 : # 备用逻辑，如果文件名是 Wafer_...
             wafer_id_from_filename = parts[0]

        df['Wafer_ID'] = wafer_id_from_filename
    
    # 确定列的新顺序
    fixed_columns = ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y', 'CONT']
    print(f"Debug: fixed_columns: {fixed_columns}") # DEBUG
    
    # 获取其他所有列（除了固定列）并按字母排序
    other_columns = sorted([col for col in df.columns if col not in fixed_columns])
    print(f"Debug: df.columns: {df.columns.tolist()}") # DEBUG
    print(f"Debug: other_columns: {other_columns}") # DEBUG
    
    # 新的列顺序
    new_column_order = fixed_columns.copy()
    
    # 添加优先参数列
    priority_params = ['IGSS0', 'IGSS1', 'IGSSR1', 'VTH', 'BVDSS1', 'BVDSS2', 'IDSS1', 'IDSS2', 'IGSS2', 'IGSSR2']
    for param in priority_params:
        if param in df.columns and param not in new_column_order:
            new_column_order.append(param)
    
    # 添加其他列
    for col in other_columns:
        if col not in new_column_order:
            new_column_order.append(col)
    
    print(f"Debug: new_column_order after additions: {new_column_order}") # DEBUG
    # 只保留存在的列
    final_columns = [col for col in new_column_order if col in df.columns]
    print(f"Debug: final_columns: {final_columns}") # DEBUG
    
    # 重排列
    df = df[final_columns]
    
    # 格式化数值型数据，特别是科学计数法的数据
    for col in df.columns:
        if df[col].dtype in ['float64', 'float32']:
            # 尝试保留原始格式
            df[col] = df[col].apply(lambda x: format_number(x))
    
    # 生成输出文件路径（如果未指定）
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        basename = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"{basename}_cleaned_{timestamp}.csv"
    
    # 保存到CSV文件
    df.to_csv(output_file, index=False)
    print(f"数据清洗完成，已保存到: {output_file}")
    
    return output_file

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