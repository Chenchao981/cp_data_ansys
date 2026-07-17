# 运行与发布

## 1. 日常运行

推荐使用多公司 GUI：

```powershell
python -m gui.multi_company_main
```

发布目录启动：

```powershell
packaging\release\start.bat

# 仅检查 Python、依赖和 app.pyz，不打开 GUI
packaging\release\start.bat --check

# Git Bash
packaging/release/start.sh
packaging/release/start.sh --check
```

发布脚本优先使用 `D:\ProgramData\anaconda3\python.exe`，避免误用 PATH 中缺少 PyQt5 的其他 Python 环境。

基本操作流程：

1. 选择公司。
2. 如需改变显示风格，点击侧边栏底部的“亮色主题”或“暗黑主题”按钮；程序会记住上次选择。
3. 输入和输出路径默认显示当前 Windows 用户桌面，用户可直接输入路径或点击浏览按钮修改。
4. 每家公司页面统一使用一个“选择数据源”入口；在同一窗口中选择一个数据文件夹，或按 `Ctrl` / `Shift` 多选 ZIP 文件，程序会自动判断来源类型。输出路径始终选择输出父目录。
5. 先清洗数据，再点击当前公司页面中的 `CP Cockpit` 进行交互分析。
6. 检查输出目录中的 CSV、HTML 和日志。

程序文件与业务数据应分离：发布程序建议安装在 `D:\CPDataAnalysis`。`start.bat` 仍会创建 `D:\CPData` 作为日志、配置和可选业务目录，但 GUI 不再把该目录写死为输入、输出默认值。

## 2. 输出检查

每次处理至少确认：

- cleaned、yield、spec 三类 CSV 已生成
- cleaned 的 Lot/Wafer/Die 数量合理
- yield 的 Good die、Gross die 和 Yield 合理
- spec 的单位和上下限完整
- HTML 可离线打开，图表参数数量合理

## 3. 常见问题

### 找不到文件

确认文件扩展名、目录层级和公司选择。JT 与 Lion 都使用 Excel，但格式和处理器不同。

ZIP 内应包含所选公司的原始文件：华虹为 DCP/TXT，JT、Lion、国宇FRD 为 Excel。可以选择单个 ZIP、一次多选多个 ZIP，或选择直接存放这些 ZIP 的文件夹；加密、损坏、缺少对应数据或包含不安全路径的 ZIP 会被拒绝并在 GUI 日志中说明原因。国宇 ZIP 应保留批次/EDS 层级；程序会识别批次 ZIP 和产品多批次 ZIP。

所有公司在 ZIP 处理后仍沿用原输出命名规则：输出父目录下创建“首个真实批次号_YYYYMMDD_HHMMSS”文件夹，临时解压目录名称不会进入最终输出名称。

### 图表无法加载

确认目录中同时存在匹配 `*_cleaned_*.csv`、`*_yield_*.csv`、`*_spec_*.csv` 的文件，并检查列名是否为标准字段。

### `.xls` 无法读取

旧版 Excel 可能需要 `xlrd`。优先转换为 `.xlsx`，并在受控环境中补充依赖。

### 中文乱码

源代码和文档统一按 UTF-8 读取。PowerShell 5 中可显式使用 `Get-Content -Encoding UTF8`。

### `chcp` 不是内部或外部命令

说明 Windows `System32` 未在 PATH 中。新版发布脚本使用 `%SystemRoot%\System32\chcp.com` 的绝对路径，不再依赖 PATH。

### `ModuleNotFoundError: No module named 'PyQt5'`

说明启动脚本使用了错误的 Python 环境。运行 `start.bat --check` 查看实际 Python；必要时运行 `install_anaconda.bat` 安装发布依赖。

## 4. 打包

```powershell
python packaging\create_frontend_release.py
```

`packaging/release` 是唯一主要发布目录。入口为 `gui.multi_company_main:main`，产物写入 `packaging/release/app.pyz`，并同时包含 CP Cockpit 启动文件、发布文档和依赖安装脚本。打包脚本会排除原始数据、输出结果、日志、测试、缓存和 Git 文件。

发布前应在干净环境验证：

- `app.pyz` 可启动
- `start.bat --check` 可同时导入多公司 GUI 与 CP Cockpit
- HH、JT、Lion、国宇FRD Widget 均可加载
- 至少一套脱敏样例可完成清洗和图表生成
- 发布目录不包含原始 CP 数据、日志或内部文档
