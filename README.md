
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

### 核心功能
- 🔢 **多格式数据兼容**: 支持 DCP, CW, MEX 等主流 CP 测试数据格式的自动解析与处理。
- 🧹 **智能数据清洗**: 内置算法自动识别和处理异常值、缺失数据，确保分析结果的准确性。
- 📊 **专业图表分析**: 生成符合行业标准的分析图表，如良率趋势图、参数分布箱体图、晶圆 MAP 图、参数对比散点图等。
- 💻 **交互式可视化**: 所有图表均基于 Plotly 生成，支持交互式操作（缩放、平移、悬停提示、数据点选择）并可导出为 HTML 文件。
- ⚙️ **参数化与自动化**: 自动生成各参数的趋势图，并叠加规格线 (Spec Limit) 和测试条件信息。支持批量处理多文件、多批次数据。
- 🛠️ **灵活操作模式**: 提供图形用户界面 (GUI)、命令行工具 (CLI) 及 Python API 调用三种使用方式，满足不同用户需求。

### 项目特色
- ✅ **一站式平台**: 从数据导入到报告导出，全程在统一平台完成，简化工作流程。
- ✅ **深度定制**: 针对半导体 CP 测试特点进行优化，图表和分析逻辑更贴合实际应用。
- ✅ **易于扩展**: 模块化设计，方便未来添加新的数据格式支持、分析算法或图表类型。
- ✅ **现代化架构**: Python 版本采用现代化技术栈，性能更优，跨平台性更好。

## 💡 为什么需要这个项目 (Why)

在半导体制造过程中，CP 测试产生了海量的关键数据。然而，工程师们常常面临以下挑战：

### 行业痛点
1.  **数据格式繁杂**: 不同测试设备或流程产生的数据格式（如 DCP, CW, MEX）不统一，增加了数据整合难度。
2.  **分析工具匮乏**: 缺乏专为 CP 数据设计的、集数据处理与高级可视化于一体的便捷工具。
3.  **手动处理低效**: 传统依赖 Excel 等工具手动处理数据，不仅耗时耗力，还容易引入人为错误。
4.  **可视化交互性差**: 静态图表难以进行深度数据探索和多维度分析。

### 解决方案
本工具通过以下方式解决上述痛点：
- 🔄 **统一数据接口**: 提供统一的数据处理流程，兼容多种主流 CP 测试数据格式。
- 📈 **专业分析能力**: 内置针对性的分析模块和可视化图表，如良率分析、参数统计、失效模式分析等。
- ⚡ **自动化处理**: 大幅减少手动操作，实现数据清洗、计算、图表生成的自动化，提升工作效率。
- 🌐 **交互式探索**: 生成的 HTML 图表具有丰富的交互功能，便于用户深入挖掘数据背后的信息。

### 适用场景
| 应用领域     | 具体用途                                     | 价值体现             |
| :----------- | :------------------------------------------- | :------------------- |
| **半导体制造** | CP 测试数据分析、良率监控、WAT 数据分析        | 提升产品质量、快速定位问题 |
| **质量控制**   | 批次间参数稳定性对比、参数趋势监控、异常值检测 | 保证产品一致性、及时预警 |
| **工艺优化**   | 工艺变更前后数据对比、参数与良率相关性分析   | 指导工艺改进、优化参数 |
| **工程报告**   | 自动化生成标准分析报告、交互式数据分享         | 提高工程师工作效率     |

## 🚀 如何使用 (How)

本项目主要推荐使用 Python 版本，它功能更强大、灵活且易于维护。

### 1. 环境准备与快速上手

**安装依赖:**
确保你的 Python 环境已安装以下基础库：
```bash
pip install pandas numpy plotly openpyxl
```
对于更复杂的可视化或特定功能，可能需要 `matplotlib`, `seaborn` 等。

**快速体验 (生成核心分析图表):**
项目内置了演示脚本，可以快速生成一套完整的分析图表。
```bash
python demo_yield_chart.py
```
执行完毕后，相关的 HTML 图表将保存在 `demo_output/all_charts/` 目录下。

### 2. 详细使用流程

#### 第一步：数据准备与清洗

**数据文件要求:**
为了顺利进行分析，你需要准备以下三类 CSV 文件，并将它们放置在同一个数据输入目录中（默认为 `output/`，也可在脚本中指定其他目录）：

| 数据类型     | 文件命名约定 (示例)                  | 必需列 (部分)                                  | 说明                                   |
| :----------- | :----------------------------------- | :--------------------------------------------- | :------------------------------------- |
| 📈 **良率数据** | `*_yield_*.csv` (e.g., `LOTID_yield_DATE.csv`) | `Lot_ID`, `Wafer_ID`, `Yield` (百分比格式) | 包含每个 Wafer 的良率信息、失效 Die 统计等 |
| 📋 **规格数据** | `*_spec_*.csv` (e.g., `LOTID_spec_DATE.csv`)  | `Parameter`, `Unit`, `LimitU`, `LimitL`, `TestCond` | 定义各测试参数的名称、单位、规格上下限、测试条件 |
| 🔧 **清洗后数据** | `*_cleaned_*.csv` (e.g., `LOTID_cleaned_DATE.csv`) | `Lot_ID`, `Wafer_ID`, 及各参数列         | 经过清洗和预处理的详细 Die-Level 测试数据 |

**数据清洗与提取:**
如果只有原始的 DCP, CSV 等格式数据，需要先进行清洗和规格提取：

1.  **清洗原始 DCP 数据** (通常为 `.txt` 文件):
    ```bash
    python clean_dcp_data.py
    ```
    此脚本会处理 DCP 文件，生成初步的 `*_cleaned_*.csv` 和可能的 `*_yield_*.csv`。

2.  **清洗原始 CSV 数据** (如果适用):
    ```bash
    python clean_csv_data.py
    ```

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

### 3. 输出结果说明

**主要输出目录结构示例:**
```
output/                     # 清洗后的数据和规格文件
├── LOTID_yield_DATE.csv
├── LOTID_spec_DATE.csv
└── LOTID_cleaned_DATE.csv

demo_output/                # 运行演示脚本产生的图表
├── all_charts/             # demo_yield_chart.py 生成的图表
│   ├── Wafer良率趋势分析_yield_chart.html
│   ├── 参数名[单位]@测试条件_yield_line_chart.html
│   └── ...
└── generated_charts/       # generate_custom_charts.py 生成的图表
    ├── yield_chart_outputs/
    └── custom_plotly_express_charts/
        ├── 参数名_boxplot.html
```

**主要图表类型说明:**

| 图表类型                 | 文件名示意 (部分)                                | 功能说明                                     |
| :----------------------- | :----------------------------------------------- | :------------------------------------------- |
| 📈 **Wafer 良率趋势图**   | `Wafer良率趋势分析_yield_chart.html`                 | 显示同一批次内或跨批次各 Wafer 良率的变化趋势        |
| 📊 **批次良率对比图**   | `批次良率对比分析_yield_chart.html`                 | 对比不同批次的平均良率、中位数、分布等         |
| 📉 **参数折线图**       | `参数名[单位]@测试条件_yield_line_chart.html`       | 显示特定参数在各 Die 上的值，叠加规格线，按 Wafer 分组 |
| 📦 **参数箱体图**       | `参数名_boxplot.html`                            | 展示参数的统计分布（中位数、四分位数、异常值）    |
| 🗺️ **晶圆 Bin Map 图**   | (通常由 CLI 或 GUI 生成，非固定文件名)              | 在晶圆物理位置上用颜色标记不同的 Bin 值        |
| 🧪 **参数数据 Map 图**   | (通常由 CLI 或 GUI 生成，非固定文件名)              | 在晶圆物理位置上用颜色深浅表示参数值大小       |
| 📉 **良率分布统计图**   | `良率分布统计_yield_chart.html`                   | 所有 Wafer 良率值的直方图或核密度估计图        |
| 🥧 **失效类型分析图**   | `失效类型分析_yield_chart.html`                   | 展示不同失效 Bin Code 的占比                 |
| ✨ **参数散点图**       | `参数1_vs_参数2_scatter.html` (若生成)          | 分析两个参数之间的相关性                       |

所有 HTML 图表均支持交互式操作。

## 🐍 Python 版本架构概述

Python 版本采用模块化设计，主要包括：
- **数据读取层 (`readers`)**: 负责解析不同格式的原始数据。
- **数据模型层 (`data_models`)**: 定义核心数据结构如 `CPLot`, `CPWafer`。
- **数据处理层 (`processing`)**: 实现数据清洗、转换、计算等。
- **数据分析层 (`analysis`)**: 执行统计分析、良率计算等。
- **数据可视化层 (`plotting` / `frontend.charts`)**: 生成各类交互式图表。
- **数据导出层 (`exporters`)**: 将结果保存为文件。
- **应用层 (`cp_data_processor_cli.py`, `cp_data_processor_gui.py`, demo 脚本等)**: 提供用户接口和主流程控制。

这种分层架构使得系统更易于维护、扩展和测试。

## 🔧 VBA 宏版本说明 (可选)

本项目亦包含一个传统的 Excel VBA 解决方案，对于习惯在 Excel 环境下工作的用户，它提供了一套完整的功能。
详细的 VBA 文件说明和业务逻辑梳理请参见原 README 的 "VBA 宏版本说明" 部分（此处为保持 Python 版本为主的简洁性而略过，但原始信息仍然有价值）。

## 📞 技术支持与贡献

- 📖 **详细文档**: 本 README 文件。部分模块可能有更详细的 Markdown 文档（如 `frontend/charts/yield_chart.md`）。
- 🐛 **问题反馈**: 建议通过项目的 GitHub Issues (如果项目已开源) 或其他指定渠道反馈问题。
- 💡 **快速体验**: 再次推荐运行 `python demo_yield_chart.py` 来快速了解核心功能。

欢迎对本项目提出改进建议或参与贡献！
```
