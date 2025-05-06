# 箱形图绘制 (`plotting/boxplot.py`)

该模块提供为 CP 测试批次中指定参数，针对每个 Wafer 单独生成箱形图，并将所有 Wafer 的箱形图批量插入 Excel 文件的功能。

## 主要功能

### `plot_wafer_boxplot(...) -> Tuple[Optional[Figure], Optional[Axes]]`

绘制**单个 Wafer** 上**指定参数**的数据分布箱形图。

**输入参数:**

*   `wafer` (`CPWafer`): 要绘制的晶圆对象。
*   `param_id` (`str`): 要绘制分布的参数 ID (例如 `'Vth'` 或 `'bin'`)。
*   `param_info` (`CPParameter`, 可选): 该参数的元信息对象，用于获取显示名称、单位、规格线 (SL/SU)。如果未提供，将直接使用 `param_id` 作为标签。
*   `ax` (Matplotlib Axes, 可选): 如果提供，则在此 Axes 对象上绘图；否则创建新的 Figure 和 Axes。

**处理逻辑:**

1.  **提取数据**: 根据 `param_id` 从 `wafer.chip_data` 或 `wafer.bin` 获取对应的数据序列。
2.  **数据清洗**: 移除数据中的 NaN 值。
3.  **绘图**: 如果清洗后数据非空，使用 `ax.boxplot()` 绘制箱形图。默认显示异常点 (`showfliers=True`) 并填充箱体颜色 (`patch_artist=True`)。
4.  **格式化**: 移除 X 轴标签和刻度（因为只有一个箱体），设置 Y 轴标签（包含参数名和单位），设置图表标题（包含 Wafer ID）。
5.  **添加规格线**: 如果 `param_info` 中提供了规格上限 (SU) 或下限 (SL)，在图上绘制对应的水平虚线，并添加图例。
6.  **空数据处理**: 如果某个 Wafer 对于指定参数没有有效数据，则在图表区域显示 "No Valid Data"。

**返回:**

*   包含绘制结果的 Matplotlib Figure 和 Axes 对象元组 `(fig, ax)`。如果绘图失败或无有效数据，返回 `(None, None)` （或一个显示提示信息的图）。

### `plot_parameter_boxplots_to_excel(...)`

为 CPLot 中的**指定参数**，将**每个 Wafer** 的箱形图批量插入到一个 Excel 文件的**新 Sheet 页**中。

**输入参数:**

*   `cp_lot` (`CPLot`): 包含所有 Wafer 数据的批次对象。
*   `param_id` (`str`): 要绘制箱形图的参数 ID。
*   `output_excel_path` (`str`): 输出 Excel 文件的完整路径。
*   `cols_per_row` (`int`, 默认 `5`): 在 Excel Sheet 页中，每行排列多少个 Wafer 的箱形图。
*   `image_options` (字典, 可选): 传递给 `xlsxwriter` 的 `worksheet.insert_image()` 函数的额外选项，用于控制图片插入的行为，例如缩放比例 `{'x_scale': 0.5, 'y_scale': 0.5}`。

**处理逻辑:**

1.  **获取参数信息**: 从 `cp_lot` 中查找 `param_id` 对应的 `CPParameter` 对象，用于图表标签和规格线。
2.  **初始化 Excel**: 使用 `xlsxwriter` 创建一个新的 Excel 工作簿。根据 `param_id` 创建一个 Sheet 页 (例如 `BoxPlot_Vth`)。
3.  **遍历 Wafer**: 迭代 `cp_lot.wafers` 列表。
4.  **绘图**: 对每个 `wafer`，调用 `plot_wafer_boxplot(wafer, param_id, ...)` 函数生成对应的箱形图 (Figure 对象)。
5.  **保存到内存**: 将生成的 Figure 对象使用 `fig.savefig()` 保存为 PNG 格式到内存中的 `BytesIO` 对象。
6.  **计算位置**: 根据 `cols_per_row` 和预设的行/列步长，计算当前 Wafer 箱形图在 Excel Sheet 页中应该插入的单元格位置。
7.  **插入标题**: 在图像插入位置的上方单元格写入 Wafer ID。
8.  **插入图像**: 使用 `worksheet.insert_image()` 将内存中的图像数据插入到计算好的单元格位置，并应用 `image_options`。
9.  **错误处理**: 如果某个 Wafer 的图生成或插入失败，会在日志中记录警告/错误，并在 Excel 对应位置写入提示信息（如 "Plot Failed"）。
10. **更新位置**: 更新下一次插入的行号和列号。
11. **保存 Excel**: 完成所有 Wafer 处理后，关闭并保存 Excel 工作簿。

## 依赖项

*   `matplotlib`: 用于核心绘图。
*   `numpy`: 用于数值计算。
*   `pandas`: 用于数据处理。
*   `xlsxwriter`: 用于将图像写入 Excel 文件。
*   `..数据类型定义`: 需要导入 `CPWafer`, `CPLot`, `CPParameter`。

## 注意事项

*   **输出格式**: 此模块专注于为每个 Wafer 单独生成箱形图，以展示 Wafer 内部的数据分布。这与某些工具可能生成的、将所有 Wafer 并列比较的箱形图不同。
*   **Excel 布局**: 图像在 Excel 中的间距 (`row_step`, `col_step`) 和缩放 (`image_options`) 可能需要根据实际需要调整。
*   **性能**: 对于大量 Wafer，生成和插入大量图像可能较慢。 