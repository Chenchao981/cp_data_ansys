"""
主处理器模块，提供一个高性能、统一的入口来处理和分析CP数据。
"""
import asyncio
import time
import os
from typing import List, Dict

from cp_data_processor.data_models.cp_data import CPLot
from cp_data_processor.processing.numba_accelerators import batch_process_parameters
from cp_data_processor.plotting.scatter_plotter import ScatterPlotter
from cp_data_processor.plotting.box_plotter import BoxPlotter
from cp_data_processor.plotting.wafer_map_plotter import WaferMapPlotter

def process_statistics_efficiently(cp_lot: CPLot) -> Dict:
    """
    使用Numba批量、高效地计算所有数值参数的统计数据，并更新CPLot对象。

    Args:
        cp_lot: 包含合并数据的CPLot对象。

    Returns:
        一个包含所有参数统计结果的字典。
    """
    print("🚀 开始使用Numba进行高性能统计计算...")
    start_time = time.time()

    # 1. 确保有合并数据
    if cp_lot.combined_data is None or cp_lot.combined_data.empty:
        print("合并晶圆数据...")
        cp_lot.combine_data_from_wafers()
        if cp_lot.combined_data is None or cp_lot.combined_data.empty:
            print("错误：没有可用的数据进行处理。")
            return {}

    # 2. 获取所有数值型参数的列名
    numeric_params = cp_lot.get_numeric_param_names()
    if not numeric_params:
        print("错误：在数据中未找到任何数值型参数。")
        return {}
    
    # 3. 调用批量处理函数
    results = batch_process_parameters(cp_lot.combined_data, numeric_params)
    statistics = results.get('statistics', {})

    # 4. 将计算结果更新回CPLot对象
    for param_id, stats in statistics.items():
        param_obj = cp_lot.get_parameter_by_id(param_id)
        if param_obj:
            param_obj.mean = stats.get('mean')
            param_obj.std_dev = stats.get('std')
            param_obj.median = stats.get('median')
            param_obj.min_val = stats.get('min')
            param_obj.max_val = stats.get('max')
    
    end_time = time.time()
    print(f"✅ 统计计算完成，耗时: {end_time - start_time:.4f} 秒")
    
    return statistics

async def generate_plots_parallel(cp_lot: CPLot, output_dir: str, plot_types: List[str] = None):
    """
    使用asyncio并行生成多种类型的图表。
    此版本经过优化，可以正确、高效地调用绘图器。

    Args:
        cp_lot: 包含数据的CPLot对象。
        output_dir: 图表输出目录。
        plot_types: 要生成的图表类型列表, e.g., ['scatter', 'box', 'wafer_map']。
                    如果为None，则生成所有类型的图表。
    """
    if plot_types is None:
        plot_types = ['scatter', 'box', 'wafer_map']

    print(f"🚀 开始并行生成图表 ({', '.join(plot_types)})...")
    start_time = time.time()
    
    tasks = []
    numeric_params = cp_lot.get_numeric_param_names()
    if not numeric_params:
        print("警告: 未找到可用于绘图的数值型参数。")
        return

    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 箱线图任务 (一个图包含所有参数)
    if 'box' in plot_types:
        try:
            print("  - 创建箱线图任务...")
            box_plotter = BoxPlotter(data=cp_lot.combined_data)
            box_plotter.plot(parameters=numeric_params, by_wafer=True)
            path = os.path.join(output_dir, "summary_boxplot_by_wafer.png")
            tasks.append(box_plotter.save_figure_async(path))
        except Exception as e:
            print(f"  - 创建箱线图失败: {e}")

    # 2. 散点图矩阵任务 (一个图包含多个参数)
    if 'scatter' in plot_types and len(numeric_params) > 1:
        try:
            print("  - 创建散点图矩阵任务...")
            scatter_plotter = ScatterPlotter(data=cp_lot.combined_data)
            # 限制最多显示5个参数的矩阵，避免过于拥挤
            params_for_matrix = numeric_params[:min(len(numeric_params), 5)]
            scatter_plotter.plot_matrix(parameters=params_for_matrix)
            path = os.path.join(output_dir, "summary_scatter_matrix.png")
            tasks.append(scatter_plotter.save_figure_async(path))
        except Exception as e:
            print(f"  - 创建散点图矩阵失败: {e}")

    # 3. 晶圆图任务 (每个参数一个图，图中可包含多个晶圆)
    if 'wafer_map' in plot_types:
        print(f"  - 为 {len(numeric_params)} 个参数创建晶圆图任务...")
        for param in numeric_params:
            try:
                wafer_plotter = WaferMapPlotter(data=cp_lot.combined_data)
                # 默认绘制最多9个晶圆
                wafer_plotter.plot_multi_wafers(parameter=param)
                path = os.path.join(output_dir, f"wafer_map_{param}.png")
                tasks.append(wafer_plotter.save_figure_async(path))
            except Exception as e:
                print(f"  - 创建晶圆图 '{param}' 失败: {e}")

    # 并行执行所有任务
    if tasks:
        print(f"⏳ 正在并发执行 {len(tasks)} 个绘图任务...")
        await asyncio.gather(*tasks)
    
    end_time = time.time()
    print(f"✅ 所有图表生成完成，耗时: {end_time - start_time:.4f} 秒")

def run_full_analysis_pipeline(cp_lot: CPLot, output_dir: str):
    """
    运行完整的高性能分析流程：计算统计数据 + 并行生成图表。

    Args:
        cp_lot: CPLot对象。
        output_dir: 输出目录。
    """
    # 第一步：高效计算统计数据
    process_statistics_efficiently(cp_lot)

    # 第二步：并行生成图表
    # 注意：在一个非async函数中调用async函数，需要使用asyncio.run()
    asyncio.run(generate_plots_parallel(cp_lot, output_dir)) 