"""
Lion公司适配器

Lion公司Excel格式CP测试数据处理适配器，将Lion格式转换为HH标准格式。
"""

import sys
import os
from pathlib import Path

# 添加lion模块路径
lion_module_path = Path(__file__).parent.parent.parent.parent / "lion"
sys.path.insert(0, str(lion_module_path))

# 导入Lion适配器
from lion_adapter import LionAdapter as BaseLionAdapter

# 为了符合命名约定，创建别名
LIONAdapter = BaseLionAdapter

__all__ = ['LIONAdapter']