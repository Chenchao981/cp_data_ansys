#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSV处理器
提供CSV文件的路径解析、数据合并和预处理功能
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging
import re

# 设置日志
logger = logging.getLogger(__name__)

class CSVProcessor:
    """CSV文件处理器"""
    
    def __init__(self, data_dir: str = "../output"):
        """
        初始化CSV处理器
        
        Args:
            data_dir (str): CSV数据文件所在目录
        """
        self.data_dir = Path(data_dir)
        logger.info(f"CSVProcessor 初始化完成 - 数据目录: {self.data_dir}")
    
    def parse_lot_id_from_filename(self, filename: str) -> Optional[str]:
        """
        从文件名中解析批次ID
        
        Args:
            filename (str): 文件名
            
        Returns:
            str: 批次ID，解析失败返回None
        """
        try:
            # 移除文件扩展名
            name = Path(filename).stem
            
            # 尝试多种模式匹配批次ID
            patterns = [
                r'(FA\d{2}-\d{4}.*?)_[a-zA-Z]+$',  # FA54-5339@203_cleaned 格式
                r'(FA\d{2}-\d{4}.*)',              # FA54-5339@203 格式
                r'([A-Z0-9\-@#]+)_[a-zA-Z]+$',     # 通用格式 LOT_ID_datatype
                r'([A-Z0-9\-@#]+)',                # 通用批次ID格式
            ]
            
            for pattern in patterns:
                match = re.search(pattern, name)
                if match:
                    lot_id = match.group(1)
                    logger.debug(f"从文件名 {filename} 解析出批次ID: {lot_id}")
                    return lot_id
            
            logger.warning(f"无法从文件名解析批次ID: {filename}")
            return None
            
        except Exception as e:
            logger.error(f"解析批次ID时出错: {str(e)}")
            return None
    
    def validate_data_format(self, df: pd.DataFrame, data_type: str) -> Tuple[bool, List[str]]:
        """
        验证数据格式是否符合要求
        
        Args:
            df (pd.DataFrame): 数据框
            data_type (str): 数据类型 - "cleaned", "yield", "spec"
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        try:
            if df is None or df.empty:
                errors.append("数据框为空")
                return False, errors
            
            # 根据数据类型进行不同的验证
            if data_type == "cleaned":
                errors.extend(self._validate_cleaned_format(df))
            elif data_type == "yield":
                errors.extend(self._validate_yield_format(df))
            elif data_type == "spec":
                errors.extend(self._validate_spec_format(df))
            else:
                errors.append(f"未知的数据类型: {data_type}")
            
            is_valid = len(errors) == 0
            if is_valid:
                logger.info(f"{data_type}数据格式验证通过")
            else:
                logger.warning(f"{data_type}数据格式验证失败: {errors}")
            
            return is_valid, errors
            
        except Exception as e:
            error_msg = f"数据格式验证时出错: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def _validate_cleaned_format(self, df: pd.DataFrame) -> List[str]:
        """验证cleaned数据格式"""
        errors = []
        
        # 检查必要的列
        required_columns = ['LotID', 'WaferID', 'X', 'Y', 'Bin']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"缺少必要列: {missing_columns}")
        
        # 检查数据类型
        if 'X' in df.columns and not pd.api.types.is_numeric_dtype(df['X']):
            errors.append("X坐标列应为数值类型")
        
        if 'Y' in df.columns and not pd.api.types.is_numeric_dtype(df['Y']):
            errors.append("Y坐标列应为数值类型")
        
        if 'Bin' in df.columns and not pd.api.types.is_numeric_dtype(df['Bin']):
            errors.append("Bin列应为数值类型")
        
        # 检查是否有参数列（除了基础列之外的数值列）
        basic_columns = {'LotID', 'WaferID', 'Seq', 'X', 'Y', 'Bin', 'CONT'}
        param_columns = [col for col in df.columns if col not in basic_columns]
        if len(param_columns) == 0:
            errors.append("未找到参数数据列")
        
        return errors
    
    def _validate_yield_format(self, df: pd.DataFrame) -> List[str]:
        """验证yield数据格式"""
        errors = []
        
        # 检查必要的列
        required_columns = ['Parameter', 'Yield']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"缺少必要列: {missing_columns}")
        
        # 检查良率数据是否为数值类型
        if 'Yield' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['Yield']):
                errors.append("Yield列应为数值类型")
            else:
                # 检查良率范围是否合理（0-100%）
                yield_values = df['Yield'].dropna()
                if len(yield_values) > 0:
                    min_yield = yield_values.min()
                    max_yield = yield_values.max()
                    if min_yield < 0 or max_yield > 100:
                        errors.append(f"良率值超出合理范围[0,100]: min={min_yield}, max={max_yield}")
        
        return errors
    
    def _validate_spec_format(self, df: pd.DataFrame) -> List[str]:
        """验证spec数据格式"""
        errors = []
        
        # 检查必要的列
        required_columns = ['Parameter', 'Unit']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"缺少必要列: {missing_columns}")
        
        # 检查规格限值列（可选但常见）
        spec_columns = ['SL', 'SU', 'Lower_Limit', 'Upper_Limit', 'Min', 'Max']
        has_spec_limits = any(col in df.columns for col in spec_columns)
        if not has_spec_limits:
            errors.append("未找到规格限值列（SL/SU, Lower_Limit/Upper_Limit, Min/Max等）")
        
        return errors
    
    def merge_data_with_spec(self, data_df: pd.DataFrame, spec_df: pd.DataFrame, 
                           data_type: str = "cleaned") -> Optional[pd.DataFrame]:
        """
        将数据与规格信息合并
        
        Args:
            data_df (pd.DataFrame): 数据框（cleaned或yield）
            spec_df (pd.DataFrame): 规格数据框
            data_type (str): 数据类型 - "cleaned"或"yield"
            
        Returns:
            pd.DataFrame: 合并后的数据框，失败返回None
        """
        try:
            if data_df is None or spec_df is None:
                logger.error("输入数据为空，无法合并")
                return None
            
            logger.info(f"开始合并{data_type}数据与规格数据")
            
            # 根据数据类型选择不同的合并策略
            if data_type == "cleaned":
                return self._merge_cleaned_with_spec(data_df, spec_df)
            elif data_type == "yield":
                return self._merge_yield_with_spec(data_df, spec_df)
            else:
                logger.error(f"不支持的数据类型: {data_type}")
                return None
                
        except Exception as e:
            logger.error(f"合并数据时出错: {str(e)}")
            return None
    
    def _merge_cleaned_with_spec(self, cleaned_df: pd.DataFrame, spec_df: pd.DataFrame) -> pd.DataFrame:
        """将cleaned数据与规格信息合并"""
        try:
            # 获取参数列（排除基础列）
            basic_columns = {'LotID', 'WaferID', 'Seq', 'X', 'Y', 'Bin', 'CONT'}
            param_columns = [col for col in cleaned_df.columns if col not in basic_columns]
            
            logger.info(f"发现参数列: {len(param_columns)}个")
            
            # 为每个参数添加规格信息
            for param in param_columns:
                spec_row = spec_df[spec_df['Parameter'] == param]
                if not spec_row.empty:
                    # 添加单位信息
                    if 'Unit' in spec_row.columns:
                        unit = spec_row['Unit'].iloc[0]
                        cleaned_df[f"{param}_Unit"] = unit
                    
                    # 添加规格限值
                    for limit_col in ['SL', 'SU', 'Lower_Limit', 'Upper_Limit', 'Min', 'Max']:
                        if limit_col in spec_row.columns:
                            limit_value = spec_row[limit_col].iloc[0]
                            if pd.notna(limit_value):
                                cleaned_df[f"{param}_{limit_col}"] = limit_value
            
            logger.info(f"合并完成，新数据形状: {cleaned_df.shape}")
            return cleaned_df
            
        except Exception as e:
            logger.error(f"合并cleaned数据时出错: {str(e)}")
            return cleaned_df  # 返回原始数据
    
    def _merge_yield_with_spec(self, yield_df: pd.DataFrame, spec_df: pd.DataFrame) -> pd.DataFrame:
        """将yield数据与规格信息合并"""
        try:
            # 直接合并yield和spec数据
            merged_df = pd.merge(yield_df, spec_df, on='Parameter', how='left')
            
            logger.info(f"合并完成，新数据形状: {merged_df.shape}")
            return merged_df
            
        except Exception as e:
            logger.error(f"合并yield数据时出错: {str(e)}")
            return yield_df  # 返回原始数据
    
    def preprocess_data(self, df: pd.DataFrame, data_type: str) -> Optional[pd.DataFrame]:
        """
        数据预处理
        
        Args:
            df (pd.DataFrame): 输入数据
            data_type (str): 数据类型
            
        Returns:
            pd.DataFrame: 处理后的数据，失败返回None
        """
        try:
            if df is None or df.empty:
                return None
            
            logger.info(f"开始预处理{data_type}数据，原始形状: {df.shape}")
            
            processed_df = df.copy()
            
            # 通用预处理
            processed_df = self._clean_column_names(processed_df)
            processed_df = self._handle_missing_values(processed_df, data_type)
            
            # 特定类型的预处理
            if data_type == "cleaned":
                processed_df = self._preprocess_cleaned_data(processed_df)
            elif data_type == "yield":
                processed_df = self._preprocess_yield_data(processed_df)
            elif data_type == "spec":
                processed_df = self._preprocess_spec_data(processed_df)
            
            logger.info(f"预处理完成，新形状: {processed_df.shape}")
            return processed_df
            
        except Exception as e:
            logger.error(f"数据预处理时出错: {str(e)}")
            return df  # 返回原始数据
    
    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """清理列名"""
        # 去除列名中的空格和特殊字符
        df.columns = df.columns.str.strip()
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """处理缺失值"""
        # 根据数据类型采用不同的缺失值处理策略
        if data_type == "cleaned":
            # 对于测试数据，保留NaN值（可能表示未测试的参数）
            pass
        elif data_type in ["yield", "spec"]:
            # 对于yield和spec数据，可以考虑填充或删除空值
            # 这里暂时保持原样
            pass
        
        return df
    
    def _preprocess_cleaned_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """预处理cleaned数据"""
        # 确保坐标和Bin列为数值类型
        for col in ['X', 'Y', 'Bin']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def _preprocess_yield_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """预处理yield数据"""
        # 确保Yield列为数值类型
        if 'Yield' in df.columns:
            df['Yield'] = pd.to_numeric(df['Yield'], errors='coerce')
        
        # 按Parameter排序
        if 'Parameter' in df.columns:
            df = df.sort_values('Parameter')
        
        return df
    
    def _preprocess_spec_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """预处理spec数据"""
        # 确保规格限值列为数值类型
        limit_columns = ['SL', 'SU', 'Lower_Limit', 'Upper_Limit', 'Min', 'Max']
        for col in limit_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 按Parameter排序
        if 'Parameter' in df.columns:
            df = df.sort_values('Parameter')
        
        return df


def main():
    """测试CSV处理器"""
    print("=== CSV处理器测试 ===")
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 创建处理器
    processor = CSVProcessor("../output")
    
    # 测试文件名解析
    test_filenames = [
        "FA54-5339@203_cleaned.csv",
        "FA54-5340_yield.csv",
        "LOT12345_spec.csv",
        "test_cleaned.csv"
    ]
    
    print("测试批次ID解析:")
    for filename in test_filenames:
        lot_id = processor.parse_lot_id_from_filename(filename)
        print(f"  {filename} -> {lot_id}")
    
    # 测试数据验证（需要实际数据文件）
    # 这里只是演示接口
    print("\n数据格式验证功能已实现，需要实际CSV文件进行测试")


if __name__ == "__main__":
    main() 