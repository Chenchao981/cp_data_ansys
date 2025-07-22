# Lion公司CP数据处理模块

Lion公司Excel格式CP测试数据的读取、适配和处理模块。

## 🚀 快速开始

### 批量处理（推荐）
```bash
# 处理./data目录下的所有Lion公司批次数据
python ../lion_batch_processor.py
```

### 单文件演示
```bash
# 演示单个文件的处理流程
python demo_lion_processing.py
```

## 📁 核心文件

### 生产文件
- **`lion_reader.py`** - Lion公司Excel数据读取器
- **`lion_adapter.py`** - Lion格式到标准格式的适配器  
- **`demo_lion_processing.py`** - 单文件处理演示脚本

### 遗留文件
- **`lion_legacy_batch_processor.py`** - 遗留的批次处理器（建议使用根目录的lion_batch_processor.py）
- **`lion_legacy_batch_demo.py`** - 遗留批次处理演示

### 备份文件
- **`*.bak`** - 已弃用的测试文件备份
- **`lion_todolist.md.completed`** - 已完成的开发清单

## ⚡ 功能特点

- **自动识别**：通过文件名模式自动识别Lion公司数据
- **格式转换**：支持Excel格式的规格和测试数据解析
- **标准输出**：生成cleaned.csv、yield.csv、spec.csv标准文件
- **统一接口**：集成到cp_data_processor统一读取器中

## 📊 数据格式

### 输入格式
- Excel文件 (.xlsx/.xls)
- 包含`summary_information`和`dut_data`工作表
- 文件命名：`批次ID_晶圆ID.xlsx` (如: F25130244_1.xlsx)

### 输出格式
- `批次ID_cleaned.csv` - 所有晶圆的测试数据
- `批次ID_yield.csv` - 各晶圆良率统计
- `批次ID_spec.csv` - 参数规格信息

## 🔧 集成使用

Lion模块已完全集成到主系统中，可通过以下方式使用：

```python
# 通过统一读取器
from cp_data_processor.readers.unified_reader import read_cp_data
lot = read_cp_data('path/to/lion_file.xlsx')  # 自动识别Lion格式

# 直接使用Lion读取器
from lion.lion_reader import LionExcelReader
reader = LionExcelReader()
lot = reader.read_file('path/to/lion_file.xlsx')
```

---
*该模块完全支持Lion公司的CP测试数据处理需求*