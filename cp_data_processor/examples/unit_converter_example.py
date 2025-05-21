#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
单位转换器使用示例

这个脚本演示了如何使用单位转换器来处理带单位的值。
"""

import logging
import sys
import os

# 添加项目根目录到 Python 路径，以便导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from cp_data_processor.processing.unit_converter import UnitConverter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """单位转换器示例的主函数"""
    logger.info("=== 单位转换器示例 ===")
    
    # 创建单位转换器实例
    converter = UnitConverter()
    
    # 示例 1: 提取单位
    value_str = "3.3V"
    unit = converter.extract_unit(value_str)
    logger.info(f"从 '{value_str}' 提取的单位是: '{unit}'")
    
    # 示例 2: 提取值和单位
    value_str = "10mA"
    value, unit = converter.extract_value_and_unit(value_str)
    logger.info(f"从 '{value_str}' 提取的值是: {value}, 单位是: '{unit}'")
    
    # 示例 3: 获取单位转换率
    units = ["mV", "uA", "nF", "kOhm", "MHz"]
    logger.info("单位转换率示例:")
    for unit in units:
        rate = converter.get_unit_order_change_rate(unit)
        logger.info(f"  单位 '{unit}' 的转换率是: {rate}")
    
    # 示例 4: 将带单位的值转换为标准单位
    values = ["3.3V", "100mV", "2.5uA", "47kOhm", "1MHz", "10.0"]
    logger.info("将带单位的值转换为标准单位:")
    for value_str in values:
        std_value = converter.convert_to_standard(value_str)
        logger.info(f"  '{value_str}' 转换为标准单位: {std_value}")
    
    # 示例 5: 将标准单位的值转换为目标单位
    logger.info("将标准单位的值转换为目标单位:")
    
    std_value = 0.001  # 1mV in V
    target_unit = "mV"
    result = converter.convert_from_standard(std_value, target_unit)
    logger.info(f"  {std_value}V 转换为 {target_unit}: {result}{target_unit}")
    
    std_value = 0.000001  # 1uA in A
    target_unit = "uA"
    result = converter.convert_from_standard(std_value, target_unit)
    logger.info(f"  {std_value}A 转换为 {target_unit}: {result}{target_unit}")
    
    std_value = 1000  # 1kOhm in Ohm
    target_unit = "kOhm"
    result = converter.convert_from_standard(std_value, target_unit)
    logger.info(f"  {std_value}Ohm 转换为 {target_unit}: {result}{target_unit}")
    
    logger.info("=== 示例结束 ===")

if __name__ == "__main__":
    main() 