"""
基础读取器抽象类，定义了所有 CP 数据读取器的通用接口。
"""

from abc import ABC, abstractmethod
from typing import List, Union, Optional
import os
import pandas as pd

from cp_data_processor.data_models.cp_data import CPLot


class BaseReader(ABC):
    """
    CP 数据读取器的抽象基类。
    所有具体格式的读取器都应继承此类并实现其抽象方法。
    """
    
    def __init__(self, file_paths: Union[str, List[str]], pass_bin: int = 1):
        """
        初始化读取器
        
        Args:
            file_paths: 要读取的文件路径，可以是单个字符串或字符串列表
            pass_bin: 表示通过的 Bin 值，默认为 1
        """
        # 标准化为列表
        self.file_paths = [file_paths] if isinstance(file_paths, str) else file_paths
        self.pass_bin = pass_bin
        self.lot = None  # 初始化为空，将在 read 方法中创建
    
    @abstractmethod
    def read(self) -> CPLot:
        """
        读取所有文件并返回一个填充好的 CPLot 对象。
        
        Returns:
            CPLot: 包含所有读取数据的 CPLot 对象
        """
        pass
    
    @abstractmethod
    def _extract_from_file(self, file_path: str, lot: CPLot) -> None:
        """
        从单个文件中提取数据到 CPLot 对象。
        
        Args:
            file_path: 要读取的文件路径
            lot: 要填充的 CPLot 对象
        """
        pass
    
    def get_file_extension(self, file_path: str) -> str:
        """获取文件扩展名（小写）"""
        _, ext = os.path.splitext(file_path)
        return ext.lower()
    
    def extract_lot_id(self, file_path: str) -> str:
        """从文件路径中提取 Lot ID"""
        # 默认使用文件名第一部分作为 Lot ID
        base_name = os.path.basename(file_path)
        # 移除扩展名
        name_without_ext = os.path.splitext(base_name)[0]
        # 尝试根据常见格式提取 Lot ID
        parts = name_without_ext.split('-')
        if len(parts) > 1:
            return parts[0]  # 假设 Lot ID 是第一部分
        return name_without_ext
    
    def extract_wafer_id(self, file_path: str) -> str:
        """从文件路径中提取 Wafer ID"""
        # 默认使用文件名的最后一部分作为 Wafer ID
        base_name = os.path.basename(file_path)
        # 移除扩展名
        name_without_ext = os.path.splitext(base_name)[0]
        # 尝试根据常见格式提取 Wafer ID
        parts = name_without_ext.split('-')
        if len(parts) > 1:
            return parts[-1]  # 假设 Wafer ID 是最后一部分
        return name_without_ext 