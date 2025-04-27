#!/usr/bin/env python
"""
CP数据处理器命令行界面启动脚本
"""

import sys
import os

# 确保可以导入cp_data_processor包
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 启动CLI
if __name__ == "__main__":
    from cp_data_processor.cli import main
    sys.exit(main()) 