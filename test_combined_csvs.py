#!/usr/bin/env python3
"""
测试多批次合并CSV生成功能
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cp_data_processor.readers.unified_reader import read_cp_data
from cp_data_processor.processing.standard_csv_generator import generate_combined_csvs

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_combined_csv_generation():
    """测试多批次合并CSV生成"""
    
    # 数据目录
    data_dir = "./data"
    output_dir = "./output"
    
    if not os.path.exists(data_dir):
        logger.error(f"数据目录不存在: {data_dir}")
        return
    
    # 扫描数据目录中的所有批次
    lots = {}
    
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isdir(item_path):
            lot_id = item  # 目录名作为批次ID
            logger.info(f"发现批次目录: {lot_id}")
            
            try:
                # 扫描目录中的Excel文件
                excel_files = []
                for file in os.listdir(item_path):
                    if file.endswith('.xlsx'):
                        excel_files.append(os.path.join(item_path, file))
                
                if not excel_files:
                    logger.warning(f"批次目录中没有Excel文件: {lot_id}")
                    continue
                
                logger.info(f"在批次 {lot_id} 中找到 {len(excel_files)} 个Excel文件")
                
                # 使用第一个Excel文件来获取lot数据（假设一个目录是一个batch）
                first_file = excel_files[0]
                logger.info(f"使用文件读取批次数据: {first_file}")
                
                # 读取批次数据
                lot_data = read_cp_data(first_file)
                if lot_data:
                    lots[lot_id] = lot_data
                    logger.info(f"成功读取批次数据: {lot_id}, 晶圆数: {len(lot_data.wafers)}")
                else:
                    logger.warning(f"批次数据为空: {lot_id}")
            except Exception as e:
                logger.error(f"读取批次数据失败 {lot_id}: {e}")
                import traceback
                traceback.print_exc()
    
    if not lots:
        logger.error("没有找到有效的批次数据")
        return
    
    logger.info(f"总共找到 {len(lots)} 个有效批次: {list(lots.keys())}")
    
    # 生成合并的CSV文件
    try:
        combined_name = "multi_lots_combined"
        file_paths = generate_combined_csvs(lots, output_dir, combined_name)
        
        logger.info("合并CSV文件生成成功:")
        for file_type, file_path in file_paths.items():
            logger.info(f"  {file_type}: {file_path}")
            
        # 检查文件是否存在并显示基本信息
        for file_type, file_path in file_paths.items():
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                logger.info(f"  {file_type} 文件大小: {file_size} 字节")
                
                # 显示前几行内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[:5]  # 读取前5行
                        logger.info(f"  {file_type} 前5行预览:")
                        for i, line in enumerate(lines, 1):
                            logger.info(f"    {i}: {line.strip()}")
                except Exception as e:
                    logger.warning(f"读取文件预览失败 {file_path}: {e}")
            else:
                logger.error(f"文件未生成: {file_path}")
                
    except Exception as e:
        logger.error(f"生成合并CSV文件失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_combined_csv_generation()