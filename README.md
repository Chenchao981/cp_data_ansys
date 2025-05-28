
好的，我理解你的需求。你需要我优化现有的 `README.md` 文件，使其结构更清晰，更好地遵循 “是什么 (What)” -> “为什么 (Why)” -> “怎么用 (How)” 的逻辑。我会重点阐述：

1.  **项目是什么 (What)**：清晰定义项目及其核心功能与特色。
2.  **为什么需要它 (Why)**：点明项目旨在解决的行业痛点、提供的解决方案及其适用场景。
3.  **如何使用它 (How)**：提供详尽的用户指南，涵盖环境配置、数据准备与清洗、各类图表的生成步骤（包括良率分析、参数统计、自定义图表等），以及不同操作模式（GUI图形界面、CLI命令行）的使用方法。

我将整合现有信息，进行结构调整和内容优化，确保最终的 `README.md` 文档以中文呈现，逻辑清晰、内容详实、易于理解和操作。

这是我为你准备的优化后的 `README.md` 内容：

```markdown
# 🔬 CP 数据分析工具

**半导体晶圆 CP (Chip Probing) 测试数据处理与可视化分析平台**

## 🎯 项目是什么 (What)

本工具是一个专为半导体制造业设计的 CP (Chip Probing) 测试数据分析平台，旨在提供从原始测试数据导入、智能清洗、专业分析到交互式可视化报告生成的一站式解决方案。它能够帮助工程师和数据分析师高效处理复杂的测试数据，快速洞察生产过程中的关键信息，从而优化工艺、提升良率。

## ✨ 项目特色

- 🚀 **智能数据处理**: 支持 DCP/CW/MEX 多种格式，自动识别和清洗
- 📊 **交互式图表**: 基于 Plotly 的 HTML 图表，支持缩放、悬停、导出
- 🎯 **专业分析**: 良率趋势、参数分布、批次对比、失效分析
- 🔧 **双重架构**: VBA 传统版本 + Python 现代化重构
- 📈 **参数化图表**: 自动生成参数折线图，含规格限制线和测试条件
- 🎨 **美观界面**: GUI 和命令行双模式，操作简单直观

## 🎯 适用场景

- **半导体制造**: CP 测试数据分析、良率监控
- **质量控制**: 批次对比、参数趋势分析
- **工艺优化**: 异常检测、统计过程控制
- **报告生成**: 自动化分析报告、交互式图表

## 🚀 快速开始

### 方式一：Python 版本（推荐）

```bash
# 1. 安装依赖
pip install pandas numpy plotly matplotlib seaborn openpyxl

# 2. 快速体验 - 生成交互式图表
python demo_yield_chart.py

# 3. GUI 界面
python cp_data_processor_gui.py

# 4. 命令行使用
python cp_data_processor_cli.py data.txt result.xlsx --format dcp --boxplot
```

### 方式二：VBA 宏版本

适用于 Excel 环境，运行 `A_业务流程.bas` 主宏文件即可。

## 📊 输出效果预览

生成的交互式 HTML 图表包括：
- 📈 **良率趋势图**: Wafer 良率随批次变化
- 📊 **批次对比图**: 不同批次平均良率对比
- 🔍 **参数分析图**: 自动生成所有参数的折线图，含规格限制线
- 📦 **箱体图**: 参数分布统计，异常值检测
- 🌈 **散点图**: 参数相关性分析
- 🥧 **失效分析图**: 失效类型分布饼图

## 🔧 VBA 宏版本说明

传统 Excel VBA 解决方案，功能完善，适合现有 Excel 工作流。

### 文件说明

以下是 VBA 项目中各主要文件的功能说明：

*   **`A_业务流程.bas`**: 项目的主入口和核心流程控制模块。负责协调调用其他模块完成数据读取、处理、图表生成和结果保存的整个过程。
*   **`BoxPlotChart.bas`**: 负责生成参数的箱形图 (Box Plot)。
*   **`clsRegEx.cls`**: 实现正则表达式功能的类模块，用于文本匹配和提取。
*   **`clsShowInfo.cls`**: 用于向用户显示信息、提示或错误消息的类模块。
*   **`CW格式数据采集.bas`**: 处理 "CW" 格式（可能是某种测试设备或数据标准）的原始数据文件（通常是 `.csv`）。
*   **`DCP格式数据采集.bas`**: 处理 "DCP" 格式的原始数据文件（通常是 `.txt`）。
*   **`List函数简化.bas`**: 提供简化列表或数组操作的函数。
*   **`MAP条件格式设置.bas`**: 设置 MAP 图（晶圆良率图）的条件格式。
*   **`MEX格式数据采集.bas`**: 处理 "MEX" 格式的原始数据文件（通常是 `.xls`）。
*   **`pptConst.bas`**: 包含与 PPT 操作相关的常量定义（*注意：当前逻辑主要输出到 Excel，PPT 相关功能可能已停用或为未来扩展预留*）。
*   **`Yield计算.bas`**: 包含计算晶圆良率 (Yield) 的相关函数。
*   **`参数分布统计.bas`**: 计算测试参数的统计分布信息，用于生成 Summary。
*   **`参数数值颜色图.bas`**: 生成参数值的颜色分布图 (Parameter Value Color Map)。
*   **`参数计算范围定义.bas`**: 定义需要进行计算的参数范围或条件。
*   **`合并到ppt中.bas`**: 包含将结果合并输出到 PowerPoint 文件中的功能（*注意：当前逻辑主要输出到 Excel*）。
*   **`增加运算数据.bas`**: 根据现有数据计算并添加新的衍生数据列。
*   **`工作表定义.bas`**: 定义项目中使用的 Excel 工作表名称、结构或相关常量。
*   **`散点图制作.bas`**: 负责生成参数之间的散点图 (Scatter Plot)。
*   **`数据填充到工作表.bas`**: 包含将处理后的数据填充到目标 Excel 工作表的函数。
*   **`数据类型定义.bas`**: 定义项目中使用的自定义数据类型（例如 `CPLot`, `CPWafer` 等），用于结构化地存储测试数据。
*   **`绘制MAP图.bas`**: 负责生成晶圆 MAP 图。
*   **`通用代码.bas`**: 包含项目中可复用的通用工具函数或过程。
*   **`通用数组操作函数.bas`**: 提供通用的数组处理函数，如转置、填充等。

### 业务逻辑梳理 (`A_业务流程.bas`)

宏的主要执行流程如下：

1.  **初始化 (`InitSheetSetup`)**: 初始化必要的环境或工作表设置。
2.  **获取数据格式 (`GetCPDataFormat`)**: 根据用户界面 (UI_SHEET) 的设置，判断待处理数据的格式（MEX, DCP, CW）。
3.  **选择文件 (`GetFileList`)**: 弹出文件选择对话框，让用户根据确定的数据格式选择一个或多个原始数据文件。
4.  **开始宏 (`StartMarco`)**: 记录开始时间，禁用屏幕刷新和自动计算以提高性能。
5.  **读取文件 (`ReadFile`)**:
    *   根据文件格式调用相应的打开函数 (`OpendBooks`) 打开选定的文件。
    *   获取每个文件中的数据工作表 (`GetWaferDataSheets`)。
    *   根据数据格式调用特定的解析函数（如 `SplitInfo_CWSW`, `SplitInfo_MEX`, `SplitInfo_DCP` 等，这些函数位于对应格式的 `.bas` 文件中），将原始数据解析并存入 `TestInfo` (CPLot 类型) 变量中。该变量包含了 Lot 信息、Wafer 列表、参数列表、测试数据等。
    *   关闭原始数据文件 (`CloseBooks`)。
6.  **设置检查 (`SetupCheck`)**: 检查用户在设置表中定义的参数（如增加计算数据、绘图选项等）是否与读取到的数据兼容或有效。
7.  **增加计算数据 (`AddCalData`)**: 如果用户启用了 `ADD_CAL_DATA_FLAG` 选项，则调用 `增加运算数据.bas` 中的逻辑，基于现有参数计算新的数据列并添加到 `TestInfo` 中。
8.  **创建结果工作簿 (`CreateResultBook`)**: 创建一个新的 Excel 工作簿，并根据 `SHEET_NAME_LIST` 常量添加所需的工作表（Spec, Data, Yield, Summary, Map, BoxPlot, Scatter, ParamColorChart 等）。
9.  **填充数据**:
    *   **`FillSpec`**: 将 `TestInfo` 中的参数规格 (ID, Unit, SL, SU, TestCond) 填充到 "Spec" 工作表。
    *   **`FillTestData`**: 将 `TestInfo` 中的详细测试数据 (Wafer, Seq, Bin, X, Y, ParamValues...) 填充到 "Data" 工作表。
    *   **`ShowYield`**: 计算良率，并将结果填充到 "Yield" 工作表（调用 `Yield计算.bas`）。
    *   **`mySummary`**: 计算参数统计信息，并将结果填充到 "Summary" 工作表（可能调用 `参数分布统计.bas`）。
10. **生成图表 (条件执行)**: 根据用户在设置表中勾选的标志位，选择性地生成图表：
    *   **`PlotAllParamBoxChart`**: 如果 `BOX_PLOT_FLAG` 为 True，则调用 `BoxPlotChart.bas` 中的逻辑，在 "BoxPlot" 工作表或独立图表页中生成箱形图。
    *   **`PlotAllMap`**: 如果 `BIN_MAP_PLOT_FLAG` 为 True，则调用 `绘制MAP图.bas` 中的逻辑，生成 MAP 图并放入 "Map" 工作表或独立图表页。
    *   **`PlotDataColor`**: 如果 `DATA_COLOR_PLOT_FLAG` 为 True，则调用 `参数数值颜色图.bas` 中的逻辑，生成参数颜色图并放入 "ParamColorChart" 工作表或独立图表页。
    *   **`PlotScatterChart`**: 如果 `SCATTER_PLOT_FLAG` 为 True，则调用 `散点图制作.bas` 中的逻辑，根据 `XY_SETUP_SHEET` 的配置生成散点图并放入 "Scatter" 工作表或独立图表页。
11. **保存结果 (`SaveResultBook`)**: 将包含所有数据和图表的结果工作簿保存为 `.xlsx` 文件。文件名通常包含 Lot 信息，保存在当前宏文件路径下的 "整理后的数据文件" 子目录中。
12. **结束宏 (`FinishMarco`)**: 恢复 Excel 的屏幕刷新和自动计算设置，显示处理完成的消息和所用时间。

该流程实现了从原始数据到最终分析报告（Excel 格式）的自动化处理。

## 🐍 Python 版本架构

现代化 Python 重构版本，提供更高效、模块化的数据处理能力。

### 🎯 核心优势

| 对比项 | VBA 版本 | Python 版本 |
|--------|----------|-------------|
| 🚀 **性能** | 中等 | 高效并行处理 |
| 🔧 **维护性** | 耦合度高 | 模块化设计 |
| 🌐 **跨平台** | 仅 Windows | Windows/Linux/Mac |
| 📊 **图表** | 静态 Excel 图表 | 交互式 HTML 图表 |
| 🔍 **扩展性** | 受限 | 易于扩展新功能 |
| 📦 **部署** | 需要 MS Office | 独立运行 |

### 系统架构

Python 版本采用现代化的模块化架构设计，遵循以下原则：
- **关注点分离**: 每个模块负责特定功能
- **松耦合设计**: 模块间通过明确接口交互
- **可扩展性**: 易于添加新功能和支持新数据格式
- **可测试性**: 组件易于单独测试

#### 核心架构图

```
CP数据处理器
├── 数据读取层 (readers)
├── 数据模型层 (data_models)
├── 数据处理层 (processing)
├── 数据分析层 (analysis)
├── 数据可视化层 (plotting)
├── 数据导出层 (exporters)
└── 应用层 (app/cli/main)
```

### 主要模块说明

#### 1. 数据读取模块 (readers)

负责从不同格式的文件中提取 CP 测试数据，采用工厂模式设计，支持：
- **CW 格式**: 从 CSV 文件读取 CW 格式数据
- **DCP 格式**: 从文本文件读取 DCP 格式数据 
- **MEX 格式**: 从 Excel 文件读取 MEX 格式数据

#### 2. 数据模型模块 (data_models)

定义系统中使用的核心数据结构：
- **`CPLot`**: 表示一个完整的 CP 测试批次，包含多个晶圆
- **`CPWafer`**: 表示单个晶圆的测试数据
- **`CPParameter`**: 表示测试参数的定义和规格

#### 3. 数据处理模块 (processing)

提供数据清洗、转换和增强功能：
- 异常值检测与处理
- 数据归一化和标准化
- 基于现有参数计算新参数

#### 4. 数据分析模块 (analysis)

提供统计分析和良率计算功能：
- 统计分析：计算均值、标准差、分位数等
- 良率分析：计算总体良率和按参数/晶圆的良率
- 工艺能力分析：计算 Cp、Cpk 等指标

#### 5. 数据可视化模块 (plotting)

生成各种图表，帮助直观理解数据：
- 箱形图：显示参数分布特征
- 晶圆图：显示 Bin 分布或参数分布
- 散点图：分析参数间相关性

#### 6. 数据导出模块 (exporters)

将处理和分析的结果导出为可共享的格式：
- Excel 导出：包括数据表和嵌入图表
- 结果文件组织和格式化

#### 7. 应用层模块 (app/cli/main)

提供用户界面和主流程控制：
- 图形用户界面 (GUI)：直观的操作界面
- 命令行界面 (CLI)：支持批处理和自动化
- 主流程模块 (main)：整合所有功能模块

## 📚 详细使用指南

### 🎮 GUI 界面使用

```bash
python cp_data_processor_gui.py
```

1. **选择文件**: 浏览并选择输入/输出文件
2. **配置选项**: 选择数据格式（DCP/CW/MEX）和圆片类型
3. **图表选项**: 勾选需要的分析图表
4. **开始处理**: 点击"整理数据"按钮

### ⌨️ 命令行使用

```bash
# 基本语法
python cp_data_processor_cli.py <输入文件> <输出文件> [选项]

# 常用示例
python cp_data_processor_cli.py data.txt result.xlsx --format dcp --boxplot --bin-map
python cp_data_processor_cli.py data.csv result.xlsx --format cw --boxplot --scatter
```

**常用参数:**
- `--format {dcp,cw,mex}`: 输入文件格式
- `--boxplot`: 生成箱形图
- `--scatter`: 生成散点图  
- `--bin-map`: 生成晶圆图
- `--data-map`: 生成数据颜色图

### 🔬 交互式图表生成

```bash
python demo_yield_chart.py

# 详细测试
python test_yield_chart.py

# 自定义箱体图
python test_boxplot.py
```

## 🗂️ 输出文件说明

### 📁 目录结构

```
demo_output/                 # 主输出目录
├── all_charts/             # 所有图表 HTML 文件
│   ├── Wafer良率趋势分析_yield_chart.html
│   ├── BVDSS1[V]@250uA_yield_line_chart.html
│   └── ...
├── generated_charts/       # 自定义生成的图表
└── detailed_analysis/      # 详细分析结果

output/                     # 数据处理输出
├── NCETSG7120BAA_yield_*.csv    # 良率数据
├── NCETSG7120BAA_spec_*.csv     # 规格数据
└── NCETSG7120BAA_cleaned_*.csv  # 清洗数据
```

### 📈 图表类型说明

| 图表类型 | 文件名格式 | 功能说明 |
|---------|-----------|----------|
| 📈 良率趋势图 | `Wafer良率趋势分析_yield_chart.html` | 显示批次内 Wafer 良率变化 |
| 📊 批次对比图 | `批次良率对比分析_yield_chart.html` | 不同批次平均良率对比 |
| 🔍 参数折线图 | `参数[单位]@测试条件_yield_line_chart.html` | 参数值变化趋势 + 规格线 |
| 📦 箱体图 | `参数_boxplot.html` | 参数分布统计 + 异常值检测 |
| 🌈 散点图 | `参数1_vs_参数2_scatter.html` | 参数间相关性分析 |

## 🚀 进阶功能

### 🎯 数据处理流程

```bash
# 1. 数据清洗
python clean_dcp_data.py          # 清洗 DCP 数据
python dcp_spec_extractor.py      # 提取规格信息

# 2. 生成分析图表
python demo_yield_chart.py        # 良率分析
python test_boxplot.py           # 参数统计分析

# 3. 批量处理
python cp_data_processor_cli.py --format dcp --boxplot --bin-map
```

### 🔧 自定义开发

```python
# 使用 YieldChart API
from frontend.charts.yield_chart import YieldChart

chart = YieldChart(data_dir="output")
chart.load_data()
params = chart.get_available_parameters()
chart.save_all_charts(output_dir="custom_output")
```

## 📞 技术支持

- 📖 **详细文档**: [readme-main.md](./readme-main.md)
- 🐛 **问题反馈**: 通过 GitHub Issues
- 💡 **快速体验**: `python demo_yield_chart.py`

---

## 📊 详细操作手册

### 🏗️ 数据准备要求

系统支持三种数据文件类型，需放置在同一目录：

| 数据类型 | 文件命名格式 | 功能说明 |
|---------|-------------|----------|
| 📈 **Yield数据** | `*_yield_*.csv` | 包含良率信息、失效统计 |
| 📋 **Spec数据** | `*_spec_*.csv` | 参数规格、单位、上下限 |
| 🔧 **Cleaned数据** | `*_cleaned_*.csv` | 清洗后的测试参数数据 |

### 📋 完整操作流程

#### 第一步：数据清洗和准备

1. **清洗原始DCP数据**
   ```bash
   python clean_dcp_data.py
   ```
   
2. **清洗原始CSV数据**（如果有）
   ```bash
   python clean_csv_data.py
   ```

3. **提取规格信息**
   ```bash
   python dcp_spec_extractor.py
   ```

完成后，在`output/`目录下会生成：
- `NCETSG7120BAA_yield_20240101.csv` - 良率数据
- `NCETSG7120BAA_spec_20240101.csv` - 规格数据  
- `NCETSG7120BAA_cleaned_20240101.csv` - 清洗数据

#### 第二步：生成交互式图表

数据准备完成后，即可生成各类分析图表。

**A. 标准良率与参数分析图表 (推荐)**
使用 `demo_yield_chart.py` 脚本，它可以一次性生成一套全面的分析图表，包括：
- Wafer 良率趋势分析 (各 Wafer 良率变化，按批次组织)
- 批次良率对比分析 (不同批次平均良率对比)
- 良率分布统计
- 失效类型分析饼图
- 各参数的折线图 (自动叠加规格线和测试条件，例如 `BVDSS[V]@10uA_yield_line_chart.html`)

```bash
python demo_yield_chart.py
```
生成的 HTML 图表默认保存在 `demo_output/all_charts/` 目录。

**B. 参数统计特性图表 (箱体图与散点图)**
若需关注参数的分布特性、异常值检测及参数间的相关性，可使用：
```bash
python test_boxplot.py
```
此脚本通常会生成：
- 各参数的箱体图 (Box Plot)，展示分布情况。
- 可选的参数间散点图 (Scatter Plot)，分析相关性。
图表输出位置可能在 `demo_output/generated_charts/custom_plotly_express_charts/` 或类似路径。

**C. 自定义图表生成**
对于更高级的定制化图表需求，可以使用 `generate_custom_charts.py`：
```bash
python generate_custom_charts.py
```
你需要确保 `generate_custom_charts.py` 脚本中配置的数据输入目录 (`data_input_dir`) 指向包含上述三类 CSV 文件的正确位置。
该脚本会调用 `YieldChart` 类及 Plotly Express 直接生成图表，输出通常在：
- `demo_output/generated_charts/yield_chart_outputs/` (通过 `YieldChart` 生成的图表)
- `demo_output/generated_charts/custom_plotly_express_charts/` (直接用 Plotly Express 生成的箱体图等)

#### 第三步：操作模式

除了直接运行 Python 脚本，还可以通过以下方式使用本工具：

**A. 图形用户界面 (GUI)**
为方便不熟悉命令行的用户，提供了基于 PyQt5 的图形界面：
```bash
python cp_data_processor_gui.py
```
通过 GUI，你可以：
1.  选择输入数据文件或目录。
2.  配置数据格式 (DCP/CW/MEX) 和分析选项。
3.  勾选需要生成的图表类型。
4.  点击按钮开始处理并生成报告。

**B. 命令行工具 (CLI)**
对于批量处理和自动化任务，命令行工具是更高效的选择：
```bash
# 基本语法
python cp_data_processor_cli.py <输入文件或目录> <输出目录或文件前缀> [选项]

# 示例：处理单个DCP文件，并生成箱体图和Bin Map
python cp_data_processor_cli.py data/NCETSG7120BAA_FA54-5339@203/FA54-5339@203.txt processed_data --format dcp --boxplot --bin-map

# 示例：处理目录下的所有CW格式数据，并生成散点图
python cp_data_processor_cli.py data_folder/ results/ --format cw --scatter
```
**常用参数:**
- `--format {dcp,cw,mex}`: 指定输入文件格式。
- `--boxplot`: 生成参数箱体图。
- `--scatter`: 生成参数散点图。
- `--bin-map`: 生成晶圆 Bin Map 图。
- `--data-map`: 生成参数值在晶圆上的颜色分布图。
- 更多参数请使用 `python cp_data_processor_cli.py --help` 查看。

**C. API 方式自定义开发 (高级)**
项目的核心功能被封装在各个模块中，可以直接在自己的 Python 脚本中调用。例如，使用 `YieldChart` 类进行图表生成：
```python
from frontend.charts.yield_chart import YieldChart
from pathlib import Path

# 指定包含 _yield_*.csv, _spec_*.csv, _cleaned_*.csv 的数据目录
data_dir = Path("output")
output_dir = Path("custom_charts_output")
output_dir.mkdir(parents=True, exist_ok=True)

# 创建分析实例并加载数据
chart_analyzer = YieldChart(data_dir=data_dir)
chart_analyzer.load_data()

# 获取可分析的参数列表
# available_params = chart_analyzer.get_available_parameters()
# print(f"Available parameters: {available_params}")

# 生成并保存所有标准图表
saved_files = chart_analyzer.save_all_charts(output_dir=output_dir)
print(f"Successfully generated {len(saved_files)} charts in {output_dir}")

# 生成特定参数的图表
# fig = chart_analyzer.get_chart(chart_type=f"param_{available_params[0]}") # Example for first parameter
# if fig:
#     chart_analyzer.save_chart(chart_type=f"param_{available_params[0]}", output_dir=output_dir)
```

#### 批量分析多个批次

```python
# 批量生成所有图表
saved_paths = chart.save_all_charts(output_dir="batch_analysis")
print(f"成功生成 {len(saved_paths)} 个图表")
```

#### 箱体图详细分析

```python
from frontend.charts.boxplot_chart import BoxplotChart

# 创建箱体图分析
chart = BoxplotChart(data_dir="output")
chart.load_data()

# 获取可用参数
params = chart.get_available_parameters()

# 生成特定参数的箱体图
fig = chart.create_boxplot_scatter_chart("BVDSS1")
chart.save_chart("BVDSS1", output_dir="boxplot_analysis")
```

### 📊 图表类型详解

#### 良率分析图表

| 图表类型 | 功能说明 | 适用场景 |
|---------|----------|----------|
| Wafer良率趋势图 | 显示各批次wafer良率随wafer编号变化 | 监控生产稳定性 |
| 批次良率对比图 | 对比不同批次的平均良率和标准差 | 批次间质量对比 |
| 良率分布统计 | 显示所有wafer良率的分布直方图 | 良率分布分析 |
| 失效类型分析 | 分析各种失效bin的分布情况 | 失效模式分析 |
| 参数折线图 | 基于cleaned数据的参数测试结果 | 参数趋势分析 |

#### 参数统计图表

| 图表类型 | 功能说明 | 适用场景 |
|---------|----------|----------|
| 箱体图+散点图 | 显示参数分布特征和异常值 | 参数质量分析 |
| 双层X轴设计 | 上层Wafer编号，下层批次信息 | 多维度数据查看 |
| 规格限制线 | 自动显示参数上下限 | 规格符合性检查 |

### 🔧 高级配置

#### 自定义图表样式

```python
# 修改图表配置
chart.chart_config.update({
    'height': 800,                    # 图表高度
    'font_size': 14,                  # 字体大小
    'colors': ['#FF6B6B', '#4ECDC4', '#45B7D1'],  # 自定义颜色
    'min_chart_width': 1400,          # 最小图表宽度
    'pixels_per_wafer': 50,           # 每个wafer分配的像素
})
```

#### 数据过滤和筛选

```python
# 过滤特定批次
chart_data = chart.wafer_data[chart.wafer_data['Lot_Short'] == 'FA54-5339']

# 过滤特定良率范围
high_yield_data = chart.wafer_data[chart.wafer_data['Yield_Numeric'] > 98.0]
```

### 🐛 常见问题解决

#### 数据加载失败

**问题**: 提示"数据加载失败"
**解决方案**:
1. 检查`output/`目录是否存在数据文件
2. 确认文件命名格式正确：`*_yield_*.csv`, `*_spec_*.csv`, `*_cleaned_*.csv`
3. 验证CSV文件编码为UTF-8

#### 参数图表生成失败

**问题**: 参数折线图不显示或显示异常
**解决方案**:
1. 确认存在spec数据文件
2. 检查参数名在spec和cleaned数据中都存在
3. 验证规格数据格式正确

#### 图表显示问题

**问题**: HTML图表在浏览器中显示异常
**解决方案**:
1. 使用现代浏览器（Chrome、Firefox、Edge）
2. 检查网络连接（Plotly可能需要加载在线资源）
3. 确认HTML文件完整且未损坏

### 📈 性能优化建议

#### 大数据集处理

```python
# 对于大数据集，建议分批处理
chart_types = chart.get_available_chart_types()
basic_charts = [ct for ct in chart_types if not ct.startswith('param_')]

# 先生成基础图表
for chart_type in basic_charts:
    chart.save_chart(chart_type, output_dir="output_batch1")

# 再分批生成参数图表
params = chart.get_available_parameters()
for i in range(0, len(params), 5):  # 每次处理5个参数
    batch_params = params[i:i+5]
    for param in batch_params:
        chart_type = f"param_{param}"
        chart.save_chart(chart_type, output_dir=f"output_batch_{i//5+2}")
```

#### 内存管理

```python
# 清理缓存
chart.all_charts_cache.clear()

# 重新加载数据
chart.load_data()
```

### 🎉 最佳实践

1. **数据组织**: 保持数据文件命名规范，统一存放在`output/`目录
2. **图表管理**: 按批次或日期创建不同的输出目录
3. **质量检查**: 生成图表后及时检查数据完整性和图表正确性
4. **文档记录**: 保存关键参数的分析结果和异常发现
5. **版本控制**: 对重要的数据分析结果进行版本备份

### 📞 技术支持

如需更多帮助，请参考：
- 详细API文档：`frontend/charts/yield_chart.md`
- 测试示例：运行`python test_yield_chart.py`
- 问题反馈：通过项目Issue系统报告问题

---

> 💡 **提示**: 建议先运行`python demo_yield_chart.py`快速体验功能，然后根据具体需求进行定制化分析。

## 🎯 自定义图表生成（高级）

使用 `generate_custom_charts.py` 脚本生成专业级分析图表：

### 📁 数据文件格式

将以下三类 CSV 文件放在同一目录（如 `output/` 或 `input_data/`）：

| 数据类型 | 文件名格式 | 必需列 | 说明 |
|---------|-----------|-------|------|
| **良率数据** | `*_yield_*.csv` | `Lot_ID`, `Wafer_ID`, `Yield` | 良率百分比（如 `99.8%`） |
| **规格数据** | `*_spec_*.csv` | `Parameter`, `Unit`, `LimitU`, `LimitL` | 参数规格限制 |
| **测试数据** | `*_cleaned_*.csv` | `Lot_ID`, `Wafer_ID`, 参数列 | 清洗后的参数数值 |

### 🚀 运行自定义脚本

```bash
# 1. 运行自定义图表生成器
python generate_custom_charts.py

# 2. 查看输出目录
# demo_output/generated_charts/
#   ├── yield_chart_outputs/        # YieldChart 内置图表
#   └── custom_plotly_express_charts/ # 自定义箱体图+散点图
```

### 📊 生成的图表类型

**YieldChart 内置图表:**
- 📈 `Wafer良率趋势分析_yield_chart.html` - 良率趋势
- 📊 `批次良率对比分析_yield_chart.html` - 批次对比  
- 🔍 `参数[单位]@测试条件_yield_line_chart.html` - 参数折线图
- 📦 `良率分布统计_yield_chart.html` - 良率分布
- 🥧 `失效类型分析_yield_chart.html` - 失效分析

**自定义 Plotly Express 图表:**
- 📦 `参数_boxplot.html` - 参数箱体图（按批次分组）
- 🌈 `参数1_vs_参数2_scatter.html` - 参数相关性散点图

### ⚙️ 自定义配置

编辑 `generate_custom_charts.py` 中的数据路径：

```python
# 修改数据输入目录
data_input_dir = Path("output")          # 使用默认 output 目录
# data_input_dir = Path("input_data")    # 或自定义目录
```