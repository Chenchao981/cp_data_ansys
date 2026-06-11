# lion

Lion Excel 数据读取、适配和图表模块。当前推荐批量入口位于仓库根目录：

```powershell
python lion_batch_processor.py
```

该脚本扫描 `data/` 下的批次目录，读取并合并数据，通过 `StandardCSVGenerator` 生成三类 CSV。

## 核心文件

- `lion_reader.py`：读取 `summary_information` 与 `dut_data`
- `lion_adapter.py`：字段标准化
- `lion_chart_generator.py`：验证 CSV、异常值处理和图表生成
- `lion_legacy_batch_processor.py`：遗留批处理器

图表入口：

```powershell
python -m lion.lion_chart_generator
```

注意：

- Lion spec 当前可能使用横向矩阵布局。
- 自动公司识别规则较宽，生产流程建议显式选择 Lion。
- 多批次合并必须保留原始 `Lot_ID`。

详见 [系统架构](../docs/architecture.md) 与 [数据契约](../docs/data-contracts.md)。
