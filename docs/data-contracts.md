# 数据契约

## 1. 核心对象

### `CPLot`

表示一个批次或合并批次，关键字段：

- `lot_id`：批次标识
- `product`：产品标识
- `wafers`：`CPWafer` 列表
- `params`：`CPParameter` 列表
- `pass_bin`：合格 Bin，默认 `1`
- `combined_data`：合并后的芯片级数据

### `CPWafer`

表示单片 Wafer，关键字段：

- `wafer_id`
- `source_lot_id`
- `seq`、`bin`、`x`、`y`
- `chip_data`：芯片级 `pandas.DataFrame`
- `yield_rate`、`pass_chips`、`fail_chips`

### `CPParameter`

表示测试参数及规格/统计：

- `id`、`unit`
- `sl` / `su`：规格下限与上限
- `mean`、`std_dev`、`median`
- `cp`、`cpk`、`yield_rate`

## 2. 标准字段

芯片级数据至少应尽量提供：

| 字段 | 含义 |
| --- | --- |
| `Lot_ID` | 原始批次 |
| `Wafer_ID` | 晶圆编号 |
| `X`, `Y` | Die 坐标 |
| `Seq` | Die 测试顺序或序号 |
| `Bin` | Soft Bin |

测试参数列位于基础字段之后。`CONT`、`SITE_NUM`、`T_TIME` 等属于可选过程字段。

## 3. 三类 CSV

标准生成器默认使用带时间戳的文件名：

```text
{lot_id}_cleaned_YYYYMMDD_HHMM.csv
{lot_id}_yield_YYYYMMDD_HHMM.csv
{lot_id}_spec_YYYYMMDD_HHMM.csv
```

### cleaned

芯片级明细。基础字段在前，测试参数在后。多批次合并时必须保留每行原始 `Lot_ID`。

### yield

Wafer 级良率汇总。当前实现以 `Gross_die`、`Good_die`、`Yield` 为核心，并可能动态增加 Bin 或参数失效计数字段。消费方不应假定失效 Bin 列固定。

### spec

参数规格。HH/JT 通常使用逐参数行结构，例如 `Parameter`、`Unit`、`LimitL`、`LimitU`、`LSL`、`USL`、`Target`。

Lion 当前可能输出横向矩阵式规格文件。图表或后续数据接口必须先确认 spec 布局，不能只按一种结构硬编码。

## 4. 厂商映射

| 厂商字段 | 标准字段 |
| --- | --- |
| JT `SOFT_BIN` | `Bin` |
| JT `X_COORD` / `Y_COORD` | `X` / `Y` |
| JT `DUT_NO` | `Seq` |
| Lion `PART_INDEX` | `Seq` |
| Lion `SOFT_BIN` | `Bin` |
| Lion `X_COORD` / `Y_COORD` | `X` / `Y` |
| Lion `PASSFG` | `CONT` |

## 5. 契约变更规则

- 基础字段改名属于破坏性变更，必须同步修改 Reader、Adapter、CSV、图表和 GUI。
- 新增可选字段应保持旧消费者可用。
- 良率必须明确 `pass_bin`，不能默认所有厂商永远为 Bin 1。
- 数据精度、单位转换和异常值处理应可追溯，避免在图表阶段静默修改原始结果。
