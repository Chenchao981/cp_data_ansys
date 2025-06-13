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
from clean_csv_data import clean_csv_data
from python_cp.yield_processor import generate_yield_report_from_dataframe
from dcp_spec_extractor import generate_spec_file
# 导入单位转换模块
from cp_unit_converter import process_excel_file as convert_units_in_file

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
            # if 'No.U' not in df.columns: # No longer ensuring No.U here
            #     df['No.U'] = 1
                
            # 添加Lot_ID作为参考（使用子目录名称作为lot_id）
            if hasattr(wafer, 'source_lot_id') and wafer.source_lot_id is not None:
                df['Lot_ID'] = wafer.source_lot_id
            else:
                # 如果没有设置source_lot_id，尝试使用批次的lot_id
                if hasattr(lot, 'lot_id') and lot.lot_id is not None:
                    df['Lot_ID'] = lot.lot_id
                else:
                    df['Lot_ID'] = 'Unknown'
                
            all_data.append(df)
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # 确保列名符合预期格式
        # if 'WaferID' in combined_df.columns and 'Wafer' not in combined_df.columns:
        #     combined_df = combined_df.rename(columns={'WaferID': 'Wafer'})
            
        return combined_df
    return pd.DataFrame()

def process_lot_data(lot: CPLot, output_dir: str, apply_clean: bool = True, 
                    outlier_method: str = 'iqr', 
                    source_dcp_file_for_spec: str | None = None,
                    convert_units: bool = True):
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
        
        # --- 新增：生成Spec文件 --- 
        spec_file_path = None
        if source_dcp_file_for_spec:
            logger.info(f"开始为批次 {lot.lot_id} (源文件: {source_dcp_file_for_spec}) 生成规格文件...")
            spec_file_path = generate_spec_file(source_dcp_file_for_spec, output_dir, lot.lot_id)
            if spec_file_path:
                logger.info(f"规格文件已成功生成: {spec_file_path}")
                print(f"规格文件已成功生成: {spec_file_path}")
                
            else:
                logger.warning(f"为批次 {lot.lot_id} 生成规格文件失败。")
        else:
            logger.info("未提供用于生成规格文件的源DCP文件路径，跳过生成规格文件步骤。")
        # --- 结束：生成Spec文件 --- 
        
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
            # 调用修改后的 clean_csv_data，直接传递 DataFrame
            # 文件名将是 LOTID_cleaned_TIMESTAMP.csv
            cleaned_file_path_str = clean_csv_data(combined_data, output_dir, lot.lot_id)
            
            if cleaned_file_path_str: 
                logger.info(f"清洗后的数据已保存到: {cleaned_file_path_str}")
                print(f"清洗后的数据已保存到: {cleaned_file_path_str}")

                # --- 开始添加良率报告生成逻辑 ---
                try:
                    logger.info(f"开始为 {cleaned_file_path_str} 生成良率报告...")
                    
                    # 从已保存的cleaned文件中读取数据
                    cleaned_df_for_yield = pd.read_csv(cleaned_file_path_str)

                    # --- 修复：确保yield文件名与cleaned文件名的时间戳部分一致 ---
                    # 从cleaned文件名生成yield文件名，例如 'lot_cleaned_timestamp.csv' -> 'lot_yield_timestamp.csv'
                    cleaned_filename = Path(cleaned_file_path_str).name
                    yield_report_filename = cleaned_filename.replace('_cleaned_', '_yield_')
                    yield_report_filepath = Path(output_dir) / yield_report_filename
                    
                    success_yield = generate_yield_report_from_dataframe(cleaned_df_for_yield, str(yield_report_filepath))
                    
                    if success_yield:
                        logger.info(f"良率报告已成功生成: {yield_report_filepath}")
                        print(f"良率报告已成功生成: {yield_report_filepath}")
                    else:
                        logger.warning(f"良率报告生成失败: {yield_report_filepath}")
                        print(f"警告: 良率报告生成失败: {yield_report_filepath}")
                
                except Exception as e_yield:
                    logger.error(f"生成良率报告时发生意外错误: {e_yield}")
                    print(f"错误: 生成良率报告时发生意外错误: {e_yield}")
                # --- 结束添加良率报告生成逻辑 ---
                
                return cleaned_file_path_str 
            else:
                logger.warning("CSV数据清洗失败或未生成数据 (可能DataFrame为空或保存失败)")
                return None
        else:
            logger.warning("未生成有效数据 (combined_data is None or empty)")
            return None
    except Exception as e:
        logger.exception(f"处理批次数据时出错: {str(e)}")
        return None

def detect_directory_structure(directory_path):
    """检测目录结构类型
    
    Returns:
        tuple: (structure_type, batch_info)
        - structure_type: 'single' 或 'double'
        - batch_info: 单层时为目录名，两层时为子目录列表
    """
    directory_path = os.path.abspath(directory_path)
    
    # 检查当前目录是否直接包含DCP文件
    has_dcp_files_in_current = False
    has_subdirs_with_dcp = False
    subdirs_with_dcp = []
    
    # 检查当前目录中的直接文件
    for file in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file)
        if os.path.isfile(file_path) and file.lower().endswith('.txt'):
            # 简单检查是否为DCP格式文件
            try:
                from cp_data_processor.readers.excel_txt_reader import ExcelTXTReader
                if not ExcelTXTReader.is_excel_format(file_path):
                    has_dcp_files_in_current = True
                    break
            except Exception:
                has_dcp_files_in_current = True
                break
    
    # 如果当前目录没有DCP文件，检查子目录
    if not has_dcp_files_in_current:
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isdir(item_path):
                # 检查子目录中是否有DCP文件
                subdir_has_dcp = False
                try:
                    for file in os.listdir(item_path):
                        if file.lower().endswith('.txt'):
                            file_path = os.path.join(item_path, file)
                            try:
                                from cp_data_processor.readers.excel_txt_reader import ExcelTXTReader
                                if not ExcelTXTReader.is_excel_format(file_path):
                                    subdir_has_dcp = True
                                    break
                            except Exception:
                                subdir_has_dcp = True
                                break
                except OSError:
                    continue
                
                if subdir_has_dcp:
                    has_subdirs_with_dcp = True
                    subdirs_with_dcp.append(item)
    
    # 根据检测结果返回结构类型
    if has_dcp_files_in_current:
        # 单层结构：当前目录直接包含DCP文件
        dir_name = os.path.basename(directory_path)
        return 'single', dir_name
    elif has_subdirs_with_dcp:
        # 两层结构：子目录包含DCP文件
        return 'double', subdirs_with_dcp
    else:
        # 没有找到DCP文件
        return 'none', None

def find_dcp_files_in_directory(directory_path, recursive=False):
    """查找指定目录中的DCP格式TXT文件
    
    Args:
        directory_path: 目录路径
        recursive: 是否递归查找（默认False，只查找当前目录）
    """
    dcp_files = []
    
    if recursive:
        # 原有的递归查找逻辑
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith('.txt'):
                    file_path = os.path.join(root, file)
                    try:
                        from cp_data_processor.readers.excel_txt_reader import ExcelTXTReader
                        if not ExcelTXTReader.is_excel_format(file_path):
                            dcp_files.append(file_path)
                            logger.info(f"找到DCP文件: {file}")
                    except Exception:
                        dcp_files.append(file_path)
                        logger.info(f"假定为DCP文件 (excel_txt_reader check failed or not available): {file}")
    else:
        # 只查找当前目录
        try:
            for file in os.listdir(directory_path):
                if file.lower().endswith('.txt'):
                    file_path = os.path.join(directory_path, file)
                    if os.path.isfile(file_path):
                        try:
                            from cp_data_processor.readers.excel_txt_reader import ExcelTXTReader
                            if not ExcelTXTReader.is_excel_format(file_path):
                                dcp_files.append(file_path)
                                logger.info(f"找到DCP文件: {file}")
                        except Exception:
                            dcp_files.append(file_path)
                            logger.info(f"假定为DCP文件 (excel_txt_reader check failed or not available): {file}")
        except OSError as e:
            logger.error(f"无法访问目录 {directory_path}: {e}")
    
    return dcp_files



def process_directory(directory_path, output_dir=None, outlier_method='iqr', convert_units=True):
    """处理指定目录中的所有DCP文件"""
    logger.info(f"开始处理目录: {directory_path}")
    
    # 设置输出目录
    if output_dir is None:
        output_dir = os.path.join(current_dir, "output")
    
    # 检测目录结构并获取正确的lot_id
    structure_type, batch_info = detect_directory_structure(directory_path)
    
    if structure_type == 'none':
        logger.warning(f"在 {directory_path} 中没有找到DCP格式文件")
        return None
    elif structure_type == 'single':
        # 单层结构：当前目录直接包含DCP文件
        lot_id = batch_info  # batch_info 是目录名
        logger.info(f"检测到单层目录结构，批次ID: {lot_id}")
        
        # 查找DCP文件
        dcp_files = find_dcp_files_in_directory(directory_path, recursive=False)
        
        if not dcp_files:
            logger.warning(f"在目录 {directory_path} 中没有找到DCP格式文件")
            return None
        
        logger.info(f"找到 {len(dcp_files)} 个DCP文件: {[os.path.basename(f) for f in dcp_files]}")
        
        # 创建DCPReader处理文件
        try:
            reader = DCPReader(dcp_files)
            lot = reader.read()
            
            # 设置正确的lot_id
            if lot:
                lot.lot_id = lot_id
                logger.info(f"设置批次ID为: {lot_id}")
            
            # 处理批次数据，使用原始输出目录
            first_dcp_file_for_spec = dcp_files[0] if dcp_files else None
            return process_lot_data(lot, output_dir, True, outlier_method, 
                                  source_dcp_file_for_spec=first_dcp_file_for_spec,
                                  convert_units=convert_units)
        except Exception as e:
            logger.exception(f"处理批次 {lot_id} 的DCP文件时出错: {str(e)}")
            return None
            
    elif structure_type == 'double':
        # 两层结构：子目录包含DCP文件，合并处理但保持各自的lot_id
        subdirs = batch_info  # batch_info 是子目录列表
        logger.info(f"检测到两层目录结构，找到 {len(subdirs)} 个子批次: {subdirs}")
        
        # 设置主输出目录的名称
        parent_dir_name = os.path.basename(directory_path)
        main_lot_id = parent_dir_name if parent_dir_name != "data" else f"Combined_{len(subdirs)}_batches"
        logger.info(f"主输出目录名称: {main_lot_id}")
        
        # 收集所有子目录中的DCP文件，并建立文件到子目录的映射
        all_dcp_files = []
        file_to_subdir_map = {}  # 文件路径 -> 子目录名称的映射
        
        for subdir in subdirs:
            subdir_path = os.path.join(directory_path, subdir)
            subdir_dcp_files = find_dcp_files_in_directory(subdir_path, recursive=False)
            all_dcp_files.extend(subdir_dcp_files)
            
            # 建立文件到子目录的映射
            for file_path in subdir_dcp_files:
                file_to_subdir_map[file_path] = subdir
            
            logger.info(f"子批次 {subdir} 找到 {len(subdir_dcp_files)} 个DCP文件")
        
        if not all_dcp_files:
            logger.warning(f"在所有子目录中都没有找到DCP格式文件")
            return None
        
        logger.info(f"总共找到 {len(all_dcp_files)} 个DCP文件")
        
        # 创建DCPReader处理所有文件
        try:
            reader = DCPReader(all_dcp_files)
            lot = reader.read()
            
            # 为每个晶圆设置正确的lot_id（基于文件的分组分配）
            if lot and lot.wafers:
                # 按子目录分组文件，并为每个子目录的文件分配连续的索引范围
                subdir_file_ranges = {}
                wafer_index = 0
                
                for subdir in subdirs:
                    subdir_files = [f for f in all_dcp_files if file_to_subdir_map[f] == subdir]
                    wafer_count_in_subdir = len(subdir_files)
                    subdir_file_ranges[subdir] = (wafer_index, wafer_index + wafer_count_in_subdir)
                    wafer_index += wafer_count_in_subdir
                    logger.info(f"子目录 {subdir}: 晶圆索引范围 {subdir_file_ranges[subdir][0]} - {subdir_file_ranges[subdir][1]-1}")
                
                # 为每个晶圆分配lot_id
                for idx, wafer in enumerate(lot.wafers):
                    wafer.source_lot_id = subdirs[0]  # 默认值
                    
                    # 根据晶圆在wafers列表中的位置确定其lot_id
                    for subdir, (start_idx, end_idx) in subdir_file_ranges.items():
                        if start_idx <= idx < end_idx:
                            wafer.source_lot_id = subdir
                            logger.info(f"晶圆 {wafer.wafer_id} (索引 {idx}) 设置lot_id为: {wafer.source_lot_id}")
                            break
                    
                    if wafer.source_lot_id == subdirs[0] and idx >= subdir_file_ranges[subdirs[0]][1]:
                        logger.warning(f"晶圆 {wafer.wafer_id} (索引 {idx}) 无法确定lot_id，使用默认值: {wafer.source_lot_id}")
                
                # 设置批次的主ID用于文件命名
                lot.lot_id = main_lot_id
                logger.info(f"设置主批次ID为: {main_lot_id}")
            
            # 处理批次数据，使用原始输出目录
            first_dcp_file_for_spec = all_dcp_files[0] if all_dcp_files else None
            return process_lot_data(lot, output_dir, True, outlier_method, 
                                  source_dcp_file_for_spec=first_dcp_file_for_spec,
                                  convert_units=convert_units)
        except Exception as e:
            logger.exception(f"处理合并批次 {main_lot_id} 时出错: {str(e)}")
            return None
    
    return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='DCP数据读取与清洗工具')
    parser.add_argument('--dir', '-d', help='包含DCP文件的目录路径', default=os.path.join(current_dir, "data"))
    parser.add_argument('--output', '-o', help='输出目录路径', default=os.path.join(current_dir, "output"))
    parser.add_argument('--method', '-m', help='异常值处理方法 (std_dev或iqr)', default='iqr', choices=['std_dev', 'iqr'])
    parser.add_argument('--no-convert', action='store_true', help='禁用单位转换（默认启用）')
    
    args = parser.parse_args()
    
    # 检查目录是否存在
    if not os.path.exists(args.dir):
        logger.error(f"目录不存在: {args.dir}")
        print(f"错误: 目录不存在: {args.dir}")
        sys.exit(1)
    
    # 处理目录
    result = process_directory(args.dir, args.output, args.method, not args.no_convert)
    
    if result:
        print(f"处理完成！最终输出文件: {result}")
    else:
        print("处理失败或未找到有效数据")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"程序运行时出错: {str(e)}")
        print(f"错误: {str(e)}")
        sys.exit(1) 