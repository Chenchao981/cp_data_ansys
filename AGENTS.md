# AGENTS.md

本文件为 Codex、Claude Code 等 AI 编码工具提供仓库级工作指引。

## 沟通与业务背景

- 默认使用中文沟通，标准技术术语可使用英文。
- 用户是新洁能 CIO，关注功率半导体业务、SAP Business One、运营分析、成本和毛利分析。
- 本项目处理晶圆 CP（Chip Probing）测试数据，当前支持华虹宏力（HH）、Jetech（JT）和 Lion。
- 分析结论应区分事实、假设、计算与结论，并明确数据限制。

## 开始工作前

按顺序阅读：

1. `README.md`
2. `docs/architecture.md`
3. `docs/data-contracts.md`
4. 与任务相关的模块代码
5. `docs/technical-debt.md`

`docs/archive/` 是历史记录，不能作为当前实现依据。

## 当前真实架构

```text
原始厂商文件
  -> 公司专用 Reader / Processor / Adapter
  -> CPLot / CPWafer / CPParameter
  -> cleaned / yield / spec CSV
  -> frontend Plotly 图表
  -> 离线 HTML
```

关键事实：

- `cp_data_processor/` 是目标核心架构。
- GUI 当前直接编排 HH、JT、Lion 三套成熟流程，并非全部通过 `UnifiedReader`。
- `frontend/` 主要消费标准 CSV。
- `python_cp/`、JT 专用模块和 Lion 专用模块仍被主流程使用，未验证前不得删除。
- 根目录存在早期重复包，删除前必须做引用审计和真实数据回归。

## 常用命令

```powershell
# 环境
python -m pip install -r requirements.txt
python -m pip install pytest

# 推荐 GUI
python -m gui.multi_company_main

# 公司专用处理
python clean_dcp_data.py --dir <input_dir> --output <output_dir>
python -m jt_data_processor.jt_main_processor <input_path> --output <output_dir>
python lion_batch_processor.py

# 图表
python chart_generator.py
python jt_chart_generator.py
python -m lion.lion_chart_generator

# 检查
python -m pytest jt_data_processor/tests/ -v
python -m compileall -q cp_data_processor gui jt_data_processor lion
git diff --check
```

不要引用不存在的 `generate_combined_analysis.py` 或 `test_modular_architecture.py`。

## 代码边界

- 原始格式解析：`cp_data_processor/readers/` 或公司专用 Reader
- 厂商字段映射与单位转换：`cp_data_processor/readers/company_adapters/`
- 公共清洗和标准输出：`cp_data_processor/processing/`
- 数据模型：`cp_data_processor/data_models/cp_data.py`
- 标准 CSV 图表：`frontend/charts/`
- GUI 工作流：`gui/widgets/`
- JT 专用流程：`jt_data_processor/`
- Lion 专用流程：`lion/`、`lion_batch_processor.py`

新增公司优先遵循 `docs/company-integration.md`，输出标准 CSV 后复用图表层。

## 数据与业务安全

- 不提交真实 CP 原始数据、输出结果、日志、账号、密钥或客户敏感信息。
- 修改良率逻辑时必须确认 `pass_bin`。
- 修改字段映射、单位或规格时必须验证上下限和量纲。
- 多批次合并必须保留每行原始 `Lot_ID` 和 `Wafer_ID`。
- 图表阶段不应静默改变原始测试值。

## 开发与验证

- 优先沿用现有模式，避免复制新的公司专用全链路。
- 修改代码前确认实际调用路径，不根据旧文档猜测。
- 变更数据契约时同步更新 `docs/data-contracts.md`。
- 变更架构或入口时同步更新 `README.md` 和 `docs/architecture.md`。
- 删除兼容代码前先增加测试，并使用脱敏真实样例回归。
- 当前已知不可编译文件和其他风险见 `docs/technical-debt.md`。

## Git

- 使用独立分支，Codex 默认分支前缀为 `codex/`。
- 小步提交，commit message 说明业务影响。
- 不提交 `data/`、`output/`、日志、缓存、发布压缩包。
- 不覆盖或回退用户已有的未提交修改。
