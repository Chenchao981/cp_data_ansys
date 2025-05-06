"""
MEX 格式数据读取器，用于读取和解析 MEX 格式的 CP 测试数据文件 (.xls, .xlsx)。
"""
import os
import pandas as pd
import numpy as np
import re
import logging
from typing import List, Tuple, Optional, Dict, Union

# 假设这些类和函数在同一目录下或已正确安装
# 使用相对导入（如果这些模块在同一包内）
# from ..data_models.cp_data import CPLot, CPWafer, CPParameter
# from .base_reader import BaseReader
# from ..utils.unit_conversion import get_unit_multiplier
# from ..utils.common_utils import ShowInfo

# 临时的占位符，你需要确保这些类和函数能够被正确导入
from cp_data_processor.data_models.cp_data import CPLot, CPWafer, CPParameter
from cp_data_processor.readers.base_reader import BaseReader

# 假设这个函数存在
def get_unit_multiplier(unit: Optional[str]) -> float:
    # 这是一个占位符实现，你需要替换为实际的单位转换逻辑
    if unit and 'm' in unit.lower(): return 0.001
    if unit and 'u' in unit.lower(): return 1e-6
    if unit and 'n' in unit.lower(): return 1e-9
    if unit and 'k' in unit.lower(): return 1000
    return 1.0

logger = logging.getLogger(__name__)

class MEXReader(BaseReader):
    """
    MEX 格式 CP 数据读取器。
    MEX 格式通常是 Excel 文件，具有特定的元数据行和数据结构。
    """
    # --- 类常量 (0-based index) ---
    PARAM_START_COL_IDX = 7  # 列 8
    STD_ITEM_ROW_IDX = 10    # 行 11
    USER_ITEM_ROW_IDX = 11   # 行 12
    UPPER_ROW_IDX = 12       # 行 13
    LOWER_ROW_IDX = 13       # 行 14
    COND_START_ROW_IDX = 14  # 行 15
    COND_END_ROW_IDX = 19    # 行 20
    PRODUCT_ROW_IDX = 4      # 行 5
    PRODUCT_COL_IDX = 2      # 列 3

    DATA_START_ROW_IDX = 26  # 行 27
    SEQ_COL_IDX = 0          # 列 1
    WAFER_COL_IDX = 1        # 列 2
    X_COL_IDX = 2            # 列 3
    Y_COL_IDX = 3            # 列 4
    BIN_COL_IDX = 4          # 列 5

    def __init__(self, file_paths: Union[str, List[str]], pass_bin: int = 1):
        super().__init__(file_paths, pass_bin)
        self.param_pos_map: Dict[int, int] = {}
        self.param_name_dict: Dict[str, int] = {}

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
        logger.info(f"开始处理 MEX 文件: {file_basename}")
        try:
            excel_data = pd.read_excel(file_path, sheet_name=None, header=None, engine='openpyxl')

            first_sheet = True
            for sheet_name, df_orig in excel_data.items():
                logger.info(f"处理工作表: {sheet_name}")
                df = df_orig.copy()
                df.replace(r"^\s*----\s*$", np.nan, regex=True, inplace=True)

                if first_sheet and lot.param_count == 0:
                    self._add_param_info(df, lot)
                    if lot.param_count == 0:
                        logger.error(f"未能从文件 {file_basename} (工作表: {sheet_name}) 提取参数。停止处理此文件。")
                        return
                    first_sheet = False
                elif lot.param_count == 0:
                     self._add_param_info(df, lot)
                     if lot.param_count == 0:
                        logger.warning(f"工作表 {sheet_name} 也未能提取参数。跳过。")
                        continue

                self._add_wafer_info(df, sheet_name, file_path, lot)

        except FileNotFoundError:
            logger.error(f"文件未找到: {file_path}")
        except Exception as e:
            logger.exception(f"处理 Excel 文件 {file_path} 时出错: {str(e)}")

    def _get_value_safe(self, df: pd.DataFrame, row: int, col: int) -> str:
        try:
            if 0 <= row < df.shape[0] and 0 <= col < df.shape[1]:
                val = df.iloc[row, col]
                return str(val).strip() if pd.notna(val) and val is not None else ""
            return ""
        except IndexError:
            return ""

    def _add_param_info(self, df: pd.DataFrame, lot: CPLot) -> None:
        logger.info("开始提取参数信息...")
        self.param_pos_map = {}
        params = []

        if self.USER_ITEM_ROW_IDX >= df.shape[0]:
            logger.error(f"用户参数行 ({self.USER_ITEM_ROW_IDX + 1}) 超出范围。")
            return

        for col_idx in range(self.PARAM_START_COL_IDX, df.shape[1]):
            param_name = self._get_value_safe(df, self.USER_ITEM_ROW_IDX, col_idx)
            if not param_name or param_name.lower() == "dischage time":
                continue

            param_index = len(params)
            self.param_pos_map[col_idx] = param_index

            display_name = param_name
            group_name = param_name
            unique_id = self._get_unique_name(group_name, self.param_name_dict)

            std_item_str = self._get_value_safe(df, self.STD_ITEM_ROW_IDX, col_idx)
            unit = self._split_unit_mex(std_item_str)

            lower_str = self._get_value_safe(df, self.LOWER_ROW_IDX, col_idx)
            upper_str = self._get_value_safe(df, self.UPPER_ROW_IDX, col_idx)
            sl_orig = pd.to_numeric(lower_str, errors='coerce')
            su_orig = pd.to_numeric(upper_str, errors='coerce')

            sl, su = None, None
            multiplier = get_unit_multiplier(unit)
            if pd.notna(sl_orig):
                # VBA的ChangeWithUnit是 value / rate，Rate是标准到目标的乘数
                # get_unit_multiplier 是目标到标准的乘数
                # 所以这里应该是 sl_orig * multiplier 转换到标准单位
                sl = sl_orig * multiplier
            if pd.notna(su_orig):
                su = su_orig * multiplier
            logger.debug(f"Param {unique_id}: Unit={unit}, SL_orig={sl_orig}, SU_orig={su_orig}, Multiplier={multiplier}, SL={sl}, SU={su}")

            test_cond = []
            for cond_row_idx in range(self.COND_START_ROW_IDX, self.COND_END_ROW_IDX + 1):
                cond = self._get_value_safe(df, cond_row_idx, col_idx)
                test_cond.append(cond)

            param = CPParameter(
                id=unique_id, group=group_name, display_name=display_name,
                unit=unit, sl=sl, su=su, test_cond=test_cond
            )
            params.append(param)

        lot.params = params
        lot.param_count = len(params)
        logger.info(f"成功提取 {lot.param_count} 个参数。")

        lot.product = self._get_value_safe(df, self.PRODUCT_ROW_IDX, self.PRODUCT_COL_IDX)
        logger.info(f"设置 Lot Product 为: {lot.product}")

    def _split_unit_mex(self, std_item_str: str) -> Optional[str]:
        if not std_item_str or not isinstance(std_item_str, str):
            return None
        match = re.search(r'\[(.*?)\]', std_item_str)
        return match.group(1).strip() if match else None

    def _add_wafer_info(self, df: pd.DataFrame, sheet_name: str, file_path: str, lot: CPLot) -> None:
        try:
            data_rows = df.shape[0] - self.DATA_START_ROW_IDX
            if data_rows <= 0:
                logger.warning(f"工作表 {sheet_name} 数据行不足，跳过。")
                return
            actual_data_start_row_idx = self.DATA_START_ROW_IDX
            actual_data_end_row_idx = df.shape[0]

            wafer_id = self._get_value_safe(df, actual_data_start_row_idx, self.WAFER_COL_IDX)
            if not wafer_id:
                wafer_id = sheet_name
                logger.warning(f"工作表 {sheet_name} 未找到 Wafer ID，使用表名代替。")
            else:
                logger.info(f"从工作表 {sheet_name} 提取 Wafer ID: {wafer_id}")

            chip_count = data_rows
            logger.info(f"处理晶圆 {wafer_id} (表: {sheet_name})，芯片数: {chip_count}")

            try:
                seq_raw = df.iloc[actual_data_start_row_idx:actual_data_end_row_idx, self.SEQ_COL_IDX].values
                bin_raw = df.iloc[actual_data_start_row_idx:actual_data_end_row_idx, self.BIN_COL_IDX].values
                x_raw = df.iloc[actual_data_start_row_idx:actual_data_end_row_idx, self.X_COL_IDX].values
                y_raw = df.iloc[actual_data_start_row_idx:actual_data_end_row_idx, self.Y_COL_IDX].values
                seq = pd.to_numeric(seq_raw, errors='coerce')
                bin_val = pd.to_numeric(bin_raw, errors='coerce')
                x = pd.to_numeric(x_raw, errors='coerce')
                y = pd.to_numeric(y_raw, errors='coerce')
            except Exception as e:
                logger.error(f"提取晶圆 {wafer_id} 基础列数据时出错: {e}，跳过。")
                return

            param_data = {}
            valid_param_count = 0
            for df_col_idx, param_idx in self.param_pos_map.items():
                if param_idx < len(lot.params):
                    param = lot.params[param_idx]
                    param_id = param.id
                    try:
                        raw_values = df.iloc[actual_data_start_row_idx:actual_data_end_row_idx, df_col_idx].values
                        numeric_values = pd.to_numeric(raw_values, errors='coerce')
                        # MEX VBA 不转换 ChipData 单位
                        param_data[param_id] = numeric_values
                        valid_param_count += 1
                    except Exception as e:
                        logger.warning(f"处理晶圆 {wafer_id} 参数 {param_id} (列 {df_col_idx + 1}) 出错: {e}。填充 NaN。")
                        param_data[param_id] = np.full(chip_count, np.nan)
                else:
                    logger.warning(f"参数映射错误: 列 {df_col_idx} -> 参数 {param_idx}")

            if valid_param_count == 0:
                logger.warning(f"晶圆 {wafer_id} 未提取到有效参数数据，跳过。")
                return

            chip_data_df = pd.DataFrame(param_data)
            wafer = CPWafer(
                wafer_id=wafer_id, file_path=file_path, chip_count=chip_count,
                seq=seq, x=x, y=y, bin=bin_val, chip_data=chip_data_df
            )
            lot.wafers.append(wafer)
            logger.info(f"成功添加晶圆 {wafer_id} (表: {sheet_name}) 到 Lot。")

        except Exception as e:
            logger.exception(f"处理工作表 {sheet_name} (晶圆 {wafer_id}) 时意外出错: {e}")

    def _get_unique_name(self, base_name: str, name_dict: Dict[str, int]) -> str:
        if base_name not in name_dict:
            name_dict[base_name] = 1
            return base_name
        count = name_dict[base_name] + 1
        name_dict[base_name] = count
        return f"{base_name}{count}" 