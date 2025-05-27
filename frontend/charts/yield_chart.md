# YieldChart 良率图表模块

## 📊 概述

`YieldChart` 是一个专门用于生成半导体CP测试良率分析图表的模块，完全复制了 `BoxplotChart` 的成功架构。它能够生成交互式的HTML图表，支持多种良率分析视图，**新增了基于参数的折线图功能，参考箱体图布局方式**。

## 🎯 主要特性

- **完全独立的HTML输出** - 生成可在浏览器中直接打开的交互式图表
- **预生成缓存机制** - 一次加载，多次使用，提高性能
- **批量处理支持** - 支持一次性生成所有图表类型
- **统一架构设计** - 与BoxplotChart保持一致的API设计
- **丰富的图表类型** - 支持4种基础图表 + N种参数折线图
- **🆕 参数折线图** - 基于cleaned数据的参数测试结果，支持双层X轴和规格限制线

## 📈 支持的图表类型

### 基础图表类型

#### 1. Wafer良率趋势图 (`wafer_trend`)
- 显示各批次wafer良率随wafer编号的变化趋势
- 包含平均良率参考线
- 支持多批次对比

#### 2. 批次良率对比图 (`lot_comparison`)
- 对比不同批次的平均良率和标准差
- 柱状图显示，包含误差棒
- 显示每个批次的wafer数量

#### 3. 良率分布直方图 (`yield_distribution`)
- 显示所有wafer良率的分布情况
- 包含平均值和标准差参考线
- 统计分析信息

#### 4. 失效类型分析饼图 (`failure_analysis`)
- 分析各种失效bin的分布情况
- 饼图显示失效类型占比
- 自动过滤零值bin

### 🆕 参数折线图类型 (`param_*`)

#### 特色功能
- **双层X轴设计**: 上层显示Wafer编号(W1~W25)，下层显示批次信息(FA54-xxxx)
- **规格限制线**: 自动从spec数据提取上下限，显示为虚线
- **参数化标题**: 格式为 `参数[单位]@测试条件_yield_line_chart`
- **批次分组显示**: 按批次分组，不同颜色区分
- **交互式悬停**: 显示详细的wafer和参数信息
- **横向滚动支持**: 支持大量数据点的横向查看

#### 数据来源
- **Cleaned数据**: 提供参数测试结果
- **Spec数据**: 提供参数单位、上下限、测试条件等信息
- **自动参数发现**: 自动识别cleaned数据中的可用参数

#### 标题格式示例
- `BVDSS1[V]@250uA_yield_line_chart`
- `IGSS1[A]@10.0V_yield_line_chart`
- `VTH[V]@250uA_yield_line_chart`

## 🚀 快速开始

### 基本使用

```python
from frontend.charts.yield_chart import YieldChart

# 1. 创建实例
chart = YieldChart(data_dir="output")

# 2. 加载数据（yield + spec + cleaned）
if chart.load_data():
    print("数据加载成功！")
    
    # 3. 获取可用图表类型
    chart_types = chart.get_available_chart_types()
    print(f"可用图表: {chart_types}")
    
    # 4. 获取可用参数
    params = chart.get_available_parameters()
    print(f"可用参数: {params}")
    
    # 5. 生成基础图表
    fig = chart.get_chart("wafer_trend")
    saved_path = chart.save_chart("wafer_trend", output_dir="charts")
    
    # 6. 生成参数图表
    param_chart_type = f"param_{params[0]}"
    fig = chart.get_chart(param_chart_type)
    saved_path = chart.save_chart(param_chart_type, output_dir="charts")
    
    # 7. 批量生成所有图表
    saved_paths = chart.save_all_charts(output_dir="all_charts")
```

### 参数图表专用功能

```python
# 获取参数详细信息
param_info = chart.get_parameter_info("BVDSS1")
print(f"单位: {param_info['unit']}")
print(f"上限: {param_info['limit_upper']}")
print(f"下限: {param_info['limit_lower']}")
print(f"测试条件: {param_info['test_condition']}")

# 准备参数图表数据
chart_data, x_labels, param_info, lot_positions = chart.prepare_parameter_chart_data("BVDSS1")
print(f"数据点数: {len(chart_data)}")
print(f"批次信息: {lot_positions}")

# 生成参数化标题
title = chart.generate_chart_title("param_BVDSS1")
print(f"标题: {title}")  # 输出: BVDSS1[V]@250uA_yield_line_chart
```

### 数据要求

#### Yield数据 (*_yield_*.csv)
- `Lot_ID`: 批次标识
- `Wafer_ID`: 晶圆标识  
- `Yield`: 良率（百分比字符串，如"98.50%"）
- `Total`: 总芯片数
- `Pass`: 通过芯片数
- `Bin3`, `Bin4`, `Bin6`, `Bin7`, `Bin8`, `Bin9`: 各失效bin的数量

#### 🆕 Spec数据 (*_spec_*.csv)
```csv
Parameter,CONT,IGSS0,IGSS1,BVDSS1,...
Unit,V,A,A,V,...
LimitU,0.5,9.90E-05,1.00E-07,140,...
LimitL,0,0,0,120,...
TestCond:,1.00mA,1.00V,10.0V,250uA,...
```

#### 🆕 Cleaned数据 (*_cleaned_*.csv)
- `Lot_ID`: 批次标识
- `Wafer_ID`: 晶圆标识
- `Seq`, `Bin`, `X`, `Y`: 芯片位置信息
- `CONT`, `IGSS0`, `IGSS1`, `BVDSS1`, ...: 各参数测试结果

## 🔧 API 参考

### 类初始化

```python
YieldChart(data_dir: str = "output")
```

**参数:**
- `data_dir`: 包含yield、spec、cleaned数据文件的目录路径

### 主要方法

#### `load_data() -> bool`
加载yield、spec、cleaned数据并预生成所有图表缓存。

**返回:** 是否成功加载数据

#### `get_available_chart_types() -> List[str]`
获取所有支持的图表类型列表（基础图表 + 参数图表）。

**返回:** 图表类型列表

#### 🆕 `get_available_parameters() -> List[str]`
获取可用的测试参数列表。

**返回:** 参数列表

#### 🆕 `get_parameter_info(parameter: str) -> Dict`
获取参数的详细信息（单位、上下限、测试条件）。

**参数:**
- `parameter`: 参数名

**返回:** 参数信息字典

#### 🆕 `prepare_parameter_chart_data(parameter: str) -> Tuple`
准备参数图表数据，按Lot_ID分组并生成X轴标签。

**参数:**
- `parameter`: 参数名

**返回:** (图表数据, X轴标签, 参数信息, 批次位置信息)

#### `get_chart(chart_type: str) -> Optional[go.Figure]`
从缓存中获取指定类型的图表。

**参数:**
- `chart_type`: 图表类型（如 "wafer_trend" 或 "param_BVDSS1"）

**返回:** Plotly图表对象

#### `save_chart(chart_type: str, output_dir: str = "charts_output") -> Optional[Path]`
保存指定类型的图表为HTML文件。

**参数:**
- `chart_type`: 图表类型
- `output_dir`: 输出目录

**返回:** 保存的文件路径

#### `save_all_charts(output_dir: str = "charts_output") -> List[Path]`
批量保存所有图表为HTML文件。

**参数:**
- `output_dir`: 输出目录

**返回:** 所有保存文件的路径列表

## 📁 文件结构

```
frontend/charts/
├── yield_chart.py          # 主模块文件
├── yield_chart.md          # 使用说明文档
└── ...

output/                     # 数据目录
├── *_yield_*.csv          # yield数据文件
├── *_spec_*.csv           # spec数据文件（新增）
├── *_cleaned_*.csv        # cleaned数据文件（新增）
└── ...

charts_output/             # 默认输出目录
├── Wafer良率趋势分析_yield_chart.html
├── 批次良率对比分析_yield_chart.html
├── 良率分布统计_yield_chart.html
├── 失效类型分析_yield_chart.html
├── BVDSS1[V]@250uA_yield_line_chart.html    # 新增
├── IGSS1[A]@10.0V_yield_line_chart.html     # 新增
└── ...
```

## 🎨 图表样式配置

可以通过修改 `chart_config` 字典来自定义图表样式：

```python
chart.chart_config = {
    'height': 600,                    # 图表高度
    'font_size': 12,                  # 字体大小
    'title_font_size': 16,            # 标题字体大小
    'colors': ['#1f77b4', '#ff7f0e', ...],  # 颜色方案
    'mean_line_color': '#FF6347',     # 平均线颜色
    'std_line_color': '#FFA500',      # 标准差线颜色
    'min_chart_width': 1200,          # 最小图表宽度（新增）
    'pixels_per_wafer': 40,           # 每个wafer分配的像素（新增）
}
```

## 🔍 示例代码

### 完整示例

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from frontend.charts.yield_chart import YieldChart

def main():
    # 创建图表实例
    chart = YieldChart(data_dir="output")
    
    # 加载数据
    if not chart.load_data():
        print("数据加载失败")
        return
    
    print(f"加载了 {len(chart.wafer_data)} 个wafer的数据")
    print(f"包含 {chart.wafer_data['Lot_Short'].nunique()} 个批次")
    
    # 获取可用参数
    params = chart.get_available_parameters()
    print(f"可用参数: {params}")
    
    # 生成所有图表
    saved_paths = chart.save_all_charts(output_dir="yield_analysis")
    
    print(f"成功生成 {len(saved_paths)} 个图表:")
    for path in saved_paths:
        print(f"  - {path.name}")

if __name__ == "__main__":
    main()
```

### 参数图表专项示例

```python
def analyze_parameter(chart, parameter):
    """分析特定参数"""
    # 获取参数信息
    param_info = chart.get_parameter_info(parameter)
    print(f"参数: {parameter}")
    print(f"单位: {param_info.get('unit', 'N/A')}")
    print(f"规格: {param_info.get('limit_lower', 'N/A')} ~ {param_info.get('limit_upper', 'N/A')}")
    print(f"测试条件: {param_info.get('test_condition', 'N/A')}")
    
    # 准备数据
    chart_data, x_labels, _, lot_positions = chart.prepare_parameter_chart_data(parameter)
    print(f"数据点数: {len(chart_data):,}")
    
    # 各批次统计
    for lot_id, pos_info in lot_positions.items():
        lot_data = chart_data[chart_data['lot_id'] == lot_id]
        mean_val = lot_data['value'].mean()
        std_val = lot_data['value'].std()
        print(f"{lot_id}: 平均 {mean_val:.2e} ± {std_val:.2e}")
    
    # 生成图表
    chart_type = f"param_{parameter}"
    saved_path = chart.save_chart(chart_type, output_dir="parameter_analysis")
    print(f"图表已保存: {saved_path}")

# 使用示例
chart = YieldChart(data_dir="output")
if chart.load_data():
    analyze_parameter(chart, "BVDSS1")
```

## 🐛 故障排除

### 常见问题

1. **数据加载失败**
   - 检查 `data_dir` 目录是否存在
   - 确认目录中有 `*_yield_*.csv` 格式的文件
   - 验证CSV文件包含必需的列

2. **参数图表生成失败**
   - 确认存在 `*_spec_*.csv` 和 `*_cleaned_*.csv` 文件
   - 检查spec数据格式是否正确
   - 验证参数名在spec和cleaned数据中都存在

3. **图表显示异常**
   - 检查数据是否包含有效的数值
   - 确认批次信息格式正确（如 "FA54-5339"）
   - 验证规格限制值是否为有效数字

4. **保存失败**
   - 检查输出目录的写入权限
   - 确认磁盘空间充足

### 调试模式

启用详细日志记录：

```python
import logging
logging.basicConfig(level=logging.INFO)

chart = YieldChart(data_dir="output")
chart.load_data()  # 将显示详细的加载信息
```

## 🔄 与BoxplotChart的对比

| 特性 | YieldChart | BoxplotChart |
|------|------------|--------------|
| 数据源 | yield + spec + cleaned CSV文件 | cleaned + spec CSV文件 |
| 图表类型 | 4种基础图表 + N种参数折线图 | 箱体图+散点图 |
| 参数支持 | ✅ 完整支持 | ✅ 完整支持 |
| 双层X轴 | ✅ | ✅ |
| 规格限制线 | ✅ | ✅ |
| 缓存机制 | ✅ | ✅ |
| HTML输出 | ✅ | ✅ |
| 批量保存 | ✅ | ✅ |
| API设计 | 完全一致 | 完全一致 |

## 📝 更新日志

### v2.0.0 (2024-01-XX)
- 🆕 新增参数折线图功能
- 🆕 支持spec数据和cleaned数据加载
- 🆕 双层X轴设计，参考箱体图布局
- 🆕 自动规格限制线显示
- 🆕 参数化标题生成
- 🆕 批次分组和颜色区分
- 🆕 横向滚动支持大量数据点
- ✅ 保持与BoxplotChart完全一致的API设计

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 支持4种基础图表类型
- 完整的HTML输出功能
- 与BoxplotChart架构保持一致 