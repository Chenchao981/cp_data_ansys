# 参数分布统计 (`参数分布统计.py`)

该模块提供计算 CP 测试批次 (`CPLot`) 中参数统计信息的功能。

## 主要功能

### `calculate_parameter_summary(cp_lot: CPLot, filter_by_spec: bool = False, scope_limits: Optional[Dict[str, Tuple[Optional[float], Optional[float]]]] = None) -> pd.DataFrame`

此函数计算给定 `CPLot` 对象中每个数值参数的主要统计信息。它允许在计算前根据参数规格 (SL/SU) 或提供的范围 (`scope_limits`) 对数据进行筛选。

**输入参数:**

*   `cp_lot` (`CPLot`): 包含整个批次数据的 `CPLot` 对象。必须先调用 `cp_lot.combine_data_from_wafers()` 来准备好 `combined_data` DataFrame。
*   `filter_by_spec` (`bool`, 可选, 默认 `False`): 如果为 `True`，则在计算统计数据前，移除那些超出其对应 `CPParameter` 对象中定义的规格下限 (SL) 或规格上限 (SU) 的数据点。仅对定义了 SL 或 SU 的参数有效。
*   `scope_limits` (`Optional[Dict[str, Tuple[Optional[float], Optional[float]]]]`, 可选, 默认 `None`):
    *   一个字典，用于指定计算统计量时参数值的有效范围。
    *   键是参数 ID (即 `CPParameter.id`)。
    *   值是一个元组 `(lower_bound, upper_bound)`，其中 `lower_bound` 和 `upper_bound` 可以是浮点数或 `None`。
    *   `None` 表示该边界不设限制。
    *   例如: `{'Param1': (0.1, 0.5), 'Param2': (None, 100.0)}` 表示 Param1 的值必须在 0.1 到 0.5 之间（不包括边界），Param2 的值必须小于 100.0。
    *   如果提供了 `scope_limits`，它将优先于 `filter_by_spec` 用于数据筛选。

**返回:**

*   `pd.DataFrame`: 一个 Pandas DataFrame，包含参数的统计摘要。
    *   **索引**: DataFrame 的索引是 `wafer_id`。包含每个晶圆的 ID 以及一个特殊的 `'_All'` 索引，表示整个 Lot 的汇总统计。
    *   **列**: DataFrame 的列是一个 MultiIndex，其级别为：
        1.  参数 ID (`Parameter`)
        2.  统计量名称 (`Statistic`)
    *   **统计量包括**: 'N' (计数), 'Mean' (平均值), 'Std' (标准差), 'Min' (最小值), '25%' (第一四分位数), 'Median' (中位数), '75%' (第三四分位数), 'Max' (最大值), 'IQR' (四分位距), 'RobustStd' (稳健标准差, IQR / 1.34898)。
*   如果 `cp_lot.combined_data` 为空或不存在，或者筛选后没有有效数据，则返回一个空的 DataFrame。

**重要前提:**

在调用此函数之前，必须确保 `cp_lot` 对象的 `combined_data` 属性已经被填充。这通常通过调用 `cp_lot.combine_data_from_wafers()` 方法完成。

**筛选逻辑:**

1.  如果提供了 `scope_limits`，则根据 `scope_limits` 字典中定义的范围筛选 `cp_lot.combined_data`。
2.  如果没有提供 `scope_limits` 但 `filter_by_spec` 为 `True`，则根据 `cp_lot.params` 中每个参数定义的 `sl` 和 `su` 筛选 `cp_lot.combined_data`。
3.  如果两者都未提供或 `filter_by_spec` 为 `False`，则不对数据进行筛选。

**计算逻辑:**

1.  对筛选后的数据（或原始数据）按 `wafer_id` 进行分组。
2.  对每个分组（每个 Wafer）计算所有数值型参数列的统计量。
3.  计算整个数据集（所有 Wafer 合并）的汇总统计量。
4.  将每个 Wafer 的统计结果和汇总结果合并到一个 DataFrame 中。

## 依赖项

*   `pandas`: 用于数据处理和统计计算。
*   `numpy`: 用于数值计算。
*   `logging`: 用于记录操作信息和潜在问题。
*   `typing`: 用于类型提示。
*   `.数据类型定义`: 需要从该模块导入 `CPLot` 类定义。 