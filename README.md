# 🔬 CP 数据分析工具

**半导体晶圆 CP (Chip Probing) 测试数据处理与可视化分析平台**

## 🎯 项目是什么 (What)

本工具是一个专为半导体制造业设计的 CP (Chip Probing) 测试数据分析平台，旨在提供从原始测试数据导入、智能清洗、专业分析到交互式可视化报告生成的一站式解决方案。它能够帮助工程师和数据分析师高效处理复杂的测试数据，快速洞察生产过程中的关键信息，从而优化工艺、提升良率。

### ✨ 核心功能

- 🔢 **多格式数据兼容**: 支持 DCP, CW, MEX 等主流 CP 测试数据格式的自动解析与处理
- 🧹 **智能数据清洗**: 内置算法自动识别和处理异常值、缺失数据，确保分析结果的准确性
- 📊 **专业图表分析**: 生成符合行业标准的分析图表，如良率趋势图、参数分布箱体图、晶圆 MAP 图、参数对比散点图等
- 💻 **交互式可视化**: 所有图表均基于 Plotly 生成，支持交互式操作（缩放、平移、悬停提示、数据点选择）并可导出为 HTML 文件
- ⚙️ **参数化与自动化**: 自动生成各参数的趋势图，并叠加规格线 (Spec Limit) 和测试条件信息。支持批量处理多文件、多批次数据
- 🛠️ **灵活操作模式**: 提供图形用户界面 (GUI)、命令行工具 (CLI) 及 Python API 调用三种使用方式，满足不同用户需求

### 🎨 项目特色

- ✅ **一站式平台**: 从数据导入到报告导出，全程在统一平台完成，简化工作流程
- ✅ **深度定制**: 针对半导体 CP 测试特点进行优化，图表和分析逻辑更贴合实际应用
- ✅ **易于扩展**: 模块化设计，方便未来添加新的数据格式支持、分析算法或图表类型
- ✅ **现代化架构**: Python 版本采用现代化技术栈，性能更优，跨平台性更好

## 💡 为什么需要这个项目 (Why)

在半导体制造过程中，CP 测试产生了海量的关键数据。然而，工程师们常常面临以下挑战：

### 🔍 行业痛点

1. **数据格式繁杂**: 不同测试设备或流程产生的数据格式（如 DCP, CW, MEX）不统一，增加了数据整合难度
2. **分析工具匮乏**: 缺乏专为 CP 数据设计的、集数据处理与高级可视化于一体的便捷工具
3. **手动处理低效**: 传统依赖 Excel 等工具手动处理数据，不仅耗时耗力，还容易引入人为错误
4. **可视化交互性差**: 静态图表难以进行深度数据探索和多维度分析

### 🎯 解决方案

本工具通过以下方式解决上述痛点：

- 🔄 **统一数据接口**: 提供统一的数据处理流程，兼容多种主流 CP 测试数据格式
- 📈 **专业分析能力**: 内置针对性的分析模块和可视化图表，如良率分析、参数统计、失效模式分析等
- ⚡ **自动化处理**: 大幅减少手动操作，实现数据清洗、计算、图表生成的自动化，提升工作效率
- 🌐 **交互式探索**: 生成的 HTML 图表具有丰富的交互功能，便于用户深入挖掘数据背后的信息

### 📋 适用场景

| 应用领域 | 具体用途 | 价值体现 |
|---------|----------|----------|
| **半导体制造** | CP 测试数据分析、良率监控、WAT 数据分析 | 提升产品质量、快速定位问题 |
| **质量控制** | 批次间参数稳定性对比、参数趋势监控、异常值检测 | 保证产品一致性、及时预警 |
| **工艺优化** | 工艺变更前后数据对比、参数与良率相关性分析 | 指导工艺改进、优化参数 |
| **工程报告** | 自动化生成标准分析报告、交互式数据分享 | 提高工程师工作效率 |

## 🚀 如何使用 (How)

### 📦 环境准备

**安装依赖:**
```bash
pip install pandas numpy plotly openpyxl
```

**快速体验:**
```bash
# 生成良率分析图表
python demo_yield_chart.py

# 生成参数统计图表
python test_boxplot.py

# 生成完整分析报告
python generate_custom_charts.py
```

### 📊 完整使用流程

#### 第一步：数据准备与清洗

**数据文件要求:**
系统需要三类 CSV 文件，放置在同一目录（默认为 `output/`）：

| 数据类型 | 文件命名约定 | 必需列 | 说明 |
|---------|-------------|-------|------|
| 📈 **良率数据** | `*_yield_*.csv` | `Lot_ID`, `Wafer_ID`, `Yield` | 包含每个 Wafer 的良率信息、失效统计 |
| 📋 **规格数据** | `*_spec_*.csv` | `Parameter`, `Unit`, `LimitU`, `LimitL`, `TestCond` | 定义各测试参数的名称、单位、规格上下限、测试条件 |
| 🔧 **清洗数据** | `*_cleaned_*.csv` | `Lot_ID`, `Wafer_ID`, 及各参数列 | 经过清洗和预处理的详细 Die-Level 测试数据 |

**数据清洗脚本:**
```bash
# 清洗原始 DCP 数据
python clean_dcp_data.py

# 清洗原始 CSV 数据（如果有）
python clean_csv_data.py

# 提取规格信息
python dcp_spec_extractor.py
```

#### 第二步：生成交互式图表

**A. 良率分析图表（推荐）**
```bash
python demo_yield_chart.py
```
生成内容：
- 📈 Wafer 良率趋势分析（各 Wafer 良率变化，按批次组织）
- 📊 批次良率对比分析（不同批次平均良率对比）
- 📦 良率分布统计
- 🥧 失效类型分析饼图
- 🔍 各参数的折线图（自动叠加规格线和测试条件）

**B. 参数统计图表**
```bash
python test_boxplot.py
```
生成内容：
- 📦 各参数的箱体图（Box Plot），展示分布情况
- 🌈 参数间散点图（可选），分析相关性
- 🔍 异常值检测和标注

**C. 完整分析报告**
```bash
python generate_custom_charts.py
```
生成完整的分析报告，包含上述所有图表类型。

#### 第三步：多种操作模式

**A. 简化版图形界面 (推荐新用户)**
```bash
cd gui
python cp_data_gui.py
# 或者双击运行: gui/start_gui.bat
```
**特点**：
- 🎯 **三步完成**：选择路径 → 清洗数据 → 生成图表
- 🤖 **高度自动化**：所有参数和图表类型默认全选
- 🖱️ **操作简洁**：最少的手动配置，智能默认设置
- 📊 **实时反馈**：处理进度和状态实时显示

**B. 图形用户界面 (GUI)**
```bash
python cp_data_processor_gui.py
```
通过 GUI 可以：
1. 选择输入数据文件或目录
2. 配置数据格式 (DCP/CW/MEX) 和分析选项
3. 勾选需要生成的图表类型
4. 点击按钮开始处理并生成报告

**C. 命令行工具 (CLI)**
```bash
# 基本语法
python cp_data_processor_cli.py <输入文件> <输出文件> [选项]

# 示例：处理 DCP 文件并生成箱体图和 Bin Map
python cp_data_processor_cli.py data.txt result.xlsx --format dcp --boxplot --bin-map

# 示例：处理 CW 格式数据并生成散点图
python cp_data_processor_cli.py data.csv result.xlsx --format cw --scatter
```

**常用参数:**
- `--format {dcp,cw,mex}`: 指定输入文件格式
- `--boxplot`: 生成参数箱体图
- `--scatter`: 生成参数散点图
- `--bin-map`: 生成晶圆 Bin Map 图
- `--data-map`: 生成参数值在晶圆上的颜色分布图

**D. API 方式自定义开发**
```python
from frontend.charts.yield_chart import YieldChart
from pathlib import Path

# 创建分析实例
chart = YieldChart(data_dir="output")
chart.load_data()

# 生成所有图表
saved_files = chart.save_all_charts(output_dir="custom_output")
print(f"成功生成 {len(saved_files)} 个图表")
```

### 📁 输出结果说明

**目录结构:**
```
demo_output/                 # 主输出目录
├── all_charts/             # demo_yield_chart.py 生成的图表
│   ├── Wafer良率趋势分析_yield_chart.html
│   ├── BVDSS1[V]@250uA_yield_line_chart.html
│   └── ...
├── generated_charts/       # generate_custom_charts.py 生成的图表
│   ├── yield_chart_outputs/        # YieldChart 内置图表
│   └── custom_plotly_express_charts/ # 自定义箱体图+散点图
└── detailed_analysis/      # 详细分析结果

output/                     # 数据处理输出
├── *_yield_*.csv           # 良率数据
├── *_spec_*.csv            # 规格数据
└── *_cleaned_*.csv         # 清洗数据
```

**图表类型说明:**

| 图表类型 | 文件名格式 | 功能说明 |
|---------|-----------|----------|
| 📈 良率趋势图 | `Wafer良率趋势分析_yield_chart.html` | 显示批次内 Wafer 良率变化 |
| 📊 批次对比图 | `批次良率对比分析_yield_chart.html` | 不同批次平均良率对比 |
| 🔍 参数折线图 | `参数[单位]@测试条件_yield_line_chart.html` | 参数值变化趋势 + 规格线 |
| 📦 箱体图 | `参数[单位]@测试条件_boxplot_chart.html` | 参数分布统计 + 异常值检测 |
| 🌈 散点图 | `参数1_vs_参数2_scatter.html` | 参数间相关性分析 |

### 🔧 高级功能

**自定义图表样式:**
```python
# 修改图表配置
chart.chart_config.update({
    'height': 800,                    # 图表高度
    'font_size': 14,                  # 字体大小
    'min_chart_width': 1400,          # 最小图表宽度
})
```

**数据过滤和筛选:**
```python
# 过滤特定批次
chart_data = chart.wafer_data[chart.wafer_data['Lot_Short'] == 'FA54-5339']

# 过滤特定良率范围
high_yield_data = chart.wafer_data[chart.wafer_data['Yield_Numeric'] > 98.0]
```

### 🐛 常见问题解决

**数据加载失败:**
1. 检查 `output/` 目录是否存在数据文件
2. 确认文件命名格式正确：`*_yield_*.csv`, `*_spec_*.csv`, `*_cleaned_*.csv`
3. 验证 CSV 文件编码为 UTF-8

**图表显示问题:**
1. 使用现代浏览器（Chrome、Firefox、Edge）
2. 检查网络连接（Plotly 可能需要加载在线资源）
3. 确认 HTML 文件完整且未损坏

## 🏗️ 系统架构

### Python 版本架构

采用现代化的模块化架构设计：

```
CP数据处理器
├── 数据读取层 (readers)      # 解析不同格式的原始数据
├── 数据模型层 (data_models)  # 定义核心数据结构
├── 数据处理层 (processing)   # 数据清洗、转换、计算
├── 数据分析层 (analysis)     # 统计分析、良率计算
├── 数据可视化层 (plotting)   # 生成各类交互式图表
├── 数据导出层 (exporters)    # 将结果保存为文件
└── 应用层 (app/cli/main)     # 用户接口和主流程控制
```

### 核心优势

| 对比项 | 传统方案 | 本工具 |
|--------|----------|--------|
| 🚀 **性能** | 手动处理，效率低 | 自动化批量处理 |
| 🔧 **维护性** | 脚本分散，难维护 | 模块化设计，易扩展 |
| 🌐 **跨平台** | 依赖特定软件 | Python 跨平台运行 |
| 📊 **图表** | 静态图表，交互性差 | 交互式 HTML 图表 |
| 🔍 **扩展性** | 功能固定，难扩展 | 易于添加新功能 |

## 📞 技术支持

- 📖 **快速体验**: `python demo_yield_chart.py`
- 🐛 **问题反馈**: 通过项目 Issues 系统
- 💡 **功能建议**: 欢迎提出改进建议

---

> 💡 **提示**: 建议先运行 `python demo_yield_chart.py` 快速体验功能，然后根据具体需求进行定制化分析。 

## 🚀 快速开始

### 安装依赖

```bash
pip install pandas numpy plotly matplotlib seaborn openpyxl pathlib2
```

### 运行程序

```bash
python chart_generator.py
```

## 📁 项目结构

```
cp_data_ansys/
├── 📊 核心应用
│   ├── chart_generator.py           # 主程序入口
│   ├── frontend/                    # 前端图表模块  
│   ├── cp_data_processor/          # 数据处理器
│   ├── output/                     # 数据输出目录
│   └── demo_output/                # 演示输出
├── 📦 打包系统 (packaging/)
│   ├── README.md                   # 打包系统说明  
│   ├── 使用说明.md                 # 快速使用指南
│   └── build_scripts/              # 构建脚本集合
│       ├── conda_pack_builder.py  # 主构建脚本
│       ├── quick_build.bat        # 一键构建
│       └── ...                    # 其他构建工具
├── 🔧 开发工具
│   ├── analyze_data.py             # 数据分析脚本
│   ├── yield_chart_generator.py    # 良率图表生成器
│   └── ...                        # 其他工具脚本
└── 📚 文档
    ├── README.md                   # 本文档
    ├── 功能实现总结.md             # 功能总结
    └── ...                        # 其他文档
```

## 🎯 主要功能

- ✅ **多格式数据读取**：支持DCP、CW、MEX等格式
- ✅ **专业图表生成**：箱体图、散点图、良率图等
- ✅ **数据统计分析**：自动统计和趋势分析
- ✅ **报告导出**：支持多种格式导出

## 📦 打包与发布

### 开发者注意

**日常开发**：
- 专注于主应用开发
- **可以完全忽略** `packaging/` 目录
- 这个目录不会影响任何开发工作

**需要发布时**：
```bash
# 进入打包目录
cd packaging

# 一键构建安装包
build_scripts\quick_build.bat
```

### 打包系统特点

- 🔄 **离线安装**：包含完整Python环境
- 📦 **体积优化**：~100-150MB安装包
- 🛡️ **环境隔离**：不影响用户现有环境
- ⚡ **快速部署**：一次构建，多次安装

详细信息请查看 [`packaging/README.md`](packaging/README.md)

## 🔧 开发指南

### 添加新功能

1. 在对应模块目录下开发
2. 更新相关文档
3. 测试功能正常工作

### 发布新版本

1. 确保代码稳定
2. 进入 `packaging/` 目录
3. 运行构建脚本
4. 测试生成的安装包

## 📊 技术栈

- **Python 3.12+**
- **数据处理**：pandas, numpy
- **图表生成**：plotly, matplotlib, seaborn  
- **文件处理**：openpyxl
- **打包工具**：conda-pack

## 📞 技术支持

- 应用问题：查看主目录文档
- 打包问题：查看 `packaging/README.md`
- 功能建议：提交Issue或联系开发团队

## 📝 更新日志

- **v1.0.0** - 初始版本，包含完整数据分析功能
- 支持多种数据格式和图表类型
- 集成conda-pack打包系统

---

💡 **提示**：新手开发者可以先忽略打包相关内容，专注于主要功能开发。 