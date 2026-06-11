# DCP规格提取器 (`dcp_spec_extractor.py`) 说明文档

## 概述

`dcp_spec_extractor.py` 是一个Python脚本，设计用于从DCP (Device Characterization Program) 格式的 `.txt` 测试数据文件的头部提取详细的参数规格信息。提取后的信息被格式化并保存为一个使用制表符分隔的 `.csv` 文件，文件名将包含原始DCP文件名和生成时间戳，格式为 `[原始DCP文件名基名]_spec_[时间戳].csv`。

此脚本旨在作为数据清洗流程 (`clean_dcp_data.py`) 的一部分被调用，为每个处理的DCP数据批次生成一份对应的规格参数总结。

## 功能特性

-   **自动解析DCP文件头部**：脚本读取DCP `.txt` 文件的前20行，以捕获包含规格信息的头部数据。
-   **动态定位关键信息行**：
    -   通过查找以 `No.U\\tX\\tY\\tBin` 开头的行来定位参数名称行。
    -   基于参数名称行的位置，推断 `LimitU` (上限)、`LimitL` (下限) 和 `Bias` (测试条件) 等信息行的位置。
-   **参数提取与格式化**：
    -   **Parameter (参数名称)**：从参数名称行提取，自动跳过前缀字段 (`No.U`, `X`, `Y`, `Bin`)。
    -   **Unit (单位)**：从 `LimitU` 行的值中推断，并标准化为 `V` (伏特)、`A` (安培) 或 `ohm` (欧姆)。如果无法识别，则单位为空。
    -   **LimitU (上限值)**：提取对应参数的上限值，并仅保留数值部分。
    -   **LimitL (下限值)**：提取对应参数的下限值，并仅保留数值部分。
    -   **TestCond (测试条件)**：从 `Bias 1` 到 `Bias 6` 行提取，每行 `Bias` 数据在CSV中生成一个 `TestCond:` 条目，保留原始值（包括单位）。
-   **精确的CSV输出格式**：
    -   严格按照用户提供的包含 `CONT` 参数的特定格式输出。
    -   `CONT` 参数在 `Unit`、`LimitU`、`LimitL` 和 `TestCond` 对应行中的值通常为空。
    -   即使某些 `Bias` 行在原始文件中没有数据（如 `Bias 2`），也会在CSV中生成对应的空 `TestCond:` 行，以保持结构一致性。
    -   所有输出行都将具有与参数行相同数量的列（参数数量 + 1个行标签列）。
-   **制表符分隔**：输出的CSV文件使用制表符 (`\\t`) 作为字段分隔符。
-   **日志记录**：脚本包含基本的日志记录，用于追踪处理过程和潜在错误。
-   **独立测试能力**：脚本包含一个 `if __name__ == '__main__':` 代码块，允许直接运行以进行测试。测试时会生成一个临时的DCP示例文件和输出目录。

## 文件结构与主要函数

### `dcp_spec_extractor.py`

-   **`_extract_unit(value_str: str) -> str`**:
    -   辅助函数，用于从字符串中提取并标准化参数单位 (`V`, `A`, `ohm`)。
-   **`_extract_value(value_str: str) -> str`**:
    -   辅助函数，用于从包含单位的字符串中提取数值部分。
-   **`generate_spec_file(dcp_file_path: str, output_dir: str) -> str | None`**:
    -   核心函数，负责整个提取和文件生成过程。
    -   **参数**:
        -   `dcp_file_path (str)`: 输入的DCP `.txt` 文件的完整路径。
        -   `output_dir (str)`: 用于保存生成的 `_spec_.csv` 文件的目录路径。
    -   **返回**:
        -   `str`: 成功生成的CSV文件的完整路径。
        -   `None`: 如果处理过程中发生错误。

## 使用方法

该脚本主要被设计为由其他脚本（如 `clean_dcp_data.py`）导入和调用。

### 作为模块调用示例：

```python
from dcp_spec_extractor import generate_spec_file

dcp_file = "/path/to/your/dcp_data.txt"
output_folder = "/path/to/output_spec_files"
spec_file_path = generate_spec_file(dcp_file, output_folder)

if spec_file_path:
    print(f"规格文件已生成: {spec_file_path}")
else:
    print("规格文件生成失败。")
```

### 独立运行 (用于测试):

可以直接通过命令行执行此脚本，它将运行内置的测试逻辑：

```bash
python dcp_spec_extractor.py
```

测试运行时，会在脚本所在目录下创建 `test_dcp_data/sample_dcp.txt` (临时DCP文件) 和 `output_spec_files` 目录 (用于存放测试生成的spec文件)。

## 输入DCP文件格式约定

脚本依赖于DCP文件头部具有特定的结构和内容：

1.  **参数名称行**: 必须存在，并且以 `No.U\\tX\\tY\\tBin` 开头，后面紧跟以制表符分隔的参数名称 (如 `CONT`, `IGSS0`, 等)。
    *   示例: `No.U\\tX\\tY\\tBin\\tCONT\\tIGSS0\\tIGSS1\\t...`
2.  **LimitU行**: 应该紧跟在参数名称行之后，通常以 `LimitU` 开头，其后的值对应各个参数的上限。
    *   示例: `LimitU\\t\\t\\t\\t0.500V\\t99.00uA\\t...` (注意 `CONT` 列可能为空)
3.  **LimitL行**: 应该紧跟在 `LimitU` 行之后，通常以 `LimitL` 开头。
    *   示例: `LimitL\\t\\t\\t\\t0V\\t0A\\t...`
4.  **Bias行**: 应该紧跟在 `LimitL` 行之后，从 `Bias 1` 到 `Bias 6` (共6行)。
    *   示例: `Bias 1\\t\\t\\t\\t1.00mA\\t1.00V\\t...`
    *   某些Bias行可能除了标签外没有其他数据 (例如 `Bias 2\\t\\t\\t...`)。

## 输出CSV文件格式

输出的 `_spec_.csv` 文件将包含以下几行，均以制表符分隔：

1.  **Parameter**: 第一个单元格为 "Parameter"，后续单元格为从DCP文件提取的参数名称。
2.  **Unit**: 第一个单元格为 "Unit"，后续单元格为对应参数的标准化单位 (V, A, ohm) 或空。
3.  **LimitU**: 第一个单元格为 "LimitU"，后续单元格为对应参数的上限数值或空。
4.  **LimitL**: 第一个单元格为 "LimitL"，后续单元格为对应参数的下限数值或空。
5.  **TestCond:** (可能多行): 每行第一个单元格为 "TestCond:"，后续单元格为对应 `Bias` 行提取的原始测试条件或空。

### CSV输出示例:

```csv
Parameter	CONT	IGSS0	IGSS1	IGSSR1	VTH	BVDSS1	BVDSS2	IDSS1	IDSS2	IGSS2	IGSSR2
Unit		V	A	A	A	V	V	V	A	A	A	A
LimitU		0.500	99.00	100.0	100.0	3.900	140.0	140.0	100.0	200.0	200.0	200.0
LimitL		0	0	0	0	2.400	120.0	120.0	0	0	0	0
TestCond:		1.00mA	1.00V	10.0V	10.0V	250uA	250uA	10.0mA	110V	120V	18.0V	18.0V
TestCond:											
TestCond:									400V	400V				
TestCond:		2.50ms	10.0ms	40.0ms	40.0ms	2.00ms	20.0ms	10.0ms	20.0ms	20.0ms	40.0ms	40.0ms
TestCond:											
TestCond:											
```

## 错误处理

-   如果输入的DCP文件未找到或格式不符合预期（例如，缺少关键的参数行），脚本将记录错误并通过 `logger` 输出，并返回 `None`。
-   其他意外错误也会被捕获、记录，并导致函数返回 `None`。

## 依赖

-   Python 3.x
-   标准库: `os`, `re`, `csv`, `datetime`, `pathlib`, `logging`

无需额外安装第三方库。

# DCP规格提取器 - 单位转换功能说明

## 概述

DCP规格提取器(`dcp_spec_extractor.py`)是一个用于从DCP(Device Characterization Program)文件中提取参数规格信息的工具。最新版本添加了单位转换功能，可将LimitU和LimitL值从带单位的字符串(如"100.0nA", "3.900V")转换为标准单位下的纯数值(如"1E-07", "3.9")，便于后续数据处理和图表生成。

## 主要功能

1. **规格数据提取**：从DCP .txt文件的头部提取参数名称、单位、上限值和下限值
2. **单位标准化**：将提取的单位统一为标准单位(V, A, ohm)
3. **数值转换**：将带单位的限值(如"100.0nA")转换为标准单位下的纯数值("1E-07")
4. **格式化输出**：根据数值大小选择合适的表示格式(科学计数法或普通数字)
5. **CSV文件生成**：将处理后的数据保存为CSV格式，便于后续分析

## 单位转换功能

### 转换原理

- 单位前缀转换表：
  - f (femto): 1e-15
  - p (pico): 1e-12
  - n (nano): 1e-9
  - u/μ (micro): 1e-6
  - m (milli): 1e-3
  - k (kilo): 1e3
  - M (mega): 1e6
  - G (giga): 1e9
  - T (tera): 1e12

- 基本单位：
  - 电压: V (volt)
  - 电流: A (ampere)
  - 电阻: ohm

### 转换示例

| 原始值(带单位) | 转换后数值(标准单位) | 格式化字符串 |
|--------------|-------------------|------------|
| 100.0nA      | 0.0000001 A       | 1E-07      |
| 99.00uA      | 0.000099 A        | 9.90E-05   |
| 3.900V       | 3.9 V             | 3.9        |
| 140.0V       | 140 V             | 140        |
| 0A           | 0 A               | 0          |

### 格式化规则

- **科学计数法**：用于非常小(<0.001)或非常大(>=100000)的数值
  - 例如: 1E-07, 9.90E-05, 2.50E+05
- **普通数字格式**：用于其他情况
  - 例如: 0.5, 140, 3.9
- **整数格式**：用于可以精确表示为整数的值
  - 例如: 0, 140, 200

## 使用方法

### 基本用法

```python
from dcp_spec_extractor import generate_spec_file

# 生成规格文件
input_file = "path/to/dcp_file.txt"
output_dir = "output_directory"
result = generate_spec_file(input_file, output_dir)

if result:
    print(f"成功生成规格文件: {result}")
else:
    print("生成规格文件失败")
```

### 命令行用法

```bash
python dcp_spec_extractor.py
```

这将运行脚本中的测试代码，创建一个示例DCP文件并生成对应的规格CSV文件。

## 输出文件格式

生成的CSV文件包含以下行:

1. **Parameter**: 参数名称(CONT, IGSS0, IGSS1等)
2. **Unit**: 标准单位(V, A, ohm)
3. **LimitU**: 上限值(转换为标准单位下的纯数值)
4. **LimitL**: 下限值(转换为标准单位下的纯数值)
5. **TestCond**: 测试条件(保持原样，不进行单位转换)
6. 其他Bias行(保持原样，不进行单位转换)

## 依赖关系

该脚本可以选择性地使用`cp_unit_converter.py`中的`UnitConverter`类进行单位转换。如果这个模块不可用，脚本会使用内置的备用转换器继续工作。

## 注意事项

1. 单位转换仅适用于LimitU和LimitL行，TestCond行和其他Bias行保持原样
2. 如果某个值无法解析或转换，将保留原始字符串
3. 输出CSV文件使用逗号作为分隔符
4. 文件名格式为`[原始DCP文件名]_spec_[时间戳].csv` 