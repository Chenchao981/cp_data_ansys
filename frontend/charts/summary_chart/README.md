# Summary Chart 模块

## 概述

Summary Chart 模块用于将所有测量参数的箱体图合并到一个HTML页面中，实现统一查看和对比分析。

## 功能特性

- **📊 合并显示**: 将所有参数的箱体图垂直排列在一个页面中
- **🔄 X轴对齐**: 所有参数共享相同的X轴（wafer_id, lot_id），确保对比一致性
- **📏 Y轴滚动**: 通过垂直滚动查看不同参数
- **↔️ X轴滑动**: 保持原有的水平滑动功能查看不同批次
- **🎨 样式一致**: 复用BoxplotChart的配色和样式
- **📈 完整功能**: 保留散点图、箱体图、上下限线等所有功能

## 使用方法

### 基本用法

```python
from frontend.charts.summary_chart import SummaryChart

# 初始化
chart = SummaryChart(data_dir="output")

# 加载数据
if chart.load_data():
    # 生成并保存合并图表
    saved_path = chart.save_summary_chart(output_dir="charts_output")
    print(f"合并图表已保存到: {saved_path}")
```

### 命令行测试

```bash
cd frontend/charts/summary_chart
python summary_chart.py
```

## 输出文件

- **文件名格式**: `{数据集名称}_summary_chart.html`
- **示例**: `FA54-5339-327A-250501_summary_chart.html`

## 技术实现

### 核心架构

1. **复用设计**: 基于BoxplotChart类进行组合复用，避免重复造轮子
2. **子图布局**: 使用Plotly的`make_subplots`创建垂直排列的子图
3. **共享X轴**: 通过`shared_xaxes=True`确保所有参数的X轴对齐
4. **独立Y轴**: 每个参数有独立的Y轴范围和标签

### 关键方法

- `create_combined_chart()`: 创建合并的箱体图
- `_add_parameter_traces()`: 为每个参数添加箱体图和散点图
- `_add_limit_lines()`: 添加上下限线
- `_configure_layout()`: 配置整体布局和样式

### 样式配置

```python
summary_config = {
    'subplot_height': 450,      # 每个参数子图高度
    'subplot_spacing': 0.02,    # 子图间距
    'title_font_size': 20,      # 主标题字体大小
    'shared_xaxis_title': "Wafer_ID / Lot_ID"
}
```

## 数据要求

### 输入文件

- `*_cleaned_*.csv`: 清洗后的测试数据
- `*_spec_*.csv`: 参数规格文件（包含单位、上下限、测试条件）

### 数据格式

参考BoxplotChart的数据格式要求，确保包含以下字段：
- `Lot_ID`: 批次标识
- `Wafer_ID`: 晶圆标识
- 各测量参数列

## 性能优化

- **缓存复用**: 利用BoxplotChart的数据缓存机制
- **批量处理**: 一次性生成所有参数的图表
- **CDN加载**: 使用unpkg CDN减小HTML文件大小


## 扩展性

模块设计支持以下扩展：
- 自定义子图高度和间距
- 添加新的图表类型
- 自定义配色方案
- 导出其他格式（PNG、PDF等）

## 故障排除

### 常见问题

1. **数据加载失败**
   - 检查数据目录是否包含required的CSV文件
   - 确认文件命名符合`*_cleaned_*.csv`和`*_spec_*.csv`格式

2. **图表为空**
   - 检查参数数据是否有效
   - 确认spec文件中的参数信息完整

3. **X轴不对齐**
   - 确保所有参数使用相同的数据源
   - 检查Lot_ID和Wafer_ID的一致性

### 调试模式

启用详细日志：
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 版本历史

- **v1.0.0**: 初始版本，支持基本的合并箱体图功能 