# Lion公司图表生成功能规划文档

## 📋 项目概述

基于Lion公司已完成的数据清洗功能，规划并实现图表生成功能。Lion公司的CP数据已成功清洗并输出为标准的3个CSV文件格式，现需要复用现有的前端图表模块生成专业的数据分析图表。

## 📊 数据基础

### 已完成的数据清洗
- **数据源**: `./data` (Lion公司Excel格式)
- **输出目录**: `./output/` (标准化CSV文件)
- **清洗状态**: ✅ 已完成，生成3个标准CSV文件

### 标准输出文件
1. **`*_cleaned_*.csv`** - 芯片级测试数据 (1008行 x 20列)
   - 包含所有测试参数和坐标信息
   - 字段: Seq, Bin, X, Y, KELVIN_CHECK, IR_35V, IR_1000V, etc.

2. **`*_yield_*.csv`** - 良率统计数据 (1行 x 多列)
   - 批次良率: 99.4% (优秀水平)
   - 失效分析: 各参数失效计数

3. **`*_spec_*.csv`** - 参数规格信息 (13行 x 7列)
   - 测试参数规格限制
   - 单位信息和目标值

## 🎯 图表生成目标

### 核心图表类型
1. **📈 良率分析图表**
   - 批次良率趋势
   - 失效类型分析
   - 批次良率对比

2. **📦 参数箱体图**
   - 13个测试参数的独立箱体图
   - 散点图叠加显示
   - 规格限制线标注

3. **📋 汇总分析图表**
   - 良率图和参数分析的综合展示
   - 一页式分析报告

## 🔧 技术实现方案

### 方案选择: 复用现有前端模块
参考JT公司的成功实现，直接复用HH公司的前端图表模块:
- `frontend.charts.yield_chart.YieldChart`
- `frontend.charts.boxplot_chart.BoxplotChart` 
- `frontend.charts.summary_chart.SummaryChart`

### 实现优势
- ✅ **零开发成本**: 直接复用成熟的图表模块
- ✅ **格式兼容**: Lion的CSV输出已标准化为HH格式
- ✅ **功能完整**: 支持所有主流图表类型
- ✅ **质量保证**: 经过JT公司验证的稳定方案

## 📝 开发任务清单

### 🚀 Phase 1: 创建Lion图表生成器 (优先级: 高)

#### 任务1.1: 创建lion_chart_generator.py
- [ ] **文件位置**: `./lion/lion_chart_generator.py`
- [ ] **功能**: 复用HH前端模块生成Lion公司图表
- [ ] **参考**: `jt_chart_generator.py` 的实现模式
- [ ] **输入**: `./output/` 目录下的3个CSV文件
- [ ] **输出**: `./output/` 目录下的HTML图表文件

#### 任务1.2: 实现核心功能函数
- [ ] **generate_yield_charts()**: 良率图表生成
  - 使用 `YieldChart` 模块
  - 生成3个良率分析图表
  
- [ ] **generate_boxplot_charts()**: 箱体图生成
  - 使用 `BoxplotChart` 模块
  - 为13个测试参数生成独立图表
  - 包含散点图叠加和规格限制
  
- [ ] **generate_summary_chart()**: 汇总图表生成
  - 使用 `SummaryChart` 模块
  - 生成综合分析报告

#### 任务1.3: 数据兼容性处理
- [ ] **列名标准化**: 确保CSV列名符合HH格式要求
  - 检查 `Lot_ID`, `Wafer_ID` 等关键字段
  - 必要时进行列名转换
- [ ] **数据验证**: 验证CSV文件完整性和格式正确性

### 🔄 Phase 2: 测试和优化 (优先级: 中)

#### 任务2.1: 功能测试
- [ ] **单元测试**: 测试各个图表生成函数
- [ ] **集成测试**: 测试完整的图表生成流程
- [ ] **数据验证**: 确认图表数据的准确性

#### 任务2.2: 性能优化
- [ ] **生成速度**: 优化图表生成效率
- [ ] **文件大小**: 控制HTML文件大小
- [ ] **错误处理**: 完善异常处理机制

### 📚 Phase 3: 文档和集成 (优先级: 低)

#### 任务3.1: 使用文档
- [ ] **更新README.md**: 添加图表生成功能说明
- [ ] **使用示例**: 提供完整的使用示例
- [ ] **故障排除**: 常见问题和解决方案

#### 任务3.2: 系统集成
- [ ] **GUI集成**: 集成到现有的GUI界面
- [ ] **批处理支持**: 支持批量图表生成
- [ ] **命令行接口**: 提供CLI调用方式

## 📋 实现细节

### 代码结构设计
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lion公司图表生成器 - 复用HH公司前端图表模块
基于Lion公司的3个清洗CSV文件生成专业分析图表
"""

def main():
    """Lion公司图表生成主函数"""
    # 1. 配置数据目录
    lion_data_dir = Path("output")
    
    # 2. 验证CSV文件存在性
    # 3. 生成良率图表
    # 4. 生成箱体图表 
    # 5. 生成汇总图表

def generate_yield_charts(data_dir, output_dir):
    """使用YieldChart模块生成良率图表"""
    
def generate_boxplot_charts(data_dir, output_dir):
    """使用BoxplotChart模块生成箱体图"""
    
def generate_summary_chart(data_dir, output_dir):
    """使用SummaryChart模块生成汇总图表"""
```

### 预期输出图表
1. **良率图表** (3个HTML文件)
   - `lion_yield_trend.html` - 良率趋势分析
   - `lion_failure_analysis.html` - 失效类型分析
   - `lion_batch_comparison.html` - 批次对比分析

2. **参数箱体图** (13个HTML文件)
   - `lion_KELVIN_CHECK_boxplot.html`
   - `lion_IR_35V_boxplot.html`
   - `lion_IR_1000V_boxplot.html`
   - ... (其他10个参数)

3. **汇总图表** (1个HTML文件)
   - `lion_summary_analysis.html` - 综合分析报告

## 🎯 成功标准

### 功能完整性
- ✅ 成功生成所有类型的图表
- ✅ 图表数据准确反映Lion公司测试结果
- ✅ HTML文件可在浏览器中正常显示

### 质量标准
- ✅ 图表美观专业，符合工程分析要求
- ✅ 交互功能正常（缩放、悬停提示等）
- ✅ 生成速度合理（< 30秒完成所有图表）

### 兼容性
- ✅ 与现有数据清洗流程无缝衔接
- ✅ 支持不同批次的Lion数据
- ✅ 可集成到现有GUI和CLI工具中

## 📊 异常值处理方案

### 方案背景

基于JT和HH公司的成功实践，为Lion公司的cleaned.csv数据制定异常值处理策略，确保图表生成的数据质量和可靠性。

### 异常值检测方法

#### IQR方法（推荐）
- **原理**: 基于四分位数间距(Interquartile Range)检测异常值
- **阈值**: Q1 - 1.5×IQR ≤ 正常值 ≤ Q3 + 1.5×IQR
- **优势**: 对数据分布要求较低，适用于非正态分布数据
- **实现**: 复用`DataValidator.detect_outliers(method="iqr")`

### 处理策略
1. **异常值标记为NaN**: 保留原始数据结构，便于后续处理和可视化
#### 数据保护原则
- **标记而非删除**: 异常值标记为NaN，保持原始数据结构完整
- **可追溯性**: 记录异常值位置和检测方法
- **批次独立**: 按参数分别进行异常值检测

#### 实施流程
```
1. 加载cleaned.csv数据
2. 识别测试参数列（排除LotID、WaferID、X、Y、Bin等基础列）
3. 对每个参数执行异常值检测：
   - 按批次(LotID)分组处理
   - 应用IQR方法检测异常值
   - 将异常值标记为NaN
   - 记录异常值统计信息
4. 生成异常值处理报告
5. 输出处理后的数据用于图表生成
```

### 技术实现

#### 代码结构
```python
class LionOutlierHandler:
    def __init__(self, method="iqr", threshold=1.5):
        self.method = method
        self.threshold = threshold
    
    def detect_and_handle_outliers(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """检测并处理异常值"""
        pass
    
    def generate_outlier_report(self, outlier_stats: Dict) -> str:
        """生成异常值处理报告"""
        pass
```

#### 集成方案
- **位置**: 在`lion_chart_generator.py`中的数据加载后、图表生成前
- **复用**: 直接使用`frontend.utils.data_validator.DataValidator`
- **配置**: 支持方法选择和阈值调整

### 输出规范

#### 处理后数据
- **文件**: `./output/cleaned_processed.csv`（可选，用于调试）
- **格式**: 与原cleaned.csv相同，异常值标记为NaN

#### 异常值报告
- **文件**: `./demo_output/generated_charts/outlier_report.html`
- **内容**: 
  - 各参数异常值统计（数量、比例）
  - 检测方法和阈值信息
  - 异常值分布可视化
  - 处理前后数据对比

### 质量控制

#### 验证标准
- 异常值检测率控制在合理范围（通常<5%）
- 保持数据完整性（行数不变）
- 关键参数的有效数据量满足统计要求

#### 监控指标
- 每个参数的异常值数量和比例
- 批次间异常值分布差异
- 处理前后参数统计特征变化

## 📅 开发时间线

### Week 1: 核心开发
- Day 1-2: 创建 `lion_chart_generator.py` 基础框架
- Day 3-4: 实现良率图表生成功能和异常值处理模块
- Day 5-7: 实现箱体图表生成功能

### Week 2: 完善和测试
- Day 1-2: 实现汇总图表功能
- Day 3-4: 功能测试和bug修复
- Day 5-7: 性能优化和文档编写

## 🔍 风险评估

### 低风险项
- ✅ **数据格式兼容**: Lion的CSV已标准化
- ✅ **技术可行性**: JT公司已验证方案可行
- ✅ **模块稳定性**: HH前端模块经过充分测试
- ✅ **异常值处理**: 可复用现有的数据验证逻辑

### 需要关注的点
- ⚠️ **参数特异性**: Lion的13个测试参数可能需要特殊处理
- ⚠️ **数据规模**: 确保1008个芯片数据的图表性能
- ⚠️ **规格限制**: 验证规格限制线的正确显示
- ⚠️ **异常值影响**: 确保异常值处理不影响数据分析结果

## 📞 技术支持

### 参考资源
- **JT实现**: `jt_chart_generator.py` - 成功案例
- **通用实现**: `chart_generator.py` - 基础框架
- **前端模块**: `frontend/charts/` - 核心图表库
- **HH案例**: 华虹公司的完整实现

### 开发环境
- **Python版本**: 3.7+
- **依赖库**: pandas, plotly, pathlib
- **测试数据**: `./output/F25130244_*.csv`

---

**项目状态**: 📋 规划完成，等待开发启动  
**预期完成时间**: 2周  
**技术风险**: 低  
**业务价值**: 高 - 为Lion公司提供完整的CP数据分析解决方案