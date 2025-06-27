from typing import Dict, Any
import pandas as pd

from .base_company_adapter import BaseCompanyAdapter
from cp_data_processor.data_models.cp_data import CPLot

class JTAdapter(BaseCompanyAdapter):
    """
    将JT公司的数据格式适配到标准的CPLot格式。
    """
    def __init__(self, company_name: str, config: Dict[str, Any]):
        super().__init__(company_name, config)

    def transform_to_standard_format(self, lot: CPLot) -> CPLot:
        """
        对从JT文件读取的CPLot对象进行字段映射和单位转换。

        Args:
            lot: 由JTReader创建的原始CPLot对象。

        Returns:
            CPLot: 经过适配和转换的标准CPLot对象。
        """
        # 1. 应用单位转换（字段映射已在JTReader中处理）
        for wafer in lot.wafers:
            if wafer.chip_data is not None:
                # JTReader已经处理了字段映射，只需要进行单位转换
                wafer.chip_data = self.convert_units(wafer.chip_data)

        # 2. 合并数据
        # 转换后，需要根据新的列名更新参数列表
        self._update_lot_params_from_data(lot)
        lot.combine_data_from_wafers()

        return lot

    def get_field_mapping(self) -> Dict[str, str]:
        """
        获取字段映射配置。
        
        Returns:
            Dict[str, str]: 厂商字段名 -> 标准字段名的映射。
        """
        return self.field_mapping

    def _update_lot_params_from_data(self, lot: CPLot):
        """根据DataFrame的列名更新CPLot对象中的参数定义。"""
        if lot.wafers and lot.wafers[0].chip_data is not None:
            # 获取转换后的参数名称
            current_columns = lot.wafers[0].chip_data.columns.tolist()
            
            # 从现有参数中过滤，只保留实际存在的列
            existing_params = {p.id: p for p in lot.params}
            updated_params = []

            for col_name in current_columns:
                if col_name in existing_params:
                    updated_params.append(existing_params[col_name])

            lot.params = updated_params
            lot.update_counts() 