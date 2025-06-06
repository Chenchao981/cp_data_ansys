# CP 数据处理器 Python 版本开发文档

## 项目概览

本项目是原始 VBA CP 数据处理宏的 Python 转换版本。旨在复刻读取多种 CP 测试数据格式 (MEX, DCP, CW)、处理数据、计算统计数据和良率、生成分析图表（箱形图、晶圆图、散点图）以及将结果保存到 Excel 工作簿的核心功能。

### 重构背景

原始程序基于Excel VBA实现，存在以下问题：
1. 代码维护困难，各模块耦合度高
2. 脚本执行效率低，难以处理大量数据
3. 跨平台支持困难，依赖Windows和MS Office

通过使用Python重构，我们提供了一个模块化、可扩展、高效的解决方案。

## 系统架构

该系统采用现代化的模块化架构设计，遵循以下原则：
- **关注点分离**: 每个模块负责特定功能
- **松耦合设计**: 模块间通过明确接口交互
- **可扩展性**: 易于添加新功能和支持新数据格式
- **可测试性**: 组件易于单独测试

### 核心架构图

```
CP数据处理器
├── 数据读取层 (readers)
├── 数据模型层 (data_models)
├── 数据处理层 (processing)
├── 数据分析层 (analysis)
├── 数据可视化层 (plotting)
├── 数据导出层 (exporters)
└── 应用层 (app/cli)
```

## 开发进展与模块说明

### 1. 数据读取模块 (readers)

数据读取模块负责从不同格式的文件中提取CP测试数据，采用工厂模式设计，便于扩展新的数据格式支持。

#### 关键组件：

- **基础读取器抽象类 (`BaseReader`)**: 定义了所有 CP 数据读取器的通用接口。
  - `read(files)`: 读取文件并返回CP数据结构
  - `validate()`: 验证数据格式有效性

- **具体格式读取器**:
  - `CWReader`: 从CSV文件读取CW格式数据（支持单/多晶圆模式）
  - `DCPReader`: 从文本文件读取DCP格式数据 
  - `MEXReader`: 从Excel文件读取MEX格式数据

- **读取器工厂 (`create_reader`)**: 根据格式类型返回对应的读取器实例

#### 实现亮点：

- 使用pandas实现高效数据解析和预处理
- 统一数据结构转换机制，保证输出一致性
- 利用工厂方法模式简化客户端代码

#### 代码示例：

```python
# 使用读取器工厂创建读取器并读取数据
reader = create_reader("dcp")  # 可选: "dcp", "cw", "mex"
data = reader.read("path/to/file.txt")
```

### 2. 数据模型模块 (data_models)

数据模型模块定义了系统中使用的核心数据结构，采用Python dataclass实现，兼顾了数据验证和类型安全。

#### 核心数据结构：

- **`CPLot`**: 表示一个完整的CP测试批次，包含多个晶圆
  - 属性：lot_id, wafer_count, param_count, pass_bin等
  - 方法：update_counts(), combine_data_from_wafers()等

- **`CPWafer`**: 表示单个晶圆的测试数据
  - 属性：wafer_id, die_count, x_size, y_size等
  - 方法：calculate_statistics(), get_bin_data()等

- **`CPParameter`**: 表示测试参数的定义和规格
  - 属性：name, unit, upper_limit, lower_limit等
  - 方法：is_within_limits(), convert_unit()等

#### 数据关系：

- 一个`CPLot`包含多个`CPWafer`
- 每个`CPWafer`包含多个测试点数据和多个参数的测量结果
- `CPParameter`定义了参数的属性和限制

### 3. 数据处理模块 (processing)

数据处理模块负责对读取的原始CP数据进行清洗、转换和增强，以便后续分析。

#### 主要功能：

- **`DataTransformer`类**: 提供数据处理的核心功能
  - 数据清洗：检测和处理异常值、缺失值
  - 数据转换：单位转换、归一化、标准化
  - 数据增强：计算派生参数、添加统计特征

#### 处理方法：

- 异常值检测：四分位法(IQR)和标准差法(σ)
- 数据归一化：min-max归一化和Z-score标准化
- 计算参数：支持基于现有参数的公式计算

#### 使用示例：

```python
# 创建数据转换器并处理数据
transformer = DataTransformer(test_info)
transformer.clean_outliers(method='iqr', threshold=1.5)
transformer.add_calculated_parameter('新参数', lambda df: df['参数1'] + df['参数2'])
processed_data = transformer.data
```

### 4. 数据分析模块 (analysis)

数据分析模块提供对CP数据的统计分析和良率计算功能，利用专业的统计方法对数据进行深入分析。

#### 分析器组件：

- **`StatsAnalyzer`**: 计算参数的统计特性
  - 基本统计量：均值、中位数、标准差、分位数等
  - 分布特征：偏度、峰度、正态性检验等
  - 分组统计：按晶圆、参数分组的统计结果

- **`YieldAnalyzer`**: 计算和分析良率指标
  - 总体良率计算
  - 参数良率分析
  - 晶圆良率分析
  - 不良模式识别

- **`CapabilityAnalyzer`**: 计算工艺能力指标
  - Cp、Cpk计算
  - 进程稳定性评估
  - SPC控制限计算

#### 分析流程：

1. 创建相应的分析器实例
2. 调用analyze()方法执行分析
3. 获取分析结果用于报告生成或可视化

### 5. 数据可视化模块 (plotting)

数据可视化模块负责生成各种图表，帮助直观理解数据特征和分布，基于matplotlib和seaborn构建。

#### 绘图器组件：

- **`BoxPlotter`**: 绘制箱形图
  - 参数分布的箱线图
  - 按晶圆分组的参数箱线图
  - 异常值突显

- **`WaferMapPlotter`**: 绘制晶圆图
  - Bin分布图
  - 参数热力图
  - 缺陷分布图

- **`ScatterPlotter`**: 绘制散点图
  - 参数相关性散点图
  - 趋势线拟合
  - 多参数相关性矩阵

#### 绘图特性：

- 支持交互式图表和静态图表
- 可自定义色彩方案和标签
- 支持导出为多种格式(PNG, PDF等)

#### 使用示例：

```python
# 创建箱形图绘图器并生成图表
plotter = BoxPlotter(test_info)
fig = plotter.plot(group_by='wafer', show_outliers=True).fig
plotter.save('box_plot.png')
```

### 6. 数据导出模块 (exporters)

数据导出模块负责将处理和分析的结果导出为可共享的格式，如Excel文件。

#### 主要组件：

- **`ExcelExporter`**: 导出数据到Excel文件
  - 导出原始数据表
  - 导出分析结果表
  - 嵌入图表
  - 应用格式化和条件格式

#### 导出特性：

- 多工作表组织数据
- 支持公式和数据验证
- 自动调整列宽和格式
- 保存图表为内嵌对象

### 7. 应用层模块 (app/cli/main)

应用层模块将各功能模块集成到统一的界面中，提供GUI和CLI两种使用方式。

#### 应用组件：

- **`CPDataProcessor`**: 核心处理器类(main.py)
  - 封装完整数据处理流程
  - 集成所有功能模块
  - 提供灵活的配置选项

- **`CPDataProcessorApp`**: GUI应用(app.py)
  - 提供直观的用户界面
  - 实时处理反馈
  - 交互式配置

- **命令行接口**: CLI应用(cli.py)
  - 支持批处理
  - 自动化集成
  - 脚本控制

#### 最近的改进：

- **模块化重构**: 将过程式代码重构为面向对象设计
- **错误处理增强**: 添加更细致的异常处理和日志记录
- **接口统一**: 统一GUI和CLI的后端处理逻辑

## 代码演进记录

### 主流程模块重构 (2023-11)

对`main.py`进行了全面重构，主要改进包括：

1. **架构改进**：
   - 将过程式代码重构为`CPDataProcessor`类
   - 增加模块化设计，每个方法专注单一职责
   - 提高代码复用性和可测试性

2. **功能增强**：
   - 改进错误处理和日志记录
   - 使用reader工厂模式替代直接导入
   - 添加返回值检查确保流程正确执行

3. **集成优化**：
   - 与现有GUI和CLI应用实现更好集成
   - 统一使用相同的分析器和绘图器组件
   - 创建统一的数据流和处理管道

### GUI应用开发 (2023-10)

1. **用户界面设计**：
   - 创建直观的文件选择界面
   - 添加测试类型和图表选项配置
   - 实现实时处理日志显示

2. **事件处理**：
   - 添加文件选择和保存对话框
   - 实现处理按钮和进度显示
   - 错误提示和状态反馈

### CLI接口开发 (2023-10)

1. **命令行参数设计**：
   - 支持必要的输入和输出路径参数
   - 添加格式选择和处理选项
   - 实现帮助文档和使用说明

2. **批处理支持**：
   - 支持批量文件处理
   - 错误处理和状态代码
   - 日志输出控制

### 模块化与功能完善 (日期: 2024-05-06)

本次迭代主要关注模块化重构和功能完善：

1.  **散点图功能**: 添加了 `python_cp/plotting/scatter_plot.py` 模块，用于根据配置生成参数间的散点图，并将结果输出到 Excel 文件。主流程 (`main_processor.py`) 已更新，可通过配置文件 (`scatter_plot_configs`, `plot_scatter_plot`) 控制此功能。
2.  **Yield 计算器重构**: 将良率计算逻辑从 `数据类型定义.py` 中提取到独立的 `python_cp/yield_calculator.py` 模块，提高了模块的内聚性。相关的 Excel 导出逻辑 (`excel_exporter.py`) 已更新为调用新模块。
3.  **Reader 模块整理**: 创建了 `python_cp/readers/` 子目录，并将 `CWReader`, `MEXReader`, `DCPReader` 相关代码和文档移入该目录，统一管理数据读取器。
4.  **启用 DCP 读取器**: 在主流程 (`main_processor.py`) 中取消了对 `DCPReader` 相关代码的注释，现在可以通过命令行参数 `--format DCP` 来使用 DCP 格式读取功能。
5.  **通用代码整合**: 移除了冗余的 `通用代码.py` 模块。将其中的核心通用函数（如唯一名称生成、成对字符内容提取、单位转换等）整合进了 `通用工具函数.py`，并更新了 `CWReader` 和 `MEXReader` 以使用整合后的函数。
6.  **文档修复**: 修正了 `wafer_map.md`, `boxplot.md`, `mex_reader.md` 等 Markdown 文件中的换行符问题，提高了文档的可读性。

## 使用说明

### 图形界面使用

1. 运行图形界面程序：

```bash
python cp_data_processor_gui.py
```

2. 在界面中完成配置：
   - 选择输入文件和输出文件
   - 选择测试类型（DCP、CW或MEX格式）和圆片类型
   - 勾选需要的图表选项（箱形图、晶圆图等）

3. 点击"整理数据"按钮开始处理
4. 查看日志区域的处理进度
5. 处理完成后，结果将保存到指定的Excel文件

### 命令行使用

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

## 开发指南

### 环境配置

1. 克隆代码库
2. 安装依赖：`pip install -r requirements.txt`
3. 推荐使用Python 3.8+

### 添加新功能

#### 支持新的数据格式

1. 在`readers`目录创建新的读取器类，继承`BaseReader`
2. 实现`read`方法解析特定格式
3. 在`reader_factory.py`中注册新格式

示例：
```python
# 新格式读取器
class NewFormatReader(BaseReader):
    def read(self, file_paths):
        # 实现读取逻辑
        return data
        
# 在工厂中注册
def create_reader(format_type):
    if format_type == "new_format":
        return NewFormatReader()
    # ...其他格式
```

#### 添加新的分析方法

1. 在`analysis`目录创建新的分析器类
2. 实现`analyze`方法执行特定分析
3. 在`main.py`和应用模块中集成新分析器

#### 添加新的图表类型

1. 在`plotting`目录创建新的绘图器类
2. 实现`plot`方法生成特定图表
3. 在应用模块中添加对应选项

### 代码风格

- 遵循PEP 8编码规范
- 添加详细文档字符串
- 对公共方法编写单元测试
- 使用类型注解提高代码可读性

## 后续计划

### 近期计划 (2023 Q4)

1. **性能优化**：
   - 支持大数据集并行处理
   - 优化内存使用
   - 改进算法效率

2. **功能拓展**：
   - 添加更多数据分析指标
   - 支持更多图表类型
   - 增强导出功能，支持更多格式

3. **用户体验改进**：
   - 优化界面设计
   - 添加处理进度显示
   - 改进错误提示和帮助信息

### 长期规划

1. **Web界面开发**：
   - 开发基于Web的界面
   - 支持远程数据处理
   - 多用户支持

2. **数据库集成**：
   - 添加历史数据存储
   - 支持趋势分析和比较
   - 提供数据查询接口

3. **机器学习集成**：
   - 添加异常检测算法
   - 支持预测分析
   - 提供参数优化建议

## AI工具辅助开发指南

为便于AI工具理解和改进代码，我们提供以下指导：

### 代码结构说明

- 模块化设计：每个功能模块位于独立目录
- 接口一致性：同类组件遵循统一接口
- 依赖注入：组件通过参数注入依赖

### 开发任务提示

要求AI工具协助开发时，建议按以下格式描述任务：

1. **需求描述**：简要说明需求目标
2. **涉及模块**：列出相关代码模块
3. **输入输出**：期望的输入和输出
4. **约束条件**：性能、兼容性等要求

示例：
```
需求：添加对新格式XYZ的支持
涉及模块：readers目录
输入：XYZ格式文件 (.xyz扩展名)
输出：标准CPLot对象
约束：保持与现有读取器接口一致，支持多文件读取
```

### 代码分析建议

为使AI更好地理解代码，请引导其关注：

1. 设计模式：工厂模式、策略模式等使用情况
2. 数据流：数据如何在各模块间传递和转换
3. 扩展点：系统中预留的可扩展接口
4. 配置系统：如何通过配置调整系统行为

## 贡献指南

1. Fork代码库并创建特性分支
2. 添加功能或修复问题
3. 确保通过所有单元测试
4. 提交Pull Request并等待审核

## 联系方式

如有问题或建议，请联系项目维护者。 