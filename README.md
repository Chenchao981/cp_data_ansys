# CP 数据分析平台

面向半导体晶圆 CP（Chip Probing）测试数据的清洗、标准化与可视化工具。当前支持华虹宏力（HH）、Jetech（JT）和 Lion 三类数据源，主要运行于 Windows 11。

## 当前能力

- 读取并清洗多种 CP 原始数据：HH DCP/TXT、JT Excel、Lion Excel
- 将不同来源转换为统一的 `CPLot` / `CPWafer` / `CPParameter` 数据模型
- 输出 cleaned、yield、spec 三类标准 CSV
- 生成良率趋势、失效分析、参数箱体图、散点图和汇总 HTML
- 提供 PyQt5 多公司 GUI、公司专用脚本和 Python API

## 推荐入口

```powershell
# 安装主要依赖
python -m pip install -r requirements.txt

# 启动多公司 GUI
python -m gui.multi_company_main
```

公司专用命令：

```powershell
# 华虹 DCP/TXT 目录
python clean_dcp_data.py --dir <input_dir> --output <output_dir>

# JT 文件或目录
python -m jt_data_processor.jt_main_processor <input_path> --output <output_dir>

# Lion：扫描 data/ 下的批次并合并
python lion_batch_processor.py
```

> 实际参数以各命令的 `--help` 为准。GUI 是当前最完整、最适合日常使用的入口。

## 处理主线

```text
原始 CP 文件
  -> 公司专用 Reader / Processor
  -> 标准 CPLot 数据模型
  -> cleaned / yield / spec CSV
  -> 共用 Plotly 图表层
  -> 离线 HTML 报告
```

仓库中同时存在统一读取器与历史兼容路径。GUI 当前仍直接调用各公司的成熟处理流程，不能简单理解为所有入口都已经切换到 `UnifiedReader`。详细说明见 [系统架构](docs/architecture.md)。

## 文档导航

- [文档中心](docs/README.md)
- [系统架构](docs/architecture.md)
- [数据契约](docs/data-contracts.md)
- [开发指南](docs/development.md)
- [新增公司支持](docs/company-integration.md)
- [运行与发布](docs/operations.md)
- [技术债与升级路线](docs/technical-debt.md)
- [AI / Codex 协作说明](AGENTS.md)

历史计划、修复记录和旧版说明统一保存在 [历史文档归档](docs/archive/README.md)，不应作为当前实现依据。

## 项目结构

```text
cp_data_processor/   核心数据模型、Reader、适配器、处理与分析模块
frontend/            基于标准 CSV 的 Plotly 图表模块
gui/                 PyQt5 多公司桌面 GUI
jt_data_processor/   JT 成熟专用处理流程
lion/                Lion Reader、适配器与图表生成
python_cp/           华虹流程仍在使用的兼容模块
packaging/           .pyz 打包与发布文件
docs/                当前文档与历史归档
```

## 当前验证状态

- 已确认三个公司入口及标准 CSV/图表处理路径。
- `jt_data_processor/tests/` 是当前唯一成体系的测试目录。
- 首选 Anaconda 环境可加载核心依赖，但 JT 测试当前在 collection 阶段被根包导入错误阻塞。
- `frontend/main.py` 与 `frontend/utils/data_loader.py` 当前含 null bytes，不能通过 `compileall`。

这些限制与后续治理顺序记录在 [技术债与升级路线](docs/technical-debt.md)。
