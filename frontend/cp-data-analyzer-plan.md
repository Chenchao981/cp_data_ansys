# CP数据分析工具 - 方案1项目计划

## 🎯 项目目标
基于现有`python_cp/`模块，快速构建本地CP数据分析工具，让用户能够：
- 输入原始CP数据文件
- 自动生成4种核心图表：散点图、箱体图、正态分布图、良率折线图
- 基于已处理的CSV文件（cleaned.csv、yield.csv、spec.csv）
- 提供简单易用的本地工具界面

## 🏗️ 技术方案：整合现有资源（方案1）

### 核心策略
- **复用python_cp模块**：利用已有的完整数据处理和图表功能
- **frontend作为接口层**：提供统一、易用的API接口
- **CSV文件为数据桥梁**：基于已生成的CSV文件进行图表绘制
- **快速交付**：3-5天内实现完整可用工具

### 数据流程设计
```
原始CP数据 → python_cp处理 → CSV文件输出 → frontend图表生成 → 最终图表文件
```

## 📊 目标图表规格

### 1. 散点图 (Scatter Plot)
- **数据源**: cleaned.csv + spec.csv  
- **功能**: 参数间关联分析，识别参数相关性
- **输出**: PNG/PDF图表文件

### 2. 箱体图 (Box Plot)  
- **数据源**: cleaned.csv + spec.csv
- **功能**: 参数分布分析，识别异常值和分布特征
- **输出**: PNG/PDF图表文件

### 3. 正态分布图 (Normal Distribution)
- **数据源**: cleaned.csv + spec.csv  
- **功能**: 单参数正态性分析，显示分布曲线和统计信息
- **输出**: PNG/PDF图表文件

### 4. 良率折线图 (Yield Trend)
- **数据源**: yield.csv + spec.csv
- **功能**: 良率趋势分析，显示各参数良率变化
- **输出**: PNG/PDF图表文件

## 🗂️ 项目结构

```
cp_data_ansys/
├── python_cp/                    # 现有核心处理模块
│   ├── plotting/                 # 现有图表功能
│   └── ...                      # 其他现有模块
├── frontend/                     # 新增接口层
│   ├── core/                    # 核心管理器
│   │   ├── data_manager.py      # 数据管理器
│   │   ├── chart_factory.py     # 图表工厂  
│   │   └── csv_processor.py     # CSV处理器(新增)
│   ├── adapters/                # 适配器层(新增)
│   │   ├── python_cp_adapter.py # python_cp功能适配器
│   │   └── csv_adapter.py       # CSV文件适配器
│   ├── charts/                  # 图表生成层
│   │   ├── base_chart.py        # 图表基类 ✅ 已完成
│   │   ├── line_chart.py        # 良率折线图 ✅ 已完成  
│   │   ├── scatter_chart.py     # 散点图 (待实现)
│   │   ├── box_chart.py         # 箱体图 (待实现)
│   │   └── normal_chart.py      # 正态分布图 (待实现)
│   ├── utils/                   # 工具层
│   │   ├── file_utils.py        # 文件工具
│   │   └── data_validator.py    # 数据验证
│   └── main_analyzer.py         # 主分析器(新增)
├── output/                      # CSV数据输出目录
└── charts_output/              # 图表输出目录(新增)
```

## 📋 开发任务分解

### 🏗️ 第1阶段：基础架构搭建（2天）

#### 任务1.1：创建项目结构 (0.5天)
**目标**: 建立完整的目录结构和基础文件

**具体任务**:
- [ ] 创建`frontend/adapters/`目录
- [ ] 创建`frontend/utils/`目录  
- [ ] 创建`charts_output/`目录
- [ ] 创建各模块的`__init__.py`文件
- [ ] 创建基础的`README.md`和`.gitignore`

**验收标准**:
- 目录结构完整
- 所有Python包可正确导入
- 基础文件创建完成

#### 任务1.2：实现CSV数据适配器 (0.5天)
**目标**: 创建CSV文件读取和处理功能

**具体任务**:
- [ ] 实现`frontend/adapters/csv_adapter.py`
  - [ ] 实现`load_cleaned_data(lot_id)`方法
  - [ ] 实现`load_yield_data(lot_id)`方法  
  - [ ] 实现`load_spec_data(lot_id)`方法
  - [ ] 添加数据验证和错误处理
- [ ] 实现`frontend/core/csv_processor.py`
  - [ ] 实现CSV文件路径解析
  - [ ] 实现数据合并和预处理功能
  - [ ] 添加数据格式验证

**验收标准**:
- 能正确读取现有的CSV文件
- 数据格式验证正常
- 错误处理完善

#### 任务1.3：升级数据管理器 (1天)
**目标**: 升级DataManager支持CSV数据源

**具体任务**:
- [ ] 修改`frontend/core/data_manager.py`
  - [ ] 添加CSV数据源支持
  - [ ] 集成csv_adapter
  - [ ] 实现数据缓存机制
  - [ ] 添加批次ID自动识别
- [ ] 实现单元测试
  - [ ] 测试数据加载功能
  - [ ] 测试缓存机制
  - [ ] 测试错误处理

**验收标准**:
- DataManager能正确加载CSV数据
- 缓存机制工作正常
- 单元测试通过

### 📊 第2阶段：图表模块实现（2天）

#### 任务2.1：实现图表基类 (0.5天)
**目标**: 创建统一的图表接口

**具体任务**:
- [ ] 实现`frontend/charts/base_chart.py`
  - [ ] 定义图表基类接口
  - [ ] 实现通用的保存和配置功能
  - [ ] 添加图表元数据管理
- [ ] 实现图表配置管理
  - [ ] 定义图表样式配置
  - [ ] 实现配置文件读取

**验收标准**:
- 基类接口设计合理
- 配置管理功能完善
- 易于扩展新图表类型

#### 任务2.2：实现散点图 (0.5天)
**目标**: 基于cleaned.csv和spec.csv生成散点图

**具体任务**:
- [ ] 实现`frontend/charts/scatter_chart.py`
  - [ ] 实现参数选择逻辑（X轴、Y轴参数）
  - [ ] 添加规格限值线显示
  - [ ] 实现颜色映射（按Bin着色）
  - [ ] 添加统计信息显示
- [ ] 添加配置选项
  - [ ] 图表尺寸配置
  - [ ] 颜色方案配置
  - [ ] 标题和标签配置

**验收标准**:
- 能生成清晰的散点图
- 规格限值线正确显示
- 支持多种参数组合

#### 任务2.3：实现箱体图 (0.5天)
**目标**: 基于cleaned.csv和spec.csv生成箱体图

**具体任务**:
- [ ] 实现`frontend/charts/box_chart.py`
  - [ ] 实现多参数箱体图绘制
  - [ ] 添加规格限值线
  - [ ] 实现异常值标注
  - [ ] 添加统计信息显示
- [ ] 优化图表布局
  - [ ] 自动调整参数排列
  - [ ] 添加参数单位显示
  - [ ] 实现图表分页

**验收标准**:
- 箱体图布局合理
- 异常值标识清晰
- 统计信息准确

#### 任务2.4：实现正态分布图 (0.5天)
**目标**: 基于cleaned.csv和spec.csv生成正态分布图

**具体任务**:
- [ ] 实现`frontend/charts/normal_chart.py`
  - [ ] 实现直方图+正态拟合曲线
  - [ ] 添加统计参数显示（均值、标准差、Cpk等）
  - [ ] 实现规格限值区域标注
  - [ ] 添加正态性检验结果
- [ ] 实现批量生成
  - [ ] 支持多参数批量分析
  - [ ] 自动参数筛选（过滤常数参数）

**验收标准**:
- 正态分布拟合准确
- 统计指标计算正确
- 图表信息丰富易读

### 🔧 第3阶段：工厂模式和主控制器（1天）

#### 任务3.1：实现图表工厂 (0.5天)
**目标**: 统一的图表创建和管理接口

**具体任务**:
- [ ] 升级`frontend/core/chart_factory.py`
  - [ ] 实现图表类型注册机制
  - [ ] 添加批量图表生成功能
  - [ ] 实现图表生成任务队列
  - [ ] 添加进度追踪功能
- [ ] 实现图表模板管理
  - [ ] 预定义常用图表组合
  - [ ] 支持自定义图表配置

**验收标准**:
- 图表创建接口统一
- 批量生成功能正常
- 支持灵活配置

#### 任务3.2：实现主分析器 (0.5天)
**目标**: 提供一键式分析功能

**具体任务**:
- [ ] 实现`frontend/main_analyzer.py`
  - [ ] 实现批次自动识别
  - [ ] 添加全套图表生成功能
  - [ ] 实现输出目录管理
  - [ ] 添加生成报告功能
- [ ] 实现命令行接口
  - [ ] 支持参数配置
  - [ ] 添加帮助信息
  - [ ] 实现日志输出

**验收标准**:
- 一键生成所有图表
- 命令行接口友好
- 日志信息完整

### 🧪 第4阶段：测试和优化（1天）

#### 任务4.1：功能测试 (0.5天)
**目标**: 验证所有功能正常工作

**具体任务**:
- [ ] 测试数据加载功能
  - [ ] 测试多种批次数据
  - [ ] 验证数据格式兼容性
  - [ ] 测试异常数据处理
- [ ] 测试图表生成功能
  - [ ] 验证4种图表正确生成
  - [ ] 测试不同参数组合
  - [ ] 检查图表质量和准确性
- [ ] 测试批量处理功能
  - [ ] 测试多批次处理
  - [ ] 验证输出文件组织

**验收标准**:
- 所有测试用例通过
- 图表质量符合要求
- 批量处理稳定

#### 任务4.2：性能优化和文档 (0.5天)
**目标**: 优化性能并完善文档

**具体任务**:
- [ ] 性能优化
  - [ ] 优化数据加载速度
  - [ ] 改进图表生成效率
  - [ ] 添加内存管理
- [ ] 完善文档
  - [ ] 编写用户使用手册
  - [ ] 添加API文档
  - [ ] 创建示例和教程
- [ ] 错误处理优化
  - [ ] 完善异常处理机制
  - [ ] 添加用户友好的错误信息

**验收标准**:
- 性能满足要求
- 文档完整易懂
- 错误处理友好

## 🚀 使用场景设计

### 场景1：命令行快速分析
```bash
# 一键生成所有图表
python frontend/main_analyzer.py --lot-id "FA54-5339@203" --output "./charts"

# 生成特定类型图表
python frontend/main_analyzer.py --lot-id "FA54-5339@203" --charts "scatter,box" --output "./charts"
```

### 场景2：Python脚本调用
```python
from frontend.main_analyzer import CPDataAnalyzer

# 创建分析器
analyzer = CPDataAnalyzer()

# 一键分析
results = analyzer.analyze_lot("FA54-5339@203", output_dir="./charts")

# 生成特定图表
scatter_chart = analyzer.create_scatter_chart("FA54-5339@203", x_param="Vth", y_param="Idsat")
```

### 场景3：批量处理
```python
# 批量处理多个批次
lot_ids = ["FA54-5339@203", "FA54-5340@203", "FA54-5341@203"]
results = analyzer.batch_analyze(lot_ids, output_dir="./batch_charts")
```

## 📈 项目里程碑

| 阶段 | 完成时间 | 交付物 | 验收标准 |
|------|----------|--------|----------|
| 第1阶段 | 第2天 | 基础架构+数据管理 | 能正确加载CSV数据 |
| 第2阶段 | 第4天 | 4种图表实现 | 所有图表正确生成 |
| 第3阶段 | 第5天 | 统一接口+主控制器 | 一键分析功能正常 |
| 第4阶段 | 第6天 | 测试优化+文档 | 生产就绪状态 |

## 🎯 成功标准

### 功能要求
- [ ] 支持基于CSV文件的图表生成
- [ ] 4种图表类型全部实现
- [ ] 一键批量分析功能
- [ ] 命令行和Python API双接口

### 质量要求
- [ ] 图表清晰美观，信息丰富
- [ ] 数据处理准确，统计指标正确
- [ ] 错误处理完善，用户体验友好
- [ ] 代码结构清晰，易于维护

### 性能要求
- [ ] 单批次分析时间 < 30秒
- [ ] 支持同时处理10+批次数据
- [ ] 内存使用合理，无内存泄漏

## 📝 开发注意事项

### 代码规范
- 使用中文注释和日志信息
- 遵循PEP8代码风格
- 添加类型提示
- 完善异常处理

### 测试数据
- 使用现有的`data/`目录真实数据
- 测试多种数据格式和边界情况
- 验证图表在不同数据规模下的表现

### 文档要求
- 每个模块包含详细的docstring
- 关键函数添加使用示例
- 提供完整的用户手册
- 包含故障排除指南

---

**文档版本**: v1.0  
**创建日期**: 2025-01-23  
**预计完成**: 6个工作日  
**项目状态**: 待开始 