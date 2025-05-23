#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据管理器 - 混合式架构的核心组件
支持文件、内存、缓存多种数据源的统一管理
"""

import os
import sys
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataManager:
    """混合式数据管理器 - 支持文件/内存/缓存多种数据源"""
    
    def __init__(self, data_source="auto", cache_enabled=True, data_dir="../output"):
        """
        初始化数据管理器
        
        Args:
            data_source (str): 数据源类型 - "file", "memory", "cache", "auto"
            cache_enabled (bool): 是否启用缓存
            data_dir (str): 数据目录路径
        """
        self.data_source = data_source
        self.cache_enabled = cache_enabled
        self.data_dir = Path(data_dir)
        self.cache_data = {}  # 内存缓存
        
        # 初始化适配器（延迟导入避免循环依赖）
        self.file_adapter = None
        self.memory_adapter = None
        self.cache_adapter = None
        
        logger.info(f"DataManager 初始化完成 - 数据源: {data_source}, 缓存: {cache_enabled}")
    
    def _init_adapters(self):
        """延迟初始化适配器"""
        if self.file_adapter is None:
            from ..data_sources.file_adapter import FileAdapter
            self.file_adapter = FileAdapter(self.data_dir)
        
        if self.memory_adapter is None:
            from ..data_sources.memory_adapter import MemoryAdapter
            self.memory_adapter = MemoryAdapter()
    
    def get_data(self, data_type: str, lot_id: Optional[str] = None, **kwargs) -> Optional[pd.DataFrame]:
        """
        统一数据获取接口
        
        Args:
            data_type (str): 数据类型 - "cleaned", "yield", "spec"
            lot_id (str): 批次ID
            **kwargs: 其他参数
            
        Returns:
            pandas.DataFrame: 数据，如果失败返回None
        """
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(data_type, lot_id, **kwargs)
            
            # 1. 尝试从缓存获取
            if self.cache_enabled and cache_key in self.cache_data:
                logger.info(f"从缓存获取数据: {cache_key}")
                return self.cache_data[cache_key]
            
            # 2. 根据配置选择数据源
            data = None
            if self.data_source == "file":
                data = self._load_from_file(data_type, lot_id, **kwargs)
            elif self.data_source == "memory":
                data = self._load_from_memory(data_type, lot_id, **kwargs)
            elif self.data_source == "auto":
                data = self._auto_load_data(data_type, lot_id, **kwargs)
            else:
                raise ValueError(f"不支持的数据源类型: {self.data_source}")
            
            # 3. 缓存数据
            if self.cache_enabled and data is not None:
                self.cache_data[cache_key] = data.copy()  # 存储副本避免意外修改
                logger.info(f"数据已缓存: {cache_key}, 形状: {data.shape}")
            
            return data
            
        except Exception as e:
            logger.error(f"获取数据失败 - 类型: {data_type}, 批次: {lot_id}, 错误: {str(e)}")
            return None
    
    def _load_from_file(self, data_type: str, lot_id: Optional[str], **kwargs) -> Optional[pd.DataFrame]:
        """从文件加载数据"""
        self._init_adapters()
        logger.info(f"从文件加载数据: {data_type}, 批次: {lot_id}")
        return self.file_adapter.load_data(data_type, lot_id, **kwargs)
    
    def _load_from_memory(self, data_type: str, lot_id: Optional[str], **kwargs) -> Optional[pd.DataFrame]:
        """从内存加载数据"""
        self._init_adapters()
        logger.info(f"从内存加载数据: {data_type}, 批次: {lot_id}")
        return self.memory_adapter.load_data(data_type, lot_id, **kwargs)
    
    def _auto_load_data(self, data_type: str, lot_id: Optional[str], **kwargs) -> Optional[pd.DataFrame]:
        """智能数据源选择（优先内存，fallback到文件）"""
        self._init_adapters()
        
        try:
            # 优先尝试内存
            logger.info(f"尝试从内存加载数据: {data_type}, 批次: {lot_id}")
            data = self.memory_adapter.load_data(data_type, lot_id, **kwargs)
            if data is not None:
                logger.info(f"内存加载成功: {data.shape}")
                return data
        except Exception as e:
            logger.debug(f"内存加载失败: {str(e)}")
        
        # fallback到文件
        try:
            logger.info(f"Fallback到文件加载数据: {data_type}, 批次: {lot_id}")
            data = self.file_adapter.load_data(data_type, lot_id, **kwargs)
            if data is not None:
                logger.info(f"文件加载成功: {data.shape}")
                return data
        except Exception as e:
            logger.error(f"文件加载也失败: {str(e)}")
        
        return None
    
    def _generate_cache_key(self, data_type: str, lot_id: Optional[str], **kwargs) -> str:
        """生成缓存键"""
        key_parts = [data_type]
        if lot_id:
            key_parts.append(lot_id)
        if kwargs:
            # 将kwargs转换为排序的字符串
            kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key_parts.append(kwargs_str)
        return "_".join(key_parts)
    
    def store_data(self, data_type: str, data: pd.DataFrame, lot_id: Optional[str] = None):
        """存储数据到内存适配器"""
        self._init_adapters()
        self.memory_adapter.store_data(data_type, data, lot_id)
        logger.info(f"数据已存储到内存: {data_type}, 批次: {lot_id}, 形状: {data.shape}")
    
    def clear_cache(self):
        """清空缓存"""
        self.cache_data.clear()
        if self.memory_adapter:
            self.memory_adapter.clear_cache()
        logger.info("缓存已清空")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        info = {
            "cache_enabled": self.cache_enabled,
            "cache_size": len(self.cache_data),
            "cache_keys": list(self.cache_data.keys()),
            "data_source": self.data_source,
            "data_dir": str(self.data_dir)
        }
        return info


def main():
    """测试数据管理器"""
    print("=== DataManager 测试 ===")
    
    # 创建数据管理器
    dm = DataManager(data_source="file", cache_enabled=True)
    
    # 显示配置信息
    info = dm.get_cache_info()
    print(f"配置信息: {info}")
    
    # 测试数据加载（如果有数据的话）
    try:
        # 尝试加载一些测试数据
        test_lot_id = "FA54-5339-327A-250501@203"
        
        print(f"\n尝试加载yield数据 - 批次: {test_lot_id}")
        yield_data = dm.get_data("yield", test_lot_id)
        if yield_data is not None:
            print(f"Yield数据加载成功: {yield_data.shape}")
            print(f"列名: {list(yield_data.columns)}")
        else:
            print("Yield数据加载失败或数据不存在")
        
        print(f"\n尝试加载spec数据 - 批次: {test_lot_id}")
        spec_data = dm.get_data("spec", test_lot_id)
        if spec_data is not None:
            print(f"Spec数据加载成功: {spec_data.shape}")
            print(f"列名: {list(spec_data.columns)}")
        else:
            print("Spec数据加载失败或数据不存在")
            
        # 显示缓存信息
        print(f"\n缓存信息: {dm.get_cache_info()}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
    
    print("\n=== DataManager 测试完成 ===")


if __name__ == "__main__":
    main() 