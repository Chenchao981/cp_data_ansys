"""
CW 格式数据读取器，用于读取和解析 CW 格式的 CP 测试数据文件 (.csv)。
"""
import os
import pandas as pd
import numpy as np
import re
import logging
from typing import List, Tuple, Optional, Dict, Union
import io

# 假设这些类和函数在同一目录下或已正确安装
from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter
from cp_data_processor.readers.base_reader import BaseReader
# from cp_data_processor.utils.common_utils import ShowInfo # 假设 ShowInfo 在这里

logger = logging.getLogger(__name__)

def get_unit_multiplier(unit_str: Optional[str]) -> float:
    """根据单位字符串（如 'mV', 'uA', 'kOhm'）返回乘以该单位值得到标准单位值的系数。"""
    if not unit_str or not isinstance(unit_str, str):
        return 1.0

    unit_str = unit_str.strip().lower()
    if not unit_str:
        return 1.0

    prefix_map = {
        'f': 1e-15, # femto
        'p': 1e-12, # pico
        'n': 1e-9,  # nano
        'u': 1e-6,  # micro
        'μ': 1e-6,  # micro (alternative)
        'm': 1e-3,  # milli
        'k': 1e3,   # kilo
        'meg': 1e6, # mega (VBA might use Meg)
        'g': 1e9,   # giga
    }

    # 检查是否有已知前缀
    for prefix, multiplier in prefix_map.items():
        # 检查单位是否以该前缀开头 (例如 'mv', 'ua')
        # 或者前缀后面直接跟基本单位 ('kohm')
        # 需要处理 'megohm' 这类情况
        if unit_str.startswith(prefix):
             # 确保不是基本单位的一部分 (例如 'm' in 'ohm')
             # 简单的检查：前缀后面是否有字母（基本单位）
            if len(unit_str) > len(prefix) and unit_str[len(prefix):].isalpha():
                 return multiplier
            # 处理 'm', 'k' 等可能单独出现的情况，如果后面没有单位，也认为有效
            elif len(unit_str) == len(prefix):
                return multiplier

    # 如果没有找到已知前缀，默认为 1
    return 1.0


class CWReader(BaseReader):
    """
    CW 格式 CP 数据读取器。
    CW 格式通常是 CSV 文件，具有特定的元数据行和数据结构。
    """
    # --- 类常量 (0-based index) ---
    PARAM_START_COL_IDX = 10 # 列 11
    USER_ITEM_ROW_IDX = 14   # 行 15
    LIMIT_ROW_IDX = 15       # 行 16
    COND_START_ROW_IDX = 16  # 行 17
    COND_END_ROW_IDX = 17    # 行 18
    DATA_START_ROW_IDX = 29  # 行 30 (标记 WAFER: 的行)

    SEQ_COL_IDX = 0          # 列 1
    BIN_COL_IDX = 1          # 列 2
    X_COL_IDX = 2            # 列 3
    Y_COL_IDX = 4            # 列 5
    WAFER_ID_IN_MW_COL_IDX = 1 # 多晶圆格式中 WaferID 所在列 (B列)
    CHIP_COUNT_IN_MW_COL_IDX = 2 # 多晶圆格式中 ChipCount 所在列 (C列)

    def __init__(self, file_paths: Union[str, List[str]], pass_bin: int = 1):
        super().__init__(file_paths, pass_bin)
        self.param_pos_map: Dict[int, int] = {} # Map from DataFrame column index to parameter index in lot.params
        self.param_name_dict: Dict[str, int] = {} # For generating unique param IDs
        # self.show_info = ShowInfo()

    def read(self) -> CPLot:
        lot_id = self.extract_lot_id(self.file_paths[0]) if self.file_paths else "UnknownLot"
        self.lot = CPLot(lot_id=lot_id, pass_bin=self.pass_bin)

        for file_path in self.file_paths:
            self._extract_from_file(file_path, self.lot)

        self.lot.update_counts()
        self.lot.combine_data_from_wafers()
        return self.lot

    def _extract_from_file(self, file_path: str, lot: CPLot) -> None:
        file_basename = os.path.basename(file_path)
        logger.info(f"开始处理 CW 文件: {file_basename}")
        try:
            # 尝试不同的编码读取 CSV
            df = None
            encodings = ['utf-8', 'gbk', 'latin1']
            for enc in encodings:
                try:
                    # 直接传递文件路径给 read_csv
                    # 使用 header=None 读取所有行，包括元数据
                    # 使用 na_values 替换 Untested
                    df = pd.read_csv(
                        file_path,
                        header=None,
                        encoding=enc,
                        sep=None, # 自动检测分隔符
                        engine='python',
                        skip_blank_lines=False,
                        na_values=['Untested']
                    )
                    logger.info(f"成功使用 {enc} 解码读取 CSV 文件: {file_basename}")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"使用 {enc} 读取时发生错误: {e}")
                    continue # 尝试下一种编码

            if df is None:
                logger.error(f"无法使用支持的编码读取或解析文件: {file_basename}")
                return

            # 将所有列强制转换为字符串以便处理元数据行
            df = df.astype(str)

            # --- 判断单晶圆 (SW) 或多晶圆 (MW) 格式 ---
            wafer_start_rows = df[df.iloc[:, 0].astype(str).str.strip() == 'WAFER:'].index.tolist()

            is_multi_wafer = len(wafer_start_rows) > 0
            logger.info(f"文件格式检测: {'多晶圆 (MW)' if is_multi_wafer else '单晶圆 (SW)'}")

            # --- 添加参数信息 (仅首次处理或为空时) ---
            if lot.param_count == 0:
                self._add_param_info(df, is_multi_wafer, lot, file_basename)
                if lot.param_count == 0:
                    logger.error(f"未能从文件 {file_basename} 提取任何参数信息。")
                    return

            # --- 添加晶圆信息 ---
            if is_multi_wafer:
                for start_row_idx in wafer_start_rows:
                    self._add_wafer_info(df, start_row_idx, lot, file_path, is_multi_wafer)
            else:
                # 单晶圆格式，假设数据从 DATA_START_ROW_IDX 开始标记
                # 需要找到一个可靠的方式定位单晶圆数据起始，这里暂时使用VBA的常量
                # 但更好的方法是寻找数据块的模式
                # 尝试使用VBA常量，如果失败则可能需要更鲁棒的查找
                potential_start_row = self.DATA_START_ROW_IDX
                if potential_start_row < len(df):
                     # 检查该行是否有预期内容，例如C列（索引2）是数字
                     chip_count_val = df.iloc[potential_start_row, self.CHIP_COUNT_IN_MW_COL_IDX]
                     # 使用 .notna() 检查非空，并确保是数字字符串
                     if pd.notna(chip_count_val) and str(chip_count_val).strip().isdigit():
                         self._add_wafer_info(df, potential_start_row, lot, file_path, is_multi_wafer)
                     else:
                         logger.warning(f"单晶圆文件的默认起始行 {potential_start_row+1} 未找到有效芯片数，尝试自动查找...")
                         # 尝试查找包含数字的行作为潜在起始行
                         found = False
                         for idx in range(len(df)):
                            cc_val = df.iloc[idx, self.CHIP_COUNT_IN_MW_COL_IDX]
                            # 确保值非空、是数字字符串且大于0
                            if pd.notna(cc_val) and str(cc_val).strip().isdigit() and int(str(cc_val).strip()) > 0:
                                logger.info(f"在行 {idx+1} 找到可能的芯片数，作为数据起始标记行。")
                                self._add_wafer_info(df, idx, lot, file_path, is_multi_wafer)
                                found = True
                                break
                         if not found:
                            logger.error(f"在单晶圆文件 {file_basename} 中无法自动定位数据起始行。")
                else:
                     logger.error(f"文件 {file_basename} 行数不足，无法找到数据起始行。")


        except pd.errors.EmptyDataError:
            logger.error(f"文件为空或无法解析: {file_path}")
        except Exception as e:
            logger.exception(f"处理文件 {file_path} 时发生意外错误: {str(e)}")

    def _get_value_safe(self, df: pd.DataFrame, row: int, col: int) -> str:
        """安全地获取 DataFrame 中的值，处理越界情况"""
        try:
            if 0 <= row < df.shape[0] and 0 <= col < df.shape[1]:
                val = df.iloc[row, col]
                return str(val).strip() if pd.notna(val) else ""
            return ""
        except IndexError:
            return ""

    def _add_param_info(self, df: pd.DataFrame, is_multi_wafer: bool, lot: CPLot, filename: str) -> None:
        logger.info("开始提取参数信息...")
        self.param_pos_map = {}
        params = []
        param_col_indices = [] # Store original df column indices for params

        if self.USER_ITEM_ROW_IDX >= df.shape[0]:
            logger.error(f"用户参数行 ({self.USER_ITEM_ROW_IDX + 1}) 超出文件范围。")
            return

        for col_idx in range(self.PARAM_START_COL_IDX, df.shape[1]):
            param_name = self._get_value_safe(df, self.USER_ITEM_ROW_IDX, col_idx)
            param_name_upper = param_name.upper()

            # 跳过 SAME 和空名称
            if param_name_upper == "SAME" or not param_name:
                continue

            param_index = len(params)
            self.param_pos_map[col_idx] = param_index
            param_col_indices.append(col_idx)

            # 提取显示名、组名，生成唯一 ID
            display_name = param_name
            group_name = param_name
            unique_id = self._get_unique_name(group_name, self.param_name_dict)

            # 解析规格和单位
            sl, su, unit = self._parse_limit_and_unit(df, col_idx)

            # 提取测试条件
            test_cond = []
            for cond_row_idx in range(self.COND_START_ROW_IDX, self.COND_END_ROW_IDX + 1):
                cond = self._get_value_safe(df, cond_row_idx, col_idx)
                test_cond.append(cond)

            param = CPParameter(
                id=unique_id,
                group=group_name,
                display_name=display_name,
                unit=unit,
                sl=sl,
                su=su,
                test_cond=test_cond
            )
            params.append(param)

        lot.params = params
        lot.param_count = len(params)
        logger.info(f"成功提取 {lot.param_count} 个参数。")

        # 设置 Lot Product 名称
        if is_multi_wafer:
            lot.product = os.path.splitext(filename)[0] # 多晶圆时，产品名为文件名（无扩展名）
        else:
            # 单晶圆，尝试从文件名中按 "-" 分割提取第一部分
            base = os.path.splitext(filename)[0]
            parts = base.split('-')
            lot.product = parts[0] if parts else base

        logger.info(f"设置 Lot Product 为: {lot.product}")

    def _parse_limit_and_unit(self, df: pd.DataFrame, col_idx: int) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        sl, su, unit = None, None, None
        limit_str = self._get_value_safe(df, self.LIMIT_ROW_IDX, col_idx)

        if not limit_str:
            return sl, su, unit

        # 尝试从末尾提取单位 (简单方式，可能不完美)
        # 改进正则以匹配字母或希腊字母 (μ)
        match_unit = re.search(r"([a-zA-Zμ]+)$", limit_str)
        value_str = limit_str # 默认整个字符串都是数值部分
        if match_unit:
            potential_unit = match_unit.group(1)
            # 检查是否是已知基本单位或以已知基本单位结尾 (允许前缀)
            base_units = ['v', 'a', 'ohm', 'hz', 'f', 's']
            is_known_unit = False
            for base_unit in base_units:
                if potential_unit.lower().endswith(base_unit):
                    is_known_unit = True
                    break
            # 或者单位本身就是基本单位
            if potential_unit.lower() in base_units:
                 is_known_unit = True

            if is_known_unit:
                unit = potential_unit
                # 尝试去除单位获取数值部分
                value_str = limit_str[:-len(unit)].strip()
            # else: unit 保持 None, value_str 保持 limit_str

        try:
            limit_val = float(value_str)
        except ValueError:
            logger.warning(f"无法将限制值 '{value_str}' (来自 '{limit_str}') 转换为数字，列索引 {col_idx}")
            limit_val = None

        if limit_val is not None:
            # 检查下一列是否为 SAME
            next_item_col_idx = col_idx + 2 # VBA逻辑是隔一列
            next_item_name = self._get_value_safe(df, self.USER_ITEM_ROW_IDX, next_item_col_idx)
            is_next_same = (next_item_name.upper() == "SAME")

            if is_next_same:
                # 当前是 SL
                sl = limit_val
                # 读取下一列的 SU
                su_str = self._get_value_safe(df, self.LIMIT_ROW_IDX, next_item_col_idx)
                if su_str:
                    # 提取 SU 的值，单位应与 SL 相同
                    su_value_str = su_str
                    if unit and su_str.lower().endswith(unit.lower()): # 比较小写
                         su_value_str = su_str[:-len(unit)].strip()
                    try:
                        su = float(su_value_str)
                    except ValueError:
                         logger.warning(f"无法将 SAME 对的上限值 '{su_value_str}' (来自 '{su_str}') 转换为数字，列索引 {next_item_col_idx}")
            else:
                # 不是 SAME 对，根据参数名猜测
                param_name = self._get_value_safe(df, self.USER_ITEM_ROW_IDX, col_idx)
                # VBA: If UCase(Left(Param, 1)) = "B" Then "ExceptHi" Else "ExceptLow"
                if param_name.upper().startswith("B"):
                    # 猜测是望小特性 (upper spec)，当前值是 SU
                    su = limit_val
                else:
                    # 猜测是望大特性 (lower spec)，当前值是 SL
                    sl = limit_val
        # 将 SL/SU 转换为基础单位存储
        final_sl, final_su = None, None
        multiplier = get_unit_multiplier(unit)
        if sl is not None:
            final_sl = sl * multiplier
        if su is not None:
            final_su = su * multiplier
        logger.debug(f"Param col {col_idx}: Limit='{limit_str}', Val='{limit_val}', Unit='{unit}', SL={final_sl}, SU={final_su}")

        return final_sl, final_su, unit # 返回转换后的 SL/SU 和原始单位

    def _add_wafer_info(self, df: pd.DataFrame, wafer_start_row_idx: int, lot: CPLot, file_path: str, is_multi_wafer: bool) -> None:

        try:
            # --- 确定 Wafer ID --- 
            if is_multi_wafer:
                wafer_id_str = self._get_value_safe(df, wafer_start_row_idx, self.WAFER_ID_IN_MW_COL_IDX)
                if not wafer_id_str:
                    logger.warning(f"在多晶圆文件 {os.path.basename(file_path)} 的行 {wafer_start_row_idx + 1} 未找到有效的 Wafer ID，跳过此晶圆。")
                    return
                wafer_id = wafer_id_str
            else:
                # 单晶圆，尝试从文件名提取（去除扩展名，取最后一个 "-" 后的部分）
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                parts = base_name.split('-')
                wafer_id = parts[-1] if len(parts) > 1 else base_name
                logger.info(f"单晶圆格式，从文件名推断 Wafer ID: {wafer_id}")

            # --- 读取 Chip Count --- 
            chip_count_str = self._get_value_safe(df, wafer_start_row_idx, self.CHIP_COUNT_IN_MW_COL_IDX)
            try:
                chip_count = int(chip_count_str)
                if chip_count <= 0:
                    logger.warning(f"晶圆 {wafer_id} (行 {wafer_start_row_idx + 1}) 的芯片数无效 ({chip_count})，跳过。")
                    return
            except (ValueError, TypeError):
                logger.warning(f"无法将晶圆 {wafer_id} (行 {wafer_start_row_idx + 1}) 的芯片数 '{chip_count_str}' 转换为整数，跳过。")
                return

            # --- 确定实际数据范围 --- 
            # VBA: DataStartRow = myStartRow + 3
            actual_data_start_row_idx = wafer_start_row_idx + 3
            actual_data_end_row_idx = actual_data_start_row_idx + chip_count # End index is exclusive for slicing

            if actual_data_start_row_idx >= df.shape[0] or actual_data_end_row_idx > df.shape[0]:
                logger.error(f"晶圆 {wafer_id} 的数据行范围 [{actual_data_start_row_idx + 1}:{actual_data_end_row_idx + 1}] 超出文件界限 ({df.shape[0]}行)，跳过。")
                return

            logger.info(f"开始处理晶圆 {wafer_id}，芯片数: {chip_count}，数据范围: 行 {actual_data_start_row_idx + 1} 到 {actual_data_end_row_idx}")

            # --- 提取基础列数据 --- 
            try:
                seq_raw = df.iloc[actual_data_start_row_idx:actual_data_end_row_idx, self.SEQ_COL_IDX].values
                bin_raw = df.iloc[actual_data_start_row_idx:actual_data_end_row_idx, self.BIN_COL_IDX].values
                x_raw = df.iloc[actual_data_start_row_idx:actual_data_end_row_idx, self.X_COL_IDX].values
                y_raw = df.iloc[actual_data_start_row_idx:actual_data_end_row_idx, self.Y_COL_IDX].values
                
                # 转换为数值类型，无法转换的设为 NaN
                seq = pd.to_numeric(seq_raw, errors='coerce')
                bin_val = pd.to_numeric(bin_raw, errors='coerce')
                x = pd.to_numeric(x_raw, errors='coerce')
                y = pd.to_numeric(y_raw, errors='coerce')
                
            except Exception as e:
                 logger.error(f"提取晶圆 {wafer_id} 的基础列 (Seq, Bin, X, Y) 数据时出错: {e}，跳过此晶圆。")
                 return

            # --- 提取参数数据并进行单位转换 --- 
            param_data = {}
            valid_param_count = 0
            for df_col_idx, param_idx in self.param_pos_map.items():
                if param_idx < len(lot.params):
                    param = lot.params[param_idx]
                    param_id = param.id
                    unit = param.unit # 参数的原始单位（可能带前缀）
                    
                    try:
                        # 提取原始参数数据列
                        raw_values = df.iloc[actual_data_start_row_idx:actual_data_end_row_idx, df_col_idx].values
                        
                        # 转换为数值，无法转换的为 NaN
                        numeric_values = pd.to_numeric(raw_values, errors='coerce')
                        
                        # 单位转换：将读取到的值转换为基础单位 (V, A, Ohm...)
                        multiplier = get_unit_multiplier(unit)
                        if multiplier != 1.0:
                            converted_values = numeric_values * multiplier
                            logger.debug(f"参数 {param_id} (单位 {unit}) 应用转换系数 {multiplier}")
                        else:
                            converted_values = numeric_values
                            
                        param_data[param_id] = converted_values
                        valid_param_count += 1
                    except Exception as e:
                         logger.warning(f"处理晶圆 {wafer_id} 的参数 {param_id} (列 {df_col_idx + 1}) 数据时出错: {e}。该参数数据将包含 NaN。")
                         # 确保即使出错，列也存在，填充 NaN
                         param_data[param_id] = np.full(chip_count, np.nan)
                else:
                     logger.warning(f"参数映射错误：DataFrame 列索引 {df_col_idx} 对应的参数索引 {param_idx} 超出范围。")

            if valid_param_count == 0:
                logger.warning(f"晶圆 {wafer_id} 未能成功提取任何有效的参数数据，跳过此晶圆。")
                return

            # --- 创建 CPWafer 对象 --- 
            chip_data_df = pd.DataFrame(param_data)

            wafer = CPWafer(
                wafer_id=wafer_id,
                file_path=file_path,
                chip_count=chip_count, 
                seq=seq,
                x=x,
                y=y,
                bin=bin_val,
                chip_data=chip_data_df
            )

            lot.wafers.append(wafer)
            logger.info(f"成功添加晶圆 {wafer_id} 到 Lot。")

        except Exception as e:
            logger.exception(f"处理晶圆数据块 (起始行 {wafer_start_row_idx + 1}) 时发生意外错误: {e}")

    def _get_unique_name(self, base_name: str, name_dict: Dict[str, int]) -> str:
        """确保名称唯一性，如果重复则添加数字后缀"""
        if base_name not in name_dict:
            name_dict[base_name] = 1
            return base_name
        
        count = name_dict[base_name] + 1
        name_dict[base_name] = count
        # VBA 的 Change2UniqueName 是直接加数字，这里也保持一致
        return f"{base_name}{count}" 