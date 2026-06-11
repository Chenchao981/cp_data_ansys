# gui

PyQt5 桌面界面。推荐入口为多公司 GUI：

```powershell
python -m gui.multi_company_main
```

## 结构

- `multi_company_main.py`：推荐启动入口
- `multi_company_gui.py`：公司导航与主窗口
- `widgets/huahong_widget.py`：HH 清洗与共用图表
- `widgets/jetech_widget.py`：JT 专用处理与共用图表
- `widgets/lion_widget.py`：Lion 批次合并与专用图表编排
- `cp_data_gui.py`：早期 HH 简化 GUI，保留兼容

GUI 是工作流编排层，不应承载新的底层数据解析规则。解析、字段映射和标准输出应放在 Reader、Adapter 与 processing 模块。

运行和排障见 [运行与发布](../docs/operations.md)。
