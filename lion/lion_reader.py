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
import math

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter
from cp_data_processor.readers.base_reader import BaseReader

logger = logging.getLogger(__name__)


LION_V1_FIXED_COLUMNS = (
    'SITE_NUM',
    'PART_INDEX',
    'PASSFG',
    'SOFT_BIN',
    'T_TIME',
    'X_COORD',
    'Y_COORD',
    'TEST_NUM',
)
LION_V1_SPEC_ROWS = ('UNIT', 'LIMIT_LOW', 'LIMIT_HIGH')


class LionV1FormatError(ValueError):
    """Raised when a workbook violates the approved dynamic Lion V1 contract."""


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
            
            # 只按工作簿内容识别，不依赖目录名称或固定参数数量。
            xl_file = pd.ExcelFile(file_path)
            required_sheets = {'summary_information', 'dut_data'}
            if not required_sheets.issubset(set(xl_file.sheet_names)):
                return False

            preview = pd.read_excel(
                file_path,
                sheet_name='dut_data',
                header=None,
                nrows=4,
            )
            if len(preview) < 4 or preview.shape[1] <= len(LION_V1_FIXED_COLUMNS):
                return False
            header = tuple(self._normalize_header(value) for value in preview.iloc[0])
            if header[:len(LION_V1_FIXED_COLUMNS)] != LION_V1_FIXED_COLUMNS:
                return False
            if any(not name for name in header[len(LION_V1_FIXED_COLUMNS):]):
                return False
            spec_labels = tuple(
                self._normalize_header(value) for value in preview.iloc[1:4, 0]
            )
            if spec_labels != LION_V1_SPEC_ROWS:
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
            lot.parameter_schema = tuple(
                spec_df.columns[len(LION_V1_FIXED_COLUMNS):]
            )
            
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
        从文件路径提取批次ID（使用文件夹名称作为lot_id）
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 批次ID（文件夹名称）
        """
        file_path_obj = Path(file_path)
        
        # Lion公司的文件夹名称就是lot_id（如./F25260021.01/F25260021_12.xlsx的lot_id是F25260021.01）
        lot_id = file_path_obj.parent.name
        
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
        raw = pd.read_excel(file_path, sheet_name='dut_data', header=None)
        if len(raw) < 5:
            raise LionV1FormatError('dut_data 缺少规格行或 Die 数据')

        header = [self._normalize_header(value) for value in raw.iloc[0]]
        if tuple(header[:len(LION_V1_FIXED_COLUMNS)]) != LION_V1_FIXED_COLUMNS:
            raise LionV1FormatError(
                'dut_data 固定字段必须为 ' + ','.join(LION_V1_FIXED_COLUMNS)
            )
        parameter_columns = header[len(LION_V1_FIXED_COLUMNS):]
        if not parameter_columns or any(not name for name in parameter_columns):
            raise LionV1FormatError('dut_data 至少需要一个非空动态测试参数')
        duplicates = sorted({name for name in header if header.count(name) > 1})
        if duplicates:
            raise LionV1FormatError(f'dut_data 存在重复字段: {duplicates}')

        body = raw.iloc[1:].copy()
        body.columns = header
        spec_labels = tuple(
            self._normalize_header(value)
            for value in body.iloc[:3][LION_V1_FIXED_COLUMNS[0]]
        )
        if spec_labels != LION_V1_SPEC_ROWS:
            raise LionV1FormatError(
                'dut_data 前三行必须依次为 UNIT、LIMIT_LOW、LIMIT_HIGH'
            )

        spec_data = body.head(3).copy()
        spec_data.index = list(LION_V1_SPEC_ROWS)
        self._validate_parameter_specs(spec_data, parameter_columns)

        data_df = body.iloc[3:].copy()
        data_df = data_df.loc[~data_df.isna().all(axis=1)].copy()
        if data_df.empty:
            raise LionV1FormatError('dut_data 没有有效 Die 数据')

        required_base = ['PART_INDEX', 'SOFT_BIN', 'X_COORD', 'Y_COORD']
        partial_rows = data_df[required_base].isna().any(axis=1)
        if partial_rows.any():
            rows = [int(index) + 1 for index in data_df.index[partial_rows][:5]]
            raise LionV1FormatError(f'Die 基础字段不完整，Excel 行: {rows}')

        for col in LION_V1_FIXED_COLUMNS:
            self._coerce_numeric_column(
                data_df,
                col,
                allow_blank=(col == 'T_TIME'),
            )
        for col in parameter_columns:
            self._coerce_numeric_column(data_df, col, allow_blank=True)

        bins = data_df['SOFT_BIN'].dropna()
        if not np.isclose(bins, np.round(bins)).all():
            raise LionV1FormatError('SOFT_BIN 必须为整数')
        if data_df.duplicated(['X_COORD', 'Y_COORD']).any():
            raise LionV1FormatError('同一 Wafer 存在重复 X_COORD + Y_COORD')
        if data_df.duplicated(['PART_INDEX']).any():
            raise LionV1FormatError('同一 Wafer 存在重复 PART_INDEX/Seq')

        data_df = data_df.reset_index(drop=True)
        return data_df, spec_data

    @staticmethod
    def _normalize_header(value) -> str:
        if pd.isna(value):
            return ''
        return str(value).strip()

    @staticmethod
    def _coerce_numeric_column(
        data: pd.DataFrame,
        column: str,
        *,
        allow_blank: bool,
    ) -> None:
        source = data[column]
        converted = pd.to_numeric(source, errors='coerce')
        invalid = source.notna() & converted.isna()
        if invalid.any():
            rows = [int(index) + 1 for index in source.index[invalid][:5]]
            raise LionV1FormatError(
                f'{column} 包含未批准的非数值内容，Excel 行: {rows}'
            )
        if not allow_blank and converted.isna().any():
            rows = [int(index) + 1 for index in source.index[converted.isna()][:5]]
            raise LionV1FormatError(f'{column} 不允许为空，Excel 行: {rows}')
        data[column] = converted

    @staticmethod
    def _validate_parameter_specs(
        spec_data: pd.DataFrame,
        parameter_columns: List[str],
    ) -> None:
        for column in parameter_columns:
            for row_name in ('LIMIT_LOW', 'LIMIT_HIGH'):
                value = spec_data.loc[row_name, column]
                if pd.isna(value) or str(value).strip() == '':
                    continue
                try:
                    numeric = float(value)
                except (TypeError, ValueError) as exc:
                    raise LionV1FormatError(
                        f'{column} 的 {row_name} 不是数值: {value}'
                    ) from exc
                if not math.isfinite(numeric):
                    raise LionV1FormatError(
                        f'{column} 的 {row_name} 不是有限数值: {value}'
                    )
    
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
            file_path=file_path,
            source_lot_id=lot_id,
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
