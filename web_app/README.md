# CP Data Cockpit

单用户、本机运行的 Streamlit 数据驾驶舱。它只消费现有清洗流程生成的标准 CSV，
不改变 Reader、清洗、单位转换或良率口径。

## 启动

在项目根目录双击 `start_web.bat`，或运行：

```powershell
D:\ProgramData\anaconda3\python.exe -m streamlit run web_app\app.py
```

浏览器默认打开 `http://127.0.0.1:8501`。左侧可以直接点击“选择文件夹”或
“选择文件”，也可以粘贴路径。选择普通 CSV/Excel 时先预览表格；选择标准 CSV
时会自动扫描同目录的以下文件：

- `*_cleaned_*.csv`
- `*_yield_*.csv`
- `*_spec_*.csv`

## MVP 范围

- 深色科技风 KPI 驾驶舱
- Lot、Wafer 联动筛选
- cleaned、yield、spec 表格预览和 CSV 下载
- Windows 原生文件夹/CSV/Excel 选择窗口与普通表格预览
- Wafer 良率趋势、Lot 对比与良率分布
- 动态 Bin 失效排行
- 参数箱体分布、规格提示和双参数散点图
- 当前筛选视图离线 HTML 报告

## 后续迭代

1. 在 Web 页面调用 HH、JT、Lion、国宇现有清洗入口，并显示任务日志。
2. 增加 Wafer Map、Cpk/Ppk、异常 Wafer 排名和参数失效贡献分析。
3. 用脱敏厂商样例补齐端到端契约测试。
