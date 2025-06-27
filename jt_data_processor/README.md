# JT数据处理器 (JT Data Processor)

专门用于处理JT公司CP测试数据的独立数据处理模块。基于HH公司的成熟数据处理技术，针对JT公司的特定需求进行定制。

## 🔥 核心特性

### 用户确认的关键配置
- **✅ 禁用单位转换**: JT数据rawdata已与unit匹配，无需转换
- **✅ IQR四分位法**: 默认异常值处理方法，保持数据完整性
- **✅ 精确字段映射**: 用户确认的字段映射关系
- **✅ 准确数据定位**: 按照用户指定的Excel结构解析

### 基于HH公司成熟技术
- **DCPReader设计模式**: 可靠的数据读取架构
- **DataTransformer清洗技术**: 成熟的异常值处理方法
- **BaseCompanyAdapter模式**: 标准化的数据适配流程
- **完整的错误处理和日志记录**: 详细的处理过程跟踪

## 📁 项目结构

```
jt_data_processor/
├── __init__.py                 # 模块初始化
├── README.md                   # 本文档
├── jt_main_processor.py        # 主处理程序
├── readers/                    # 数据读取器
│   ├── __init__.py
│   └── jt_reader.py           # JT Excel文件读取器
├── adapters/                   # 数据适配器
│   ├── __init__.py
│   └── jt_adapter.py          # JT数据适配器
├── config/                     # 配置管理
│   ├── __init__.py
│   └── jt_config.py           # JT配置文件
└── tests/                      # 测试模块
    ├── __init__.py
    └── test_jt_processor.py    # 单元测试
```

## 🚀 快速开始

### 1. 基本使用

```python
from jt_data_processor.jt_main_processor import process_jt_files

# 处理单个JT文件
result = process_jt_files(
    file_paths="path/to/FA44-4149-03.xls",
    output_dir="jt_output",
    pass_bin=1
)

# 处理多个JT文件
result = process_jt_files(
    file_paths=["file1.xls", "file2.xls"],
    output_dir="jt_output"
)
```

### 2. 命令行使用

```bash
# 处理单个文件
python jt_main_processor.py FA44-4149-03.xls -o output_dir

# 处理多个文件
python jt_main_processor.py file1.xls file2.xls -o output_dir -v

# 查看帮助
python jt_main_processor.py --help
```

### 3. 运行测试

```bash
# 运行基础功能测试
python tests/test_jt_processor.py

# 运行完整单元测试
python -m unittest jt_data_processor.tests.test_jt_processor
```

## 📊 数据结构要求

### Excel文件结构（用户确认）

1. **Summary information工作表**:
   - 第8行: Lot ID信息
   - 第9行: Wafer ID信息

2. **Statistics Information工作表**: 
   - 直接跳过，不处理

3. **DUT_DATA工作表**:
   - 第1行: 参数列表头
   - 第2行: 单位信息
   - 第3行: 上限(LimitU)
   - 第4行: 下限(LimitL) 
   - 第6行开始: 实际测试数据

### 字段映射关系（用户确认）

| JT字段名 | 标准字段名 | 说明 |
|---------|-----------|------|
| DUT_NO  | Seq       | 芯片序号 |
| SOFT_BIN| Bin       | Bin值 |
| X_COORD | X         | X坐标 |
| Y_COORD | Y         | Y坐标 |
| TEST_NUM| CONT      | 测试编号 |

## ⚙️ 配置说明

### 核心配置项

```python
# JT公司特定配置
JT_CONFIG = {
    # 🔥 禁用单位转换（重要）
    'disable_unit_conversion': True,
    'unit_conversion': {},  # 空字典
    
    # ✅ IQR异常值处理
    'cleaning_config': {
        'default_outlier_method': 'iqr',
        'replace_outliers_with_nan': True
    },
    
    # ✅ 字段映射
    'field_mapping': {
        'DUT_NO': 'Seq',
        'SOFT_BIN': 'Bin',
        'X_COORD': 'X',
        'Y_COORD': 'Y',
        'TEST_NUM': 'CONT'
    },
    
    # Excel工作表配置
    'excel_sheet_config': {
        'lot_id_row': 8,      # 第8行获取Lot ID
        'wafer_id_row': 9,    # 第9行获取Wafer ID
        'data_start_row': 6   # 第6行开始为数据
    }
}
```

## 📤 输出文件

### 清洗后数据文件
- **文件名**: `{lot_id}_cleaned_data.csv`
- **格式**: 标准CSV格式，每行一个芯片
- **列**: `Lot_ID`, `Wafer_ID`, `Seq`, `Bin`, `X`, `Y`, `CONT`, 以及所有参数列

### 规格文件
- **文件名**: `{original_filename}_spec.csv`
- **列**: `CONT`, `Unit`, `LimitU`, `LimitL`, `TestCond`
- **说明**: TestCond为空（JT公司无测试条件信息）

### 处理报告
- **文件名**: `{lot_id}_processing_report.json`
- **内容**: 处理统计、配置信息、文件列表等

## 🔍 数据处理流程

### 1. 数据读取阶段
- 验证Excel文件格式和存在性
- 从Summary information提取元数据
- 从DUT_DATA读取测试数据和规格信息
- **🔥 重要**: 保持原始数值，不进行单位转换

### 2. 数据转换阶段  
- 应用用户确认的字段映射
- 跳过单位转换逻辑（JT特有）
- 合并所有晶圆数据

### 3. 数据清洗阶段
- 使用IQR四分位法检测异常值
- 异常值替换为NaN（保持数据完整性）
- 应用HH公司的DataTransformer技术

### 4. 输出阶段
- 生成标准格式CSV文件
- 创建规格文件（测试条件为空）
- 生成处理报告

## 🚨 重要提醒

### JT数据特有配置
1. **🔥 单位转换禁用**: JT数据无需单位转换，程序会跳过所有单位转换逻辑
2. **✅ IQR异常值处理**: 默认使用四分位法，保持数据完整性
3. **测试条件为空**: JT公司规格文件中testcond字段设为空值
4. **数据值保持原始**: 输出数据值与Excel原始数据完全一致

### 与现有模块隔离
- JT处理器位于独立文件夹，不影响现有CP数据处理模块
- 自包含的导入和配置系统
- 可以与现有系统并行运行

## 🧪 测试验证

### 配置验证
```python
from jt_data_processor.config.jt_config import JTConfig

# 验证配置正确性
if JTConfig.validate_config():
    print("✅ JT配置验证通过")

# 检查关键配置
print(f"单位转换禁用: {JTConfig.is_unit_conversion_disabled()}")
print(f"异常值方法: {JTConfig.get_cleaning_config()['default_outlier_method']}")
```

### 适配器测试
```python
from jt_data_processor.adapters.jt_adapter import JTAdapter
from jt_data_processor.config.jt_config import DEFAULT_JT_CONFIG

adapter = JTAdapter('JT', DEFAULT_JT_CONFIG)
summary = adapter.get_processing_summary()
print(f"🔥 单位转换禁用: {summary['unit_conversion_disabled']}")
```

## 📞 技术支持

### 常见问题
1. **数据值与原文件不一致**: 检查是否错误调用了单位转换
2. **字段映射错误**: 确认Excel文件的列名与配置匹配
3. **文件读取失败**: 检查Excel文件路径和格式

### 日志排查
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# 运行处理程序，查看详细日志
```

## 📝 版本信息

- **版本**: 1.0.0
- **作者**: CP Data Analysis Team
- **基于**: HH公司成熟数据处理技术
- **专为**: JT公司CP数据处理需求设计

## 🎯 后续计划

1. **性能优化**: 根据实际数据量调整处理策略
2. **扩展功能**: 添加更多JT特定的数据验证规则
3. **集成测试**: 使用真实JT数据进行全面测试
4. **文档完善**: 添加更多使用示例和最佳实践

---

**🔥 重要**: 本处理器严格按照用户确认的要求实现，特别是禁用单位转换和使用IQR异常值处理方法。所有数据处理都基于HH公司的成熟技术，确保可靠性和一致性。 