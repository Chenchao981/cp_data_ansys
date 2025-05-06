# Python CP 通用工具函数 (`通用工具函数.py`)

该 Python 模块 (`通用工具函数.py`) 整合并实现了 VBA 版本中 `通用数组操作函数.bas` 和 `List函数简化.bas` 模块里的部分通用辅助函数功能。旨在提供一些在数据处理流程中可能用到的便捷操作，特别是处理不同格式的输入（如列表或逗号分隔字符串）以及进行基本的列表/数组检查。

使用了 Python 的标准库和 `numpy` 库来实现相关功能。

## 主要函数说明

### 1. `is_valid_list(lst)`

*   **功能**: 检查输入 `lst` 是否为一个有效的 Python 列表或 NumPy 数组，并且不能为空。
*   **对应 VBA**: `IsList`, `IsArrayNotEmpty`
*   **实现**: 利用 `isinstance` 检查类型，并用 `len()` 检查是否为空。

```python
import numpy as np
from typing import Any, List, Union, Sequence

def is_valid_list(lst: Any) -> bool:
    """检查输入是否为非空列表或 NumPy 数组。"""
    return isinstance(lst, (list, np.ndarray)) and len(lst) > 0
```

### 2. `check_list(input_var: Union[str, Sequence, Any]) -> List[Any]`

*   **功能**: 检查输入变量 `input_var`。
    *   如果已经是列表或 NumPy 数组，直接返回（如果是 NumPy 数组，会尝试转为列表）。
    *   如果是字符串，尝试按逗号 `,` 分割成列表。
    *   如果是其他类型，将其放入一个单元素的列表中返回。
    *   如果是 `None` 或空字符串，返回空列表。
*   **对应 VBA**: `CheckList`
*   **用途**: 常用于处理函数参数，使其能接受列表、NumPy 数组或逗号分隔的字符串作为输入。

```python
def check_list(input_var: Union[str, Sequence, Any]) -> List[Any]:
    """检查输入变量，将其规范化为列表。"
    if input_var is None:
        return []
    if isinstance(input_var, (list, tuple)):
        return list(input_var)
    if isinstance(input_var, np.ndarray):
        return input_var.tolist() # 将 NumPy 数组转换为 Python 列表
    if isinstance(input_var, str):
        if not input_var.strip(): # 处理空字符串
            return []
        # 按逗号分割，并去除每个元素前后的空白字符
        return [item.strip() for item in input_var.split(',')]
    # 其他类型，放入单元素列表
    return [input_var]
```

### 3. `safe_get_element(lst: Sequence, index: int) -> Any`

*   **功能**: 安全地获取序列（列表、元组等）中指定索引 `index` 的元素。
    *   支持正索引（从 0 开始）和负索引（从 -1 开始，表示最后一个元素）。
    *   如果索引越界，返回 `None`。
*   **对应 VBA**: `nth` (部分功能)

```python
def safe_get_element(lst: Sequence, index: int) -> Any:
    """安全地获取序列中指定索引的元素，支持负索引。索引越界返回 None。"""
    try:
        return lst[index]
    except (IndexError, TypeError):
        return None
```

### 4. `ensure_list(item_or_list: Any) -> List[Any]`

*   **功能**: 确保返回值是一个列表。
    *   如果输入本身是列表或元组，直接返回（元组转为列表）。
    *   否则，将输入元素放入一个新的单元素列表中返回。
*   **对应 VBA**: (无直接对应，但常用于需要列表输入的场景)

```python
def ensure_list(item_or_list: Any) -> List[Any]:
    """确保输入被包装成列表。"""
    if isinstance(item_or_list, list):
        return item_or_list
    if isinstance(item_or_list, tuple):
        return list(item_or_list)
    return [item_or_list]
```

### 5. `ShowInfo` 类

*   **功能**: 模拟 VBA `clsShowInfo` 的功能，提供显示信息和错误消息的接口。内部使用 Python 的 `logging` 模块进行标准化的日志输出，并能限制相同提示信息的重复输出次数。
*   **对应 VBA**: `clsShowInfo`
*   **方法**:
    *   `__init__(repeat_count_max=10)`: 初始化，设置重复消息的最大显示次数。
    *   `info(message, title="提示")`: 记录普通信息 (INFO 级别)，限制重复。
    *   `alarm(error_info, title="警告", ocap=None)`: 记录警告信息 (WARNING 级别)。
    *   `stop(error_info, title="异常终止", ocap=None)`: 记录严重错误信息 (CRITICAL 级别) 并退出程序。

```python
import logging
import sys

# (日志配置代码...)

class ShowInfo:
    def __init__(self, repeat_count_max: int = 10):
        self._show_info_dic = {}
        self._repeat_count_max = repeat_count_max

    def info(self, message: Any, title: str = "提示") -> None:
        # ... 实现 ...
        logger.info(f"[{title}] {str(message)}")

    def alarm(self, error_info: Any, title: str = "警告", ocap: Any = None) -> None:
        # ... 实现 ...
        s_ocap = f"\n  推荐解决方案: {str(ocap)}" if ocap else ""
        logger.warning(f"[{title}] {str(error_info)}{s_ocap}")

    def stop(self, error_info: Any, title: str = "异常终止", ocap: Any = None) -> None:
        # ... 实现 ...
        s_ocap = f"\n  推荐解决方案: {str(ocap)}" if ocap else ""
        logger.critical(f"[{title}] {str(error_info)}{s_ocap}")
        sys.exit(1)

# 可以创建一个全局实例供使用
# g_show = ShowInfo()

## 未包含的 VBA 函数及原因

*   **`Push`, `cons`, `Append`, `cdr`, `car`**: 这些是函数式编程风格的列表操作，在 Python 中通常使用列表的内置方法（如 `append`, `insert`, `+` 运算符, 切片 `[:]`）或列表推导式更自然、高效。
*   **`ExpandBlank2List`, `ExpandValue2List`, `ExpandList2List`**: Python 列表是动态的，可以使用 `append()` 或 `extend()` 方法，或 `+` 运算符进行扩展。
*   **`GetDimension`, `DimensionLength`**: 对于 NumPy 数组，可以使用 `.ndim` 获取维度数，`.shape` 获取各维度长度。对于 Python 列表，通常只关心 `len()`。
*   **`IsArrayEmpty`**: 可以用 `not is_valid_list(arr)` 或 `len(arr) == 0` 实现。
*   **`ArrayValueCopy`**: Python 的赋值 (`=`) 对于不可变类型（数字、字符串、元组）是值复制，对于可变类型（列表、字典）是引用复制。如果需要深拷贝，可以使用 `copy` 模块的 `deepcopy()`。
*   **`BigArrayTranspose`**: NumPy 提供了强大的 `numpy.transpose()` 函数或 `.T` 属性，无需手动实现。

这个 Python 模块专注于提供 VBA 中常用且在 Python 中有用的辅助函数，同时利用 Python 和 NumPy 的现有能力，避免冗余实现。

# --- 未转换的 VBA 函数说明 ---
# clsRegEx: Python 中有内置的 re 模块
# clsShowInfo: 下方添加了 ShowInfo 类作为替代