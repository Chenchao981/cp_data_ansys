"""
DCP 格式数据读取器，用于读取和解析 DCP 格式的 CP 测试数据文件 (.txt)。
"""

import os
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Union, Optional, Tuple
import io # 导入io模块
import logging # 导入日志模块
import sys # 添加系统模块

from cp_data_processor.readers.base_reader import BaseReader
from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter

logger = logging.getLogger(__name__) # 获取日志记录器
# 设置日志级别为DEBUG以显示所有日志
logger.setLevel(logging.DEBUG)
# 确保日志输出到控制台
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

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
        针对特定格式的CP文件进行优化：表头在第6行，数据从第15行开始。
        跳过LimitU, LimitL, Bias行。
        """
        file_basename = os.path.basename(file_path)
        logger.info(f"开始处理文件: {file_basename}")

        try:
            # 直接以二进制模式读取文件，强制不使用解码
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 尝试解码
            decoded = None
            for encoding in ['utf-8', 'latin1', 'gbk']:
                try:
                    decoded = content.decode(encoding)
                    logger.info(f"成功使用 {encoding} 解码")
                    break
                except:
                    continue
            
            if decoded is None:
                # 如果解码失败，强制使用latin1（不会引发解码错误）
                decoded = content.decode('latin1', errors='replace')
                logger.warning(f"无法使用标准编码解码，强制使用latin1替代字符")
            
            # 按行分割
            lines = decoded.splitlines()
            line_count = len(lines)
            
            if line_count < 16: # 需要至少16行（根据您提供的示例）
                logger.error(f"文件行数不足: {line_count}行")
                return
            
            # --- 硬编码表头和数据位置 ---
            # 根据您提供的示例，第6行是表头，第15行之后是数据
            header_line = lines[6] if line_count > 7 else None
            data_lines = lines[15:] if line_count > 15 else []
            
            if not header_line:
                logger.error("找不到表头行")
                return
                
            if not data_lines:
                logger.error("找不到数据行")
                return
            
            # 日志输出前几行数据，帮助调试
            logger.debug(f"表头行: {header_line[:100]}...")
            for i, line in enumerate(data_lines[:3]):
                logger.debug(f"数据行 {i+1}: {line[:100]}...")
            
            # 准备给Pandas的内容
            cleaned_data = header_line + '\n' + '\n'.join([line for line in data_lines if line.strip()])
            
            # 创建StringIO对象
            csv_data = io.StringIO(cleaned_data)
            
            # 使用pandas读取数据
            df = pd.read_csv(
                csv_data, 
                sep='\t',          # 使用制表符分隔
                header=0,          # 第一行为表头
                engine='python',   # 使用Python引擎
                skip_blank_lines=True,
                on_bad_lines='warn'
            )
            
            if df.empty:
                logger.error("Pandas返回了空DataFrame")
                return
                
            # 处理列名问题：确保所有列都有名称
            df.columns = [f"Col{i}" if not col or pd.isna(col) else col for i, col in enumerate(df.columns)]
            
            # 清理列名中的空白
            df.columns = df.columns.str.strip()
            
            logger.info(f"成功读取数据，形状: {df.shape}")
            
            # 初始化参数信息
            if lot.param_count == 0:
                self._setup_header_map(df)
                self._add_param_info(df, lot)
                logger.info(f"从文件提取了 {lot.param_count} 个参数信息")
            
            # 创建晶圆对象
            wafer_id = self.extract_wafer_id(file_path)
            wafer = self._create_wafer(df, wafer_id, file_path)
            
            # 添加到Lot
            if wafer and wafer.chip_count > 0:
                lot.wafers.append(wafer)
                logger.info(f"成功添加晶圆 {wafer.wafer_id}，包含 {wafer.chip_count} 个芯片数据")
            else:
                logger.warning(f"晶圆数据无效或为空，已跳过")
                
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