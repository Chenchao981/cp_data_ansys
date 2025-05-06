# Wafer Map 绘图 (`plotting/wafer_map.py`)

该模块提供了使用 Matplotlib 绘制 Wafer Map（包括 Bin Map 和参数 Map）并将结果批量插入 Excel 文件的功能。

## 主要功能

### `plot_wafer_map(...) -> Tuple[Optional[Figure], Optional[Axes]]`

核心函数，用于绘制单个 Wafer 的 Map 图。

**输入参数:**

*   `wafer` (`CPWafer`): 包含数据的晶圆对象。
*   `value_col` (`str`, 默认 `'bin'`): 指定要绘制的数据来源列名（例如 `'bin'` 或某个参数 ID 如 `'Vth'`）。
*   `cmap` (字典, Colormap, 或 None): 指定颜色映射。
    *   **字典**: 用于离散数据 (如 Bin Map)。键是 Bin 值，值是 Matplotlib 颜色字符串 (如 `'lime'`, `'red'`)。可以包含 `np.nan` 键指定 NaN 颜色，`'default'` 键指定未明确列出的 Bin 的颜色。
    *   **Colormap**: 用于连续数据 (如参数 Map)。例如 `plt.cm.viridis`。
    *   **None**: 函数会尝试自动判断。如果 `value_col` 是 `'bin'` 或数据看起来是整数且唯一值不多，则使用模块内定义的 `DEFAULT_BIN_COLOR_MAP`；否则使用 `plt.cm.viridis` 作为连续颜色映射。
*   `ax` (Matplotlib Axes, 可选): 如果提供，则在此 Axes 对象上绘图；否则创建新的 Figure 和 Axes。
*   `title` (`str`, 可选): 图表标题，默认为 `f"Wafer: {wafer.wafer_id}"`。
*   `show_missing_dies` (`bool`, 默认 `True`): 控制是否在图中用特定颜色（由 cmap 的 `bad` 颜色决定，通常是浅灰色）显示坐标范围内但数据缺失的点。
*   `invert_xaxis` (`bool`, 默认 `True`): **重要**，用于模拟 VBA 的 `d(y, MaxX-x)` 坐标填充逻辑。如果为 `True`，绘制的数据矩阵会进行水平翻转，使得在 `origin='lower'` 时，X 轴看起来是从右向左递增（即 MinX 在右侧，MaxX 在左侧），以匹配 VBA 可能的输出效果。如果你的期望是标准的 X 轴从左到右递增，请设为 `False`。

**处理逻辑:**

1.  **数据提取**: 从 `wafer` 对象获取 X, Y 坐标和 `value_col` 对应的数据。
2.  **范围计算**: 计算有效的 X, Y 坐标范围 (MinX, MaxX, MinY, MaxY)。
3.  **矩阵构建**: 创建一个大小为 `(MaxY - MinY + 1, MaxX - MinX + 1)` 的 NumPy 数组，并用 NaN 初始化。根据 `wafer` 的 X, Y 坐标将 `value_col` 的值填充到矩阵的相应位置 `matrix[y - min_y, x - min_x]`。
4.  **颜色映射准备**: 根据传入的 `cmap` 参数或自动判断，准备好 `matplotlib.colors.Colormap` 和 `matplotlib.colors.BoundaryNorm` (用于离散数据)。处理 NaN 和默认颜色。
5.  **绘图**:
    *   根据 `invert_xaxis` 决定是否对数据矩阵进行水平翻转 (`np.fliplr`)。
    *   使用 `ax.imshow()` 绘制（翻转后的）数据矩阵。`origin='lower'` 使 Y 轴原点在左下角，`aspect='equal'` 使单元格呈方形。
    *   移除坐标轴刻度，设置标题。
6.  **图例/颜色条**: 如果是离散数据，尝试在图像右侧添加一个图例；如果是连续数据，添加一个颜色条。

**返回:**

*   包含绘制结果的 Matplotlib Figure 和 Axes 对象元组 `(fig, ax)`。如果绘图失败（例如数据无效），返回 `(None, None)`。

### `plot_all_wafers_to_excel(...)`

将一个 `CPLot` 对象中所有 Wafer 的指定 Map 图批量插入到一个 Excel 文件的 "Map" Sheet 页中。

**输入参数:**

*   `cp_lot` (`CPLot`): 包含所有 Wafer 数据的批次对象。
*   `output_excel_path` (`str`): 输出 Excel 文件的完整路径。
*   `value_col` (`str`, 默认 `'bin'`): 要为每个 Wafer 绘制的 Map 类型。
*   `color_map` (字典, Colormap, 或 None): 应用于所有 Wafer Map 的颜色映射。规则同 `plot_wafer_map`。
*   `invert_xaxis` (`bool`, 默认 `True`): 是否反转所有 Wafer Map 的 X 轴。
*   `cols_per_row` (`int`, 默认 `4`): 在 Excel Sheet 页中，每行排列多少个 Wafer Map 图像。
*   `image_options` (字典, 可选): 传递给 `xlsxwriter` 的 `worksheet.insert_image()` 函数的额外选项，用于控制图片插入的行为，例如缩放比例 `{'x_scale': 0.5, 'y_scale': 0.5}`。

**处理逻辑:**

1.  **初始化 Excel**: 使用 `xlsxwriter` 创建一个新的 Excel 工作簿和名为 "Map" 的工作表。
2.  **遍历 Wafer**: 迭代 `cp_lot.wafers` 列表。
3.  **绘图**: 对每个 `wafer`，调用 `plot_wafer_map` 函数生成对应的 Map 图 (Figure 对象)。
4.  **保存到内存**: 将生成的 Figure 对象使用 `fig.savefig()` 保存为 PNG 格式到内存中的 `BytesIO` 对象。
5.  **计算位置**: 根据 `cols_per_row` 和预设的行/列步长，计算当前 Wafer Map 在 Excel Sheet 页中应该插入的单元格位置。
6.  **插入标题**: 在图像插入位置的上方单元格写入 Wafer ID。
7.  **插入图像**: 使用 `worksheet.insert_image()` 将内存中的图像数据插入到计算好的单元格位置，并应用 `image_options`。
8.  **更新位置**: 更新下一次插入的行号和列号。
9.  **(TODO) 添加图例**: 未来可以考虑在 Excel 中添加一个全局的图例（例如，将图例单独绘制成图片并插入）。
10. **保存 Excel**: 完成所有 Wafer 处理后，关闭并保存 Excel 工作簿。

## 依赖项

*   `matplotlib`: 用于核心绘图。
*   `numpy`: 用于数值计算和矩阵操作。
*   `pandas`: 用于数据处理（尤其是在 `CPWafer.chip_data` 中）。
*   `xlsxwriter`: 用于将图像写入 Excel 文件。
*   `..数据类型定义`: 需要从项目的数据类型模块导入 `CPWafer` 和 `CPLot` 类。

## 注意事项

*   **坐标系与 VBA 匹配**: `invert_xaxis=True` 参数是关键，用于尝试匹配 VBA 中可能的 X 轴反向填充逻辑。请根据实际 VBA 输出效果验证 Python 生成的图像方向是否正确，必要时调整 `invert_xaxis` 参数。
*   **颜色配置**: 目前 Bin Map 使用模块内定义的 `DEFAULT_BIN_COLOR_MAP`。实际应用中，建议修改代码以从外部配置文件（如 Excel 或 CSV）加载颜色映射。
*   **Excel 图像布局**: `plot_all_wafers_to_excel` 中的 `row_step` 和 `col_step` 以及 `image_options` 中的缩放比例可能需要根据实际生成的图像大小和期望的 Excel 布局进行调整。
*   **性能**: 对于非常多的 Wafer 或非常大的 Die 数量，生成和插入大量图像到 Excel 可能会比较耗时。 