"""
DCP 格式数据读取器，用于读取和解析 DCP 格式的 CP 测试数据文件 (.txt)。
"""

import os
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Union, Optional, Tuple

from cp_data_processor.readers.base_reader import BaseReader
from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter


class DCPReader(BaseReader):
    """
    DCP 格式 CP 数据读取器。
    DCP 格式是一种制表符分隔的文本文件格式。
    """
    
    def __init__(self, file_paths: Union[str, List[str]], pass_bin: int = 1):
        """
        初始化 DCP 格式数据读取器
        
        Args:
            file_paths: 要读取的文件路径，可以是单个字符串或字符串列表
            pass_bin: 表示通过的 Bin 值，默认为 1
        """
        super().__init__(file_paths, pass_bin)
        self.header_map = {}  # 列标题映射到索引
        self.param_columns = []  # 参数列索引列表
    
    def read(self) -> CPLot:
        """
        读取所有 DCP 格式文件并返回一个填充好的 CPLot 对象。
        
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
        从单个 DCP 格式文件中提取数据到 CPLot 对象。
        
        Args:
            file_path: 要读取的文件路径
            lot: 要填充的 CPLot 对象
        """
        try:
            # 读取制表符分隔的文本文件
            df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
        except UnicodeDecodeError:
            # 如果 UTF-8 解码失败，尝试其他编码
            df = pd.read_csv(file_path, sep='\t', encoding='latin1')
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")
            return
        
        # 如果是第一个文件，提取参数信息
        if lot.param_count == 0:
            self._setup_header_map(df)
            self._add_param_info(df, lot)
        
        # 提取晶圆数据
        wafer_id = self.extract_wafer_id(file_path)
        wafer = self._create_wafer(df, wafer_id, file_path)
        
        # 添加到 lot 中
        lot.wafers.append(wafer)
    
    def _setup_header_map(self, df: pd.DataFrame) -> None:
        """设置列标题映射和参数列列表"""
        self.header_map = {}
        self.param_columns = []
        
        # 生成列标题映射
        for i, col_name in enumerate(df.columns):
            self.header_map[col_name] = i
            
            # 检查是否为必需的特殊列
            if col_name.lower() not in ['waferid', 'site', 'bin', 'x', 'y']:
                # 假设其他列都是参数列
                self.param_columns.append(i)
    
    def _add_param_info(self, df: pd.DataFrame, lot: CPLot) -> None:
        """添加参数信息到 lot 对象"""
        test_name_dict = {}  # 用于确保参数名称唯一
        
        for col_idx in self.param_columns:
            if col_idx < len(df.columns):
                param_name = df.columns[col_idx]
                
                # 跳过空名称
                if param_name.strip():
                    # 创建参数对象
                    param_id = self._get_unique_name(param_name, test_name_dict)
                    
                    # 尝试从数据推断上下限和单位
                    sl, su, unit = self._infer_limits_and_unit(df, df.columns[col_idx])
                    
                    # 创建参数对象并添加到 lot
                    param = CPParameter(
                        id=param_id,
                        unit=unit,
                        sl=sl,
                        su=su,
                        test_cond=[]  # DCP 格式可能没有明确的测试条件
                    )
                    lot.params.append(param)
        
        # 设置 lot 产品名
        product_name = lot.lot_id.split('-')[0] if '-' in lot.lot_id else lot.lot_id
        lot.product = product_name
        lot.param_count = len(lot.params)
    
    def _create_wafer(self, df: pd.DataFrame, wafer_id: str, file_path: str) -> CPWafer:
        """创建并填充晶圆对象"""
        # 过滤出对应晶圆的数据
        wafer_df = df
        if 'WAFERID' in df.columns:
            # 如果文件包含多个晶圆，过滤出当前晶圆的数据
            wafer_df = df[df['WAFERID'] == wafer_id]
        
        # 如果没有数据，返回空晶圆
        if wafer_df.empty:
            return CPWafer(wafer_id=wafer_id, file_path=file_path)
        
        # 创建晶圆对象
        wafer = CPWafer(
            wafer_id=wafer_id,
            file_path=file_path,
            chip_count=len(wafer_df)
        )
        
        # 提取基本数据：序号、Bin、X坐标、Y坐标
        try:
            if 'SITE' in wafer_df.columns:
                wafer.seq = np.array(wafer_df['SITE'])
            else:
                wafer.seq = np.array(range(1, len(wafer_df) + 1))
            
            if 'BIN' in wafer_df.columns:
                wafer.bin = np.array(wafer_df['BIN'])
            elif 'HARDBIN' in wafer_df.columns:
                wafer.bin = np.array(wafer_df['HARDBIN'])
            else:
                wafer.bin = np.ones(len(wafer_df))
            
            if 'X' in wafer_df.columns:
                wafer.x = np.array(wafer_df['X'])
            else:
                wafer.x = np.zeros(len(wafer_df))
            
            if 'Y' in wafer_df.columns:
                wafer.y = np.array(wafer_df['Y'])
            else:
                wafer.y = np.zeros(len(wafer_df))
            
            # 计算晶圆尺寸
            if len(wafer.x) > 0:
                wafer.width = int(np.max(wafer.x) - np.min(wafer.x) + 2)
                wafer.height = int(np.max(wafer.y) - np.min(wafer.y) + 1)
            
        except Exception as e:
            print(f"提取基本数据时出错: {e}")
        
        # 创建参数数据 DataFrame
        param_data = {}
        
        for i, param in enumerate(self.lot.params):
            if i < len(self.param_columns) and self.param_columns[i] < len(wafer_df.columns):
                col_name = wafer_df.columns[self.param_columns[i]]
                if col_name in wafer_df.columns:
                    # 提取参数值并转换为浮点数
                    values = wafer_df[col_name].values
                    float_values = []
                    for val in values:
                        try:
                            float_values.append(float(val))
                        except (ValueError, TypeError):
                            float_values.append(np.nan)
                    
                    param_data[param.id] = np.array(float_values)
        
        wafer.chip_data = pd.DataFrame(param_data)
        return wafer
    
    def _infer_limits_and_unit(self, df: pd.DataFrame, param_name: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """从数据推断参数的上下限和单位"""
        sl = None
        su = None
        unit = None
        
        if param_name in df.columns:
            # 尝试从数据推断单位
            # 在实际应用中，可能需要更复杂的逻辑或者预定义的单位映射
            if 'V' in param_name or 'VOLT' in param_name.upper():
                unit = 'V'
            elif 'A' in param_name or 'CURR' in param_name.upper():
                unit = 'A'
            elif 'OHM' in param_name.upper() or 'RES' in param_name.upper():
                unit = 'Ohm'
            elif 'F' in param_name or 'CAP' in param_name.upper():
                unit = 'F'
            elif 'HZ' in param_name.upper() or 'FREQ' in param_name.upper():
                unit = 'Hz'
            
            # 根据参数名推断规格类型
            param_name_upper = param_name.upper()
            if 'MIN' in param_name_upper or 'LOW' in param_name_upper:
                # 参数名暗示下限
                sl = df[param_name].min() * 0.9  # 假设值的 90% 作为下限
            elif 'MAX' in param_name_upper or 'HIGH' in param_name_upper or 'UP' in param_name_upper:
                # 参数名暗示上限
                su = df[param_name].max() * 1.1  # 假设值的 110% 作为上限
            elif param_name_upper.startswith('B'):
                # 以 B 开头的通常是"望小特性"
                su = df[param_name].max() * 1.1  # 假设值的 110% 作为上限
            else:
                # 其他默认为"望大特性"
                sl = df[param_name].min() * 0.9  # 假设值的 90% 作为下限
        
        return sl, su, unit
    
    def _get_unique_name(self, base_name: str, name_dict: Dict[str, int]) -> str:
        """确保名称唯一性，如果重复则添加数字后缀"""
        if base_name not in name_dict:
            name_dict[base_name] = 1
            return base_name
        
        count = name_dict[base_name] + 1
        name_dict[base_name] = count
        return f"{base_name}{count}" 