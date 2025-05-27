#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
备份不需要的文件
将测试输出目录和临时文件重命名为.bak结尾
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


def backup_directories():
    """备份测试输出目录"""
    backup_dirs = [
        "test_charts",
        "test_charts_output", 
        "test_output_clean_csv",
        "test_dcp_data",
        "demo_output",
        "__pycache__"
    ]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for dir_name in backup_dirs:
        if os.path.exists(dir_name):
            backup_name = f"{dir_name}_{timestamp}.bak"
            print(f"📦 备份目录: {dir_name} -> {backup_name}")
            shutil.move(dir_name, backup_name)
        else:
            print(f"⚠️ 目录不存在: {dir_name}")


def backup_log_files():
    """备份日志文件"""
    log_files = [
        "dcp_process_20250527_142900.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            backup_name = f"{log_file}.bak"
            print(f"📄 备份日志: {log_file} -> {backup_name}")
            shutil.move(log_file, backup_name)
        else:
            print(f"⚠️ 日志文件不存在: {log_file}")


def backup_old_modules():
    """备份旧的模块目录"""
    old_modules = [
        "python_cp",
        "cp_data_processor"
    ]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for module_dir in old_modules:
        if os.path.exists(module_dir):
            backup_name = f"{module_dir}_{timestamp}.bak"
            print(f"📁 备份模块: {module_dir} -> {backup_name}")
            shutil.move(module_dir, backup_name)
        else:
            print(f"⚠️ 模块目录不存在: {module_dir}")


def main():
    """主函数"""
    print("🧹 开始备份不需要的文件和目录...")
    print("=" * 50)
    
    # 备份测试输出目录
    print("\n📦 备份测试输出目录...")
    backup_directories()
    
    # 备份日志文件
    print("\n📄 备份日志文件...")
    backup_log_files()
    
    # 备份旧模块
    print("\n📁 备份旧模块目录...")
    backup_old_modules()
    
    print("\n✅ 备份完成！")
    print("💡 提示: .bak文件可以在需要时恢复")


if __name__ == "__main__":
    main()
