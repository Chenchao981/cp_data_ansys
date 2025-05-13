#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行Excel TXT Reader示例脚本
"""

import os
import sys
import logging
import numpy as np
import pandas as pd

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 设置日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 导入必要的模块
from cp_data_processor.readers import create_reader
from cp_data_processor.readers.excel_txt_reader import ExcelTXTReader
from cp_data_processor.data_models.cp_data import CPLot, CPWafer

def test_excel_txt_reader():
    """测试Excel TXT Reader功能"""
    # 使用固定路径
    data_dir = os.path.join(parent_dir, "data", "FA53-5465-305A-250303@203_001")
    
    # 指定TXT文件路径
    txt_files = [
        os.path.join(data_dir, "FA53-5465-305A-250303@203_001.TXT"),
        os.path.join(data_dir, "FA53-5465-305A-250303@203_002.TXT"),
        os.path.join(data_dir, "FA53-5465-305A-250303@203_003.TXT")
    ]
    
    # 检查文件是否存在
    existing_files = []
    for file_path in txt_files:
        if os.path.isfile(file_path):
            existing_files.append(file_path)
            print(f"文件存在: {os.path.basename(file_path)}")
        else:
            print(f"文件不存在: {os.path.basename(file_path)}")
    
    if not existing_files:
        print("没有找到测试文件，请检查路径")
        return
    
    # 检查文件是否为Excel格式
    excel_txt_files = []
    for file_path in existing_files:
        is_excel = ExcelTXTReader.is_excel_format(file_path)
        status = "是" if is_excel else "不是"
        print(f"{os.path.basename(file_path)} {status}Excel格式文件")
        if is_excel:
            excel_txt_files.append(file_path)
    
    if not excel_txt_files:
        print("未发现Excel格式的TXT文件，无法进行测试")
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
    
    # 从lot对象中手动提取数据
    combined_data = collect_wafer_data(lot)
    
    if combined_data is not None and not combined_data.empty:
        output_dir = os.path.join(parent_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{lot.lot_id}_combined_data.csv")
        combined_data.to_csv(output_file)
        print(f"数据已保存到: {output_file}")
    else:
        print("未生成有效数据")

def collect_wafer_data(lot: CPLot) -> pd.DataFrame:
    """从lot对象的晶圆中收集数据"""
    all_data = []
    
    for wafer in lot.wafers:
        if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
            # 添加Wafer ID和Bin列
            df = wafer.chip_data.copy()
            df['WaferID'] = wafer.wafer_id
            
            # 如果有X,Y坐标，添加到数据中
            if hasattr(wafer, 'x') and wafer.x is not None:
                df['X'] = wafer.x
            if hasattr(wafer, 'y') and wafer.y is not None:
                df['Y'] = wafer.y
            if hasattr(wafer, 'bin') and wafer.bin is not None:
                df['Bin'] = wafer.bin
                
            all_data.append(df)
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

def print_lot_info(lot: CPLot):
    """打印Lot信息"""
    print(f"Lot ID: {lot.lot_id}")
    print(f"Product: {lot.product}")
    print(f"晶圆数量: {len(lot.wafers)}")
    print(f"参数数量: {lot.param_count}")
    
    if lot.wafers:
        print("\n晶圆信息:")
        for wafer in lot.wafers:
            # 计算Pass率
            pass_rate = 0.0
            if wafer.chip_count > 0 and hasattr(wafer, 'bin') and wafer.bin is not None:
                # 统计bin等于pass_bin的芯片数
                pass_count = np.sum(wafer.bin == lot.pass_bin)
                pass_rate = pass_count / wafer.chip_count
            
            print(f" - Wafer {wafer.wafer_id}: {wafer.chip_count} 芯片, "
                  f"Pass率: {pass_rate:.2%}")
    
    if lot.params:
        print("\n参数信息:")
        for i, param in enumerate(lot.params[:5]):  # 只显示前5个参数
            print(f" - {param.id}: 单位={param.unit}, SL={param.sl}, SU={param.su}")
        
        if len(lot.params) > 5:
            print(f" ... 以及 {len(lot.params)-5} 个其他参数")

if __name__ == "__main__":
    print("====== 开始运行Excel TXT Reader测试 ======")
    try:
        test_excel_txt_reader()
        print("====== 测试运行完成 ======")
    except Exception as e:
        logging.exception("运行测试时出错")
        print(f"错误: {str(e)}")
        sys.exit(1) 