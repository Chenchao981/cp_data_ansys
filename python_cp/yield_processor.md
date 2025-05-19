# `yield_processor.py` - 良率报告生成模块

## 1. 功能概述

本模块 (`yield_processor.py`) 提供了一个核心函数 `generate_yield_report_from_dataframe`，用于根据已清洗的半导体晶圆测试数据（以Pandas DataFrame形式传入）生成一个详细的良率报告。该报告遵循 `yield.md` 文件中定义的格式和计算规则，并以CSV格式输出。

此模块设计为在数据清洗流程之后被调用，直接利用内存中的DataFrame进行处理，以提高效率并保持模块化。

## 2. 主要函数

### `generate_yield_report_from_dataframe(cleaned_df: pd.DataFrame, output_filepath: str) -> bool`

*   **功能描述**：接收一个包含清洗后晶圆测试数据的Pandas DataFrame和一个输出文件路径，计算每个晶圆的良率、指定Bin的Die数量、总Die数、Pass Die数，并计算整个批次的汇总统计数据。最后，将这些信息保存为一个CSV文件。
*   **参数**：
    *   `cleaned_df (pd.DataFrame)`: 包含清洗后数据的Pandas DataFrame。该DataFrame必须包含以下列：
        *   `Lot_ID`: 批次标识。
        *   `Wafer_ID`: 晶圆标识。
        *   `Bin`: 每个Die的Bin分类值（数值型）。
    *   `output_filepath (str)`: 生成的良率报告CSV文件的完整路径和文件名 (例如：`LOTXYZ_timestampA_yield_timestampB.csv`)。
*   **处理逻辑**：
    1.  **输入校验**：检查输入是否为DataFrame，是否包含必需列。
    2.  **晶圆数据处理**：按 `Wafer_ID` 对 `cleaned_df`进行分组。
        *   对每个晶圆，计算 `Lot_ID`, `Wafer_ID`, `Total` (总Die数), `Pass` (Bin 1的Die数)。
        *   计算指定Bin（`Bin3`, `Bin4`, `Bin6`, `Bin7`, `Bin8`, `Bin9`）的Die数量。若计数为0，则显示0。
        *   计算数值良率 `(Pass / Total) * 100`（若Total为0，则良率为0.0）。
        *   将数值良率格式化为字符串 `"XX.YY%"`。
        *   收集每个晶圆的数值良率用于后续计算批次平均良率。
    3.  **批次汇总 ("ALL" 行)**：
        *   `Lot_ID` 和 `Wafer_ID` 固定为 `"ALL"`。
        *   `Total`, `Pass`, 及各 `BinX` 数量为所有单个晶圆对应值的总和。
        *   `Yield` ("ALL"行): 所有单个晶圆**数值良率**的算术平均值，然后格式化为 `"XX.YY%"`。若所有晶圆Total为0或无晶圆数据，则批次Yield为 `"0.00%"`。
    4.  **输出**：将处理后的数据（包括所有晶圆行和"ALL"汇总行）构建成一个新的DataFrame，并按照 `yield.md` 中指定的列顺序和格式保存到 `output_filepath`。
*   **返回**：`bool`
    *   `True`: 如果报告成功生成并保存。
    *   `False`: 如果在处理或保存过程中发生错误（例如，输入数据无效，无法写入文件等）。详细错误会通过日志记录。

## 3. 输出文件 (`*_yield_*.csv`)

*   **文件名规则**：由调用时传入的 `output_filepath` 参数决定。通常建议遵循 `yield.md` 中的命名约定，例如，若输入数据概念上对应 `LOTXYZ_timestampA_cleaned_timestampB.csv`，则输出可以是 `LOTXYZ_timestampA_yield_timestampB.csv`。
*   **格式**：CSV (逗号分隔值)，UTF-8编码 (采用 `utf-8-sig` 以确保Excel正确显示中文字符)。
*   **内容结构**：
    *   第一行为表头。
    *   后续每行代表一个独立晶圆的良率数据。
    *   最后一行是整个批次的汇总统计，其 `Lot_ID` 和 `Wafer_ID` 字段标记为 `"ALL"`。

## 4. 输出字段定义 (与 `yield.md` 一致)

| 字段名    | 描述                                                                 | 数据类型 (CSV中) | 晶圆行示例    | "ALL"行示例 | 备注                                                                 |
| :-------- | :------------------------------------------------------------------- | :--------------- | :------------ | :---------- | :------------------------------------------------------------------- |
| `Lot_ID`  | 批次标识符                                                           | String           | "FA54-..."    | "ALL"       | "ALL"行固定为 "ALL"                                     |
| `Wafer_ID`| 晶圆标识符                                                           | String           | "1", "2", ... | "ALL"       | "ALL"行固定为 "ALL"                                     |
| `Yield`   | 良率                                                                 | String           | "98.45%"      | "98.18%"    | 格式为百分比，保留两位小数；"ALL"行为批次内所有晶圆良率的算术平均值 |
| `Total`   | 总Die数量                                                            | Integer          | 193           | 4825        | "ALL"行为批次内所有晶圆Total的累加                                   |
| `Pass`    | Bin 1 的Die数量                                                      | Integer          | 190           | 4737        | "ALL"行为批次内所有晶圆Pass的累加                                    |
| `Bin3`    | Bin 3 的Die数量                                                      | Integer          | 0             | 10          | "ALL"行为批次内所有晶圆Bin3的累加；若计数为0，显示0          |
| `Bin4`    | Bin 4 的Die数量                                                      | Integer          | 1             | 19          | "ALL"行为批次内所有晶圆Bin4的累加；若计数为0，显示0          |
| `Bin6`    | Bin 6 的Die数量                                                      | Integer          | 2             | 51          | "ALL"行为批次内所有晶圆Bin6的累加；若计数为0，显示0          |
| `Bin7`    | Bin 7 的Die数量                                                      | Integer          | 0             | 3           | "ALL"行为批次内所有晶圆Bin7的累加；若计数为0，显示0          |
| `Bin8`    | Bin 8 的Die数量                                                      | Integer          | 0             | 2           | "ALL"行为批次内所有晶圆Bin8的累加；若计数为0，显示0          |
| `Bin9`    | Bin 9 的Die数量                                                      | Integer          | 0             | 3           | "ALL"行为批次内所有晶圆Bin9的累加；若计数为0，显示0          |

*   **空值/0值表示**：如果某个Bin的计数为0，在CSV中应明确显示为 `0`。

## 5. 计算逻辑关键点

*   **特定Bin列**：良率报告固定输出 `Bin3`, `Bin4`, `Bin6`, `Bin7`, `Bin8`, `Bin9` 的计数。
*   **良率格式**：所有 `Yield` 字段均以百分比字符串形式表示，并保留两位小数 (例如 `"98.45%"`)。
*   **"ALL"行良率计算**：批次汇总行的 `Yield` 是基于所有单个晶圆的**数值良率**（即百分比值，如98.45）进行算术平均后，再格式化为百分比字符串。
*   **零Die处理**：如果一个晶圆的 `Total` Die数量为0，其 `Yield` 显示为 `"0.00%"`。
*   **Lot_ID 和 Wafer_ID 字符串化**：输入DataFrame中的`Lot_ID`和`Wafer_ID`（即使是数字）在输出CSV中会转换为字符串类型。

## 6. 依赖项

*   `pandas`: 用于DataFrame操作和CSV文件读写。
*   `typing` (Python内建): 用于类型提示。
*   `logging` (Python内建): 用于记录程序运行信息和错误。

## 7. 集成方式

`yield_processor.py` 模块中的 `generate_yield_report_from_dataframe` 函数主要被设计为由其他数据处理脚本（例如主数据清洗脚本 `clean_dcp_data.py` 或类似功能的脚本）在完成数据清洗步骤后调用。调用时，将清洗后得到的 Pandas DataFrame 直接作为参数传递给该函数，同时指定期望的输出CSV文件路径。

**示例调用场景 (在另一个脚本中):**

```python
# 假设在 clean_dcp_data.py 或类似脚本中
import pandas as pd
from python_cp.yield_processor import generate_yield_report_from_dataframe # 假设正确的导入路径

# ... (执行数据清洗的逻辑) ...
# cleaned_data_df 是清洗后得到的DataFrame

# 假设 cleaned_data_df 已经准备好
output_yield_report_path = "path/to/your/output_yield_report.csv"

success = generate_yield_report_from_dataframe(cleaned_data_df, output_yield_report_path)

if success:
    print(f"良率报告已生成: {output_yield_report_path}")
else:
    print("良率报告生成失败，请查看日志。")
``` 