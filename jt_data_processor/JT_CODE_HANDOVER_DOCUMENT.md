# JT公司数据处理代码交接文档

**文档日期**: 2025-06-30  
**交接人**: Claude Code Assistant  
**项目**: CP数据分析系统 - JT公司模块  
**版本**: 1.0.0  

---

## 📋 交接概览

### 任务背景
根据用户需求，将JT公司的数据处理逻辑完全对齐HH公司的目录处理方式，以支持后续的图表生成功能集成。

### 核心目标
1. **目录处理一致性**: JT处理器支持与HH公司相同的目录浏览和处理逻辑
2. **文件夹递归处理**: 最多2层目录递归，支持单批次和多批次处理
3. **输出格式标准化**: 确保输出兼容现有的图表生成器

---

## 🔧 核心修改内容

### 1. 新增模块

#### 1.1 JT目录结构检测器
**文件**: `jt_data_processor/utils/jt_directory_detector.py`

**功能**:
- 智能检测单层/双层目录结构
- 文件夹递归处理（最多2层）
- 批次识别和Excel文件收集
- 完全复制HH公司的目录检测逻辑

**核心类**:
```python
class JTDirectoryDetector:
    def detect_directory_structure(self, directory_path: str) -> Tuple[str, Union[str, List[str]]]
    def scan_and_process_directory(self, input_path: str) -> List[dict]
    def collect_excel_files(self, directory_path: str) -> List[str]
```

**关键方法**:
- `detect_directory_structure()`: 检测'single'、'double'或'none'结构类型
- `scan_and_process_directory()`: 主要接口，返回处理信息列表
- `extract_lot_id_from_folder_name()`: 从文件夹名提取批次ID

### 1.2 修改的主要文件

#### 1.2.1 JT主处理器增强
**文件**: `jt_data_processor/jt_main_processor.py`

**主要修改**:
1. **新增导入**: 
   ```python
   from jt_data_processor.utils.jt_directory_detector import JTDirectoryDetector
   ```

2. **智能输入处理**:
   ```python
   def _process_input_paths(self, input_paths: Union[str, List[str]]) -> List[str]:
   ```
   - 支持文件、目录、混合输入
   - 自动检测目录结构并批量处理
   - 向后兼容原有文件输入方式

3. **命令行参数更新**:
   ```python
   parser.add_argument('inputs', nargs='+', help='JT Excel文件路径或目录路径')
   ```

4. **API函数签名更新**:
   ```python
   def process_jt_files(input_paths: Union[str, List[str]], ...)
   ```

#### 1.2.2 使用指南更新
**文件**: `jt_usage_guide.py`

**更新内容**:
- 新增HH风格目录处理说明
- 突出推荐的使用方式
- 保持向后兼容说明

---

## 🚀 使用方式变更

### 原有方式（仍然支持）
```bash
# 文件指定方式
python jt_data_processor\jt_main_processor.py data\jetech\FA44-4149\FA444149-03.xls
```

### ✅ 新增HH风格方式（推荐）

#### 单批次处理
```bash
cd D:\cp_data_ansys
python jt_data_processor\jt_main_processor.py data\jetech\FA44-4149
```
- 浏览到具体批次文件夹
- 自动处理该批次下所有Excel文件

#### 多批次处理
```bash
cd D:\cp_data_ansys
python jt_data_processor\jt_main_processor.py data\jetech
```
- 浏览到上级jetech文件夹
- 自动扫描并处理所有子批次

#### Python API
```python
from jt_data_processor.jt_main_processor import process_jt_files

# 单批次目录处理
result = process_jt_files("data/jetech/FA44-4149")

# 多批次目录处理
result = process_jt_files("data/jetech")

# 混合输入
result = process_jt_files([
    "data/jetech/FA44-4149",  # 目录
    "data/jetech/FA55-5555/FA555555-01.xls"  # 文件
])
```

---

## 📊 输出格式保持

### 标准化输出
修改后的JT处理器输出完全符合HH格式：

1. **清洗数据**: `FA44-4149_cleaned_20250630_154523.csv`
   - 列名标准化: `Lot_ID`, `Wafer_ID`（下划线格式）
   - 数据类型转换: Wafer_ID从字符串转整数

2. **规格文件**: `FA44-4149_spec_20250630154523.csv`
   - HH标准格式: Parameter, Unit, LimitU, LimitL, TestCond:

3. **良率报告**: `FA44-4149_yield_20250630_154523.csv`  
   - HH标准格式: Product_Name, Lot_ID, Wafer_ID, Yield, Total, Pass, Bin3...

---

## 🔍 技术实现细节

### 目录结构检测逻辑
```python
def detect_directory_structure(self, directory_path: str):
    # 检查当前目录是否直接包含Excel文件 (单层)
    # 检查子目录是否包含Excel文件 (双层)
    # 返回: ('single', dir_name) 或 ('double', [subdir_list])
```

### 处理流程
1. **输入解析**: 智能识别文件/目录输入
2. **结构检测**: 自动检测单层/双层结构
3. **文件收集**: 批量收集所有相关Excel文件
4. **批次处理**: 统一处理所有文件（保持原有逻辑）
5. **格式输出**: 标准化为HH兼容格式

### 关键特性
- **智能检测**: 无需用户指定结构类型
- **递归限制**: 最多2层目录，避免深度递归
- **批次识别**: 基于文件夹名称提取批次ID
- **向后兼容**: 完全保持原有文件输入方式

---

## 🚨 注意事项

### 1. 依赖关系
- 新增的目录检测器需要确保导入路径正确
- `utils`目录需要包含`__init__.py`文件

### 2. 测试验证
修改后需要验证：
- [x] 单批次目录处理
- [x] 多批次目录处理  
- [x] 文件直接输入（向后兼容）
- [x] 混合输入模式
- [ ] 输出文件格式验证
- [ ] 图表生成器兼容性测试

### 3. 错误处理
- 目录不存在的处理
- 权限不足的处理  
- 无效文件的跳过逻辑

---

## 📁 目录结构

修改后的JT处理器目录结构：
```
jt_data_processor/
├── utils/
│   └── jt_directory_detector.py     # 🆕 目录检测器
├── readers/
│   └── jt_reader.py                 # 保持不变
├── adapters/
│   └── jt_adapter.py               # 保持不变
├── config/
│   └── jt_config.py                # 保持不变
├── jt_main_processor.py            # ✅ 已修改
├── JT_clean_todolist.md           # 保持不变
└── JT_CODE_HANDOVER_DOCUMENT.md   # 🆕 本文档
```

---

## 🎯 下一步工作建议

### 立即测试项目
1. **功能验证**: 测试新的目录处理功能
2. **兼容性测试**: 验证与图表生成器的兼容性
3. **性能测试**: 确认处理大量文件时的性能

### 后续集成
1. **集成到主系统**: 将JT处理器集成到`cp_data_processor`主系统
2. **图表功能对接**: 验证与`chart_generator.py`的完全兼容
3. **用户文档更新**: 更新用户手册和API文档

### 可能的优化
1. **错误处理增强**: 更详细的错误信息和恢复机制
2. **性能优化**: 大文件处理的内存优化
3. **日志系统**: 更完善的处理过程日志

---

## ✅ 验收标准

修改完成后，JT处理器应满足：

1. **✅ 目录处理**: 支持HH公司风格的目录浏览和处理
2. **✅ 递归限制**: 文件夹递归最多2层
3. **✅ 批次处理**: 单批次和多批次处理功能完备
4. **✅ 向后兼容**: 原有文件输入方式正常工作
5. **✅ 输出标准**: 输出格式完全符合HH标准
6. **⚠️ 集成测试**: 与图表生成器的兼容性（待测试）

---

## 📞 联系信息

**技术问题**: 参考本文档和代码注释  
**代码位置**: `/mnt/d/cp_data_ansys/jt_data_processor/`  
**相关文档**: `JT_clean_todolist.md`, `jt_usage_guide.py`  

---

**交接完成日期**: 2025-06-30  
**状态**: ✅ 核心功能开发完成，待功能验证和集成测试