# 🔬 CP 数据分析工具

**半导体晶圆 CP (Chip Probing) 测试数据处理与可视化分析平台**

## 🎯 项目简介

专为半导体制造业设计的 CP (Chip Probing) 测试数据分析平台，提供从原始测试数据导入、智能清洗、专业分析到交互式可视化报告生成的一站式解决方案。

### ✨ 核心功能

- 🔢 **多格式数据兼容**: 支持 DCP, CW, MEX 等主流 CP 测试数据格式
- 🧹 **智能数据清洗**: 自动识别和处理异常值、缺失数据
- 📊 **专业图表分析**: 良率趋势图、参数分布箱体图、晶圆 MAP 图、参数对比散点图
- 💻 **交互式可视化**: 基于 Plotly 生成交互式 HTML 图表
- ⚙️ **参数化与自动化**: 自动生成各参数趋势图，叠加规格线和测试条件
- 🛠️ **多种操作模式**: GUI、CLI 及 Python API 三种使用方式

## 🚀 快速开始

### 📦 环境准备

```bash
pip install pandas numpy plotly openpyxl
```

### 🎮 使用方式

#### 1. 简化版图形界面（推荐新用户）

```bash
cd gui
python cp_data_gui.py
```

**特点**：

- 🎯 三步完成：选择路径 → 清洗数据 → 生成图表
- 🤖 高度自动化：智能默认设置
- 🖱️ 操作简洁：基于 PyQt5，现代化界面

#### 2. 通用图形界面

```bash
python cp_data_processor_gui.py
```

**特点**：

- 🔧 功能完整：支持所有数据格式和图表类型
- ⚙️ 参数可调：可配置各种处理选项
- 📋 基于 Tkinter：跨平台兼容性好

#### 3. 命令行工具

```bash
python cp_data_processor_cli.py <输入文件> <输出文件> [选项]

# 示例
python cp_data_processor_cli.py data.txt result.xlsx --format dcp --boxplot --bin-map
```

#### 4. Python API

```python
from frontend.charts.yield_chart import YieldChart

chart = YieldChart(data_dir="output")
chart.load_data()
saved_files = chart.save_all_charts(output_dir="custom_output")
```

### 📊 快速体验

```bash
# 生成良率分析图表（主要功能）
python chart_generator.py

# 数据清洗（可选）
python clean_dcp_data.py
python clean_csv_data.py

# 规格提取（可选）
python dcp_spec_extractor.py
```

## 📁 项目结构

```
cp_data_ansys/
├── 📊 核心模块
│   ├── chart_generator.py          # 主程序入口
│   ├── cp_data_processor/          # 数据处理器
│   │   ├── readers/                # 数据读取
│   │   ├── processing/             # 数据处理
│   │   ├── analysis/               # 数据分析
│   │   ├── plotting/               # 图表生成
│   │   └── exporters/              # 数据导出
│   ├── frontend/                   # 前端图表模块
│   │   ├── charts/                 # 图表组件
│   │   ├── core/                   # 核心功能
│   │   └── utils/                  # 工具函数
│   └── gui/                        # 图形界面
├── 🔧 数据处理工具
│   ├── clean_dcp_data.py           # DCP 数据清洗
│   ├── clean_csv_data.py           # CSV 数据清洗
│   ├── dcp_spec_extractor.py       # 规格提取器
│   └── cp_unit_converter.py        # 单位转换器
├── 📦 打包系统
│   └── packaging/                  # .pyz 打包和 Anaconda 部署
└── 📚 输出目录
    ├── output/                     # 数据输出
    └── charts_output/              # 图表输出
```

## 📊 支持的数据格式

### 输入格式

- **DCP**: 标准 DCP 测试数据文件
- **CW**: Cascade 微探针数据
- **MEX**: 其他格式测试数据

### 输出数据

系统需要三类 CSV 文件：

| 数据类型 | 文件命名 | 说明 |
|---------|---------|------|
| 📈 良率数据 | `*_yield_*.csv` | 包含每个 Wafer 的良率信息 |
| 📋 规格数据 | `*_spec_*.csv` | 测试参数的规格上下限 |
| 🔧 清洗数据 | `*_cleaned_*.csv` | 清洗后的详细测试数据 |

## 📈 生成的图表类型

| 图表类型 | 功能说明 |
|---------|----------|
| 📈 良率趋势图 | 显示批次内 Wafer 良率变化 |
| 📊 批次对比图 | 不同批次平均良率对比 |
| 🔍 参数折线图 | 参数值变化趋势 + 规格线 |
| 📦 箱体图 | 参数分布统计 + 异常值检测 |
| 🌈 散点图 | 参数间相关性分析 |
| 🗺️ 晶圆 MAP 图 | 晶圆上的参数分布 |

## 🔧 开发环境

### 技术栈

- **Python 3.12+**
- **数据处理**: pandas, numpy
- **图表生成**: plotly, matplotlib, seaborn  
- **GUI**: PyQt5
- **文件处理**: openpyxl

### 安装依赖

```bash
# 核心依赖
pip install -r cp_data_processor/requirements.txt

# GUI 依赖
pip install -r gui/requirements.txt
```

## 📦 打包发布

### 开发者打包

创建 .pyz 可执行包：

```bash
cd packaging
python create_pyz.py
```

### 用户部署

使用 Anaconda 环境快速部署：

```bash
cd packaging/release
# 安装 Anaconda 环境和依赖
install_anaconda.bat
# 启动程序
start.bat
```

**部署特点**：

- 🐍 **基于 Anaconda**: 预装科学计算包，稳定性好
- 📦 **.pyz 打包**: 单文件可执行，便于分发
- 🛡️ **环境隔离**: 不影响用户现有环境
- ⚡ **快速安装**: 自动检测和安装依赖

## 🐛 常见问题

**数据加载失败**：

1. 检查 `output/` 目录是否存在数据文件
2. 确认文件命名格式正确
3. 验证 CSV 文件编码为 UTF-8

**图表显示问题**：

1. 使用现代浏览器（Chrome、Firefox、Edge）
2. 检查网络连接
3. 确认 HTML 文件完整

## 📞 技术支持

- 📖 **快速体验**: `python chart_generator.py`
- 🐛 **问题反馈**: 通过项目 Issues 系统
- 💡 **功能建议**: 欢迎提出改进建议

---

> 💡 **提示**: 建议先运行 `python chart_generator.py` 快速体验功能，然后根据具体需求进行定制化分析。
