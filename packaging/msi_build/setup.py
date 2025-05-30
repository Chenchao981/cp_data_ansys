#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据分析工具 - MSI安装包配置
"""

import sys
from cx_Freeze import setup, Executable
from pathlib import Path

# 构建选项
build_exe_options = {
    # 包含的包
    "packages": [
        "pandas", "numpy", "plotly", "matplotlib", "seaborn", 
        "openpyxl", "pathlib2", "datetime", "json", "csv",
        "tkinter", "threading", "webbrowser", "urllib",
        "encodings", "encodings.utf_8", "encodings.gbk"
    ],
    
    # 包含的模块
    "includes": [
        "pandas.plotting._matplotlib",
        "matplotlib.backends.backend_tkagg",
        "plotly.graph_objects",
        "plotly.express",
        "plotly.io",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.ttk"
    ],
    
    # 排除的模块（减小体积）
    "excludes": [
        "test", "unittest", "email", "html", "http", "urllib3",
        "xml", "pydoc", "doctest", "argparse", "sqlite3",
        "tkinter.test", "matplotlib.tests", "pandas.tests"
    ],
    
    # 包含的文件
    "include_files": [
        # 应用程序文件
        (r"D:\cp_data_ansys\frontend", "frontend"),
        (r"D:\cp_data_ansys\cp_data_processor", "cp_data_processor"),
        (r"D:\cp_data_ansys\output", "output"),
        (r"D:\cp_data_ansys\demo_output", "demo_output"),
        
        # 文档文件
        (r"D:\cp_data_ansys\README.md", "README.md"),
        
        # 示例数据（如果存在）
        # (r"example_data", "example_data"),
    ],
    
    # 优化选项
    "optimize": 2,
}

# MSI构建选项
bdist_msi_options = {
    "upgrade_code": "{12345678-1234-5678-9ABC-123456789012}",  # 固定的升级代码
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\CP数据分析工具",
}

# 可执行文件配置
executables = [
    Executable(
        script=r"D:\cp_data_ansys\chart_generator.py",
        base="Win32GUI" if sys.platform == "win32" else None,  # Windows GUI应用
        target_name="CP数据分析工具.exe",
        copyright="© 2024 半导体数据分析团队",
    )
]

# 设置配置
setup(
    name="CP数据分析工具",
    version="1.0.0",
    description="专业的半导体测试数据分析工具",
    author="半导体数据分析团队",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options
    },
    executables=executables
)
