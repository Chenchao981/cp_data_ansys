# Python CP 数据模型 (`数据类型定义.py`)

该 Python 模块 (`数据类型定义.py`) 定义了用于表示半导体 CP (Chip Probing) 测试数据的核心数据结构。这些结构是 VBA 版本中 `数据类型定义.bas` 模块内 `Type` 定义的 Python 实现，并进行了一些优化和调整以适应 Python 的编程范式和常用库（如 `pandas` 和 `numpy`）。

主要包含三个数据类：`CPParameter`, `CPWafer`, 和 `CPLot`。

## 1. `CPParameter` 类

对应 VBA 中的 `TestItem` 类型，用于存储单个测试参数的详细信息。

```python
from dataclasses import dataclass
from typing import List, Optional, Any

@dataclass
class CPParameter:
    """
    表示单个 CP 测试参数的信息。
    对应 VBA 中的 TestItem 类型。
    """
    id: str                     # 内部唯一标识符 (通常是参数名，可能包含后缀以保证唯一性)
    group: str                  # 参数的组别或原始名称 (通常与 id 相同或为其基础)
    display_name: str           # 用于在报告或图表中显示的名称
    unit: Optional[str] = None  # 参数的物理单位 (例如: 'V', 'A', 'Ohm')
    sl: Optional[float] = None  # 规格下限 (Specification Lower Limit)
    su: Optional[float] = None  # 规格上限 (Specification Upper Limit)
    test_cond: List[Any] = field(default_factory=list) # 测试条件列表 (具体内容格式取决于数据源)
```

**字段说明:**

*   `id`: 参数的唯一标识符，字符串类型。在 VBA 版本中，可能通过 `Change2UniqueName` 函数添加数字后缀来确保唯一性。
*   `group`: 参数所属的组别，字符串类型。通常是参数的原始名称。
*   `display_name`: 用于最终报告或图表展示的名称，字符串类型。
*   `unit`: 参数值的单位，可选的字符串类型。
*   `sl`: 参数的规格下限，可选的浮点数类型。
*   `su`: 参数的规格上限，可选的浮点数类型。
*   `test_cond`: 记录该参数测试时的相关条件，列表类型。列表中的元素类型可以是字符串、数字等，具体取决于原始数据格式。

**注意:** VBA `TestItem` 中的 `ScopeHi`, `ScopeLow`, `QualityCharacteristic` 字段在现有 VBA 代码中似乎未被积极使用，因此在 Python 版本中暂未包含，以保持简洁。

## 2. `CPWafer` 类

对应 VBA 中的 `CPWafer` 类型，用于存储单个晶圆的测试数据和元信息。

```python
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class CPWafer:
    """
    表示单个晶圆 (Wafer) 的测试数据。
    对应 VBA 中的 CPWafer 类型。
    """
    wafer_id: str                     # 晶圆编号 (例如: "Wafer01", "Slot3")
    file_path: Optional[str] = None   # 读取该晶圆数据的源文件路径 (Python新增字段)
    chip_count: int = 0               # 该晶圆上测试的芯片 (Die/Site) 总数
    seq: Optional[np.ndarray] = None  # 芯片测试序号 (1D NumPy 数组, int/float)
    x: Optional[np.ndarray] = None    # 芯片的 X 坐标 (1D NumPy 数组, int/float)
    y: Optional[np.ndarray] = None    # 芯片的 Y 坐标 (1D NumPy 数组, int/float)
    bin: Optional[np.ndarray] = None  # 芯片的 Bin 值 (1D NumPy 数组, int/float)
    chip_data: Optional[pd.DataFrame] = None # 存储参数测试数据的 Pandas DataFrame。
                                            # 行对应芯片 (Die/Site), 列对应参数 (`CPParameter.id`)。

    # ... (包含计算 width, height, param_count 的 @property 方法)

    # --- 新增方法 ---
    def get_bin_counts(self) -> pd.Series:
        """计算并返回该晶圆的 Bin 值统计 (每个 Bin 的数量)。"""
        # ... (方法实现) ...

    def calculate_yield(self, pass_bin_value: int = 1) -> Tuple[float, int, int]:
        """
        计算该晶圆的良率。
        Args:
            pass_bin_value: 定义为 Pass 的 Bin 值。
        Returns:
            元组 (良率, Pass 数量, Total 数量)。良率是 0 到 1 之间的小数。
            如果无法计算（如无 Bin 数据），返回 (0.0, 0, 0)。
        """
        # ... (方法实现) ...
```

**字段说明:**

*   `wafer_id`: 晶圆的唯一标识符，字符串类型。
*   `file_path`: （Python 新增）记录该晶圆数据来源的文件路径，可选字符串。
*   `chip_count`: 该晶圆上进行测试的芯片数量，整数。
*   `seq`: 存储每个芯片测试序号的一维 NumPy 数组，可选。数组元素通常为整数或浮点数。
*   `x`: 存储每个芯片 X 坐标的一维 NumPy 数组，可选。
*   `y`: 存储每个芯片 Y 坐标的一维 NumPy 数组，可选。
*   `bin`: 存储每个芯片 Bin 值的一维 NumPy 数组，可选。Bin 值通常表示芯片的测试结果分类（例如，1 代表 Pass）。
*   `chip_data`: 存储该晶圆所有芯片、所有参数测试结果的核心数据结构，使用 Pandas DataFrame。
    *   DataFrame 的**行**代表不同的芯片（Die/Site），可以通过 `seq` 或默认的整数索引。
    *   DataFrame 的**列**代表不同的测试参数，列名通常是 `CPParameter.id`。
    *   DataFrame 中的值为对应芯片、对应参数的测试数值（通常是浮点数，无效值用 `np.nan` 表示）。

**计算属性:**

*   `width`: 通过 `@property` 装饰器实现，根据 `x` 坐标计算晶圆的宽度。
*   `height`: 通过 `@property` 装饰器实现，根据 `y` 坐标计算晶圆的高度。
*   `param_count`: 通过 `@property` 装饰器实现，返回 `chip_data` 的列数，即参数数量。

**注意:** VBA `CPWafer` 中的 `SiteCount`, `MaxX`, `MinX`, `MaxY`, `MinY`, `Height`, `Width` (作为直接存储字段), `ParamCount` (作为直接存储字段), `Params`, `StatInfo`, `PassBin` 等字段在 Python 版本中进行了调整：
*   坐标范围和尺寸 (`MaxX`...`Width`) 可以根据 `x`, `y` 动态计算，通过 `@property` 提供访问。
*   `ParamCount` 也可以动态计算。
*   `Params` 信息通常在 `CPLot` 级别统一定义。
*   `StatInfo` 在 VBA 中未见使用，暂不包含。
*   `PassBin` 通常在 `CPLot` 级别定义。
*   核心数据 `ChipDatas` (VBA 中的多维数组) 被更强大的 `chip_data` (Pandas DataFrame) 替代。

## 3. `CPLot` 类

对应 VBA 中的 `CPLot` 类型，用于表示整个测试批次 (Lot) 的数据，包含一个或多个晶圆以及批次级别的元信息。

```python
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass
class CPLot:
    """
    表示整个 CP 测试批次 (Lot) 的数据。
    对应 VBA 中的 CPLot 类型。
    """
    lot_id: str                             # Lot 编号 (例如: "LOT12345")
    product: Optional[str] = None           # 产品名称
    pass_bin: int = 1                       # 定义 Pass Bin 的值 (默认值为 1)
    wafers: List[CPWafer] = field(default_factory=list) # 包含该 Lot 中所有 `CPWafer` 对象的列表
    params: List[CPParameter] = field(default_factory=list) # 包含该 Lot 所有参数 (`CPParameter` 对象) 的列表
    combined_data: Optional[pd.DataFrame] = None # (Python 新增) 合并所有 Wafer 数据的 Pandas DataFrame

    # ... (包含计算 wafer_count, param_count 的 @property 方法)
    # ... (包含 get_param_by_id, get_wafer_by_id, combine_data_from_wafers 等方法)

    # --- 新增方法 ---
    def calculate_lot_yield_summary(self) -> pd.DataFrame:
        """
        计算整个 Lot 的良率汇总表，结构类似于 VBA 宏输出到 "Yield" 表的结果。

        Returns:
            一个 Pandas DataFrame，包含以下列:
            - Wafer: 晶圆 ID (末尾可能带有 '#') 或 "All" (汇总行)。
            - Yield: 良率 (0.0 到 1.0 之间的小数)。
            - Total: 该晶圆/整个 Lot 的有效芯片总数 (排除了 Bin 为空的情况)。
            - Pass: Pass Bin (由 CPLot.pass_bin 定义) 的数量。
            - BinX, BinY, ...: 其他每个唯一 Bin 值对应的数量列。
        """
        # ... (方法实现) ...
```

**字段说明:**

*   `lot_id`: 整个测试批次的唯一标识符，字符串类型。
*   `product`: 该批次测试的产品名称，可选字符串。
*   `pass_bin`: 定义判定为 "Pass" 的 Bin 值，整数类型，默认为 1。
*   `wafers`: 一个列表，包含该 Lot 中所有处理过的 `CPWafer` 对象。
*   `params`: 一个列表，包含该 Lot 涉及的所有测试参数的 `CPParameter` 对象。通常在读取第一个 Wafer 数据时确定。
*   `combined_data`: （Python 新增）一个 Pandas DataFrame，将 `wafers` 列表中所有 `CPWafer` 的 `chip_data` 合并在一起，并增加了 `wafer_id`, `seq`, `x`, `y`, `bin` 列以区分数据来源。方便进行 Lot 级别的整体分析。

**计算属性:**

*   `wafer_count`: 通过 `@property` 装饰器实现，返回 `wafers` 列表的长度。
*   `param_count`: 通过 `@property` 装饰器实现，返回 `params` 列表的长度。

**方法:**

*   `get_param_by_id(param_id)`: 根据参数 ID 在 `params` 列表中查找并返回对应的 `CPParameter` 对象。
*   `get_wafer_by_id(wafer_id)`: 根据晶圆 ID 在 `wafers` 列表中查找并返回对应的 `CPWafer` 对象。
*   `combine_data_from_wafers()`: 将 `wafers` 列表中所有 `CPWafer` 的 `chip_data` 合并到 `combined_data` 这个 DataFrame 中。

**注意:** VBA `CPLot` 中的 `Id` (似乎未使用，用 `lot_id` 代替), `WaferCount` (动态计算), `ParamCount` (动态计算), `ParamData`, `StatInfo` 字段在 Python 版本中进行了调整或移除。核心的数据存储通过 `wafers` 列表（包含各自的 `chip_data`）和新增的 `combined_data` DataFrame 实现。 