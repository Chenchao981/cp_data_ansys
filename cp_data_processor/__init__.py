"""
CP数据处理器 - 用于处理CP测试数据的Python工具包
"""

import sys

# 导出主要模块
from .readers import create_reader, BaseReader, CWReader, DCPReader, MEXReader
from .data_models import CPLot, CPWafer, CPParameter
from .analysis import StatsAnalyzer, YieldAnalyzer, CapabilityAnalyzer
from .plotting import BoxPlotter, WaferMapPlotter, ScatterPlotter
from .exporters import ExcelExporter
from .processing import DataTransformer

# 导出应用程序入口点
from .app import CPDataProcessorApp

__version__ = '0.1.0'

def run_gui():
    """
    启动图形用户界面应用程序
    """
    # 延迟导入tk，避免在不需要GUI时导入
    import tkinter as tk
    from .app import main as app_main
    app_main()

def run_cli():
    """
    启动命令行应用程序
    """
    from .cli import main as cli_main
    sys.exit(cli_main()) 