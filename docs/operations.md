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
```

发布脚本优先使用 `D:\ProgramData\anaconda3\python.exe`，避免误用 PATH 中缺少 PyQt5 的其他 Python 环境。

基本操作流程：

1. 选择公司。
2. 选择包含原始 CP 文件的目录。
3. 选择输出目录。
4. 先清洗数据，再生成图表。
5. 检查输出目录中的 CSV、HTML 和日志。

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
cd packaging
python create_pyz.py
```

入口为 `gui.multi_company_main:main`，产物写入 `packaging/release/app.pyz`。打包脚本会排除 Markdown、日志、测试和 Git 文件。

发布前应在干净环境验证：

- `app.pyz` 可启动
- 三个公司 Widget 可加载
- 至少一套脱敏样例可完成清洗和图表生成
- 发布目录不包含原始 CP 数据、日志或内部文档
