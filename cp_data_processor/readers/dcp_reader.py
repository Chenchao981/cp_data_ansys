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
        # 从第一个文件路径提取批次ID（使用文件夹名称）
        batch_id = self._extract_batch_id_from_folder(self.file_paths[0]) if self.file_paths else "UnknownLot"
        
        # 创建新的 CPLot 对象，使用文件夹名称作为批次ID
        self.lot = CPLot(lot_id=batch_id, pass_bin=self.pass_bin) 
        
        for file_path in self.file_paths:
            lot_id_from_r2c2, wafer_id_from_r3c2 = self._extract_ids_from_r2c2_r2c3(file_path)
            self._extract_from_file(file_path, self.lot, lot_id_from_r2c2, wafer_id_from_r3c2)

        # 更新计数并合并数据
        self.lot.update_counts()
        self.lot.combine_data_from_wafers()
        
        return self.lot
    
    def _extract_batch_id_from_folder(self, file_path: str) -> str:
        """
        从文件路径中提取批次ID（文件夹名称）
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 批次ID（文件夹名称）
        """
        try:
            # 获取文件的父目录名称作为批次ID
            folder_name = os.path.basename(os.path.dirname(file_path))
            if folder_name and folder_name != '.' and folder_name != '':
                logger.info(f"从文件夹名称提取批次ID: {folder_name}")
                return folder_name
            else:
                # 如果无法获取文件夹名称，使用默认方式
                logger.warning(f"无法从文件路径获取文件夹名称，使用默认提取方式")
                return self.extract_lot_id(file_path)
        except Exception as e:
            logger.error(f"从文件夹提取批次ID时出错: {e}")
            return "UnknownLot_Fallback"
    
    def _extract_ids_from_r2c2_r2c3(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        从文件的第二行第二列和第三行第二列提取LotID和WaferID。
        
        Returns:
            Tuple[Optional[str], Optional[str]]: (lot_id_r2c2, wafer_id_r3c2)
        """
        lot_id_r2c2 = None
        wafer_id_r3c2 = None
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                try:
                    lines = f.readlines()
                except Exception as e:
                    logger.error(f"读取文件时出错: {e}，尝试二进制读取")
                    with open(file_path, 'rb') as f2:
                        content = f2.read()
                        # 尝试不同编码
                        for encoding in ['utf-8', 'latin1', 'gbk']:
                            try:
                                lines = content.decode(encoding).splitlines()
                                logger.info(f"成功使用{encoding}解码文件")
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # 如果所有编码都失败，使用replace模式
                            lines = content.decode('latin1', errors='replace').splitlines()
            
            logger.debug(f"文件的前三行内容：")
            for i in range(min(3, len(lines))):
                logger.debug(f"行 {i+1}: {lines[i]}")
            
            # 提取第二行第二列的LotID
            if len(lines) >= 2:
                # 尝试不同的分隔符
                for sep in ['\t', '\\t', ' ', ',']:
                    parts = lines[1].split(sep)
                    if len(parts) >= 2:
                        lot_id_r2c2 = parts[1].strip()
                        logger.debug(f"使用分隔符 '{sep}' 从R2C2提取到LotID: {lot_id_r2c2}")
                        break
            
            # 提取第三行第二列的WaferID
            if len(lines) >= 3:
                # 尝试不同的分隔符
                for sep in ['\t', '\\t', ' ', ',']:
                    parts = lines[2].split(sep)
                    if len(parts) >= 2:
                        wafer_id_r3c2 = parts[1].strip()
                        logger.debug(f"使用分隔符 '{sep}' 从R3C2提取到WaferID: {wafer_id_r3c2}")
                        break
            
            if len(lines) < 3:
                logger.warning(f"文件 {os.path.basename(file_path)} 行数不足3行，无法提取完整ID信息。")

        except Exception as e:
            logger.error(f"从文件 {os.path.basename(file_path)} 提取ID时出错: {e}")
        
        return lot_id_r2c2, wafer_id_r3c2
    
    def _extract_from_file(self, file_path: str, lot: CPLot, lot_id_r2c2: Optional[str], wafer_id_r3c2: Optional[str]) -> None:
        """
        从单个 DCP 格式文件中提取数据到 CPLot 对象。
        使用从R2C2/R2C3预先提取的ID。
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
            
            # --- LotID 和 WaferID 从参数传入，不再依赖文件名提取 ---
            current_wafer_id = wafer_id_r3c2

            if not current_wafer_id: # 如果从R2C3未能提取到wafer_id，则尝试从文件名后备
                current_wafer_id = self.extract_wafer_id(file_path)
                logger.warning(f"未能从 {file_basename} 的R2C3提取WaferID，回退到从文件名提取: {current_wafer_id}")
            
            # 格式化wafer_id为"250303@203_001"形式
            if wafer_id_r3c2 and lot_id_r2c2:
                # 提取lot_id中的编号部分
                lot_parts = lot_id_r2c2.split('-')
                if len(lot_parts) > 2 and '@' in lot_parts[2]:
                    wafer_part = lot_parts[2].split('@')[0]
                    site_part = lot_parts[2].split('@')[1]
                    formatted_wafer_id = f"{wafer_part}@{site_part}_{wafer_id_r3c2.zfill(3)}"
                    current_wafer_id = formatted_wafer_id
            
            if not lot_id_r2c2:
                 logger.warning(f"未能从 {file_basename} 的R2C2提取LotID。CPWafer.source_lot_id 将为 None。")

            # --- 调整表头和数据位置基于提供的示例 ---
            # 源数据中：
            # 第1行(索引0)为 "Program name..."
            # 标题行 ("No.U X Y Bin...") 实际为文件的第7行 (索引6)
            # 数据从文件的第16行 (索引15) 开始 (跳过Limit和Bias信息行)
            header_line_index = 6 
            data_start_index = 15

            header_line = lines[header_line_index] if line_count > header_line_index else None
            data_lines = lines[data_start_index:] if line_count > data_start_index else []
            
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
            
            # 尝试使用pandas读取数据
            try:
                # 优先尝试使用正则表达式匹配一个或多个空白字符作为分隔符
                csv_data.seek(0) # 确保每次尝试前重置 StringIO 对象
                df = pd.read_csv(csv_data, sep='\s+', engine='python')
                logger.info(f"成功使用 sep='\\s+' 读取数据，形状: {df.shape}")
            except Exception as e_regex:
                logger.warning(f"使用 sep='\\s+' 读取失败: {e_regex}。尝试使用 sep='\\t'...")
                try:
                    csv_data.seek(0)
                    df = pd.read_csv(csv_data, sep='\t', engine='python') # engine='python' 可以更好地处理复杂情况
                    logger.info(f"成功使用 sep='\\t' 读取数据，形状: {df.shape}")
                except Exception as e_tab:
                    logger.error(f"使用 sep='\\t' 也失败: {e_tab}。Pandas无法读取数据。")
                    return
            
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
            wafer = self._create_wafer(df, current_wafer_id, file_path, lot_id_r2c2)
            
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
    
    def _create_wafer(self, df: pd.DataFrame, wafer_id: str, file_path: str, lot_id_r2c2: Optional[str] = None) -> CPWafer:
        """创建并填充晶圆对象"""
        # 过滤出对应晶圆的数据
        wafer_df = df
        if 'WAFERID' in df.columns:
            # 如果文件包含多个晶圆，过滤出当前晶圆的数据
            wafer_df = df[df['WAFERID'] == wafer_id]
        
        # 如果没有数据，返回空晶圆
        if wafer_df.empty:
            return CPWafer(wafer_id=wafer_id, file_path=file_path, source_lot_id=lot_id_r2c2)
        
        # 创建晶圆对象
        wafer = CPWafer(
            wafer_id=wafer_id,
            file_path=file_path,
            source_lot_id=lot_id_r2c2,
            chip_count=len(wafer_df)
        )
        
        # 提取基本数据：序号、Bin、X坐标、Y坐标
        try:
            # 优先使用 'SITE' (如果存在且大小写匹配)
            if 'SITE' in wafer_df.columns:
                wafer.seq = np.array(wafer_df['SITE'])
            else: 
                # 备选方案：不区分大小写查找 'NO.U'
                no_u_col_name = None
                for col in wafer_df.columns:
                    if col.strip().upper() == 'NO.U': 
                        no_u_col_name = col
                        break
                if no_u_col_name:
                     wafer.seq = np.array(wafer_df[no_u_col_name])
                else: # 如果 'SITE' 和 'No.U' 都不存在，则使用行号作为序号
                    logger.warning(f"在晶圆 {wafer_id} 的数据中未找到 'SITE' 或 'NO.U' 列，将使用行号作为序号。可用列: {wafer_df.columns.tolist()}")
                    wafer.seq = np.array(range(1, len(wafer_df) + 1))

            # 修改Bin列的提取逻辑，使其不区分大小写
            bin_col_name = None
            for col in wafer_df.columns:
                col_upper = col.strip().upper() 
                if col_upper == 'BIN':
                    bin_col_name = col
                    break
                elif col_upper == 'HARDBIN':
                    bin_col_name = col
                    break
            
            if bin_col_name:
                wafer.bin = np.array(wafer_df[bin_col_name])
            else:
                logger.warning(f"在晶圆 {wafer_id} 的数据中未找到 'BIN' 或 'HARDBIN' 列，将默认设置为1。可用列: {wafer_df.columns.tolist()}")
                wafer.bin = np.ones(len(wafer_df))

            # 修改X列的提取逻辑，使其不区分大小写
            x_col_name = None
            for col in wafer_df.columns:
                if col.strip().upper() == 'X':
                    x_col_name = col
                    break
            if x_col_name:
                wafer.x = np.array(wafer_df[x_col_name])
            else:
                logger.warning(f"在晶圆 {wafer_id} 的数据中未找到 'X' 列，将默认设置为0。可用列: {wafer_df.columns.tolist()}")
                wafer.x = np.zeros(len(wafer_df))

            # 修改Y列的提取逻辑，使其不区分大小写
            y_col_name = None
            for col in wafer_df.columns:
                if col.strip().upper() == 'Y':
                    y_col_name = col
                    break
            if y_col_name:
                wafer.y = np.array(wafer_df[y_col_name])
            else:
                logger.warning(f"在晶圆 {wafer_id} 的数据中未找到 'Y' 列，将默认设置为0。可用列: {wafer_df.columns.tolist()}")
                wafer.y = np.zeros(len(wafer_df))
            
            # 计算晶圆尺寸
            if wafer.x is not None and len(wafer.x) > 0 and np.any(wafer.x) and \
               wafer.y is not None and len(wafer.y) > 0 and np.any(wafer.y):
                min_x, max_x = np.min(wafer.x), np.max(wafer.x)
                min_y, max_y = np.min(wafer.y), np.max(wafer.y)
                wafer.width = int(max_x - min_x + 1) 
                wafer.height = int(max_y - min_y + 1)
            else:
                wafer.width = 0
                wafer.height = 0
        except KeyError as e:
            logger.error(f"在晶圆 {wafer_id} 提取基本数据时发生KeyError: {e} - 检查列名是否存在于 {wafer_df.columns.tolist()}")
            wafer.seq = getattr(wafer, 'seq', np.array([]))
            wafer.bin = getattr(wafer, 'bin', np.array([]))
            wafer.x = getattr(wafer, 'x', np.array([]))
            wafer.y = getattr(wafer, 'y', np.array([]))
            wafer.width = 0
            wafer.height = 0
        except Exception as e:
            logger.error(f"在晶圆 {wafer_id} 提取基本数据时发生未知错误: {e}")
            if not hasattr(wafer, 'seq') or wafer.seq is None: wafer.seq = np.array([])
            if not hasattr(wafer, 'bin') or wafer.bin is None: wafer.bin = np.array([])
            if not hasattr(wafer, 'x') or wafer.x is None: wafer.x = np.array([])
            if not hasattr(wafer, 'y') or wafer.y is None: wafer.y = np.array([])
            wafer.width = 0
            wafer.height = 0
        
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
        
        # 添加No.U列，默认为1
        if 'No.U' not in param_data:
            param_data['No.U'] = np.ones(len(wafer_df))
        
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