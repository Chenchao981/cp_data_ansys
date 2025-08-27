# 🔬 CP 数据分析工具

**半导体晶圆 CP (Chip Probing) 测试数据处理与可视化分析平台**

> 📚 **文档导航**: [完整文档索引](文档索引.md) | [开发者指南](CLAUDE.md) | [新公司集成](add_new_company_data_function.md)

## 🎯 项目简介

专为半导体制造业设计的 CP (Chip Probing) 测试数据分析平台，提供从原始测试数据导入、智能清洗、专业分析到交互式可视化报告生成的一站式解决方案。

### ✨ 核心功能

- 🔢 **多格式数据兼容**: 支持 DCP, CW, MEX, JT Excel 等主流 CP 测试数据格式
- 🏭 **多公司数据支持**: 专门支持 HH 公司、JT 公司数据格式
- 🧹 **智能数据清洗**: 自动识别和处理异常值、缺失数据
- 📊 **专业图表分析**: 良率趋势图、参数分布箱体图、晶圆 MAP 图、参数对比散点图
- 💻 **交互式可视化**: 基于 Plotly 生成交互式 HTML 图表
- ⚙️ **参数化与自动化**: 自动生成各参数趋势图，叠加规格线和测试条件
- 🎯 **高精度数据处理**: 保留原始数据小数点后5位精度，确保分析准确性
- 🔄 **动态失效分析**: 根据实际情况自动识别和保留失效bin类型，不再局限于固定配置
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
# HH公司数据处理
python cp_data_processor_cli.py <输入文件> <输出文件> [选项]

# 示例
python cp_data_processor_cli.py data.txt result.xlsx --format dcp --boxplot --bin-map

# 🆕 JT公司数据处理
python -m jt_data_processor.jt_main_processor <JT文件路径或目录> --output output
```

#### 4. Python API

```python
# HH公司数据处理
from frontend.charts.yield_chart import YieldChart

chart = YieldChart(data_dir="output")
chart.load_data()
saved_files = chart.save_all_charts(output_dir="custom_output")

# 🆕 JT公司数据处理
from jt_data_processor import process_jt_files

result = process_jt_files(
    input_paths="path/to/jt/files", 
    output_dir="output",
    pass_bin=1
)
```

### 📊 快速体验

```bash
# HH公司：生成良率分析图表（主要功能）
python chart_generator.py

# 🆕 JT公司：生成完整图表分析
python jt_chart_generator.py

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
│   ├── chart_generator.py          # HH公司图表生成器
│   ├── 🆕 jt_chart_generator.py    # JT公司图表生成器
│   ├── cp_data_processor/          # HH公司数据处理器
│   │   ├── readers/                # HH数据读取
│   │   ├── processing/             # 数据处理
│   │   ├── analysis/               # 数据分析
│   │   ├── plotting/               # 图表生成
│   │   └── exporters/              # 数据导出
│   ├── 🆕 jt_data_processor/       # JT公司数据处理器
│   │   ├── readers/                # JT Excel读取器
│   │   ├── adapters/               # JT数据适配器
│   │   ├── config/                 # JT配置管理
│   │   └── utils/                  # JT目录检测工具
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

#### HH公司格式
- **DCP**: 标准 DCP 测试数据文件
- **CW**: Cascade 微探针数据
- **MEX**: 其他格式测试数据

#### 🆕 JT公司格式
- **Excel**: JT公司专用 Excel 文件格式 (FA*.xls/xlsx)
  - 支持 Summary information 工作表元数据
  - 支持 DUT_DATA 工作表测试数据
  - 智能目录结构检测（单层/双层目录）

### 输出数据

系统需要三类 CSV 文件：

| 数据类型    | 文件命名            | 说明                      |
| ----------- | ------------------- | ------------------------- |
| 📈 良率数据 | `*_yield_*.csv`   | 包含每个 Wafer 的良率信息 |
| 📋 规格数据 | `*_spec_*.csv`    | 测试参数的规格上下限      |
| 🔧 清洗数据 | `*_cleaned_*.csv` | 清洗后的详细测试数据      |

## 📈 生成的图表类型

| 图表类型         | 功能说明                  | 支持公司 |
| ---------------- | ------------------------- | -------- |
| 📈 良率趋势图    | 显示批次内 Wafer 良率变化 | HH、JT   |
| 📊 批次对比图    | 不同批次平均良率对比      | HH、JT   |
| 🔍 失效分析图    | 失效类型分布分析          | HH、JT   |
| 📦 箱体图        | 参数分布统计 + 异常值检测 | HH、JT   |
| 🌈 散点图        | 参数间相关性分析          | HH、JT   |
| 📋 汇总图表      | 良率图+参数图综合展示     | HH、JT   |
| 🗺️ 晶圆 MAP 图 | 晶圆上的参数分布          | HH       |

## 🏭 公司特有功能

### HH公司数据处理
- **数据格式**: DCP, CW, MEX 文件
- **单位转换**: 支持完整的单位转换体系
- **清洗方法**: IQR 和标准差方法
- **图表生成**: `python chart_generator.py`

### 🆕 JT公司数据处理

#### 特色功能
- **数据格式**: Excel 工作簿 (FA*.xls/xlsx)
- **单位转换**: 禁用单位转换（JT数据已匹配）
- **清洗方法**: 专用 IQR 四分位法
- **目录智能**: 支持单层/双层目录结构检测
- **字段映射**: 专门的JT字段到标准字段映射

#### 使用示例

```bash
# 处理单个JT文件
python -m jt_data_processor.jt_main_processor FA44-4149.xlsx

# 处理JT目录（智能检测结构）
python -m jt_data_processor.jt_main_processor ./jt_data_folder/

# 生成JT图表
python jt_chart_generator.py
```

#### JT数据处理流程

1. **数据读取**: 从 Excel 工作表提取元数据和测试数据
2. **字段映射**: DUT_NO→Seq, SOFT_BIN→Bin 等
3. **数据清洗**: IQR 四分位法处理异常值
4. **标准输出**: 生成标准CSV三件套
5. **图表生成**: 复用HH前端模块生成图表

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

# JT公司模块依赖
pip install -r jt_data_processor/requirements.txt
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

### HH公司数据

**数据加载失败**：

1. 检查 `output/` 目录是否存在数据文件
2. 确认文件命名格式正确
3. 验证 CSV 文件编码为 UTF-8

### 🆕 JT公司数据

**Excel文件读取失败**：

1. 确认文件为 .xls 或 .xlsx 格式
2. 检查文件命名符合 FA*.xlsx 格式
3. 验证 Excel 文件包含必要工作表

**列名转换问题**：

1. 确保 Summary information 工作表存在
2. 检查 DUT_DATA 工作表数据格式
3. 验证字段映射配置正确

**图表显示问题**：

1. 使用现代浏览器（Chrome、Firefox、Edge）
2. 检查网络连接
3. 确认 HTML 文件完整

## 📈 使用建议

### 新用户推荐流程

1. **HH公司用户**: 
   ```bash
   python chart_generator.py
   ```

2. **🆕 JT公司用户**:
   ```bash
   # 第一步：数据处理
   python -m jt_data_processor.jt_main_processor ./your_jt_data/
   
   # 第二步：图表生成
   python jt_chart_generator.py
   ```

### 高级用户

- 使用 Python API 进行定制化分析
- 利用 GUI 界面进行交互式操作
- 批量处理多个数据源

## 📞 技术支持

- 📖 **HH公司数据**: `python chart_generator.py`
- 📖 **🆕 JT公司数据**: `python jt_chart_generator.py`
- 🐛 **问题反馈**: 通过项目 Issues 系统
- 💡 **功能建议**: 欢迎提出改进建议

## 🆕 版本更新 (v1.3)

### 新增功能

- 🏭 **JT公司完整支持**: 专门的JT数据处理器和图表生成器
- 🔧 **智能目录检测**: 支持复杂的目录结构自动识别
- ⚙️ **公司特化配置**: 针对不同公司的专门配置管理
- 📊 **图表模块复用**: JT公司复用HH公司成熟的前端图表模块

### 技术改进

- 🎯 **X轴显示修复**: 修复良率图表X轴范围限制问题
- 🔧 **汇总图表集成**: 添加完整的汇总分析功能
- 📦 **打包系统更新**: 使用.pyz打包替代conda-pack

---

> 💡 **提示**: 
> - HH公司用户建议先运行 `python chart_generator.py` 快速体验功能
> - 🆕 JT公司用户建议先运行 `python jt_chart_generator.py` 体验完整流程
> - 然后根据具体需求进行定制化分析
