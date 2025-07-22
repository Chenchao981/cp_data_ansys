#!/usr/bin/env python3
"""
Lion公司数据处理演示脚本

演示如何使用统一读取器处理Lion公司数据并生成标准CSV文件。

功能：
- 使用统一读取器自动识别Lion公司格式
- 生成标准的cleaned.csv、yield.csv、spec.csv文件
- 适用于单个文件的快速测试

使用方法：
    python demo_lion_processing.py

注意：对于批量处理多个文件，请使用 ../lion_batch_processor.py
"""

import sys
import os
from pathlib import Path
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cp_data_processor.readers.unified_reader import read_cp_data
from cp_data_processor.processing.standard_csv_generator import generate_standard_csvs

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def process_lion_data():
    """使用统一读取器处理Lion数据"""
    
    # 输入和输出路径
    data_dir = project_root / "data" / "F25130244"
    output_dir = project_root / "output_lion_models"
    
    # 确保输出目录存在
    output_dir.mkdir(exist_ok=True)
    
    # 获取第一个Excel文件
    excel_files = list(data_dir.glob("*.xlsx"))
    if not excel_files:
        logger.error("未找到Lion Excel文件")
        return
    
    test_file = excel_files[0]
    logger.info(f"处理文件: {test_file}")
    
    try:
        # 使用统一读取器读取数据
        logger.info("使用统一读取器读取Lion数据...")
        lot = read_cp_data(str(test_file))
        
        if lot is None:
            logger.error("读取失败")
            return
        
        logger.info(f"读取成功: 批次={lot.lot_id}, 晶圆数={len(lot.wafers)}, 参数数={len(lot.params)}")
        
        # 生成标准CSV文件
        logger.info("生成标准CSV文件...")
        generate_standard_csvs(lot, str(output_dir))
        
        logger.info(f"CSV文件已生成到: {output_dir}")
        
        # 显示生成的文件
        csv_files = list(output_dir.glob("*.csv"))
        logger.info(f"生成的文件:")
        for csv_file in sorted(csv_files):
            logger.info(f"  - {csv_file.name}")
        
        logger.info("Lion数据处理演示完成!")
        
    except Exception as e:
        logger.error(f"处理失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("="*50)
    print("Lion公司CP数据处理演示")
    print("="*50)
    process_lion_data()
    print("="*50)