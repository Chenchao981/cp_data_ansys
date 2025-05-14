#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Excel TXT Reader示例脚本
=======================

本示例演示如何使用ExcelTXTReader读取伪装成TXT的Excel格式数据文件，
并进行数据清洗和初步分析。
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 设置日志格式
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入CP数据处理模块
from cp_data_processor.readers import create_reader
from cp_data_processor.readers.excel_txt_reader import ExcelTXTReader
from cp_data_processor.data_models.cp_data import CPLot, CPWafer
from cp_data_processor.processing.data_transformer import DataTransformer
from cp_data_processor.analysis.summary_stats import SummaryStats # 新增导入
from cp_data_processor.readers.dcp_reader import DCPReader

def perform_data_analysis_and_save_csvs(lot: CPLot, output_dir: Path):
    """
    对清洗后的数据进行分析，并输出多个csv文件
    """
    if not lot or not lot.wafers:
        logger.warning("Lot数据为空或没有晶圆数据，跳过数据分析和CSV保存步骤。")
        return

    logger.info(f"开始对Lot {lot.lot_id} 进行数据分析并保存CSV文件...")

    # 1. 保存清洗后的合并数据
    cleaned_df_full = lot.combined_data  # 替换原来的 get_all_data()
    if cleaned_df_full is None or cleaned_df_full.empty:
        logger.error("CPLot.combined_data 为空，无法输出清洗后数据！")
        return
    
    cleaned_df = cleaned_df_full.copy() # 操作副本

    # 1. 保存清洗后的合并数据 (_combined_data.csv)
    try:
        logger.info(f"准备生成 {lot.lot_id}_combined_data.csv ...")
        # df_to_save = cleaned_df.copy() # cleaned_df已经是combined_data的副本
        # df_to_save.insert(0, 'LotID', lot.lot_id) # LotID 列已经由 CPLot.combine_data_from_wafers() 添加，且值来自 wafer.source_lot_id
                                                # 所以这里不再需要插入 CPLot 对象的 lot_id

        # 确保列的顺序是期望的，特别是 LotID, wafer_id 等在前面
        # CPLot.combine_data_from_wafers() 已经处理了列顺序
        # 但如果需要强制特定顺序，可以在这里重新排序列
        # desired_order = ['LotID', 'wafer_id', 'seq', 'Bin', 'X', 'Y'] # 示例，Bin,X,Y的大小写需匹配实际列名
        # param_cols_sorted = sorted([col for col in cleaned_df.columns if col not in desired_order and col not in ['CONT']])
        # final_columns = desired_order + ['CONT'] + param_cols_sorted
        # final_columns = [col for col in final_columns if col in cleaned_df.columns] # 确保列存在
        # df_to_save_ordered = cleaned_df[final_columns]

        # 直接使用 cleaned_df，因为 LotID 和顺序已在 CPLot 中处理
        df_to_save = cleaned_df 

        output_combined_filename = f"{lot.lot_id}_combined_data.csv"
        output_combined_file = output_dir / output_combined_filename
        df_to_save.to_csv(output_combined_file, index=False)
        logger.info(f"清洗后的合并数据已保存到: {output_combined_file}")

    except Exception as e:
        logger.exception(f"保存 {lot.lot_id}_combined_data.csv 时出错: {e}")

    # 实例化 SummaryStats (使用包含清洗后数据的 lot 对象)
    stats_analyzer = SummaryStats(lot)

    # 2. 保存基本统计量 (all_lots_combined_summary.csv)
    try:
        logger.info(f"准备为Lot {lot.lot_id} 生成或更新 all_lots_combined_summary.csv ...")
        stats_analyzer.calculate_basic_stats()
        summary_df = lot.summary_stats
        if summary_df is not None and not summary_df.empty:
            # summary_df 的 LotID 列将是 CPLot 对象的 lot_id (例如 "FA53")
            # 这符合我们对 all_lots_combined_summary.csv 的预期，即按批次（如FA53, NCEH等）汇总
            summary_df_with_lotid = summary_df.copy()
            summary_df_with_lotid.insert(0, 'LotID', lot.lot_id) 
            
            output_summary_global_filename = "all_lots_combined_summary.csv"
            output_summary_file = output_dir / output_summary_global_filename
            
            summary_df_with_lotid.to_csv(output_summary_file, index=False)
            logger.info(f"基本统计量已保存到: {output_summary_file}")
        else:
            logger.warning(f"Lot {lot.lot_id} 的统计摘要数据为空，无法保存。")
    except Exception as e:
        logger.exception(f"保存 all_lots_combined_summary.csv 时出错: {e}")

    # 3. 保存良率信息 (_yield.csv)
    try:
        logger.info(f"准备生成 {lot.lot_id}_yield.csv ...")
        yield_df = lot.calculate_yield_summary() # 假设这个方法现在也考虑了新的 LotID 结构
                                              # 或者它操作的是 wafer 级别的良率，然后我们按 wafer.source_lot_id 分组
                                              # 目前 calculate_yield_summary 内部可能需要调整以正确处理多 LotID 的情况
                                              # 但为了简化，我们先假设它能工作，或者只针对 CPLot.lot_id 这一级
                                              # 如果要在 _yield.csv 中体现每个文件的R2C2 LotID，则该函数和这里的调用需要修改
        if yield_df is not None and not yield_df.empty:
            # 当前 yield_df 应该是基于 CPLot.wafers 计算的，每个 wafer 有自己的 wafer_id 和 source_lot_id
            # 我们需要确保输出的 _yield.csv 包含正确的 LotID (来自 wafer.source_lot_id) 和 WaferID
            # 假设 calculate_yield_summary() 返回的 DataFrame 已经包含了 wafer_id
            # 我们需要从 lot.wafers 映射 source_lot_id 到 yield_df
            
            # 创建 wafer_id 到 source_lot_id 的映射
            wafer_to_source_lot_map = {w.wafer_id: w.source_lot_id for w in lot.wafers}
            
            # 将 source_lot_id 添加到 yield_df
            # 假设 yield_df 中有一列是 'WaferID' 或类似的，并且与 CPWafer.wafer_id 对应
            # 找到与 wafer_id 匹配的列名，可能需要更灵活的匹配
            wafer_id_col_in_yield = 'WaferID' # 与CPLot.combine_data_from_wafers中的命名一致
            if wafer_id_col_in_yield in yield_df.columns:
                yield_df_with_lotid = yield_df.copy()
                yield_df_with_lotid.insert(0, 'LotID', yield_df_with_lotid[wafer_id_col_in_yield].map(wafer_to_source_lot_map))
            else:
                logger.warning(f"在 {lot.lot_id}_yield.csv 的源数据中未找到WaferID列，无法添加精确的LotID(R2C2)")
                yield_df_with_lotid = yield_df.copy()
                yield_df_with_lotid.insert(0, 'LotID', lot.lot_id) # 回退到使用批次LotID

            # 调整列顺序
            desired_yield_cols = ['LotID', 'WaferID', 'Yield', 'Total', 'Pass']
            # 提取Bin列，通常是 'BinX' 格式
            bin_cols = sorted([col for col in yield_df_with_lotid.columns if col.startswith('Bin') and col not in desired_yield_cols])
            final_yield_columns = [col for col in desired_yield_cols + bin_cols if col in yield_df_with_lotid.columns]
            df_to_save_yield = yield_df_with_lotid[final_yield_columns]

            output_yield_filename = f"{lot.lot_id}_yield.csv"
            output_yield_file = output_dir / output_yield_filename
            df_to_save_yield.to_csv(output_yield_file, index=False)
            logger.info(f"良率信息已保存到: {output_yield_file}")
        else:
            logger.warning(f"Lot {lot.lot_id} 的良率数据为空，无法保存。")
    except Exception as e:
        logger.exception(f"保存 {lot.lot_id}_yield.csv 时出错: {e}")

    # 4. 保存正态性检验结果 (_normality_test_results.csv - 保持per-lot)
    try:
        logger.info(f"准备为Lot {lot.lot_id} 生成正态性检验结果文件 ...")
        normality_df = stats_analyzer.test_normality()
        if normality_df is not None and not normality_df.empty:
            output_normality_file = output_dir / f"{lot.lot_id}_normality_test_results.csv"
            normality_df.to_csv(output_normality_file, index=False)
            logger.info(f"Lot {lot.lot_id} 的正态性检验结果已保存到: {output_normality_file}")
        else:
            logger.warning(f"Lot {lot.lot_id} 未生成正态性检验结果。")
    except Exception as e:
        logger.exception(f"保存 {lot.lot_id}_normality_test_results.csv 时出错: {e}")
    
    logger.info(f"Lot {lot.lot_id} 的数据分析和CSV保存完成。")

def main():
    """主函数"""
    # 获取示例数据文件路径
    data_dir = Path("D:/data/rawdata")
    
    # 递归查找所有TXT文件
    txt_files = list(data_dir.glob("**/*.TXT"))
    if not txt_files:
        logger.error(f"在 {data_dir} 中未找到TXT文件")
        return
    
    print(f"发现 {len(txt_files)} 个TXT文件:")
    for file in txt_files:
        print(f" - {file.name}")
    
    # 直接用DCPReader读取所有TXT文件
    print("\n----------- 开始读取数据 -----------")
    reader = DCPReader([str(f) for f in txt_files])
    lot = reader.read()

    if not lot or not lot.wafers: # 检查lot是否成功读取并且包含数据
        logger.error("未能成功读取Lot数据或Lot中没有晶圆数据，无法继续处理。")
        return
        
    print_lot_info(lot)
    
    # ---- 开始数据清洗 ----
    logger.info("开始数据清洗（IQR方法处理异常值）...")
    if lot and lot.wafers: # 确保 lot 对象和晶圆数据存在
        transformer = DataTransformer(lot)
        transformer.clean_data(outlier_method='iqr')
        logger.info("数据清洗完成。异常值已替换为 NaN。")
    else:
        logger.warning("Lot数据为空或没有晶圆数据，跳过清洗步骤。")
    # ---- 数据清洗结束 ----
    
    # 定义输出目录
    current_script_dir = Path(__file__).parent
    project_root = current_script_dir.parent 
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)

    # ---- 开始数据分析并保存CSV ----
    perform_data_analysis_and_save_csvs(lot, output_dir)
    # ---- 数据分析结束 ----

def print_lot_info(lot: CPLot):
    """打印Lot信息"""
    if not lot:
        print("Lot 对象为空，无法打印信息。")
        return
        
    print(f"Lot ID: {lot.lot_id}")
    print(f"Product: {lot.product}")
    print(f"晶圆数量: {len(lot.wafers)}")
    print(f"参数数量: {lot.param_count}")
    
    if lot.wafers:
        print("\n晶圆信息 (前3个):")
        for i, wafer in enumerate(lot.wafers[:3]):
            pass_rate_val = wafer.yield_rate if wafer.yield_rate is not None else np.nan
            print(f" - Wafer {wafer.wafer_id}: {wafer.chip_count} 芯片, "
                  f"Pass率: {pass_rate_val:.2%}")
        if len(lot.wafers) > 3:
            print(f" ... 以及 {len(lot.wafers)-3} 个其他晶圆")
            
    if lot.params:
        print("\n参数信息 (前5个):")
        for i, param in enumerate(lot.params[:5]): 
            print(f" - {param.id}: 单位={param.unit}, SL={param.sl}, SU={param.su}")
        
        if len(lot.params) > 5:
            print(f" ... 以及 {len(lot.params)-5} 个其他参数")

if __name__ == "__main__":
    main() 