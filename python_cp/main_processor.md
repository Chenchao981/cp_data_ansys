# CP 数据处理主流程 (`main_processor.py`)

该脚本是 CP (Chip Probing) 数据处理和分析流程的 Python 实现入口点，旨在模拟 VBA 版本 `A_业务流程.bas` 的核心功能。

## 设计思路

*   **模块化**: 将不同的功能（数据读取、数据处理、绘图、导出）拆分到独立的 Python 模块中，提高代码的可维护性和复用性。
*   **配置驱动**: 使用 YAML 配置文件来控制流程中的可选步骤（例如是否绘图、是否生成 PPT）和相关参数，而不是依赖 Excel UI Sheet。
*   **命令行接口**: 提供命令行参数来指定输入文件、格式、输出目录和配置文件路径。
*   **面向对象**: 使用数据类 (`CPParameter`, `CPWafer`, `CPLot`) 来组织内存中的数据。
*   **标准化库**: 使用 `pandas` 进行数据处理，`matplotlib`/`seaborn` 进行绘图，`xlsxwriter` 或 `openpyxl` 导出 Excel，`python-pptx` 导出 PPT，`PyYAML` 读取配置。

## 主要流程 (`main` 函数)

1.  **参数解析 (`argparse`)**: 解析命令行参数，获取输入文件列表 (`data_files`)、数据格式 (`format`)、输出目录 (`output_dir`) 和可选的配置文件路径 (`config`)。
2.  **日志和计时**: 配置 `logging` (同时输出到控制台和日志文件 `cp_processor.log`)，记录流程开始时间。
3.  **加载配置 (`load_config`)**: 读取指定的 YAML 配置文件。如果未提供或文件无效，则使用脚本中定义的 `DEFAULT_CONFIG` 默认配置。配置项控制后续的处理步骤和参数。
4.  **准备输出目录**: 创建指定的输出目录（如果不存在）。
5.  **读取数据**: 根据命令行指定的 `format`，实例化对应的数据读取器类 (例如 `CWReader`, `MEXReader`)。
    *   调用读取器的 `read()` 方法，将原始数据文件解析并加载到 `CPLot` 对象 (`cp_lot`) 中。
    *   **关键**: 调用 `cp_lot.combine_data_from_wafers()` 将所有 Wafer 的 `chip_data` DataFrame 合并到 `cp_lot.combined_data`，并添加 'wafer_id', 'seq', 'x', 'y', 'bin' 等列。这是后续许多分析和绘图的基础。
6.  **(占位) 添加计算数据**: 如果配置中 `add_calculated_data` 为 True，调用（未来实现的）`add_calculated_data(cp_lot)` 函数，该函数将基于 `增加运算数据.bas` 的逻辑修改 `cp_lot` 中的数据。
7.  **(占位) 导出核心 Excel 数据表**: 调用（未来实现的）`excel_exporter.export_analysis_to_excel()` 函数。
    *   该函数将负责创建一个 Excel 文件（例如 `LotID_analysis.xlsx`）。
    *   根据配置 `excel_export` 中的标志，选择性地将以下数据导出到不同的 Sheet 页：
        *   `Spec`: 参数规格信息 (来自 `cp_lot.params`)。
        *   `Data`: 完整的合并数据 (来自 `cp_lot.combined_data`)。
        *   `Yield`: 良率汇总表 (调用 `cp_lot.calculate_lot_yield_summary()`)。
        *   `Summary`: 参数统计汇总表 (调用 `calculate_parameter_summary()`)。
8.  **生成图表**: 根据配置中的标志位 (`plot_bin_map`, `plot_box_plot` 等) 和参数列表/配置：
    *   **Wafer Map**: 调用 `plotting.wafer_map.plot_all_wafers_to_excel()` 生成包含所有 Wafer Bin Map 的 Excel 文件。
    *   **Box Plot**: 遍历 `box_plot_params` 列表，对每个参数调用 `plotting.boxplot.plot_parameter_boxplots_to_excel()` 生成包含该参数所有 Wafer 箱线图的 Excel 文件。
    *   **(占位) Scatter Plot**: 根据 `scatter_plot_configs` 调用（未来实现的）散点图生成函数。
    *   **(占位) Parameter Color Map**: 根据 `param_color_map_params` 调用（未来实现的）参数颜色图生成函数。
9.  **(占位) 生成 PPT 报告**: 如果配置中 `generate_ppt` 为 True，调用（未来实现的）`ppt_exporter.create_ppt_report()` 函数，将分析结果和图表（可能来自之前生成的 Excel 文件或直接传入图像数据）汇总到 PPT 文件中。
10. **完成与退出**: 记录结束时间，计算并打印总耗时。日志文件中会包含详细的处理信息和可能的错误。

## 如何运行

```bash
# 示例：处理两个 CWSW 格式的 CSV 文件，使用默认配置，输出到 output 目录
python -m python_cp.main_processor data/file1.csv data/file2.csv --format CWSW --output-dir output

# 示例：处理一个 MEX 格式的 Excel 文件，使用自定义配置文件
python -m python_cp.main_processor data/mydata.xlsx --format MEX --output-dir results --config my_config.yaml 
```
*(需要确保 `python_cp` 在 Python 的搜索路径中，或者在项目根目录下运行)*

## 配置文件 (`config.yaml` 示例)

```yaml
# 控制是否执行某些步骤
add_calculated_data: false
plot_bin_map: true
plot_box_plot: true
plot_scatter_plot: false 
generate_ppt: false

# 需要绘制箱线图的参数 ID 列表
box_plot_params:
  - "Vth_lin"
  - "Idsat"
  - "Ioff"

# Excel 导出选项
excel_export:
  spec: true
  data: true
  yield: true
  summary: true

# 参数统计选项
summary_options:
  filter_by_spec: false
  # scope_limits: # 示例
  #   Vth_lin: [0.2, 0.8]
  #   Idsat: [null, 1.0e-3] # null 表示无限制

# Wafer Map 绘图选项 (传递给 plot_all_wafers_to_excel)
wafer_map_options:
  invert_xaxis: true
  cols_per_row: 4
  image_options: {x_scale: 0.4, y_scale: 0.4}

# Box Plot 绘图选项 (传递给 plot_parameter_boxplots_to_excel)
boxplot_options:
  cols_per_row: 5
  image_options: {x_scale: 0.4, y_scale: 0.4}

# ... (未来可以添加散点图、颜色图、PPT 的配置)
```

## 后续步骤

*   实现 `excel_exporter.py` 模块，完成核心数据表的导出功能。
*   翻译 `增加运算数据.bas` 并实现 `add_calculated_data` 函数。
*   翻译 `散点图制作.bas` 并实现 `plot_scatter_charts` 函数。
*   翻译 `参数数值颜色图.bas` 并实现 `plot_param_color_map` 函数。
*   翻译 `pptConst.bas` 和 `合并到ppt中.bas` 并实现 `ppt_exporter.py` 模块。
*   完善错误处理和日志记录。
*   根据实际需求调整绘图函数的输出方式（例如，是否将所有图表整合到一个 Excel 文件，或插入 PPT）。 