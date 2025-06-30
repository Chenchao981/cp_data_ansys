# CLAUDE.md

这个文件为在此代码仓库中工作的 Claude Code (claude.ai/code) 提供指导。

## 常用命令

### 运行应用程序

```bash
# 快速演示（从 output/ 目录生成所有图表）
python chart_generator.py

# 图形界面
cd gui
python cp_data_gui.py                # 简化版图形界面（推荐）
python ../cp_data_processor_gui.py   # 完整功能图形界面

# 命令行使用
python cp_data_processor_cli.py <输入文件> <输出文件> [选项]
python cp_data_processor_cli.py data.txt result.xlsx --format dcp --boxplot --bin-map
```

### 数据处理工具

```bash
# 数据清洗工具
python clean_dcp_data.py     # 清洗 DCP 格式数据
python clean_csv_data.py     # 清洗 CSV 格式数据

# 规格提取和单位转换
python dcp_spec_extractor.py # 从 DCP 文件提取规格
python cp_unit_converter.py  # 转换测量单位
```

### 开发和打包

```bash
# 安装依赖
pip install -r cp_data_processor/requirements.txt  # 核心依赖
pip install -r gui/requirements.txt                # 图形界面依赖

# 创建 .pyz 发布包
cd packaging
python create_pyz.py

# 测试（有限 - 主要是集成测试）
python -m pytest jt_data_processor/tests/
```

## 架构概览

这是一个面向半导体制造业的综合性 **CP (Chip Probing) 测试数据分析平台**。系统处理各种格式的原始测试数据，执行智能数据清洗、统计分析，并生成交互式可视化图表。

### 核心数据流

1. **数据输入** → 多种文件格式读取器（DCP、CW、MEX、Excel/TXT）
2. **数据处理** → 清洗、转换、单位转换
3. **分析** → 统计分析、良率计算、能力分析
4. **可视化** → 交互式图表（基于 Plotly）、晶圆图、箱体图、散点图
5. **导出** → Excel 报告、HTML 图表、CSV 数据

### 关键模块

- **`cp_data_processor/`** - 具有模块化架构的主要处理引擎
  - `readers/` - 文件格式解析器，包含公司特定适配器
  - `processing/` - 数据转换和清洗逻辑
  - `analysis/` - 统计分析、良率计算、能力分析
  - `plotting/` - 图表生成（基于 Plotly）
  - `exporters/` - Excel 和数据导出功能
  - `data_models/cp_data.py` - 核心数据结构（CPLot、CPWafer、CPParameter）

- **`frontend/`** - 交互式图表组件和 Web 界面
  - `charts/` - 专用图表类（YieldChart、BoxplotChart 等）
  - `core/` - 数据管理和图表工厂
  - `utils/` - 文件处理和验证工具

- **`gui/`** - 桌面图形界面应用程序（基于 PyQt5）

### 数据模型层次结构

```
CPLot (批次/批量级别)
├── lot_id, product, wafer_count
├── wafers: List[CPWafer]
├── params: List[CPParameter] 
└── combined_data: DataFrame (所有晶圆的所有芯片)

CPWafer (单个晶圆)
├── wafer_id, chip_count, yield_rate
├── x, y, seq, bin 数组 (芯片坐标和结果)
└── chip_data: DataFrame (每个芯片的测试结果)

CPParameter (测试参数)
├── id, unit, sl/su (规格限制)
└── mean, std_dev, cp, cpk (计算统计值)
```

### 文件格式支持

系统使用 **读取器工厂模式** 和公司特定适配器：

- **DCP** - 标准半导体测试数据格式（基于文本）
- **CW** - Cascade 微探针数据（CSV，单/多晶圆模式）
- **MEX** - 基于 Excel 的测试数据
- **ExcelTXT** - Excel 导出的文本格式
- **JT** - Jetech 公司格式（专用 Excel 结构）

`cp_data_processor/readers/company_adapters/` 中的公司适配器处理供应商特定的数据布局。

### 图表生成系统

图表使用 **Plotly** 生成，嵌入 JavaScript 以支持离线查看：

- **YieldChart** - 良率趋势分析、批次对比、参数折线图
- **BoxplotChart** - 参数分布分析，包含规格限制
- **ScatterChart** - 参数相关性分析
- **WaferMapPlotter** - 晶圆表面空间分布

所有图表支持：
- 交互式缩放/平移/悬停
- 离线查看（嵌入式 Plotly.js）
- 批量生成，自动参数检测
- HTML 输出，嵌入样式

### 预期数据结构

系统期望在 `output/` 目录中有特定命名模式的 CSV 文件：

- `*_yield_*.csv` - 良率数据（晶圆级良率）
- `*_spec_*.csv` - 规格限制（参数上下限）  
- `*_cleaned_*.csv` - 清洗后的测试数据（芯片级测量）

### 配置

- **`cp_data_processor/config/settings.py`** - 主配置标志和路径
- **`cp_data_processor/config/performance_config.py`** - 性能优化设置
- `readers/company_adapters/` 中的公司特定配置

### 打包和分发

项目使用复杂的打包系统：

- **`.pyz` 打包** 通过 `packaging/create_pyz.py` 进行安全过滤
- **Anaconda 部署** 自动环境设置
- **安全过滤** 自动排除分发包中的文档和敏感文件

### 性能特性

- **Numba 加速** 用于数学计算
- **并行处理** 用于大数据集  
- **内存优化** 用于处理大晶圆数据
- **智能缓存** 用于图表生成

## 开发说明

- 代码库支持中英文界面
- 所有图表生成离线兼容的 HTML，嵌入 JavaScript
- 系统为 Windows 部署设计，但可跨平台运行
- 未配置正式测试运行器 - 测试主要基于集成测试
- 配置主要基于代码而非文件