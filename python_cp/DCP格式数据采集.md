# DCP格式数据采集工具

本文档描述了`DCP格式数据采集.py`的功能、使用方法及实现逻辑，用于半导体晶圆测试数据的处理与分析。

## 功能概述

DCP格式是半导体测试领域中常用的一种数据格式，包含晶圆测试的参数定义、测试条件及每个芯片的测试结果。本工具提供以下核心功能：

1. 读取DCP格式Excel文件
2. 提取测试参数定义（名称、单位、规格等）
3. 提取晶圆测试数据（坐标、Bin值、参数测量值）
4. 实现单位自动换算（如mV→V, μA→A等）

本工具专注于数据采集和处理功能，不包含可视化部分，遵循模块化设计原则，以便后续与其他可视化模块集成。

## 文件格式说明

DCP格式文件通常为Excel格式，具有以下结构：

- 第1行：文件标题，第2列包含产品名(.dcp后缀)
- 第3行：晶圆ID在第2列
- 第7行：参数名称(从第5列开始)
- 第8行：参数上限
- 第9行：参数下限(包含单位信息)
- 第10-15行：测试条件
- 第16行开始：芯片测试数据
- 数据结构：第1列为序号，第2/3列为x/y坐标，第4列为Bin值，第5列及之后为各参数测试值

## 代码结构

### 核心类

1. **TestItem** - 测试参数定义类
   - 存储参数名称、单位、规格上下限、测试条件等信息

2. **WaferInfo** - 晶圆信息类
   - 存储晶圆ID、坐标数据、Bin值及各参数测量值

3. **LotInfo** - 批次信息类
   - 存储产品名称、晶圆列表、参数定义列表

4. **DCPDataParser** - 数据解析器类
   - 实现文件读取、格式验证、数据提取功能
   - 处理单位换算

### 常量定义

代码中定义了一系列常量指定DCP文件中各项信息的位置：

```python
PARAM_START_COL = 4  # 参数起始列(Python中索引从0开始)
STD_ITEM_ROW = 6     # 标准项目行
USER_ITEM_ROW = 6    # 用户项目行
UPPER_ROW = 7        # 上限行
LOWER_ROW = 8        # 下限行
COND_START_ROW = 9   # 测试条件开始行
COND_END_ROW = 14    # 测试条件结束行
DATA_START_ROW = 15  # 数据开始行
```

## 使用示例

### 基本使用

```python
# 创建解析器
parser = DCPDataParser()

# 解析DCP文件
lot_info = parser.parse_file("path/to/your/dcp_file.xlsx")

# 访问解析结果
print(f"产品名称: {lot_info.product}")
print(f"晶圆数量: {lot_info.wafer_count}")
print(f"参数数量: {lot_info.param_count}")

# 访问第一片晶圆的信息
if lot_info.wafer_count > 0:
    wafer = lot_info.wafers[0]
    print(f"晶圆ID: {wafer.wafer_id}")
    print(f"芯片数量: {wafer.chip_count}")
    
    # 计算良率
    pass_count = np.sum(wafer.bin == 1)  # 假设Bin=1为通过
    yield_rate = pass_count / wafer.chip_count if wafer.chip_count > 0 else 0
    print(f"良率: {yield_rate:.2%}")
```

### 数据处理

```python
# 获取某个参数的所有测量值
param_index = 1  # 第一个参数
param_data = wafer.chip_datas[param_index]

# 进行基本的统计分析
mean_value = np.mean(param_data)
std_dev = np.std(param_data)
min_value = np.min(param_data)
max_value = np.max(param_data)

print(f"平均值: {mean_value}")
print(f"标准差: {std_dev}")
print(f"最小值: {min_value}")
print(f"最大值: {max_value}")
```

## 实现细节

### 数据解析流程

1. **文件读取**：使用pandas读取Excel文件
2. **格式验证**：检查文件基本格式是否符合DCP规范
3. **空行检查**：确保第6行为空行，如果不是则插入空行
4. **参数解析**：提取测试参数信息（首次导入时）
5. **晶圆数据提取**：提取晶圆ID、坐标、Bin值等基本信息
6. **测试数据提取**：提取各个参数的测试结果数据

### 单位换算实现

代码使用正则表达式处理不同的单位前缀，实现自动换算：

```python
def _cal_rate(self, rate_str):
    """计算单位换算率"""
    rates = {
        'm': 0.001,          # 毫 (milli)
        'u': 0.000001,       # 微 (micro)
        'n': 0.000000001,    # 纳 (nano)
        'p': 0.000000000001, # 皮 (pico)
        'f': 0.000000000000001, # 飞 (femto)
        'k': 1000,           # 千 (kilo)
    }
    return rates.get(rate_str, 1.0)  # 默认为1
```

### 数据结构优化

- 使用NumPy数组存储测试数据，提高处理效率
- 使用字典映射参数位置，实现快速访问
- 使用dataclass简化类定义

## 注意事项

1. 本工具需要以下Python库：
   - pandas：用于Excel文件读取
   - numpy：用于数据处理
   - re：用于正则表达式处理

2. DCP文件格式可能有细微变化，如有需要，请调整常量定义适应不同格式

3. 单位换算目前支持以下前缀：m(毫)、u(微)、n(纳)、p(皮)、f(飞)、k(千)

## 与其他模块集成

本模块设计为专注于数据采集和解析，可以轻松与其他功能模块集成：

1. **可视化模块**：使用解析后的数据创建各种图表
2. **数据分析模块**：进行深入的统计分析和机器学习
3. **报告生成模块**：生成晶圆测试报告
4. **数据存储模块**：将解析的数据保存到数据库或其他格式

## 故障排除

如果遇到解析错误，请检查：

1. 文件格式是否符合DCP标准
2. 文件是否包含完整数据
3. 常量定义是否与文件实际格式匹配

如有其他问题，请与开发人员联系。 