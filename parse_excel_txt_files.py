#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
解析指定路径下的所有Excel格式TXT文件
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import datetime

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 设置日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"parse_excel_txt_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 导入必要的模块
from cp_data_processor.readers import create_reader
from cp_data_processor.readers.excel_txt_reader import ExcelTXTReader
from cp_data_processor.data_models.cp_data import CPLot, CPWafer

def collect_wafer_data(lot: CPLot) -> pd.DataFrame:
    """从lot对象的晶圆中收集数据"""
    all_data = []
    
    for wafer in lot.wafers:
        if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
            # 添加Wafer ID和基本信息列
            df = wafer.chip_data.copy()
            
            # 正确命名晶圆ID列为Wafer
            df['Wafer'] = wafer.wafer_id
            
            # 确保X,Y,Bin,Seq列存在并添加到数据中
            if hasattr(wafer, 'seq') and wafer.seq is not None:
                df['Seq'] = wafer.seq
            if hasattr(wafer, 'x') and wafer.x is not None:
                df['X'] = wafer.x
            if hasattr(wafer, 'y') and wafer.y is not None:
                df['Y'] = wafer.y
            if hasattr(wafer, 'bin') and wafer.bin is not None:
                df['Bin'] = wafer.bin
            
            # 确保CONT和No.U列存在
            if 'CONT' not in df.columns:
                df['CONT'] = ''
            if 'No.U' not in df.columns:
                df['No.U'] = 1
                
            # 添加source_lot_id作为参考
            if hasattr(wafer, 'source_lot_id') and wafer.source_lot_id is not None:
                df['source_lot_id'] = wafer.source_lot_id
                
            all_data.append(df)
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # 确保列名符合预期格式
        if 'WaferID' in combined_df.columns and 'Wafer' not in combined_df.columns:
            combined_df = combined_df.rename(columns={'WaferID': 'Wafer'})
            
        return combined_df
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

def parse_directory(directory_path):
    """解析指定目录下的所有文件"""
    logger.info(f"开始解析目录: {directory_path}")
    
    # 检查目录是否存在
    if not os.path.exists(directory_path):
        logger.error(f"目录不存在: {directory_path}")
        return
    
    # 获取目录中的所有文件
    all_files = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            all_files.append(os.path.join(root, file))
    
    logger.info(f"发现 {len(all_files)} 个文件")
    
    # 检测每个文件的格式
    txt_files = []
    excel_txt_files = []
    other_files = []
    
    for file_path in all_files:
        file_basename = os.path.basename(file_path)
        ext = os.path.splitext(file_basename)[1].lower()
        
        if ext == '.txt':
            txt_files.append(file_path)
            # 检查是否为Excel格式的TXT文件
            if ExcelTXTReader.is_excel_format(file_path):
                logger.info(f"检测到Excel格式TXT文件: {file_basename}")
                excel_txt_files.append(file_path)
            else:
                logger.info(f"标准TXT文件: {file_basename}")
        else:
            other_files.append(file_path)
            logger.info(f"其他类型文件: {file_basename}")
    
    logger.info(f"共找到 {len(txt_files)} 个TXT文件, 其中 {len(excel_txt_files)} 个是Excel格式")
    
    if not excel_txt_files:
        logger.warning("未发现Excel格式的TXT文件，无法解析")
        return
    
    # 解析Excel格式TXT文件
    lot = None
    try:
        logger.info("创建Excel TXT读取器...")
        reader = ExcelTXTReader(excel_txt_files)
        logger.info("开始读取数据...")
        lot = reader.read()
        logger.info(f"成功读取数据: Lot ID={lot.lot_id}, 晶圆数量={len(lot.wafers)}")
        
        # 打印信息
        print_lot_info(lot)
        
        # 保存数据
        output_dir = os.path.join(current_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        combined_data = collect_wafer_data(lot)
        if combined_data is not None and not combined_data.empty:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"{lot.lot_id}_{timestamp}.csv")
            combined_data.to_csv(output_file)
            logger.info(f"数据已保存到: {output_file}")
            print(f"数据已保存到: {output_file}")
        else:
            logger.warning("未生成有效数据")
    except Exception as e:
        logger.exception(f"解析数据时发生错误: {str(e)}")
    
    return lot

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 使用命令行参数指定的路径
        directory_path = sys.argv[1]
    else:
        # 默认使用项目根目录下的 "data" 文件夹
        directory_path = os.path.join(current_dir, "data")
        
        # 检查默认路径是否存在，如果不存在则提示用户并退出
        if not os.path.exists(directory_path):
            logger.error(f"默认数据目录 {directory_path} 不存在。请创建该目录并放入数据文件，或通过命令行参数指定有效的数据目录路径。")
            print(f"错误: 默认数据目录 {directory_path} 不存在。请创建该目录并放入数据文件，或通过命令行参数指定有效的数据目录路径。")
            sys.exit(1)
    
    # 解析指定目录
    print(f"开始解析目录: {directory_path}")
    lot = parse_directory(directory_path)
    
    if lot:
        print("解析完成！")
    else:
        print("解析失败或未找到有效数据")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"程序运行时出错: {str(e)}")
        print(f"错误: {str(e)}")
        sys.exit(1) 