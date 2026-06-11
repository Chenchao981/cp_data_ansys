# 文档维护规范

## 1. 单一事实来源

- 根目录 `README.md`：项目入口、推荐命令和文档导航
- 根目录 `AGENTS.md`：AI / Codex 工作规则
- `docs/architecture.md`：当前架构
- `docs/data-contracts.md`：当前数据契约
- `docs/technical-debt.md`：已确认但尚未解决的问题

同一信息不要在多个当前文档中完整复制，使用链接引用。

## 2. 何时更新

| 代码变更 | 必须更新 |
| --- | --- |
| 新增/删除入口命令 | `README.md`、`operations.md` |
| 修改模块边界或主流程 | `architecture.md` |
| 修改字段、文件名、规格或良率定义 | `data-contracts.md` |
| 新增公司 | `company-integration.md`、`architecture.md` |
| 新增已知风险 | `technical-debt.md` |

## 3. 历史归档

- 已完成计划、专项修复说明、交接记录移动到 `docs/archive/`。
- 归档文档保留原内容和文件名，方便 Git 历史追溯。
- 归档文档不得作为当前命令或架构依据。

## 4. 文档质量检查

- 使用 UTF-8。
- 命令必须在仓库中存在，并尽可能通过 `--help` 或实际运行验证。
- 链接使用相对路径。
- 明确区分事实、计划和技术债。
- 不在文档中放真实客户数据、内部路径、账号或密钥。
