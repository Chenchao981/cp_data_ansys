# CP 数据处理工具

本项目包含两部分：
1. 原始 VBA 宏版本：用于处理半导体晶圆制造过程中的 CP (Chip Probing) 测试数据
2. Python 重构版本：提供更高效、模块化和可扩展的数据处理解决方案

## VBA 宏版本说明

VBA 宏版本主要功能包括读取不同格式的原始测试数据，进行数据清洗和整理，计算良率 (Yield) 和其他统计参数，并生成多种分析图表（如 BoxPlot、MAP 图、散点图等），最终将处理结果保存到 Excel 文件中。

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

## Python 版本介绍

Python 版本是对原始 VBA 宏的重构，旨在提供更模块化、可扩展和高效的解决方案，同时保持相同的业务功能。

### 重构背景

原始程序基于 Excel VBA 实现，存在以下问题：
1. 代码维护困难，各模块耦合度高
2. 脚本执行效率低，难以处理大量数据
3. 跨平台支持困难，依赖 Windows 和 MS Office

通过使用 Python 重构，我们提供了一个模块化、可扩展、高效且跨平台的解决方案。

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

### 使用说明

#### 依赖项安装

```bash
pip install numpy pandas matplotlib seaborn tkinter openpyxl
```

#### 图形界面使用

1. 运行图形界面程序：

```bash
python cp_data_processor_gui.py
```

2. 在界面中完成配置：
   - 选择输入文件和输出文件
   - 选择测试类型（DCP、CW或MEX格式）和圆片类型
   - 勾选需要的图表选项（箱形图、晶圆图等）

3. 点击"整理数据"按钮开始处理

#### 命令行使用

基本语法：

```bash
python cp_data_processor_cli.py <输入文件> <输出文件> [选项]
```

常用选项：

- `--format, -f {dcp,cw,mex}`: 指定输入文件格式
- `--wafer-type, -w {normal,mpw}`: 指定圆片类型
- `--boxplot`: 生成箱形图
- `--fact-info`: 包含Fact信息
- `--scatter`: 生成散点图
- `--bin-map`: 生成晶圆Bin图
- `--data-map`: 生成数据颜色图
- `--add-calc`: 添加计算数据

示例：

```bash
# 处理DCP格式文件，生成箱形图和晶圆图
python cp_data_processor_cli.py data.txt result.xlsx --format dcp --boxplot --bin-map

# 处理CW格式文件，生成所有类型的图表
python cp_data_processor_cli.py data.csv result.xlsx --format cw --boxplot --scatter --bin-map --data-map --add-calc
```

### 模块示例

以 MAP 格式化器模块为例，它提供了晶圆 MAP 数据的可视化功能：

```bash
python cp_data_processor/examples/map_formatter_example.py
```

### 后续计划

1. **性能优化**：
   - 支持大数据集并行处理
   - 优化内存使用
   - 改进算法效率

2. **功能拓展**：
   - 添加更多数据分析指标
   - 支持更多图表类型
   - 增强导出功能

3. **用户体验改进**：
   - 优化界面设计
   - 添加处理进度显示
   - 改进错误提示

### 更多文档

有关详细的开发文档和模块说明，请参阅 [readme-main.md](./readme-main.md)。