# Python CP MEX 格式数据采集 (`MEX格式数据采集.py`)

该 Python 模块 (`MEX格式数据采集.py`) 旨在复现 VBA 版本中 `MEX格式数据采集.bas` 模块的功能，用于读取和解析特定格式（称为 "MEX" 格式）的 CP 测试数据文件（通常是 Excel 的 `.xls` 或 `.xlsx` 格式）。

## MEX 文件格式假设

根据 VBA 源码分析，脚本假设 MEX 格式的 Excel 文件具有以下结构特点：

*   **文件类型**: Excel (`.xls`, `.xlsx`)。
*   **数据工作表**: 假设数据存在于 Excel 文件中的某个工作表（通常可能是第一个，或者需要指定）。
*   **元数据行**: 文件包含特定的行用于定义参数信息：
    *   行 12 (`USER_ITEM_ROW`): 参数的用户定义名称。
    *   行 11 (`STD_ITEM_ROW`): 标准项目名称，其中单位信息通常包含在方括号 `[]` 内。
    *   行 13 (`UPPER_ROW`): 规格上限。
    *   行 14 (`LOWER_ROW`): 规格下限。
    *   行 15-20 (`COND_START_ROW` 到 `COND_END_ROW`): 参数的测试条件。
*   **固定单元格**: 单元格 (5, 3) (第5行，C列) 包含产品名称。
*   **数据块**: 测试数据从行 27 (`DATA_START_ROW`) 开始，直到文件的末尾。
*   **固定列**: 数据块中存在固定的列用于存储基本信息：
    *   列 1 (`SEQ_COL`): 芯片序号。
    *   列 2 (`WAFER_COL`): 晶圆 ID (VBA 代码似乎假设每个文件/工作表对应一个晶圆)。
    *   列 3 (`X_COL`): 芯片 X 坐标。
    *   列 4 (`Y_COL`): 芯片 Y 坐标。
    *   列 5 (`BIN_COL`): 芯片 Bin 值。
    *   参数数据从列 8 (`PARAM_START_COL`) 开始。
*   **特殊值**: 字符串 " ----" (前后可能有空格) 会被视为空值或 NaN。
*   **单位转换**: VBA 脚本中使用了 `ChangeWithUnit`，意味着可能需要进行单位转换（基于从标准项目行提取的单位）。

## Python 实现 (`MEXReader` 类)

Python 版本将使用 `pandas` 库的 `read_excel` 函数来读取 Excel 数据，并结合自定义逻辑来解析元数据和测试数据。

```python
import pandas as pd
import numpy as np
import re
import logging
from typing import List, Tuple, Optional, Dict, Union

# (假设 CPLot, CPWafer, CPParameter 类已从 数据类型定义.py 导入)
# from .数据类型定义 import CPLot, CPWafer, CPParameter
# (假设辅助函数已从 通用工具函数.py 导入)
# from .通用工具函数 import ShowInfo, change_to_unique_name, get_unit_multiplier

logger = logging.getLogger(__name__)
# (建议配置 logger)

class MEXReader:
    # --- 常量定义 (从 VBA 移植, 0-based index) ---
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
        # ... (类似 CWReader) ...
        self.file_paths = file_paths
        self.pass_bin = pass_bin
        self.lot = None
        self.param_name_dict = {} # 用于生成唯一参数 ID
        self.param_pos_map: Dict[int, int] = {} # 列索引到参数列表索引的映射

    def read(self) -> CPLot:
        # ... (类似 CWReader) ...
        # 1. 初始化 CPLot 对象
        # 2. 遍历 file_paths
        # 3. 对每个文件调用 _extract_from_file
        # 4. 合并数据
        # 5. 返回 lot
        pass

    def _extract_from_file(self, file_path: str):
        # ... 实现单个文件提取逻辑 ...
        # 1. 使用 pandas.read_excel 读取 (可能需要指定 sheet_name=None 读取所有)
        # 2. 处理 " ----" 替换为空值
        # 3. 遍历工作表 (如果读取了多个)
        # 4. 对每个工作表:
        #    a. 如果是第一次处理 (lot.param_count == 0):
        #       - 调用 _add_param_info 解析参数
        #    b. 调用 _add_wafer_info 解析晶圆数据
        pass

    def _add_param_info(self, df: pd.DataFrame):
        # ... 实现参数解析逻辑 ...
        # 1. 遍历 PARAM_START_COL_IDX 之后的列
        # 2. 获取 USER_ITEM_ROW_IDX 的参数名，跳过空值和 "Dischage Time"
        # 3. 生成唯一 ID
        # 4. 从 STD_ITEM_ROW_IDX 提取单位 (使用 _split_unit_mex)
        # 5. 读取上限 (UPPER_ROW_IDX) 和下限 (LOWER_ROW_IDX)
        # 6. 可能需要进行单位转换后存储 SL, SU
        # 7. 提取测试条件
        # 8. 创建 CPParameter 对象并添加到 self.lot.params
        # 9. 记录参数列索引映射
        # 10. 从固定单元格读取 Lot Product 名称
        pass

    def _split_unit_mex(self, std_item_str: str) -> Optional[str]:
        # ... 实现从方括号提取单位的逻辑 ...
        # 对应 VBA SplitContentInPairChar(StdItem, "[]")
        match = re.search(r'\\\[(.*?)\\\]', str(std_item_str))
        return match.group(1).strip() if match else None

    def _add_wafer_info(self, df: pd.DataFrame):
        # ... 实现晶圆数据解析逻辑 ...
        # 1. 确定数据行数 (从 DATA_START_ROW_IDX 到末尾)
        # 2. 从 WAFER_COL_IDX 读取 Wafer ID (假设该列值相同)
        # 3. 提取 Seq, Bin, X, Y 列数据 (转为 NumPy)
        # 4. 创建 CPWafer 对象
        # 5. 提取各参数列的原始数据
        # 6. (注意: MEX 的 VBA 代码似乎没有进行单位转换，直接获取数据)
        # 7. 将数据存入 Wafer 的 chip_data (Pandas DataFrame)
        # 8. 将 Wafer 对象添加到 self.lot.wafers
        pass
```

## 主要挑战与实现细节

*   **Excel 文件读取**: 需要处理 `.xls` 和 `.xlsx` 格式，并可能需要处理多个工作表的情况。
*   **单位提取**: 从标准项目行中稳健地提取 `[]` 内的单位。
*   **单位转换 (确认)**: VBA 代码在读取 SL/SU 时调用了 `ChangeWithUnit`，但在读取 `ChipDatas` 时似乎没有。需要确认 Python 版本是否需要在读取参数数据时也进行转换。
*   **错误处理**: 处理文件读取错误、工作表缺失、格式不匹配等。

该 Python 实现旨在提供 MEX 格式数据的读取功能，保持与 VBA 脚本的逻辑一致性，同时利用 `pandas` 提高效率和灵活性。 