# 散点图绘制 (`scatter_plot.py`)

该模块负责根据配置生成参数间的散点图，并将结果输出到 Excel 文件中。

## 主要功能

*   **`plot_scatter_charts_to_excel`**: 核心函数，接受 `CPLot` 数据、配置列表和输出路径，生成包含散点图的 Excel 文件。

## 工作流程

1.  **读取配置**: 函数接收一个 `scatter_configs` 列表作为输入。列表中的每个字典定义了一组散点图的配置。
2.  **遍历配置**: 对列表中的每一个配置项：
    *   获取 X 轴参数 (`x_param`) 和 Y 轴参数 (`y_param`)。
    *   检查参数是否有效且存在于 `CPLot.combined_data` 中。
    *   根据配置中的 `title` 或参数名生成一个 Sheet 名称，并在输出的 Excel 文件中创建该 Sheet 页。
3.  **遍历 Wafer**: 在当前配置的 Sheet 页内，遍历 `CPLot` 对象中的每一个 `wafer`：
    *   从 `cp_lot.combined_data` 中筛选出当前 Wafer 的数据。
    *   提取该 Wafer 对应的 X 轴和 Y 轴参数数据，并移除任何包含 NaN 的数据对。
    *   如果存在有效数据，则使用 `matplotlib` 生成该 Wafer 的 X-Y 散点图。
        *   设置图表标题（包含 Wafer ID 和配置标题）。
        *   设置坐标轴标签（包含参数名和单位，如果可用）。
        *   应用配置中指定的坐标轴选项 (`x_axis_options`, `y_axis_options`)，包括手动设置刻度范围 (`min`, `max`) 和自定义轴标题 (`title`)。
    *   将生成的图表保存为 PNG 图片到内存中。
    *   使用 `xlsxwriter` 将内存中的图片插入到当前 Excel Sheet 页。
4.  **布局**: 图表在每个 Sheet 页内按照指定的 `cols_per_row` 进行网格布局。
5.  **输出**: 完成所有配置和 Wafer 的处理后，保存并关闭 Excel 文件。

## 配置 (`config.yaml` 中的 `scatter_plot_configs`)

主流程 (`main_processor.py`) 会从配置文件的 `scatter_plot_configs` 字段读取散点图的配置列表。列表中的每个元素是一个字典，定义一个 X-Y 参数组合的绘图设置：

```yaml
scatter_plot_configs:
  - x_param: 'Vth'       # 必需：X 轴参数的 ID
    y_param: 'Idsat'     # 必需：Y 轴参数的 ID
    title: 'Vth vs Idsat' # 可选：用于 Sheet 名称和图表标题的基础部分，若省略则自动生成
    x_axis_options:       # 可选：X 轴的详细设置
      min: 0.2           # 可选：手动指定 X 轴最小值
      max: 0.9           # 可选：手动指定 X 轴最大值
      title: 'Threshold Voltage (V)' # 可选：自定义 X 轴标题，若省略则使用 参数ID (单位)
    y_axis_options:       # 可选：Y 轴的详细设置
      # min: ...
      # max: ...
      title: 'Saturation Current (mA)' # 可选：自定义 Y 轴标题
  - x_param: 'Iol'
    y_param: 'Ioh'
    # ... 可以有更多配置项
```

## 绘图选项 (`config.yaml` 中的 `scatter_plot_options`)

主流程还会读取 `scatter_plot_options` 字典，并将这些选项传递给 `plot_scatter_charts_to_excel` 函数：

```yaml
scatter_plot_options:
  cols_per_row: 5              # 每行排列的图表数量
  image_options:               # 传递给 xlsxwriter insert_image 的选项
    x_scale: 0.4             # 图片 X 方向缩放比例
    y_scale: 0.4             # 图片 Y 方向缩放比例
    # object_position: 1     # 其他 xlsxwriter 选项...
  marker_size: 5               # 散点图中点的大小 (matplotlib scatter s 参数)
  figure_size: [6, 4]          # matplotlib 图形的基本尺寸 (宽, 高), 单位英寸
```

## 依赖

*   `pandas`: 用于数据处理。
*   `matplotlib`: 用于生成图表。
*   `xlsxwriter`: 用于将图表写入 Excel 文件。
*   `CPLot` (来自 `数据类型定义.py`): 用于数据输入。 