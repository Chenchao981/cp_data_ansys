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
        df_to_save = cleaned_df.copy()
        df_to_save.insert(0, 'LotID', lot.lot_id)
        df_to_save.rename(columns={'Wafer': 'WaferID'}, inplace=True)

        base_columns = ['LotID', 'WaferID', 'Seq', 'Bin', 'X', 'Y']
        final_ordered_cols = list(base_columns)
        
        remaining_cols = [col for col in df_to_save.columns if col not in base_columns]
        
        if 'CONT' in remaining_cols:
            final_ordered_cols.append('CONT')
            remaining_cols.remove('CONT')
        
        remaining_cols.sort() # 按字母顺序排序其余参数
        final_ordered_cols.extend(remaining_cols)
        
        # 确保所有期望的列都存在于DataFrame中，只选择存在的列
        final_ordered_cols = [col for col in final_ordered_cols if col in df_to_save.columns]
        
        df_output_combined = df_to_save[final_ordered_cols]
        
        output_combined_file = output_dir / f"{lot.lot_id}_combined_data.csv"
        df_output_combined.to_csv(output_combined_file, index=False)
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
            summary_df_with_lotid = summary_df.copy()
            summary_df_with_lotid.insert(0, 'LotID', lot.lot_id) # 插入LotID作为第一列
            
            # 使用固定的全局文件名
            output_summary_global_filename = "all_lots_combined_summary.csv"
            output_summary_file = output_dir / output_summary_global_filename
            
            # 当前实现会覆盖文件。若要追加，需要在main函数层面进行读取、合并、写入的逻辑。
            summary_df_with_lotid.to_csv(output_summary_file, index=False)
            logger.info(f"基本统计量 (LotID: {lot.lot_id}) 已保存到: {output_summary_file}")
        else:
            logger.warning(f"Lot {lot.lot_id} 未生成统计摘要数据。")
    except Exception as e:
        logger.exception(f"保存统计摘要到 all_lots_combined_summary.csv 时出错: {e}")

    # 3. 保存良率信息 (_combined_Yield.csv - 保持per-lot)
    try:
        logger.info(f"准备生成 {lot.lot_id}_combined_Yield.csv ...")
        yield_data_list = []
        bins_to_count = [3, 4, 6, 7, 8, 9]

        for wafer in lot.wafers:
            wafer_yield_data = {
                'LotID': lot.lot_id,
                'WaferID': wafer.wafer_id,
                'Yield': wafer.yield_rate if wafer.yield_rate is not None else np.nan,
                'Total': wafer.chip_count,
                'Pass': wafer.pass_chips if wafer.pass_chips is not None else np.nan
            }
            if wafer.bin is not None:
                for bin_val in bins_to_count:
                    wafer_yield_data[f'Bin{bin_val}'] = np.sum(wafer.bin == bin_val)
            else:
                 for bin_val in bins_to_count:
                    wafer_yield_data[f'Bin{bin_val}'] = 0
            
            yield_data_list.append(wafer_yield_data)

        if yield_data_list:
            yield_df = pd.DataFrame(yield_data_list)
            # 确保列顺序
            yield_columns_ordered = ['LotID', 'WaferID', 'Yield', 'Total', 'Pass'] + [f'Bin{b}' for b in bins_to_count]
            yield_df = yield_df[yield_columns_ordered]
            output_yield_file = output_dir / f"{lot.lot_id}_combined_Yield.csv"
            yield_df.to_csv(output_yield_file, index=False)
            logger.info(f"Lot {lot.lot_id} 的良率信息已保存到: {output_yield_file}")
        else:
            logger.warning(f"Lot {lot.lot_id} 未生成良率数据。")
    except Exception as e:
        logger.exception(f"保存 {lot.lot_id}_combined_Yield.csv 时出错: {e}")

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