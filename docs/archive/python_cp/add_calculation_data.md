# 增加运算数据模块 (`增加运算数据.py`)

## 模块概述

`增加运算数据.py` 模块用于根据用户在外部 Excel 文件中定义的计算公式，在现有的 `CPLot` 数据对象中动态添加新的计算参数列，并填充计算结果。这允许用户在不修改核心数据处理代码的情况下，灵活地基于已存在的参数衍生出新的分析参数。

##核心功能

1.  **读取计算配置**: 从指定的 Excel 文件和工作表读取新参数的定义。
2.  **公式转换**: 将 Excel 中使用特殊占位符（如 `f1`, `f2` 代表原始数据中的第一、第二个参数）的公式，转换为 Python 可执行的表达式。
3.  **数据结构扩展**: 自动扩展 `CPLot` 对象中的参数列表 (`CPLot.params`) 和每个晶圆的芯片数据 (`CPWafer.chip_data`)，以容纳新的计算参数。
4.  **执行计算**: 遍历每个芯片的数据，应用转换后的公式进行计算，并将结果填充到对应的新参数列中。
5.  **错误处理**: 在公式计算过程中，如果遇到数学错误（如除零）或依赖数据缺失 (`NaN`)，则对应芯片的新参数结果将被置为 `NaN`，并记录相应的日志信息。

## 主要组件

### 数据类

*   **`CalculatedParameterSetup`**:
    *   `new_param_name (str)`: 用户定义的新参数显示名称。
    *   `new_param_id (str)`: 新参数的唯一标识符。
    *   `original_formula (str)`: 用户在 Excel 中输入的原始 "fN" 风格公式。
    *   `python_formula (str)`: 模块内部转换后，可供 Python `eval()` 执行的公式字符串。
    *   `dependent_param_ids (List[str])`: 该公式所依赖的原始参数的ID列表。
    *   `unit (Optional[str])`: 新参数的单位。
    *   `sl (Optional[float])`: 新参数的规格下限。
    *   `su (Optional[float])`: 新参数的规格上限。

*   **`CalculatedParameterConfig`**:
    *   `setups (List[CalculatedParameterSetup])`: 包含所有从 Excel 读取并解析后的计算参数设置。

### 主要函数

*   **`read_calculation_setup(excel_path: str, sheet_name: str, existing_param_names_ordered: List[str]) -> CalculatedParameterConfig`**:
    *   **功能**: 读取指定 Excel 文件 (`excel_path`) 中的特定工作表 (`sheet_name`)，解析计算参数的定义。
    *   **参数**:
        *   `excel_path`: Excel 配置文件的路径。
        *   `sheet_name`: Excel 文件中包含配置信息的工作表名称。
        *   `existing_param_names_ordered`: 一个包含现有 `CPLot` 数据中所有原始参数 **ID** 的有序列表。这个顺序至关重要，因为 Excel 公式中的 `f1` 将映射到此列表的第一个参数 ID，`f2` 映射到第二个，以此类推。
    *   **返回**: `CalculatedParameterConfig` 对象，包含了所有有效的计算设置。
    *   **Excel 配置表格式**:
        *   数据按列组织，每一列定义一个新计算参数。
        *   **第1行**: 新参数的显示名称 (e.g., "Resistance")。
        *   **第2行**: 新参数的唯一ID (e.g., "R_calc")。此ID不能与现有参数ID或已定义的其他新参数ID冲突。
        *   **第3行**: 计算公式。使用 `fN` 表示法引用原始参数 (e.g., "f1/f2", "Abs(f3)*100")。
        *   **第4行**: 新参数的单位 (e.g., "Ohm") (可选)。
        *   **第5行**: 新参数的规格下限 (SL) (可选, 数值型)。
        *   **第6行**: 新参数的规格上限 (SU) (可选, 数值型)。

*   **`add_calculated_parameters(cp_lot_data: CPLot, config: CalculatedParameterConfig) -> CPLot`**:
    *   **功能**: 将 `config` 中定义的计算参数添加到 `cp_lot_data` 中。此函数会修改传入的 `cp_lot_data` 对象。
    *   **参数**:
        *   `cp_lot_data`: 包含原始数据的 `CPLot` 对象。
        *   `config`: 从 `read_calculation_setup` 获取的 `CalculatedParameterConfig` 对象。
    *   **返回**: 修改后的 `CPLot` 对象。
    *   **处理逻辑**:
        1.  将新参数的定义（名称、ID、单位、SL/SU、原始公式等）添加到 `cp_lot_data.params` 列表中。
        2.  对于 `cp_lot_data.wafers` 中的每个 `CPWafer` 对象：
            *   在其 `chip_data` (Pandas DataFrame) 中为每个新计算参数ID添加新列，初始值填充为 `NaN`。
            *   遍历 `chip_data` 的每一行（代表一个芯片）。
            *   准备一个包含当前芯片各依赖参数值的局部作用域字典。
            *   使用 Python 的 `eval()` 函数，在受控的全局作用域（包含允许的数学函数和常量）和上述局部作用域下执行转换后的 `python_formula`。
            *   将计算结果（或因错误产生的 `NaN`）存入 `chip_data` 的相应位置。

### 公式支持

*   **变量引用**: 在 Excel 公式中，使用 `fN` (如 `f1`, `f2`, `f10`) 来引用原始数据中的参数。`f1` 对应 `existing_param_names_ordered` 列表中的第一个参数ID，`f2` 对应第二个，以此类推。
*   **基本运算符**: `+`, `-`, `*`, `/`, `**` (乘方)。 Excel 公式中的 `^` 会被自动转换为 `**`。
*   **支持的函数**: 用户可以在公式中直接使用以下函数名（不区分大小写，模块内部会处理为小写以匹配Python函数）：
    *   `abs`, `sqrt`, `log` (自然对数), `log10`, `exp`
    *   `sin`, `cos`, `tan`, `asin`, `acos`, `atan`
    *   `degrees`, `radians`
    *   `max`, `min` (可接受多个参数，如 `max(f1, f2, 100)`)
    *   `round`
*   **支持的常量**:
    *   `pi` (圆周率)
    *   `e` (自然常数)

## 使用示例

```python
from python_cp.数据类型定义 import CPLot, CPParameter, CPWafer # 假设这些已定义
from python_cp.增加运算数据 import read_calculation_setup, add_calculated_parameters
import pandas as pd
import logging

# 0. 配置日志 (可选)
logging.basicConfig(level=logging.INFO)

# 1. 准备 CPLot 数据 (示例)
# 假设 cp_lot 是一个已加载数据的 CPLot 对象
# existing_param_ids 是 cp_lot.params 中按顺序排列的参数 ID 列表
# 例如: existing_param_ids = ["VOLT", "CURR", "TEMP"]
# cp_lot.wafers[0].chip_data 包含 VOLT, CURR, TEMP 列

# 示例：创建简单的 CPLot 结构
param_v = CPParameter(id="VOLT", name="Voltage", unit="V")
param_i = CPParameter(id="CURR", name="Current", unit="A")
param_t = CPParameter(id="TEMP", name="Temperature", unit="C")
existing_params_list = [param_v, param_i, param_t]
existing_param_ids_ordered = [p.id for p in existing_params_list]

chip_data_w1 = pd.DataFrame({
    "VOLT": [1.0, 1.1, 0.9],
    "CURR": [0.1, 0.11, 0.09],
    "TEMP": [25.0, 25.1, 24.9]
})
wafer1 = CPWafer(wafer_id="W01_test", chip_data=chip_data_w1, param_count=3, chip_count=3)
cp_lot = CPLot(
    lot_id="LotCalcTest",
    params=existing_params_list,
    wafers=[wafer1],
    param_count=3,
    wafer_count=1
)

# 2. 指定 Excel 配置文件路径和表名
excel_file = "path/to/your/calculation_setup.xlsx" # 替换为实际路径
sheet = "Sheet1"

# 创建一个虚拟的 Excel 文件用于演示
# 内容应符合 "Excel 配置表格式" 中描述的结构
# 例如，第一列定义 Resistance (R_CALC = f1/f2)
# 第二列定义 Power (P_CALC = f1*f2)
mock_setup_data = {
    0: ["Resistance", "R_CALC", "f1/f2", "Ohm", 1.0, 100.0],
    1: ["Power", "P_CALC", "f1*f2", "Watt", None, None],
    2: ["Temp_F", "T_F", "f3 * 9/5 + 32", "F", None, None]
}
df_mock_excel = pd.DataFrame(mock_setup_data)
mock_excel_file_path = "dummy_calc_setup.xlsx"
df_mock_excel.to_excel(mock_excel_file_path, sheet_name=sheet, header=False, index=False)


# 3. 读取计算配置
# 注意：existing_param_ids_ordered 必须准确反映 cp_lot 中参数的顺序
# 这些参数是 f1, f2, ... 将要引用的
calculation_config = read_calculation_setup(mock_excel_file_path, sheet, existing_param_ids_ordered)

if not calculation_config.setups:
    print("未能读取到有效的计算配置。")
else:
    # 4. 添加计算参数到 CPLot 数据
    cp_lot_updated = add_calculated_parameters(cp_lot, calculation_config)

    # 5. 查看结果
    print("\\nUpdated Parameters in CPLot:")
    for p in cp_lot_updated.params:
        print(f"  ID: {p.id}, Name: {p.name}, Unit: {p.unit}, Formula: {p.test_conditions}")

    print("\\nUpdated Chip Data for Wafer W01_test:")
    print(cp_lot_updated.wafers[0].chip_data.to_string())

# 清理虚拟文件 (可选)
import os
os.remove(mock_excel_file_path)

```

## 注意事项

*   **参数顺序**: `existing_param_names_ordered` 列表的顺序对于正确解析 "fN" 公式至关重要。
*   **`eval()` 安全性**: 尽管 `eval()` 的使用被限制在受控的全局和局部作用域内，但公式的来源（Excel文件）仍应被认为是可信的。避免执行来自不可信源的任意公式。
*   **参数ID有效性**: 作为公式一部分的原始参数ID（以及新生成的参数ID）最好遵循Python变量命名规范，以避免在`eval`过程中出现问题。如果ID包含特殊字符，可能需要更复杂的处理或确保 `locals_dict` 的键能精确匹配。
*   **依赖关系**: 模块目前不处理计算参数之间的依赖关系（例如，一个计算参数依赖于另一个先计算出的参数）。所有公式都基于原始输入参数进行计算。如果需要多级计算，需要多次调用 `add_calculated_parameters` 或进行相应的功能增强。
*   **日志**: 模块使用 `logging` 记录其操作和潜在错误，有助于调试。 