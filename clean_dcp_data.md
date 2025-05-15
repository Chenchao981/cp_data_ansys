# clean_dcp_data.py 说明文档

## 功能概述

`clean_dcp_data.py` 是一个完整的DCP格式数据处理工具，用于读取、提取、清洗和输出半导体晶圆测试数据。该工具专门针对DCP格式的TXT文件，能够自动完成从原始数据到清洗后CSV文件的全流程处理。

## 主要功能

1. **DCP文件识别与读取**：自动识别并读取目录中的DCP格式TXT文件
2. **数据提取与解析**：使用DCPReader模块提取数据，构建CPLot数据结构
3. **异常值检测与处理**：支持IQR和标准差两种异常值处理方法
4. **数据整理与输出**：将处理后的数据整理为标准格式并输出为CSV文件
5. **列格式优化**：调用clean_csv_data.py进行列排序优化

## 命令行参数

```
python clean_dcp_data.py [--dir 目录路径] [--output 输出目录] [--method 异常值处理方法]
```

| 参数 | 短选项 | 描述 | 默认值 |
|------|-------|------|--------|
| `--dir` | `-d` | 包含DCP文件的目录路径 | "./data" |
| `--output` | `-o` | 输出目录路径 | "./output" |
| `--method` | `-m` | 异常值处理方法 (std_dev或iqr) | "iqr" |

## 执行流程

1. **查找DCP文件**：搜索指定目录中的TXT文件，并识别DCP格式
2. **创建DCPReader**：初始化DCPReader处理找到的文件
3. **读取数据**：调用reader.read()提取数据到CPLot对象
4. **数据转换与清洗**：使用DataTransformer进行异常值处理
5. **收集处理后数据**：整理晶圆数据，确保必要字段存在
6. **输出原始CSV**：保存处理后的原始数据为CSV格式
7. **应用CSV清洗**：调用clean_csv_data.py进行列顺序优化
8. **生成最终CSV**：输出最终清洗后的CSV文件

## 主要函数

| 函数名 | 描述 |
|--------|------|
| `process_directory` | 处理指定目录中的所有DCP文件 |
| `process_lot_data` | 处理批次数据并保存 |
| `collect_wafer_data` | 从CPLot对象的晶圆中收集数据 |
| `find_dcp_files` | 查找目录中的DCP格式TXT文件 |
| `main` | 主函数，处理命令行参数并调用处理函数 |

## 依赖模块

- `cp_data_processor.readers.dcp_reader`：DCP格式文件读取器
- `cp_data_processor.processing.data_transformer`：数据转换与清洗
- `cp_data_processor.data_models.cp_data`：CP数据模型
- `clean_csv_data`：CSV数据清洗工具

## 输出文件

工具会生成两种输出文件：
1. **原始数据CSV**：处理后但未优化列顺序的数据，命名格式为`{lot_id}_{timestamp}.csv`
2. **清洗后CSV**：列顺序优化后的最终数据，命名格式为`{lot_id}_{timestamp}_cleaned_{timestamp}.csv`

## 使用示例

```python
# 使用默认参数处理data目录中的DCP文件
python clean_dcp_data.py

# 指定目录和异常值处理方法
python clean_dcp_data.py --dir data/FA53-5465-305A-250303@203_001 --method iqr

# 指定输出目录
python clean_dcp_data.py --dir data/NCEHSM650PBA_C127251.00@CP --output custom_output
```

## 注意事项

- 确保安装了所有依赖模块
- 输入目录必须存在并包含DCP格式的TXT文件
- 如果输出目录不存在，脚本会自动创建
- 处理过程会生成日志文件，命名格式为`dcp_process_{timestamp}.log`

## 未来改进方向

1. 增加并行处理能力，提高大量文件处理效率
2. 增强异常值检测算法，支持更多方法
3. 添加更多数据可视化功能
4. 改进错误处理和用户反馈机制 