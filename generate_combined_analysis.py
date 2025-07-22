#!/usr/bin/env python3
"""
多批次数据合并分析脚本

使用说明：
1. 将多个批次的数据文件夹放入 ./data 目录下
2. 每个批次一个文件夹，文件夹名为批次ID
3. 运行此脚本生成合并的3个标准CSV文件

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

输出文件：
./output/
├── multi_lots_combined_cleaned_YYYYMMDD_HHMM.csv  - 所有芯片测试数据
├── multi_lots_combined_yield_YYYYMMDD_HHMM.csv    - 良率汇总数据
└── multi_lots_combined_spec_YYYYMMDD_HHMM.csv     - 参数规格数据
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

def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('combined_analysis.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def main():
    """主函数：生成多批次合并分析"""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("多批次数据合并分析开始")
    logger.info("=" * 60)
    
    # 配置路径
    data_dir = "./data"
    output_dir = "./output"
    
    # 检查数据目录
    if not os.path.exists(data_dir):
        logger.error(f"数据目录不存在: {data_dir}")
        logger.error("请创建 ./data 目录并将批次数据文件夹放入其中")
        return
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 扫描和处理批次数据
    lots = {}
    
    logger.info(f"扫描数据目录: {data_dir}")
    
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isdir(item_path):
            lot_id = item
            logger.info(f"发现批次目录: {lot_id}")
            
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
    
    # 检查是否有有效的批次数据
    if not lots:
        logger.error("没有找到有效的批次数据")
        logger.error("请检查 ./data 目录中是否包含正确的批次文件夹和Excel文件")
        return
    
    logger.info(f"成功读取 {len(lots)} 个批次: {list(lots.keys())}")
    
    # 生成合并的CSV文件
    try:
        logger.info("开始生成合并CSV文件...")
        
        combined_name = "multi_lots_combined"
        file_paths = generate_combined_csvs(lots, output_dir, combined_name)
        
        logger.info("=" * 60)
        logger.info("合并CSV文件生成成功！")
        logger.info("=" * 60)
        
        for file_type, file_path in file_paths.items():
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                logger.info(f"{file_type.upper():8} 文件: {file_path}")
                logger.info(f"         大小: {file_size:,} 字节")
                
                # 显示行数统计
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                    logger.info(f"         行数: {line_count:,} 行")
                except:
                    pass
                    
                logger.info("")
            else:
                logger.error(f"文件生成失败: {file_path}")
        
        # 显示文件说明
        logger.info("文件说明:")
        logger.info("- *_cleaned_*.csv: 包含所有批次所有芯片的详细测试数据")
        logger.info("- *_yield_*.csv:   包含所有批次的良率汇总数据和参数平均值")
        logger.info("- *_spec_*.csv:    包含测试参数的规格限制信息")
        
        logger.info("=" * 60)
        logger.info("多批次数据合并分析完成")
        logger.info("=" * 60)
                
    except Exception as e:
        logger.error(f"生成合并CSV文件失败: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()