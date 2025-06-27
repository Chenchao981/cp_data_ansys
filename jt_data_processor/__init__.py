"""
JT数据处理器模块

专门用于处理JT公司的CP测试数据，基于HH公司的成熟数据处理技术。

主要组件：
- JTReader: JT Excel文件读取器
- JTAdapter: JT数据适配器
- JTConfig: JT公司配置管理

设计原则：
- 基于HH公司成熟技术
- 不调用单位转换逻辑
- 使用IQR四分位法处理异常值
- 保持数据完整性
"""

__version__ = '1.0.0'
__author__ = 'CP Data Analysis Team'

# 导入核心组件
from .readers.jt_reader import JTReader
from .adapters.jt_adapter import JTAdapter
from .config.jt_config import JTConfig

__all__ = [
    'JTReader',
    'JTAdapter', 
    'JTConfig'
] 