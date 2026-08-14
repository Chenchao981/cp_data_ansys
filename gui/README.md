# gui

PyQt5 桌面界面。推荐入口为多公司 GUI：

```powershell
python -m gui.multi_company_main
```

## 结构

- `multi_company_main.py`：推荐启动入口
- `multi_company_gui.py`：公司导航与主窗口
- `theme.py`：暗黑/亮色主题颜色、全局 QSS 和主题切换公共逻辑
- `widgets/input_source_selector.py`：共用的“单文件夹 / 多压缩文件”数据源选择窗口
- `widgets/huahong_widget.py`：HH 文件夹/单个或多个 ZIP/7z 输入、清洗与共用图表
- `widgets/jetech_widget.py`：JT 文件夹/单 ZIP/多 ZIP 输入、专用处理与共用图表
- `widgets/lion_widget.py`：Lion 文件夹/单 ZIP/多 ZIP 输入、V1/V2 严格内容分派、批次合并与 CP Cockpit 编排
- `widgets/lion_die_count_widget.py`：Lion 管芯数月度目录递归清洗、四列 Excel 汇总与日志编排
- `widgets/guoyu_widget.py`：国宇FRD 文件夹/单 ZIP/多 ZIP 输入与标准 CSV 编排
- `cp_data_gui.py`：早期 HH 简化 GUI，保留兼容

GUI 是工作流编排层，不应承载新的底层数据解析规则。解析、字段映射和标准输出应放在 Reader、Adapter 与 processing 模块。

四家公司页面统一为一个“选择数据源”按钮。同一选择窗口支持一个数据文件夹或多个压缩文件；华虹可选 ZIP/7z，其他公司仍只显示 ZIP。确认时会阻止“文件夹 + 压缩文件”混选和多文件夹选择；实际格式判断、公共安全检查、临时解压和目录规整仍位于 `cp_data_processor/processing/archive_input.py`，华虹兼容入口保留在 `zip_input.py`。输出框始终填写父目录，四家公司统一通过 `output_naming.py` 创建“首个真实批次号_YYYYMMDD_HHMMSS”目录；多批次取稳定处理顺序中的第一个批次号，同秒重名时追加 `_001` 防覆盖。

`path_preferences.py` 使用每个 Windows 用户自己的 `QSettings`，按公司分别保存最后一次输入选择、输入浏览目录和输出父目录。首次启动或保存路径失效时，通过 `QStandardPaths.DesktopLocation` 回退到 Windows 已知桌面，因此桌面重定向到 D 盘等场景也能正确识别。设置不写入发布目录，也不会在不同 Windows 用户之间共享。

多公司 GUI 默认使用暗黑主题，侧边栏底部的主题按钮可切换亮色/暗黑模式。主题通过 `theme.py` 统一覆盖导航、表单、普通/操作按钮、日志、进度条、状态栏、菜单、数据源选择窗口和消息框，并通过 `QSettings` 记住上次选择；公司 Widget 不再单独硬编码背景色。

运行和排障见 [运行与发布](../docs/operations.md)。
