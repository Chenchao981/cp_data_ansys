# 技术债与升级路线

本文件记录已从代码和验证中确认的问题，作为后续迭代依据。

## P0：先保证可验证

1. 补齐统一开发环境和锁定依赖。当前 `requirements.txt`、核心 requirements 和 GUI requirements 内容不一致。
2. 修复 `frontend/main.py` 与 `frontend/utils/data_loader.py` 的 null bytes；它们当前无法通过 Python 语法编译。
3. 建立最小端到端脱敏样例和回归测试，覆盖 HH、JT、Lion 的三类 CSV。

## P1：收敛主路径

1. 明确 GUI 公司专用流程与 `UnifiedReader` 的关系，逐步让 Reader/Adapter/CSV 契约成为唯一公共主线。
2. 审计 `python_cp/` 的仍在用能力，迁移后再删除兼容模块。
3. 合并两套 JT Reader/Adapter，减少规则漂移。
4. 逐步让未来新公司使用 `CompanyCleaningPipeline`；现有四家公司完成黄金样本回归前保持成熟路径。

## P1：修正识别与契约风险

1. Lion 的路径识别包含过宽的 `/data/` 规则，可能把其他 Excel 错识别为 Lion。
2. `reader_factory.create_reader()` 默认把所有 Excel 当作 JT，而另一条路径又把 Excel 当作 MEX，规则不一致。
3. spec CSV 同时存在逐参数行和 Lion 横向矩阵两种结构，需要显式版本化。
4. `company_config.py` 仍集中维护所有公司配置，后续应按公司拆分并保留兼容聚合入口。

## 已建立的治理基础

- 项目级 `cp-new-company-engineer` Agent 与四阶段接入 Skills 已建立。
- `devtools/cp_onboarding/` 已提供脱敏画像、批准档案校验、骨架生成和三类 CSV 对账。
- `StandardLotValidator` 和 `CompanyCleaningPipeline` 已建立未来新公司的确定性公共入口。
- 公共 CSV 良率使用显式 `CPLot.pass_bin`，缺少行级批次时优先回填 `CPWafer.source_lot_id`。

## P2：工程质量

1. 将日志、输出目录、发布包和真实数据从源码版本管理中彻底隔离。
2. 统一 CLI 参数、返回值和错误码。
3. 为图表层增加标准 CSV contract tests。
4. 将版本号集中管理，避免 GUI、文档和发布包各自维护。
5. 评估 Python 3.11/3.12、pandas 2.x 和 PyQt 版本升级。

## 建议迭代顺序

```text
环境与测试基线
  -> 修复不可编译文件
  -> 固化 CSV 契约
  -> 收敛公司 Reader/Adapter
  -> 收敛 python_cp 兼容模块
  -> 发布自动化与业务数据集成
```

每次删除遗留路径前，必须通过真实脱敏数据回归确认业务结果不变。
