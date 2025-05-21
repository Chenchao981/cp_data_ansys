"""
单位转换模块，用于处理单位转换和提取。
"""

import re
import logging
from typing import Dict, Optional, Tuple, Union, Any
import numpy as np

logger = logging.getLogger(__name__)

class UnitConverter:
    """
    单位转换器类，处理单位提取和值转换。
    提供了将带单位的值转换为标准单位的功能。
    
    示例用法:
    ```
    converter = UnitConverter()
    # 提取单位
    unit = converter.extract_unit("3.3V")  # 返回 "V"
    # 转换带单位的值到标准单位
    value = converter.convert_to_standard("3.3mV")  # 返回 0.0033 (V)
    # 获取单位转换率
    rate = converter.get_unit_order_change_rate("mV")  # 返回 0.001
    ```
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