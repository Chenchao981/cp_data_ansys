# frontend

基于标准 CSV 生成 Plotly 交互式 HTML 图表的共用图表层。

## 当前组件

- `charts/yield_chart.py`：良率趋势、批次对比、失效分析
- `charts/boxplot_chart.py`：参数箱体图与规格对比
- `charts/scatter_chart.py`：参数相关性
- `charts/summary_chart/`：汇总报告
- `charts/js_embedder.py`：离线 Plotly.js 嵌入
- `core/`、`adapters/`、`data_sources/`：CSV 加载与适配

图表层预期目录中存在：

```text
*_cleaned_*.csv
*_yield_*.csv
*_spec_*.csv
```

示例：

```python
from frontend.charts.yield_chart import YieldChart

chart = YieldChart(data_dir="output")
if chart.load_data():
    chart.save_all_charts(output_dir="output")
```

注意：`frontend/main.py` 与 `frontend/utils/data_loader.py` 当前含 null bytes，属于已记录技术债；主流程应使用具体图表类。

详见 [数据契约](../docs/data-contracts.md) 与 [技术债](../docs/technical-debt.md)。
