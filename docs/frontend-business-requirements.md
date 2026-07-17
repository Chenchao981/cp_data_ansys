# CP 前端业务需求说明

## 1. 背景

功率芯片 CP（Chip Probing）测试数据是研发、工艺、质量和生产管理判断晶圆批次状态的重要依据。当前项目已经可以把 HH、JT、Lion、扬州国宇 FRD 等来源的原始 CP 文件清洗为统一的 `cleaned`、`yield`、`spec` CSV。

前端的目标不是重新清洗数据，而是把清洗后的标准数据转换成研发和质量部门容易理解、容易追溯、容易分享的分析界面和图表报告。

## 2. 目标用户

| 用户角色 | 主要关注点 | 典型问题 |
| --- | --- | --- |
| 研发工程师 | 参数分布、规格边界、异常点、晶圆内分布 | 某个参数是否偏移？是否存在边缘效应？ |
| 工艺工程师 | Wafer Map、区域差异、失效点聚集 | 失效是否集中在 Center / Mid / Edge？ |
| 质量工程师 | 良率、失效 Bin、Cpk、超限数量 | 批次是否满足放行或复判条件？ |
| 生产/测试管理 | 批次良率趋势、Wafer 间差异、失效结构 | 哪些 Wafer 或批次需要优先关注？ |
| IT / 数据维护人员 | 数据契约、部署、问题定位 | 用户打不开图表、找不到数据、结果为空时如何排障？ |

## 3. 前端业务目标

前端需要满足以下业务目标：

1. 让用户在完成 CP 清洗后，可以直接打开分析界面，不需要手工整理 Excel。
2. 支持按批次、Wafer、参数、Bin 查看数据。
3. 支持研发/质量常用统计图：
   - 良率总览
   - Wafer 良率趋势
   - 失效 Bin Pareto
   - 参数 BoxPlot
   - 参数 Wafer 散点图
   - Wafer Mapping
   - Center / Mid / Edge 区域分析
   - Cpk / 超限统计
   - Wafer Summary
4. 支持两种使用习惯：
   - GUI 内一键打开交互式 Cockpit。
   - 生成一个离线 HTML，方便发给其他同事查看。
5. 前端结果必须可追溯到清洗输出文件，不能在展示阶段静默修改测试值。

## 4. 当前前端形态

当前用户侧只保留一类前端：

| 前端 | 入口 | 适用场景 |
| --- | --- | --- |
| CP Cockpit | 各公司页面操作区内的 `CP Cockpit` 按钮，或 `streamlit run frontend/yield_analyzer_app.py` | 工程师交互分析、筛选、切换参数 |

VDMOS 工具只作为界面风格和交互思路参考，不作为用户发布功能。CP Cockpit 只读取标准 CSV：

```text
*_cleaned_*.csv
*_yield_*.csv
*_spec_*.csv
```

## 5. 数据输入需求

### cleaned CSV

用于芯片级明细和参数图表，至少应尽量包含：

| 字段 | 用途 |
| --- | --- |
| `Lot_ID` | 批次筛选、批次追溯 |
| `Wafer_ID` | Wafer 分组、趋势、Summary |
| `X`, `Y` | Wafer Map、区域分析、失效叠加 |
| `Seq` | Die 测试顺序或序号 |
| `Bin` | 良品/失效判断、Bin Pareto |
| 参数列 | BoxPlot、散点、Cpk、分布分析 |

### yield CSV

用于 Wafer 级良率和失效结构分析，核心字段包括：

- `Lot_ID`
- `Wafer_ID`
- `Gross_die`
- `Good_die`
- `Yield`
- 动态 Bin 或失效统计列

### spec CSV

用于规格线、Cpk 和超限统计。前端支持逐参数行或矩阵式规格，但推荐逐参数行：

```text
Parameter,Unit,LimitL,LimitU,LSL,USL,Target
```

## 6. 图表需求

| 图表 | 业务用途 | 关键字段 |
| --- | --- | --- |
| KPI 总览 | 快速看总测试数、良率、Wafer 数、参数数；跨批次时 Wafer 数按 `Lot_ID + Wafer_ID` 计数 | cleaned / yield |
| 良率趋势 | 比较不同 Wafer 或批次良率 | `Wafer_ID`, `Yield` |
| 失效 Bin Pareto | 找主要失效类型 | `Bin` 或 yield 动态 Bin 列 |
| 参数 BoxPlot | 看参数分布、离群值、规格边界 | 参数列、spec |
| 参数 Wafer 散点图 | 看每个参数在不同 Wafer 上的原始点分布和离散程度 | `Lot_ID`、`Wafer_ID`、参数列、spec |
| Wafer Mapping | 默认一次展示全部圆片的同一着色项目；也可选择 1～25 片查看逐 die 详情。可切换综合 Bin 或测试参数，定位 Bin 不良、低于 LSL 和高于 USL 的 die | `Lot_ID`, `Wafer_ID`, `X`, `Y`, `Bin`, 参数列、spec |
| 区域分析 | 比较 Center / Mid / Edge | `X`, `Y`, 参数列 |
| 失效叠加 | 看多个失效点位是否聚集 | `X`, `Y`, `Bin` |
| Wafer Summary | 横向比较 Wafer 的均值、标准差、中位数 | `Wafer_ID`, 参数列 |
| Cpk / 超限表 | 质量评价与规格风险识别 | 参数列、spec |

## 7. 业务边界

前端不承担以下职责：

1. 不读取 HH、JT、Lion、国宇等原始厂商文件。
2. 不修正清洗阶段产生的单位、规格或 Bin 逻辑错误。
3. 不静默删除异常值，不在展示阶段改变原始测试值。
4. 不替代质量部门的放行判定流程；前端只提供统计证据。

如果图表为空或结果异常，应优先检查清洗输出是否符合数据契约，而不是在前端临时补规则。

## 8. 当前限制和后续建议

当前已知限制：

1. 如果 `X`、`Y` 全为 0，Wafer Mapping 和区域分析无法体现真实空间分布。
2. 全参数 BoxPlot 和全参数 Wafer 散点图会一次性展示多张图，参数很多时页面加载会更重。
3. `spec` 中上下限方向必须由清洗程序保证，前端按字段原样展示。
4. 参数 Mapping 只有在所选参数存在 LSL 或 USL 时才能判定不良；前端不会自动交换方向异常的上下限。
5. 全部 Wafer 总览默认关闭逐 die 悬浮文本，以控制 Plotly 页面数据量；着色状态和每片 NG 数仍完整保留。

后续建议：

1. 为前端增加标准 CSV 合同测试，防止字段变更导致图表失效。
2. 针对真实坐标样例补充 Wafer Mapping 和区域分析验证集。
3. 当参数数量很多时，评估按参数分组或分页加载，避免单页过重。
