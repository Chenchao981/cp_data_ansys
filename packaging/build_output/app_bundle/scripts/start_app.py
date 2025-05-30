#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据分析工具启动器
"""

import os
import sys
import subprocess
import tempfile
import tarfile
from pathlib import Path

def main():
    """主启动函数"""
    print("🔬 CP数据分析工具启动器")
    print("=" * 40)
    
    # 获取路径
    script_dir = Path(__file__).parent
    app_dir = script_dir.parent
    env_dir = app_dir / "python_env"
    app_code_dir = app_dir / "app"
    
    # 检查并初始化环境
    if not (env_dir / "python.exe").exists():
        print("📦 首次运行，初始化Python环境...")
        initialize_environment(env_dir)
    
    # 设置环境变量
    env_path = str(env_dir)
    env_scripts = str(env_dir / "Scripts")
    
    new_env = os.environ.copy()
    new_env["PATH"] = f"{env_path};{env_scripts};" + new_env.get("PATH", "")
    new_env["PYTHONPATH"] = str(app_code_dir) + ";" + new_env.get("PYTHONPATH", "")
    
    # 启动应用程序
    print("🚀 启动CP数据分析工具...")
    python_exe = env_dir / "python.exe"
    app_script = app_code_dir / "chart_generator.py"
    
    try:
        result = subprocess.run([
            str(python_exe), str(app_script)
        ], env=new_env, cwd=str(app_code_dir))
        
        if result.returncode == 0:
            print("✅ 应用程序运行完成")
        else:
            print(f"❌ 应用程序退出，代码: {result.returncode}")
            
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1
    
    return 0

def initialize_environment(env_dir):
    """初始化Python环境"""
    env_archive = env_dir / "environment.tar.gz"
    
    if not env_archive.exists():
        print("❌ 未找到环境包文件")
        return False
    
    print("🔄 正在解压Python环境...")
    try:
        with tarfile.open(env_archive, 'r:gz') as tar:
            tar.extractall(path=env_dir)
        
        # 运行conda-unpack
        conda_unpack = env_dir / "Scripts" / "conda-unpack.exe"
        if conda_unpack.exists():
            subprocess.run([str(conda_unpack)], cwd=str(env_dir), check=True)
        
        print("✅ Python环境初始化完成")
        return True
        
    except Exception as e:
        print(f"❌ 环境初始化失败: {e}")
        return False

if __name__ == "__main__":
    sys.exit(main())
