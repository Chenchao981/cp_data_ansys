# Lion 多 Lot 规格隔离完成报告（2026-09-04）

## 1. 结论

Lion V1 多 Lot 清洗已支持不同 Lot 使用不同版本的同名参数规格。程序合并输出一份 cleaned 和一份 yield，并为每个 Lot 分别输出一份横向 spec，历史规格不会被新规格覆盖，也不会使用新规格回算旧 Lot。

本次问题中的 `VF1` 规格均按源文件保留：

- `F26250717`：`0.5–1.3 V`。
- `F26221488`：`1.0–1.2 V`，属于后续收紧的新规范。

## 2. 规则边界

- 同一 Lot 内允许 Wafer 测试参数增加或减少，使用参数有序并集，未测试值保留为空。
- 同一 Lot 内同名参数的单位、上下限或测试条件冲突时继续失败关闭。
- 不同 Lot 的同名参数允许规格不同，每个 Lot 保留独立 spec。
- cleaned/yield 的每行 `Lot_ID` 保持原始值；CP Cockpit 按所选 Lot 同步选择对应规格。
- `pass_bin=1` 未改变。

## 3. 真实数据验证

使用用户实际的 Lion `data5` 多 Lot 数据完整运行 GUI Worker：

- 15 个 Lot。
- 357 个 Excel / Wafer。
- 314,874 行 cleaned，等于 `357 × 882`。
- 357 行 yield。
- 15 份按 Lot 命名的 spec。
- `F26221488` 的 `VF1` 输出为 `1.0–1.2 V`。
- `F26250717` 的 `VF1` 输出为 `0.5–1.3 V`。
- 清洗结果：PASS。

验收输出位于仓库外的 `F:\cp_onboarding_cases\lion_data5_multi_lot_20260904`，未修改或提交原始数据与生成结果。

## 4. 自动化验证

- 增加跨 Lot 同名参数不同规格的回归测试。
- 保留同一 Lot 内规格冲突的拒绝测试。
- 验证 combined cleaned/yield 包含全部原始 Lot_ID。
- 验证每份 spec 与对应 Lot 的源规格一致。
- 相关完整回归：123 passed，6 skipped。
- `git diff --check`：通过。
- 本次修改模块语法编译检查：通过。

## 5. 发布说明

本次只修改 Python 运行包内部代码和数据契约，不新增依赖，也不修改启动脚本。目标电脑已有正常运行的发布目录时，仅替换 `app.pyz` 即可；替换前应退出正在运行的程序。

- 发布包：`packaging/release/app.pyz`。
- 大小：556,899 bytes。
- SHA-256：`2c7b9c6a7bc8fae66b889a47190b2646932b35d7d0aa2a6e0c79cfc63eafe4f8`。
- `start.bat --check`：通过。
- 发布包内真实 `data5` 全量运行：PASS。
- 包内条目：197；测试目录、原始 Excel、CSV、日志等禁止项为 0。
