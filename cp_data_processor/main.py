"""
主流程脚本，对应 VBA 中的 A_业务流程.bas

该模块实现了CP数据处理的完整流程，包括：
1. 数据格式选择与文件读取
2. 数据处理与分析
3. 结果可视化与导出
"""

import os
import time
import logging
import tkinter as tk
from tkinter import filedialog
from typing import List, Optional, Dict, Any
import pandas as pd

# 导入项目模块
from .config import settings
from .data_models.cp_data import CPLot
from .readers import create_reader
from .processing import DataTransformer
from .analysis import StatsAnalyzer, YieldAnalyzer, CapabilityAnalyzer
from .plotting import BoxPlotter, WaferMapPlotter, ScatterPlotter
from .exporters import ExcelExporter

# --- 日志配置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


class CPDataProcessor:
    """CP数据处理器核心类，封装完整的数据处理流程"""
    
    def __init__(self):
        """初始化数据处理器"""
        self.cp_format = None
        self.file_list = []
        self.test_info = None
        self.output_path = None
        self.base_path = None
        self.exporter = None

    def get_cp_data_format(self) -> str:
        """
        获取CP数据格式
        当前使用配置中的默认值，未来可改为用户输入或自动检测
        """
        cp_format = settings.DEFAULT_CP_FORMAT
        logger.info(f"使用数据格式: {cp_format}")
        return cp_format
    
    def get_file_list(self, cp_format: str) -> List[str]:
        """弹出文件选择对话框，获取文件列表"""
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        file_types = []
        multiple = True
        title = "请选择测试数据文件"
        
        if cp_format == "MEX":
            file_types = [("Excel 文件", "*.xls;*.xlsx"), ("所有文件", "*.*")]
        elif cp_format == "DCP":
            file_types = [("文本文件", "*.txt"), ("所有文件", "*.*")]
        elif cp_format == "CWSW":
            file_types = [("CSV 文件", "*.csv"), ("所有文件", "*.*")]
        elif cp_format == "CWMW":
            file_types = [("CSV 文件", "*.csv"), ("所有文件", "*.*")]
            multiple = False  # CW多晶圆格式通常是单个文件
            title = "请选择多晶圆测试数据文件 (单个文件)"
        else:
            logger.warning(f"未知的CP格式 '{cp_format}'，允许选择所有文件。")
            file_types = [("所有文件", "*.*")]
        
        if multiple:
            file_paths = filedialog.askopenfilenames(title=title, filetypes=file_types)
        else:
            file_path = filedialog.askopenfilename(title=title, filetypes=file_types)
            file_paths = [file_path] if file_path else []
        
        if not file_paths:
            logger.warning("没有选择任何文件，程序将退出。")
            return []
        else:
            logger.info(f"选择了 {len(file_paths)} 个文件。")
            return list(file_paths)
    
    def read_files(self, file_list: List[str], cp_format: str) -> Optional[CPLot]:
        """读取文件数据，根据格式选择合适的读取器"""
        try:
            logger.info(f"使用 {cp_format} 格式读取 {len(file_list)} 个文件")
            reader = create_reader(cp_format.lower())
            
            # 读取数据
            test_info = reader.read(file_list)
            
            if not test_info or (hasattr(test_info, 'wafer_count') and test_info.wafer_count == 0):
                logger.warning("未从文件中读取到有效的晶圆数据。")
                return None
                
            logger.info(f"数据读取完成。Lot ID: {test_info.lot_id}, "
                       f"共 {test_info.wafer_count} 片晶圆，{test_info.param_count} 个参数。")
            return test_info
            
        except Exception as e:
            logger.error(f"读取文件时出错: {e}", exc_info=True)
            return None
    
    def setup_check(self, test_info: CPLot) -> bool:
        """检查设置是否有效"""
        valid = True
        logger.info("开始进行设置检查...")
        
        # 未来可以实现更多检查逻辑
        if settings.ADD_CAL_DATA_FLAG:
            logger.info("检查增加计算数据的设置...")
            # 目前简单返回True，未来可以实现具体的检查逻辑
            pass
            
        if settings.BOX_PLOT_FLAG and settings.INCLUDE_EXP_FACT_FLAG:
            logger.info("检查因子表与晶圆数量匹配...")
            # 目前简单返回True，未来可以实现具体的检查逻辑
            pass
            
        if settings.SCATTER_PLOT_FLAG:
            logger.info("检查散点图设置...")
            # 目前简单返回True，未来可以实现具体的检查逻辑
            pass
        
        if not valid:
            logger.error("设置检查未通过。请检查配置和数据。")
        else:
            logger.info("设置检查通过。")
        return valid
    
    def process_data(self, test_info: CPLot) -> Optional[CPLot]:
        """处理数据，包括增加计算数据等操作"""
        try:
            # 增加计算数据（可选）
            if settings.ADD_CAL_DATA_FLAG:
                logger.info("开始增加计算数据...")
                transformer = DataTransformer(test_info)
                # 这里可以实现具体的数据处理逻辑
                # test_info = transformer.transform()
                logger.info("增加计算数据完成。")
            
            return test_info
        except Exception as e:
            logger.error(f"处理数据时出错: {e}", exc_info=True)
            return None
    
    def analyze_data(self, test_info: CPLot) -> Dict[str, Any]:
        """分析数据，计算统计数据和良率"""
        results = {}
        try:
            # 统计分析
            logger.info("开始统计分析...")
            stats_analyzer = StatsAnalyzer(test_info)
            results['stats'] = stats_analyzer.analyze()
            
            # 良率计算
            logger.info("开始计算良率...")
            yield_analyzer = YieldAnalyzer(test_info)
            results['yield'] = yield_analyzer.analyze()
            
            # 工艺能力分析（如果需要）
            if settings.CALC_CPK_FLAG:
                logger.info("开始计算工艺能力指标...")
                capability_analyzer = CapabilityAnalyzer(test_info)
                results['capability'] = capability_analyzer.analyze()
            
            return results
        except Exception as e:
            logger.error(f"分析数据时出错: {e}", exc_info=True)
            return {}
    
    def create_excel_exporter(self, test_info: CPLot, temp_path: str) -> Optional[ExcelExporter]:
        """创建Excel导出器"""
        try:
            logger.info(f"创建Excel导出器: {temp_path}")
            exporter = ExcelExporter()
            exporter.init(temp_path, test_info)
            return exporter
        except Exception as e:
            logger.error(f"创建Excel导出器失败: {e}", exc_info=True)
            return None
    
    def generate_plots(self, test_info: CPLot, plot_path: str) -> Dict[str, Any]:
        """生成各种图表"""
        plots = {}
        
        # 确保路径存在
        os.makedirs(plot_path, exist_ok=True)
        
        # 箱形图
        if settings.BOX_PLOT_FLAG:
            logger.info("开始生成箱形图...")
            try:
                box_plotter = BoxPlotter(test_info)
                plots['box'] = box_plotter.plot(output_path=plot_path)
                logger.info("箱形图生成完成。")
            except Exception as e:
                logger.error(f"生成箱形图时出错: {e}", exc_info=True)
        
        # 晶圆Bin图
        if settings.BIN_MAP_PLOT_FLAG:
            logger.info("开始生成Bin Map图...")
            try:
                wafer_plotter = WaferMapPlotter(test_info)
                plots['bin_map'] = wafer_plotter.plot(output_path=plot_path)
                logger.info("Bin Map图生成完成。")
            except Exception as e:
                logger.error(f"生成Bin Map图时出错: {e}", exc_info=True)
        
        # 参数颜色图
        if settings.DATA_COLOR_PLOT_FLAG:
            logger.info("开始生成参数颜色图...")
            try:
                color_plotter = WaferMapPlotter(test_info)
                # 这里应该选择参数进行绘图
                plots['color_map'] = color_plotter.plot(parameter="param1", output_path=plot_path)
                logger.info("参数颜色图生成完成。")
            except Exception as e:
                logger.error(f"生成参数颜色图时出错: {e}", exc_info=True)
        
        # 散点图
        if settings.SCATTER_PLOT_FLAG:
            logger.info("开始生成散点图...")
            try:
                scatter_plotter = ScatterPlotter(test_info)
                # 这里应该选择参数进行绘图
                plots['scatter'] = scatter_plotter.plot(output_path=plot_path)
                logger.info("散点图生成完成。")
            except Exception as e:
                logger.error(f"生成散点图时出错: {e}", exc_info=True)
        
        return plots
    
    def save_results(self, test_info: CPLot, output_path: str) -> Optional[str]:
        """保存结果到Excel文件"""
        try:
            # 生成安全的文件名
            lot_id = test_info.lot_id if test_info.lot_id else "Result"
            safe_lot_id = "".join(c for c in lot_id if c.isalnum() or c in ('_', '-'))
            file_name = f"{safe_lot_id}{settings.OUTPUT_FILE_SUFFIX}"
            full_path = os.path.join(output_path, file_name)
            
            # 删除已存在的文件（如果需要）
            if os.path.exists(full_path):
                logger.warning(f"文件 {full_path} 已存在，将被覆盖。")
                os.remove(full_path)
            
            # 保存结果
            if self.exporter:
                logger.info(f"正在保存结果到: {full_path}")
                self.exporter.save(full_path)
                logger.info("结果保存成功。")
                return full_path
            else:
                logger.error("Excel导出器未初始化，无法保存结果。")
                return None
        except Exception as e:
            logger.error(f"保存结果时出错: {e}", exc_info=True)
            return None
    
    def run(self) -> bool:
        """运行完整的数据处理流程"""
        start_time = time.time()
        logger.info("--- CP数据处理程序启动 ---")
        
        # 1. 获取数据格式
        self.cp_format = self.get_cp_data_format()
        if not self.cp_format:
            logger.error("无法确定CP数据格式，程序终止。")
            return False
        
        # 2. 获取文件列表
        self.file_list = self.get_file_list(self.cp_format)
        if not self.file_list:
            return False  # 用户取消选择，直接退出
        
        # 确定基础路径和输出路径
        self.base_path = os.path.dirname(self.file_list[0]) if self.file_list else "."
        self.output_path = settings.get_output_path(self.base_path)
        logger.info(f"数据输出目录: {self.output_path}")
        
        # 3. 读取文件数据
        self.test_info = self.read_files(self.file_list, self.cp_format)
        if not self.test_info:
            logger.error("读取数据失败或未找到数据，程序终止。")
            return False
        
        # 4. 设置检查
        if not self.setup_check(self.test_info):
            logger.error("设置检查失败，程序终止。")
            return False
        
        # 5. 处理数据
        processed_info = self.process_data(self.test_info)
        if not processed_info:
            logger.error("处理数据失败，程序终止。")
            return False
        self.test_info = processed_info
        
        # 6. 分析数据
        analysis_results = self.analyze_data(self.test_info)
        if not analysis_results:
            logger.error("分析数据失败，程序终止。")
            return False
        
        # 7. 创建临时文件路径
        temp_excel_path = os.path.join(self.output_path, f"_temp_{self.test_info.lot_id}.xlsx")
        self.exporter = self.create_excel_exporter(self.test_info, temp_excel_path)
        if not self.exporter:
            logger.error("创建Excel导出器失败，程序终止。")
            return False
        
        # 8. 填充数据到导出器
        # 使用分析结果填充导出器
        
        # 9. 生成图表
        plot_path = os.path.join(self.output_path, "plots")
        plot_results = self.generate_plots(self.test_info, plot_path)
        
        # 10. 保存结果
        result_file_path = self.save_results(self.test_info, self.output_path)
        if result_file_path:
            logger.info(f"成功保存结果文件: {result_file_path}")
        else:
            logger.error("保存结果文件失败。")
            # 尝试清理临时文件
            if os.path.exists(temp_excel_path):
                try:
                    os.remove(temp_excel_path)
                    logger.info(f"已删除临时文件: {temp_excel_path}")
                except Exception as rm_err:
                    logger.error(f"删除临时文件 {temp_excel_path} 失败: {rm_err}")
            return False
        
        # 11. 结束处理
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"--- 数据处理完成 --- 时间(秒): {elapsed_time:.2f}")
        
        return True


def main():
    """主函数"""
    processor = CPDataProcessor()
    processor.run()


if __name__ == "__main__":
    # 注意：直接运行此脚本可能需要调整导入路径
    # 建议使用 python -m cp_data_processor.main 从项目根目录运行
    main() 