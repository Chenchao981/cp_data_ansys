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

Lion 使用横向矩阵式规格文件。成熟格式单次运行保持一份 spec；格式 2 在多 Lot 规格不一致时按 `Lot_ID` 分别输出 `{lot_id}_spec_*.csv`，每份仍保持 `Parameter / UNIT / LIMIT_LOW / LIMIT_HIGH` 四行矩阵。消费方不得任取第一份规格；必须按 cleaned 行的 `Lot_ID` 选择对应 spec。CP Cockpit 会在多规格运行中要求先选择参数分析 Lot，并同步过滤 cleaned/yield。

### 输出文件夹

四家公司统一采用 `<首个真实批次号>_YYYYMMDD_HHMMSS`。多批次输入按稳定的识别/处理顺序取第一个真实批次号；这只影响文件夹名称，不得把后续批次的 `Lot_ID` 改成首批次号。同名目录已存在时追加三位防覆盖流水号，例如 `_001`。

### CP Cockpit 便携文件

Cockpit ZIP 是标准 CSV 的便携分析压缩包，不是新的原始数据格式，也不改变 cleaned/yield/spec 字段和值。压缩包内部包括：

- `manifest.json`：格式标识 `nce-cp-cockpit`、版本号、创建时间，以及每份 CSV 的角色、原始文件名、字节数和 SHA-256。
- `data/*.csv`：本次 Cockpit 实际使用的一份 cleaned、可选的一份 yield，以及零到多份 spec。

每个容器至少需要 cleaned 或 yield；cleaned/yield 各不超过一份。多 Lot 独立 spec 必须全部保存，载入后继续按 `Lot_ID` 选择匹配规格。Cockpit 载入时必须拒绝未知版本、路径穿越、重复/额外文件、大小或哈希不一致，且不得把容器内容解压到用户目录。

## 4. 厂商映射

| 厂商字段 | 标准字段 |
| --- | --- |
| JT `SOFT_BIN` | `Bin` |
| JT `X_COORD` / `Y_COORD` | `X` / `Y` |
| JT `DUT_NO` | `Seq` |
| Lion `PART_INDEX` | `Seq` |
| Lion 格式 2 `DUT_NO` | `Seq` |
| Lion `SOFT_BIN` | `Bin` |
| Lion `X_COORD` / `Y_COORD` | `X` / `Y` |
| Lion `PASSFG` | `CONT` |

Lion 格式 2 明确使用 `pass_bin=1`，保留所有整数 Fail Bin 且不重映射；失败 Die 的后续未测参数保留为空值，不能因此删除整行。`PART_ID`、`SITE_NUM`、`T_TIME`、`TEST_NUM` 属于过程/追溯字段，不作为测量参数。测量参数必须匹配已批准的完整有序 schema：原格式 2 为 15 参数，F0122A1 为 14 参数；不能仅凭“参数位于 TEST_NUM 右侧”接受未知产品结构。
| 国宇 `Serial#` | `Seq` |
| 国宇 `Bin#` | `Bin` |
| 国宇重复 `IR` 列 | `IR_665V_1[nA]` / `IR_665V_2[nA]` |

## 5. 扬州国宇 FRD 单位契约

国宇源文件使用带工程前缀的显示字符串，Reader 在标准 CSV 中转换为数值：

| 参数 | 标准单位 |
| --- | --- |
| `CONT2[mV]` | `mV` |
| `IR_665V_1[nA]` / `IR_665V_2[nA]` | `nA` |
| `VZ1[V]` / `VZ2[V]` / `DELTA[V]` / `VF[V]` | `V` |

国宇参数列名直接标记单位，列下方仅存数值；`spec.csv` 同时保留独立 `Unit` 字段。`F Over` 等失效文本转换为缺失值，但对应 `Bin` 保持原值。当前样例的 `X`、`Y` 均为 0，不能用于真实 Wafer Map 位置分析。

国宇输入目录采用递归发现，支持“产品目录 → 批次目录 → 一个或多个 EDS/数据子目录 → Excel”等多层结构。业务批次号取产品目录下的第一层批次文件夹名称；同一批次内源文件 `LotName` 可能带有 `-D70` 等工艺后缀，不应因此拆分批次。合并输出必须保留每行原始 `Lot_ID`；输出文件夹遵循四家公司共用的首批次号加时间流水号契约。Reader 仅保留 `Serial#` 符合 `P数字`（Pass）或 `F数字`（Fail）的有效 Die 行，排除 `Unit` 行，并校验 Devices、Pass、Fail 与 Bin 统计一致。

## 6. Lion 管芯数汇总契约

`lion-管芯数` 不是 Die 级 CP 标准 CSV，而是 Wafer 级 Excel 业务汇总。格式 1 映射为：

| 输出列 | 源数据 | 规则 |
| --- | --- | --- |
| `NCE品名` | 第 2 行 `DEVICE=` | 取等号后的非空字符串 |
| `LOT` | 第 2 行 `LOT#=` | 取等号后的非空字符串；文件名须为“批号”或“批号 + 空格 + 备注” |
| `Wafer` | `WAFER#` | 大于 0 的整数 |
| `PASS` | `PASS` | CP Pass 数，非负整数 |
| `Good Die` | `DIE` | 管芯数，非负整数；不用 `PASS` 代替 |

处理器递归读取 `.xlsx`，忽略 Excel `~$` 临时锁文件，未知 Sheet/缺字段/重复“NCE品名+LOT+Wafer”均 fail closed。每个文件的 Wafer 行数、`PASS` 合计和 `DIE` 合计必须同时与 `SUMMARY` 一致。输出文件为 `Lion_管芯数.xlsx`，置于“首个真实 Lot_YYYYMMDD_HHMMSS”运行目录。

格式 2（LCD235）使用已批准的完整 34 列有序表头，字段映射为：

| 输出列 | LCD235 源数据 | 规则 |
| --- | --- | --- |
| `NCE品名` | `型号` | 非空字符串 |
| `LOT` | `批号` | 非空字符串；文件名须为“批号”或“批号 + 空格 + 备注” |
| `Wafer` | `片号` | 大于 0 的整数 |
| `PASS` | `CP合格管芯数` | 非负整数 |
| `Good Die` | `CP合格管芯数 - QAD补点数` | 计算结果必须为非负整数 |

LCD235 每个文件的明细行数、`CP合格管芯数` 合计和计算后 `Good Die` 合计，必须分别与摘要中的总片数、CP合格管芯总数和合格管芯总数一致。两种格式可共用同一 GUI 页面和五列输出契约。

## 7. 契约变更规则

- 基础字段改名属于破坏性变更，必须同步修改 Reader、Adapter、CSV、图表和 GUI。
- 新增可选字段应保持旧消费者可用。
- 良率必须明确 `pass_bin`，不能默认所有厂商永远为 Bin 1。
- `StandardCSVGenerator` 必须使用 `CPLot.pass_bin` 计算 `Good_die`、Yield 和良品参数统计，不得在公共层写死 Bin 1。
- 当 `chip_data` 缺少行级 `Lot_ID` 时，生成器使用 `CPWafer.source_lot_id` 回填；只有该值缺失时才回退到 `CPLot.lot_id`。
- 数据精度、单位转换和异常值处理应可追溯，避免在图表阶段静默修改原始结果。

## 8. 新公司生产入口契约

新公司进入 `CompanyCleaningPipeline` 前必须提供已批准的格式档案。Pipeline 依次执行 Reader、Adapter、`StandardLotValidator` 和标准 CSV 生成；`pass_bin` 与批准值不一致、标准字段缺失、重复 `Lot_ID + Wafer_ID` 或空数据时必须停止。Agent、Skill 和格式档案不属于运行时数据契约。
