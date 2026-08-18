# CP 前端系统设计

## 1. 设计原则

CP 前端遵循以下原则：

1. 清洗与展示分离：Reader / Processor 负责清洗，前端只负责加载标准 CSV 和展示图表。
2. 标准数据契约优先：前端入口统一消费 `cleaned`、`yield`、`spec` 三类 CSV。
3. GUI 与命令行并存：普通用户从 GUI 使用，IT 或开发人员可用 CLI 自动化。
4. 离线优先：报告应尽量支持内网和无公网环境使用。
5. 不静默改数据：图表阶段不改变测试值、Bin、规格上下限。

## 2. 总体架构

```mermaid
flowchart LR
    A["厂商原始 CP 文件"] --> B["公司专用清洗流程"]
    B --> C["标准 CSV 输出目录"]
    C --> C1["*_cleaned_*.csv"]
    C --> C2["*_yield_*.csv"]
    C --> C3["*_spec_*.csv"]
    C --> D["frontend 数据加载层"]
    D --> E["CP Cockpit<br/>Streamlit + Plotly"]
    G["PyQt 多公司 GUI"] --> B
    G --> E
```

## 3. 模块职责

| 模块 | 职责 |
| --- | --- |
| `gui/multi_company_gui.py` | 多公司桌面入口，提供公司清洗和 CP Cockpit 按钮 |
| `gui/widgets/` | 各公司数据清洗界面，维护输入输出路径 |
| `frontend/cp_dashboard_app.py` | Streamlit 交互式 Cockpit 主界面 |
| `frontend/yield_analyzer_app.py` | 兼容入口，转到 `cp_dashboard_app.py` |
| `frontend/charts/` | Plotly 离线图表组件 |
| `docs/data-contracts.md` | 前端和清洗程序共同遵守的数据契约 |

## 4. 数据流设计

### 4.1 清洗阶段

用户在 GUI 中选择公司和输入目录，清洗流程输出：

```text
output/<批次或流水目录>/
  <lot>_cleaned_YYYYMMDD_HHMM.csv
  <lot>_yield_YYYYMMDD_HHMM.csv
  <lot>_spec_YYYYMMDD_HHMM.csv
```

清洗阶段负责：

- 原始文件解析
- 字段映射
- 单位转换
- Bin 判断
- 规格提取
- CSV 输出

### 4.2 前端加载阶段

前端从用户选择的输出目录开始递归查找最新的标准 CSV。这一点很重要，因为真实输出经常在 `output/<batch>/` 子目录中。

查找规则：

```text
cleaned: *_cleaned_*.csv 或 *cleaned*.csv
yield:   *_yield_*.csv   或 *yield*.csv
spec:    *_spec_*.csv    或 *spec*.csv
```

### 4.3 图表展示阶段

前端根据标准字段生成图表：

| 数据来源 | 主要消费图表 |
| --- | --- |
| cleaned | BoxPlot、散点、Wafer Map、区域分析、Cpk、数据预览 |
| yield | 良率趋势、Wafer 汇总 |
| spec | 规格线、Cpk、超限统计 |

## 5. CP Cockpit 设计

CP Cockpit 是交互式分析界面，适合工程师边看边切换参数。

左侧分析表单提供批次、片号、参数筛选器。首次加载均为全选；用户可保留 1 个或多个选项。片号选择项使用 `Lot_ID + Wafer_ID` 组合键，显示为“批次 / W片号”。另有“参数样本范围”选项：`全部 Die` 或 `仅 Good Die`（`Bin = Pass Bin`）。Good Die 只作用于参数 BoxPlot、散点、区域参数、Wafer Summary、Cpk 和 cleaned 数据预览；KPI、良率、Bin、Pareto、Mapping 和失效叠加仍使用当前批次/片号范围内的全部 Die，防止良率被筛选结果虚高。页面先保存筛选草稿，首次打开不执行 Plotly 图表函数；只有点击“绘制图形”时才记录筛选快照。筛选草稿再次变化时停止展示旧图并要求重新点击，避免每次勾选都触发重计算。源 CSV 与测试值保持不变。

图表页采用侧边栏分组折叠菜单，按“数据总览、失效分析、空间分析、参数分析、数据查看”组织页面。一次只渲染当前选中的分析页，避免旧的横向多页签在每次交互时同时计算全部 Plotly 图表。当前 Cockpit 压缩包以紧凑状态条显示，cleaned/yield/spec 文件清单折叠放在侧边栏底部，不遮挡筛选和绘图操作。

Cockpit 还支持便携 ZIP 分析压缩包。该文件带有版本清单，只封装前端已经使用的标准 cleaned/yield/spec CSV，不包含厂商原始文件，也不改变测试值。用户通过文件选择器手动选择此前保存的 ZIP；载入时在内存中验证路径、版本、文件数量与完整性，不向磁盘解压。清单记录每个文件的角色、原始文件名、大小和 SHA-256。多 Lot 独立 spec 文件全部保留，载入后继续使用现有按 Lot 隔离逻辑。

数据管理交互参考 `F:\vdmos\VDMOS_Tool_v5.6.html` 的两个操作，但保持 CP 数据契约不变：`保存数据` 下载上述 ZIP；`加载数据` 直接显示文件选择控件，选中 ZIP 后立即校验、加载并渲染图表。用户需要查看其他保存文件时可再次选择“加载数据”；修改“标准 CSV 输出目录”时，Cockpit 自动回到该目录数据。CP Cockpit 不引入 VDMOS 的 JSON 项目格式、原始文件解析、规格常量或用户界面名称。

入口：

```powershell
streamlit run frontend/yield_analyzer_app.py
```

GUI 打开时会：

1. 获取当前公司页面的输出目录。
2. 如果 `127.0.0.1:8501` 未启动，则启动 Streamlit。
3. 通过 URL 参数 `?data_dir=...` 和环境变量 `CP_COCKPIT_DATA_DIR` 传入数据目录。
4. 用浏览器打开本地页面。

主要页面包括：

- 分组图表导航：数据总览、失效分析、空间分析、参数分析、数据查看
- 良率和 Bin
- 参数 BoxPlot（支持 Good Die 样本范围）
- 参数 Wafer 散点图（支持 Good Die 样本范围）
- 批次 / 片号 / 参数全局多选筛选及“绘制图形”确认触发
- Wafer Mapping（全部 Lot/Wafer 轻量总览，或选择 1～25 片详看；可选择综合 Bin 或具体测试参数）
- 区域分析
- 失效叠加
- Wafer Summary
- Cpk / 超限
- 数据预览

## 6. 关键数据映射

| 标准 CSV 字段 | 前端用途 | 用途 |
| --- | --- | --- |
| `Lot_ID` | 批次显示和分组 | BoxPlot、良率趋势、追溯 |
| `Wafer_ID` | Wafer 序列；Wafer 总数按 `Lot_ID + Wafer_ID` 组合计数 | BoxPlot X 轴、Mapping、Summary |
| `X` | Wafer Mapping 横坐标 | die 方格空间图与区域分析 |
| `Y` | Wafer Mapping 纵坐标 | die 方格空间图与区域分析 |
| `Seq` | `Seq` | Die 顺序 |
| `Bin` | 良率和失效标识 | 良率、失效 Bin |
| 参数列 | 同名参数 | 统计图和 Cpk |
| `spec.LimitL/LSL` | 规格下限 | 规格线、Cpk |
| `spec.LimitU/USL` | 规格上限 | 规格线、Cpk |

## 7. 错误处理和数据限制

| 情况 | 前端行为 | 建议排查 |
| --- | --- | --- |
| 找不到 cleaned CSV | 提示未找到标准数据 | 检查是否先完成清洗，输出目录是否正确 |
| 找不到 spec CSV | 图表仍可显示，规格/Cpk 不完整 | 检查清洗流程是否提取规格 |
| `X/Y` 全为 0 | Wafer Mapping 无真实空间分布 | 回到 Reader / Adapter 检查坐标来源 |
| 参数没有 LSL/USL | 不生成该参数的不良 Mapping | 检查 spec CSV 是否缺规格 |
| `LSL > USL` | 明确提示规格方向异常，不自动交换 | 回到清洗/spec 生成环节修正规格 |
| 同一 Lot/Wafer/X/Y 有复测记录 | 该坐标按最高不良优先级展示，悬浮显示记录数 | 确认复测规则与 Seq 数据 |
| 数据量很大 | 全参数 BoxPlot、散点页或大量 Wafer Mapping 加载变慢 | 降低散点图最大样本数；Wafer Mapping 使用默认轻量总览，需要逐 die 数值时再选择最多 25 片详看 |
| Cpk 方向异常 | 前端按 spec 原样计算 | 检查清洗输出的 `LimitL/LimitU` 是否正确 |

## 8. 扩展设计

新增公司或新格式时，不建议为每家公司复制一套前端。推荐路径：

```text
新原始格式
  -> Reader / Adapter
  -> 标准 cleaned / yield / spec CSV
  -> 复用 CP Cockpit
```

如果确实需要新增图表，应优先放在 `frontend/charts/` 或 `frontend/cp_dashboard_app.py` 中，并保持数据输入仍为标准 CSV。
