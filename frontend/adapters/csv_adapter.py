#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSV数据适配器
提供CSV文件的读取和预处理功能
"""

import os
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List
import logging

# 设置日志
logger = logging.getLogger(__name__)

class CSVAdapter:
    """CSV文件数据适配器"""
    
    def __init__(self, data_dir: str = "../output"):
        """
        初始化CSV适配器
        
        Args:
            data_dir (str): CSV数据文件所在目录
        """
        self.data_dir = Path(data_dir)
        logger.info(f"CSVAdapter 初始化完成 - 数据目录: {self.data_dir}")
    
    def load_cleaned_data(self, lot_id: str) -> Optional[pd.DataFrame]:
        """
        加载清洗后的测试数据
        
        Args:
            lot_id (str): 批次ID，如 "FA54-5339@203"
            
        Returns:
            pandas.DataFrame: 清洗后的数据，失败返回None
        """
        try:
            file_path = self._find_csv_file(lot_id, "cleaned")
            if file_path is None:
                return None
            
            logger.info(f"加载cleaned数据: {file_path}")
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # 数据验证
            if df.empty:
                logger.warning(f"Cleaned数据文件为空: {file_path}")
                return None
            
            logger.info(f"Cleaned数据加载成功 - 形状: {df.shape}, 列数: {len(df.columns)}")
            return df
            
        except Exception as e:
            logger.error(f"加载cleaned数据失败: {str(e)}")
            return None
    
    def load_yield_data(self, lot_id: str) -> Optional[pd.DataFrame]:
        """
        加载良率统计数据
        
        Args:
            lot_id (str): 批次ID
            
        Returns:
            pandas.DataFrame: 良率数据，失败返回None
        """
        try:
            file_path = self._find_csv_file(lot_id, "yield")
            if file_path is None:
                return None
            
            logger.info(f"加载yield数据: {file_path}")
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # 数据验证
            if df.empty:
                logger.warning(f"Yield数据文件为空: {file_path}")
                return None
                
            # 检查必要列是否存在
            required_columns = ['Parameter', 'Yield']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"Yield数据缺少必要列: {missing_columns}")
            
            logger.info(f"Yield数据加载成功 - 形状: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"加载yield数据失败: {str(e)}")
            return None
    
    def load_spec_data(self, lot_id: str) -> Optional[pd.DataFrame]:
        """
        加载参数规格数据
        
        Args:
            lot_id (str): 批次ID
            
        Returns:
            pandas.DataFrame: 规格数据，失败返回None
        """
        try:
            file_path = self._find_csv_file(lot_id, "spec")
            if file_path is None:
                return None
            
            logger.info(f"加载spec数据: {file_path}")
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # 数据验证
            if df.empty:
                logger.warning(f"Spec数据文件为空: {file_path}")
                return None
                
            # 检查必要列是否存在
            required_columns = ['Parameter', 'Unit']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"Spec数据缺少必要列: {missing_columns}")
            
            logger.info(f"Spec数据加载成功 - 形状: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"加载spec数据失败: {str(e)}")
            return None
    
    def _find_csv_file(self, lot_id: str, data_type: str) -> Optional[Path]:
        """
        查找指定批次和数据类型的CSV文件
        
        Args:
            lot_id (str): 批次ID
            data_type (str): 数据类型 - "cleaned", "yield", "spec"
            
        Returns:
            Path: 文件路径，未找到返回None
        """
        try:
            # 移除批次ID中可能的特殊字符用于文件名匹配
            clean_lot_id = lot_id.replace("@", "_").replace("#", "_")
            
            # 尝试多种可能的文件名模式
            possible_patterns = [
                f"{clean_lot_id}_{data_type}.csv",
                f"{lot_id}_{data_type}.csv", 
                f"{data_type}_{clean_lot_id}.csv",
                f"{data_type}_{lot_id}.csv",
                f"{data_type}.csv"  # 通用文件名
            ]
            
            for pattern in possible_patterns:
                file_path = self.data_dir / pattern
                if file_path.exists():
                    logger.debug(f"找到文件: {file_path}")
                    return file_path
            
            # 如果精确匹配失败，尝试模糊匹配
            logger.debug(f"精确匹配失败，尝试模糊匹配: {lot_id}, {data_type}")
            return self._fuzzy_find_file(lot_id, data_type)
            
        except Exception as e:
            logger.error(f"查找CSV文件时出错: {str(e)}")
            return None
    
    def _fuzzy_find_file(self, lot_id: str, data_type: str) -> Optional[Path]:
        """
        模糊查找文件（包含关键字即可）
        
        Args:
            lot_id (str): 批次ID
            data_type (str): 数据类型
            
        Returns:
            Path: 文件路径，未找到返回None
        """
        try:
            if not self.data_dir.exists():
                logger.error(f"数据目录不存在: {self.data_dir}")
                return None
            
            # 提取批次ID的关键部分
            lot_key = lot_id.split("@")[0] if "@" in lot_id else lot_id
            lot_key = lot_key.split("#")[0] if "#" in lot_key else lot_key
            
            # 搜索包含关键字的CSV文件
            csv_files = list(self.data_dir.glob("*.csv"))
            
            for csv_file in csv_files:
                filename = csv_file.name.lower()
                if data_type.lower() in filename and lot_key.lower() in filename:
                    logger.info(f"模糊匹配找到文件: {csv_file}")
                    return csv_file
            
            # 如果仍然找不到，尝试只匹配数据类型
            for csv_file in csv_files:
                filename = csv_file.name.lower()
                if data_type.lower() in filename:
                    logger.info(f"按数据类型匹配找到文件: {csv_file}")
                    return csv_file
            
            logger.warning(f"未找到匹配的CSV文件: lot_id={lot_id}, data_type={data_type}")
            return None
            
        except Exception as e:
            logger.error(f"模糊查找文件时出错: {str(e)}")
            return None
    
    def list_available_lots(self) -> List[str]:
        """
        列出数据目录中可用的批次ID
        
        Returns:
            List[str]: 可用的批次ID列表
        """
        try:
            if not self.data_dir.exists():
                return []
            
            csv_files = list(self.data_dir.glob("*.csv"))
            lot_ids = set()
            
            for csv_file in csv_files:
                filename = csv_file.stem  # 不含扩展名的文件名
                
                # 尝试从文件名中提取批次ID
                # 假设文件名格式为: lot_id_datatype.csv
                parts = filename.split("_")
                if len(parts) >= 2:
                    # 重组批次ID（去掉最后一部分，通常是数据类型）
                    potential_lot_id = "_".join(parts[:-1])
                    lot_ids.add(potential_lot_id)
            
            result = list(lot_ids)
            logger.info(f"发现可用批次: {result}")
            return result
            
        except Exception as e:
            logger.error(f"列出可用批次时出错: {str(e)}")
            return []
    
    def get_data_info(self, lot_id: str) -> Dict[str, bool]:
        """
        获取指定批次的数据可用性信息
        
        Args:
            lot_id (str): 批次ID
            
        Returns:
            Dict[str, bool]: 数据类型到可用性的映射
        """
        info = {}
        data_types = ["cleaned", "yield", "spec"]
        
        for data_type in data_types:
            file_path = self._find_csv_file(lot_id, data_type)
            info[data_type] = file_path is not None
        
        logger.info(f"批次 {lot_id} 数据可用性: {info}")
        return info


def main():
    """测试CSV适配器"""
    print("=== CSV适配器测试 ===")
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 创建适配器
    adapter = CSVAdapter("../output")
    
    # 列出可用批次
    lots = adapter.list_available_lots()
    print(f"可用批次: {lots}")
    
    if lots:
        # 测试第一个批次
        test_lot = lots[0]
        print(f"\n测试批次: {test_lot}")
        
        # 检查数据可用性
        info = adapter.get_data_info(test_lot)
        print(f"数据可用性: {info}")
        
        # 尝试加载各种数据
        if info.get('cleaned'):
            cleaned = adapter.load_cleaned_data(test_lot)
            if cleaned is not None:
                print(f"Cleaned数据形状: {cleaned.shape}")
        
        if info.get('yield'):
            yield_data = adapter.load_yield_data(test_lot)
            if yield_data is not None:
                print(f"Yield数据形状: {yield_data.shape}")
        
        if info.get('spec'):
            spec = adapter.load_spec_data(test_lot)
            if spec is not None:
                print(f"Spec数据形状: {spec.shape}")
    else:
        print("未找到可用的批次数据")


if __name__ == "__main__":
    main() 