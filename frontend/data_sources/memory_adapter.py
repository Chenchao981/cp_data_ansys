#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存数据适配器 - 支持直接处理DataFrame数据
用于高性能的内存数据处理和缓存
"""

import pandas as pd
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class MemoryAdapter:
    """内存数据适配器 - 支持直接处理DataFrame"""
    
    def __init__(self):
        """初始化内存适配器"""
        self.memory_store = {}  # 内存数据存储
        logger.info("MemoryAdapter 初始化完成")
    
    def load_data(self, data_type: str, lot_id: Optional[str] = None, **kwargs) -> Optional[pd.DataFrame]:
        """
        从内存获取数据
        
        Args:
            data_type (str): 数据类型 - "cleaned", "yield", "spec"
            lot_id (str): 批次ID
            **kwargs: 其他参数
            
        Returns:
            pandas.DataFrame: 数据，如果不存在返回None
        """
        key = self._generate_key(data_type, lot_id)
        
        if key in self.memory_store:
            data = self.memory_store[key]
            logger.info(f"从内存获取数据成功: {key}, 形状: {data.shape}")
            return data.copy()  # 返回副本避免意外修改
        else:
            logger.debug(f"内存中未找到数据: {key}")
            return None
    
    def store_data(self, data_type: str, data: pd.DataFrame, lot_id: Optional[str] = None):
        """
        存储数据到内存
        
        Args:
            data_type (str): 数据类型
            data (pd.DataFrame): 要存储的数据
            lot_id (str): 批次ID
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError("数据必须是pandas DataFrame")
        
        key = self._generate_key(data_type, lot_id)
        self.memory_store[key] = data.copy()  # 存储副本
        
        logger.info(f"数据已存储到内存: {key}, 形状: {data.shape}")
    
    def _generate_key(self, data_type: str, lot_id: Optional[str]) -> str:
        """生成内存存储键"""
        if lot_id:
            return f"{data_type}_{lot_id}"
        else:
            return data_type
    
    def clear_cache(self):
        """清空内存缓存"""
        count = len(self.memory_store)
        self.memory_store.clear()
        logger.info(f"内存缓存已清空，释放 {count} 个数据对象")
    
    def remove_data(self, data_type: str, lot_id: Optional[str] = None):
        """删除指定数据"""
        key = self._generate_key(data_type, lot_id)
        if key in self.memory_store:
            del self.memory_store[key]
            logger.info(f"数据已从内存删除: {key}")
        else:
            logger.warning(f"尝试删除不存在的数据: {key}")
    
    def list_stored_data(self) -> Dict[str, Any]:
        """列出内存中存储的数据"""
        result = {}
        for key, data in self.memory_store.items():
            result[key] = {
                "shape": data.shape,
                "columns": list(data.columns),
                "memory_usage_mb": data.memory_usage(deep=True).sum() / 1024 / 1024,
                "dtypes": data.dtypes.to_dict()
            }
        return result
    
    def get_memory_info(self) -> Dict[str, Any]:
        """获取内存使用信息"""
        total_memory = 0
        data_count = len(self.memory_store)
        
        for data in self.memory_store.values():
            total_memory += data.memory_usage(deep=True).sum()
        
        return {
            "data_count": data_count,
            "total_memory_mb": total_memory / 1024 / 1024,
            "keys": list(self.memory_store.keys())
        }
    
    def has_data(self, data_type: str, lot_id: Optional[str] = None) -> bool:
        """检查是否存在指定数据"""
        key = self._generate_key(data_type, lot_id)
        return key in self.memory_store
    
    def get_data_info(self, data_type: str, lot_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取指定数据的信息"""
        key = self._generate_key(data_type, lot_id)
        if key not in self.memory_store:
            return None
        
        data = self.memory_store[key]
        return {
            "key": key,
            "shape": data.shape,
            "columns": list(data.columns),
            "memory_usage_mb": data.memory_usage(deep=True).sum() / 1024 / 1024,
            "dtypes": data.dtypes.to_dict(),
            "null_counts": data.isnull().sum().to_dict()
        }


def main():
    """测试内存适配器"""
    print("=== MemoryAdapter 测试 ===")
    
    # 创建内存适配器
    adapter = MemoryAdapter()
    
    # 创建测试数据
    print("\n1. 创建测试数据")
    test_data = {
        'Lot_ID': ['TEST_LOT'] * 5,
        'Wafer_ID': [1, 1, 1, 2, 2],
        'Seq': [1, 2, 3, 1, 2],
        'Bin': [1, 1, 1, 1, 1],
        'X': [10, 11, 12, 10, 11],
        'Y': [20, 21, 22, 20, 21],
        'VTH': [3.1, 3.2, 3.0, 3.15, 3.25]
    }
    test_df = pd.DataFrame(test_data)
    print(f"测试数据创建完成: {test_df.shape}")
    
    # 存储数据
    print("\n2. 存储数据到内存")
    adapter.store_data("cleaned", test_df, "TEST_LOT")
    adapter.store_data("test", test_df.head(3), "SAMPLE")
    
    # 检查内存信息
    print("\n3. 内存信息:")
    memory_info = adapter.get_memory_info()
    print(f"   存储数据数量: {memory_info['data_count']}")
    print(f"   总内存使用: {memory_info['total_memory_mb']:.3f} MB")
    print(f"   存储键: {memory_info['keys']}")
    
    # 列出存储的数据
    print("\n4. 存储的数据详情:")
    stored_data = adapter.list_stored_data()
    for key, info in stored_data.items():
        print(f"   {key}:")
        print(f"     形状: {info['shape']}")
        print(f"     列名: {info['columns']}")
        print(f"     内存: {info['memory_usage_mb']:.3f} MB")
    
    # 测试数据加载
    print("\n5. 测试数据加载:")
    loaded_data = adapter.load_data("cleaned", "TEST_LOT")
    if loaded_data is not None:
        print(f"   加载成功! 形状: {loaded_data.shape}")
        print(f"   数据预览:")
        print(loaded_data.head())
    else:
        print("   加载失败")
    
    # 测试数据检查
    print("\n6. 测试数据检查:")
    has_data = adapter.has_data("cleaned", "TEST_LOT")
    print(f"   是否存在cleaned_TEST_LOT: {has_data}")
    
    has_nonexistent = adapter.has_data("cleaned", "NONEXISTENT")
    print(f"   是否存在cleaned_NONEXISTENT: {has_nonexistent}")
    
    # 获取数据详细信息
    print("\n7. 数据详细信息:")
    data_info = adapter.get_data_info("cleaned", "TEST_LOT")
    if data_info:
        print(f"   键: {data_info['key']}")
        print(f"   形状: {data_info['shape']}")
        print(f"   列名: {data_info['columns']}")
        print(f"   内存使用: {data_info['memory_usage_mb']:.3f} MB")
        print(f"   空值统计: {data_info['null_counts']}")
    
    # 删除数据
    print("\n8. 测试数据删除:")
    adapter.remove_data("test", "SAMPLE")
    memory_info_after = adapter.get_memory_info()
    print(f"   删除后数据数量: {memory_info_after['data_count']}")
    print(f"   剩余键: {memory_info_after['keys']}")
    
    # 清空缓存
    print("\n9. 清空缓存:")
    adapter.clear_cache()
    final_info = adapter.get_memory_info()
    print(f"   清空后数据数量: {final_info['data_count']}")
    
    print("\n=== MemoryAdapter 测试完成 ===")


if __name__ == "__main__":
    main() 