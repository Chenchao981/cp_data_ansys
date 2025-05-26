#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据验证工具模块
提供数据格式、内容验证等功能
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
import logging
import re

# 设置日志
logger = logging.getLogger(__name__)

class DataValidator:
    """数据验证工具类"""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, required_columns: List[str] = None,
                          data_type: str = "unknown") -> Tuple[bool, List[str]]:
        """
        验证DataFrame的基本有效性
        
        Args:
            df (pd.DataFrame): 要验证的数据框
            required_columns (List[str]): 必需的列名列表
            data_type (str): 数据类型描述
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        try:
            # 检查DataFrame是否为空
            if df is None:
                errors.append("数据框为None")
                return False, errors
            
            if df.empty:
                errors.append("数据框为空")
                return False, errors
            
            # 检查必需列
            if required_columns:
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    errors.append(f"缺少必需列: {missing_columns}")
            
            # 检查数据框基本信息
            row_count, col_count = df.shape
            if row_count == 0:
                errors.append("数据框没有行数据")
            if col_count == 0:
                errors.append("数据框没有列")
            
            # 检查是否有重复列名
            duplicated_columns = df.columns[df.columns.duplicated()].tolist()
            if duplicated_columns:
                errors.append(f"存在重复列名: {duplicated_columns}")
            
            is_valid = len(errors) == 0
            if is_valid:
                logger.info(f"{data_type}数据框验证通过 - 形状: {df.shape}")
            else:
                logger.warning(f"{data_type}数据框验证失败: {errors}")
            
            return is_valid, errors
            
        except Exception as e:
            error_msg = f"验证数据框时出错: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    @staticmethod
    def validate_numeric_column(df: pd.DataFrame, column_name: str,
                               min_value: float = None, max_value: float = None,
                               allow_nan: bool = True) -> Tuple[bool, List[str]]:
        """
        验证数值列的有效性
        
        Args:
            df (pd.DataFrame): 数据框
            column_name (str): 列名
            min_value (float): 最小值限制，可选
            max_value (float): 最大值限制，可选
            allow_nan (bool): 是否允许NaN值，默认True
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        try:
            if column_name not in df.columns:
                errors.append(f"列不存在: {column_name}")
                return False, errors
            
            column_data = df[column_name]
            
            # 检查数据类型
            if not pd.api.types.is_numeric_dtype(column_data):
                errors.append(f"列 {column_name} 不是数值类型")
                return False, errors
            
            # 检查NaN值
            nan_count = column_data.isna().sum()
            total_count = len(column_data)
            
            if not allow_nan and nan_count > 0:
                errors.append(f"列 {column_name} 包含 {nan_count} 个NaN值，但不允许NaN")
            
            # 检查有效数据
            valid_data = column_data.dropna()
            if len(valid_data) == 0:
                errors.append(f"列 {column_name} 没有有效数值数据")
                return False, errors
            
            # 检查范围
            if min_value is not None:
                below_min = (valid_data < min_value).sum()
                if below_min > 0:
                    errors.append(f"列 {column_name} 有 {below_min} 个值小于最小值 {min_value}")
            
            if max_value is not None:
                above_max = (valid_data > max_value).sum()
                if above_max > 0:
                    errors.append(f"列 {column_name} 有 {above_max} 个值大于最大值 {max_value}")
            
            # 检查异常值（使用IQR方法）
            outlier_info = DataValidator.detect_outliers(valid_data)
            if outlier_info['outlier_count'] > 0:
                outlier_ratio = outlier_info['outlier_count'] / len(valid_data)
                if outlier_ratio > 0.1:  # 超过10%的数据是异常值
                    errors.append(f"列 {column_name} 有过多异常值: {outlier_info['outlier_count']}/{len(valid_data)} ({outlier_ratio:.1%})")
            
            is_valid = len(errors) == 0
            if is_valid:
                logger.debug(f"数值列 {column_name} 验证通过")
            
            return is_valid, errors
            
        except Exception as e:
            error_msg = f"验证数值列 {column_name} 时出错: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    @staticmethod
    def validate_categorical_column(df: pd.DataFrame, column_name: str,
                                  valid_categories: List[Any] = None,
                                  max_categories: int = None) -> Tuple[bool, List[str]]:
        """
        验证分类列的有效性
        
        Args:
            df (pd.DataFrame): 数据框
            column_name (str): 列名
            valid_categories (List[Any]): 有效类别列表，可选
            max_categories (int): 最大类别数量，可选
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        try:
            if column_name not in df.columns:
                errors.append(f"列不存在: {column_name}")
                return False, errors
            
            column_data = df[column_name]
            
            # 获取唯一值
            unique_values = column_data.dropna().unique()
            unique_count = len(unique_values)
            
            # 检查类别数量
            if max_categories is not None and unique_count > max_categories:
                errors.append(f"列 {column_name} 类别数量 ({unique_count}) 超过限制 ({max_categories})")
            
            # 检查有效类别
            if valid_categories is not None:
                invalid_values = [val for val in unique_values if val not in valid_categories]
                if invalid_values:
                    errors.append(f"列 {column_name} 包含无效类别: {invalid_values}")
            
            is_valid = len(errors) == 0
            if is_valid:
                logger.debug(f"分类列 {column_name} 验证通过，包含 {unique_count} 个类别")
            
            return is_valid, errors
            
        except Exception as e:
            error_msg = f"验证分类列 {column_name} 时出错: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    @staticmethod
    def detect_outliers(data: pd.Series, method: str = "iqr") -> Dict:
        """
        检测异常值
        
        Args:
            data (pd.Series): 数据序列
            method (str): 检测方法，"iqr"或"zscore"
            
        Returns:
            Dict: 异常值信息
        """
        try:
            data_clean = data.dropna()
            
            if len(data_clean) == 0:
                return {'outlier_count': 0, 'outlier_indices': [], 'method': method}
            
            if method == "iqr":
                Q1 = data_clean.quantile(0.25)
                Q3 = data_clean.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = (data_clean < lower_bound) | (data_clean > upper_bound)
                
            elif method == "zscore":
                z_scores = np.abs((data_clean - data_clean.mean()) / data_clean.std())
                outliers = z_scores > 3
                
            else:
                raise ValueError(f"未知的异常值检测方法: {method}")
            
            outlier_indices = data_clean[outliers].index.tolist()
            
            return {
                'outlier_count': len(outlier_indices),
                'outlier_indices': outlier_indices,
                'outlier_ratio': len(outlier_indices) / len(data_clean),
                'method': method,
                'bounds': {'lower': lower_bound, 'upper': upper_bound} if method == "iqr" else None
            }
            
        except Exception as e:
            logger.error(f"检测异常值时出错: {str(e)}")
            return {'outlier_count': 0, 'outlier_indices': [], 'method': method, 'error': str(e)}
    
    @staticmethod
    def validate_lot_id_format(lot_id: str) -> Tuple[bool, str]:
        """
        验证批次ID格式
        
        Args:
            lot_id (str): 批次ID
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            if not lot_id or not isinstance(lot_id, str):
                return False, "批次ID为空或不是字符串"
            
            # 去除前后空格
            lot_id = lot_id.strip()
            
            if len(lot_id) == 0:
                return False, "批次ID为空字符串"
            
            # 检查常见的批次ID格式
            patterns = [
                r'^FA\d{2}-\d{4}.*@\d{3}$',  # FA54-5339@203 格式
                r'^[A-Z0-9\-_@#]+$',         # 通用格式（字母数字和常见符号）
            ]
            
            for pattern in patterns:
                if re.match(pattern, lot_id):
                    return True, ""
            
            # 如果不匹配任何模式，检查是否包含非法字符
            illegal_chars = '<>:"|?*\\/'
            for char in illegal_chars:
                if char in lot_id:
                    return False, f"批次ID包含非法字符: {char}"
            
            # 长度检查
            if len(lot_id) > 50:
                return False, "批次ID过长（超过50字符）"
            
            return True, ""
            
        except Exception as e:
            return False, f"验证批次ID时出错: {str(e)}"
    
    @staticmethod
    def validate_parameter_data(df: pd.DataFrame) -> Dict:
        """
        验证参数测试数据的完整性
        
        Args:
            df (pd.DataFrame): 参数数据框
            
        Returns:
            Dict: 验证结果详情
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'summary': {}
        }
        
        try:
            # 基础验证
            basic_valid, basic_errors = DataValidator.validate_dataframe(
                df, required_columns=['X', 'Y', 'Bin'], data_type="参数数据"
            )
            
            if not basic_valid:
                result['is_valid'] = False
                result['errors'].extend(basic_errors)
                return result
            
            # 识别参数列
            basic_columns = {'LotID', 'WaferID', 'Seq', 'X', 'Y', 'Bin', 'CONT'}
            param_columns = [col for col in df.columns if col not in basic_columns]
            
            result['summary']['total_parameters'] = len(param_columns)
            result['summary']['total_samples'] = len(df)
            
            # 验证坐标数据
            for coord_col in ['X', 'Y']:
                if coord_col in df.columns:
                    coord_valid, coord_errors = DataValidator.validate_numeric_column(
                        df, coord_col, min_value=0, allow_nan=False
                    )
                    if not coord_valid:
                        result['errors'].extend(coord_errors)
                        result['is_valid'] = False
            
            # 验证Bin数据
            if 'Bin' in df.columns:
                bin_valid, bin_errors = DataValidator.validate_categorical_column(
                    df, 'Bin', max_categories=20
                )
                if not bin_valid:
                    result['errors'].extend(bin_errors)
                
                # 统计Bin分布
                bin_counts = df['Bin'].value_counts()
                result['summary']['bin_distribution'] = bin_counts.to_dict()
            
            # 验证参数数据
            param_stats = []
            for param in param_columns:
                param_valid, param_errors = DataValidator.validate_numeric_column(
                    df, param, allow_nan=True
                )
                
                if param_errors:
                    result['warnings'].extend([f"{param}: {err}" for err in param_errors])
                
                # 计算参数统计信息
                param_data = df[param].dropna()
                if len(param_data) > 0:
                    stats = {
                        'parameter': param,
                        'valid_count': len(param_data),
                        'missing_count': df[param].isna().sum(),
                        'mean': param_data.mean(),
                        'std': param_data.std(),
                        'min': param_data.min(),
                        'max': param_data.max()
                    }
                    param_stats.append(stats)
            
            result['summary']['parameter_stats'] = param_stats
            
            # 整体数据质量评估
            total_cells = len(df) * len(param_columns)
            missing_cells = sum(df[col].isna().sum() for col in param_columns)
            if total_cells > 0:
                missing_ratio = missing_cells / total_cells
                result['summary']['missing_data_ratio'] = missing_ratio
                
                if missing_ratio > 0.5:
                    result['warnings'].append(f"数据缺失率过高: {missing_ratio:.1%}")
            
            logger.info(f"参数数据验证完成 - 有效: {result['is_valid']}, 参数: {len(param_columns)}, 样本: {len(df)}")
            
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"验证参数数据时出错: {str(e)}")
            logger.error(f"验证参数数据时出错: {str(e)}")
        
        return result


def main():
    """测试数据验证器"""
    print("=== 数据验证器测试 ===")
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 测试批次ID验证
    test_lot_ids = [
        "FA54-5339@203",
        "FA54-5340-327A-250501@203",
        "LOT12345",
        "",
        "invalid<lot>id",
        "toolong" * 20
    ]
    
    print("批次ID格式验证:")
    for lot_id in test_lot_ids:
        is_valid, error = DataValidator.validate_lot_id_format(lot_id)
        status = "✓" if is_valid else "✗"
        print(f"  {status} '{lot_id}' - {error}")
    
    # 测试数据框验证（需要实际数据）
    print("\n创建测试数据框:")
    test_df = pd.DataFrame({
        'X': [1, 2, 3, 4, 5],
        'Y': [1, 1, 2, 2, 3],
        'Bin': [1, 1, 2, 1, 3],
        'Param1': [1.1, 2.2, np.nan, 4.4, 5.5],
        'Param2': [10, 20, 30, 1000, 50]  # 包含异常值
    })
    
    # 验证基础数据框
    is_valid, errors = DataValidator.validate_dataframe(test_df, ['X', 'Y', 'Bin'], "测试")
    print(f"基础验证: {'通过' if is_valid else '失败'}")
    if errors:
        for error in errors:
            print(f"  错误: {error}")
    
    # 验证数值列
    param_valid, param_errors = DataValidator.validate_numeric_column(test_df, 'Param2')
    print(f"Param2列验证: {'通过' if param_valid else '失败'}")
    if param_errors:
        for error in param_errors:
            print(f"  警告: {error}")
    
    # 检测异常值
    outliers = DataValidator.detect_outliers(test_df['Param2'])
    print(f"异常值检测: 发现 {outliers['outlier_count']} 个异常值")


if __name__ == "__main__":
    main() 