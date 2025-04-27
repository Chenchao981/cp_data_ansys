#!/usr/bin/env python
"""
CP数据处理器图形界面启动脚本
"""

import sys
import os

# 确保可以导入cp_data_processor包
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 启动GUI
if __name__ == "__main__":
    import tkinter as tk
    from cp_data_processor.app import CPDataProcessorApp
    
    root = tk.Tk()
    app = CPDataProcessorApp(root)
    root.mainloop() 