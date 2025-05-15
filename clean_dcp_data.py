#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DCP数据读取与清洗工具

自动读取目录中的DCP格式文件，提取数据，清洗并输出CSV文件
"""

import os
import sys
import logging
import pandas as pd
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 设置日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"dcp_process_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 导入必要的模块
from cp_data_processor.readers.dcp_reader import DCPReader
from cp_data_processor.processing.data_transformer import DataTransformer
from cp_data_processor.data_models.cp_data import CPLot
from clean_csv_data import clean_csv_data, format_number

def collect_wafer_data(lot: CPLot) -> pd.DataFrame:
    """从lot对象的晶圆中收集数据"""
    all_data = []
    
    for wafer in lot.wafers:
        if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
            # 添加Wafer ID和基本信息列
            df = wafer.chip_data.copy()
            
            # 正确命名晶圆ID列为Wafer_ID
            df['Wafer_ID'] = wafer.wafer_id
            
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
                
            # 添加Lot_ID作为参考
            if hasattr(wafer, 'source_lot_id') and wafer.source_lot_id is not None:
                df['Lot_ID'] = wafer.source_lot_id
                
            all_data.append(df)
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # 确保列名符合预期格式
        # if 'WaferID' in combined_df.columns and 'Wafer' not in combined_df.columns:
        #     combined_df = combined_df.rename(columns={'WaferID': 'Wafer'})
            
        return combined_df
    return pd.DataFrame()

def process_lot_data(lot: CPLot, output_dir: str, apply_clean: bool = True, outlier_method: str = 'iqr'):
    """处理批次数据并保存"""
    if not lot or not lot.wafers:
        logger.warning("没有有效的晶圆数据，无法处理")
        return None
        
    try:
        # 打印批次信息
        print(f"Lot ID: {lot.lot_id}")
        print(f"Product: {lot.product}")
        print(f"晶圆数量: {len(lot.wafers)}")
        print(f"参数数量: {lot.param_count}")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 确保CPLot对象有combined_data属性
        if not hasattr(lot, 'combined_data') or lot.combined_data is None:
            logger.info("创建批次的combined_data...")
            lot.combine_data_from_wafers()
        
        # 应用数据转换和清洗
        if apply_clean:
            transformer = DataTransformer(lot)
            transformer.clean_data(outlier_method=outlier_method)
            logger.info(f"已应用{outlier_method}方法处理异常值")
        
        # 收集处理后的数据
        combined_data = collect_wafer_data(lot)
        
        if combined_data is not None and not combined_data.empty:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_output_file = os.path.join(output_dir, f"{lot.lot_id}_{timestamp}.csv")
            # Ensure index is not written to the CSV
            combined_data.to_csv(raw_output_file, index=False)
            logger.info(f"原始数据已保存到: {raw_output_file}")
            print(f"原始数据已保存到: {raw_output_file}")
            
            # 应用CSV清洗
            cleaned_file = clean_csv_data(raw_output_file)
            if cleaned_file:
                logger.info(f"清洗后的数据已保存到: {cleaned_file}")
                print(f"清洗后的数据已保存到: {cleaned_file}")
                return cleaned_file
            else:
                logger.warning("CSV数据清洗失败")
                return raw_output_file
        else:
            logger.warning("未生成有效数据")
            return None
    except Exception as e:
        logger.exception(f"处理批次数据时出错: {str(e)}")
        return None

def find_dcp_files(directory_path):
    """查找目录中的DCP格式TXT文件"""
    dcp_files = []
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith('.txt'):
                file_path = os.path.join(root, file)
                # 检查是否为Excel格式，如果不是则视为DCP格式
                try:
                    from cp_data_processor.readers.excel_txt_reader import ExcelTXTReader
                    if not ExcelTXTReader.is_excel_format(file_path):
                        dcp_files.append(file_path)
                        logger.info(f"找到DCP文件: {file}")
                except:
                    # 如果检查出错，默认当作DCP格式
                    dcp_files.append(file_path)
                    logger.info(f"假定为DCP文件: {file}")
    
    return dcp_files

def process_directory(directory_path, output_dir=None, outlier_method='iqr'):
    """处理指定目录中的所有DCP文件"""
    logger.info(f"开始处理目录: {directory_path}")
    
    # 设置输出目录
    if output_dir is None:
        output_dir = os.path.join(current_dir, "output")
    
    # 查找DCP文件
    dcp_files = find_dcp_files(directory_path)
    
    if not dcp_files:
        logger.warning(f"在 {directory_path} 中没有找到DCP格式文件")
        return None
    
    logger.info(f"找到 {len(dcp_files)} 个DCP文件")
    
    # 创建DCPReader处理文件
    try:
        reader = DCPReader(dcp_files)
        lot = reader.read()
        
        # 处理批次数据
        return process_lot_data(lot, output_dir, True, outlier_method)
    except Exception as e:
        logger.exception(f"处理DCP文件时出错: {str(e)}")
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='DCP数据读取与清洗工具')
    parser.add_argument('--dir', '-d', help='包含DCP文件的目录路径', default=os.path.join(current_dir, "data"))
    parser.add_argument('--output', '-o', help='输出目录路径', default=os.path.join(current_dir, "output"))
    parser.add_argument('--method', '-m', help='异常值处理方法 (std_dev或iqr)', default='iqr', choices=['std_dev', 'iqr'])
    
    args = parser.parse_args()
    
    # 检查目录是否存在
    if not os.path.exists(args.dir):
        logger.error(f"目录不存在: {args.dir}")
        print(f"错误: 目录不存在: {args.dir}")
        sys.exit(1)
    
    # 处理目录
    output_file = process_directory(args.dir, args.output, args.method)
    
    if output_file:
        print(f"处理完成！最终输出文件: {output_file}")
    else:
        print("处理失败或未找到有效数据")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"程序运行时出错: {str(e)}")
        print(f"错误: {str(e)}")
        sys.exit(1) 