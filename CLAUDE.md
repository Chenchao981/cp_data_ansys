# CLAUDE.md

这个文件为在此代码仓库中工作的 Claude Code (claude.ai/code) 提供指导。

## 🚀 常用命令

### 快速开始

```bash
# 快速演示（从 output/ 目录生成所有图表）
python chart_generator.py                      # HH公司数据图表生成
python jt_chart_generator.py                   # JT公司数据图表生成

# 模块化架构测试（验证新架构）
python test_modular_architecture.py
```

### GUI应用程序

```bash
# 多公司版本GUI（推荐）
cd gui
python multi_company_gui.py                    # 多公司统一界面
python cp_data_gui.py                          # 简化版界面
python ../cp_data_processor_gui.py             # 完整功能界面
```

### 命令行工具

```bash
# 统一数据处理接口（使用新的模块化架构）
python -c "from cp_data_processor.readers.unified_reader import read_cp_data; from cp_data_processor.processing.standard_csv_generator import generate_standard_csvs; lot = read_cp_data('data.txt'); generate_standard_csvs(lot, 'output/')"

# 传统命令行工具
python cp_data_processor_cli.py <输入文件> <输出文件> [选项]
python cp_data_processor_cli.py data.txt result.xlsx --format dcp --boxplot --bin-map

# JT公司专用处理器
python -m jt_data_processor.jt_main_processor <JT文件路径或目录> --output output
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

### 开发和测试

```bash
# 安装依赖
pip install -r cp_data_processor/requirements.txt  # 核心依赖
pip install -r gui/requirements.txt                # 图形界面依赖

# 模块化架构测试
python test_modular_architecture.py                # 验证新架构工作正常

# 创建 .pyz 发布包
cd packaging
python create_pyz.py

# 运行测试
python -m pytest jt_data_processor/tests/ -v      # JT公司测试
python -m pytest tests/ -v                        # 通用测试（如果存在）
```

## 🏗️ 架构概览

这是一个面向半导体制造业的综合性 **CP (Chip Probing) 测试数据分析平台**，采用**模块化架构**设计，支持多公司数据格式，实现快速扩展。

### 🔄 模块化数据流（新架构）

```
原始数据 → 公司识别 → 公司适配器 → 标准数据处理 → 统一CSV输出 → 图表生成 → GUI展示
```

1. **数据输入** → UnifiedReader 统一读取器（自动识别公司和格式）
2. **公司适配** → CompanyAdapter 将各公司格式转换为标准格式
3. **标准处理** → 清洗、转换、单位转换（统一处理逻辑）
4. **标准输出** → 生成3个标准CSV文件（cleaned、yield、spec）
5. **图表生成** → 基于标准CSV的图表工厂（复用现有图表）
6. **GUI展示** → 多公司统一界面（自动加载公司组件）

### 🎯 新架构优势

- **新公司集成时间**：从2-3周缩短到3-5天
- **代码复用率**：80%以上（只需实现数据适配器）
- **零侵入设计**：现有图表、GUI、打包模块无需修改
- **统一标准**：所有公司数据输出相同的3个CSV文件

### 🔧 核心模块架构

#### 1. 模块化数据处理引擎
- **`cp_data_processor/`** - 具有模块化架构的主要处理引擎
  - `readers/` - 统一读取器和公司适配器系统
    - `unified_reader.py` - 统一数据读取接口
    - `company_adapters/` - 公司特定适配器（HH、JT、新增公司）
    - `reader_factory.py` - 格式读取器工厂
  - `processing/` - 标准化数据处理
    - `standard_csv_generator.py` - 标准CSV生成器（3个文件）
    - `data_transformer.py` - 数据转换逻辑
    - `unit_converter.py` - 单位转换
  - `analysis/` - 统计分析、良率计算、能力分析
  - `plotting/` - 图表生成（基于 Plotly）
  - `exporters/` - Excel 和数据导出功能
  - `data_models/cp_data.py` - 核心数据结构（CPLot、CPWafer、CPParameter）

#### 2. 图表生成系统
- **`frontend/`** - 交互式图表组件（复用架构）
  - `charts/` - 专用图表类（YieldChart、BoxplotChart、SummaryChart 等）
  - `core/` - 数据管理和图表工厂
  - `utils/` - 文件处理和验证工具

#### 3. 多公司GUI系统
- **`gui/`** - 桌面图形界面应用程序（基于 PyQt5）
  - `multi_company_gui.py` - 多公司统一界面（推荐）
  - `widgets/` - 公司特定组件（自动加载）

#### 4. 公司特定处理器（遗留支持）
- **`jt_data_processor/`** - JT公司专用处理器（遗留系统）
- **未来新公司** - 仅需创建适配器即可集成

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

### 📁 支持的公司和格式

系统使用 **模块化适配器架构** 和 **统一读取器**：

#### 当前支持的公司
- **HH公司** (标准格式)
  - DCP - 标准半导体测试数据格式（基于文本）
  - CW - Cascade 微探针数据（CSV，单/多晶圆模式）
  - MEX - 基于 Excel 的测试数据
  - ExcelTXT - Excel 导出的文本格式

- **JT公司** (Jetech 半导体)
  - JT_EXCEL - 专用 Excel 结构（FA*.xls/xlsx）

#### 新公司集成
通过 `cp_data_processor/readers/company_adapters/` 中的适配器系统：
1. 创建公司适配器类（继承 BaseCompanyAdapter）
2. 配置字段映射和单位转换规则
3. 自动集成到统一处理流程

**参考文档**：`add_new_company_data_function.md` - 新公司集成指南

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

### 📊 标准化数据格式

新架构统一所有公司数据为3个标准CSV文件：

#### 标准输出格式（由 StandardCSVGenerator 生成）
- `{lot_id}_cleaned.csv` - 清洗后的测试数据（芯片级测量）
  ```csv
  Lot_ID,Wafer_ID,X,Y,Seq,Bin,Param1,Param2,...
  ```
- `{lot_id}_yield.csv` - 良率数据（晶圆级良率）
  ```csv
  Lot_ID,Wafer_ID,Total_Chips,Good_Chips,Yield_Rate,Bin_1,Bin_2,...
  ```
- `{lot_id}_spec.csv` - 规格限制（参数上下限）
  ```csv
  Parameter,Unit,LimitL,LimitU,LSL,USL,Target
  ```

#### 兼容性支持（遗留格式）
- `*_yield_*.csv` - 旧命名格式的良率数据
- `*_spec_*.csv` - 旧命名格式的规格限制
- `*_cleaned_*.csv` - 旧命名格式的清洗数据

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

## 🛠️ 开发说明

### 基本特性
- 代码库支持中英文界面
- 所有图表生成离线兼容的 HTML，嵌入 JavaScript
- 系统为 Windows 部署设计，但可跨平台运行
- 配置主要基于代码而非文件

### 新架构特性
- **模块化设计**：新公司集成只需3-5天
- **统一接口**：UnifiedReader 自动识别公司和格式
- **标准化输出**：所有公司输出相同格式的CSV文件
- **自动测试**：`python test_modular_architecture.py` 验证架构

### 测试策略
- **架构测试**：`python test_modular_architecture.py` - 验证新架构工作正常
- **公司测试**：`python -m pytest jt_data_processor/tests/ -v` - JT公司专用测试
- **集成测试**：主要基于端到端的数据处理验证

### 新公司开发流程
1. 参考 `add_new_company_data_function.md` 指南
2. 创建公司适配器（约300-500行代码）
3. 配置字段映射和单位转换
4. 运行 `test_modular_architecture.py` 验证集成
5. 图表生成、GUI、打包自动复用现有功能

## 📚 重要文档索引

> 📖 **完整文档导航**: [文档索引.md](文档索引.md) - 包含所有文档的详细分类和使用场景指导

### 核心文档
- `README.md` - 项目主入口和使用说明
- `CLAUDE.md` - 本文档，开发者指南
- `模块化重构计划.md` - 架构重构详细方案

### 新公司集成
- `add_new_company_data_function.md` - 新公司集成完整指南
- `cp_data_processor/readers/company_adapters/README.md` - 适配器模块说明

### 技术特性
- `JavaScript嵌入改进说明.md` - JavaScript离线化改进
- `性能优化集成文档.md` - Numba和asyncio性能优化
- `GUI集成汇总图表功能说明.md` - GUI汇总图表功能

### 用户文档
- `packaging/release/用户手册.md` - 多公司版用户操作手册
- `packaging/release/参数速查.md` - 参数和文件格式速查

### 工具说明
- `clean_dcp_data.md` - DCP数据清洗说明
- `dcp_spec_extractor.md` - DCP规格提取说明
- `cp_unit_converter.md` - 单位转换说明
