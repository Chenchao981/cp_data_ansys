# python_cp/yield_calculator.py
import pandas as pd
import numpy as np
import logging
from typing import Tuple, Optional, Dict, List

# 尝试相对导入数据类型定义
try:
    from .数据类型定义 import CPWafer, CPLot
except ImportError:
    # 处理直接运行或包结构问题
    logger_init_error = logging.getLogger(__name__)
    logger_init_error.warning("无法执行相对导入 '.数据类型定义'。请确保从包结构运行或调整路径。将使用占位符类。")
    # 定义占位符以便脚本基本可解析
    class CPWafer:
        def __init__(self, wafer_id: str, bin_data: Optional[np.ndarray] = None):
            self.wafer_id = wafer_id
            self.bin = bin_data

    class CPLot:
        def __init__(self, wafers: Optional[List[CPWafer]] = None, pass_bin: int = 1):
            self.wafers = wafers if wafers is not None else []
            self.pass_bin = pass_bin

logger = logging.getLogger(__name__)

def get_wafer_bin_counts(wafer: CPWafer) -> pd.Series:
    """计算并返回单个晶圆的 Bin 值统计 (每个 Bin 的数量)。

    Args:
        wafer (CPWafer): 晶圆对象。

    Returns:
        pd.Series: 以 Bin 值为索引，数量为值的 Series。如果无 Bin 数据则返回空 Series。
    """
    if wafer.bin is None or len(wafer.bin) == 0:
        return pd.Series(dtype=int)
    # 确保 bin 是 Series 以使用 value_counts
    bin_series = pd.Series(wafer.bin)
    # 移除 NaN 值进行计数
    return bin_series.dropna().value_counts().astype(int)

def calculate_wafer_yield(wafer: CPWafer, pass_bin_value: int = 1) -> Tuple[float, int, int]:
    """
    计算单个晶圆的良率。

    Args:
        wafer (CPWafer): 晶圆对象。
        pass_bin_value (int): 定义为 Pass 的 Bin 值。

    Returns:
        元组 (良率, Pass 数量, Total 数量)。良率是 0 到 1 之间的小数。
        如果无法计算（如无 Bin 数据），返回 (0.0, 0, 0)。
    """
    if wafer.bin is None or len(wafer.bin) == 0:
        return 0.0, 0, 0

    # 移除 NaN 值进行计算
    valid_bins = wafer.bin[~np.isnan(wafer.bin)]
    total_count = len(valid_bins)

    if total_count == 0:
        return 0.0, 0, 0

    pass_count = int(np.sum(valid_bins == pass_bin_value))
    yield_rate = pass_count / total_count if total_count > 0 else 0.0

    return yield_rate, pass_count, total_count

def calculate_lot_yield_summary(cp_lot: CPLot) -> pd.DataFrame:
    """
    计算整个 Lot 的良率汇总表，类似 VBA 的 ShowYield 输出。

    Args:
        cp_lot (CPLot): 包含所有 Wafer 数据的批次对象。

    Returns:
        Pandas DataFrame 包含每片 Wafer 及汇总行的良率信息。
        列包括: Wafer, Yield, Total, Pass, BinX, BinY, ...
        如果无 Wafer 数据则返回空 DataFrame。
    """
    if not cp_lot.wafers:
        return pd.DataFrame()

    all_bin_counts = []
    wafer_yields = []
    all_bins_set = set()

    # 1. 计算每个 wafer 的 bin 统计和良率
    for wafer in cp_lot.wafers:
        yield_rate, pass_count, total_count = calculate_wafer_yield(wafer, cp_lot.pass_bin)
        bin_counts = get_wafer_bin_counts(wafer)
        all_bin_counts.append(bin_counts)
        wafer_yields.append({
            'Wafer': f"{wafer.wafer_id}#", # VBA 风格加 # 号
            'Yield': yield_rate,
            'Total': total_count,
            'Pass': pass_count
        })
        all_bins_set.update(bin_counts.index)

    # 2. 确定所有 Bin 列并排序 (Pass Bin 在前)
    if not all_bins_set:
        # 如果没有任何 bin 数据
        return pd.DataFrame(wafer_yields, columns=['Wafer', 'Yield', 'Total', 'Pass'])

    # 尝试将 bin 值转换为数值类型进行排序，处理非数值类型
    numeric_bins = []
    non_numeric_bins = []
    for b in all_bins_set:
        try:
            numeric_bins.append(float(b))
        except (ValueError, TypeError):
            non_numeric_bins.append(b)

    sorted_numeric_bins = sorted(numeric_bins)
    sorted_non_numeric_bins = sorted(non_numeric_bins)
    
    # 组合排序后的 bins，确保 Pass Bin (如果存在且为数值) 在最前
    final_sorted_bins = []
    pass_bin_float = float(cp_lot.pass_bin)
    if pass_bin_float in sorted_numeric_bins:
         final_sorted_bins.append(cp_lot.pass_bin) # Use original pass_bin value
         sorted_numeric_bins.remove(pass_bin_float)
         
    # 转换数值 bin 回原始类型 (int 如果可能)
    sorted_bins_typed = [int(b) if b.is_integer() else b for b in sorted_numeric_bins]
    final_sorted_bins.extend(sorted_bins_typed)
    final_sorted_bins.extend(sorted_non_numeric_bins)
    

    # 3. 构建 DataFrame 数据
    summary_data = []
    for i, wafer_info in enumerate(wafer_yields):
        row_data = wafer_info.copy()
        wafer_bins = all_bin_counts[i]
        for bin_val in final_sorted_bins:
            col_name = f"Bin{bin_val}" if bin_val != cp_lot.pass_bin else "Pass" # Pass 列已存在
            if col_name != "Pass": # Pass 列的值已在 wafer_info 中
                row_data[col_name] = wafer_bins.get(bin_val, 0)
        summary_data.append(row_data)

    # 4. 创建 DataFrame
    # 定义列顺序，确保 Pass 在 Total 之后
    base_cols = ['Wafer', 'Yield', 'Total', 'Pass']
    other_bin_cols = [f"Bin{b}" for b in final_sorted_bins if b != cp_lot.pass_bin]
    final_cols = base_cols + other_bin_cols

    summary_df = pd.DataFrame(summary_data, columns=final_cols)
    summary_df = summary_df.fillna(0).astype({col: int for col in other_bin_cols + ['Total', 'Pass']})

    # 5. 添加汇总行 ("All")
    if not summary_df.empty:
        total_row = {'Wafer': 'All'}
        # 计算各列总和 (数值列)
        numeric_cols_to_sum = ['Total', 'Pass'] + other_bin_cols
        for col in numeric_cols_to_sum:
            if col in summary_df.columns:
                 total_row[col] = summary_df[col].sum()
            else:
                 total_row[col] = 0 # 以防万一某列在某些情况下不存在
                 
        pass_total = total_row['Pass']
        total_total = total_row['Total']
        
        # 计算总良率
        total_row['Yield'] = pass_total / total_total if total_total > 0 else 0.0
        
        # 将 total_row 转换为 DataFrame 以便 concat
        total_df = pd.DataFrame([total_row], columns=final_cols)
        summary_df = pd.concat([summary_df, total_df], ignore_index=True)

    return summary_df

# --- 示例用法 (可选，用于独立测试) ---
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("运行 Yield Calculator 模块示例...")

    # 创建模拟 Wafer
    wafer1_bins = np.array([1, 1, 2, 1, 3, 1, np.nan, 2, 1])
    wafer2_bins = np.array([1, 2, 2, 1, 1, np.nan, np.nan, 2, 2, 4])
    wafer1 = CPWafer(wafer_id="W01", bin_data=wafer1_bins)
    wafer2 = CPWafer(wafer_id="W02", bin_data=wafer2_bins)

    # 创建模拟 Lot
    lot = CPLot(wafers=[wafer1, wafer2], pass_bin=1)

    # 测试 Wafer Bin 计数
    logger.info("--- Wafer Bin Counts ---")
    counts1 = get_wafer_bin_counts(wafer1)
    logger.info(f"Wafer 1 Bin Counts:\n{counts1}")
    counts2 = get_wafer_bin_counts(wafer2)
    logger.info(f"Wafer 2 Bin Counts:\n{counts2}")

    # 测试 Wafer 良率计算
    logger.info("--- Wafer Yield ---")
    yield1, pass1, total1 = calculate_wafer_yield(wafer1, lot.pass_bin)
    logger.info(f"Wafer 1 Yield: {yield1:.2%}, Pass: {pass1}, Total: {total1}")
    yield2, pass2, total2 = calculate_wafer_yield(wafer2, lot.pass_bin)
    logger.info(f"Wafer 2 Yield: {yield2:.2%}, Pass: {pass2}, Total: {total2}")

    # 测试 Lot 良率汇总
    logger.info("--- Lot Yield Summary ---")
    summary_table = calculate_lot_yield_summary(lot)
    logger.info(f"Lot Yield Summary Table:\n{summary_table.to_string()}")

    # 测试空 Lot
    empty_lot = CPLot()
    empty_summary = calculate_lot_yield_summary(empty_lot)
    logger.info(f"Empty Lot Yield Summary Table (should be empty):\n{empty_summary}") 