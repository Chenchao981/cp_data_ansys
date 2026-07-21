# 新增公司支持

目标是把新厂商原始数据转换为统一 `CPLot` 和三类标准 CSV，并复用现有图表。完整的 Agent、Skills、开发后端和 GUI 分层见 [新晶圆厂接入研发架构](new-company-onboarding.md)。

## 1. 接入前确认

收集并确认：

- 原始文件格式、文件命名和目录层级
- Lot、Wafer、Die 坐标、Seq、Bin 的来源
- pass bin 定义
- 参数名、单位、规格上下限和测试条件
- 单文件/多文件与单批次/多批次关系
- 异常值、缺失值和重复 Die 的处理规则

## 2. 研发阶段

1. 使用项目级 `cp-new-company-engineer` Agent 或 `$cp-onboard-new-company` 编排接入。
2. 使用 `$cp-profile-new-company-format` 生成脱敏结构画像、`format-profile.json` 和待确认清单。
3. 人工批准全部关键业务规则；未批准时不得修改生产代码。
4. 使用 `$cp-build-new-company-cleaner` 生成 staging 骨架并实现确定性代码。
5. 使用 `$cp-validate-new-company-cleaner` 完成源数据和三类 CSV 对账；只有 `PASS` 才能接 GUI。

## 3. 生产实现步骤

1. 在 `cp_data_processor/readers/` 或独立厂商模块实现 Reader，将原始文件读为 `CPLot`。
2. 在 `cp_data_processor/readers/company_adapters/` 实现 `BaseCompanyAdapter` 子类。
3. 在 `company_config.py` 配置字段映射、格式、识别规则和 Bin。
4. 在 `company_registry.py` 注册适配器。
5. 优先使用 `CompanyCleaningPipeline` 组合 Reader、Adapter、`StandardLotValidator` 和 `StandardCSVGenerator`。
6. 使用 `StandardCSVGenerator` 生成 cleaned、yield、spec。
7. 用 `YieldChart`、`BoxplotChart` 和 `SummaryChart` 验证复用。
8. 需要桌面入口时，在 `gui/widgets/` 增加公司 Widget 并接入导航。

## 4. 最小验收

- 能识别或显式指定公司
- 每个 Wafer 的行数、坐标、Bin 与源文件一致
- `Lot_ID` 和 `Wafer_ID` 在合并后仍可追溯
- pass bin 与良率计算一致
- 规格和单位无静默转换错误
- 三类 CSV 可被图表层加载
- 至少增加 Reader、Adapter 和端到端样例测试

## 5. 设计建议

- 自动识别只能作为便利功能，业务批处理应允许显式指定公司。
- 不要使用过宽路径规则，例如仅凭目录名 `data` 判定厂商。
- 厂商特例应保留在 Reader/Adapter，公共 CSV 和图表层保持稳定。
- 规格布局存在差异时，应先定义显式契约，而不是在图表代码中猜测。
- GUI 只调用已验收的确定性清洗器，不显示 Agent、Skill、置信度或字段映射确认。
