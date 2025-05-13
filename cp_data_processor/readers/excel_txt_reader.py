"""
ExcelTXT 格式数据读取器，用于读取和解析伪装成TXT文件的Excel格式CP测试数据。
"""

import os
import pandas as pd
import numpy as np
from typing import List, Dict, Union, Optional, Tuple
import logging
import sys

from cp_data_processor.readers.base_reader import BaseReader
from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter

# 获取日志记录器
logger = logging.getLogger(__name__)

class ExcelTXTReader(BaseReader):
    """
    ExcelTXT 格式 CP 数据读取器。
    用于处理扩展名为.TXT但实际上是Excel格式（Office XML）的文件。
    """
    
    def __init__(self, file_paths: Union[str, List[str]], pass_bin: int = 1):
        """
        初始化 ExcelTXT 格式数据读取器
        
        Args:
            file_paths: 要读取的文件路径，可以是单个字符串或字符串列表
            pass_bin: 表示通过的 Bin 值，默认为 1
        """
        super().__init__(file_paths, pass_bin)
        self.header_map = {}  # 列标题映射到索引
        self.param_columns = []  # 参数列索引列表
    
    def read(self) -> CPLot:
        """
        读取所有 ExcelTXT 格式文件并返回一个填充好的 CPLot 对象。
        
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
        从单个 ExcelTXT 格式文件中提取数据到 CPLot 对象。
        
        Args:
            file_path: 要读取的文件路径
            lot: 要填充的 CPLot 对象
        """
        file_basename = os.path.basename(file_path)
        logger.info(f"开始处理文件: {file_basename}")
        
        try:
            # 使用pandas的read_excel函数读取整个文件
            raw_df = pd.read_excel(file_path, header=None)
            logger.info(f"成功读取Excel格式文件，形状: {raw_df.shape}")
            
            # 提取元数据（Lot ID, Wafer ID等）
            lot_id = None
            wafer_id = None
            for i in range(min(5, raw_df.shape[0])):
                if pd.notna(raw_df.iloc[i, 0]):
                    cell_text = str(raw_df.iloc[i, 0]).lower()
                    if 'lot' in cell_text and pd.notna(raw_df.iloc[i, 1]):
                        lot_id = raw_df.iloc[i, 1]
                    elif 'wafer' in cell_text and pd.notna(raw_df.iloc[i, 1]):
                        wafer_id = raw_df.iloc[i, 1]
            
            if lot_id and not lot.lot_id or lot.lot_id == "UnknownLot":
                lot.lot_id = str(lot_id)
            
            if not wafer_id:
                wafer_id = self.extract_wafer_id(file_path)
            
            # 查找表头行 - 查找包含 "No.U", "X", "Y", "Bin" 的行
            header_row = None
            for i in range(raw_df.shape[0]):
                row_values = [str(x).strip() if pd.notna(x) else '' for x in raw_df.iloc[i]]
                row_text = ' '.join(row_values)
                
                # 检查是否包含关键词
                if any(keyword in row_text for keyword in ['No.U', 'Bin']) and 'X' in row_values and 'Y' in row_values:
                    header_row = i
                    logger.info(f"找到表头行 {i+1}: {row_text[:100]}")
                    break
            
            if header_row is None:
                logger.error(f"无法找到有效表头行，跳过文件: {file_basename}")
                return
            
            # 查找数据起始行 - 第一列是数字的行
            data_row = None
            for i in range(header_row + 1, raw_df.shape[0]):
                # 尝试将第一列转换为整数
                if pd.notna(raw_df.iloc[i, 0]):
                    try:
                        int(float(raw_df.iloc[i, 0]))  # 先转为float再转为int，处理可能的浮点数表示
                        data_row = i
                        logger.info(f"找到数据起始行 {i+1}: {raw_df.iloc[i, 0]}")
                        break
                    except (ValueError, TypeError):
                        pass
            
            if data_row is None:
                logger.error(f"无法找到数据起始行，跳过文件: {file_basename}")
                return
            
            # 提取列名
            header = []
            for j in range(raw_df.shape[1]):
                if pd.notna(raw_df.iloc[header_row, j]) and str(raw_df.iloc[header_row, j]).strip():
                    header.append(str(raw_df.iloc[header_row, j]).strip())
                else:
                    # 为空列名添加默认值
                    header.append(f'Unnamed_{j}')
            
            logger.info(f"提取到的表头: {header}")
            
            # 提取数据
            data = raw_df.iloc[data_row:].copy()
            
            # 确保列数匹配
            if len(header) > data.shape[1]:
                header = header[:data.shape[1]]
            elif len(header) < data.shape[1]:
                for j in range(len(header), data.shape[1]):
                    header.append(f'Extra_{j}')
            
            # 设置数据列名
            data.columns = header
            
            # 处理数据类型 - 尝试将数值列转换为浮点数
            for col in data.columns:
                try:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
                except:
                    # 如果转换失败，保留原始类型
                    pass
            
            # 初始化参数信息（如果尚未初始化）
            if lot.param_count == 0:
                self._setup_header_map(data)
                self._add_param_info(data, lot)
                logger.info(f"从文件提取了 {lot.param_count} 个参数信息")
            
            # 创建晶圆对象
            wafer = self._create_wafer(data, wafer_id, file_path)
            
            # 添加到Lot
            if wafer and wafer.chip_count > 0:
                lot.wafers.append(wafer)
                logger.info(f"成功添加晶圆 {wafer.wafer_id}，包含 {wafer.chip_count} 个芯片数据")
            else:
                logger.warning(f"晶圆数据无效或为空，已跳过: {file_basename}")
            
        except Exception as e:
            logger.exception(f"处理文件 {file_path} 时出错: {str(e)}")
            return
    
    def _setup_header_map(self, df: pd.DataFrame) -> None:
        """设置列标题映射和参数列列表"""
        self.header_map = {}
        self.param_columns = []
        
        # 生成列标题映射
        for i, col_name in enumerate(df.columns):
            self.header_map[col_name] = i
            
            # 检查是否为必需的特殊列
            if col_name.lower() not in ['no.u', 'waferid', 'site', 'bin', 'x', 'y']:
                # 假设其他列都是参数列
                self.param_columns.append(i)
    
    def _add_param_info(self, df: pd.DataFrame, lot: CPLot) -> None:
        """添加参数信息到 lot 对象"""
        test_name_dict = {}  # 用于确保参数名称唯一
        
        for col_idx in self.param_columns:
            if col_idx < len(df.columns):
                param_name = df.columns[col_idx]
                
                # 跳过空名称
                if param_name.strip() and not param_name.startswith('Unnamed_') and not param_name.startswith('Extra_'):
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
                        test_cond=[]  # ExcelTXT 格式可能没有明确的测试条件
                    )
                    lot.params.append(param)
        
        # 设置 lot 产品名
        if not lot.product:
            product_name = lot.lot_id.split('-')[0] if '-' in lot.lot_id else lot.lot_id
            lot.product = product_name
        
        lot.param_count = len(lot.params)
    
    def _create_wafer(self, df: pd.DataFrame, wafer_id: str, file_path: str) -> CPWafer:
        """创建并填充晶圆对象"""
        # 如果数据为空，返回空晶圆
        if df.empty:
            logger.warning(f"数据为空，无法创建晶圆: {wafer_id}")
            return CPWafer(wafer_id=wafer_id, file_path=file_path)
        
        # 创建晶圆对象
        wafer = CPWafer(
            wafer_id=wafer_id,
            file_path=file_path,
            chip_count=len(df)
        )
        
        # 提取基本数据：序号、Bin、X坐标、Y坐标
        try:
            # 尝试不同列名组合
            seq_cols = ['No.U', 'NO.U', 'Site', 'SITE', 'SEQ', 'Seq']
            bin_cols = ['Bin', 'BIN', 'HARDBIN', 'HardBin']
            x_cols = ['X', 'x', 'X_COORD']
            y_cols = ['Y', 'y', 'Y_COORD']
            
            # 查找序号列
            seq_col = next((col for col in seq_cols if col in df.columns), None)
            if seq_col:
                wafer.seq = np.array(df[seq_col].astype(float, errors='ignore'))
            else:
                wafer.seq = np.array(range(1, len(df) + 1))
            
            # 查找Bin列
            bin_col = next((col for col in bin_cols if col in df.columns), None)
            if bin_col:
                wafer.bin = np.array(df[bin_col].astype(float, errors='ignore'))
            else:
                # 如果找不到Bin列，默认全部为Pass（使用lot的pass_bin值）
                wafer.bin = np.ones(len(df)) * 1
            
            # 查找X坐标列
            x_col = next((col for col in x_cols if col in df.columns), None)
            if x_col:
                wafer.x = np.array(df[x_col].astype(float, errors='ignore'))
            else:
                wafer.x = np.zeros(len(df))
            
            # 查找Y坐标列
            y_col = next((col for col in y_cols if col in df.columns), None)
            if y_col:
                wafer.y = np.array(df[y_col].astype(float, errors='ignore'))
            else:
                wafer.y = np.zeros(len(df))
            
            # 提取参数列数据
            param_data = pd.DataFrame()
            for i in self.param_columns:
                if i < len(df.columns):
                    col_name = df.columns[i]
                    if col_name in df.columns:  # 验证列名存在
                        param_data[col_name] = df[col_name]
            
            # 保存数据到晶圆对象
            wafer.chip_data = param_data
            
            return wafer
            
        except Exception as e:
            logger.exception(f"创建晶圆对象时出错: {str(e)}")
            return CPWafer(wafer_id=wafer_id, file_path=file_path)
    
    def _infer_limits_and_unit(self, df: pd.DataFrame, param_name: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """尝试从数据推断参数的上下限和单位"""
        try:
            # 默认值
            sl = None
            su = None
            unit = None
            
            # 尝试处理仅包含数值的列
            values = df[param_name].dropna()
            numeric_values = pd.to_numeric(values, errors='coerce').dropna()
            
            if len(numeric_values) > 0:
                # 使用数据的最小值和最大值作为默认的规格下限和上限
                sl = float(numeric_values.min())
                su = float(numeric_values.max())
                
                # 尝试从参数名中提取单位（通常在结尾）
                unit_match = None
                common_units = ['V', 'A', 'mA', 'uA', 'nA', 'pA', 'OHM', 'mOHM', 'ns', 'ms', 'us']
                for u in common_units:
                    if param_name.endswith(u):
                        unit_match = u
                        break
                
                if unit_match:
                    unit = unit_match
            
            return sl, su, unit
        except Exception as e:
            logger.warning(f"推断参数 {param_name} 的限值和单位时出错: {str(e)}")
            return None, None, None
    
    def _get_unique_name(self, base_name: str, name_dict: Dict[str, int]) -> str:
        """获取唯一的参数名称，避免重复"""
        if base_name not in name_dict:
            name_dict[base_name] = 0
            return base_name
        else:
            name_dict[base_name] += 1
            return f"{base_name}_{name_dict[base_name]}"

    @staticmethod
    def is_excel_format(file_path: str) -> bool:
        """
        检查文件是否为Excel格式（即使扩展名是.TXT）
        
        Args:
            file_path: 要检查的文件路径
            
        Returns:
            bool: 如果文件是Excel格式，返回True；否则返回False
        """
        try:
            # 尝试读取文件的前几个字节
            with open(file_path, 'rb') as f:
                header = f.read(8)  # 读取前8个字节
            
            # 检查是否为Office XML格式的特征（以"PK"开头）
            if header.startswith(b'PK'):
                return True
            
            # 尝试使用pandas读取
            try:
                # 尝试读取前几行
                pd.read_excel(file_path, nrows=5)
                return True
            except:
                pass
                
            return False
        except:
            return False 