# CP数据分析工具 - Frontend模块

## 🎯 项目简介
基于现有`python_cp/`模块的CP数据分析工具，提供简单易用的本地数据分析和图表生成功能。

## 🚀 快速开始

### 安装依赖
```bash
pip install pandas matplotlib seaborn numpy scipy
```

### 基本使用
```python
from frontend.main_analyzer import CPDataAnalyzer

# 创建分析器
analyzer = CPDataAnalyzer()

# 一键分析
results = analyzer.analyze_lot("FA54-5339@203", output_dir="./charts")
```

### 命令行使用
```bash
# 生成所有图表
python frontend/main_analyzer.py --lot-id "FA54-5339@203" --output "./charts"

# 生成特定图表
python frontend/main_analyzer.py --lot-id "FA54-5339@203" --charts "scatter,box" --output "./charts"
```

## 📊 支持的图表类型

1. **散点图** - 参数间关联分析
2. **箱体图** - 参数分布分析  
3. **正态分布图** - 单参数正态性分析
4. **良率折线图** - 良率趋势分析

## 📂 模块结构

```
frontend/
├── core/           # 核心管理器
├── adapters/       # 数据适配器
├── charts/         # 图表生成
├── utils/          # 工具函数
└── main_analyzer.py # 主分析器
```

## 📝 数据要求

工具需要以下CSV文件：
- `cleaned.csv` - 清洗后的测试数据
- `yield.csv` - 良率统计数据
- `spec.csv` - 参数规格数据

这些文件通过`python_cp/`模块处理原始CP数据生成。

## 🔧 开发状态

当前项目处于开发阶段，正在按照项目计划逐步实现各个功能模块。

详细开发计划请参考：[cp-data-analyzer-plan.md](./cp-data-analyzer-plan.md)

---

**版本**: v1.0-dev  
**最后更新**: 2025-01-23 