"""
MEX 格式数据读取器，用于读取和解析 MEX 格式的 CP 测试数据文件 (.xls, .xlsx)。
"""

import os
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Union, Optional, Tuple, Any

from cp_data_processor.readers.base_reader import BaseReader
from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter


class MEXReader(BaseReader):
    """
    MEX 格式 CP 数据读取器。
    MEX 格式是一种常见的 Excel 格式 CP 测试数据。
    """
    
    def __init__(self, file_paths: Union[str, List[str]], pass_bin: int = 1):
        """
        初始化 MEX 格式数据读取器
        
        Args:
            file_paths: 要读取的文件路径，可以是单个字符串或字符串列表
            pass_bin: 表示通过的 Bin 值，默认为 1
        """
        super().__init__(file_paths, pass_bin)
        # MEX 格式特有的常量和配置
        self.header_row = 0  # 默认标题行索引
        self.data_start_row = 1  # 默认数据起始行索引
        self.seq_col = None  # 序号列
        self.bin_col = None  # Bin 值列
        self.x_col = None  # X 坐标列
        self.y_col = None  # Y 坐标列
        self.param_cols = {}  # 参数列映射 {参数索引: 列索引}
    
    def read(self) -> CPLot:
        """
        读取所有 MEX 格式文件并返回一个填充好的 CPLot 对象。
        
        Returns:
            CPLot: 包含所有读取数据的 CPLot 对象
        """
        # 创建新的 CPLot 对象
        lot_id = self.extract_lot_id(self.file_paths[0]) if self.file_paths else "UnknownLot"
        self.lot = CPLot(lot_id=lot_id, pass_bin=self.pass_bin)
        
        # 遍历所有文件
        for file_path in self.file_paths:
            self._extract_from_file(file_path, self.lot)
        
        # 更新计数并合并数据
        self.lot.update_counts()
        self.lot.combine_data_from_wafers()
        
        return self.lot
    
    def _extract_from_file(self, file_path: str, lot: CPLot) -> None:
        """
        从单个 MEX 格式文件中提取数据到 CPLot 对象。
        
        Args:
            file_path: 要读取的文件路径
            lot: 要填充的 CPLot 对象
        """
        try:
            # 读取 Excel 文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # 替换 'Untested' 为 NaN
            df = df.replace('Untested', np.nan)
            
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")
            return
        
        # 如果是第一个晶圆，设置列映射和参数信息
        if lot.param_count == 0:
            self._setup_column_mapping(df)
            self._add_param_info(df, lot)
        
        # 提取晶圆数据
        wafer_id = self.extract_wafer_id(file_path)
        wafer = self._create_wafer(df, wafer_id, file_path)
        
        # 添加到 lot 中
        lot.wafers.append(wafer)
    
    def _setup_column_mapping(self, df: pd.DataFrame) -> None:
        """设置列映射，确定特殊列和参数列"""
        # 查找特殊列
        for i, col_name in enumerate(df.columns):
            col_name_upper = str(col_name).upper()
            
            if 'SEQ' in col_name_upper or 'SITE' in col_name_upper:
                self.seq_col = i
            elif 'BIN' in col_name_upper:
                self.bin_col = i
            elif col_name_upper == 'X':
                self.x_col = i
            elif col_name_upper == 'Y':
                self.y_col = i
        
        # 设置默认值（如果没有找到对应列）
        if self.seq_col is None:
            self.seq_col = 0  # 假设第一列是序号
        if self.bin_col is None:
            self.bin_col = 1  # 假设第二列是 Bin
        if self.x_col is None:
            self.x_col = 2  # 假设第三列是 X
        if self.y_col is None:
            self.y_col = 3  # 假设第四列是 Y
        
        # 确定参数列（除了特殊列外的所有列）
        special_cols = {self.seq_col, self.bin_col, self.x_col, self.y_col}
        param_index = 0
        
        for i, col_name in enumerate(df.columns):
            if i not in special_cols and pd.notna(col_name) and str(col_name).strip():
                param_index += 1
                self.param_cols[param_index] = i
    
    def _add_param_info(self, df: pd.DataFrame, lot: CPLot) -> None:
        """添加参数信息到 lot 对象"""
        test_name_dict = {}  # 用于确保参数名称唯一
        
        for param_idx, col_idx in self.param_cols.items():
            if col_idx < len(df.columns):
                param_name = str(df.columns[col_idx])
                
                # 跳过空名称
                if param_name.strip():
                    # 创建参数对象
                    param_id = self._get_unique_name(param_name, test_name_dict)
                    
                    # 尝试从数据推断上下限和单位
                    sl, su, unit = self._infer_limits_and_unit(df, col_idx)
                    
                    # 创建参数对象并添加到 lot
                    param = CPParameter(
                        id=param_id,
                        unit=unit,
                        sl=sl,
                        su=su,
                        test_cond=[]  # MEX 格式可能没有明确的测试条件
                    )
                    lot.params.append(param)
        
        # 设置 lot 产品名
        product_name = lot.lot_id.split('-')[0] if '-' in lot.lot_id else lot.lot_id
        lot.product = product_name
        lot.param_count = len(lot.params)
    
    def _create_wafer(self, df: pd.DataFrame, wafer_id: str, file_path: str) -> CPWafer:
        """创建并填充晶圆对象"""
        # 提取数据部分
        data_df = df.iloc[self.data_start_row:]
        
        # 如果没有数据，返回空晶圆
        if data_df.empty:
            return CPWafer(wafer_id=wafer_id, file_path=file_path)
        
        # 创建晶圆对象
        wafer = CPWafer(
            wafer_id=wafer_id,
            file_path=file_path,
            chip_count=len(data_df)
        )
        
        # 提取基本数据：序号、Bin、X坐标、Y坐标
        try:
            wafer.seq = np.array(data_df.iloc[:, self.seq_col]) if self.seq_col < data_df.shape[1] else np.array(range(1, len(data_df) + 1))
            wafer.bin = np.array(data_df.iloc[:, self.bin_col]) if self.bin_col < data_df.shape[1] else np.ones(len(data_df))
            wafer.x = np.array(data_df.iloc[:, self.x_col]) if self.x_col < data_df.shape[1] else np.zeros(len(data_df))
            wafer.y = np.array(data_df.iloc[:, self.y_col]) if self.y_col < data_df.shape[1] else np.zeros(len(data_df))
            
            # 计算晶圆尺寸
            if len(wafer.x) > 0:
                wafer.width = int(np.max(wafer.x) - np.min(wafer.x) + 2)
                wafer.height = int(np.max(wafer.y) - np.min(wafer.y) + 1)
            
        except Exception as e:
            print(f"提取基本数据时出错: {e}")
        
        # 创建参数数据 DataFrame
        param_data = {}
        
        for param_idx, col_idx in self.param_cols.items():
            if param_idx <= len(self.lot.params) and col_idx < data_df.shape[1]:
                param_id = self.lot.params[param_idx - 1].id
                
                # 提取参数值并转换为浮点数
                values = data_df.iloc[:, col_idx].values
                float_values = []
                for val in values:
                    try:
                        float_values.append(float(val))
                    except (ValueError, TypeError):
                        float_values.append(np.nan)
                
                param_data[param_id] = np.array(float_values)
        
        wafer.chip_data = pd.DataFrame(param_data)
        return wafer
    
    def _infer_limits_and_unit(self, df: pd.DataFrame, col_idx: int) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """从数据推断参数的上下限和单位"""
        sl = None
        su = None
        unit = None
        
        if col_idx < len(df.columns):
            param_name = str(df.columns[col_idx])
            param_name_upper = param_name.upper()
            
            # 尝试从参数名称推断单位
            if 'V' in param_name_upper or 'VOLT' in param_name_upper:
                unit = 'V'
            elif 'A' in param_name_upper or 'CURR' in param_name_upper:
                unit = 'A'
            elif 'OHM' in param_name_upper or 'RES' in param_name_upper:
                unit = 'Ohm'
            elif 'F' in param_name_upper or 'CAP' in param_name_upper:
                unit = 'F'
            elif 'HZ' in param_name_upper or 'FREQ' in param_name_upper:
                unit = 'Hz'
            
            # 从实际数据推断上下限
            data_values = df.iloc[self.data_start_row:, col_idx]
            numeric_values = pd.to_numeric(data_values, errors='coerce')
            valid_values = numeric_values.dropna()
            
            if not valid_values.empty:
                min_val = valid_values.min()
                max_val = valid_values.max()
                
                # 根据参数名推断规格类型
                if 'MIN' in param_name_upper or 'LOW' in param_name_upper:
                    # 参数名暗示下限
                    sl = min_val * 0.9  # 假设值的 90% 作为下限
                elif 'MAX' in param_name_upper or 'HIGH' in param_name_upper or 'UP' in param_name_upper:
                    # 参数名暗示上限
                    su = max_val * 1.1  # 假设值的 110% 作为上限
                elif param_name_upper.startswith('B'):
                    # 以 B 开头的通常是"望小特性"
                    su = max_val * 1.1  # 假设值的 110% 作为上限
                else:
                    # 其他默认为"望大特性"
                    sl = min_val * 0.9  # 假设值的 90% 作为下限
        
        return sl, su, unit
    
    def _get_unique_name(self, base_name: str, name_dict: Dict[str, int]) -> str:
        """确保名称唯一性，如果重复则添加数字后缀"""
        if base_name not in name_dict:
            name_dict[base_name] = 1
            return base_name
        
        count = name_dict[base_name] + 1
        name_dict[base_name] = count
        return f"{base_name}{count}" 