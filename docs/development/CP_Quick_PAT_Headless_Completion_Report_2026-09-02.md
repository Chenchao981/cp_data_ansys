# CP 快速 PAT 无界面入口完成报告（2026-09-02）

## 已完成

- 在 CP 工具包新增 `cp_data_processor.analysis.quick_pat`，从 Cleaner 生成的标准 cleaned/spec CSV 计算 PAT，并输出可供 TMS 读取的 Excel 和审计摘要。
- 参数从 spec 合同读取；非数值及不足 10 个有效点的项目跳过，全部不可统计时失败。
- 公式按历史 VDMOS v5.6 CP PAT 等价迁移，合同名为 `AEC_Q101_MEDIAN_IQR_5SIGMA_VDMOS_V5_6`。
- 重新构建 `packaging/release/app.pyz`，发布目录未发现原始数据、结果、日志或内部文档。

## 验证

- PAT 与发布打包测试：5 passed。
- `packaging/release/start.bat --check`：通过。
- 包内入口导入：通过。
- 最终 app.pyz SHA-256：`c1d6f65b9530944b70cd66205678f3ecd4a2bf2948a2b012f6178b78260838ae`。
- TMS 真实积塔批次验收：最终 Release 45，2,581 行、22 个参数、约 5.426 秒，PAT Excel 成功生成。

## 未确定

- 历史 VDMOS 公式是现有算法来源，但尚未取得业务负责人对生产 CP PAT 标准的书面确认。
- 华虹、立昂微、国宇还需要各自 Golden 样本做结果对比；本轮仅完成真实目录预览、Release 登记和通用调用链验证。

## 下一步

1. 固化四家 CP Golden 样本和预期 PAT 结果。
2. 确认生产 CP PAT 公式与版本命名。
3. 公式确认后将对应 Release 从开发验证状态纳入正式发布流程。
