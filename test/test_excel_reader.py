import sys
import os
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# 创建日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 控制台处理器
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(handler)

def read_excel_format_file(file_path: str) -> pd.DataFrame:
    """
    读取Excel格式的文件（即使扩展名是.TXT）
    
    Args:
        file_path: 文件路径
        
    Returns:
        pd.DataFrame: 读取的数据
    """
    logger.info(f"尝试使用pandas.read_excel读取文件: {os.path.basename(file_path)}")
    
    try:
        # 使用备用方法: 先读取整个文件，然后找出结构
        raw_df = pd.read_excel(file_path, header=None)
        logger.info(f"成功读取整个文件，形状: {raw_df.shape}")
        
        # 提取元数据
        lot_id = None
        wafer_id = None
        for i in range(min(5, raw_df.shape[0])):
            if pd.notna(raw_df.iloc[i, 0]):
                cell_text = str(raw_df.iloc[i, 0]).lower()
                if 'lot' in cell_text and pd.notna(raw_df.iloc[i, 1]):
                    lot_id = raw_df.iloc[i, 1]
                elif 'wafer' in cell_text and pd.notna(raw_df.iloc[i, 1]):
                    wafer_id = raw_df.iloc[i, 1]
        
        logger.info(f"提取到元数据: Lot ID={lot_id}, Wafer ID={wafer_id}")
        
        # 查找表头行 - 查找包含 "No.U", "X", "Y", "Bin" 的行
        header_row = None
        for i in range(raw_df.shape[0]):
            row_values = [str(x).strip() if pd.notna(x) else '' for x in raw_df.iloc[i]]
            row_text = ' '.join(row_values)
            
            # 输出前20行，帮助调试
            if i < 20:
                logger.debug(f"行 {i+1}: {row_text[:100]}")
            
            # 检查是否包含关键词
            if any(keyword in row_text for keyword in ['No.U', 'Bin']) and 'X' in row_values and 'Y' in row_values:
                header_row = i
                logger.info(f"找到表头行 {i+1}: {row_text[:100]}")
                break
        
        if header_row is None:
            logger.error("无法找到包含 'No.U', 'X', 'Y', 'Bin' 的表头行")
            
            # 尝试直接使用第6行（索引5）作为表头，基于用户提供的例子
            if raw_df.shape[0] > 6:
                header_row = 6
                logger.warning(f"使用默认的第7行作为表头: {' '.join([str(x) for x in raw_df.iloc[6] if pd.notna(x)])}")
            else:
                return None
        
        # 查找数据起始行 - 第一列是数字的行
        data_row = None
        for i in range(header_row + 1, raw_df.shape[0]):
            # 尝试将第一列转换为整数
            if pd.notna(raw_df.iloc[i, 0]):
                try:
                    int(float(raw_df.iloc[i, 0]))  # 先转为float再转为int，处理可能的浮点数表示
                    data_row = i
                    logger.info(f"找到数据起始行 {i+1}: {raw_df.iloc[i, 0]}")
                    break
                except (ValueError, TypeError):
                    pass
        
        if data_row is None:
            logger.error("无法找到数据起始行")
            return None
        
        # 提取列名
        header = []
        for j in range(raw_df.shape[1]):
            if pd.notna(raw_df.iloc[header_row, j]) and str(raw_df.iloc[header_row, j]).strip():
                header.append(str(raw_df.iloc[header_row, j]).strip())
            else:
                # 查找前一个非空列名，添加后缀
                if j > 0 and len(header) > 0 and header[-1] != f'Unnamed_{j-1}':
                    header.append(f'{header[-1]}_{j-header.index(header[-1])}')
                else:
                    header.append(f'Unnamed_{j}')
        
        logger.info(f"提取到的表头: {header}")
        
        # 提取数据
        data = raw_df.iloc[data_row:].copy()
        
        # 确保列数匹配
        if len(header) > data.shape[1]:
            header = header[:data.shape[1]]
        elif len(header) < data.shape[1]:
            for j in range(len(header), data.shape[1]):
                header.append(f'Extra_{j}')
        
        data.columns = header
        
        # 添加元数据
        data.attrs['lot_id'] = lot_id
        data.attrs['wafer_id'] = wafer_id
        data.attrs['header_row'] = header_row
        data.attrs['data_row'] = data_row
        
        logger.info(f"成功提取数据，形状: {data.shape}")
        logger.debug(f"数据前5行:\n{data.head()}")
        
        return data
        
    except Exception as e:
        logger.exception(f"读取文件失败: {str(e)}")
        return None

def analyze_cp_data(df: pd.DataFrame, pass_bin: int = 1) -> None:
    """
    分析CP数据
    
    Args:
        df: 包含CP数据的DataFrame
        pass_bin: 表示良品的bin值，默认为1
    """
    if df is None or df.empty:
        logger.error("无数据可分析")
        return
    
    print("\n=== CP数据分析 ===")
    print(f"数据形状: {df.shape}")
    
    # 显示列名
    print("\n列名列表:")
    print(df.columns.tolist())
    
    # 显示前5行数据
    print("\n前5行数据:")
    print(df.head())
    
    # 识别bin列
    bin_col = None
    for col in df.columns:
        if 'bin' in str(col).lower():
            bin_col = col
            break
    
    if bin_col:
        # 计算良率
        df_bin = df[bin_col].astype(float, errors='ignore')
        pass_count = sum(df_bin == pass_bin)
        total_count = len(df_bin)
        yield_rate = pass_count / total_count * 100 if total_count > 0 else 0
        print(f"\nBin列: {bin_col}")
        print(f"良率: {yield_rate:.2f}% ({pass_count}/{total_count})")
        
        # Bin分布
        bin_counts = df_bin.value_counts().sort_index()
        print("\nBin分布:")
        for bin_value, count in bin_counts.items():
            print(f"  Bin {bin_value}: {count} 颗芯片 ({count/total_count*100:.2f}%)")
    else:
        print("\n未找到Bin列，无法计算良率")
    
    # 检查参数列（在Bin列右边的所有列）
    if bin_col:
        bin_idx = list(df.columns).index(bin_col)
        param_cols = list(df.columns)[bin_idx+1:]
        print(f"\n识别到的参数列（Bin列右侧的列）: {len(param_cols)}个")
        for i, col in enumerate(param_cols[:10]):  # 只显示前10个
            print(f"  参数{i+1}: {col}")
        if len(param_cols) > 10:
            print(f"  ... 还有{len(param_cols)-10}个参数（总计{len(param_cols)}个）")
        
        # 对数值型参数进行基本统计
        print("\n参数统计（前5个数值型参数）:")
        num_params_analyzed = 0
        for col in param_cols:
            try:
                if num_params_analyzed >= 5:
                    break
                    
                # 尝试转换为数值型
                param_data = pd.to_numeric(df[col], errors='coerce')
                if param_data.notna().sum() > 0:  # 如果有有效数值
                    num_params_analyzed += 1
                    print(f"\n  参数: {col}")
                    print(f"    最小值: {param_data.min()}")
                    print(f"    最大值: {param_data.max()}")
                    print(f"    平均值: {param_data.mean()}")
                    print(f"    标准差: {param_data.std()}")
            except Exception as e:
                pass  # 跳过无法处理的列
    
    # 检查预期的特定参数是否存在
    expected_params = [
        "CONT", "IGSS0", "IGSS1", "IGSSR1", "BVDSS1", "BVDSS2", "DELTABV", 
        "IDSS1", "VTH", "RDSON1", "VFSDS", "IGSS2", "IGSSR2", "IDSS2"
    ]
    
    print("\n预期参数检查:")
    found_params = []
    missing_params = []
    
    for param in expected_params:
        param_found = False
        for col in df.columns:
            if param == str(col) or param in str(col):
                print(f"  [已找到] {param} (列名: {col})")
                found_params.append(param)
                param_found = True
                break
        
        if not param_found:
            print(f"  [未找到] {param}")
            missing_params.append(param)
    
    print(f"\n找到 {len(found_params)}/{len(expected_params)} 个预期参数")
    
    # 总结
    print("\n=== 数据分析总结 ===")
    print(f"总芯片数: {len(df)}")
    if bin_col:
        print(f"良率: {yield_rate:.2f}%")
    print(f"参数列数: {len(param_cols) if 'param_cols' in locals() else '未知'}")
    print(f"预期参数匹配率: {len(found_params)}/{len(expected_params)} ({len(found_params)/len(expected_params)*100:.1f}%)")


def main():
    # 文件路径
    file_path = os.path.join(project_root, "data", "FA53-5465-305A-250303@203_001", "FA53-5465-305A-250303@203_001.TXT")
    
    logger.info(f"测试文件路径: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return
    
    # 读取数据
    df = read_excel_format_file(file_path)
    
    # 分析数据
    if df is not None and not df.empty:
        analyze_cp_data(df)
    else:
        logger.error("未能读取到有效数据")

if __name__ == "__main__":
    main() 