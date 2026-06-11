# 良率计算 (`yield_calculator.py`)

该模块负责处理 CP 测试数据的良率相关计算。

## 主要功能

*   **`get_wafer_bin_counts(wafer: CPWafer) -> pd.Series`**:
    *   计算单个 `CPWafer` 对象中有效（非 NaN）Bin 值的统计数量。
    *   返回一个 Pandas Series，索引为 Bin 值，值为该 Bin 出现的次数。
    *   如果晶圆没有 Bin 数据，返回一个空的 Series。

*   **`calculate_wafer_yield(wafer: CPWafer, pass_bin_value: int = 1) -> Tuple[float, int, int]`**:
    *   计算单个 `CPWafer` 对象的良率。
    *   **参数**:
        *   `wafer`: 需要计算良率的 `CPWafer` 对象。
        *   `pass_bin_value`: 定义为 "Pass" 状态的 Bin 值 (默认为 1)。
    *   **返回**: 一个元组 `(yield_rate, pass_count, total_count)`
        *   `yield_rate`: 良率 (0.0 到 1.0 之间的小数)，计算公式为 `pass_count / total_count`。
        *   `pass_count`: Bin 值等于 `pass_bin_value` 的有效芯片数量。
        *   `total_count`: 有效（非 NaN）Bin 值的总数量。
        *   如果晶圆没有有效 Bin 数据，返回 `(0.0, 0, 0)`。

*   **`calculate_lot_yield_summary(cp_lot: CPLot) -> pd.DataFrame`**:
    *   计算整个 `CPLot` 批次的良率汇总表，格式类似于 VBA 版本的 `ShowYield` 输出。
    *   **参数**:
        *   `cp_lot`: 需要计算汇总的 `CPLot` 对象 (需要包含 `wafers` 列表和 `pass_bin` 属性)。
    *   **处理逻辑**:
        1.  遍历 `cp_lot.wafers` 中的每个 `wafer`。
        2.  调用 `calculate_wafer_yield` 计算每个 wafer 的良率、Pass 数量和 Total 数量。
        3.  调用 `get_wafer_bin_counts` 计算每个 wafer 的 Bin 分布。
        4.  收集合并所有 wafer 中出现的 Bin 值。
        5.  确定最终表格的 Bin 列顺序：将 `cp_lot.pass_bin` 对应的 Bin 值放在 "Pass" 列之后，其他 Bin 值按数值和非数值分别排序后追加，列名为 `BinX` (例如 `Bin2`, `Bin3`)。
        6.  构建 Pandas DataFrame，包含列：`Wafer` (Wafer ID 加 `#`), `Yield`, `Total`, `Pass`, 以及每个其他 Bin 的计数列 (`BinX`)。
        7.  计算并添加一个名为 "All" 的汇总行，包含所有 Wafer 的 Pass、Total 和各 Bin 的总数，以及基于总数计算的 Lot 整体良率。
    *   **返回**: 一个包含良率汇总信息的 Pandas DataFrame。如果 Lot 中没有 Wafer，返回空 DataFrame。

## 依赖项

*   `pandas`: 用于数据结构和计算。
*   `numpy`: 用于数值操作。
*   `.数据类型定义`: 需要导入 `CPWafer` 和 `CPLot` 类。 