# python_cp/main_processor.py
import argparse
import logging
import os
import time
from pathlib import Path
import yaml # 用于读取配置文件
from typing import Optional # 明确导入 Optional

# --- 相对导入我们已创建的模块 ---
# 注意：实际运行时需要确保 python_cp 是一个可识别的包，或者调整 sys.path
try:
    from .数据类型定义 import CPLot
    from .readers.cw_reader import CWReader
    from .readers.mex_reader import MEXReader
    from .readers.dcp_reader import DCPReader # 取消注释
    from .参数分布统计 import calculate_parameter_summary
    # from .增加运算数据 import add_calculated_data # 占位
    from .plotting.wafer_map import plot_all_wafers_to_excel
    from .plotting.boxplot import plot_parameter_boxplots_to_excel
    from .plotting.scatter_plot import plot_scatter_charts_to_excel # 导入散点图
    # from .plotting.param_color_map import plot_param_color_map # 占位
    from .excel_exporter import export_analysis_to_excel # 导入 Excel 导出器
    # from .ppt_exporter import create_ppt_report # 占位
    import pandas as pd # 导入 pandas
except ImportError as e:
    # 尝试在导入失败时获取 logger
    logger_init_error = logging.getLogger(__name__)
    logger_init_error.error(f"导入模块时出错，请确保运行环境和路径正确: {e}")
    # 定义占位符，以便脚本能基本解析
    class CPLot: pass
    class CWReader:
        def read(self, *args, **kwargs):
            logger_init_error.warning("Using placeholder CWReader.read()")
            return CPLot() # 返回一个 CPLot 实例
    class MEXReader:
        def read(self, *args, **kwargs):
            logger_init_error.warning("Using placeholder MEXReader.read()")
            return CPLot() # 返回一个 CPLot 实例
    class DCPReader: # 添加 DCPReader 占位符
        def read(self, *args, **kwargs):
            logger_init_error.warning("Using placeholder DCPReader.read()")
            return CPLot()
    # ... 其他占位符 ...
    import pandas as pd # 确保 pandas 在这个块中也导入了
    def calculate_parameter_summary(*args, **kwargs): return pd.DataFrame()
    def plot_all_wafers_to_excel(*args, **kwargs): pass
    def plot_parameter_boxplots_to_excel(*args, **kwargs): pass
    def plot_scatter_charts_to_excel(*args, **kwargs): pass
    def export_analysis_to_excel(*args, **kwargs): pass

# --- 日志配置 ---
# 确保 logger 在 try-except 块外部定义，以便全局可用
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    handlers=[
                        logging.FileHandler("cp_processor.log", mode='w'), # 写入日志文件
                        logging.StreamHandler() # 输出到控制台
                    ])
logger = logging.getLogger(__name__)
logging.getLogger('matplotlib').setLevel(logging.WARNING) # 减少 matplotlib 的冗余日志

# --- 默认配置 ---
# 这些值会被配置文件覆盖
DEFAULT_CONFIG = {
    'add_calculated_data': False,
    'plot_bin_map': True,
    'plot_box_plot': True,
    'plot_param_color_map': False,
    'plot_scatter_plot': False, # 添加散点图开关
    'generate_ppt': False,
    'box_plot_params': [], # 需要绘制箱线图的参数 ID 列表
    'scatter_plot_configs': [], # 散点图设置列表，例如 [{'x_param': 'Vth', 'y_param': 'Idsat', 'title': 'Optional Title', 'x_axis_options': {'min': 0, 'max': 1}, 'y_axis_options': {}}, ...]
    'param_color_map_params': [], # 参数颜色图参数列表 (未来定义)
    'excel_export': {
        'spec': True,
        'data': True,
        'yield': True,
        'summary': True
    },
    'summary_options': {'filter_by_spec': False, 'scope_limits': None}, # 参数统计选项
    'wafer_map_options': {'invert_xaxis': True, 'cols_per_row': 4, 'image_options': {'x_scale': 0.4, 'y_scale': 0.4}},
    'boxplot_options': {'cols_per_row': 5, 'image_options': {'x_scale': 0.4, 'y_scale': 0.4}},
    'scatter_plot_options': {'cols_per_row': 5, 'image_options': {'x_scale': 0.4, 'y_scale': 0.4}, 'marker_size': 5, 'figure_size': (6, 4)}, # 散点图选项, 添加 figure_size
    # ... 其他配置项
}

def load_config(config_path: Optional[str]) -> dict:
    """加载 YAML 配置文件，如果路径无效或文件不存在则使用默认配置。"""
    config = DEFAULT_CONFIG.copy()
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
            if user_config:
                # 深层合并字典，用户配置覆盖默认配置
                def merge_dicts(d1, d2):
                    for k, v in d2.items():
                        if isinstance(v, dict) and k in d1 and isinstance(d1[k], dict):
                            merge_dicts(d1[k], v)
                        else:
                            d1[k] = v
                merge_dicts(config, user_config)
                logger.info(f"成功加载配置文件: {config_path}")
            else:
                 logger.warning(f"配置文件 '{config_path}' 为空，使用默认配置。")
        except Exception as e:
            logger.error(f"加载配置文件 '{config_path}' 时出错: {e}，将使用默认配置。", exc_info=True)
    else:
        # 只有在提供了 config_path 但无效时才警告，如果没提供则静默使用默认值
        if config_path:
            logger.warning(f"配置文件路径无效或文件不存在: '{config_path}'，使用默认配置。")
        else:
            logger.info("未提供配置文件路径，使用默认配置。")
    return config

def main():
    parser = argparse.ArgumentParser(description="CP 数据处理与分析工具")
    parser.add_argument("data_files", nargs='+', help="输入的原始数据文件路径 (支持多个)")
    parser.add_argument("-f", "--format", required=True, choices=["CWSW", "CWMW", "MEX", "DCP"],
                        help="输入数据的格式")
    parser.add_argument("-o", "--output-dir", default=".", help="输出文件存放目录 (默认为当前目录)")
    parser.add_argument("-c", "--config", help="YAML 配置文件路径")
    # 可以添加更多参数，例如直接覆盖配置项

    args = parser.parse_args()

    start_time = time.time()
    logger.info("=== CP 数据处理开始 ===")
    logger.info(f"数据格式: {args.format}")
    logger.info(f"输入文件: {args.data_files}")
    logger.info(f"输出目录: {args.output_dir}")
    logger.info(f"配置文件: {args.config}")

    # --- 加载配置 ---
    config = load_config(args.config)
    logger.debug(f"当前使用的配置: {config}")

    # --- 创建输出目录 ---
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"输出将保存到: {output_dir.resolve()}")

    # --- 1. 读取数据 ---
    cp_lot: Optional[CPLot] = None
    reader = None
    try:
        # 重新导入 scatter plot 相关模块，确保在 try 块内
        try:
            from .plotting.scatter_plot import plot_scatter_charts_to_excel
        except ImportError:
            # 如果导入失败，使用之前定义的占位符
            logger.warning("无法导入 scatter_plot 模块，将使用占位符函数。")
            pass # 占位符已在外部定义

        if args.format == "CWSW":
            reader = CWReader(args.data_files, is_multi_wafer=False)
        elif args.format == "CWMW":
            if len(args.data_files) > 1:
                logger.warning("CWMW 格式通常只处理单个文件，但收到了多个文件，将尝试只处理第一个。")
            reader = CWReader(args.data_files[0], is_multi_wafer=True)
        elif args.format == "MEX":
            reader = MEXReader(args.data_files)
        elif args.format == "DCP": # 取消注释 DCP 分支
            reader = DCPReader(args.data_files)
        else:
            raise ValueError(f"不支持的数据格式: {args.format}")

        if reader:
            logger.info(f"开始使用 {args.format} 读取器读取数据...")
            cp_lot = reader.read()
            if cp_lot is None or not hasattr(cp_lot, 'wafers') or not cp_lot.wafers: # 更健壮的检查
                logger.error("数据读取失败或未找到任何 Wafer 数据。程序终止。")
                return # 退出程序
            logger.info(f"数据读取完成。Lot ID: {getattr(cp_lot, 'lot_id', 'N/A')}, 产品: {getattr(cp_lot, 'product', 'N/A')}, Wafer 数量: {getattr(cp_lot, 'wafer_count', 0)}")

            # 合并数据（核心步骤）
            if hasattr(cp_lot, 'combine_data_from_wafers'):
                logger.info("合并所有 Wafer 数据到 combined_data...")
                cp_lot.combine_data_from_wafers()
                logger.info("数据合并完成。")
            else:
                 logger.error("CPLot 对象缺少 combine_data_from_wafers 方法，无法合并数据。")
                 return # 无法继续

    except Exception as e:
        logger.error(f"读取或处理输入文件时发生严重错误: {e}", exc_info=True)
        return

    # --- 2. (占位) 添加计算数据 ---
    if config.get('add_calculated_data'):
        logger.info("(占位) 需要添加计算数据 (逻辑待实现)...")
        # try:
        #     add_calculated_data(cp_lot) # 需要实现此函数
        # except Exception as e:
        #     logger.error(f"添加计算数据时出错: {e}", exc_info=True)

    # --- 3. 导出核心 Excel 数据表 ---
    # 检查 cp_lot 是否有效
    if cp_lot is None:
        logger.error("无法继续处理，因为 cp_lot 对象无效。")
        return
        
    base_excel_filename = f"{getattr(cp_lot, 'lot_id', 'output')}_analysis.xlsx"
    base_excel_path = output_dir / base_excel_filename

    # 调用实际的 Excel 导出函数
    try:
        logger.info(f"准备导出核心数据到 Excel: {base_excel_path}") # 将日志移到 try 块内
        export_analysis_to_excel(
            cp_lot,
            str(base_excel_path), # 确保路径是字符串
            export_spec=config.get('excel_export', {}).get('spec', True), # 使用 get 防御
            export_data=config.get('excel_export', {}).get('data', True),
            export_yield=config.get('excel_export', {}).get('yield', True),
            export_summary=config.get('excel_export', {}).get('summary', True),
            summary_options=config.get('summary_options', {}) # 使用 get 防御
        )
    except Exception as e:
        logger.error(f"导出核心 Excel 数据时出错: {e}", exc_info=True)


    # --- 4. 生成图表 ---
    # 4.1 Wafer Map
    if config.get('plot_bin_map'):
        map_output_path = output_dir / f"{getattr(cp_lot, 'lot_id', 'output')}_WaferMaps.xlsx"
        logger.info(f"准备生成 Bin Map 到: {map_output_path}")
        try:
            plot_all_wafers_to_excel(
                cp_lot,
                str(map_output_path),
                value_col='bin',
                **config.get('wafer_map_options', {})
            )
        except Exception as e:
            logger.error(f"生成 Wafer Map 时出错: {e}", exc_info=True)

    # 4.2 Box Plot
    box_plot_params = config.get('box_plot_params')
    if config.get('plot_box_plot') and box_plot_params:
        logger.info(f"准备为参数 {box_plot_params} 生成箱线图...")
        for param_id in box_plot_params:
            boxplot_output_path = output_dir / f"{getattr(cp_lot, 'lot_id', 'output')}_BoxPlot_{param_id}.xlsx"
            logger.info(f"  生成参数 '{param_id}' 的箱线图到: {boxplot_output_path}")
            try:
                plot_parameter_boxplots_to_excel(
                    cp_lot,
                    param_id,
                    str(boxplot_output_path),
                    **config.get('boxplot_options', {})
                )
            except Exception as e:
                 logger.error(f"为参数 '{param_id}' 生成箱线图时出错: {e}", exc_info=True)

    # 4.3 Scatter Plot
    scatter_configs = config.get('scatter_plot_configs')
    if config.get('plot_scatter_plot') and scatter_configs:
        logger.info(f"准备为配置 {scatter_configs} 生成散点图...")
        scatter_output_path = output_dir / f"{getattr(cp_lot, 'lot_id', 'output')}_ScatterPlots.xlsx"
        logger.info(f"  生成散点图到: {scatter_output_path}")
        try:
            # 确保导入的函数是正确的
            plot_scatter_charts_to_excel(
                cp_lot,
                scatter_configs, # 传递配置列表
                str(scatter_output_path),
                **config.get('scatter_plot_options', {}) # 传递选项
            )
        except NameError:
             logger.error("plot_scatter_charts_to_excel 函数未定义或未正确导入。请检查 plotting.scatter_plot 模块。")
        except Exception as e:
            logger.error(f"生成散点图时出错: {e}", exc_info=True)

    # 4.4 (占位) Parameter Color Map
    param_color_map_params = config.get('param_color_map_params')
    if config.get('plot_param_color_map') and param_color_map_params:
         logger.info("(占位) 准备生成参数颜色图...")
         # ... 实现逻辑 ...

    # --- 5. (占位) 生成 PPT 报告 ---
    if config.get('generate_ppt'):
        ppt_output_path = output_dir / f"{getattr(cp_lot, 'lot_id', 'output')}_Report.pptx"
        logger.info(f"(占位) 准备生成 PPT 报告到: {ppt_output_path}")
        # try:
        #     create_ppt_report(
        #         cp_lot,
        #         str(ppt_output_path),
        #         # 传递需要的图表文件路径或对象
        #         # ... 其他选项 ...
        #     )
        # except Exception as e:
        #     logger.error(f"生成 PPT 报告时出错: {e}", exc_info=True)

    # --- 完成 ---
    end_time = time.time()
    duration = end_time - start_time
    logger.info("=== CP 数据处理完成 ===")
    logger.info(f"总耗时: {duration:.2f} 秒")
    logger.info(f"输出文件已保存到: {output_dir.resolve()}")

if __name__ == "__main__":
    main() 