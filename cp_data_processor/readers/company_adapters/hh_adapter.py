"""
HH公司适配器

HH公司作为标准格式，适配器主要用于格式验证和兼容性处理。
"""

from typing import Dict
import logging
from cp_data_processor.data_models.cp_data import CPLot
from .base_company_adapter import BaseCompanyAdapter

logger = logging.getLogger(__name__)


class HHAdapter(BaseCompanyAdapter):
    """
    HH公司数据适配器
    
    由于HH格式是标准格式，此适配器主要负责：
    1. 数据格式验证
    2. 向后兼容性保证
    3. 为其他适配器提供实现参考
    """
    
    def __init__(self, config: Dict):
        """
        初始化HH适配器
        
        Args:
            config: HH公司配置字典
        """
        super().__init__('HH', config)
        self.logger = logging.getLogger(f"{__name__}.HH")
        
    def transform_to_standard_format(self, lot: CPLot) -> CPLot:
        """
        将HH格式转换为标准格式
        
        由于HH格式就是标准格式，这里主要进行数据验证和清理。
        
        Args:
            lot: HH格式的CPLot对象
            
        Returns:
            CPLot: 处理后的CPLot对象
        """
        self.logger.info(f"开始处理HH格式数据，批次: {lot.lot_id}")
        
        # 验证数据格式
        if not self.validate_data_format(lot):
            self.logger.error("HH格式数据验证失败")
            raise ValueError("HH格式数据验证失败")
        
        # 由于是标准格式，直接返回原对象
        processed_lot = lot
        
        # 确保数据完整性
        self._ensure_data_integrity(processed_lot)
        
        self.logger.info(f"HH格式数据处理完成，晶圆数: {len(processed_lot.wafers)}")
        return processed_lot
    
    def get_field_mapping(self) -> Dict[str, str]:
        """
        获取HH字段映射
        
        Returns:
            Dict[str, str]: HH字段的恒等映射
        """
        return self.field_mapping
    
    def _ensure_data_integrity(self, lot: CPLot) -> None:
        """
        确保HH格式数据的完整性
        
        Args:
            lot: 待检查的CPLot对象
        """
        # 检查必要字段是否存在
        required_fields = self.config.get('data_validation', {}).get('required_fields', [])
        
        for wafer in lot.wafers:
            if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
                missing_fields = []
                for field in required_fields:
                    if field not in wafer.chip_data.columns:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.logger.warning(f"晶圆 {wafer.wafer_id} 缺少字段: {missing_fields}")
                else:
                    self.logger.debug(f"晶圆 {wafer.wafer_id} 数据完整性检查通过")
    
    def validate_hh_specific_format(self, lot: CPLot) -> bool:
        """
        HH格式特定验证
        
        Args:
            lot: 待验证的CPLot对象
            
        Returns:
            bool: 验证通过返回True
        """
        try:
            # 检查Bin值是否符合HH标准
            bin_config = self.config.get('data_validation', {}).get('bin_values', {})
            valid_bins = bin_config.get('pass_bins', []) + bin_config.get('fail_bins', [])
            
            for wafer in lot.wafers:
                if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
                    if 'Bin' in wafer.chip_data.columns:
                        unique_bins = wafer.chip_data['Bin'].unique()
                        invalid_bins = [bin_val for bin_val in unique_bins if bin_val not in valid_bins]
                        
                        if invalid_bins:
                            self.logger.warning(f"晶圆 {wafer.wafer_id} 发现非标准Bin值: {invalid_bins}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"HH格式特定验证失败: {e}")
            return False 