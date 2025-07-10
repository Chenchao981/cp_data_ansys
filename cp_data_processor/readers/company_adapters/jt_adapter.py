"""
JT公司适配器

将JT公司的Excel格式数据转换为标准HH格式。
"""

from typing import Dict, Any
import pandas as pd
import logging
from pathlib import Path

from .base_company_adapter import BaseCompanyAdapter
from cp_data_processor.data_models.cp_data import CPLot

logger = logging.getLogger(__name__)


class JTAdapter(BaseCompanyAdapter):
    """
    JT公司数据适配器
    
    负责将JT公司的Excel格式数据转换为标准HH格式。
    处理字段映射、单位转换和数据验证。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化JT适配器
        
        Args:
            config: JT公司配置字典
        """
        super().__init__('JT', config)
        self.logger = logging.getLogger(f"{__name__}.JT")
    
    def transform_to_standard_format(self, lot: CPLot) -> CPLot:
        """
        将JT格式转换为标准HH格式
        
        Args:
            lot: JT格式的CPLot对象
            
        Returns:
            CPLot: 转换为标准格式的CPLot对象
        """
        self.logger.info(f"开始处理JT格式数据，批次: {lot.lot_id}")
        
        # 验证输入数据
        if not self.validate_data_format(lot):
            self.logger.error("JT格式数据验证失败")
            raise ValueError("JT格式数据验证失败")
        
        # 处理每个晶圆的数据
        for wafer in lot.wafers:
            if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
                # 1. 应用字段映射
                wafer.chip_data = self.apply_field_mapping(wafer.chip_data)
                
                # 2. 应用单位转换
                wafer.chip_data = self.convert_units(wafer.chip_data)
                
                # 3. 标准化数据类型
                wafer.chip_data = self._standardize_data_types(wafer.chip_data)
                
                # 4. 添加缺失的标准字段
                wafer.chip_data = self._add_missing_standard_fields(wafer.chip_data, lot.lot_id, wafer.wafer_id)
        
        # 更新参数信息
        self._update_lot_parameters(lot)
        
        # 重新计算统计数据
        lot.combine_data_from_wafers()
        
        self.logger.info(f"JT格式数据处理完成，晶圆数: {len(lot.wafers)}")
        return lot
    
    def get_field_mapping(self) -> Dict[str, str]:
        """
        获取JT字段映射配置
        
        Returns:
            Dict[str, str]: JT字段到标准字段的映射
        """
        return self.field_mapping
    
    def can_process_file(self, file_path: str) -> bool:
        """
        检查是否能处理指定文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 能处理返回True，否则返回False
        """
        file_path_obj = Path(file_path)
        
        # 检查文件扩展名
        file_ext = file_path_obj.suffix.lower()
        supported_extensions = self.config.get('file_patterns', {}).get('file_extensions', [])
        
        if file_ext not in supported_extensions:
            return False
        
        # 检查文件名模式
        filename = file_path_obj.name
        filename_patterns = self.config.get('file_patterns', {}).get('filename_patterns', [])
        
        for pattern in filename_patterns:
            if pattern.startswith('FA') and pattern.endswith('.xls*'):
                # 匹配FA开头的文件模式
                import re
                pattern_regex = pattern.replace('*', '.*')
                if re.match(pattern_regex, filename):
                    return True
            else:
                # 简单字符串匹配
                pattern_clean = pattern.replace('*', '')
                if pattern_clean.lower() in filename.lower():
                    return True
        
        # 检查路径模式
        path_patterns = self.config.get('file_patterns', {}).get('path_patterns', [])
        for pattern in path_patterns:
            if pattern.lower() in file_path.lower():
                return True
        
        return False
    
    def _standardize_data_types(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        标准化数据类型
        
        Args:
            data: 待标准化的数据
            
        Returns:
            pd.DataFrame: 标准化后的数据
        """
        standardized_data = data.copy()
        
        # 标准化整数字段
        int_fields = ['Wafer_ID', 'X', 'Y', 'Seq', 'Bin']
        for field in int_fields:
            if field in standardized_data.columns:
                try:
                    standardized_data[field] = pd.to_numeric(standardized_data[field], errors='coerce').fillna(0).astype(int)
                except:
                    self.logger.warning(f"无法标准化字段 {field} 的数据类型")
        
        # 标准化浮点字段 (测试参数)
        float_fields = [col for col in standardized_data.columns if col not in ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Seq', 'Bin']]
        for field in float_fields:
            try:
                standardized_data[field] = pd.to_numeric(standardized_data[field], errors='coerce')
            except:
                self.logger.warning(f"无法标准化字段 {field} 的数据类型")
        
        return standardized_data
    
    def _add_missing_standard_fields(self, data: pd.DataFrame, lot_id: str, wafer_id: str) -> pd.DataFrame:
        """
        添加缺失的标准字段
        
        Args:
            data: 芯片数据
            lot_id: 批次ID
            wafer_id: 晶圆ID
            
        Returns:
            pd.DataFrame: 添加标准字段后的数据
        """
        enhanced_data = data.copy()
        
        # 添加Lot_ID字段
        if 'Lot_ID' not in enhanced_data.columns:
            enhanced_data['Lot_ID'] = lot_id
        
        # 添加Wafer_ID字段
        if 'Wafer_ID' not in enhanced_data.columns:
            enhanced_data['Wafer_ID'] = wafer_id
        
        # 确保列顺序：基本字段在前
        basic_columns = ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Seq', 'Bin']
        param_columns = [col for col in enhanced_data.columns if col not in basic_columns]
        ordered_columns = [col for col in basic_columns if col in enhanced_data.columns] + param_columns
        
        return enhanced_data[ordered_columns]
    
    def _update_lot_parameters(self, lot: CPLot):
        """
        更新批次参数信息
        
        Args:
            lot: CPLot对象
        """
        if not lot.wafers or not lot.wafers[0].chip_data is not None:
            return
        
        # 获取参数列（排除基本字段）
        sample_data = lot.wafers[0].chip_data
        basic_fields = ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Seq', 'Bin']
        param_columns = [col for col in sample_data.columns if col not in basic_fields]
        
        # 更新参数列表
        from cp_data_processor.data_models.cp_data import CPParameter
        
        updated_params = []
        for param_name in param_columns:
            # 查找现有参数
            existing_param = None
            for p in lot.params:
                if p.id == param_name:
                    existing_param = p
                    break
            
            if existing_param:
                updated_params.append(existing_param)
            else:
                # 创建新参数
                new_param = CPParameter(param_name)
                updated_params.append(new_param)
        
        lot.params = updated_params
        self.logger.info(f"更新了{len(updated_params)}个参数定义") 