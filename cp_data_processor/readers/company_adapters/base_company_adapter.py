"""
厂商适配器基类

定义所有厂商适配器必须实现的接口，提供统一的数据转换框架。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import pandas as pd
import logging
from cp_data_processor.data_models.cp_data import CPLot

logger = logging.getLogger(__name__)


class BaseCompanyAdapter(ABC):
    """
    厂商适配器基类
    
    所有厂商适配器都应继承此类并实现抽象方法。
    提供统一的数据转换接口，将厂商特定格式转换为HH标准格式。
    """
    
    def __init__(self, company_name: str, config: Dict[str, Any]):
        """
        初始化适配器
        
        Args:
            company_name: 厂商名称 (如: 'HH', 'JT')
            config: 厂商配置字典
        """
        self.company_name = company_name
        self.config = config
        self.field_mapping = config.get('field_mapping', {})
        self.unit_conversion = config.get('unit_conversion', {})
        self.logger = logging.getLogger(f"{__name__}.{company_name}")
        
    @abstractmethod
    def transform_to_standard_format(self, lot: CPLot) -> CPLot:
        """
        将厂商特定的CPLot对象转换为HH标准格式
        
        Args:
            lot: 包含厂商特定数据的CPLot对象
            
        Returns:
            CPLot: 转换为HH标准格式的CPLot对象
        """
        pass
    
    @abstractmethod
    def get_field_mapping(self) -> Dict[str, str]:
        """
        获取字段映射配置
        
        Returns:
            Dict[str, str]: 厂商字段名 -> HH标准字段名的映射
        """
        pass
    
    def validate_data_format(self, lot: CPLot) -> bool:
        """
        验证数据格式是否符合预期
        
        Args:
            lot: 待验证的CPLot对象
            
        Returns:
            bool: 验证通过返回True，否则返回False
        """
        try:
            # 基础验证：检查必要的数据结构
            if not lot or not lot.wafers:
                self.logger.warning("CPLot对象为空或没有晶圆数据")
                return False
                
            # 检查每个晶圆是否有基本数据
            for wafer in lot.wafers:
                if not hasattr(wafer, 'chip_data') or wafer.chip_data is None:
                    self.logger.warning(f"晶圆 {wafer.wafer_id} 缺少芯片数据")
                    return False
                    
            self.logger.info(f"{self.company_name}格式数据验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"数据格式验证失败: {e}")
            return False
    
    def convert_units(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        执行单位转换
        
        Args:
            data: 待转换的数据DataFrame
            
        Returns:
            pd.DataFrame: 单位转换后的数据
        """
        if not self.unit_conversion:
            return data
            
        converted_data = data.copy()
        
        for column, conversion_config in self.unit_conversion.items():
            if column in converted_data.columns:
                try:
                    factor = conversion_config.get('factor', 1.0)
                    offset = conversion_config.get('offset', 0.0)
                    
                    # 执行单位转换: new_value = (old_value * factor) + offset
                    converted_data[column] = (converted_data[column] * factor) + offset
                    
                    self.logger.info(f"已转换 {column} 列的单位 (factor={factor}, offset={offset})")
                    
                except Exception as e:
                    self.logger.warning(f"转换 {column} 列单位时出错: {e}")
                    
        return converted_data
    
    def apply_field_mapping(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        应用字段映射，将厂商字段名转换为HH标准字段名
        
        Args:
            data: 待映射的数据DataFrame
            
        Returns:
            pd.DataFrame: 字段映射后的数据
        """
        if not self.field_mapping:
            return data
            
        mapped_data = data.copy()
        
        # 执行字段重命名
        rename_mapping = {}
        for source_field, target_field in self.field_mapping.items():
            if source_field in mapped_data.columns:
                rename_mapping[source_field] = target_field
                
        if rename_mapping:
            mapped_data = mapped_data.rename(columns=rename_mapping)
            self.logger.info(f"已映射字段: {rename_mapping}")
            
        return mapped_data
    
    def get_supported_formats(self) -> List[str]:
        """
        获取支持的数据格式列表
        
        Returns:
            List[str]: 支持的格式列表
        """
        return self.config.get('supported_formats', [])
    
    def get_company_info(self) -> Dict[str, Any]:
        """
        获取厂商信息
        
        Returns:
            Dict[str, Any]: 厂商基本信息
        """
        return {
            'name': self.company_name,
            'display_name': self.config.get('name', self.company_name),
            'supported_formats': self.get_supported_formats(),
            'default_format': self.config.get('default_format'),
            'version': self.config.get('version', '1.0.0')
        } 