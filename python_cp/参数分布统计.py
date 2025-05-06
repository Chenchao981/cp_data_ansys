import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, Tuple

# 假设 CPLot 类定义在同级目录的 数据类型定义.py 文件中
# 使用相对导入
from .数据类型定义 import CPLot 

# 配置日志记录器
logger = logging.getLogger(__name__)

def calculate_parameter_summary(
        cp_lot: CPLot,
        filter_by_spec: bool = False,
        scope_limits: Optional[Dict[str, Tuple[Optional[float], Optional[float]]]] = None
    ) -> pd.DataFrame:
    """
    计算 Lot 中每个参数的主要统计信息 (Avg, Std, Median, RobustStd 等)。
    可以按 Wafer 分组计算，并选择性地在计算前根据规格或范围筛选数据。

    Args:
        cp_lot (CPLot): 包含批次数据的 CPLot 对象。
                       必须已调用 combine_data_from_wafers()。
        filter_by_spec (bool): 如果为 True，则在计算前移除超出参数规格 (SL/SU) 的数据。
                                 注意：仅当参数的 SL 或 SU 被定义时才有效。
        scope_limits (Optional[Dict[str, Tuple[Optional[float], Optional[float]]]]):
                                 一个字典，定义了计算时要使用的范围。
                                 键是参数 ID (param.id)，值是 (下限, 上限) 元组。
                                 如果提供了此字典，则在计算前仅保留在此范围内的数据。
                                 `None` 表示无限制。
                                 优先级高于 filter_by_spec。

    Returns:
        pd.DataFrame: 索引是 Wafer ID (加 "_All" 表示 Lot 汇总)，
                      列是 MultiIndex: (参数 ID, 统计量名称)。
                      统计量包括 'N', 'Mean', 'Std', 'Min', '25%', 'Median', '75%', 'Max', 'IQR', 'RobustStd'。
    """
    if cp_lot.combined_data is None or cp_lot.combined_data.empty:
        logger.warning("CPLot 对象的 combined_data 为空或不存在，无法计算参数统计。请先调用 combine_data_from_wafers()。")
        return pd.DataFrame()

    data_to_process = cp_lot.combined_data.copy()
    param_cols = [p.id for p in cp_lot.params if p.id in data_to_process.columns]
    if not param_cols:
        logger.warning("combined_data 中未找到任何在 cp_lot.params 中定义的参数列。")
        return pd.DataFrame()

    # 1. 数据筛选 (根据 scope_limits 或 filter_by_spec)
    if scope_limits:
        logger.info("根据提供的 scope_limits 进行数据筛选...")
        initial_rows = len(data_to_process)
        for param_id, (lower, upper) in scope_limits.items():
            if param_id in data_to_process.columns:
                mask = pd.Series(True, index=data_to_process.index)
                if lower is not None:
                    # 使用 > 而不是 >= 遵循 VBA 逻辑（如果适用）或常见定义
                    mask &= (data_to_process[param_id] > lower)
                if upper is not None:
                    # 使用 < 而不是 <= 
                    mask &= (data_to_process[param_id] < upper)
                # 应用掩码前记录行数
                rows_before_param_filter = len(data_to_process)
                data_to_process = data_to_process.loc[mask]
                rows_after_param_filter = len(data_to_process)
                if rows_before_param_filter > rows_after_param_filter:
                     logger.debug(f"  筛选参数 '{param_id}' 范围 ({lower}, {upper})，移除了 {rows_before_param_filter - rows_after_param_filter} 行，剩余 {rows_after_param_filter} 行。")
            else:
                logger.warning(f"范围字典中的参数 '{param_id}' 不在数据中，已忽略。")
        logger.info(f"Scope limits 筛选完成，总共移除 {initial_rows - len(data_to_process)} 行，剩余 {len(data_to_process)} 行。")

    elif filter_by_spec:
        logger.info("根据参数规格 (SL/SU) 进行数据筛选...")
        initial_rows = len(data_to_process)
        for param in cp_lot.params:
            if param.id in data_to_process.columns:
                mask = pd.Series(True, index=data_to_process.index)
                rows_before_param_filter = len(data_to_process)
                applied_filter = False
                if param.sl is not None:
                    mask &= (data_to_process[param.id] >= param.sl)
                    applied_filter = True
                if param.su is not None:
                    mask &= (data_to_process[param.id] <= param.su)
                    applied_filter = True
                
                if applied_filter:
                    data_to_process = data_to_process.loc[mask]
                    rows_after_param_filter = len(data_to_process)
                    if rows_before_param_filter > rows_after_param_filter:
                        logger.debug(f"  筛选参数 '{param.id}' 规格 [{param.sl}, {param.su}]，移除了 {rows_before_param_filter - rows_after_param_filter} 行，剩余 {rows_after_param_filter} 行。")
        logger.info(f"规格筛选完成，总共移除 {initial_rows - len(data_to_process)} 行，剩余 {len(data_to_process)} 行。")

    if data_to_process.empty:
        logger.warning("数据筛选后为空，无法计算参数统计。")
        return pd.DataFrame()

    # 2. 计算统计量 (按 Wafer 分组)
    if 'wafer_id' not in data_to_process.columns:
        logger.error("筛选后的数据中缺少 'wafer_id' 列，无法按晶圆分组计算统计量。")
        return pd.DataFrame()

    # 只选择数值类型的参数列进行统计
    # 再次检查 param_cols 是否还存在于 data_to_process 中（虽然不太可能被删除）
    numeric_param_cols = data_to_process.select_dtypes(include=np.number).columns
    valid_param_cols = [p for p in param_cols if p in numeric_param_cols]
    
    if not valid_param_cols:
        logger.warning("筛选后的数据中没有找到数值类型的参数列进行统计。")
        return pd.DataFrame()
    logger.info(f"将对以下数值参数进行统计: {valid_param_cols}")

    # 定义聚合函数
    agg_funcs = {
        'count': 'count', # N
        'mean': 'mean',   # Avg
        'std': 'std',    # Std
        'min': 'min',
        'q1': lambda x: x.quantile(0.25),
        'median': 'median',
        'q3': lambda x: x.quantile(0.75),
        'max': 'max'
    }

    try:
        # 按 wafer_id 分组并聚合
        grouped_stats = data_to_process.groupby('wafer_id')[valid_param_cols].agg(agg_funcs)
        logger.debug(f"分组统计计算完成，得到 {len(grouped_stats)} 个晶圆的统计数据。")

        # 计算 IQR 和 RobustStd
        for param_id in valid_param_cols:
            q3 = grouped_stats.get((param_id, 'q3')) # 使用 get 处理可能的 MultiIndex
            q1 = grouped_stats.get((param_id, 'q1'))
            if q3 is not None and q1 is not None:
                iqr = q3 - q1
                # 处理 IQR 为 0 的情况以避免除零错误
                robust_std = iqr / 1.34898 if 1.34898 != 0 else np.nan 
                grouped_stats[(param_id, 'iqr')] = iqr
                grouped_stats[(param_id, 'robust_std')] = robust_std
            else:
                # 如果 q1 或 q3 缺失 (例如数据点太少无法计算分位数)
                grouped_stats[(param_id, 'iqr')] = np.nan
                grouped_stats[(param_id, 'robust_std')] = np.nan
        logger.debug("IQR 和 RobustStd 计算完成。")

        # 重新排序列名以匹配期望的输出
        stats_order = ['count', 'mean', 'std', 'min', 'q1', 'median', 'q3', 'max', 'iqr', 'robust_std']
        # 检查实际生成的统计列，因为某些 lambda 函数可能不会生成预期的列名
        actual_stats_in_cols = grouped_stats.columns.get_level_values(1).unique().tolist()
        # 仅保留实际存在的统计列，并按期望顺序排序
        effective_stats_order = [s for s in stats_order if s in actual_stats_in_cols]
        
        new_multi_index = pd.MultiIndex.from_product([valid_param_cols, effective_stats_order], names=['Parameter', 'Statistic'])
        # 使用 reindex 确保列顺序和填充缺失列 (如果需要)
        grouped_stats = grouped_stats.reindex(columns=new_multi_index)
        logger.debug("分组统计列重新排序完成。")

        # 计算整个 Lot 的汇总统计
        overall_stats = data_to_process[valid_param_cols].agg(agg_funcs)
        if not overall_stats.empty:
            # 计算 IQR 和 RobustStd for overall
            overall_q3 = overall_stats.loc['q3']
            overall_q1 = overall_stats.loc['q1']
            overall_iqr = overall_q3 - overall_q1
            overall_robust_std = overall_iqr / 1.34898 if 1.34898 != 0 else np.nan
            overall_stats.loc['iqr'] = overall_iqr
            overall_stats.loc['robust_std'] = overall_robust_std
            # 确保汇总统计的索引顺序与分组统计一致
            overall_stats = overall_stats.reindex(effective_stats_order)
            
            # 将汇总行添加到 DataFrame
            # 创建一个 MultiIndex DataFrame 用于汇总行
            # Series 转置后是 DataFrame, index 默认是原 Series index ('count', 'mean', ...) columns 是原参数名
            overall_df_transposed = pd.DataFrame(overall_stats) 
            # 再次转置使 index 变成参数名， columns 变成统计量名
            overall_df = overall_df_transposed.T 
            overall_df.index = pd.Index(["_All"], name="wafer_id") # 设置索引为 "_All"
            # 重构列为 MultiIndex
            overall_df.columns = pd.MultiIndex.from_product([valid_param_cols, effective_stats_order], names=['Parameter', 'Statistic'])
            # 使用 reindex 确保汇总行的列与 grouped_stats 完全一致
            overall_df = overall_df.reindex(columns=new_multi_index)

            logger.debug("Lot 汇总统计计算完成。")
            # 合并分组统计和汇总统计
            final_summary = pd.concat([grouped_stats, overall_df])
        else:
            logger.warning("无法计算 Lot 汇总统计，可能是因为没有有效数据。")
            final_summary = grouped_stats # 仅返回分组统计

        # 重命名统计量列以匹配 VBA (可选)
        final_summary.rename(columns={'count': 'N', 'mean': 'Mean', 'std': 'Std',
                                      'q1': '25%', 'median': 'Median', 'q3': '75%',
                                      'iqr': 'IQR', 'robust_std': 'RobustStd'},
                             level=1, inplace=True)
        logger.info("参数统计汇总计算成功。")
        return final_summary

    except Exception as e:
        logger.error(f"计算参数统计时发生错误: {e}", exc_info=True)
        return pd.DataFrame() # 返回空 DataFrame 表示失败

# 示例用法 (假设已有 CPLot 对象 cp_lot_obj 且已调用 combine_data_from_wafers)
if __name__ == '__main__':
    # 配置基本日志记录
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("运行参数分布统计模块示例...")
    
    # 需要创建模拟的 CPLot 对象进行测试
    # (省略了创建模拟数据的代码，需要从 数据类型定义.py 引入并创建实例)
    
    # from 数据类型定义 import CPLot, CPWafer, CPParameter
    # # ... 创建 cp_lot_obj ...
    # cp_lot_obj.combine_data_from_wafers()
    
    # 假设 cp_lot_obj 已准备好
    # summary_df = calculate_parameter_summary(cp_lot_obj)
    # print("\n--- 默认统计结果 ---")
    # print(summary_df)
    
    # # 测试带范围筛选
    # scopes = {'Param1': (0, 10), 'Param2': (None, 50)}
    # summary_scoped_df = calculate_parameter_summary(cp_lot_obj, scope_limits=scopes)
    # print("\n--- 带范围筛选统计结果 ---")
    # print(summary_scoped_df)
    
    # # 测试带规格筛选 (假设 Param1 定义了 SL=1, SU=9)
    # # cp_lot_obj.params[0].sl = 1
    # # cp_lot_obj.params[0].su = 9
    # summary_spec_df = calculate_parameter_summary(cp_lot_obj, filter_by_spec=True)
    # print("\n--- 带规格筛选统计结果 ---")
    # print(summary_spec_df)
    
    print("\n(请取消注释并提供有效的 CPLot 对象以运行完整示例)") 