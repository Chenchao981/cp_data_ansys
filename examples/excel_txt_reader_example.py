#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Excel TXT Reader示例脚本
=======================

本示例演示如何使用ExcelTXTReader读取伪装成TXT的Excel格式数据文件。
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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入CP数据处理模块
from cp_data_processor.readers import create_reader
from cp_data_processor.readers.excel_txt_reader import ExcelTXTReader
from cp_data_processor.data_models.cp_data import CPLot, CPWafer

def main():
    """主函数"""
    # 获取示例数据文件路径
    current_dir = Path(__file__).parent
    data_dir = current_dir.parent / "data" / "FA53-5465-305A-250303@203_001"
    
    # 列出所有TXT文件
    txt_files = list(data_dir.glob("*.TXT"))
    if not txt_files:
        logger.error(f"在 {data_dir} 中未找到TXT文件")
        return
    
    print(f"发现 {len(txt_files)} 个TXT文件:")
    for file in txt_files:
        print(f" - {file.name}")
    
    # 检查文件是否为Excel格式
    excel_txt_files = []
    for file in txt_files:
        is_excel = ExcelTXTReader.is_excel_format(str(file))
        status = "是" if is_excel else "不是"
        print(f"{file.name} {status}Excel格式文件")
        if is_excel:
            excel_txt_files.append(str(file))
    
    if not excel_txt_files:
        logger.warning("未发现Excel格式的TXT文件，请确保文件格式正确")
        return
    
    print("\n----------- 开始读取数据 -----------")
    
    # 方法1：使用reader_factory自动检测并创建读取器
    print("\n使用reader_factory自动检测文件格式:")
    reader = create_reader(excel_txt_files)
    lot = reader.read()
    print_lot_info(lot)
    
    # 方法2：直接创建ExcelTXTReader
    print("\n直接创建ExcelTXTReader:")
    reader = ExcelTXTReader(excel_txt_files)
    lot = reader.read()
    print_lot_info(lot)
    
    # 保存数据示例
    print("\n保存数据示例:")
    output_dir = current_dir.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # 将参数数据合并为DataFrame
    df = lot.get_all_data()
    if df is not None and not df.empty:
        output_file = output_dir / f"{lot.lot_id}_combined_data.csv"
        df.to_csv(output_file)
        print(f"数据已保存到: {output_file}")
    else:
        print("未生成有效数据")

def print_lot_info(lot: CPLot):
    """打印Lot信息"""
    print(f"Lot ID: {lot.lot_id}")
    print(f"Product: {lot.product}")
    print(f"晶圆数量: {len(lot.wafers)}")
    print(f"参数数量: {lot.param_count}")
    
    if lot.wafers:
        print("\n晶圆信息:")
        for wafer in lot.wafers:
            print(f" - Wafer {wafer.wafer_id}: {wafer.chip_count} 芯片, "
                  f"Pass率: {wafer.get_pass_rate():.2%}")
    
    if lot.params:
        print("\n参数信息:")
        for i, param in enumerate(lot.params[:5]):  # 只显示前5个参数
            print(f" - {param.id}: 单位={param.unit}, SL={param.sl}, SU={param.su}")
        
        if len(lot.params) > 5:
            print(f" ... 以及 {len(lot.params)-5} 个其他参数")

if __name__ == "__main__":
    main() 