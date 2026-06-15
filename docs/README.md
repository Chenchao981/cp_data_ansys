# 文档中心

本目录是项目当前文档的唯一主入口。文档按使用场景组织，避免把历史计划、临时修复说明和当前事实混在一起。

## 当前文档

| 文档 | 适用场景 |
| --- | --- |
| [系统架构](architecture.md) | 理解模块边界、真实调用关系和兼容路径 |
| [数据契约](data-contracts.md) | 开发 Reader、适配器、CSV 和图表功能 |
| [开发指南](development.md) | 搭建环境、修改代码、测试和提交 |
| [新增公司支持](company-integration.md) | 接入新的晶圆厂或测试厂格式 |
| [运行与发布](operations.md) | 日常运行、排障和生成发布包 |
| [技术债与升级路线](technical-debt.md) | 规划重构、测试补强和版本升级 |
| [文档维护规范](documentation-governance.md) | 保持文档与代码同步 |

## 阅读路径

新开发者或 AI 工具：

1. 阅读根目录 `AGENTS.md`
2. 阅读 `README.md`
3. 阅读 `architecture.md` 和 `data-contracts.md`
4. 根据任务进入公司专用模块或图表模块

日常业务使用者：

1. 阅读根目录 `README.md`
2. 阅读 `operations.md`
3. 必要时参考 `packaging/release/用户手册.md`

## 文档状态规则

- `docs/` 顶层文档描述当前实现，修改代码时应同步更新。
- 模块内 README 只描述该模块的局部细节。
- 代码与文档冲突时，以已验证的代码行为为准，并立即修正文档。
