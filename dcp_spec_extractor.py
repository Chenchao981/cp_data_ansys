#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DCP规格提取器

本脚本从DCP (Device Characterization Program) .txt文件的头部
提取参数规格信息，并将其保存到一个使用制表符分隔的CSV文件中。
"""

import os
import re
import csv
from datetime import datetime
from pathlib import Path
import logging

try:
    from cp_unit_converter import UnitConverter  # 导入UnitConverter类
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("无法导入UnitConverter类，请确保cp_unit_converter.py文件存在且在Python路径中")
    # 创建一个简单的备用转换器类
    class UnitConverter:
        """如果cp_unit_converter.py不可用，提供基本功能的备用单位转换器"""
        
        def __init__(self):
            self.prefix_map = {
                'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'μ': 1e-6, 
                'm': 1e-3, 'k': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12
            }
        
        def extract_value_and_unit(self, value_str):
            """从带单位的字符串中提取数值和单位"""
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
        
        def convert_to_standard(self, value_str):
            """将带单位的值转换为标准单位的值"""
            if isinstance(value_str, (int, float)):
                return float(value_str)
                
            value, unit = self.extract_value_and_unit(str(value_str))
            if value is None:
                return None
                
            # 如果没有单位，假设已经是标准单位
            if not unit:
                return value
                
            # 处理单位前缀
            unit_lower = unit.lower()
            for prefix, factor in self.prefix_map.items():
                if unit_lower.startswith(prefix.lower()):
                    return value * factor
            
            # 没有找到前缀，返回原值
            return value

# # 配置基本日志 (注释掉或删除这行，避免冲突)
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__) # __name__ 在这里是 'dcp_spec_extractor'
logger.setLevel(logging.DEBUG) # 强制为此logger设置DEBUG级别

# 如果此logger没有handler（例如，如果根logger没有配置或者没有传播），则添加一个
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)

def _extract_unit(value_str: str) -> str:
    """
    从字符串中提取并标准化单位 (V, A, ohm)。
    如果找到可识别的单位，则返回 'V', 'A', 'ohm'，否则返回空字符串。
    """
    if not isinstance(value_str, str):
        return ""
    value_str_lower = value_str.lower()
    if 'v' in value_str_lower:
        return 'V'
    if 'a' in value_str_lower:
        return 'A'
    if 'ohm' in value_str_lower:
        return 'ohm'
    return ""

def _format_value_for_csv(value: float | None) -> str:
    """
    将浮点数格式化为CSV所需的字符串格式。
    
    参数:
        value: 要格式化的浮点数，或者None（如果转换失败）
        
    返回:
        格式化后的字符串:
        - 科学计数法用于非常小或非常大的数字 (例如 "1E-07", "9.90E-05")
        - 普通数字格式用于其他情况 (例如 "0.5", "140", "0")
        - 空字符串，如果输入为None
    """
    if value is None:
        return ""
    
    # 对于0，直接返回"0"
    if value == 0:
        return "0"
    
    # 对于非常小的数值，使用科学计数法
    if abs(value) < 1e-3 and value != 0:
        return f"{value:.2E}"  # 例如 1E-07, 9.90E-05
    
    # 对于非常大的数值，使用科学计数法
    elif abs(value) >= 1e5:
        return f"{value:.2E}"
    
    # 对于浮点数，尝试保留合理的精度
    elif isinstance(value, float) and not value.is_integer():
        # 如果四舍五入到5位小数与原值非常接近
        if abs(value - round(value, 5)) < 1e-9:
            # 移除尾部的0和小数点
            return str(round(value, 5)).rstrip('0').rstrip('.')
        else:
            # 否则使用通用格式，可能会有较多小数
            return f"{value:g}"  # g会自动选择合适的表示
    
    # 整数或可以精确表示为整数的浮点数
    else:
        return str(int(value))

def generate_spec_file(dcp_file_path: str, output_dir: str, lot_id: str = None) -> str | None:
    """
    解析DCP文件的头部，提取规格数据，
    并将其写入一个使用制表符分隔的 _spec_.csv 文件。

    参数:
        dcp_file_path (str): 输入的DCP .txt文件路径。
        output_dir (str): 输出CSV文件将被保存的目录。
        lot_id (str, optional): 批次ID，用于统一文件命名。如果提供，将使用{lot_id}_spec_{timestamp}.csv格式。

    返回:
        str | None: 生成的CSV文件的路径，如果发生错误则返回None。
    """
    try:
        dcp_file = Path(dcp_file_path)
        if not dcp_file.exists() or not dcp_file.is_file():
            logger.error(f"DCP文件未找到或不是一个文件: {dcp_file_path}")
            return None
        
        # 创建单位转换器实例
        converter = UnitConverter()

        # 读取文件的前约20行，这应该包含头部信息
        header_lines = []
        with open(dcp_file, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if i >= 20: # 最多读取20行，应足以包含头部
                    break
                header_lines.append(line.strip())

        if len(header_lines) < 15: # 检查是否有足够的行用于典型的规格数据
            logger.warning(f"文件 {dcp_file_path} 的行数少于15行。规格数据可能不完整或缺失。")
            # 允许继续处理，但需注意结果可能不完整或失败。

        # --- 行索引 (0-based) 基于典型的DCP结构 ---
        # 参数名称行: 通常以 "No.U X Y Bin CONT..." 开头
        # 查找 "No.U" 然后是 "X" 然后是 "Y" 然后是 "Bin"
        param_line_idx = -1
        for i, line in enumerate(header_lines):
            parts = line.split('\t') # 使用实际的制表符进行分割
            if len(parts) > 4 and parts[0].strip() == "No.U" and \
               parts[1].strip() == "X" and parts[2].strip() == "Y" and \
               parts[3].strip() == "Bin":
                param_line_idx = i
                break
        
        if param_line_idx == -1:
            logger.error(f"在 {dcp_file_path} 中未找到参数标题行 (例如 'No.U X Y Bin...')")
            return None

        limit_u_line_idx = param_line_idx + 1
        limit_l_line_idx = param_line_idx + 2
        bias_start_line_idx = param_line_idx + 3
        bias_end_line_idx = bias_start_line_idx + 5 # Bias 1 到 Bias 6

        # --- 直接从源文件提取参数、限值和单位 ---
        # 参数从第5列开始 (索引为4)
        param_line = header_lines[param_line_idx].split('\t') # 使用实际的制表符
        limit_u_line = header_lines[limit_u_line_idx].split('\t')
        limit_l_line = header_lines[limit_l_line_idx].split('\t')
        
        # 检查行长度是否足够
        if len(param_line) <= 4:
            logger.error(f"文件 {dcp_file_path} 中的参数行没有足够的列: {header_lines[param_line_idx]}")
            return None
        
        # 提取参数名称 (从第5列开始，即索引4)
        parameters = [p.strip().strip('"') for p in param_line[4:]]
        num_params = len(parameters)
        
        # 提取原始的上限值字符串 (从第5列开始，即索引4)
        limit_u_values_original = []
        if len(limit_u_line) > 4:
            limit_u_values_original = [val.strip().strip('"') for val in limit_u_line[4:]]
            # 确保与参数列表长度一致
            if len(limit_u_values_original) < num_params:
                limit_u_values_original.extend([''] * (num_params - len(limit_u_values_original)))
            elif len(limit_u_values_original) > num_params:
                limit_u_values_original = limit_u_values_original[:num_params]
        else:
            limit_u_values_original = [''] * num_params
        
        # 提取原始的下限值字符串 (从第5列开始，即索引4)
        limit_l_values_original = []
        if len(limit_l_line) > 4:
            limit_l_values_original = [val.strip().strip('"') for val in limit_l_line[4:]]
            # 确保与参数列表长度一致
            if len(limit_l_values_original) < num_params:
                limit_l_values_original.extend([''] * (num_params - len(limit_l_values_original)))
            elif len(limit_l_values_original) > num_params:
                limit_l_values_original = limit_l_values_original[:num_params]
        else:
            limit_l_values_original = [''] * num_params
        
        # 提取单位 (从limit_u_values_original中提取)
        units = []
        for value in limit_u_values_original:
            unit = _extract_unit(value)
            units.append(unit)
        
        # 转换LimitU和LimitL为标准单位下的纯数值字符串
        limit_u_values_converted = []
        for i, val_str in enumerate(limit_u_values_original):
            # 转换为标准单位的浮点数
            standard_val_float = converter.convert_to_standard(val_str)
            # 格式化为CSV所需的字符串格式
            formatted_val = _format_value_for_csv(standard_val_float)
            limit_u_values_converted.append(formatted_val)
            logger.debug(f"LimitU转换: '{val_str}' -> {standard_val_float} -> '{formatted_val}'")

        limit_l_values_converted = []
        for i, val_str in enumerate(limit_l_values_original):
            # 转换为标准单位的浮点数
            standard_val_float = converter.convert_to_standard(val_str)
            # 格式化为CSV所需的字符串格式
            formatted_val = _format_value_for_csv(standard_val_float)
            limit_l_values_converted.append(formatted_val)
            logger.debug(f"LimitL转换: '{val_str}' -> {standard_val_float} -> '{formatted_val}'")
        
        # 准备输出数据
        output_data = []
        
        # 第1行: 参数名称
        output_data.append(["Parameter"] + parameters)
        
        # 第2行: 单位
        output_data.append(["Unit"] + units)
        
        # 第3行: 上限 (使用转换后的纯数值)
        output_data.append(["LimitU"] + limit_u_values_converted)
        
        # 第4行: 下限 (使用转换后的纯数值)
        output_data.append(["LimitL"] + limit_l_values_converted)

        # --- 处理Bias行，直接从源文件提取 ---
        # 创建对应Bias数据的行
        bias_rows = []
        
        for line_idx in range(bias_start_line_idx, min(bias_end_line_idx + 1, len(header_lines))):
            if line_idx < len(header_lines):
                bias_line = header_lines[line_idx].split('\t')
                
                # 如果是Bias行
                if len(bias_line) > 0 and bias_line[0].strip().startswith("Bias"):
                    # 获取从索引4开始的所有数据（对应参数列）
                    bias_data = [''] * num_params
                    
                    if len(bias_line) > 4:
                        # 直接从源文件复制相应列的数据
                        for i in range(min(len(bias_line) - 4, num_params)):
                            bias_data[i] = bias_line[i+4].strip().strip('"')
                    
                    # 特殊处理Bias 1行，第一行设为"TestCond:"
                    if line_idx == bias_start_line_idx:
                        bias_rows.append(["TestCond:"] + bias_data)
                    else:
                        bias_rows.append([''] + bias_data)
                else:
                    # 如果行不是以Bias开头但应该是Bias行（例如空行），添加空行
                    bias_rows.append([''] + [''] * num_params)
        
        # 添加所有Bias行数据
        output_data.extend(bias_rows)
        
        # 确保Output CSV内容中的所有行具有相同长度（参数数+1）
        expected_cols = num_params + 1
        for i, row in enumerate(output_data):
            if len(row) < expected_cols:
                output_data[i].extend([''] * (expected_cols - len(row)))
            elif len(row) > expected_cols:
                output_data[i] = row[:expected_cols]

        # --- 写入CSV文件 ---
        # 文件名: 如果提供了lot_id，使用统一格式 {lot_id}_spec_{timestamp}.csv，否则使用原格式
        if lot_id:
            output_filename = f"{lot_id}_spec_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        else:
            output_filename = f"{dcp_file.stem}_spec_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        output_path = Path(output_dir) / output_filename
        os.makedirs(output_dir, exist_ok=True)

        # 使用CSV模块写入，使用逗号作为分隔符
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            for i, row in enumerate(output_data):
                logger.debug(f"Writing row {i} to CSV: {row}")
                logger.debug(f"Type of row {i}: {type(row)}")
                if row:
                    logger.debug(f"Type of first element in row {i}: {type(row[0])}")
                writer.writerow(row)
        
        logger.info(f"成功生成规格文件: {output_path}")
        return str(output_path)

    except FileNotFoundError:
        logger.error(f"未找到输入DCP文件: {dcp_file_path}")
        return None
    except IndexError as e:
        logger.error(f"处理文件 {dcp_file_path} 时因数据缺失或格式不符导致错误 (IndexError): {e}")
        # 尝试记录发生问题的行号，如果param_line_idx已定义
        problem_line_info = str(param_line_idx) if 'param_line_idx' in locals() and param_line_idx != -1 else '未知或参数行解析前'
        logger.error(f"问题可能发生在参数行(或其后继行)解析，参数行索引: {problem_line_info}")
        return None
    except Exception as e:
        logger.exception(f"生成规格文件 {dcp_file_path} 时发生意外错误: {e}")
        return None

if __name__ == '__main__':
    # 用法示例 (用于测试目的)
    # 创建一个用于测试的伪DCP文件内容
    dummy_dcp_content = """Program name	ME58XX1_G00Z2AB.jtf													
Lot number	FA54-5339-327A-250501@203													
Wafer number	1													
Date	5/1/2025													
Time	0:49:13													
														
No.U	X	Y	Bin	CONT	IGSS0	IGSS1	IGSSR1	VTH	BVDSS1	BVDSS2	IDSS1	IDSS2	IGSS2	IGSSR2
LimitU				0.500V	99.00uA	100.0nA	100.0nA	3.900V	140.0V	140.0V	100.0nA	200.0nA	200.0nA	200.0nA
LimitL				0V	0A	0A	0A	2.400V	120.0V	120.0V	0A	0A	0A	0A
Bias 1				1.00mA	1.00V	10.0V	10.0V	250uA	250uA	10.0mA	110V	120V	18.0V	18.0V
Bias 2														
Bias 3									400V	400V				
Bias 4				2.50ms	10.0ms	40.0ms	40.0ms	2.00ms	20.0ms	10.0ms	20.0ms	20.0ms	40.0ms	40.0ms
Bias 5														
Bias 6														
"""
    test_dcp_dir = "test_dcp_data" # 测试数据目录
    os.makedirs(test_dcp_dir, exist_ok=True)
    test_dcp_file = Path(test_dcp_dir) / "sample_dcp.txt"
    with open(test_dcp_file, "w", encoding="utf-8") as f:
        f.write(dummy_dcp_content)

    output_directory = "output_spec_files" # 输出目录
    os.makedirs(output_directory, exist_ok=True)
    
    logger.info(f"使用伪文件进行测试: {test_dcp_file}")
    generated_file = generate_spec_file(str(test_dcp_file), output_directory)

    if generated_file:
        logger.info(f"测试生成的规格文件: {generated_file}")
        logger.info("请验证其内容。")
        # 可选: 打印内容以便快速检查
        with open(generated_file, 'r', encoding='utf-8') as f_check:
            print("--- 生成的规格文件内容 ---")
            print(f_check.read())
            print("------------------------------------")
    else:
        logger.error("测试规格文件生成失败。")

    # 清理伪文件和目录 (可选)
    # os.remove(test_dcp_file)
    # if not os.listdir(test_dcp_dir): # 仅当目录为空时删除
    #     os.rmdir(test_dcp_dir)
    # 如果此测试频繁运行，请考虑更稳健的清理方法 