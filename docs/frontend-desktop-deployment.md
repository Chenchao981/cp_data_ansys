# CP 前端桌面部署说明

## 1. 部署目标

本说明面向 IT 或数据维护人员，用于把 CP 清洗和前端分析工具部署到用户 Windows 桌面。目标是让用户通过 GUI 完成：

1. 选择公司。
2. 选择原始 CP 数据目录。
3. 运行清洗。
4. 打开 CP Cockpit 交互分析。
5. 打开 CP Cockpit 查看全参数图表。

## 2. 推荐部署方式

当前推荐使用“可替换程序目录 + 持久化业务数据目录 + Python 环境”的方式部署。

程序目录：

```text
D:\CPDataAnalysis\
  app.pyz
  start.bat
  frontend\
  requirements_anaconda.txt
```

持久化业务目录：

```text
D:\CPData\
  raw\
    HH\
    JT\
    Lion\
    Guoyu\
  output\
    HH\
    JT\
    Lion\
    Guoyu\
  logs\
  config\
```

- `D:\CPDataAnalysis` 只保存程序文件，升级时可整体替换。
- `D:\CPData\raw` 保存用户原始 CP 文件。
- `D:\CPData\output` 保存 cleaned、yield、spec CSV 和图表。
- `D:\CPData\logs` 保存按天滚动的 UTF-8 运行日志。
- `D:\CPData\config` 预留用户配置，程序升级时不删除。

`start.bat` 会自动创建缺少的业务目录。可以通过 `CP_DATA_ROOT` 环境变量覆盖默认根目录。

## 3. 环境要求

推荐环境：

- Windows 11
- Anaconda 或 Python 3.11/3.12
- 主要 Python 包：
  - pandas
  - numpy
  - plotly
  - streamlit
  - PyQt5
  - openpyxl

安装命令：

```powershell
cd F:\cp_data_ansys
python -m pip install -r requirements.txt
python -m pip install streamlit PyQt5 openpyxl
```

如果使用 Anaconda，可先创建专用环境：

```powershell
conda create -n cpdata python=3.12 -y
conda activate cpdata
cd F:\cp_data_ansys
python -m pip install -r requirements.txt
python -m pip install streamlit PyQt5 openpyxl
```

## 4. 启动 GUI

开发或维护人员可直接运行：

```powershell
cd F:\cp_data_ansys
python -m gui.multi_company_main
```

普通用户建议使用 `start_gui.bat` 或桌面快捷方式。

示例 `start_cp_gui.bat`：

```bat
@echo off
cd /d F:\cp_data_ansys
python -m gui.multi_company_main
pause
```

如果使用 conda 环境：

```bat
@echo off
call D:\ProgramData\anaconda3\Scripts\activate.bat cpdata
cd /d F:\cp_data_ansys
python -m gui.multi_company_main
pause
```

把 `.bat` 文件发送到桌面快捷方式即可。

## 5. GUI 中的前端入口

每个公司页面的操作区都有一个前端入口，位置取代原来的“生成图表”按钮：

| 按钮 | 功能 | 依赖 |
| --- | --- | --- |
| `CP Cockpit` | 启动本地 Streamlit 前端并打开浏览器 | Python + streamlit |

### CP Cockpit 部署行为

点击当前公司页面的 `CP Cockpit` 后：

1. GUI 获取当前公司页面输出目录。
2. 检查 `127.0.0.1:8501` 是否已有服务。
3. 未启动则后台启动 Streamlit。
4. 浏览器打开本地地址。

本功能只在本机运行，不需要公网。

## 6. 用户目录建议

建议给用户约定清晰目录：

```text
D:\CPData\
  raw\
    HH\
    JT\
    Lion\
    Guoyu\
  output\
    HH\
    JT\
    Lion\
    Guoyu\
  logs\
  config\
```

GUI 的输入和输出文本框默认显示当前 Windows 用户桌面，例如：

```text
C:\Users\<用户名>\Desktop
```

用户只需要记住：

- 原始数据放 `raw`。
- 用户在 GUI 文本框中手动输入路径，或点击“选择文件夹”浏览选择。
- 输入路径选择具体批次目录；输出路径选择输出父目录。
- 图表和报告到 `output/<公司>/<批次目录>` 里查看。

## 7. 程序升级

1. 关闭 GUI 和 CP Cockpit。
2. 将新版程序先解压到临时目录并执行 `start.bat --check`。
3. 将旧 `D:\CPDataAnalysis` 改名为备份目录。
4. 将新版目录改名为 `D:\CPDataAnalysis`。
5. 启动并确认四家公司页面默认路径和 Cockpit 正常。

升级过程不得删除或覆盖 `D:\CPData`。

## 8. 发布包注意事项

正式发布给用户桌面前，需要确认：

1. `frontend/cp_dashboard_app.py` 已包含在发布包。
2. `frontend/yield_analyzer_app.py` 已包含在发布包。
3. `requirements.txt` 或发布环境包含 `streamlit`。
4. 不打包真实 CP 原始数据、输出结果、日志、账号或密钥。

## 9. 常见问题

### `start.bat` 一闪而过并提示 `was unexpected at this time`

旧版发布脚本在程序目录名包含括号时可能触发 CMD 解析错误，例如：

```text
D:\tools\release_frontend(1)\release_frontend
```

应优先使用已修复的新版发布包。暂时无法更新时，可把外层目录改为不含括号的名称，例如 `release_frontend_1`，或按推荐路径部署到 `D:\CPDataAnalysis`。这类 `was unexpected at this time` 提示是批处理语法错误，不应先关闭 360；只有 360 明确显示拦截或隔离记录时，才由 IT 在核实程序来源后处理对应文件。

### 点击 CP Cockpit 没反应

检查：

```powershell
python -m streamlit --version
```

如果未安装：

```powershell
python -m pip install streamlit
```

### 图表没有数据

检查输出目录是否包含：

```text
*_cleaned_*.csv
*_yield_*.csv
*_spec_*.csv
```

如果只有原始文件，说明还没有执行清洗。

### Wafer Map 没有图形

检查 cleaned CSV 的 `X`、`Y` 是否有效。如果全部是 0，前端无法生成真实空间图。
