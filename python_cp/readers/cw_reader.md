# Python CP CW 格式数据采集 (`CW格式数据采集.py`)

该 Python 模块 (`CW格式数据采集.py`) 旨在复现 VBA 版本中 `CW格式数据采集.bas` 模块的功能，用于读取和解析特定格式（称为 "CW" 格式）的 CP 测试数据文件（通常是 `.csv` 格式）。

## CW 文件格式假设

根据 VBA 源码分析，脚本假设 CW 格式的 CSV 文件具有以下结构特点：

*   **分隔符**: 虽然未明确指定，但 CSV 通常使用逗号分隔。
*   **元数据行**: 文件包含特定的行用于定义参数信息：
    *   行 15 (`USER_ITEM_ROW`): 参数的用户定义名称。
    *   行 16 (`LIMIT_ROW`): 参数的限制值和单位。单位通常是值的最后两个字符。
    *   行 17-18 (`COND_START_ROW` 到 `COND_END_ROW`): 参数的测试条件。
    *   *注意*: VBA 中的 `UNIT_RATE_ROW` (行 20) 是 VBA 脚本写入的，源文件中不应存在。
*   **数据块**: 测试数据从某一行开始（VBA 中是 `DATA_START_ROW` = 30），实际数据在该行后几行。
    *   芯片数量通常在数据块开始行的第 3 列。
    *   实际芯片数据从数据块开始行 + 3 行开始。
*   **固定列**: 存在固定的列用于存储基本信息：
    *   列 1 (`SEQ_COL`): 芯片序号。
    *   列 2 (`BIN_COL`): 芯片 Bin 值。
    *   列 3 (`X_COL`): 芯片 X 坐标。
    *   列 5 (`Y_COL`): 芯片 Y 坐标。
    *   参数数据从列 11 (`PARAM_START_COL`) 开始。
*   **特殊值**: "Untested" 值会被视为空值或 NaN。
*   **"SAME" 参数**: 如果 `USER_ITEM_ROW` 中某参数列的值为 "SAME"，则表示该列与前一参数共享信息（例如，形成上下限对）。
*   **单位转换**: VBA 脚本会在读取过程中进行单位转换，Python 版本也需要实现类似逻辑。
*   **单/多晶圆格式**: 存在两种变体：
    *   **单晶圆 (SW)**: 文件只包含一个晶圆的数据。晶圆 ID 通常从工作表名（或文件名）派生。
    *   **多晶圆 (MW)**: 文件包含多个晶圆的数据，每个晶圆块由 "WAFER:" 标记开始。晶圆 ID 从数据块内部读取。

## Python 实现 (`CWReader` 类)

Python 版本将使用 `pandas` 库来读取和处理 CSV 数据，并结合自定义逻辑来解析元数据和测试数据。

```python
import pandas as pd
import numpy as np
import re
import logging
from typing import List, Tuple, Optional, Dict

# (假设 CPLot, CPWafer, CPParameter 类已从 数据类型定义.py 导入)
# from .数据类型定义 import CPLot, CPWafer, CPParameter
# (假设辅助函数已从 通用工具函数.py 导入)
# from .通用工具函数 import ShowInfo, change_to_unique_name # (需要实现 change_to_unique_name)

logger = logging.getLogger(__name__)
# (建议配置 logger)

class CWReader:
    # --- 常量定义 (从 VBA 移植) ---
    PARAM_START_COL_IDX = 10 # 列 11 (0-based index)
    USER_ITEM_ROW_IDX = 14   # 行 15 (0-based index)
    LIMIT_ROW_IDX = 15       # 行 16
    COND_START_ROW_IDX = 16  # 行 17
    COND_END_ROW_IDX = 17    # 行 18
    DATA_START_ROW_IDX = 29  # 行 30

    SEQ_COL_IDX = 0          # 列 1
    BIN_COL_IDX = 1          # 列 2
    X_COL_IDX = 2            # 列 3
    Y_COL_IDX = 4            # 列 5

    def __init__(self, file_paths: List[str], pass_bin: int = 1):
        self.file_paths = file_paths
        self.pass_bin = pass_bin
        self.lot = None
        # self.show_info = ShowInfo() # 可选：用于信息提示
        self.param_name_dict = {} # 用于生成唯一参数 ID

    def read(self) -> CPLot:
        # ... 实现读取逻辑 ...
        # 1. 初始化 CPLot 对象
        # 2. 遍历 file_paths
        # 3. 对每个文件调用 _extract_from_file
        # 4. 合并数据 (如果需要 lot.combine_data_from_wafers())
        # 5. 返回 lot
        pass

    def _extract_from_file(self, file_path: str):
        # ... 实现单个文件提取逻辑 ...
        # 1. 使用 pandas 读取 CSV (处理编码, 替换 "Untested")
        # 2. 判断是单晶圆 (SW) 还是多晶圆 (MW) 格式
        #    - 查找 "WAFER:" 标记
        # 3. 如果是第一次处理文件 (lot.param_count == 0):
        #    - 调用 _add_param_info 解析参数
        # 4. 根据 SW/MW 调用 _add_wafer_info 解析晶圆数据
        pass

    def _add_param_info(self, df: pd.DataFrame, is_multi_wafer: bool):
        # ... 实现参数解析逻辑 ...
        # 1. 遍历 PARAM_START_COL_IDX 之后的列
        # 2. 获取 USER_ITEM_ROW_IDX 的参数名，跳过 "SAME" 和空值
        # 3. 生成唯一 ID (使用 self.param_name_dict)
        # 4. 调用 _parse_limit_and_unit 解析规格和单位
        # 5. 提取测试条件
        # 6. 创建 CPParameter 对象并添加到 self.lot.params
        # 7. 记录参数列索引映射 (类似 VBA 的 ParamPos)
        # 8. 设置 Lot Product 名称
        pass

    def _parse_limit_and_unit(self, df: pd.DataFrame, col_idx: int) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        # ... 实现规格和单位解析逻辑 ...
        # 1. 读取 LIMIT_ROW_IDX 的值
        # 2. 尝试提取末尾作为单位
        # 3. 检查下一列是否为 "SAME"
        # 4. 根据是否 "SAME" 和猜测的 QC 类型 ("B"开头) 设置 SL, SU
        pass

    def _add_wafer_info(self, df: pd.DataFrame, wafer_start_row_idx: int):
        # ... 实现晶圆数据解析逻辑 ...
        # 1. 确定 Wafer ID (根据 SW/MW)
        # 2. 读取 Chip Count
        # 3. 确定实际数据开始行
        # 4. 提取 Seq, Bin, X, Y 列数据 (转为 NumPy)
        # 5. 创建 CPWafer 对象
        # 6. 提取各参数列的原始数据
        # 7. 对每个参数应用单位换算 (需要 _get_unit_conversion_rate 函数)
        # 8. 将转换后的数据存入 Wafer 的 chip_data (Pandas DataFrame)
        # 9. 将 Wafer 对象添加到 self.lot.wafers
        pass

    def _get_unit_conversion_rate(self, unit: Optional[str]) -> float:
        # ... 实现单位换算率计算 (类似 VBA CalRate / ChangeWithUnit) ...
        # 返回乘以原始值得到标准单位值的系数
        pass
```

## 主要挑战与实现细节

*   **文件结构变体**: 需要能稳健地处理单晶圆和多晶圆两种格式。
*   **"SAME" 参数**: 处理上下限配对的逻辑需要准确实现。
*   **单位转换**: 需要正确解析单位并实现与 VBA 兼容的转换逻辑（例如，将 mV, uA 等转换为 V, A）。
*   **错误处理**: 添加对文件读取错误、格式不匹配、数据转换失败等的处理。
*   **性能**: 对于非常大的 CSV 文件，需要考虑 `pandas` 读取和处理的性能优化。

该 Python 实现旨在提供一个功能上等同于 VBA 脚本的数据读取器，同时利用 Python 库的优势提高代码的可读性、可维护性和性能。 