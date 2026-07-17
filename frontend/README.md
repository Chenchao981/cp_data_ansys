# frontend

基于标准 CSV 的 CP Cockpit 前端与共用图表层。

## 当前组件

- `cp_dashboard_app.py`：Streamlit 数据分析 Cockpit，读取标准 cleaned/yield/spec CSV，适合研发、质量和工艺部门交互查看。
- `yield_analyzer_app.py`：兼容启动入口，当前转到 `cp_dashboard_app.py`。
- `charts/yield_chart.py`：良率趋势、批次对比、失效分析。
- `charts/boxplot_chart.py`：参数箱体图与规格对比。
- `charts/wafer_mapping.py`：全部 Lot/Wafer 的 die-level Mapping、不良判定、范围筛选与轻量小图矩阵。
- `charts/scatter_chart.py`：参数散点图历史模块。
- `charts/summary_chart/`：汇总报告。
- `charts/js_embedder.py`：离线 Plotly.js 嵌入。
- `core/`、`adapters/`、`data_sources/`：CSV 加载与适配。

图表层预期目录中存在：

```text
*_cleaned_*.csv
*_yield_*.csv
*_spec_*.csv
```

## 启动

```powershell
streamlit run frontend/yield_analyzer_app.py
```

多公司 PyQt GUI 在各公司页面操作区提供 `CP Cockpit` 按钮，会把当前页面的输出目录传给前端；左侧边栏只用于切换公司。

## Cockpit 当前包含

- Bin 总览、失效 Bin Pareto、良率趋势
- 全参数 BoxPlot：按 Huahong 箱体图轴逻辑展示，X 轴为 Lot/Wafer 顺序，刻度显示 Wafer_ID，Y 轴为参数值；只显示箱线图，不叠加原始散点
- 全参数散点图：按 Huahong/BoxPlot 轴逻辑展示，X 轴为 Lot/Wafer 顺序，刻度显示 Wafer_ID，Y 轴为参数值
- Wafer Mapping：默认以轻量模式同时展示全部 Lot/Wafer，也可选择 1～25 片查看逐 die 悬浮详情；可选择综合 Bin 或具体测试参数，参数模式按 LSL/USL 高亮低超限和高超限 die
- Center/Mid/Edge 区域分析、失效点位叠加
- Wafer Summary、Cpk/超限表、CSV 数据预览

图表层不重新解析厂商原始文件，也不修改测试值；如果清洗输出没有有效 X/Y 坐标，Wafer Mapping 和区域分析无法体现真实空间分布。参数 Mapping 没有有效 LSL/USL 时不会猜测不良规则；规格下限大于上限时会提示回到清洗/spec 环节修正。

## 代码示例

```python
from frontend.charts.yield_chart import YieldChart

chart = YieldChart(data_dir="output")
if chart.load_data():
    chart.save_all_charts(output_dir="output")
```

注意：`frontend/main.py` 与 `frontend/utils/data_loader.py` 当前含 null bytes，属于已记录技术债；主流程应使用 `cp_dashboard_app.py` 和具体图表类。

## 前端专题文档

- [CP 前端业务需求](../docs/frontend-business-requirements.md)
- [CP 前端系统设计](../docs/frontend-system-design.md)
- [CP 前端桌面部署](../docs/frontend-desktop-deployment.md)
- [CP 前端用户快速上手](../docs/frontend-user-quickstart.md)
