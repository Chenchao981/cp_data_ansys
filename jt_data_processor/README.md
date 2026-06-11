# jt_data_processor

JT Excel 数据的成熟专用处理链，当前仍由多公司 GUI 直接调用。

## 入口

```powershell
python -m jt_data_processor.jt_main_processor <file_or_dir> --output <output_dir>
```

```python
from jt_data_processor.jt_main_processor import process_jt_files

result = process_jt_files("input_dir", output_dir="output", pass_bin=1)
```

## 流程

```text
JT Excel
  -> JTReader
  -> JTAdapter
  -> IQR 清洗与字段标准化
  -> cleaned / yield / spec CSV
  -> 共用 frontend 图表
```

主要字段映射和输出契约见 [数据契约](../docs/data-contracts.md)。

测试：

```powershell
python -m pytest jt_data_processor/tests/ -v
```

仓库中还存在 `cp_data_processor/readers/jt_reader.py` 与公司适配器版本，合并两套实现前必须做回归验证。
