import os
import sys
import argparse
import pandas as pd

from .readers import create_reader
from .analysis import StatsAnalyzer, YieldAnalyzer, CapabilityAnalyzer
from .plotting import BoxPlotter, WaferMapPlotter, ScatterPlotter
from .exporters import ExcelExporter
from .processing import DataTransformer


def main():
    """命令行应用入口点"""
    parser = argparse.ArgumentParser(description="CP数据处理器命令行工具")
    
    # 必须参数
    parser.add_argument("input_file", help="输入文件路径")
    parser.add_argument("output_file", help="输出文件路径")
    
    # 可选参数
    parser.add_argument("--format", "-f", choices=["dcp", "cw", "mex"], default="dcp",
                        help="输入文件格式 (默认: dcp)")
    parser.add_argument("--wafer-type", "-w", choices=["normal", "mpw"], default="normal",
                        help="圆片类型 (默认: normal)")
    
    # 图表选项
    parser.add_argument("--boxplot", action="store_true", help="生成箱形图")
    parser.add_argument("--fact-info", action="store_true", help="包含Fact信息")
    parser.add_argument("--scatter", action="store_true", help="生成散点图")
    parser.add_argument("--bin-map", action="store_true", help="生成晶圆Bin图")
    parser.add_argument("--data-map", action="store_true", help="生成数据颜色图")
    parser.add_argument("--add-calc", action="store_true", help="添加计算数据")
    
    # 解析参数
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input_file):
        print(f"错误: 输入文件不存在 - {args.input_file}")
        return 1
    
    try:
        print(f"读取文件: {args.input_file}")
        print(f"使用格式: {args.format}")
        
        # 创建读取器
        reader = create_reader(args.format)
        data = reader.read(args.input_file)
        
        if isinstance(data, pd.DataFrame):
            print(f"成功读取数据: {len(data)} 行, {len(data.columns)} 列")
        else:
            print(f"成功读取数据")
        
        # 数据转换
        if args.add_calc:
            print("添加计算数据...")
            transformer = DataTransformer(data)
            # 这里可以添加一些计算参数的代码
            data = transformer.data
        
        # 创建导出器
        exporter = ExcelExporter()
        
        # 添加原始数据
        exporter.add_dataframe(data, "原始数据")
        
        # 进行统计分析
        print("执行统计分析...")
        stats_analyzer = StatsAnalyzer(data, by_wafer=True)
        stats_results = stats_analyzer.analyze()
        
        # 添加统计分析结果
        summary_df = stats_analyzer.get_summary(format='dataframe')
        exporter.add_dataframe(summary_df, "统计分析")
        
        # 进行良率分析
        print("执行良率分析...")
        yield_analyzer = YieldAnalyzer(data)
        yield_results = yield_analyzer.analyze()
        
        # 添加良率分析结果
        if yield_results['wafer_yields']:
            wafer_yield_df = pd.DataFrame({
                '晶圆': list(yield_results['wafer_yields'].keys()),
                '良率(%)': [round(y, 2) for y in yield_results['wafer_yields'].values()]
            })
            exporter.add_dataframe(wafer_yield_df, "良率分析")
        
        print(f"总良率: {yield_results['total_yield']:.2f}%")
        
        # 生成图表
        if args.boxplot:
            print("生成箱形图...")
            box_plotter = BoxPlotter(data)
            fig_box = box_plotter.plot().fig
            exporter.add_figure(fig_box, "箱形图")
        
        if args.bin_map and 'X' in data.columns and 'Y' in data.columns:
            print("生成晶圆Bin图...")
            wafer_plotter = WaferMapPlotter(data)
            fig_bin = wafer_plotter.plot().fig
            exporter.add_figure(fig_bin, "晶圆Bin图")
        
        if args.data_map and 'X' in data.columns and 'Y' in data.columns:
            print("生成数据颜色图...")
            # 选择第一个参数生成颜色图
            exclude_cols = ['Wafer', 'Seq', 'Bin', 'X', 'Y']
            params = [col for col in data.columns if col not in exclude_cols]
            if params:
                wafer_plotter = WaferMapPlotter(data)
                fig_param = wafer_plotter.plot(parameter=params[0]).fig
                exporter.add_figure(fig_param, f"参数{params[0]}图")
        
        if args.scatter:
            print("生成散点图...")
            # 选择前两个参数生成散点图
            exclude_cols = ['Wafer', 'Seq', 'Bin', 'X', 'Y']
            params = [col for col in data.columns if col not in exclude_cols]
            if len(params) >= 2:
                scatter_plotter = ScatterPlotter(data)
                fig_scatter = scatter_plotter.plot(x_param=params[0], y_param=params[1]).fig
                exporter.add_figure(fig_scatter, f"{params[0]} vs {params[1]}")
        
        # 保存结果
        print(f"保存结果到: {args.output_file}")
        success = exporter.save(args.output_file)
        
        if success:
            print("处理完成")
            return 0
        else:
            print("保存结果失败")
            return 1
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 