# ✅ JT 数据清洗转换计划 (JT Clean Todo List)

**目标**: 将JT公司的CP数据 (以 `FA44-4149-03.xls` 为例) 转换为与HH公司对齐的标准CSV格式。

**核心挑战**: JT数据源是Excel文件，其结构通常比HH的TXT文件复杂，需要进行数据重塑（unpivot/melt）和字段/单位转换。

---

## ✅ 用户确认信息 (User Confirmations)

1. **✅ JT数据结构分析**: 与实际 `FA44-4149-03.xls` 文件完全匹配
2. **✅ 字段映射关系**: 完整准确，确认使用指定的映射关系
3. **✅ 异常值处理方法**: 同意使用IQR四分位法作为默认异常值处理方法
4. **🔥 重要：JT数据无需单位转换**: **JT公司的rawdata数据不需要单位转换，DUT_DATA第六行开始的数据都与上面的unit单位匹配，不需要转换。请勿调用单位转换逻辑！**

---

## 📝 任务清单

### 阶段一：HH公司成熟技术学习与应用 (Analysis & Learning)

-   [x] **分析HH公司数据清洗流程**: 已完成技术学习
    -   **核心技术栈**: DCPReader + DataTransformer + clean_csv_data + 异常值处理
    -   **数据清洗方法**: 
        - 标准差法 (std_dev): 超出均值±3倍标准差的数据标记为异常值
        - **IQR四分位法 (iqr)**: ✅**已确认为JT数据默认方法** - 超出Q1-1.5*IQR 或 Q3+1.5*IQR 的数据标记为异常值
        - 异常值处理: 替换为NaN，而非删除数据行
    -   **数据流程**: 读取 → 合并晶圆数据 → 数据清洗 → 字段重排 → CSV输出 → 生成规格文件 → 良率报告
    -   **字段重排顺序**: `['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y', 'CONT', 优先参数, 其他参数]`
    -   **数据转换器**: 使用DataTransformer类的clean_data方法进行异常值处理

-   [x] **分析标准CSV格式**: 已完成。目标格式为每行一个Die，包含 `Lot_ID`, `Wafer_ID`, `X`, `Y`, `Bin` 及多个参数列。

-   [x] **分析JT XLS格式**: ✅**已确认与实际文件匹配**
    -   **元数据定位**: 
        - `Summary information` 工作表：第8行获取 `Lot Id`，第9行获取 `WAFER_ID`
        - `Statistics Information` 工作表：**直接跳过，不处理**
    -   **测试数据定位**: 
        - `DUT_DATA` 工作表：第1行为参数列表头，第2行为单位信息，第3-4行为规格限制，第6行开始为实际测试数据
        - **字段映射**: ✅**已确认准确** - `Seq = DUT_NO`, `Bin = SOFT_BIN`, `X = X_COORD`, `Y = Y_COORD`, `CONT = TEST_NUM`
        - **参数列处理**: `TEST_NUM` 及右侧所有参数列都需要处理和映射
    -   **规格文件生成**: 
        - 参数列: `CONT`（对应TEST_NUM）及右侧所有参数
        - 单位信息: `Unit = Unit`（第2行）
        - 规格限制: `LimitU = LimitU`（第3行）, `LimitL = LimitL`（第4行）
        - **测试条件**: `testcond = 空值`（JT公司数据没有测试条件信息）
    -   **🔥 重要：单位转换策略**: 
        - **JT数据无需单位转换**: 第6行开始的rawdata数据已与第2行的unit单位匹配
        - **禁止调用单位转换逻辑**: 在JT适配器中明确跳过单位转换步骤

### 阶段二：开发JT数据读取与转换模块 (Development) - 应用HH成熟技术

-   [ ] **1. 创建 `jt_reader.py`** - 基于HH公司DCPReader设计模式:
    -   **技术选型**: 使用 `pandas` 库，参考DCPReader的异常处理和日志记录机制
    -   **元数据读取**: 
        - 从 `Summary information` 工作表的第8行精确提取 `Lot Id`
        - 从 `Summary information` 工作表的第9行精确提取 `WAFER_ID`
    -   **测试数据读取**: 
        - 从 `DUT_DATA` 工作表读取，跳过前5行，第1行作为表头
        - 提取第2行作为单位信息字典（仅用于规格文件生成，不用于数据转换）
        - 提取第3-4行作为规格限制信息
        - 从第6行开始读取实际测试数据
    -   **异常处理**: 参考HH公司的异常处理机制，包含详细的日志记录
    -   **🔥 单位转换标记**: 在读取器中明确标记JT数据无需单位转换

-   [ ] **2. 实现 `jt_adapter.py`** - 基于HH公司DataTransformer清洗技术:
    -   **继承结构**: 继承 `BaseCompanyAdapter`，应用HH公司的适配器设计模式
    -   **数据转换流程**: 
        - 调用 `jt_reader` 获取元数据和测试数据DataFrame
        - **字段映射**: ✅**已确认映射关系** - 根据用户确认的映射关系重命名列
            ```python
            field_mapping = {
                'DUT_NO': 'Seq',
                'SOFT_BIN': 'Bin', 
                'X_COORD': 'X',
                'Y_COORD': 'Y',
                'TEST_NUM': 'CONT'
            }
            ```
        - **🔥 跳过单位转换**: **明确跳过单位转换逻辑** - JT rawdata已与unit匹配，不调用convert_units方法
        - **数据清洗**: 应用HH公司的DataTransformer.clean_data方法
            - ✅**使用IQR四分位法** - 作为默认异常值处理方法
            - 异常值替换为NaN而非删除
            - 保持数据完整性
        - **数据整合**: 将 `Lot Id` 和 `Wafer_ID` 添加到每一行
        - **字段重排**: 按照HH公司的标准顺序重排列

-   [ ] **3. 扩展规格文件生成** - 基于HH公司的dcp_spec_extractor:
    -   **规格数据提取**: 从 `DUT_DATA` 工作表提取规格信息
        - 参数列: `CONT` 及右侧所有参数
        - 单位: 第2行对应的单位信息（直接使用，无需转换）
        - 上限: 第3行的 `LimitU` 值
        - 下限: 第4行的 `LimitL` 值  
        - 测试条件: 设置为空值（JT公司无此信息）
    -   **输出格式**: 参考HH公司的spec.csv格式

### 阶段三：集成与测试 (Integration & Test) - 应用HH成熟验证方法

-   [ ] **1. 更新 `company_config.py`** - 基于HH公司配置管理:
    -   **完整JT配置**:
        ```python
        'JT': {
            'name': 'JT公司',
            'supported_formats': ['.xls', '.xlsx'],
            'field_mapping': {
                'DUT_NO': 'Seq',
                'SOFT_BIN': 'Bin',
                'X_COORD': 'X', 
                'Y_COORD': 'Y',
                'TEST_NUM': 'CONT'
            },
            # 🔥 重要：JT数据禁用单位转换
            'unit_conversion': {},  # 空字典 - JT数据无需单位转换
            'disable_unit_conversion': True,  # 明确标记禁用单位转换
            'file_pattern': r'^FA\d{4}-\d{4}-\d{2}\.xls$',
            'data_validation': {
                'required_fields': ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y'],
                'optional_fields': ['CONT']
            },
            # 数据清洗配置
            'cleaning_config': {
                'default_outlier_method': 'iqr',  # 使用IQR四分位法
                'outlier_threshold': None  # IQR方法不需要阈值
            }
        }
        ```

-   [ ] **2. 扩展 `reader_factory.py`** - 基于HH公司工厂模式:
    -   **JT读取器注册**: 添加JT读取器到工厂类
    -   **文件识别**: 基于文件扩展名和命名模式自动识别JT文件
    -   **单位转换标记**: 传递单位转换禁用标记

-   [ ] **3. 编写单元测试 `test_jt_adapter.py`** - 基于HH公司测试框架:
    -   **测试数据**: 使用 `tests/fixtures/jt_sample_data/` 下的样本文件
    -   **测试覆盖**: 
        - DataFrame结构验证（shape, columns, dtypes）
        - 关键数据抽样检查（Lot ID, Wafer ID, 参数值）
        - 异常值处理验证（IQR方法）
        - 字段映射正确性检查
        - **🔥 单位转换禁用验证** - 确保没有调用单位转换逻辑
        - 数据值完整性检查（原始数据值保持不变）

-   [ ] **4. 端到端测试** - 基于HH公司完整流程:
    -   **完整流程测试**: 运行主处理脚本，验证JT数据处理完整性
    -   **输出验证**: 确保生成的CSV文件符合标准格式
    -   **数据值验证**: 确认输出数据值与原始Excel文件中的数值完全一致
    -   **性能验证**: 参考HH公司的处理性能基准

### 阶段四：技术债务清理与优化 (Technical Debt & Optimization)

-   [ ] **1. 代码质量优化**:
    -   **日志系统**: 应用HH公司的日志记录标准
    -   **异常处理**: 使用HH公司的异常处理模式
    -   **代码复用**: 最大化复用HH公司的成熟代码组件
    -   **单位转换逻辑隔离**: 确保JT适配器中的单位转换跳过逻辑清晰明确

-   [ ] **2. 性能优化**:
    -   **数据处理**: 应用HH公司的数据处理优化技术
    -   **内存管理**: 参考HH公司的大数据处理方法
    -   **跳过不必要步骤**: 由于无需单位转换，可优化处理速度

---

## 🔧 HH公司成熟技术应用总结

### 核心技术栈
1. **数据读取器模式**: 专用读取器类 + 工厂模式
2. **数据转换器**: DataTransformer类，包含clean_data方法
3. **适配器模式**: BaseCompanyAdapter基类 + 厂商特定实现
4. **异常值处理**: ✅**IQR四分位法**（JT默认）和标准差法，替换为NaN
5. **字段管理**: 标准化字段重排和优先参数处理
6. **输出流程**: clean_csv_data + 规格文件生成 + 良率报告

### 关键设计原则
- **数据完整性**: 异常值标记为NaN而非删除
- **可扩展性**: 基于配置文件的字段映射和单位转换
- **错误处理**: 详细的日志记录和异常处理机制
- **测试驱动**: 完整的单元测试和端到端测试

### JT公司特殊处理
- **🔥 禁用单位转换**: JT数据天然匹配，无需调用转换逻辑
- **✅ IQR异常值处理**: 使用四分位法作为默认异常值检测方法
- **直接字段映射**: 简化的字段重命名，无需复杂转换

---

## 👨‍💻 确认完成事项 ✅

1. **✅ 数据定位确认**: JT数据结构分析与实际 `FA44-4149-03.xls` 文件完全匹配
2. **✅ 字段映射确认**: 字段映射关系完整准确，已集成到配置中
3. **✅ 异常值处理方法确认**: 使用IQR四分位法作为JT数据默认处理方法
4. **✅ 单位转换策略确认**: **JT rawdata无需单位转换，明确禁用单位转换逻辑调用**

---

## 🚀 下一步行动计划

基于用户确认信息，可以立即开始：

1. **立即开始**: 创建 `jt_reader.py`，实现Excel文件读取逻辑
2. **紧接着**: 实现 `jt_adapter.py`，特别注意跳过单位转换步骤
3. **配置更新**: 更新 `company_config.py`，加入JT公司完整配置
4. **测试验证**: 编写测试用例，确保单位转换禁用生效

**关键提醒**: 在整个开发过程中，务必确保JT适配器不调用任何单位转换相关的代码逻辑！ 

jt_data_processor/
├── __init__.py                 # 模块初始化  
├── README.md                   # 完整使用文档
├── jt_main_processor.py        # 主处理程序
├── readers/
│   └── jt_reader.py           # JT Excel读取器
├── adapters/  
│   └── jt_adapter.py          # JT数据适配器
├── config/
│   └── jt_config.py           # JT配置管理
└── tests/
    └── test_jt_processor.py    # 单元测试 

现在JT数据清洗程序已经完全准备就绪！您可以：
立即测试配置：运行 python jt_data_processor/tests/test_jt_processor.py
处理实际数据：使用命令行或Python API处理JT Excel文件
查看详细文档：参考 jt_data_processor/README.md
所有功能都严格按照您确认的要求实现，特别是禁用单位转换和使用IQR四分位法处理异常值！