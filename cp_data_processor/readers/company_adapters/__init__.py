"""
厂商适配器模块

该模块提供多厂商CP数据格式的统一适配功能，将不同厂商的数据格式转换为标准HH格式。

设计原则：
- 模块化：每个厂商一个独立适配器
- 可扩展：基于基类的插件式架构
- 配置驱动：通过配置文件管理厂商差异
- 向后兼容：保持现有HH格式功能不变
"""

from .base_company_adapter import BaseCompanyAdapter
from .company_config import COMPANY_CONFIGS, get_company_config
from .company_registry import CompanyRegistry, get_company_registry, get_adapter_for_file
from .hh_adapter import HHAdapter
from .jt_adapter import JTAdapter

__all__ = [
    'BaseCompanyAdapter',
    'COMPANY_CONFIGS', 
    'get_company_config',
    'CompanyRegistry',
    'get_company_registry',
    'get_adapter_for_file',
    'HHAdapter',
    'JTAdapter'
]

__version__ = '1.0.0' 