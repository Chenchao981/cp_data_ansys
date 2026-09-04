# CP 数据分析平台

面向半导体晶圆 CP（Chip Probing）测试数据的清洗、标准化与可视化工具。当前支持华虹宏力（HH）、Jetech（JT）、Lion 和扬州国宇 FRD 数据源，主要运行于 Windows 11。

## 当前能力

- 读取并清洗多种 CP 原始数据：HH DCP/TXT、JT Excel、Lion 两种已验收 CP Excel 格式、Lion 管芯数月度 Excel 汇总、扬州国宇 FRD Excel；华虹 GUI 支持文件夹、ZIP 和 7z，JT/Lion CP/国宇支持文件夹和 ZIP
- 将不同来源转换为统一的 `CPLot` / `CPWafer` / `CPParameter` 数据模型
- 输出 cleaned、yield、spec 三类标准 CSV
- 生成良率趋势、失效分析、参数箱体图、散点图和汇总 HTML；CP Cockpit 提供批次、片号、参数的全选/单选/多选筛选，首次打开不自动绘图，点击“绘制图形”后按所选范围生成，并支持“保存数据 / 加载数据”
- 提供 PyQt5 多公司 GUI、全局暗黑/亮色主题切换、公司专用脚本和 Python API
- 提供面向开发人员的新晶圆厂接入 Agent、阶段化 Skills 和确定性画像/骨架/验收工具；这些研发能力不进入用户 GUI 和发布包

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

# 扬州国宇 FRD：支持单批次目录，或产品目录下的多个批次子目录
python guoyu_batch_processor.py data/257375 --output output
```

> 实际参数以各命令的 `--help` 为准。GUI 是当前最完整、最适合日常使用的入口。

四家公司 GUI 统一使用一个“选择数据源”入口：在同一窗口中可选择一个原始数据目录，或按 `Ctrl` / `Shift` 多选压缩文件。华虹可选 ZIP/7z，Jetech、Lion 和国宇 FRD 可选 ZIP。GUI 只负责返回路径，后端自动判断目录或压缩格式并调用原有独立处理流程；Lion 进一步按工作簿内容严格区分成熟 V1 与三 Sheet 格式 2。V1 固定识别基础字段和三行规格结构，`TEST_NUM` 之后的测试参数按每片实际表头动态解析；同批次允许测试项增减，合并时取有序并集并把未测试项保留为空，同名参数的单位或上下限冲突则停止。格式 2 仍只接受已批准的精确参数 schema（当前包含 15 参数和 F0122A1 14 参数两套），未知 schema 或混合 V1/V2 会停止。压缩文件仅在后台临时目录中安全解压，处理完成后自动清理。输出路径选择父目录，四家公司统一创建“首个真实批次号_YYYYMMDD_HHMMSS”文件夹；包含多个批次时按稳定的识别/处理顺序取第一个批次号，CSV 明细仍保留每行原始 `Lot_ID`。

`lion-管芯数` 是独立的业务汇总页面：递归扫描月度目录下的 `.xlsx`，严格识别两种已验收格式，统一生成 `NCE品名 / LOT / Wafer / PASS / Good Die` 五列 `Lion_管芯数.xlsx`。格式 1 映射 `DEVICE= / LOT#= / WAFER# / PASS / DIE`；格式 2（LCD235）映射 `型号 / 批号 / 片号 / CP合格管芯数`，`Good Die = CP合格管芯数 - QAD补点数`。文件名可使用“批号 + 空格 + 备注”，但批号始终取报表元数据；未知表头或汇总对账失败会停止。该页面不改动现有 Lion CP V1/V2 流程，也不生成 cleaned/yield/spec CSV。

桌面 GUI 默认使用暗黑主题，侧边栏底部可一键切换亮色主题或暗黑主题；主题应用于公司菜单、路径表单、操作按钮、日志、状态栏、数据源选择窗口和应用内弹窗，并自动记住上次选择。各业务页面会分别记住当前 Windows 用户最后一次使用的输入源、输入浏览目录和输出父目录；首次启动或原路径失效时回退到 Windows 的真实桌面位置，包括重定向到其他磁盘的桌面。

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
- [CP 前端业务需求](docs/frontend-business-requirements.md)
- [CP 前端系统设计](docs/frontend-system-design.md)
- [CP 前端桌面部署](docs/frontend-desktop-deployment.md)
- [CP 前端用户快速上手](docs/frontend-user-quickstart.md)
- [开发指南](docs/development.md)
- [新增公司支持](docs/company-integration.md)
- [新晶圆厂接入研发架构](docs/new-company-onboarding.md)
- [CP 数据 FTP 接入设计（未来规划）](docs/ftp-integration-design.md)
- [运行与发布](docs/operations.md)
- [发布版用户手册](docs/release-user-manual.md)
- [发布版参数速查](docs/release-quick-reference.md)
- [技术债与升级路线](docs/technical-debt.md)
- [AI / Codex 协作说明](AGENTS.md)

## 项目结构

```text
cp_data_processor/   核心数据模型、Reader、适配器、处理与分析模块
frontend/            基于标准 CSV 的 Plotly 图表模块
gui/                 PyQt5 多公司桌面 GUI
jt_data_processor/   JT 成熟专用处理流程
lion/                Lion Reader、适配器、图表与管芯数汇总
guoyu/               扬州国宇 FRD Reader 与批次处理
python_cp/           华虹流程仍在使用的兼容模块
packaging/           .pyz 打包与发布文件
docs/                当前有效文档
.agents/skills/      项目级新晶圆厂接入 Skills（研发使用）
.codex/agents/       项目级 CP 新厂商接入 Agent（研发使用）
devtools/            新格式画像、骨架生成和输出验收工具（不打包）
```

## 当前验证状态

- 已确认四家公司入口及标准 CSV/图表处理路径。
- HH/JT/Lion/国宇均已有针对输入发现或处理路径的回归测试；公共压缩输入层另有 ZIP/7z 安全与目录结构测试。
- 首选 Anaconda 环境可加载核心依赖，当前厂商定向测试可正常收集和运行。
- `frontend/main.py` 与 `frontend/utils/data_loader.py` 当前含 null bytes，不能通过 `compileall`。

这些限制与后续治理顺序记录在 [技术债与升级路线](docs/technical-debt.md)。
