#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
兼容入口：原 Yield 分析前端已升级为 CP 数据分析 Cockpit。

保留此文件名，避免已有启动命令失效：
    streamlit run frontend/yield_analyzer_app.py
"""

import sys
from pathlib import Path


# 发布版由磁盘上的本入口启动，但完整 frontend 包位于 app.pyz。
# 必须在导入 frontend 前把 app.pyz 放到搜索路径首位，否则 release/frontend
# 这个不完整的启动目录会遮蔽压缩包内的 frontend/charts。
release_root = Path(__file__).resolve().parents[1]
packaged_app = release_root / "app.pyz"
if packaged_app.is_file():
    packaged_app_path = str(packaged_app)
    if packaged_app_path in sys.path:
        sys.path.remove(packaged_app_path)
    sys.path.insert(0, packaged_app_path)

from frontend.cp_dashboard_app import main


if __name__ == "__main__":
    main()
