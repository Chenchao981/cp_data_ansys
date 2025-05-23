#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件数据适配器 - 兼容现有CSV文件结构
负责从output目录加载spec.csv、yield.csv、cleaned.csv文件
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List
import logging
import re

logger = logging.getLogger(__name__)

class FileAdapter:
    """文件数据适配器 - 兼容现有文件结构"""
    
    def __init__(self, data_dir="../output"):
        """
        初始化文件适配器
        
        Args:
            data_dir (str): 数据目录路径
        """
        self.data_dir = Path(data_dir)
        logger.info(f"FileAdapter 初始化 - 数据目录: {self.data_dir}")
        
        # 验证数据目录是否存在
        if not self.data_dir.exists():
            logger.warning(f"数据目录不存在: {self.data_dir}")
    
    def load_data(self, data_type: str, lot_id: Optional[str] = None, **kwargs) -> Optional[pd.DataFrame]:
        """
        从CSV文件加载数据
        
        Args:
            data_type (str): 数据类型 - "cleaned", "yield", "spec"
            lot_id (str): 批次ID
            **kwargs: 其他参数
            
        Returns:
            pandas.DataFrame: 数据，如果失败返回None
        """
        try:
            if data_type == "cleaned":
                return self._load_cleaned_data(lot_id)
            elif data_type == "yield":
                return self._load_yield_data(lot_id)
            elif data_type == "spec":
                return self._load_spec_data(lot_id)
            else:
                logger.error(f"未知数据类型: {data_type}")
                return None
                
        except Exception as e:
            logger.error(f"加载数据失败 - 类型: {data_type}, 批次: {lot_id}, 错误: {str(e)}")
            return None
    
    def _load_cleaned_data(self, lot_id: Optional[str]) -> Optional[pd.DataFrame]:
        """加载清洗后的测试数据"""
        files = self._find_files_by_pattern("*cleaned*.csv", lot_id)
        if not files:
            logger.warning(f"未找到cleaned数据文件 - 批次: {lot_id}")
            return None
        
        # 使用最新的文件
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        logger.info(f"加载cleaned数据: {latest_file}")
        
        try:
            data = pd.read_csv(latest_file)
            logger.info(f"Cleaned数据加载成功: {data.shape}")
            return data
        except Exception as e:
            logger.error(f"读取cleaned文件失败: {str(e)}")
            return None
    
    def _load_yield_data(self, lot_id: Optional[str]) -> Optional[pd.DataFrame]:
        """加载良率统计数据"""
        files = self._find_files_by_pattern("*yield*.csv", lot_id)
        if not files:
            logger.warning(f"未找到yield数据文件 - 批次: {lot_id}")
            return None
        
        # 使用最新的文件
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        logger.info(f"加载yield数据: {latest_file}")
        
        try:
            data = pd.read_csv(latest_file)
            logger.info(f"Yield数据加载成功: {data.shape}")
            return data
        except Exception as e:
            logger.error(f"读取yield文件失败: {str(e)}")
            return None
    
    def _load_spec_data(self, lot_id: Optional[str]) -> Optional[pd.DataFrame]:
        """加载参数规格数据"""
        files = self._find_files_by_pattern("*spec*.csv", lot_id)
        if not files:
            logger.warning(f"未找到spec数据文件 - 批次: {lot_id}")
            return None
        
        # 使用最新的文件
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        logger.info(f"加载spec数据: {latest_file}")
        
        try:
            data = pd.read_csv(latest_file)
            logger.info(f"Spec数据加载成功: {data.shape}")
            return data
        except Exception as e:
            logger.error(f"读取spec文件失败: {str(e)}")
            return None
    
    def _find_files_by_pattern(self, pattern: str, lot_id: Optional[str] = None) -> List[Path]:
        """
        根据模式和批次ID查找文件
        
        Args:
            pattern (str): 文件名模式，如 "*yield*.csv"
            lot_id (str): 批次ID
            
        Returns:
            List[Path]: 匹配的文件列表
        """
        if not self.data_dir.exists():
            return []
        
        # 如果指定了lot_id，优先查找包含lot_id的文件
        if lot_id:
            # 尝试包含完整lot_id的模式
            # 注意：pattern 已经包含了 *，所以不要重复添加
            if pattern.startswith('*'):
                specific_pattern = f"{lot_id}{pattern}"
            else:
                specific_pattern = f"{lot_id}*{pattern}"
            
            files = list(self.data_dir.glob(specific_pattern))
            if files:
                return files
            
            # 尝试包含lot_id部分的模式（例如只包含批次号前缀）
            lot_prefix = self._extract_lot_prefix(lot_id)
            if lot_prefix:
                if pattern.startswith('*'):
                    prefix_pattern = f"{lot_prefix}{pattern}"
                else:
                    prefix_pattern = f"{lot_prefix}*{pattern}"
                
                files = list(self.data_dir.glob(prefix_pattern))
                if files:
                    return files
        
        # 如果没有找到特定批次的文件，返回所有匹配模式的文件
        all_files = list(self.data_dir.glob(pattern))
        return all_files
    
    def _extract_lot_prefix(self, lot_id: str) -> Optional[str]:
        """
        从批次ID中提取前缀
        例如: "FA54-5339-327A-250501@203" -> "FA54-5339"
        """
        if not lot_id:
            return None
        
        # 使用正则表达式提取前缀
        match = re.match(r"(FA\d+-\d+)", lot_id)
        if match:
            return match.group(1)
        
        # 如果正则匹配失败，使用前两个短横线之间的部分
        parts = lot_id.split('-')
        if len(parts) >= 2:
            return f"{parts[0]}-{parts[1]}"
        
        return None
    
    def list_available_files(self) -> dict:
        """列出可用的数据文件"""
        if not self.data_dir.exists():
            return {}
        
        files_info = {
            "cleaned": list(self.data_dir.glob("*cleaned*.csv")),
            "yield": list(self.data_dir.glob("*yield*.csv")),
            "spec": list(self.data_dir.glob("*spec*.csv"))
        }
        
        # 转换为字符串以便显示
        result = {}
        for data_type, files in files_info.items():
            result[data_type] = [str(f.name) for f in files]
        
        return result
    
    def get_file_info(self, file_path: Path) -> dict:
        """获取文件信息"""
        if not file_path.exists():
            return {}
        
        stat = file_path.stat()
        return {
            "name": file_path.name,
            "path": str(file_path),
            "size": stat.st_size,
            "modified": stat.st_mtime
        }


def main():
    """测试文件适配器"""
    print("=== FileAdapter 测试 ===")
    
    # 创建文件适配器
    adapter = FileAdapter("../output")
    
    # 列出可用文件
    print("\n可用数据文件:")
    available_files = adapter.list_available_files()
    for data_type, files in available_files.items():
        print(f"  {data_type}: {len(files)} 个文件")
        for file_name in files[:3]:  # 只显示前3个
            print(f"    - {file_name}")
        if len(files) > 3:
            print(f"    ... 还有 {len(files)-3} 个文件")
    
    # 测试数据加载
    test_lot_id = "FA54-5339-327A-250501@203"
    
    print(f"\n测试加载数据 - 批次: {test_lot_id}")
    
    # 测试yield数据
    print("\n1. 加载yield数据:")
    yield_data = adapter.load_data("yield", test_lot_id)
    if yield_data is not None:
        print(f"   成功! 形状: {yield_data.shape}")
        print(f"   列名: {list(yield_data.columns)}")
        if len(yield_data) > 0:
            print(f"   前几行预览:")
            print(yield_data.head(3))
    else:
        print("   失败或数据不存在")
    
    # 测试spec数据
    print("\n2. 加载spec数据:")
    spec_data = adapter.load_data("spec", test_lot_id)
    if spec_data is not None:
        print(f"   成功! 形状: {spec_data.shape}")
        print(f"   列名: {list(spec_data.columns)}")
        if len(spec_data) > 0:
            print(f"   前几行预览:")
            print(spec_data.head(3))
    else:
        print("   失败或数据不存在")
    
    # 测试cleaned数据（比较大，只显示基本信息）
    print("\n3. 加载cleaned数据:")
    cleaned_data = adapter.load_data("cleaned", test_lot_id)
    if cleaned_data is not None:
        print(f"   成功! 形状: {cleaned_data.shape}")
        print(f"   列名: {list(cleaned_data.columns)}")
        print(f"   内存使用: {cleaned_data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    else:
        print("   失败或数据不存在")
    
    print("\n=== FileAdapter 测试完成 ===")


if __name__ == "__main__":
    main() 