#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
兼容入口：原 Yield 分析前端已升级为 CP 数据分析 Cockpit。

保留此文件名，避免已有启动命令失效：
    streamlit run frontend/yield_analyzer_app.py
"""

from frontend.cp_dashboard_app import main


if __name__ == "__main__":
    main()
