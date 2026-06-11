# cp_data_processor

项目的目标核心包，负责统一数据模型、Reader、公司适配器、处理、分析和标准 CSV 输出。

## 主要模块

- `data_models/cp_data.py`：`CPLot`、`CPWafer`、`CPParameter`
- `readers/`：DCP、CW、MEX、ExcelTXT、JT Reader 与 `UnifiedReader`
- `readers/company_adapters/`：HH、JT、Lion 公司适配器与注册表
- `processing/standard_csv_generator.py`：cleaned、yield、spec CSV
- `analysis/`：良率、统计与制程能力
- `plotting/`：较早期的绘图接口

## Python API

```python
from cp_data_processor.readers.unified_reader import read_cp_data
from cp_data_processor.processing.standard_csv_generator import generate_standard_csvs

lot = read_cp_data("input_file.xlsx", company_code="LION")
files = generate_standard_csvs(lot, "output")
```

自动识别存在误判风险，生产批处理建议显式传入 `company_code`。

完整架构和数据契约见：

- [系统架构](../docs/architecture.md)
- [数据契约](../docs/data-contracts.md)
- [新增公司支持](../docs/company-integration.md)
