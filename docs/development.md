# 开发指南

## 1. 环境

推荐 Windows 11、PowerShell 和 conda 环境：

```powershell
D:\ProgramData\anaconda3\Scripts\conda.exe create -n cp-data python=3.11 -y
D:\ProgramData\anaconda3\Scripts\conda.exe activate cp-data
python -m pip install -r requirements.txt
python -m pip install pytest
```

代码使用了 `list[str]`、`tuple[str, str]` 和 `str | None`，因此建议 Python 3.10+。

## 2. 开发入口

```powershell
# GUI
python -m gui.multi_company_main

# 查看命令帮助
python clean_dcp_data.py --help
python -m jt_data_processor.jt_main_processor --help
python clean_lion_data.py --help

# 图表演示入口，默认读取 output/
python chart_generator.py
python jt_chart_generator.py
python -m lion.lion_chart_generator
```

## 3. 推荐修改流程

1. 先确认任务属于 Reader、Adapter、标准 CSV、图表还是 GUI 编排。
2. 优先修改现有主路径，避免在根目录复制新版本。
3. 对真实脱敏样例做端到端验证。
4. 检查三类 CSV 的字段、文件名与图表加载。
5. 更新 `docs/` 中受影响的当前文档。
6. 小提交、清晰 commit message，避免同时混入发布包和原始数据。

## 4. 测试与检查

```powershell
# 当前已有的 JT 测试
python -m pytest jt_data_processor/tests/ -v

# 核心包语法检查
python -m compileall -q cp_data_processor gui jt_data_processor lion

# 查看变更
git status --short
git diff --check
```

仓库当前没有可靠的全量自动化测试。涉及真实数据处理时，应至少验证：

- Wafer 数、Die 数和参数数未异常变化
- `Lot_ID` / `Wafer_ID` 未丢失或错位
- Good die 与 pass bin 定义一致
- cleaned、yield、spec 三类文件均可被图表层加载
- 单位与规格上下限仍一致

## 5. Git 规则

- 功能或文档整理使用独立分支，默认 `codex/<topic>`。
- 不提交 `data/`、`output/`、日志、临时文件和发布压缩包。
- 发布产物与源代码版本分开管理。
- 重构时先增加测试，再删除兼容路径。
