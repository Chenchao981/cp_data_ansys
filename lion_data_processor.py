#!/usr/bin/env python3
"""
Lion公司专用数据清洗处理器

针对Lion公司数据格式的专门清洗和处理工具，支持多批次数据处理。

使用说明：
1. 将Lion公司的批次数据文件夹放入 ./data 目录下
2. 每个批次一个文件夹，文件夹名为批次ID (如: F25130244, F25130246等)
3. 运行此脚本生成清洗后的CSV文件

示例目录结构：
./data/
├── F25130244/
│   ├── F25130244_1.xlsx
│   ├── F25130244_2.xlsx
│   └── ...
├── F25130246/
│   ├── F25130246_1.xlsx
│   └── ...
└── F25130247/
    ├── F25130247_1.xlsx
    └── ...

输出文件（每个批次一套）：
./output_lion_models/
├── F25130244_cleaned_YYYYMMDD_HHMM.csv
├── F25130244_yield_YYYYMMDD_HHMM.csv  
├── F25130244_spec_YYYYMMDD_HHMM.csv
├── F25130246_cleaned_YYYYMMDD_HHMM.csv
├── F25130246_yield_YYYYMMDD_HHMM.csv
├── F25130246_spec_YYYYMMDD_HHMM.csv
└── ...

如果需要合并所有批次，请使用：
python lion_data_processor.py --combined
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cp_data_processor.readers.unified_reader import read_cp_data
from cp_data_processor.processing.standard_csv_generator import generate_standard_csvs, generate_combined_csvs

def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('lion_data_processor.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def process_single_lot(lot_id: str, lot_path: str, output_dir: str, logger) -> bool:
    """
    处理单个批次的Lion数据
    
    Args:
        lot_id: 批次ID
        lot_path: 批次数据路径
        output_dir: 输出目录
        logger: 日志记录器
        
    Returns:
        bool: 处理成功返回True
    """
    try:
        logger.info(f"开始处理Lion批次: {lot_id}")
        
        # 扫描Excel文件
        excel_files = [f for f in os.listdir(lot_path) if f.endswith('.xlsx')]
        
        if not excel_files:
            logger.warning(f"批次目录 {lot_id} 中没有Excel文件，跳过")
            return False
        
        logger.info(f"批次 {lot_id} 包含 {len(excel_files)} 个Excel文件")
        
        # 使用第一个Excel文件读取批次数据
        first_file = os.path.join(lot_path, excel_files[0])
        logger.info(f"读取批次数据: {first_file}")
        
        # 读取Lion数据
        lot_data = read_cp_data(first_file)
        if not lot_data:
            logger.warning(f"批次数据为空: {lot_id}")
            return False
        
        logger.info(f"成功读取批次: {lot_id} (晶圆数: {len(lot_data.wafers)})")
        
        # 生成标准CSV文件
        file_paths = generate_standard_csvs(lot_data, output_dir)
        
        logger.info(f"批次 {lot_id} 处理完成:")
        for file_type, file_path in file_paths.items():
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                logger.info(f"  {file_type.upper():8}: {os.path.basename(file_path)} ({file_size:,} 字节)")
        
        return True
        
    except Exception as e:
        logger.error(f"处理批次 {lot_id} 失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def process_multiple_lots_individual(data_dir: str, output_dir: str, logger) -> Dict[str, bool]:
    """
    处理多个批次，每个批次生成独立的CSV文件
    
    Args:
        data_dir: 数据目录
        output_dir: 输出目录
        logger: 日志记录器
        
    Returns:
        Dict[str, bool]: 批次ID到处理结果的映射
    """
    results = {}
    
    if not os.path.exists(data_dir):
        logger.error(f"数据目录不存在: {data_dir}")
        return results
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"扫描Lion数据目录: {data_dir}")
    
    # 扫描所有批次目录
    lot_dirs = []
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isdir(item_path) and item.startswith('F'):  # Lion批次通常以F开头
            lot_dirs.append((item, item_path))
    
    if not lot_dirs:
        logger.error("没有找到Lion批次目录（以F开头的目录）")
        return results
    
    logger.info(f"发现 {len(lot_dirs)} 个Lion批次目录")
    
    # 处理每个批次
    successful = 0
    for lot_id, lot_path in lot_dirs:
        success = process_single_lot(lot_id, lot_path, output_dir, logger)
        results[lot_id] = success
        if success:
            successful += 1
    
    logger.info(f"批次处理完成: {successful}/{len(lot_dirs)} 成功")
    return results

def process_multiple_lots_combined(data_dir: str, output_dir: str, logger) -> bool:
    """
    处理多个批次，合并为单套CSV文件
    
    Args:
        data_dir: 数据目录
        output_dir: 输出目录
        logger: 日志记录器
        
    Returns:
        bool: 处理成功返回True
    """
    try:
        if not os.path.exists(data_dir):
            logger.error(f"数据目录不存在: {data_dir}")
            return False
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"开始Lion多批次合并处理: {data_dir}")
        
        # 收集所有批次数据
        lots = {}
        
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path) and item.startswith('F'):  # Lion批次通常以F开头
                lot_id = item
                logger.info(f"发现Lion批次目录: {lot_id}")
                
                try:
                    # 扫描Excel文件
                    excel_files = [f for f in os.listdir(item_path) if f.endswith('.xlsx')]
                    
                    if not excel_files:
                        logger.warning(f"批次目录 {lot_id} 中没有Excel文件，跳过")
                        continue
                    
                    logger.info(f"批次 {lot_id} 包含 {len(excel_files)} 个Excel文件")
                    
                    # 使用第一个Excel文件读取批次数据
                    first_file = os.path.join(item_path, excel_files[0])
                    logger.info(f"读取批次数据: {first_file}")
                    
                    lot_data = read_cp_data(first_file)
                    if lot_data:
                        lots[lot_id] = lot_data
                        logger.info(f"成功读取批次: {lot_id} (晶圆数: {len(lot_data.wafers)})")
                    else:
                        logger.warning(f"批次数据为空: {lot_id}")
                        
                except Exception as e:
                    logger.error(f"读取批次 {lot_id} 失败: {e}")
                    continue
        
        if not lots:
            logger.error("没有找到有效的Lion批次数据")
            return False
        
        logger.info(f"成功读取 {len(lots)} 个Lion批次: {list(lots.keys())}")
        
        # 生成合并的CSV文件
        combined_name = "lion_multi_lots_combined"
        file_paths = generate_combined_csvs(lots, output_dir, combined_name)
        
        logger.info("Lion多批次合并处理完成:")
        for file_type, file_path in file_paths.items():
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                logger.info(f"  {file_type.upper():8}: {os.path.basename(file_path)} ({file_size:,} 字节, {line_count:,} 行)")
        
        return True
        
    except Exception as e:
        logger.error(f"Lion多批次合并处理失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Lion公司专用数据清洗处理器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  python lion_data_processor.py                    # 处理每个批次为独立文件
  python lion_data_processor.py --combined         # 合并所有批次为单套文件
  python lion_data_processor.py --data ./data --output ./output_lion
        """
    )
    
    parser.add_argument(
        '--data', 
        default='./data',
        help='Lion数据目录路径 (默认: ./data)'
    )
    
    parser.add_argument(
        '--output', 
        default='./output_lion_models',
        help='输出目录路径 (默认: ./output_lion_models)'
    )
    
    parser.add_argument(
        '--combined', 
        action='store_true',
        help='合并所有批次为单套CSV文件'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging()
    
    logger.info("=" * 80)
    logger.info("Lion公司数据清洗处理器启动")
    logger.info("=" * 80)
    logger.info(f"数据目录: {args.data}")
    logger.info(f"输出目录: {args.output}")
    logger.info(f"处理模式: {'合并模式' if args.combined else '独立文件模式'}")
    logger.info("=" * 80)
    
    try:
        if args.combined:
            # 合并模式
            success = process_multiple_lots_combined(args.data, args.output, logger)
            if success:
                logger.info("Lion数据合并处理成功完成！")
            else:
                logger.error("Lion数据合并处理失败！")
                sys.exit(1)
        else:
            # 独立文件模式
            results = process_multiple_lots_individual(args.data, args.output, logger)
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            
            if successful > 0:
                logger.info(f"Lion数据处理完成：{successful}/{total} 个批次成功")
                if successful < total:
                    logger.warning("部分批次处理失败，请查看日志")
            else:
                logger.error("所有批次处理都失败了！")
                sys.exit(1)
                
    except KeyboardInterrupt:
        logger.info("用户中断处理")
        sys.exit(1)
    except Exception as e:
        logger.error(f"处理过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("Lion公司数据清洗处理器结束")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()