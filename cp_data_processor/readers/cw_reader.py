"""
CW 格式数据读取器，用于读取和解析 CW 格式的 CP 测试数据文件 (.csv)。
支持单晶圆 (CWSW) 和多晶圆 (CWMW) 两种模式。
"""

import os
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Union, Optional, Tuple

from cp_data_processor.readers.base_reader import BaseReader
from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter

# 定义 CW 格式数据文件的列和行常量
PARAM_START_COL = 11       # 参数数据起始列
STD_ITEM_ROW = 14          # 标准项目行
USER_ITEM_ROW = 15         # 用户项目行
LIMIT_ROW = 16             # 限制值行
COND_START_ROW = 17        # 测试条件开始行
COND_END_ROW = 18          # 测试条件结束行
UNIT_RATE_ROW = 20         # 单位换算行
DATA_START_ROW = 30        # 数据开始行
SEQ_COL = 1                # 序号列
BIN_COL = 2                # Bin值列
X_COL = 3                  # X坐标列
Y_COL = 5                  # Y坐标列


class CWReader(BaseReader):
    """
    CW 格式 CP 数据读取器，支持单晶圆和多晶圆数据格式。
    """
    
    def __init__(self, file_paths: Union[str, List[str]], pass_bin: int = 1, multi_wafer: bool = False):
        """
        初始化 CW 格式数据读取器
        
        Args:
            file_paths: 要读取的文件路径，可以是单个字符串或字符串列表
            pass_bin: 表示通过的 Bin 值，默认为 1
            multi_wafer: 是否为多晶圆模式，默认为 False (单晶圆模式)
        """
        super().__init__(file_paths, pass_bin)
        self.multi_wafer = multi_wafer
        self.param_positions = {}  # 参数位置映射 {列索引: 参数索引}
    
    def read(self) -> CPLot:
        """
        读取所有 CW 格式文件并返回一个填充好的 CPLot 对象。
        
        Returns:
            CPLot: 包含所有读取数据的 CPLot 对象
        """
        # 创建新的 CPLot 对象
        lot_id = self.extract_lot_id(self.file_paths[0]) if self.file_paths else "UnknownLot"
        self.lot = CPLot(lot_id=lot_id, pass_bin=self.pass_bin)
        
        # 多晶圆模式下只读取第一个文件
        if self.multi_wafer and self.file_paths:
            self._extract_from_file(self.file_paths[0], self.lot)
        else:
            # 单晶圆模式下遍历所有文件
            for file_path in self.file_paths:
                self._extract_from_file(file_path, self.lot)
        
        # 更新计数并合并数据
        self.lot.update_counts()
        self.lot.combine_data_from_wafers()
        
        return self.lot
    
    def _extract_from_file(self, file_path: str, lot: CPLot) -> None:
        """
        从单个 CW 格式文件中提取数据到 CPLot 对象。
        
        Args:
            file_path: 要读取的文件路径
            lot: 要填充的 CPLot 对象
        """
        # 读取 CSV 文件到 DataFrame
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            # 如果 UTF-8 解码失败，尝试其他编码
            df = pd.read_csv(file_path, encoding='latin1')
        
        # 替换 'Untested' 为 NaN
        df = df.replace('Untested', np.nan)
        
        if self.multi_wafer:
            self._extract_multi_wafer(df, lot, file_path)
        else:
            self._extract_single_wafer(df, lot, file_path)
    
    def _extract_single_wafer(self, df: pd.DataFrame, lot: CPLot, file_path: str) -> None:
        """处理单晶圆模式的数据提取"""
        # 如果是第一个晶圆，添加参数信息
        if lot.param_count == 0:
            self._add_param_info(df, lot)
        
        # 提取晶圆 ID
        wafer_id = self.extract_wafer_id(file_path)
        
        # 创建晶圆对象并填充基础数据
        wafer = self._create_wafer(df, wafer_id, file_path)
        
        # 添加到 lot 中
        lot.wafers.append(wafer)
    
    def _extract_multi_wafer(self, df: pd.DataFrame, lot: CPLot, file_path: str) -> None:
        """处理多晶圆模式的数据提取"""
        # 如果是第一次处理，添加参数信息
        if lot.param_count == 0:
            self._add_param_info(df, lot, multi_wafer=True)
        
        # 获取所有晶圆数据的起始行
        wafer_start_rows = self._get_wafer_start_rows(df)
        
        for i, start_row in enumerate(wafer_start_rows):
            # 从数据中提取晶圆 ID
            wafer_id = str(df.iloc[start_row, 1]) if len(df) > start_row and df.shape[1] > 1 else f"Wafer{i+1}"
            
            # 提取该晶圆的数据子集
            end_row = wafer_start_rows[i+1] if i+1 < len(wafer_start_rows) else len(df)
            wafer_df = df.iloc[start_row:end_row].reset_index(drop=True)
            
            # 创建晶圆对象并填充数据
            wafer = self._create_wafer(wafer_df, wafer_id, file_path, start_row)
            
            # 添加到 lot 中
            lot.wafers.append(wafer)
    
    def _add_param_info(self, df: pd.DataFrame, lot: CPLot, multi_wafer: bool = False) -> None:
        """添加参数信息到 lot 对象"""
        param_index = 0
        test_name_dict = {}  # 用于确保参数名称唯一
        
        # 遍历从参数起始列开始的所有列
        for col_idx in range(PARAM_START_COL, df.shape[1]):
            # 获取用户项目名
            if USER_ITEM_ROW < df.shape[0] and col_idx < df.shape[1]:
                param_name = str(df.iloc[USER_ITEM_ROW - 1, col_idx])
                
                # 跳过 "SAME" 和空名称
                if param_name.upper() != "SAME" and param_name.strip():
                    param_index += 1
                    self.param_positions[col_idx] = param_index
                    
                    # 创建参数对象
                    display_name = param_name
                    param_id = self._get_unique_name(param_name, test_name_dict)
                    
                    # 获取限制值和单位
                    limit_value = str(df.iloc[LIMIT_ROW - 1, col_idx]) if LIMIT_ROW - 1 < df.shape[0] else ""
                    unit = self._extract_unit(limit_value)
                    
                    # 设置上限和下限
                    sl, su = self._setup_limits(df, col_idx, param_name)
                    
                    # 获取测试条件
                    test_cond = []
                    for i in range(COND_START_ROW, COND_END_ROW + 1):
                        if i - 1 < df.shape[0] and col_idx < df.shape[1]:
                            cond = str(df.iloc[i - 1, col_idx])
                            test_cond.append(cond)
                    
                    # 创建参数对象并添加到 lot
                    param = CPParameter(
                        id=param_id,
                        unit=unit,
                        sl=sl,
                        su=su,
                        test_cond=test_cond
                    )
                    lot.params.append(param)
        
        # 设置 lot 的产品名
        if multi_wafer:
            # 多晶圆模式下，使用文件名或第一行作为产品名
            product_name = os.path.basename(os.path.dirname(df.iloc[0, 0])) if df.shape[0] > 0 else "Unknown"
        else:
            # 单晶圆模式下，使用文件名的第一部分作为产品名
            product_name = lot.lot_id.split('-')[0] if '-' in lot.lot_id else lot.lot_id
        
        lot.product = product_name
        lot.param_count = len(lot.params)
    
    def _create_wafer(self, df: pd.DataFrame, wafer_id: str, file_path: str, data_start_offset: int = 0) -> CPWafer:
        """创建并填充晶圆对象"""
        # 确定实际数据的起始行
        data_start = DATA_START_ROW - 1 + data_start_offset
        if data_start >= df.shape[0]:
            # 如果数据起始行超出范围，尝试查找数据区域
            for i in range(df.shape[0]):
                if str(df.iloc[i, 0]).strip() == "1":  # 假设第一个芯片的序号为 1
                    data_start = i
                    break
        
        # 计算数据量
        data_count = 0
        for i in range(data_start, df.shape[0]):
            if i < df.shape[0] and df.shape[1] > SEQ_COL and pd.notna(df.iloc[i, SEQ_COL - 1]):
                data_count += 1
            else:
                break
        
        if data_count == 0:
            return CPWafer(wafer_id=wafer_id, file_path=file_path)
        
        # 创建晶圆对象
        wafer = CPWafer(
            wafer_id=wafer_id,
            file_path=file_path,
            chip_count=data_count
        )
        
        # 提取基本数据：序号、Bin、X坐标、Y坐标
        if data_start + data_count <= df.shape[0]:
            wafer.seq = np.array(df.iloc[data_start:data_start+data_count, SEQ_COL-1])
            wafer.bin = np.array(df.iloc[data_start:data_start+data_count, BIN_COL-1])
            wafer.x = np.array(df.iloc[data_start:data_start+data_count, X_COL-1])
            wafer.y = np.array(df.iloc[data_start:data_start+data_count, Y_COL-1])
            
            # 计算晶圆尺寸
            if len(wafer.x) > 0:
                wafer.width = int(np.max(wafer.x) - np.min(wafer.x) + 2)
                wafer.height = int(np.max(wafer.y) - np.min(wafer.y) + 1)
        
        # 创建参数数据 DataFrame
        param_data = {}
        for col_idx, param_idx in self.param_positions.items():
            if col_idx < df.shape[1] and param_idx <= len(self.lot.params):
                param_id = self.lot.params[param_idx-1].id
                values = df.iloc[data_start:data_start+data_count, col_idx].values
                
                # 应用单位换算
                unit_rate = 1.0
                if UNIT_RATE_ROW - 1 < df.shape[0] and col_idx < df.shape[1]:
                    unit_rate_val = df.iloc[UNIT_RATE_ROW-1, col_idx]
                    if pd.notna(unit_rate_val):
                        try:
                            unit_rate = float(unit_rate_val)
                        except (ValueError, TypeError):
                            pass
                
                # 将值转换为浮点数并应用单位换算
                float_values = []
                for val in values:
                    try:
                        float_values.append(float(val) * unit_rate)
                    except (ValueError, TypeError):
                        float_values.append(np.nan)
                
                param_data[param_id] = np.array(float_values)
        
        wafer.chip_data = pd.DataFrame(param_data)
        return wafer
    
    def _get_wafer_start_rows(self, df: pd.DataFrame) -> List[int]:
        """获取多晶圆格式中各晶圆数据的开始行"""
        start_rows = []
        
        for i in range(df.shape[0]):
            if i < df.shape[0] and df.shape[1] > 0:
                cell_value = str(df.iloc[i, 0]).strip()
                if cell_value == "WAFER:":
                    # 检查是否是有效的晶圆数据开始行
                    if i+3 < df.shape[0] and df.shape[1] > 2:
                        chip_count = df.iloc[i, 2]
                        try:
                            if float(chip_count) > 0:
                                start_rows.append(i)
                        except (ValueError, TypeError):
                            pass
        
        return start_rows if start_rows else [0]  # 如果没找到，假设从第一行开始
    
    def _setup_limits(self, df: pd.DataFrame, col_idx: int, param_name: str) -> Tuple[Optional[float], Optional[float]]:
        """设置参数的上下限"""
        sl = None  # 下限
        su = None  # 上限
        
        # 获取限制值信息
        if LIMIT_ROW - 1 < df.shape[0] and col_idx < df.shape[1]:
            limit_value = str(df.iloc[LIMIT_ROW - 1, col_idx])
            
            # 检查下一列是否为 "SAME"
            next_is_same = False
            if col_idx + 2 < df.shape[1] and USER_ITEM_ROW - 1 < df.shape[0]:
                next_item = str(df.iloc[USER_ITEM_ROW - 1, col_idx + 2]).upper()
                next_is_same = (next_item == "SAME")
            
            # 提取数值部分
            numeric_part = re.search(r'-?\d+\.?\d*', limit_value)
            if numeric_part:
                limit_numeric = float(numeric_part.group())
                
                if next_is_same:
                    # 当前列为下限，下一列为上限
                    sl = limit_numeric
                    
                    # 获取上限
                    if col_idx + 2 < df.shape[1] and LIMIT_ROW - 1 < df.shape[0]:
                        su_value = str(df.iloc[LIMIT_ROW - 1, col_idx + 2])
                        su_numeric = re.search(r'-?\d+\.?\d*', su_value)
                        if su_numeric:
                            su = float(su_numeric.group())
                else:
                    # 根据参数名判断是上限还是下限控制
                    if param_name and param_name[0].upper() == 'B':
                        # 以 B 开头的参数通常是"望小特性"，设置上限
                        su = limit_numeric
                    else:
                        # 其他参数通常是"望大特性"，设置下限
                        sl = limit_numeric
        
        return sl, su
    
    def _extract_unit(self, limit_value: str) -> Optional[str]:
        """从限制值字符串中提取单位"""
        if limit_value:
            # 尝试提取单位（假设在数字后面的所有非数字字符）
            match = re.search(r'[a-zA-Z]+', limit_value)
            if match:
                return match.group()
        return None
    
    def _get_unique_name(self, base_name: str, name_dict: Dict[str, int]) -> str:
        """确保名称唯一性，如果重复则添加数字后缀"""
        if base_name not in name_dict:
            name_dict[base_name] = 1
            return base_name
        
        count = name_dict[base_name] + 1
        name_dict[base_name] = count
        return f"{base_name}{count}" 