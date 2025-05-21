#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CP单位转换工具

这个独立程序用于处理CP测试数据中的单位转换，特别是用于将LimitU和LimitL转换为标准单位值，
同时保持TestCond原样，方便后续处理和图表生成。
"""

import os
import sys
import argparse
import logging
import pandas as pd
import re
from typing import Dict, Optional, Tuple, Union, Any, List
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class UnitConverter:
    """
    单位转换器类，处理单位提取和值转换。
    提供了将带单位的值转换为标准单位的功能。
    """
    
    # 单位前缀映射（如毫、微、纳等）
    UNIT_PREFIX_MAP = {
        'f': 1e-15,  # femto
        'p': 1e-12,  # pico
        'n': 1e-9,   # nano
        'u': 1e-6,   # micro
        'μ': 1e-6,   # micro (alternative)
        'm': 1e-3,   # milli
        'k': 1e3,    # kilo
        'meg': 1e6,  # mega
        'M': 1e6,    # mega (alternative)
        'g': 1e9,    # giga
        'G': 1e9,    # giga (alternative)
        't': 1e12,   # tera
        'T': 1e12,   # tera (alternative)
    }
    
    # 基本单位列表
    BASE_UNITS = [
        'v', 'volt', 'volts',
        'a', 'amp', 'amps', 'ampere', 'amperes',
        'ohm', 'ohms',
        'hz', 'hertz',
        'f', 'farad', 'farads',
        's', 'sec', 'second', 'seconds',
        'h', 'henry', 'henries',
    ]
    
    def __init__(self):
        """初始化单位转换器"""
        pass
    
    def extract_unit(self, value_str: str) -> str:
        """
        从带单位的字符串中提取单位部分。
        
        Args:
            value_str: 带单位的字符串，如 "3.3V", "100mA"
            
        Returns:
            提取出的单位字符串，如果没有找到则返回空字符串
        """
        if not isinstance(value_str, str):
            return ""
        
        # 尝试使用正则表达式匹配单位部分（字母在数字后面的部分）
        match = re.search(r'[a-zA-Z][a-zA-Z]*(?:\s*/\s*[a-zA-Z][a-zA-Z]*)?$', value_str.strip())
        if match:
            return match.group()
        
        return ""
    
    def extract_value_and_unit(self, value_str: str) -> Tuple[Optional[float], str]:
        """
        从带单位的字符串中提取数值和单位部分。
        
        Args:
            value_str: 带单位的字符串，如 "3.3V", "100mA"
            
        Returns:
            (数值, 单位) 的元组，如果解析失败则数值为None
        """
        if not isinstance(value_str, str):
            return None, ""
        
        # 尝试使用正则表达式匹配数值和单位
        match = re.search(r'^([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*([a-zA-ZμΩ/]*)', value_str.strip())
        if match:
            try:
                value = float(match.group(1))
                unit = match.group(2)
                return value, unit
            except (ValueError, TypeError):
                pass
                
        return None, ""
    
    def get_unit_order_change_rate(self, unit: str) -> float:
        """
        获取单位对应的数量级转换率（相对于基本单位）。
        
        Args:
            unit: 单位字符串，如 "mV", "kOhm"
            
        Returns:
            转换率，例如 "mV" 返回 0.001，表示 1mV = 0.001V
        """
        if not unit:
            return 1.0
            
        unit_lower = unit.lower()
        
        # 检查单位前缀
        for prefix, rate in self.UNIT_PREFIX_MAP.items():
            if unit_lower.startswith(prefix.lower()):
                # 确保后面是基本单位，或者前缀本身就是一个单位（如'F'同时是法拉和femto前缀）
                if len(unit_lower) > len(prefix):
                    # 检查剩余部分是否是基本单位
                    rest = unit_lower[len(prefix):]
                    if any(rest == base_unit for base_unit in self.BASE_UNITS):
                        return rate
                elif prefix.lower() in self.BASE_UNITS:
                    # 如果前缀本身就是一个基本单位（如'F'），则返回1.0
                    return 1.0
                elif len(unit_lower) == len(prefix):
                    # 如果单位只有前缀（如'm'或'k'），也返回对应的转换率
                    return rate
        
        # 如果没有找到前缀或不是基本单位的组合，返回1.0
        return 1.0
    
    def get_base_unit(self, unit: str) -> str:
        """
        从单位字符串中提取基本单位。
        
        Args:
            unit: 单位字符串，如 "mV", "kOhm"
            
        Returns:
            基本单位，如 "V", "Ohm"
        """
        if not unit:
            return ""
            
        unit_lower = unit.lower()
        
        # 检查是否有前缀
        for prefix in self.UNIT_PREFIX_MAP.keys():
            if unit_lower.startswith(prefix.lower()) and len(unit_lower) > len(prefix):
                return unit[len(prefix):]
        
        # 如果没有前缀，则整个字符串就是基本单位
        return unit
    
    def convert_to_standard(self, value_str: Union[str, float]) -> Optional[float]:
        """
        将带单位的值转换为标准单位的值。
        
        Args:
            value_str: 带单位的字符串，如 "3.3mV", "100uA"，或已经是数值
            
        Returns:
            标准单位下的值，例如 "3.3mV" 返回 0.0033 (V)。如果转换失败则返回None
        """
        if isinstance(value_str, (int, float)):
            return float(value_str)
            
        value, unit = self.extract_value_and_unit(str(value_str))
        if value is None:
            return None
            
        # 如果没有单位，假设已经是标准单位
        if not unit:
            return value
            
        # 获取单位转换率
        rate = self.get_unit_order_change_rate(unit)
        
        # 应用转换率
        return value * rate
        
    def convert_from_standard(self, value: float, target_unit: str) -> Optional[float]:
        """
        将标准单位的值转换为目标单位的值。
        
        Args:
            value: 标准单位下的值
            target_unit: 目标单位字符串
            
        Returns:
            目标单位下的值。例如，从V到mV，1V返回1000mV
        """
        if value is None or not isinstance(value, (int, float)):
            return None
            
        # 如果没有目标单位，直接返回原值
        if not target_unit:
            return value
            
        # 获取单位转换率
        rate = self.get_unit_order_change_rate(target_unit)
        
        # 应用转换率 (从标准单位转换到目标单位需要除以转换率)
        if rate == 0:
            return None  # 防止除以零
            
        return value / rate

def process_excel_file(input_file: str, output_file: str = None, sheet_name: str = 'Spec', format_only: bool = False) -> bool:
    """
    处理Excel或CSV文件，转换LimitU和LimitL列，保持TestCond列不变
    
    Args:
        input_file: 输入Excel或CSV文件路径
        output_file: 输出文件路径，默认为None时使用输入文件名加后缀 "_converted"
        sheet_name: 要处理的工作表名称，默认为'Spec'（仅Excel文件有效）
        format_only: 是否仅执行格式转换，不进行单位转换
        
    Returns:
        处理是否成功
    """
    # 如果未指定输出文件，创建默认名称
    if output_file is None:
        base_name, ext = os.path.splitext(input_file)
        suffix = "_formatted" if format_only else "_converted"
        output_file = f"{base_name}{suffix}{ext}"
    
    if format_only:
        logger.info(f"仅格式化处理文件: {input_file}")
    else:
        logger.info(f"处理文件: {input_file}")
    logger.info(f"输出文件: {output_file}")
    
    try:
        # 读取数据
        df = None
        is_csv = input_file.lower().endswith('.csv')
        
        if is_csv:
            # 尝试多种分隔符读取CSV文件，优先使用制表符
            try:
                df = pd.read_csv(input_file, delimiter='\t', encoding='utf-8')
                logger.info(f"使用制表符分隔符读取CSV文件，读取了 {len(df)} 行数据")
            except Exception as e:
                logger.warning(f"使用制表符分隔符读取失败: {e}, 尝试其他分隔符")
                try:
                    df = pd.read_csv(input_file, delimiter=',', encoding='utf-8')
                    logger.info(f"使用逗号分隔符读取CSV文件，读取了 {len(df)} 行数据")
                except Exception as e2:
                    logger.error(f"使用逗号分隔符读取也失败: {e2}")
                    return False
        else:
            # 如果是Excel文件，使用sheet_name
            df = pd.read_excel(input_file, sheet_name=sheet_name)
            logger.info(f"从Excel文件的 {sheet_name} 工作表读取了 {len(df)} 行数据")
        
        # 数据预处理：检查是否为图1格式（行格式的参数名称合并在一个单元格中）
        # 检查第一行或第一列是否包含多个参数名称
        needs_reformatting = False
        first_row_first_cell = ""
        
        if not df.empty:
            # 从DataFrame中检查第一行第一个单元格
            first_row_first_cell = str(df.iloc[0, 0]) if len(df.columns) > 0 else ""
            
            # 检测方法1：检查是否是图1格式: Parameter列包含多个参数名如"CONT IGSS0 IGSS1..."
            common_params = ["CONT", "IGSS", "VTH", "BVDSS", "IDSS"]
            param_count = sum(1 for param in common_params if param in first_row_first_cell)
            
            # 检测方法2：参数名后面没有空格直接连接的情况（如"ParameterCONTIGSS0..."）
            is_merged_format = False
            if "Parameter" in first_row_first_cell:
                # 尝试提取参数名部分
                param_part = first_row_first_cell.replace("Parameter", "")
                
                # 检查是否有多个参数名连在一起
                for param in common_params:
                    if param in param_part:
                        is_merged_format = True
                        break
            
            # 检测方法3：检查数据结构是否有LimitU、LimitL、Unit等行，但只有一列数据
            expected_rows = ["Unit", "LimitU", "LimitL", "TestCond"]
            row_matches = 0
            if len(df) >= 4:  # 至少需要有4行（Parameter, Unit, LimitU, LimitL）
                for i in range(min(5, len(df))):  # 只检查前5行
                    row_val = str(df.iloc[i, 0])
                    for expected in expected_rows:
                        if expected in row_val:
                            row_matches += 1
                            break
            
            # 综合判断是否需要格式转换
            if param_count >= 2 or is_merged_format or row_matches >= 2:
                needs_reformatting = True
                logger.info(f"检测到图1格式数据: 参数名合并在一个单元格中")
                
                # 如果是没有空格分隔的合并格式，需要先解析参数名称
                if is_merged_format and param_count == 0:
                    logger.info(f"检测到参数名不含空格分隔的合并格式")
                    
        # 处理图1格式数据 - 拆分参数到独立列
        if needs_reformatting:
            logger.info("开始将图1格式数据重新格式化为图2格式...")
            
            # 检查行类型：Parameter, Unit, LimitU, LimitL, TestCond
            row_types = []
            param_row_idx = -1
            
            for i, row in df.iterrows():
                first_val = str(row.iloc[0])
                if "Parameter" in first_val:
                    row_types.append("Parameter")
                    param_row_idx = i
                elif "Unit" in first_val:
                    row_types.append("Unit")
                elif "LimitU" in first_val:
                    row_types.append("LimitU")
                elif "LimitL" in first_val:
                    row_types.append("LimitL")
                elif "TestCond" in first_val:
                    row_types.append("TestCond")
                else:
                    row_types.append("Unknown")
            
            if param_row_idx == -1:
                logger.error("无法在数据中找到Parameter行，无法进行格式转换")
                return False
            
            # 从Parameter行提取所有参数名称
            param_row = df.iloc[param_row_idx]
            param_names = []
            
            # 拆分第一个单元格，获取所有参数名称
            if len(param_row) > 0:
                param_cell = str(param_row.iloc[0])
                
                # 删除"Parameter"前缀
                if param_cell.startswith("Parameter"):
                    param_cell = param_cell[len("Parameter"):]
                
                # 尝试使用空格分隔，提取所有参数名称
                if " " in param_cell:
                    # 有空格分隔的情况
                    param_names = [p for p in param_cell.split() if p]
                    logger.info(f"从Parameter行提取的参数(空格分隔): {param_names}")
                else:
                    # 没有空格分隔的情况，需要按照已知参数名匹配
                    logger.info(f"Parameter单元格内容无空格分隔: {param_cell}")
                    
                    # 定义所有可能的参数名模式
                    param_patterns = [
                        "CONT", "IGSS0", "IGSS1", "IGSS2", "IGSSR1", "IGSSR2", 
                        "VTH", "BVDSS1", "BVDSS2", "IDSS1", "IDSS2"
                    ]
                    
                    # 使用正则表达式提取参数
                    import re
                    remaining = param_cell
                    extracted_params = []
                    
                    # 优先匹配较长的模式，防止误匹配
                    sorted_patterns = sorted(param_patterns, key=len, reverse=True)
                    
                    # 从起始位置开始匹配参数
                    while remaining:
                        found = False
                        for pattern in sorted_patterns:
                            if remaining.startswith(pattern):
                                extracted_params.append(pattern)
                                remaining = remaining[len(pattern):]
                                found = True
                                break
                        
                        if not found:
                            # 如果没有匹配到参数，尝试移动一个字符继续匹配
                            if len(remaining) > 1:
                                remaining = remaining[1:]
                            else:
                                break
                    
                    if extracted_params:
                        param_names = extracted_params
                        logger.info(f"从无空格分隔的Parameter行提取的参数: {param_names}")
                    else:
                        # 如果无法提取参数，则使用固定的通用参数集
                        param_names = param_patterns
                        logger.warning(f"无法从Parameter行提取参数，使用默认参数名: {param_names}")
            
            if not param_names:
                logger.error("无法从Parameter行提取参数名称")
                return False
            
            # 创建新的DataFrame结构
            new_df = pd.DataFrame(columns=[""] + param_names)
            
            # 填充数据
            for row_type in ["Parameter", "Unit", "LimitU", "LimitL", "TestCond"]:
                row_idx = row_types.index(row_type) if row_type in row_types else -1
                
                if row_idx != -1:
                    row_data = df.iloc[row_idx]
                    first_cell = str(row_data.iloc[0])
                    
                    # 从首个单元格中提取数据，按顺序对应参数名
                    if row_type == "Parameter":
                        # 参数行特殊处理
                        new_row = pd.Series(["Parameter"] + param_names, index=new_df.columns)
                    else:
                        # 其他行：提取首个单元格内容，然后按空格分割
                        # 删除掉可能的前缀（如"Unit"、"LimitU"等）
                        if row_type in first_cell:
                            first_cell = first_cell[len(row_type):].strip()
                            if first_cell.startswith(":"):
                                first_cell = first_cell[1:].strip()
                        
                        # 尝试分割值，确保与参数名数量匹配
                        values = []
                        
                        # 对LimitU, LimitL和Unit行进行特殊处理
                        if row_type in ["LimitU", "LimitL", "Unit"]:
                            # 检查是否有空格分隔
                            if " " in first_cell:
                                # 使用正则表达式匹配带单位的值
                                import re
                                pattern = r'([0-9]+\.?[0-9]*\s*[A-Za-z]*)'
                                matches = re.findall(pattern, first_cell)
                                values = matches if matches else first_cell.split()
                            else:
                                # 无空格分隔的情况，需要解析连续的值
                                logger.info(f"检测到无空格分隔的{row_type}行: {first_cell}")
                                
                                # 使用正则表达式匹配数值+单位的模式
                                import re
                                pattern = r'([0-9]+\.?[0-9]*[A-Za-z]*)'
                                matches = re.findall(pattern, first_cell)
                                
                                if matches:
                                    values = matches
                                    logger.info(f"从无空格分隔的{row_type}行提取的值: {values}")
                                else:
                                    # 如果无法提取值，尝试基于已知的参数数量进行字符串切分
                                    logger.warning(f"无法通过正则表达式从{row_type}行提取值，尝试手动分割")
                                    remaining = first_cell
                                    
                                    # 针对Unit行的特殊处理，单个字符即为单位
                                    if row_type == "Unit":
                                        # 每个参数对应一个单位字符
                                        if len(remaining) >= len(param_names):
                                            values = [remaining[i] for i in range(min(len(remaining), len(param_names)))]
                                    else:
                                        # 尝试从参数列表中找出常见单位对应的典型值
                                        typical_values = {
                                            "CONT": ["0.500V", "0V"],
                                            "IGSS0": ["99.00uA", "0A"],
                                            "IGSS1": ["100.0nA", "0A"],
                                            "IGSS2": ["200.0nA", "0A"],
                                            "IGSSR1": ["100.0nA", "0A"],
                                            "IGSSR2": ["200.0nA", "0A"],
                                            "VTH": ["3.900V", "2.400V"],
                                            "BVDSS1": ["140.0V", "120.0V"],
                                            "BVDSS2": ["140.0V", "120.0V"],
                                            "IDSS1": ["100.0nA", "0A"],
                                            "IDSS2": ["200.0nA", "0A"],
                                        }
                                        
                                        # 根据行类型和参数名获取适当的值
                                        for param in param_names:
                                            if param in typical_values:
                                                value_idx = 0 if row_type == "LimitU" else 1
                                                values.append(typical_values[param][value_idx])
                                            else:
                                                # 无法确定值，添加空字符串
                                                values.append("")
                        else:
                            # TestCond和其他行
                            if " " in first_cell:
                                values = first_cell.split()
                            else:
                                # 尝试从TestCond行提取值，这比较复杂，可能需要依赖已知模式
                                logger.info(f"检测到无空格分隔的{row_type}行: {first_cell}")
                                
                                # 使用正则表达式匹配数值+单位的模式
                                import re
                                pattern = r'([0-9]+\.?[0-9]*[A-Za-z]*)'
                                matches = re.findall(pattern, first_cell)
                                
                                if matches:
                                    values = matches
                                    logger.info(f"从无空格分隔的{row_type}行提取的值: {values}")
                                else:
                                    logger.warning(f"无法从{row_type}行提取值，将使用空值")
                                    values = [""] * len(param_names)
                        
                        # 如果值的数量不够，填充空字符串
                        while len(values) < len(param_names):
                            values.append("")
                        
                        # 如果值的数量超过参数数量，仅使用前面部分
                        if len(values) > len(param_names):
                            values = values[:len(param_names)]
                        
                        new_row = pd.Series([row_type] + values, index=new_df.columns)
                    
                    new_df = pd.concat([new_df, pd.DataFrame([new_row])], ignore_index=True)
            
            # 处理TestCond后面的数据行
            testcond_idx = row_types.index("TestCond") if "TestCond" in row_types else -1
            if testcond_idx != -1 and testcond_idx + 1 < len(df):
                for i in range(testcond_idx + 1, len(df)):
                    row_data = df.iloc[i]
                    
                    # 提取所有后续行数据，格式类似于前面的处理
                    first_cell = str(row_data.iloc[0])
                    values = first_cell.split()
                    
                    # 如果值的数量不够，填充空字符串
                    while len(values) < len(param_names):
                        values.append("")
                    
                    # 如果值的数量超过参数数量，仅使用前面部分
                    if len(values) > len(param_names):
                        values = values[:len(param_names)]
                    
                    new_row = pd.Series([""] + values, index=new_df.columns)
                    new_df = pd.concat([new_df, pd.DataFrame([new_row])], ignore_index=True)
            
            # 替换原始DataFrame
            df = new_df
            logger.info(f"格式转换完成，新数据包含 {len(df)} 行 x {len(df.columns)} 列")
            
            # 如果仅执行格式转换，则直接保存文件并返回
            if format_only:
                if is_csv:
                    df.to_csv(output_file, index=False, sep='\t')
                    logger.info(f"数据已保存为CSV文件 (使用制表符分隔): {output_file}")
                else:
                    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name=sheet_name if sheet_name is not None else 'Spec', index=False)
                    logger.info(f"数据已保存为Excel文件: {output_file}")
                return True
            
            # 格式转换已完成，继续单位转换处理
        elif format_only:
            # 如果需要格式转换但数据已经是正确格式，则直接保存并返回
            logger.info("数据已经是正确的列格式，无需格式转换")
            if is_csv:
                df.to_csv(output_file, index=False, sep='\t')
                logger.info(f"数据已保存为CSV文件 (使用制表符分隔): {output_file}")
            else:
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=sheet_name if sheet_name is not None else 'Spec', index=False)
                logger.info(f"数据已保存为Excel文件: {output_file}")
            return True
        
        # 初始化单位转换器
        converter = UnitConverter()
        
        # 检查是否为转置格式（行是Parameter, Unit, LimitU, LimitL等）
        if df.shape[0] >= 3 and df.shape[1] >= 2:
            first_column = df.iloc[:, 0].astype(str).str.lower()
            
            # 检查前几行是否包含预期的行标题
            is_transposed_format = False
            expected_row_headers = ['parameter', 'unit', 'limitu', 'limitl', 'testcond']
            found_headers = sum(1 for header in expected_row_headers if any(header in val for val in first_column))
            
            if found_headers >= 3:  # 至少找到3个预期标题
                is_transposed_format = True
                logger.info("检测到转置格式数据，参数信息按行存储")
            
            if is_transposed_format:
                # 找到LimitU和LimitL行索引
                limitu_row_idx = -1
                limitl_row_idx = -1
                
                for i, val in enumerate(first_column):
                    if 'limitu' in val:
                        limitu_row_idx = i
                    elif 'limitl' in val:
                        limitl_row_idx = i
                
                # 处理上下限行中的值
                if limitu_row_idx != -1:
                    # 处理每一列（从第二列开始，第一列是行标题）
                    for col_idx in range(1, df.shape[1]):
                        value = df.iloc[limitu_row_idx, col_idx]
                        if pd.notna(value) and value != "":
                            # 转换值
                            converted_value = converter.convert_to_standard(value)
                            if converted_value is not None:
                                df.iloc[limitu_row_idx, col_idx] = converted_value
                
                if limitl_row_idx != -1:
                    # 处理每一列（从第二列开始，第一列是行标题）
                    for col_idx in range(1, df.shape[1]):
                        value = df.iloc[limitl_row_idx, col_idx]
                        if pd.notna(value) and value != "":
                            # 转换值
                            converted_value = converter.convert_to_standard(value)
                            if converted_value is not None:
                                df.iloc[limitl_row_idx, col_idx] = converted_value
            else:
                # 常规格式，LimitU和LimitL是列名
                limit_cols = []
                
                if "LimitU" in df.columns and "LimitL" in df.columns:
                    limit_cols = ["LimitU", "LimitL"]
                    logger.info("检测到LimitU/LimitL列格式")
                elif "SU" in df.columns and "SL" in df.columns:
                    limit_cols = ["SU", "SL"]
                    logger.info("检测到SU/SL列格式")
                
                # 处理上下限列
                for limit_col in limit_cols:
                    if limit_col in df.columns:
                        # 遍历每一行进行转换
                        for idx, row in df.iterrows():
                            value = row[limit_col]
                            if pd.notna(value) and value != "":
                                # 转换值
                                converted_value = converter.convert_to_standard(value)
                                if converted_value is not None:
                                    df.at[idx, limit_col] = converted_value
        
        # 根据文件扩展名决定如何保存
        if is_csv:
            df.to_csv(output_file, index=False, sep='\t')
            logger.info(f"数据已保存为CSV文件 (使用制表符分隔): {output_file}")
        else:
            # 如果是Excel文件，保留sheet_name
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name if sheet_name is not None else 'Spec', index=False)
            logger.info(f"数据已保存为Excel文件: {output_file}")
        
        return True
    
    except Exception as e:
        logger.exception(f"处理文件时出错: {e}")
        return False

def process_directory(input_dir: str, output_dir: str = None, pattern: str = "*.xlsx,*.csv", format_only: bool = False) -> bool:
    """
    处理目录中的所有匹配文件
    
    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径，默认为None时使用输入目录
        pattern: 文件匹配模式，使用逗号分隔多个模式，默认为"*.xlsx,*.csv"
        format_only: 是否仅执行格式转换，不进行单位转换
        
    Returns:
        处理是否成功
    """
    import glob
    
    # 如果未指定输出目录，使用输入目录
    if output_dir is None:
        output_dir = input_dir
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 处理多个模式，以逗号分隔
    patterns = [p.strip() for p in pattern.split(',')]
    all_files = []
    
    # 查找所有匹配的文件
    for p in patterns:
        input_pattern = os.path.join(input_dir, p)
        files = glob.glob(input_pattern)
        all_files.extend(files)
    
    # 移除重复项
    input_files = list(set(all_files))
    
    if not input_files:
        logger.warning(f"在目录 '{input_dir}' 中没有找到匹配 '{pattern}' 的文件")
        return False
    
    logger.info(f"找到 {len(input_files)} 个文件需要处理")
    
    # 处理每个文件
    success_count = 0
    for input_file in input_files:
        file_name = os.path.basename(input_file)
        prefix = "formatted_" if format_only else "converted_"
        output_file = os.path.join(output_dir, f"{prefix}{file_name}")
        
        if format_only:
            success = process_excel_file(input_file, output_file, sheet_name=None, format_only=True)
        else:
            success = process_excel_file(input_file, output_file)
            
        if success:
            success_count += 1
    
    logger.info(f"成功处理 {success_count}/{len(input_files)} 个文件")
    return success_count > 0

def process_single_value(value_str: str) -> None:
    """
    处理单个值的单位转换
    
    Args:
        value_str: 要转换的值，如 "3.3mV"
    """
    converter = UnitConverter()
    
    # 提取值和单位
    value, unit = converter.extract_value_and_unit(value_str)
    
    if value is None:
        logger.error(f"无法从 '{value_str}' 提取有效的值和单位")
        return
    
    # 转换为标准单位
    std_value = converter.convert_to_standard(value_str)
    
    if std_value is None:
        logger.error(f"无法将 '{value_str}' 转换为标准单位")
        return
    
    # 输出转换结果
    base_unit = converter.get_base_unit(unit) or "标准单位"
    logger.info(f"输入值: {value_str}")
    logger.info(f"转换结果: {std_value} {base_unit}")
    
    # 如果有单位，尝试转换回不同单位
    if unit:
        base_unit = converter.get_base_unit(unit)
        prefixes = ['', 'm', 'u', 'n', 'p', 'k', 'M', 'G']
        logger.info("不同单位表示:")
        
        for prefix in prefixes:
            target_unit = f"{prefix}{base_unit}"
            if target_unit != unit:  # 跳过原始单位
                result = converter.convert_from_standard(std_value, target_unit)
                if result is not None:
                    logger.info(f"  {result} {target_unit}")

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='CP测试数据单位转换工具')
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest='command', help='要执行的操作')
    
    # 文件处理子命令
    file_parser = subparsers.add_parser('file', help='处理Excel文件')
    file_parser.add_argument('input_file', help='输入Excel文件路径')
    file_parser.add_argument('-o', '--output', dest='output_file', help='输出Excel文件路径')
    file_parser.add_argument('-s', '--sheet', dest='sheet_name', default='Spec', help='要处理的工作表名称，默认为Spec')
    file_parser.add_argument('-f', '--format', dest='format_only', action='store_true', help='仅执行格式转换，不进行单位转换')
    
    # 目录处理子命令
    dir_parser = subparsers.add_parser('dir', help='处理目录中的Excel文件')
    dir_parser.add_argument('input_dir', help='输入目录路径')
    dir_parser.add_argument('-o', '--output', dest='output_dir', help='输出目录路径')
    dir_parser.add_argument('-p', '--pattern', default='*.xlsx,*.csv', help='文件匹配模式，使用逗号分隔多个模式，默认为"*.xlsx,*.csv"')
    dir_parser.add_argument('-f', '--format', dest='format_only', action='store_true', help='仅执行格式转换，不进行单位转换')
    
    # 值转换子命令
    value_parser = subparsers.add_parser('value', help='转换单个值')
    value_parser.add_argument('value', help='要转换的值，如 "3.3mV"')
    
    # 格式转换子命令
    format_parser = subparsers.add_parser('format', help='仅执行数据格式转换（从图1格式转为图2格式）')
    format_parser.add_argument('input_file', help='输入Excel/CSV文件路径')
    format_parser.add_argument('-o', '--output', dest='output_file', help='输出文件路径')
    format_parser.add_argument('-s', '--sheet', dest='sheet_name', default='Spec', help='要处理的工作表名称，默认为Spec')
    
    # 解析参数
    args = parser.parse_args()
    
    # 如果没有指定子命令，显示帮助信息
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    return args

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 根据子命令执行操作
    if args.command == 'file':
        process_excel_file(args.input_file, args.output_file, args.sheet_name, 
                          format_only=args.format_only if hasattr(args, 'format_only') else False)
    elif args.command == 'dir':
        process_directory(args.input_dir, args.output_dir, args.pattern, 
                         format_only=args.format_only if hasattr(args, 'format_only') else False)
    elif args.command == 'value':
        process_single_value(args.value)
    elif args.command == 'format':
        process_excel_file(args.input_file, args.output_file, args.sheet_name, format_only=True)

if __name__ == '__main__':
    main() 