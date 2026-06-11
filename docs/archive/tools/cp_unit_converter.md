# CP单位转换工具

## 简介

CP单位转换工具是一个专用的命令行工具，用于处理CP测试数据中的单位转换问题。该工具主要用于将LimitU和LimitL列中带单位的值转换为标准单位值，同时保持TestCond列不变，以便于后续数据处理和图表生成。此外，工具还支持数据格式的重新组织，可以将规格参数从合并列(图1格式)转换为分列显示(图2格式)。

## 功能特点

- 将LimitU和LimitL列中的值转换为标准单位值，如将"3.3mV"转换为0.0033(V)
- 保持TestCond列原样不变
- 支持单个Excel文件处理
- 支持批量处理目录中的多个Excel文件
- 提供单个值的单位转换功能
- 支持多种单位前缀，如毫(m)、微(u)、纳(n)、皮(p)、千(k)等
- 支持常见的测量单位，如V、A、Ohm、Hz等
- **新增功能**: 支持数据格式转换，将合并格式数据转换为分列格式，便于读取和处理

## 安装要求

- Python 3.6+
- 依赖库：pandas, numpy, openpyxl

### 安装依赖库

```bash
pip install pandas numpy openpyxl
```

## 使用方法

CP单位转换工具提供了以下使用模式：

1. 处理单个Excel/CSV文件（单位转换+格式转换）
2. 批量处理目录中的Excel/CSV文件（单位转换+格式转换）
3. 单个值的单位转换
4. 仅执行数据格式转换（从图1格式转换为图2格式）

### 处理单个Excel/CSV文件

```bash
python cp_unit_converter.py file <输入文件路径> [-o <输出文件路径>] [-s <工作表名称>] [-f]
```

参数说明：
- `<输入文件路径>`: 要处理的Excel/CSV文件路径
- `-o, --output`: 输出文件路径（可选，默认为输入文件名加`_converted`后缀）
- `-s, --sheet`: 要处理的工作表名称（可选，默认为'Spec'，仅Excel文件有效）
- `-f, --format`: 仅执行格式转换，不进行单位转换（可选，默认执行单位转换）

示例：
```bash
# 处理输入文件，使用默认输出文件名和默认工作表
python cp_unit_converter.py file data/test_data.xlsx

# 指定输出文件名和工作表
python cp_unit_converter.py file data/test_data.xlsx -o output/converted_test_data.xlsx -s Spec

# 仅执行格式转换，不进行单位转换
python cp_unit_converter.py file data/test_data.xlsx -f
```

### 批量处理目录中的Excel/CSV文件

```bash
python cp_unit_converter.py dir <输入目录路径> [-o <输出目录路径>] [-p <文件匹配模式>] [-f]
```

参数说明：
- `<输入目录路径>`: 包含要处理的Excel/CSV文件的目录路径
- `-o, --output`: 输出目录路径（可选，默认为输入目录）
- `-p, --pattern`: 文件匹配模式，使用逗号分隔多个模式（可选，默认为"*.xlsx,*.csv"）
- `-f, --format`: 仅执行格式转换，不进行单位转换（可选，默认执行单位转换）

示例：
```bash
# 处理目录中的所有Excel和CSV文件
python cp_unit_converter.py dir data

# 指定输出目录和文件匹配模式
python cp_unit_converter.py dir data -o output -p "*.xlsx"

# 处理目录中的所有Excel和CSV文件，仅执行格式转换
python cp_unit_converter.py dir data -f
```

### 单个值的单位转换

```bash
python cp_unit_converter.py value <值>
```

参数说明：
- `<值>`: 要转换的值，如 "3.3mV"

示例：
```bash
python cp_unit_converter.py value 3.3mV
```

### 仅执行数据格式转换

```bash
python cp_unit_converter.py format <输入文件路径> [-o <输出文件路径>] [-s <工作表名称>]
```

参数说明：
- `<输入文件路径>`: 要处理的Excel/CSV文件路径
- `-o, --output`: 输出文件路径（可选，默认为输入文件名加`_formatted`后缀）
- `-s, --sheet`: 要处理的工作表名称（可选，默认为'Spec'，仅Excel文件有效）

示例：
```bash
# 仅执行格式转换，不进行单位转换
python cp_unit_converter.py format data/test_data.csv
```

## 数据格式说明

该工具能处理的数据格式包括：

### 图1格式（合并格式）

所有参数和值挤在同一列/单元格中：

```
Parameter CONT IGSS0 IGSS1 IGSSR1 VTH BVDSS1 ...
Unit V A A A V V ...
LimitU 0.500V 99.00uA 100.0nA 100.0nA 3.900V 140.0V ...
LimitL 0V 0A 0A 0A 2.400V 120.0V ...
TestCond: 1.00mA 1.00V 10.0V 10.0V 250uA 250uA ...
```

### 图2格式（分列格式）

每个参数有独立的列显示：

```
       | CONT  | IGSS0  | IGSS1  | IGSSR1 | VTH   | ...
-------+-------+--------+--------+--------+-------+----
Unit   | V     | A      | A      | A      | V     | ...
LimitU | 0.500V| 99.00uA| 100.0nA| 100.0nA| 3.900V| ...
LimitL | 0V    | 0A     | 0A     | 0A     | 2.400V| ...
TestCond|1.00mA| 1.00V  | 10.0V  | 10.0V  | 250uA | ...
```

## 转换规则

1. **单位转换规则**：
   - 对于带单位的值（如"3.3mV"），工具会将其转换为标准单位值（0.0033V）
   - 单位前缀转换率：f(10^-15), p(10^-12), n(10^-9), u/μ(10^-6), m(10^-3), k(10^3), M/meg(10^6), G/g(10^9), T/t(10^12)
   - 支持的基本单位：V, A, Ohm, Hz, F, s, h 等

2. **格式转换规则**：
   - 工具能识别图1格式，并自动将其转换为图2格式
   - 如果数据已经是图2格式，则保持不变
   - 在转换过程中保留原始值的完整性

## 实现细节

CP单位转换工具实现了以下主要功能类：

1. **UnitConverter类**：核心单位转换引擎，支持单位提取和数值转换
2. **格式化处理**：自动检测数据格式，并执行必要的格式转换
3. **命令行接口**：便捷的命令行参数和子命令

## 常见问题

1. **为什么我的CSV文件无法正确读取？**
   - 请确保CSV文件使用制表符(\t)或逗号(,)作为分隔符
   - 检查文件编码，工具默认使用UTF-8编码

2. **如何仅执行格式转换，不改变LimitU和LimitL的值？**
   - 使用`-f`或`--format`选项，或使用`format`子命令

3. **为什么格式转换后的数据列对齐有问题？**
   - 如果源数据格式严重错乱，可能需要手动调整结果文件
   - 确保源数据中的参数名、单位和值数量一致

## 开发历史

- 初始版本：实现基本的单位转换功能
- 当前版本：增加了数据格式转换功能，支持从图1格式转换为图2格式

## 支持的单位前缀

| 前缀符号 | 名称 | 倍率 |
|---------|------|-----|
| f | femto（飞） | 10^-15 |
| p | pico（皮） | 10^-12 |
| n | nano（纳） | 10^-9 |
| u/μ | micro（微） | 10^-6 |
| m | milli（毫） | 10^-3 |
| k | kilo（千） | 10^3 |
| M/meg | mega（兆） | 10^6 |
| G/g | giga（吉） | 10^9 |
| T/t | tera（太） | 10^12 |

## 支持的基本单位

- V, volt, volts（伏特）
- A, amp, amps, ampere, amperes（安培）
- Ohm, ohms（欧姆）
- Hz, hertz（赫兹）
- F, farad, farads（法拉）
- S, sec, second, seconds（秒）
- H, henry, henries（亨利）

## 示例输入输出

### 输入Excel示例

| Param | Unit | SL | SU | TestCond1 | TestCond2 |
|-------|------|----|----|-----------|-----------|
| Vth   | V    | 0.3V | 0.7V | Vds=0.1V | Ids=1uA |
| Idsat | A    | 1.0mA | 10mA | Vds=1.2V | Vgs=1.2V |
| Res   | Ohm  | 100Ohm | 1kOhm | I=1mA | - |

### 输出Excel示例

| Param | Unit | SL | SU | TestCond1 | TestCond2 |
|-------|------|----|----|-----------|-----------|
| Vth   | V    | 0.3 | 0.7 | Vds=0.1V | Ids=1uA |
| Idsat | A    | 0.001 | 0.01 | Vds=1.2V | Vgs=1.2V |
| Res   | Ohm  | 100 | 1000 | I=1mA | - |

## 更新日志

- 1.0.0 (2023-05-20): 初始版本

## 许可证

MIT 