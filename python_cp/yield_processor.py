import pandas as pd
from typing import List, Dict, Any
import logging

# 配置日志
logger = logging.getLogger(__name__)

def generate_yield_report_from_dataframe(cleaned_df: pd.DataFrame, output_filepath: str) -> bool:
    """
    根据清洗后的DataFrame生成良率报告CSV文件。

    该函数遵循 yield.md 中的规范来计算每个晶圆的良率以及整个批次的汇总统计。

    Args:
        cleaned_df (pd.DataFrame): 包含清洗后数据的Pandas DataFrame。
                                   必须包含 'Lot_ID', 'Wafer_ID', 'Bin' 列。
        output_filepath (str): 生成的良率报告CSV文件的完整路径。

    Returns:
        bool: 如果报告成功生成则返回True，否则返回False。
    """
    if not isinstance(cleaned_df, pd.DataFrame):
        logger.error("输入数据不是有效的Pandas DataFrame。")
        return False

    if cleaned_df.empty:
        logger.warning("输入的DataFrame为空，无法生成良率报告。")
        # 可以选择创建一个空的或只有表头的CSV
        # pd.DataFrame(columns=TARGET_COLUMNS).to_csv(output_filepath, index=False, encoding='utf-8-sig')
        return False

    required_columns = ['Lot_ID', 'Wafer_ID', 'Bin']
    if not all(col in cleaned_df.columns for col in required_columns):
        logger.error(f"输入DataFrame缺失必要列。需要: {required_columns}, 实际拥有: {cleaned_df.columns.tolist()}")
        return False

    TARGET_BINS = [3, 4, 6, 7, 8, 9]
    TARGET_COLUMNS = ['Lot_ID', 'Wafer_ID', 'Yield', 'Total', 'Pass'] + [f'Bin{b}' for b in TARGET_BINS]

    wafer_reports_data: List[Dict[str, Any]] = []
    all_wafer_numerical_yields: List[float] = [] # 用于计算批次平均良率

    # 修改分组方式，支持多批次同名晶圆
    grouped_by_wafer = cleaned_df.groupby(['Lot_ID', 'Wafer_ID'], sort=False) # sort=False 保持原始顺序

    if grouped_by_wafer.ngroups == 0:
        logger.warning("DataFrame中没有找到任何Lot_ID+Wafer_ID分组，无法生成良率报告。")
        return False
        
    for (lot_id, wafer_id), wafer_data in grouped_by_wafer:
        wafer_report: Dict[str, Any] = {}
        wafer_report['Lot_ID'] = str(lot_id)
        wafer_report['Wafer_ID'] = str(wafer_id)
        total_die = len(wafer_data)
        wafer_report['Total'] = total_die
        pass_die = wafer_data[wafer_data['Bin'] == 1].shape[0]
        wafer_report['Pass'] = pass_die
        for bin_val in TARGET_BINS:
            wafer_report[f'Bin{bin_val}'] = wafer_data[wafer_data['Bin'] == bin_val].shape[0]
        numerical_yield = 0.0
        if total_die > 0:
            numerical_yield = (pass_die / total_die) * 100
        all_wafer_numerical_yields.append(numerical_yield)
        wafer_report['Yield'] = f"{numerical_yield:.2f}%"
        wafer_reports_data.append(wafer_report)

    # 计算 "ALL" 汇总行
    if wafer_reports_data: # 确保至少有一个晶圆被处理了
        all_row: Dict[str, Any] = {'Lot_ID': 'ALL', 'Wafer_ID': 'ALL'}
        
        all_total_die = sum(item['Total'] for item in wafer_reports_data)
        all_pass_die = sum(item['Pass'] for item in wafer_reports_data)
        
        all_row['Total'] = all_total_die
        all_row['Pass'] = all_pass_die

        for bin_val in TARGET_BINS:
            all_row[f'Bin{bin_val}'] = sum(item[f'Bin{bin_val}'] for item in wafer_reports_data)

        average_lot_yield = 0.0
        if all_wafer_numerical_yields: # 避免除以零
            # 根据 yield.md: "ALL"行为批次内所有晶圆良率的算术平均值
            average_lot_yield = sum(all_wafer_numerical_yields) / len(all_wafer_numerical_yields)
        
        # 特殊情况：如果所有晶圆的Total都为0，则批次Yield为 "0.00%"
        # 这个条件实际上通过上面的 average_lot_yield 计算可以自然处理，
        # 因为如果所有 wafer 的 total_die 为 0，则 numerical_yield 都为 0。
        # 但可以显式检查一下，如果所有 all_wafer_numerical_yields 都是 0，则 average_lot_yield 也是 0.
        
        all_row['Yield'] = f"{average_lot_yield:.2f}%"
        wafer_reports_data.append(all_row)

    # 创建最终的 DataFrame 并保存
    try:
        final_df = pd.DataFrame(wafer_reports_data, columns=TARGET_COLUMNS)
        # 确保所有目标列都存在，以防万一（例如，如果没有晶圆数据，wafer_reports_data为空）
        # 对于空的 wafer_reports_data，DataFrame(data, columns=cols) 会创建带列名但无数据的df
        if final_df.empty and not wafer_reports_data: # 处理完全没有晶圆数据的情况
             final_df = pd.DataFrame(columns=TARGET_COLUMNS) # 创建一个带表头的空文件

        final_df.to_csv(output_filepath, index=False, encoding='utf-8-sig')
        logger.info(f"良率报告已成功生成并保存到: {output_filepath}")
        return True
    except Exception as e:
        logger.error(f"保存良率报告到 {output_filepath} 时发生错误: {e}")
        return False

if __name__ == '__main__':
    # 示例用法，用于模块独立测试
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 构建一个符合输入要求的模拟 DataFrame
    sample_data = {
        'Lot_ID': ['LOT001'] * 10 + ['LOT001'] * 8,
        'Wafer_ID': ['W1'] * 10 + ['W2'] * 8,
        'X': [i for i in range(10)] + [i for i in range(8)],
        'Y': [i*2 for i in range(10)] + [i*3 for i in range(8)],
        'Bin': [1, 1, 2, 3, 1, 4, 1, 6, 1, 1,   # Wafer W1 data (10 dies, 6 pass)
                1, 2, 1, 1, 7, 8, 9, 1],     # Wafer W2 data (8 dies, 4 pass)
        'Test_Time': [pd.Timestamp('2023-01-01 10:00:00')] * 18
    }
    # 模拟一些其他列
    for i in range(1, 5):
        sample_data[f'Param{i}'] = [i * 10 + j for j in range(18)]

    mock_cleaned_df = pd.DataFrame(sample_data)
    
    # 增加一个 Bin 值不存在于 TARGET_BINS 中的情况
    mock_cleaned_df.loc[2, 'Bin'] = 50 # This Bin won't be in BinX columns but is part of Total

    # 测试情况1: 正常数据
    output_file_1 = "sample_yield_report.csv"
    logger.info(f"测试1: 使用模拟数据生成报告到 {output_file_1}")
    success1 = generate_yield_report_from_dataframe(mock_cleaned_df, output_file_1)
    logger.info(f"测试1 完成, 结果: {'成功' if success1 else '失败'}")
    if success1:
        logger.info(f"测试1 内容:\n{pd.read_csv(output_file_1)}")

    # 测试情况2: 空 DataFrame
    empty_df = pd.DataFrame(columns=['Lot_ID', 'Wafer_ID', 'X', 'Y', 'Bin', 'Test_Time'])
    output_file_2 = "empty_yield_report.csv"
    logger.info(f"测试2: 使用空DataFrame生成报告到 {output_file_2}")
    success2 = generate_yield_report_from_dataframe(empty_df, output_file_2)
    logger.info(f"测试2 完成, 结果: {'成功' if success2 else '失败'}")
    if success2 and pd.read_csv(output_file_2).empty:
         logger.info(f"测试2: {output_file_2} 正确地生成为空文件或只有表头。")
    elif success2:
         logger.info(f"测试2 内容:\n{pd.read_csv(output_file_2)}")


    # 测试情况3: DataFrame 中没有目标 Bin 值 （例如所有都是 Bin 1）
    all_pass_data = {
        'Lot_ID': ['LOT002'] * 5,
        'Wafer_ID': ['W3'] * 5,
        'X': range(5), 'Y': range(5),
        'Bin': [1] * 5,
        'Test_Time': [pd.Timestamp('2023-01-01 11:00:00')] * 5
    }
    all_pass_df = pd.DataFrame(all_pass_data)
    output_file_3 = "all_pass_yield_report.csv"
    logger.info(f"测试3: DataFrame中只有Pass Bin，报告到 {output_file_3}")
    success3 = generate_yield_report_from_dataframe(all_pass_df, output_file_3)
    logger.info(f"测试3 完成, 结果: {'成功' if success3 else '失败'}")
    if success3:
        logger.info(f"测试3 内容:\n{pd.read_csv(output_file_3)}")

    # 测试情况4: DataFrame 中一个晶圆total die为0 (通过一个空的group)
    # 这种情况groupby不会产生该group，所以不会在all_wafer_numerical_yields中产生除0问题
    # 若要严格模拟一个wafer total 0, 可以构造一个空的wafer_data传入（但groupby会跳过空组）
    # 或者一个wafer_id存在，但所有相关行都被过滤掉了，导致cleaned_df中没有该wafer_id的数据
    # 当前逻辑下，如果一个WaferID在cleaned_df中没有行，它就不会出现在grouped_by_wafer中。
    # 如果一个WaferID有行，但被过滤后total_die=0 (理论上不太可能，因为行存在就有数量)
    # 关键是 (pass_die / total_die) if total_die > 0 else 0.0

    # 测试情况5: DataFrame 中包含 Lot_ID 和 Wafer_ID 为非字符串类型 (例如数字)
    numeric_id_data = {
        'Lot_ID': [200] * 3, # Numeric Lot ID
        'Wafer_ID': [101] * 3, # Numeric Wafer ID
        'X': range(3), 'Y': range(3),
        'Bin': [1,3,6],
        'Test_Time': [pd.Timestamp('2023-01-01 12:00:00')] * 3
    }
    numeric_id_df = pd.DataFrame(numeric_id_data)
    output_file_4 = "numeric_id_yield_report.csv"
    logger.info(f"测试4: DataFrame中LotID和WaferID为数字，报告到 {output_file_4}")
    success4 = generate_yield_report_from_dataframe(numeric_id_df, output_file_4)
    logger.info(f"测试4 完成, 结果: {'成功' if success4 else '失败'}")
    if success4:
        logger.info(f"测试4 内容:\n{pd.read_csv(output_file_4)}")
        # 验证输出的Lot_ID和Wafer_ID是否为字符串
        df_check = pd.read_csv(output_file_4)
        if isinstance(df_check['Lot_ID'].iloc[0], str) and isinstance(df_check['Wafer_ID'].iloc[0], str):
            logger.info("测试4: Lot_ID 和 Wafer_ID 已正确转换为字符串。")
        else:
            logger.error("测试4: Lot_ID 或 Wafer_ID 未能正确转换为字符串。")
            
    # 测试情况6: 输入的 DataFrame 中没有 'Bin' 列
    no_bin_df = pd.DataFrame({
        'Lot_ID': ['LOT003'] * 2,
        'Wafer_ID': ['W4'] * 2,
        'X': [1,2], 'Y': [1,2]
    })
    output_file_5 = "no_bin_yield_report.csv"
    logger.info(f"测试5: DataFrame中缺少 'Bin' 列，报告到 {output_file_5}")
    success5 = generate_yield_report_from_dataframe(no_bin_df, output_file_5) #应该返回False
    logger.info(f"测试5 完成, 结果: {'成功' if success5 else '失败 (预期)'}")


    # 测试情况7: 一个Wafer的Total Die为0的情况 (例如，输入数据被过滤到空)
    # 这种情况，groupby('Wafer_ID') 将不会包含这个Wafer_ID，因此不会出错
    # 但如果cleaned_df 包含一个Wafer_ID，而其所有Bin都是NaN导致处理后total_die有效计数为0，
    # yield.md要求"如果Total为0，Yield应为 '0.00%'"。
    # 当前的 (pass_die / total_die) * 100 if total_die > 0 else 0.0 已经处理了此情况
    # get_wafer_bin_counts 在 yield_calculator.py 中有dropna()
    # 在此脚本中，total_die = len(wafer_data)。如果wafer_data本身就是空的（被过滤掉了），那它不会进入循环
    # 如果wafer_data不空，total_die > 0。

    logger.info("示例用法执行完毕。") 