#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据分析工具 - 多公司版启动脚本
支持华虹(HH)和捷泰(JT)两家公司的数据处理
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        # 创建QApplication实例
        app = QApplication(sys.argv)
        
        # 设置应用程序属性
        app.setApplicationName("CP数据分析工具 - 多公司版")
        app.setApplicationDisplayName("CP数据分析工具")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("CP Data Analysis Team")
        app.setOrganizationDomain("cp-data-analysis.com")
        
        # 设置高DPI缩放
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # 导入并创建主窗口
        from .multi_company_gui import MultiCompanyCPDataGUI
        
        logger.info("正在启动多公司CP数据分析工具...")
        
        # 创建主窗口
        window = MultiCompanyCPDataGUI()
        
        # 显示窗口
        window.show()
        
        logger.info("多公司CP数据分析工具启动成功")
        logger.info("支持的公司: HuaHong, JeTech")
        
        # 运行应用
        exit_code = app.exec_()
        
        logger.info(f"应用程序退出，退出代码: {exit_code}")
        sys.exit(exit_code)
        
    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        print(f"错误: 无法导入必要的模块 - {e}")
        print("请确保所有依赖项已正确安装")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}")
        print(f"错误: 应用程序启动失败 - {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()