#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据处理器 - 主应用程序
整合所有功能模块，提供统一的数据处理入口
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from readers.reader_factory import ReaderFactory
from analysis.yield_analyzer import YieldAnalyzer
from analysis.stats_analyzer import StatsAnalyzer
from plotting.box_plotter import BoxPlotter
from plotting.scatter_plotter import ScatterPlotter
from plotting.wafer_map_plotter import WaferMapPlotter
from exporters.excel_exporter import ExcelExporter


class CPDataProcessor:
    """CP数据处理器主类"""
    
    def __init__(self):
        self.lot_data = None
        self.yield_analyzer = None
        self.stats_analyzer = None
        
    def process_files(self, file_paths: list, data_format: str, output_path: str, 
                     enable_boxplot: bool = False, enable_scatter: bool = False,
                     enable_wafer_map: bool = False) -> bool:
        """
        处理CP测试数据文件
        
        Args:
            file_paths: 输入文件路径列表
            data_format: 数据格式 (dcp/cw/mex)
            output_path: 输出文件路径
            enable_boxplot: 是否生成箱形图
            enable_scatter: 是否生成散点图
            enable_wafer_map: 是否生成晶圆图
            
        Returns:
            bool: 处理是否成功
        """
        try:
            # 1. 读取数据
            print(f"📖 读取 {data_format.upper()} 格式数据...")
            reader = ReaderFactory.create_reader(data_format, file_paths)
            self.lot_data = reader.read()
            
            if not self.lot_data or not self.lot_data.wafers:
                print("❌ 数据读取失败或数据为空")
                return False
                
            print(f"✅ 成功读取 {self.lot_data.wafer_count} 个晶圆的数据")
            
            # 2. 数据分析
            print("📊 进行数据分析...")
            self.yield_analyzer = YieldAnalyzer(self.lot_data)
            self.stats_analyzer = StatsAnalyzer(self.lot_data)
            
            # 计算良率
            yield_results = self.yield_analyzer.calculate_yield()
            print(f"   总体良率: {yield_results.get('overall_yield', 0):.2f}%")
            
            # 计算统计信息
            stats_results = self.stats_analyzer.calculate_statistics()
            print(f"   参数统计完成，共 {len(stats_results)} 个参数")
            
            # 3. 生成图表
            if enable_boxplot:
                print("📦 生成箱形图...")
                box_plotter = BoxPlotter(self.lot_data)
                box_plotter.create_all_plots(output_dir=Path(output_path).parent / "plots")
                
            if enable_scatter:
                print("🌈 生成散点图...")
                scatter_plotter = ScatterPlotter(self.lot_data)
                scatter_plotter.create_correlation_plots(output_dir=Path(output_path).parent / "plots")
                
            if enable_wafer_map:
                print("🗺️ 生成晶圆图...")
                map_plotter = WaferMapPlotter(self.lot_data)
                map_plotter.create_wafer_maps(output_dir=Path(output_path).parent / "plots")
            
            # 4. 导出结果
            print("💾 导出分析结果...")
            exporter = ExcelExporter(self.lot_data)
            exporter.export_to_excel(output_path)
            
            print(f"✅ 处理完成！结果已保存到: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CP数据处理器")
    parser.add_argument("input_files", nargs="+", help="输入文件路径")
    parser.add_argument("output_file", help="输出Excel文件路径")
    parser.add_argument("--format", choices=["dcp", "cw", "mex"], 
                       default="dcp", help="数据格式")
    parser.add_argument("--boxplot", action="store_true", help="生成箱形图")
    parser.add_argument("--scatter", action="store_true", help="生成散点图")
    parser.add_argument("--wafer-map", action="store_true", help="生成晶圆图")
    
    args = parser.parse_args()
    
    # 创建处理器并执行
    processor = CPDataProcessor()
    success = processor.process_files(
        file_paths=args.input_files,
        data_format=args.format,
        output_path=args.output_file,
        enable_boxplot=args.boxplot,
        enable_scatter=args.scatter,
        enable_wafer_map=args.wafer_map
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
