#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JT公司数据适配器

基于HH公司DataTransformer的成熟数据清洗技术，专门处理JT公司的数据转换。

特点：
- 应用HH公司的适配器设计模式
- 使用IQR四分位法处理异常值
- 禁用单位转换逻辑
- 保持数据完整性

作者: CP Data Analysis Team
版本: 1.0.0
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

# 添加项目根目录到路径以导入现有模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter
from cp_data_processor.readers.company_adapters.base_company_adapter import BaseCompanyAdapter
from cp_data_processor.processing.data_transformer import DataTransformer

# 设置日志
logger = logging.getLogger(__name__)


class JTAdapter(BaseCompanyAdapter):
    """
    JT公司数据适配器
    
    基于HH公司的BaseCompanyAdapter和DataTransformer，
    专门处理JT公司数据格式到标准格式的转换。
    
    重要特性：
    - 禁用单位转换：JT数据rawdata已与unit匹配
    - 使用IQR四分位法处理异常值
    - 应用HH公司的字段映射技术
    - 保持数据完整性
    """
    
    def __init__(self, company_name: str, config: Dict[str, Any]):
        """
        初始化JT适配器
        
        Args:
            company_name: 公司名称，应为'JT'
            config: JT公司配置字典
        """
        super().__init__(company_name, config)
        self.logger = logging.getLogger(f"{__name__}.JTAdapter")
        
        # 从配置中获取清洗参数
        cleaning_config = config.get('cleaning_config', {})
        self.outlier_method = cleaning_config.get('default_outlier_method', 'iqr')
        self.outlier_threshold = cleaning_config.get('outlier_threshold', None)
        
        # 确认单位转换被禁用
        self.unit_conversion_disabled = config.get('disable_unit_conversion', True)
        
        self.logger.info(f"初始化JT适配器，异常值处理方法: {self.outlier_method}")
        self.logger.info(f"单位转换禁用状态: {self.unit_conversion_disabled}")
    
    def transform_to_standard_format(self, lot: CPLot) -> CPLot:
        """
        将JT格式的CPLot对象转换为标准格式
        
        基于HH公司的成熟数据处理流程：
        1. 字段映射
        2. 跳过单位转换（JT特有）
        3. 数据清洗（IQR四分位法）
        4. 数据整合
        
        Args:
            lot: JT格式的CPLot对象
            
        Returns:
            CPLot: 转换为标准格式的CPLot对象
        """
        self.logger.info(f"开始处理JT格式数据，批次: {lot.lot_id}")
        
        # 验证数据格式
        if not self.validate_data_format(lot):
            self.logger.error("JT格式数据验证失败")
            raise ValueError("JT格式数据验证失败")
        
        # 1. 应用字段映射
        self._apply_field_mapping_to_lot(lot)
        
        # 2. 🔥 跳过单位转换 - JT数据特有逻辑
        self._skip_unit_conversion(lot)
        
        # 3. 合并晶圆数据
        lot.combine_data_from_wafers()
        
        # 4. 应用HH公司的数据清洗技术
        self._apply_data_cleaning(lot)
        
        # 5. 确保数据完整性
        self._ensure_data_integrity(lot)
        
        self.logger.info(f"JT格式数据处理完成，晶圆数: {len(lot.wafers)}")
        return lot
    
    def _apply_field_mapping_to_lot(self, lot: CPLot) -> None:
        """
        对CPLot对象中的所有晶圆应用字段映射
        
        根据用户确认的映射关系：
        - DUT_NO -> Seq
        - SOFT_BIN -> Bin
        - X_COORD -> X
        - Y_COORD -> Y
        - TEST_NUM -> CONT
        
        Args:
            lot: 要处理的CPLot对象
        """
        self.logger.info("开始应用字段映射...")
        
        mapped_count = 0
        for wafer in lot.wafers:
            if wafer.chip_data is not None:
                # 应用字段映射
                original_columns = wafer.chip_data.columns.tolist()
                wafer.chip_data = self.apply_field_mapping(wafer.chip_data)
                new_columns = wafer.chip_data.columns.tolist()
                
                # 记录映射变化
                if original_columns != new_columns:
                    mapped_count += 1
                    self.logger.debug(f"晶圆 {wafer.wafer_id} 字段映射完成")
        
        self.logger.info(f"字段映射完成，处理晶圆数: {mapped_count}")
    
    def _skip_unit_conversion(self, lot: CPLot) -> None:
        """
        跳过单位转换逻辑 - JT数据特有处理
        
        JT公司的rawdata数据不需要单位转换，DUT_DATA第六行开始的数据
        都与上面的unit单位匹配，不需要转换。
        
        Args:
            lot: CPLot对象
        """
        self.logger.info("🔥 跳过单位转换 - JT数据已与unit匹配")
        
        if not self.unit_conversion_disabled:
            self.logger.warning("配置中未禁用单位转换，但JT数据不应进行单位转换")
        
        # 确保不调用任何单位转换逻辑
        for wafer in lot.wafers:
            if wafer.chip_data is not None:
                # 记录原始数据值用于验证
                param_columns = [col for col in wafer.chip_data.columns 
                               if col not in ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y', 'CONT']]
                
                for param in param_columns:
                    if param in wafer.chip_data.columns:
                        self.logger.debug(f"保持参数 {param} 原始数值")
        
        self.logger.info("单位转换跳过完成 - 数据值保持原始状态")
    
    def _apply_data_cleaning(self, lot: CPLot) -> None:
        """
        应用HH公司的数据清洗技术
        
        使用DataTransformer的clean_data方法，默认使用IQR四分位法
        
        Args:
            lot: 要清洗的CPLot对象
        """
        self.logger.info(f"开始数据清洗，使用方法: {self.outlier_method}")
        
        try:
            # 创建DataTransformer实例
            transformer = DataTransformer(lot)
            
            # 应用数据清洗
            if self.outlier_method == 'iqr':
                transformer.clean_data(outlier_method='iqr')
            elif self.outlier_method == 'std_dev' and self.outlier_threshold:
                transformer.clean_data(outlier_method='std_dev', 
                                     std_dev_threshold=self.outlier_threshold)
            else:
                # 默认使用IQR方法
                transformer.clean_data(outlier_method='iqr')
            
            self.logger.info("数据清洗完成")
            
        except Exception as e:
            self.logger.error(f"数据清洗失败: {e}")
            # 继续处理，但记录错误
    
    def _ensure_data_integrity(self, lot: CPLot) -> None:
        """
        确保JT格式数据的完整性
        
        基于HH公司的数据完整性检查机制
        
        Args:
            lot: 待检查的CPLot对象
        """
        self.logger.info("开始数据完整性检查...")
        
        # 检查必要字段是否存在
        required_fields = self.config.get('data_validation', {}).get('required_fields', [])
        
        integrity_issues = 0
        for wafer in lot.wafers:
            if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
                missing_fields = []
                for field in required_fields:
                    if field not in wafer.chip_data.columns:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.logger.warning(f"晶圆 {wafer.wafer_id} 缺少字段: {missing_fields}")
                    integrity_issues += 1
                else:
                    self.logger.debug(f"晶圆 {wafer.wafer_id} 数据完整性检查通过")
        
        if integrity_issues == 0:
            self.logger.info("数据完整性检查通过")
        else:
            self.logger.warning(f"发现 {integrity_issues} 个数据完整性问题")
    
    def get_field_mapping(self) -> Dict[str, str]:
        """
        获取JT字段映射配置
        
        Returns:
            Dict[str, str]: JT字段名 -> 标准字段名的映射
        """
        return self.field_mapping
    
    def validate_jt_specific_format(self, lot: CPLot) -> bool:
        """
        JT格式特定验证
        
        Args:
            lot: 待验证的CPLot对象
            
        Returns:
            bool: 验证通过返回True
        """
        try:
            # 检查是否有晶圆数据
            if not lot.wafers:
                self.logger.error("CPLot对象中没有晶圆数据")
                return False
            
            # 检查关键JT字段是否存在（映射前）
            jt_fields = ['DUT_NO', 'SOFT_BIN', 'X_COORD', 'Y_COORD', 'TEST_NUM']
            
            for wafer in lot.wafers:
                if wafer.chip_data is not None:
                    available_fields = wafer.chip_data.columns.tolist()
                    
                    # 检查是否有基本的JT字段
                    found_jt_fields = [field for field in jt_fields if field in available_fields]
                    
                    if len(found_jt_fields) < 2:  # 至少要有2个JT特有字段
                        self.logger.warning(f"晶圆 {wafer.wafer_id} 中JT特有字段不足")
                    else:
                        self.logger.debug(f"晶圆 {wafer.wafer_id} JT格式验证通过")
            
            return True
            
        except Exception as e:
            self.logger.error(f"JT格式特定验证失败: {e}")
            return False
    
    def convert_units(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        重写单位转换方法 - JT数据禁用单位转换
        
        Args:
            data: 待转换的数据DataFrame
            
        Returns:
            pd.DataFrame: 原始数据（未转换）
        """
        self.logger.info("🔥 JT数据禁用单位转换，返回原始数据")
        return data  # 直接返回原始数据，不进行任何转换
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        获取处理摘要信息
        
        Returns:
            Dict[str, Any]: 处理摘要
        """
        return {
            'company': self.company_name,
            'outlier_method': self.outlier_method,
            'unit_conversion_disabled': self.unit_conversion_disabled,
            'field_mapping': self.field_mapping,
            'supported_formats': self.config.get('supported_formats', []),
            'version': '1.0.0'
        }


# 简化的函数接口
def create_jt_adapter(config: Dict[str, Any]) -> JTAdapter:
    """
    创建JT适配器实例
    
    Args:
        config: JT配置字典
        
    Returns:
        JTAdapter: JT适配器实例
    """
    return JTAdapter('JT', config)


if __name__ == "__main__":
    # 测试代码
    print("JT适配器模块测试")
    
    # 示例配置
    test_config = {
        'name': 'JT公司',
        'field_mapping': {
            'DUT_NO': 'Seq',
            'SOFT_BIN': 'Bin',
            'X_COORD': 'X',
            'Y_COORD': 'Y',
            'TEST_NUM': 'CONT'
        },
        'unit_conversion': {},
        'disable_unit_conversion': True,
        'cleaning_config': {
            'default_outlier_method': 'iqr'
        },
        'data_validation': {
            'required_fields': ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y']
        }
    }
    
    adapter = JTAdapter('JT', test_config)
    summary = adapter.get_processing_summary()
    
    print("JT适配器配置摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("JT适配器初始化成功") 