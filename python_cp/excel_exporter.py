import pandas as pd
import logging
from typing import Optional, Dict
import xlsxwriter # 使用 xlsxwriter 以便后续可能插入图表等
import time # 修正导入
import numpy as np # 修正导入

# 尝试相对导入
try:
    from .数据类型定义 import CPLot, CPParameter, CPWafer # 导入 CPWafer
    from .参数分布统计 import calculate_parameter_summary # 需要导入统计函数
    from .yield_calculator import calculate_lot_yield_summary # 导入新的良率计算函数
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("无法执行相对导入 '..数据类型定义' 或 '.参数分布统计'。请确保脚本从正确的包结构运行，" 
                   "或调整导入路径。将使用占位符类和函数。")
    class CPLot: 
        def __init__(self): 
            self.wafers = []
            self.params = []
            self.combined_data = pd.DataFrame()
            self.lot_id = "temp"
            self.pass_bin = 1 # Add pass_bin for placeholder
        def get_param_by_id(self, id): return None
        
    class CPParameter: pass
    class CPWafer: pass # Add placeholder
    def calculate_parameter_summary(*args, **kwargs): return pd.DataFrame()
    def calculate_lot_yield_summary(*args, **kwargs): return pd.DataFrame() # 添加占位符

logger = logging.getLogger(__name__)

def _export_spec_sheet(cp_lot: CPLot, writer: pd.ExcelWriter, convert_limits: bool = True):
    """
    将参数规格信息导出到 Spec Sheet。模拟 VBA FillSpec。
    
    Args:
        cp_lot (CPLot): CP测试数据对象
        writer (pd.ExcelWriter): Excel写入器
        convert_limits (bool): 是否将上下限转换为标准单位值（默认为True）
    """
    logger.info("正在导出 Spec Sheet...")
    if not cp_lot.params:
        logger.warning("CPLot 对象中没有参数信息，无法导出 Spec Sheet。")
        # 创建一个空表头
        df_spec = pd.DataFrame(columns=['Param', 'Unit', 'SL', 'SU', 'TestCond:'])
        df_spec.to_excel(writer, sheet_name='Spec', index=False)
        return

    # 如果需要转换单位，创建单位转换器
    converter = None
    if convert_limits:
        try:
            from cp_data_processor.processing.unit_converter import UnitConverter
            converter = UnitConverter()
            logger.info("已启用上下限单位转换功能")
        except ImportError:
            logger.warning("无法导入单位转换器，将使用原始上下限值")

    spec_data = []
    max_test_cond_len = 0
    for param in cp_lot.params:
        # 处理上下限值，如果需要则转换为标准单位
        sl = param.sl
        su = param.su
        
        if converter and sl is not None and sl != "" and not pd.isna(sl):
            if isinstance(sl, str):
                # 如果上下限是字符串格式，尝试提取值和单位
                converted_sl = converter.convert_to_standard(sl)
                if converted_sl is not None:
                    sl = converted_sl
            
        if converter and su is not None and su != "" and not pd.isna(su):
            if isinstance(su, str):
                # 如果上下限是字符串格式，尝试提取值和单位
                converted_su = converter.convert_to_standard(su)
                if converted_su is not None:
                    su = converted_su
            
        row = {
            'Param': param.id,
            'Unit': param.unit,
            'SL': sl,
            'SU': su
        }
        
        # 测试条件保持原样
        if param.test_cond:
             max_test_cond_len = max(max_test_cond_len, len(param.test_cond))
             for i, cond in enumerate(param.test_cond):
                 row[f'TestCond{i+1}'] = cond # 使用 TestCond1, TestCond2 ... 作为列名
        
        spec_data.append(row)

    df_spec = pd.DataFrame(spec_data)
    
    # 调整列顺序，确保 TestCond 列在后面
    base_cols = ['Param', 'Unit', 'SL', 'SU']
    cond_cols = [f'TestCond{i+1}' for i in range(max_test_cond_len)]
    final_cols = base_cols + cond_cols
    # Reindex 以确保所有列存在且顺序正确，缺失的 TestCond 列会填充 NaN
    df_spec = df_spec.reindex(columns=final_cols)

    # 写入 Excel
    df_spec.to_excel(writer, sheet_name='Spec', index=False)
    logger.debug("Spec Sheet 导出完成。")

def _export_data_sheet(cp_lot: CPLot, writer: pd.ExcelWriter):
    """将合并后的测试数据导出到 Data Sheet。模拟 VBA FillTestData。"""
    logger.info("正在导出 Data Sheet...")
    if cp_lot.combined_data is None or cp_lot.combined_data.empty:
        logger.warning("CPLot 对象的 combined_data 为空，无法导出 Data Sheet。请先调用 combine_data_from_wafers()。")
        # 创建一个空表头模拟
        header = ['Wafer', 'Seq', 'Bin', 'X', 'Y'] + [p.id for p in cp_lot.params]
        df_data = pd.DataFrame(columns=header)
        df_data.to_excel(writer, sheet_name='Data', index=False)
        return
        
    # combined_data 应该已经包含了 'wafer_id', 'seq', 'x', 'y', 'bin' 和参数列
    # 直接写入即可
    cp_lot.combined_data.to_excel(writer, sheet_name='Data', index=False)
    logger.debug("Data Sheet 导出完成。")

def _export_yield_sheet(cp_lot: CPLot, writer: pd.ExcelWriter):
    """将良率汇总信息导出到 Yield Sheet。模拟 VBA ShowYield。"""
    logger.info("正在导出 Yield Sheet...")
    try:
        df_yield = calculate_lot_yield_summary(cp_lot)
        if df_yield.empty:
            logger.warning("计算得到的良率汇总为空，Yield Sheet 将只包含表头或为空。")
        
        # 格式化 Yield 列为百分比 (可选，也可以在 Excel 中设置格式)
        if 'Yield' in df_yield.columns:
             # 仅对数值类型应用格式化，避免对 'All' 行的字符串等操作
             yield_col = df_yield['Yield']
             mask = pd.to_numeric(yield_col, errors='coerce').notna()
             # 使用 .loc 避免 SettingWithCopyWarning
             df_yield.loc[mask, 'Yield_str'] = df_yield.loc[mask, 'Yield'].apply(lambda x: f"{x:.2%}")
             df_yield.loc[~mask, 'Yield_str'] = df_yield.loc[~mask, 'Yield'] # 保留非数值（如 'All' 行的0.0）
             # 可以选择重命名或删除原始 Yield 列
             df_yield = df_yield.rename(columns={'Yield': 'Yield_float', 'Yield_str': 'Yield'})
             df_yield = df_yield.drop(columns=['Yield_float'], errors='ignore')

        df_yield.to_excel(writer, sheet_name='Yield', index=False)
        logger.debug("Yield Sheet 导出完成。")
    except Exception as e:
        logger.error(f"导出 Yield Sheet 时出错: {e}", exc_info=True)
        # 写入一个空表以避免文件损坏
        pd.DataFrame().to_excel(writer, sheet_name='Yield', index=False)

def _export_summary_sheet(cp_lot: CPLot, writer: pd.ExcelWriter, summary_options: Optional[Dict] = None):
    """将参数统计汇总信息导出到 Summary Sheet。模拟 VBA mySummary。"""
    logger.info("正在导出 Summary Sheet...")
    summary_opts = summary_options or {}
    try:
        # 调用独立的统计函数
        df_summary = calculate_parameter_summary(cp_lot, **summary_opts)
        
        if df_summary.empty:
            logger.warning("计算得到的参数统计汇总为空，Summary Sheet 将只包含表头或为空。")
        
        # MultiIndex 列导出到 Excel 时通常会自动处理
        # 需要将 MultiIndex 行索引 ("wafer_id") 也写入为普通列
        df_summary.reset_index(inplace=True) 
        
        # 写入 Excel
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        logger.debug("Summary Sheet 导出完成。")
        
    except Exception as e:
        logger.error(f"导出 Summary Sheet 时出错: {e}", exc_info=True)
        pd.DataFrame().to_excel(writer, sheet_name='Summary', index=False)

def export_analysis_to_excel(
    cp_lot: CPLot,
    output_excel_path: str,
    export_spec: bool = True,
    export_data: bool = True,
    export_yield: bool = True,
    export_summary: bool = True,
    convert_limits: bool = True,  # 新增参数：是否转换上下限
    summary_options: Optional[Dict] = None
):
    """
    将 CP Lot 的核心分析数据导出到单个 Excel 文件的不同 Sheet 页。

    Args:
        cp_lot (CPLot): 已处理和合并数据的 CPLot 对象。
        output_excel_path (str): 输出 Excel 文件的完整路径。
        export_spec (bool): 是否导出 Spec Sheet。
        export_data (bool): 是否导出 Data Sheet (合并后的原始数据)。
        export_yield (bool): 是否导出 Yield Sheet (良率汇总)。
        export_summary (bool): 是否导出 Summary Sheet (参数统计汇总)。
        convert_limits (bool): 是否将规格上下限转换为标准单位值。
        summary_options (Optional[Dict]): 传递给 calculate_parameter_summary 的选项。
    """
    logger.info(f"准备将分析结果导出到 Excel 文件: {output_excel_path}")
    start_time = time.time()
    
    try:
        # 使用 Pandas ExcelWriter (基于 xlsxwriter 引擎)
        with pd.ExcelWriter(output_excel_path, engine='xlsxwriter') as writer:
            
            if export_spec:
                _export_spec_sheet(cp_lot, writer, convert_limits=convert_limits)
                
            if export_data:
                _export_data_sheet(cp_lot, writer)
                
            if export_yield:
                _export_yield_sheet(cp_lot, writer)
                
            if export_summary:
                 _export_summary_sheet(cp_lot, writer, summary_options)
                 
            # (未来可以在这里添加其他 sheet 页，例如图例说明等)
            
        duration = time.time() - start_time
        logger.info(f"成功将核心分析数据导出到 Excel 文件 (耗时: {duration:.2f} 秒)。")

    except Exception as e:
        logger.error(f"导出 Excel 分析文件 '{output_excel_path}' 时发生严重错误: {e}", exc_info=True)

# --- 示例用法 --- 
if __name__ == '__main__':
    import time # 导入 time 模块
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("运行 Excel Exporter 模块示例...")

    # --- 创建模拟 CPLot 数据 (与 main_processor.py 类似) ---
    logger.info("创建模拟 CPLot 数据...")
    lot = CPLot(lot_id="ExportTest01", product="ExportProd")
    params = [
        CPParameter(id='Vth', group='FET', display_name='Threshold V', unit='V', sl=0.3, su=0.7, test_cond=['Vds=0.1V', 'Ids=1uA']),
        CPParameter(id='Idsat', group='FET', display_name='Saturation I', unit='mA', sl=1.0, su=None, test_cond=['Vds=1.2V', 'Vgs=1.2V']),
        CPParameter(id='Res', group='Passive', display_name='Resistance', unit='Ohm', test_cond=['I=1mA'])
    ]
    lot.params = params

    all_wafer_data = []
    for i in range(1, 4): # 创建 3 个 Wafer
        wafer_id = f"ExpW{i:02d}"
        chip_count = 50
        seq = np.arange(1, chip_count + 1)
        x = np.random.randint(-5, 6, size=chip_count)
        y = np.random.randint(-5, 6, size=chip_count)
        bins = np.random.randint(1, 4, size=chip_count).astype(float)
        bins[np.random.choice(chip_count, 5, replace=False)] = np.nan # Add some NaN bins
        
        vth_data = np.random.normal(0.5, 0.1, size=chip_count)
        idsat_data = np.random.normal(1.5, 0.2, size=chip_count) * 1e-3 # mA -> A for calculation consistency?
        res_data = np.random.normal(100, 10, size=chip_count)
        
        # Add some NaN param data
        vth_data[np.random.choice(chip_count, 3, replace=False)] = np.nan
        idsat_data[np.random.choice(chip_count, 4, replace=False)] = np.nan
        
        chip_df = pd.DataFrame({
            'Vth': vth_data,
            'Idsat': idsat_data,
            'Res': res_data
        })
        
        wafer = CPWafer(
            wafer_id=wafer_id,
            chip_count=chip_count,
            seq=seq,
            x=x,
            y=y,
            bin=bins,
            chip_data=chip_df
        )
        lot.wafers.append(wafer)
        
        # 准备合并数据
        temp_df = chip_df.copy()
        temp_df['wafer_id'] = wafer_id
        temp_df['seq'] = seq
        temp_df['x'] = x
        temp_df['y'] = y
        temp_df['bin'] = bins
        all_wafer_data.append(temp_df)
        
    # 手动合并数据 (模拟 combine_data_from_wafers)
    if all_wafer_data:
        lot.combined_data = pd.concat(all_wafer_data, ignore_index=True)
        cols_to_move = ['wafer_id', 'seq', 'x', 'y', 'bin']
        remaining_cols = [col for col in lot.combined_data.columns if col not in cols_to_move]
        lot.combined_data = lot.combined_data[cols_to_move + remaining_cols]
    else:
        lot.combined_data = pd.DataFrame()
        
    logger.info("模拟数据创建完成。")

    # --- 测试导出 --- 
    output_file = "excel_exporter_output.xlsx"
    logger.info(f"开始将分析结果导出到 {output_file}...")
    export_analysis_to_excel(lot, output_file, 
                             export_spec=True,
                             export_data=True,
                             export_yield=True,
                             export_summary=True,
                             convert_limits=True,
                             summary_options={'filter_by_spec': False} # 示例统计选项
                            )
    logger.info("Excel 导出完成。")

    print(f"\n请检查生成的 Excel 文件: '{output_file}'") 