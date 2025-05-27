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

## 📊 数据分析操作手册

本章节详细介绍如何使用新的图表生成功能分析CP测试数据，包括数据清洗、良率分析和交互式图表生成。

### 🚀 快速开始

#### 环境要求

确保已安装必要的Python包：

```bash
pip install pandas numpy plotly matplotlib seaborn openpyxl
```

#### 数据准备

系统支持三种数据文件类型：
- **Yield数据**: `*_yield_*.csv` - 包含良率信息
- **Spec数据**: `*_spec_*.csv` - 包含参数规格、单位、上下限
- **Cleaned数据**: `*_cleaned_*.csv` - 包含清洗后的测试参数数据

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

##### 🏭 良率分析图表（推荐）

生成完整的良率分析HTML图表：

```bash
# 快速演示
python demo_yield_chart.py

# 详细测试
python test_yield_chart.py
```

**输出内容：**
- 📈 Wafer良率趋势分析
- 📊 批次良率对比分析
- 📊 良率分布统计
- 🔍 失效类型分析
- 🔬 参数折线图（支持CONT、IGSS0、IGSS1、BVDSS1等所有参数）

**特色功能：**
- ✅ 交互式HTML图表，可缩放、悬停查看详情
- ✅ 双层X轴：上层显示Wafer编号，下层显示批次信息
- ✅ 自动规格限制线：显示参数上下限
- ✅ 参数化标题：格式为`参数[单位]@测试条件_yield_line_chart`
- ✅ 批次分组显示，不同颜色区分

##### 📦 箱体图+散点图分析

生成参数统计分析图表：

```bash
# 快速演示
python test_boxplot.py
```

**输出内容：**
- 📊 参数箱体图+散点图组合
- 📈 参数分布统计分析
- 🔍 异常值检测和标注

#### 第三步：图表文件管理

生成的HTML图表保存在以下目录：

```
demo_output/              # 演示输出目录
├── all_charts/          # 所有图表
│   ├── Wafer良率趋势分析_yield_chart.html
│   ├── 批次良率对比分析_yield_chart.html
│   ├── BVDSS1[V]@250uA_yield_line_chart.html
│   └── ...
└── detailed_analysis/   # 详细分析

test_charts/             # 测试输出目录
├── yield/              # 良率图表
├── yield_batch/        # 批量生成
└── yield_detailed/     # 详细分析
```

### 🎯 专业级图表生成

#### 自定义参数分析

```python
from frontend.charts.yield_chart import YieldChart

# 创建分析实例
chart = YieldChart(data_dir="output")
chart.load_data()

# 获取可用参数
params = chart.get_available_parameters()
print(f"可用参数: {params}")

# 分析特定参数
param_info = chart.get_parameter_info("BVDSS1")
print(f"参数信息: {param_info}")

# 生成特定参数图表
chart_type = "param_BVDSS1"
fig = chart.get_chart(chart_type)
chart.save_chart(chart_type, output_dir="custom_analysis")
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

## 使用 YieldChart 和 Plotly Express 生成和分析图表

本节将指导您如何使用 `frontend.charts.yield_chart.YieldChart` 类结合 `plotly.express` 来加载数据、生成各种分析图表并保存为 HTML 文件。

### 1. 准备数据

在进行分析之前，您需要准备以下三种类型的 CSV 文件，并将它们放置在同一个数据目录中（例如，项目根目录下的 `input_data` 文件夹，您可以自行创建）：

*   **良率数据 (Yield Data)**：
    *   文件名应包含 `_yield_`，例如 `YOUR_BATCH_ID_yield_summary.csv`。
    *   此文件应包含每个晶圆 (Wafer) 的良率信息以及可能的批次 (Lot) 汇总信息。
    *   关键列（列名需精确匹配）：
        *   `Lot_ID`: 批次和晶圆的唯一标识符（例如，`NCETXXX_FA54-1234@203_W01` 表示批次 `NCETXXX_FA54-1234@203` 中的 `W01` 晶圆；汇总行可以用 `ALL` 表示 `Lot_ID`）。
        *   `Wafer_ID`: 晶圆编号（例如 `1`, `2`, `01`, `25`）。
        *   `Yield`: 良率百分比，字符串格式，带 `%` 号（例如 `98.5%`）。
        *   `Bin3`, `Bin4`, `Bin6`, `Bin7`, `Bin8`, `Bin9`: (可选) 不同失效类型的芯片数量，用于生成失效分析图。
    *   示例 (`NCETXXX_FA54-1234_yield_summary.csv`):
        ```csv
        Lot_ID,Wafer_ID,Site,Yield,Bin3,Bin4,Bin5,Bin6,Bin7,Bin8,Bin9
        NCETXXX_FA54-1234@203_W01,1,1,99.8%,0,1,0,0,0,0,0
        NCETXXX_FA54-1234@203_W02,2,1,99.5%,1,0,0,0,0,0,0
        ...
        ALL,ALL,1,99.65%,10,5,0,2,0,0,0
        ```

*   **规格数据 (Spec Data)**：
    *   文件名应包含 `_spec_`，例如 `YOUR_BATCH_ID_spec_limits.csv`。
    *   此文件定义了各个测试参数的规格信息，如单位、上下限、测试条件等。
    *   第一列通常是参数属性的描述（例如 `Parameter`, `Unit`, `LimitU`, `LimitL`, `TestCond:`），后续列是具体的参数名。
    *   `YieldChart` 会读取此文件以获取参数的额外信息，并用于参数折线图的标题和规格线。
    *   示例 (`NCETXXX_FA54-1234_spec_limits.csv`):
        ```csv
        Parameter,ParamA,ParamB,ParamC
        Unit,mV,uA,Ohm
        LimitU,100,50,10
        LimitL,90,40,8
        TestCond:,Vcc=3.3V,Temp=25C,Iload=1mA
        ```

*   **清洗后的参数数据 (Cleaned Data)**：
    *   文件名应包含 `_cleaned_`，例如 `YOUR_BATCH_ID_cleaned_data.csv`。
    *   此文件包含每个芯片的详细测试参数值，经过了初步清洗。
    *   `YieldChart` 使用此数据生成参数折线图。`plotly.express` 也将使用此数据生成箱体图和散点图。
    *   关键列（列名需精确匹配）：
        *   `Lot_ID`: 批次和晶圆的唯一标识符 (格式同良率数据)。
        *   `Wafer_ID`: 晶圆编号。
        *   `X`, `Y`: (可选) 芯片在晶圆上的坐标。
        *   `Bin`: (可选) 芯片的 Bin 值。
        *   其他列：每个测试参数的名称及其对应的数值 (例如 `ParamA`, `ParamB`, ...)。
    *   示例 (`NCETXXX_FA54-1234_cleaned_data.csv`):
        ```csv
        Lot_ID,Wafer_ID,X,Y,Bin,ParamA,ParamB,ParamC
        NCETXXX_FA54-1234@203_W01,1,0,0,1,95.5,45.1,8.8
        NCETXXX_FA54-1234@203_W01,1,0,1,1,96.0,45.3,8.9
        ...
        NCETXXX_FA54-1234@203_W25,25,10,10,3,105.0,55.0,10.5
        ```

将这三类文件准备好并放入您指定的数据目录。

### 2. 运行示例脚本生成图表

我们提供一个示例脚本 `generate_custom_charts.py` (您可以创建此文件)，它演示了如何使用 `YieldChart` 和 `plotly.express`。

**`generate_custom_charts.py` 内容如下：**

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from pathlib import Path
import plotly.express as px
import pandas as pd

# 导入 YieldChart 类 - 确保您的 PYTHONPATH 包含项目根目录
# 或者根据您的项目结构调整导入路径
from frontend.charts.yield_chart import YieldChart

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # 1. 配置数据目录和输出目录
    #    请确保将 "your_data_directory" 替换为您实际存放CSV文件的目录路径。
    #    例如：data_input_dir = Path("cp_data_ansys/data/NCETSG7120BAA_FA54-5339@203")
    #    或者在项目根目录创建 "input_data" 文件夹并放入数据文件。
    data_input_dir = Path("input_data") # <<--- 修改这里：指向您的CSV数据文件夹
    charts_output_dir = Path("demo_output/generated_charts") # 所有图表将保存在这里
    charts_output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"数据输入目录: {data_input_dir.resolve()}")
    logger.info(f"图表输出目录: {charts_output_dir.resolve()}")

    # 2. 初始化 YieldChart 并加载数据
    #    YieldChart 会自动从 data_input_dir 查找 *_yield_*.csv, *_spec_*.csv, *_cleaned_*.csv 文件
    yield_analyzer = YieldChart(data_dir=str(data_input_dir))
    
    if not yield_analyzer.load_data():
        logger.error("数据加载失败，请检查数据文件是否存在且格式正确。")
        return

    logger.info("数据加载成功。")

    # 3. 生成并保存 YieldChart 内置的图表
    logger.info("开始生成并保存 YieldChart 内置图表...")
    saved_yield_charts = yield_analyzer.save_all_charts(output_dir=str(charts_output_dir / "yield_chart_outputs"))
    if saved_yield_charts:
        logger.info(f"YieldChart 内置图表已保存到: {charts_output_dir / 'yield_chart_outputs'}")
        for chart_path in saved_yield_charts:
            logger.info(f"  - {chart_path.name}")
    else:
        logger.warning("未能保存任何 YieldChart 内置图表。")

    # 4. 使用 Plotly Express 生成额外的参数箱体图和散点图
    #    我们将使用从 YieldChart 加载的 cleaned_data。
    cleaned_df = yield_analyzer.cleaned_data
    
    if cleaned_df is None or cleaned_df.empty:
        logger.warning("Cleaned data 未加载或为空，无法生成箱体图和散点图。")
    else:
        logger.info("开始生成自定义箱体图和散点图...")
        custom_charts_output_dir = charts_output_dir / "custom_plotly_express_charts"
        custom_charts_output_dir.mkdir(parents=True, exist_ok=True)

        # 获取可用于绘图的参数列表 (排除非数值或标识列)
        # YieldChart 的 get_available_parameters() 也可以获取参数列，这里我们直接从 cleaned_df 推断
        potential_params = [
            col for col in cleaned_df.columns 
            if col not in ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y', 'True_Lot_ID', 'x_position', 'lot_id', 'wafer_id', 'value'] 
            and cleaned_df[col].dtype in ['int64', 'float64']
        ]
        
        # 如果 YieldChart 加载了 spec, 它有更精确的参数列表
        params_from_yield_chart = yield_analyzer.get_available_parameters()
        if params_from_yield_chart: # 优先使用 YieldChart 提供的参数列表
             plot_params = [p for p in params_from_yield_chart if p in cleaned_df.columns and cleaned_df[p].dtype in ['int64', 'float64']]
        else:
             plot_params = potential_params

        if not plot_params:
            logger.warning("未能从 cleaned_data 中找到合适的数值参数列来生成箱体图/散点图。")
        else:
            logger.info(f"将为以下参数生成图表: {plot_params}")

            for param in plot_params:
                try:
                    # a. 生成并保存箱体图 (按 Lot_ID 分组)
                    #    提取简化的 Lot_ID 用于图例，假设 Lot_ID 格式为 PREFIX_FAXX-YYYY@ZZZ_WNN
                    #    我们仅提取 FAXX-YYYY 部分作为分组依据
                    if 'Lot_ID' in cleaned_df.columns:
                        cleaned_df['Short_Lot_ID'] = cleaned_df['Lot_ID'].str.extract(r'(FA\d{2}-\d+)', expand=False).fillna('Unknown')
                        color_group = 'Short_Lot_ID'
                    else:
                        color_group = None

                    fig_box = px.box(
                        cleaned_df, 
                        y=param, 
                        color=color_group,
                        title=f"参数 {param} 箱体图 (按批次)",
                        labels={param: f"{param} ({yield_analyzer.get_parameter_info(param).get('unit','')})"},
                        points="all" #显示所有数据点
                    )
                    box_filename = custom_charts_output_dir / f"{param}_boxplot.html"
                    fig_box.write_html(str(box_filename))
                    logger.info(f"  - 已保存箱体图: {box_filename.name}")

                    # b. 生成并保存散点图 (示例：对比两个参数，如果多于一个参数)
                    #    这里仅为第一个参数和（如果存在）第二个参数生成散点图
                    #    您可以根据需要扩展此逻辑
                    if len(plot_params) > 1 and param == plot_params[0]:
                        param2 = plot_params[1]
                        fig_scatter = px.scatter(
                            cleaned_df, 
                            x=param, 
                            y=param2, 
                            color=color_group,
                            title=f"参数 {param} vs {param2} 散点图",
                            labels={
                                param: f"{param} ({yield_analyzer.get_parameter_info(param).get('unit','')})",
                                param2: f"{param2} ({yield_analyzer.get_parameter_info(param2).get('unit','')})"
                            },
                            hover_data=['Wafer_ID']
                        )
                        scatter_filename = custom_charts_output_dir / f"{param}_vs_{param2}_scatter.html"
                        fig_scatter.write_html(str(scatter_filename))
                        logger.info(f"  - 已保存散点图: {scatter_filename.name}")
                
                except Exception as e:
                    logger.error(f"为参数 {param} 生成自定义图表时出错: {e}")
            
            logger.info(f"自定义箱体图/散点图已保存到: {custom_charts_output_dir}")

    logger.info("图表生成流程结束。")

if __name__ == "__main__":
    main()
```

**如何运行 `generate_custom_charts.py`:**

1.  **创建数据目录**：
    在您的项目根目录下创建一个名为 `input_data` 的文件夹（或者您在脚本中指定的其他路径）。
2.  **放入数据文件**：
    将您的 `_yield_*.csv`, `_spec_*.csv`, 和 `_cleaned_*.csv` 文件复制到 `input_data` 文件夹中。
    *   **重要**: 确保文件名中的批次标识部分（例如 `YOUR_BATCH_ID`）对于这三个文件是相同的，`YieldChart` 会根据这个共同的前缀来匹配文件。
3.  **修改脚本中的 `data_input_dir`**：
    打开 `generate_custom_charts.py` 文件，找到以下行：
    ```python
    data_input_dir = Path("input_data") # <<--- 修改这里：指向您的CSV数据文件夹
    ```
    如果您的数据文件夹不是项目根目录下的 `input_data`，请修改此路径使其指向正确的位置。
4.  **执行脚本**：
    打开终端或命令提示符，导航到您的项目根目录 (`cp_data_ansys`)，然后运行脚本：
    ```bash
    python generate_custom_charts.py
    ```
    或者，如果您在 IDE (如 VS Code, PyCharm) 中，可以直接运行该文件。

    *注意：* 确保您的 Python 环境已安装必要的库 (`pandas`, `plotly`）。如果 `frontend.charts.yield_chart` 导入失败，请检查您的 `PYTHONPATH` 是否已将项目根目录（`cp_data_ansys`）包括在内，或者 `generate_custom_charts.py` 是否相对于 `frontend` 目录放置正确。如果 `generate_custom_charts.py` 放在项目根目录，导入路径应为 `from frontend.charts.yield_chart import YieldChart`。

### 3. 查看生成的 HTML 图表

脚本执行完毕后，所有生成的 HTML 图表文件将保存在您脚本中 `charts_output_dir` 指定的目录下（默认为项目根目录下的 `demo_output/generated_charts`）。

*   `YieldChart` 生成的图表会位于子目录 `yield_chart_outputs` 中。
*   使用 `plotly.express` 生成的箱体图和散点图会位于子目录 `custom_plotly_express_charts` 中。

您可以直接用网页浏览器（如 Chrome, Firefox, Edge）打开这些 `.html` 文件来查看交互式图表。

### 4. 图表说明

*   **YieldChart 内置图表 (位于 `yield_chart_outputs`)**:
    *   `Wafer良率趋势分析_yield_chart.html`: 显示每个批次内各个 Wafer 的良率变化趋势。
    *   `批次良率对比分析_yield_chart.html`: 对比不同批次的平均良率（柱状图形式，可能带误差棒）。
    *   `良率分布统计_yield_chart.html`: 显示所有 Wafer 良率的分布情况（直方图）。
    *   `失效类型分析_yield_chart.html`: (如果提供了 Bin 数据) 显示不同失效类型的占比（饼图）。
    *   `参数名_[单位]_@测试条件_yield_line_chart.html`: 针对 `cleaned_data` 和 `spec_data` 中定义的每个参数，生成参数值随 Wafer 变化的折线图，并标出规格上下限。

*   **自定义 Plotly Express 图表 (位于 `custom_plotly_express_charts`)**:
    *   `参数名_boxplot.html`: 为 `cleaned_data` 中的每个数值参数生成箱体图，按批次（从 `Lot_ID` 提取的简称）进行颜色区分，显示数据的分布、中位数、四分位数和异常点。
    *   `参数1_vs_参数2_scatter.html`: (示例) 如果有两个或更多参数，会生成第一个参数与第二个参数的散点图，用于观察它们之间的相关性，按批次进行颜色区分。

通过以上步骤，您可以方便地对新的 CP 测试数据进行处理、可视化分析，并获得可交互的 HTML 报告。