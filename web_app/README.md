# CP Data Cockpit

单用户、本机运行的原始 CP 数据分析项目。它直接读取厂商 TXT/Excel/CSV，
在内存中清洗并计算良率、Bin、参数统计、交互图表和 HTML 报告，不要求先生成
cleaned、yield、spec 中间文件。

## 启动

在项目根目录双击 `start_web.bat`，或运行：

```powershell
D:\ProgramData\anaconda3\python.exe -m streamlit run web_app\app.py
```

浏览器默认打开 `http://127.0.0.1:8501`。左侧可以直接点击“选择文件夹”或
“选择文件”，也可以粘贴路径。应用会自动选择原始格式适配器：

- HuaHong DCP/TXT
- Jetech Excel
- Lion Excel
- 国宇 FRD Excel
- 通用 CSV/Excel
- 原有 cleaned/yield/spec CSV（兼容入口）

## MVP 范围

- 深色科技风 KPI 驾驶舱
- Lot、Wafer 联动筛选
- cleaned、yield、spec 表格预览和 CSV 下载
- Windows 原生文件夹/CSV/Excel 选择窗口与普通表格预览
- 原始文件自动识别、内存 IQR 清洗和动态良率/Bin 计算
- 参数统计摘要与带处理口径的离线 HTML 报告
- Wafer 良率趋势、Lot 对比与良率分布
- 动态 Bin 失效排行与 Pareto 累计贡献
- Bin/参数 Wafer Map
- 华虹规则参数全览：每个参数自动生成 Lot/Wafer 箱体 + Die 散点 + 规格线
- Histogram、Box、Violin、ECDF、Normal Q-Q
- Cp/Cpk（片内 pooled sigma）与 Pp/Ppk（总体 sigma）
- 自动高相关二维散点、3D 散点、Scatter Matrix、Correlation Heatmap
- Wafer Mean 3-sigma SPC 与测试顺序 Run Chart
- 当前筛选视图离线 HTML 报告

## 后续迭代

1. 增加 Wafer Map、Cpk/Ppk、异常 Wafer 排名和参数失效贡献分析。
2. 为每一种厂商格式增加更多脱敏端到端样例。
3. 将适配器进一步从历史 Reader 解耦，形成 Web 项目自己的解析实现。
