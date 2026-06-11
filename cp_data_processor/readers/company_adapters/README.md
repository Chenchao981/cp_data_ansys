# Company Adapters

公司适配器负责把厂商 Reader 产生的 `CPLot` 转换为公共字段和数据类型。

## 组件

- `base_company_adapter.py`：适配器抽象基类
- `company_config.py`：公司名称、格式、字段映射、识别规则和 Bin 配置
- `company_registry.py`：适配器注册、实例化和自动识别
- `hh_adapter.py`：HH 基准格式
- `jt_adapter.py`：JT 字段映射和单位转换
- `lion_adapter.py`：连接 `lion/lion_adapter.py`

## 使用

```python
from cp_data_processor.readers.unified_reader import read_cp_data

lot = read_cp_data("input.xlsx", company_code="JT")
```

自动识别依赖路径、文件名和 `can_process_file()`，存在 Excel 厂商误判风险。生产流程应优先显式指定公司。

新增适配器流程见 [新增公司支持](../../../docs/company-integration.md)。
