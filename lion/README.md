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

## 📊 图表生成功能

### 快速开始
```bash
# 确保output目录中有Lion公司的3个CSV文件
# (*_cleaned_*.csv, *_spec_*.csv, *_yield_*.csv)

# 运行Lion图表生成器
python lion/lion_chart_generator.py
```

### 生成的图表类型

#### 1. 参数箱体图 (35个)
- 每个测试参数的独立箱体图和散点图
- 包含规格限制线标注
- 异常值突出显示
- 文件命名：`{参数名}_boxplot_chart.html`

#### 2. 汇总分析图表 (1个)
- 综合展示良率分析和所有参数分析
- 交互式图表支持缩放和悬停提示
- 文件命名：`V{批次ID}_summary_chart.html`

#### 3. 处理报告 (2个)
- **异常值报告**: `lion_outlier_report.html` - 数据质量分析
- **处理报告**: `lion_processing_report.html` - 生成结果汇总

### 功能特性

- ✅ **自动异常值检测**: 使用IQR方法检测和处理异常值
- ✅ **数据验证**: 完整的CSV文件和数据质量验证
- ✅ **列名标准化**: 自动转换为HH标准格式
- ✅ **错误恢复**: 优雅处理各类异常情况
- ✅ **性能优化**: 22秒内完成所有图表生成
- ✅ **详细日志**: 完整的处理过程记录

### 使用示例

```python
# 编程方式调用
from lion.lion_chart_generator import main

# 生成所有图表
success = main()
if success:
    print("图表生成成功！")
```

### 故障排除

#### 常见问题

1. **缺少CSV文件**
   ```
   错误: ❌ 缺少必要的CSV文件
   解决: 确保output目录中存在*_cleaned_*.csv, *_spec_*.csv, *_yield_*.csv文件
   ```

2. **列名不匹配**
   ```
   解决: 系统会自动进行列名标准化转换 (LotID -> Lot_ID, WaferID -> Wafer_ID)
   ```

3. **参数数据不足**
   ```
   警告: ⚠️ 未找到可用的测试参数
   解决: 检查cleaned.csv文件中是否包含数值型测试参数列
   ```

### 性能指标

- **处理速度**: ~22秒 (14,976行数据，35个参数)
- **文件大小**: 单个HTML文件 < 5MB
- **内存使用**: 峰值 < 500MB
- **支持规模**: 15,000+ 芯片数据点

---
*该模块完全支持Lion公司的CP测试数据处理和图表生成需求*