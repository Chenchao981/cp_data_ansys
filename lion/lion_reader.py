"""
Lion公司Excel数据读取器

读取Lion公司Excel格式的CP测试数据，包含规格处理和数据转换功能。

数据格式：
- Excel文件包含summary_information和dut_data两个工作表
- dut_data前3行为规格信息（UNIT、LIMIT_LOW、LIMIT_HIGH）
- 从第4行开始为实际测试数据
- 自动提取lot_id和wafer_id从文件名

核心功能：
- 自动识别Lion公司Excel格式
- 读取并解析规格信息和测试数据
- 处理summary信息提取良率数据
- 转换为标准CPLot数据模型
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter
from cp_data_processor.readers.base_reader import BaseReader

logger = logging.getLogger(__name__)


class LionExcelReader(BaseReader):
    """
    Lion公司Excel格式数据读取器
    
    支持读取Lion公司Excel格式的CP测试数据：
    1. 包含summary_information和dut_data两个工作表
    2. dut_data工作表前3行为规格信息（UNIT、LIMIT_LOW、LIMIT_HIGH）
    3. 从第4行开始为实际测试数据
    """
    
    def __init__(self, file_paths=None, pass_bin=1):
        # 如果没有提供file_paths，使用空列表
        if file_paths is None:
            file_paths = []
        super().__init__(file_paths, pass_bin)
        self.logger = logging.getLogger(f"{__name__}.LionExcelReader")
    
    def can_read(self, file_path: str) -> bool:
        """
        检查是否能读取指定文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 能读取返回True，否则返回False
        """
        try:
            file_path_obj = Path(file_path)
            
            # 检查文件扩展名
            if file_path_obj.suffix.lower() not in ['.xlsx', '.xls']:
                return False
            
            # 检查文件是否存在
            if not file_path_obj.exists():
                return False
            
            # 尝试读取Excel文件并检查工作表
            xl_file = pd.ExcelFile(file_path)
            if 'dut_data' not in xl_file.sheet_names:
                return False
            
            # 检查dut_data工作表的基本结构
            df = pd.read_excel(file_path, sheet_name='dut_data')
            required_columns = ['PART_INDEX', 'SOFT_BIN', 'X_COORD', 'Y_COORD']
            
            # 检查是否包含必要的列
            if not all(col in df.columns for col in required_columns):
                return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"无法读取文件 {file_path}: {e}")
            return False
    
    def read(self) -> CPLot:
        """
        读取所有文件并返回一个填充好的 CPLot 对象
        
        Returns:
            CPLot: 包含所有读取数据的 CPLot 对象
        """
        if not self.file_paths:
            raise ValueError("没有指定要读取的文件")
        
        # 使用第一个文件来创建CPLot
        first_file = self.file_paths[0]
        lot_id = self._extract_lot_id(first_file)
        
        # 创建CPLot对象
        lot = CPLot(
            lot_id=lot_id,
            product="Lion_Product",
            wafer_count=len(self.file_paths)
        )
        
        # 处理所有文件
        for file_path in self.file_paths:
            self._extract_from_file(file_path, lot)
        
        return lot
    
    def read_file(self, file_path: str) -> CPLot:
        """
        读取单个文件（统一接口）
        
        Args:
            file_path: 文件路径
            
        Returns:
            CPLot: 读取的数据对象
        """
        return self.read_single_file(file_path)
    
    def read_single_file(self, file_path: str) -> CPLot:
        """
        读取单个Lion Excel文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            CPLot: 读取的数据对象
        """
        self.logger.info(f"开始读取Lion Excel文件: {file_path}")
        
        try:
            # 从文件名提取批次ID
            lot_id = self._extract_lot_id(file_path)
            
            # 读取数据
            data_df, spec_df = self._read_excel_data(file_path)
            
            # 创建CPLot对象
            lot = CPLot(
                lot_id=lot_id,
                product="Lion_Product",
                wafer_count=1  # Lion数据通常每个文件包含一个晶圆
            )
            
            # 处理数据并创建晶圆
            wafer = self._create_wafer_from_data(data_df, spec_df, lot_id, file_path)
            lot.wafers = [wafer]
            
            # 提取参数信息
            lot.params = self._extract_parameters_from_spec(spec_df)
            
            # 创建合并数据
            lot.combined_data = data_df.copy()
            
            self.logger.info(f"成功读取Lion数据，批次: {lot_id}, 芯片数: {len(data_df)}")
            return lot
            
        except Exception as e:
            self.logger.error(f"读取Lion Excel文件失败: {e}")
            raise
    
    def _extract_from_file(self, file_path: str, lot: CPLot) -> None:
        """
        从单个文件中提取数据到 CPLot 对象
        
        Args:
            file_path: 要读取的文件路径
            lot: 要填充的 CPLot 对象
        """
        self.logger.info(f"从文件提取数据: {file_path}")
        
        try:
            # 读取数据
            data_df, spec_df = self._read_excel_data(file_path)
            
            # 从文件名提取批次ID
            lot_id = self._extract_lot_id(file_path)
            
            # 处理数据并创建晶圆
            wafer = self._create_wafer_from_data(data_df, spec_df, lot_id, file_path)
            lot.wafers.append(wafer)
            
            # 如果是第一个文件，设置参数信息
            if not lot.params:
                lot.params = self._extract_parameters_from_spec(spec_df)
            
            # 合并数据
            if lot.combined_data is None or lot.combined_data.empty:
                lot.combined_data = data_df.copy()
            else:
                lot.combined_data = pd.concat([lot.combined_data, data_df], ignore_index=True)
            
        except Exception as e:
            self.logger.error(f"从文件 {file_path} 提取数据失败: {e}")
            raise
    
    def _extract_lot_id(self, file_path: str) -> str:
        """
        从文件路径提取批次ID
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 批次ID
        """
        file_path_obj = Path(file_path)
        
        # 从文件名中提取批次ID（如F25130244_1.xlsx -> F25130244）
        filename = file_path_obj.stem
        if '_' in filename:
            lot_id = filename.split('_')[0]
        else:
            lot_id = filename
        
        return lot_id
    
    def _extract_wafer_id(self, file_path: str) -> str:
        """
        从文件路径提取晶圆ID
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 晶圆ID
        """
        file_path_obj = Path(file_path)
        
        # 从文件名中提取晶圆ID（如F25130244_1.xlsx -> 1）
        filename = file_path_obj.stem
        if '_' in filename:
            wafer_id = filename.split('_')[1]
        else:
            wafer_id = "1"  # 默认值
        
        return wafer_id
    
    def _read_excel_data(self, file_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        读取Excel文件并分离数据和规格
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (数据DataFrame, 规格DataFrame)
        """
        # 读取dut_data工作表
        df = pd.read_excel(file_path, sheet_name='dut_data')
        
        # 分离规格信息和实际数据
        spec_rows = ['UNIT', 'LIMIT_LOW', 'LIMIT_HIGH']
        
        # 提取规格信息（前3行）
        spec_data = df.head(3).copy()
        spec_data.index = spec_rows
        
        # 提取实际数据（从第4行开始）
        data_df = df.iloc[3:].copy().reset_index(drop=True)
        
        # 清理数据：移除空行和无效数据
        data_df = data_df.dropna(subset=['PART_INDEX', 'SOFT_BIN', 'X_COORD', 'Y_COORD'])
        
        # 确保数值列的数据类型正确
        numeric_columns = ['PART_INDEX', 'SOFT_BIN', 'X_COORD', 'Y_COORD', 'PASSFG']
        for col in numeric_columns:
            if col in data_df.columns:
                data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
        
        # 处理测试参数列
        param_columns = [col for col in data_df.columns 
                        if col not in numeric_columns + ['SITE_NUM', 'T_TIME', 'TEST_NUM']]
        
        for col in param_columns:
            if col in data_df.columns:
                # 尝试转换为数值，如果失败则保持原值
                data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
        
        return data_df, spec_data
    
    def _read_summary_information(self, file_path: str) -> Dict:
        """
        读取summary_information工作表并提取yield相关数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 包含yield相关信息的字典
        """
        try:
            # 读取summary_information工作表
            df = pd.read_excel(file_path, sheet_name='summary_information')
            
            # 提取数据
            summary_data = {}
            
            # 获取所有行的数据（第一列）
            all_rows = df.iloc[:, 0].tolist()
            
            # 提取gross_die (第20行，索引19): "Total: 1008" -> 1008
            if len(all_rows) > 19:
                total_row = str(all_rows[19])
                if 'Total:' in total_row or 'total:' in total_row.lower():
                    import re
                    match = re.search(r'total:\s*(\d+)', total_row, re.IGNORECASE)
                    if match:
                        summary_data['gross_die'] = int(match.group(1))
            
            # 提取good_die和yield (第21行，索引20): "Pass: 1002   99.40%" -> 1002, 99.40
            if len(all_rows) > 20:
                pass_row = str(all_rows[20])
                if 'Pass:' in pass_row or 'pass:' in pass_row.lower():
                    import re
                    # 提取good_die数字
                    match = re.search(r'pass:\s*(\d+)', pass_row, re.IGNORECASE)
                    if match:
                        summary_data['good_die'] = int(match.group(1))
                    
                    # 提取yield百分比
                    yield_match = re.search(r'(\d+\.?\d*)%', pass_row)
                    if yield_match:
                        summary_data['yield'] = f"{yield_match.group(1)}%"
            
            # 提取参数失败计数 (从第24行开始，索引23)
            param_counts = {}
            for i in range(23, len(all_rows)):
                row_data = str(all_rows[i])
                if 'SBin[' in row_data and '__AllFail' in row_data:
                    import re
                    # 匹配模式: "SBin[6]   IR_35V__AllFail                 0     0.00%   2"
                    # 提取失败计数（第三个数字）而不是最后的bin number
                    match = re.search(r'SBin\[\d+\]\s+(\w+)__AllFail\s+(\d+)', row_data)
                    if match:
                        param_name = match.group(1)
                        fail_count = int(match.group(2))
                        param_counts[param_name] = fail_count
            
            summary_data['param_counts'] = param_counts
            
            self.logger.info(f"提取summary信息: gross_die={summary_data.get('gross_die')}, "
                           f"good_die={summary_data.get('good_die')}, yield={summary_data.get('yield')}")
            self.logger.info(f"参数失败计数: {param_counts}")
            
            return summary_data
            
        except Exception as e:
            self.logger.error(f"读取summary_information失败: {e}")
            return {}
    
    def _create_wafer_from_data(self, data_df: pd.DataFrame, spec_df: pd.DataFrame, lot_id: str, file_path: str = None) -> CPWafer:
        """
        从数据创建CPWafer对象
        
        Args:
            data_df: 数据DataFrame
            spec_df: 规格DataFrame
            lot_id: 批次ID
            file_path: 文件路径（用于提取wafer_id）
            
        Returns:
            CPWafer: 晶圆对象
        """
        # 从文件名提取晶圆ID
        if file_path:
            wafer_id = self._extract_wafer_id(file_path)
        else:
            wafer_id = "1"  # 默认值
        
        # 计算良率
        total_chips = len(data_df)
        pass_bins = [1]  # 假设Bin=1为良品
        good_chips = len(data_df[data_df['SOFT_BIN'] == 1]) if 'SOFT_BIN' in data_df.columns else 0
        yield_rate = (good_chips / total_chips * 100) if total_chips > 0 else 0.0
        
        # 创建晶圆对象
        wafer = CPWafer(
            wafer_id=wafer_id,
            chip_count=total_chips,
            yield_rate=yield_rate
        )
        
        # 处理数据并进行必要的字段转换
        data_processed = data_df.copy()
        
        # 将SITE_NUM替换为从文件名提取的wafer_id值
        if 'SITE_NUM' in data_processed.columns:
            data_processed['SITE_NUM'] = int(wafer_id)
        
        # 添加批次和晶圆ID到数据中
        data_processed['Lot_ID'] = lot_id
        data_processed['Wafer_ID'] = int(wafer_id)
        
        # 重新排列列顺序，确保Lot_ID和Wafer_ID在最前面
        basic_columns = ['Lot_ID', 'Wafer_ID']
        other_columns = [col for col in data_processed.columns if col not in basic_columns]
        column_order = basic_columns + other_columns
        data_processed = data_processed[column_order]
        
        # 设置坐标和基本信息（从处理后的数据）
        if 'X_COORD' in data_processed.columns:
            wafer.x = data_processed['X_COORD'].values
        if 'Y_COORD' in data_processed.columns:
            wafer.y = data_processed['Y_COORD'].values
        if 'PART_INDEX' in data_processed.columns:
            wafer.seq = data_processed['PART_INDEX'].values
        if 'SOFT_BIN' in data_processed.columns:
            wafer.bin = data_processed['SOFT_BIN'].values
        
        # 设置芯片数据和规格数据
        wafer.chip_data = data_processed
        wafer.spec_data = spec_df
        wafer.lot_id = lot_id
        
        # 读取summary信息
        if file_path:
            summary_data = self._read_summary_information(file_path)
            wafer.summary_data = summary_data
        
        return wafer
    
    def _extract_parameters_from_spec(self, spec_df: pd.DataFrame) -> List[CPParameter]:
        """
        从规格数据中提取参数信息
        
        Args:
            spec_df: 规格DataFrame
            
        Returns:
            List[CPParameter]: 参数列表
        """
        parameters = []
        
        # 跳过非参数列
        skip_columns = ['SITE_NUM', 'PART_INDEX', 'PASSFG', 'SOFT_BIN', 'T_TIME', 
                       'X_COORD', 'Y_COORD', 'TEST_NUM']
        
        for column in spec_df.columns:
            if column in skip_columns:
                continue
                
            # 获取单位
            unit = 'Unknown'
            if 'UNIT' in spec_df.index:
                unit_value = spec_df.loc['UNIT', column]
                if pd.notna(unit_value) and str(unit_value).strip():
                    unit = str(unit_value).strip()
            
            # 获取规格限制
            sl = None
            su = None
            
            if 'LIMIT_LOW' in spec_df.index:
                sl_value = spec_df.loc['LIMIT_LOW', column]
                if pd.notna(sl_value):
                    try:
                        sl = float(sl_value)
                    except (ValueError, TypeError):
                        pass
            
            if 'LIMIT_HIGH' in spec_df.index:
                su_value = spec_df.loc['LIMIT_HIGH', column]
                if pd.notna(su_value):
                    try:
                        su = float(su_value)
                    except (ValueError, TypeError):
                        pass
            
            # 创建参数对象
            param = CPParameter(
                id=column,
                unit=unit,
                sl=sl,
                su=su
            )
            parameters.append(param)
        
        return parameters
    
    def get_supported_formats(self) -> List[str]:
        """
        获取支持的格式列表
        
        Returns:
            List[str]: 支持的格式列表
        """
        return ['LION_EXCEL']
    
    def get_format_description(self) -> str:
        """
        获取格式描述
        
        Returns:
            str: 格式描述
        """
        return "Lion公司Excel格式CP测试数据（.xlsx/.xls）"