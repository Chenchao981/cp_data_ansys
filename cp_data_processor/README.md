# CP 数据处理器 (Python)

本项目是原始 VBA CP 数据处理宏的 Python 转换版本。旨在复刻读取多种 CP 测试数据格式 (MEX, DCP, CW)、处理数据、计算统计数据和良率、生成分析图表（箱形图、晶圆图、散点图）以及将结果保存到 Excel 工作簿的核心功能。

## 项目结构

```
cp_data_processor/
├── main.py                     # 主应用程序入口和工作流编排
│
├── config/                     # 配置文件
│   ├── __init__.py
│   └── settings.py             # 工作表名、文件路径、处理标志、常量
│
├── data_models/                # 数据结构定义
│   ├── __init__.py
│   └── cp_data.py              # 使用 dataclasses 定义 CPLot, CPWafer, CPParameter
│
├── readers/                    # 读取不同原始数据格式的模块
│   ├── __init__.py
│   ├── base_reader.py          # 读取器的抽象基类
│   ├── cw_reader.py            # 读取 CW 格式 (.csv)
│   ├── dcp_reader.py           # 读取 DCP 格式 (.txt)
│   └── mex_reader.py           # 读取 MEX 格式 (.xls/.xlsx)
│
├── processing/                 # 数据清洗、转换、特征工程
│   ├── __init__.py
│   └── data_transformer.py     # 添加计算列、数据清洗等
│
├── analysis/                   # 核心计算模块
│   ├── __init__.py
│   ├── yield_calculator.py     # 计算晶圆/批次良率
│   ├── summary_stats.py        # 计算参数统计数据 (均值, 标准差, Cp/Cpk)
│   └── map_formatter.py        # 准备晶圆图的数据和格式化规则
│
├── plotting/                   # 生成图表的模块
│   ├── __init__.py
│   ├── box_plot.py             # 生成箱形图
│   ├── map_plot.py             # 生成晶圆 Bin 图/参数图
│   ├── color_map_plot.py       # 生成参数颜色图 (map_plot 的封装)
│   └── scatter_plot.py         # 生成散点图
│
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── excel_handler.py        # 处理 Excel 文件的读/写/样式
│   └── helpers.py              # 通用辅助函数 (文件对话框, 正则表达式, 列表操作)
│
├── requirements.txt            # 项目依赖
└── README.md                   # 本文件
```

## 依赖项

主要依赖项列在 `requirements.txt` 文件中。使用 pip 安装它们：

```bash
pip install -r requirements.txt
```

关键库包括：
*   `pandas`: 用于数据操作和读写文件。
*   `numpy`: 用于数值运算。
*   `openpyxl`: 用于读写 `.xlsx` 文件。
*   `matplotlib`: 用于创建静态图表。
*   `seaborn`: 基于 matplotlib 的增强型统计绘图库。

## 如何使用

在项目根目录下从命令行运行主脚本：

```bash
python -m cp_data_processor.main
```
*(注意: 使用 `-m` 运行模块假定你的项目结构已正确设置在 Python 路径中，或者你正从包含 `cp_data_processor` 的目录运行)*

或者，进入 `cp_data_processor` 目录并运行：
```bash
python main.py
```

脚本通常会执行以下操作：
1.  从 `config/settings.py` 加载设置。
2.  提示用户使用 GUI 对话框选择输入数据文件（基于指定或检测到的格式）。
3.  使用相应的读取器模块读取所选文件。
4.  执行数据转换（例如，如果启用，则添加计算列）。
5.  计算良率和汇总统计信息。
6.  根据设置中的标志生成图表（箱形图、晶圆图、散点图），并将它们保存为图像文件（通常保存在 `整理后的数据文件` 的子目录中）。
7.  创建一个新的 Excel 工作簿 (`.xlsx`)，包含 Spec、Data、Yield、Summary 等工作表。
8.  将生成的结果 Excel 工作簿保存在 `整理后的数据文件` 目录中，并以 Lot ID 命名。

## 配置

修改 `config/settings.py` 文件以调整：
*   默认的输入/输出目录。
*   Excel 工作表名称。
*   启用/禁用特定处理步骤或绘图的标志 (`ADD_CAL_DATA_FLAG`, `BOX_PLOT_FLAG` 等)。
*   计算参数的定义 (在 `processing/data_transformer.py` 的逻辑中)。
*   散点图的配置源 (在 `plotting/scatter_plot.py` 的逻辑中)。

## 后续开发

*   根据具体的文件格式和原始 VBA `SplitInfo_*` 函数，在每个读取器 (`cw_reader.py`, `dcp_reader.py`, `mex_reader.py`) 中实现详细的解析逻辑。
*   优化 `processing`, `analysis`, 和 `plotting` 模块中的计算逻辑，以精确匹配 VBA 的结果。
*   实现健壮的错误处理和日志记录。
*   为各个组件添加单元测试。
*   考虑添加一个简单的 GUI（例如，使用 Tkinter, PyQt, 或 Streamlit）来替代 VBA UI 工作表进行选项设置。
*   针对非常大的数据集优化性能。 