"""
Lion公司适配器

Lion公司Excel格式CP测试数据处理适配器，将Lion格式转换为标准格式。

核心功能：
- 字段映射：PART_INDEX->Seq, SOFT_BIN->Bin, X_COORD->X, Y_COORD->Y
- 单位转换：根据配置进行必要的单位转换
- 数据标准化：确保输出符合标准CPLot格式
- 参数提取：从规格数据中提取测试参数信息

适配流程：
1. 验证Lion格式数据
2. 应用字段映射和单位转换
3. 处理每个晶圆数据
4. 生成标准化的参数规格
5. 创建合并的数据集
"""

from typing import Dict, List, Optional, Tuple
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter
from cp_data_processor.readers.company_adapters.base_company_adapter import BaseCompanyAdapter

logger = logging.getLogger(__name__)


class LionAdapter(BaseCompanyAdapter):
    """
    Lion公司数据适配器
    
    处理Lion公司Excel格式的CP测试数据，特点：
    1. Excel文件格式，包含summary_information和dut_data两个工作表
    2. dut_data工作表前3行为规格信息：UNIT、LIMIT_LOW、LIMIT_HIGH
    3. 从第4行开始为实际测试数据
    4. 字段映射：PART_INDEX->Seq, SOFT_BIN->Bin, X_COORD->X, Y_COORD->Y
    """
    
    def __init__(self, config: Dict):
        """
        初始化Lion适配器
        
        Args:
            config: Lion公司配置字典
        """
        super().__init__('LION', config)
        self.logger = logging.getLogger(f"{__name__}.LION")
        
    def transform_to_standard_format(self, lot: CPLot) -> CPLot:
        """
        将Lion格式转换为标准格式
        
        Args:
            lot: Lion格式的CPLot对象
            
        Returns:
            CPLot: 转换为HH标准格式的CPLot对象
        """
        self.logger.info(f"开始处理Lion格式数据，批次: {lot.lot_id}")
        
        # 验证数据格式
        if not self.validate_data_format(lot):
            self.logger.error("Lion格式数据验证失败")
            raise ValueError("Lion格式数据验证失败")
        
        # 创建新的CPLot对象
        processed_lot = CPLot(
            lot_id=lot.lot_id,
            product=getattr(lot, 'product', 'Unknown'),
            wafer_count=len(lot.wafers)
        )
        
        # 处理每个晶圆
        processed_wafers = []
        all_params = set()
        
        for wafer in lot.wafers:
            processed_wafer = self._process_wafer(wafer)
            if processed_wafer:
                processed_wafers.append(processed_wafer)
                # 收集所有参数名
                if hasattr(processed_wafer, 'chip_data') and processed_wafer.chip_data is not None:
                    param_columns = [col for col in processed_wafer.chip_data.columns 
                                   if col not in ['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Seq', 'Bin', 'CONT']]
                    all_params.update(param_columns)
        
        processed_lot.wafers = processed_wafers
        
        # 生成参数规格信息
        processed_lot.params = self._extract_parameters(lot, all_params)
        
        # 生成合并数据
        processed_lot.combined_data = self._create_combined_data(processed_lot)
        
        self.logger.info(f"Lion格式数据处理完成，晶圆数: {len(processed_lot.wafers)}, 参数数: {len(processed_lot.params)}")
        return processed_lot
    
    def _process_wafer(self, wafer: CPWafer) -> Optional[CPWafer]:
        """
        处理单个晶圆数据
        
        Args:
            wafer: 原始晶圆数据
            
        Returns:
            CPWafer: 处理后的晶圆数据
        """
        if not hasattr(wafer, 'chip_data') or wafer.chip_data is None:
            self.logger.warning(f"晶圆 {wafer.wafer_id} 无芯片数据")
            return None
            
        # 应用字段映射
        chip_data = self.apply_field_mapping(wafer.chip_data.copy())
        
        # 应用单位转换
        chip_data = self.convert_units(chip_data)
        
        # 添加批次和晶圆ID
        if 'Lot_ID' not in chip_data.columns:
            chip_data['Lot_ID'] = wafer.lot_id if hasattr(wafer, 'lot_id') else 'Unknown'
        if 'Wafer_ID' not in chip_data.columns:
            chip_data['Wafer_ID'] = wafer.wafer_id
            
        # 确保必要列存在
        required_columns = ['X', 'Y', 'Seq', 'Bin']
        for col in required_columns:
            if col not in chip_data.columns:
                self.logger.warning(f"晶圆 {wafer.wafer_id} 缺少必要列: {col}")
                return None
        
        # 计算良率
        total_chips = len(chip_data)
        pass_bins = self.config.get('data_validation', {}).get('bin_values', {}).get('pass_bins', [1])
        good_chips = len(chip_data[chip_data['Bin'].isin(pass_bins)])
        yield_rate = (good_chips / total_chips * 100) if total_chips > 0 else 0.0
        
        # 创建新的晶圆对象
        processed_wafer = CPWafer(
            wafer_id=wafer.wafer_id,
            chip_count=total_chips,
            yield_rate=yield_rate
        )
        
        # 设置坐标和序号数组
        processed_wafer.x = chip_data['X'].values
        processed_wafer.y = chip_data['Y'].values
        processed_wafer.seq = chip_data['Seq'].values
        processed_wafer.bin = chip_data['Bin'].values
        
        # 设置芯片数据
        processed_wafer.chip_data = chip_data
        
        # 保留summary数据
        if hasattr(wafer, 'summary_data'):
            processed_wafer.summary_data = wafer.summary_data
        
        return processed_wafer
    
    def _extract_parameters(self, original_lot: CPLot, param_names: set) -> List[CPParameter]:
        """
        从原始数据中提取参数规格信息
        
        Args:
            original_lot: 原始CPLot对象
            param_names: 参数名称集合
            
        Returns:
            List[CPParameter]: 参数列表
        """
        parameters = []
        
        # 从原始数据的第一个晶圆获取规格信息（假设所有晶圆规格相同）
        if not original_lot.wafers:
            return parameters
            
        first_wafer = original_lot.wafers[0]
        if not hasattr(first_wafer, 'spec_data') or first_wafer.spec_data is None:
            # 如果没有规格数据，创建默认参数
            for param_name in param_names:
                param = CPParameter(
                    id=param_name,
                    unit='Unknown',
                    sl=None,
                    su=None
                )
                parameters.append(param)
            return parameters
        
        # 从规格数据中提取参数信息
        spec_data = first_wafer.spec_data
        
        for param_name in param_names:
            if param_name in spec_data.columns:
                # 获取单位信息
                unit = 'Unknown'
                if 'UNIT' in spec_data.index:
                    unit_value = spec_data.loc['UNIT', param_name]
                    if pd.notna(unit_value):
                        unit = str(unit_value)
                
                # 获取规格限制
                sl = None
                su = None
                
                if 'LIMIT_LOW' in spec_data.index:
                    sl_value = spec_data.loc['LIMIT_LOW', param_name]
                    if pd.notna(sl_value) and str(sl_value).replace('.', '', 1).isdigit():
                        sl = float(sl_value)
                
                if 'LIMIT_HIGH' in spec_data.index:
                    su_value = spec_data.loc['LIMIT_HIGH', param_name]
                    if pd.notna(su_value) and str(su_value).replace('.', '', 1).isdigit():
                        su = float(su_value)
                
                param = CPParameter(
                    id=param_name,
                    unit=unit,
                    sl=sl,
                    su=su
                )
                parameters.append(param)
            else:
                # 参数不在规格数据中，创建默认参数
                param = CPParameter(
                    id=param_name,
                    unit='Unknown',
                    sl=None,
                    su=None
                )
                parameters.append(param)
        
        return parameters
    
    def _create_combined_data(self, lot: CPLot) -> pd.DataFrame:
        """
        创建合并的数据DataFrame
        
        Args:
            lot: CPLot对象
            
        Returns:
            pd.DataFrame: 合并的数据
        """
        combined_data_list = []
        
        for wafer in lot.wafers:
            if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
                combined_data_list.append(wafer.chip_data)
        
        if combined_data_list:
            combined_data = pd.concat(combined_data_list, ignore_index=True)
        else:
            combined_data = pd.DataFrame()
        
        return combined_data
    
    def get_field_mapping(self) -> Dict[str, str]:
        """
        获取Lion字段映射
        
        Returns:
            Dict[str, str]: Lion字段映射
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
        from pathlib import Path
        
        file_path_obj = Path(file_path)
        
        # 检查文件扩展名
        file_ext = file_path_obj.suffix.lower()
        supported_extensions = self.config.get('file_patterns', {}).get('file_extensions', [])
        
        if file_ext not in supported_extensions:
            return False
        
        # 检查文件名模式（Lion公司文件通常以F开头）
        filename = file_path_obj.name
        filename_patterns = self.config.get('file_patterns', {}).get('filename_patterns', [])
        
        for pattern in filename_patterns:
            if pattern.startswith('F*') and filename.startswith('F') and filename.endswith('.xlsx'):
                return True
            pattern_clean = pattern.replace('*', '')
            if pattern_clean.lower() in filename.lower():
                return True
        
        # 检查路径模式
        path_patterns = self.config.get('file_patterns', {}).get('path_patterns', [])
        for pattern in path_patterns:
            if pattern.lower() in file_path.lower():
                return True
        
        return False
    
    def validate_lion_specific_format(self, lot: CPLot) -> bool:
        """
        Lion格式特定验证
        
        Args:
            lot: 待验证的CPLot对象
            
        Returns:
            bool: 验证通过返回True
        """
        try:
            # 检查Lion特有字段
            required_fields = self.config.get('data_validation', {}).get('required_fields', [])
            
            for wafer in lot.wafers:
                if hasattr(wafer, 'chip_data') and wafer.chip_data is not None:
                    missing_fields = []
                    for field in required_fields:
                        if field not in wafer.chip_data.columns:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        self.logger.warning(f"晶圆 {wafer.wafer_id} 缺少Lion特定字段: {missing_fields}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Lion格式特定验证失败: {e}")
            return False