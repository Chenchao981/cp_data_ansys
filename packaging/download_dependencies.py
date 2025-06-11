#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载依赖包到本地的脚本
用于创建离线安装包
"""

import os
import subprocess
import sys
from pathlib import Path

def download_dependencies():
    """下载requirements.txt中的所有依赖到本地wheels文件夹"""
    
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent
    dist_dir = current_dir / "dist"
    wheels_dir = dist_dir / "wheels"
    requirements_file = dist_dir / "requirements.txt"
    
    # 创建wheels目录
    wheels_dir.mkdir(exist_ok=True)
    
    print("🚀 开始下载依赖包...")
    print(f"📁 下载目录: {wheels_dir}")
    print(f"📄 依赖文件: {requirements_file}")
    
    if not requirements_file.exists():
        print(f"❌ 错误: 找不到 {requirements_file}")
        return False
    
    try:
        # 使用pip download命令下载依赖
        cmd = [
            sys.executable, "-m", "pip", "download",
            "-r", str(requirements_file),
            "-d", str(wheels_dir)
            # 下载完整的依赖树，确保离线安装时不缺少依赖
        ]
        
        print(f"🔄 执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ 依赖包下载成功!")
            
            # 列出下载的文件
            downloaded_files = list(wheels_dir.glob("*"))
            print(f"📦 共下载 {len(downloaded_files)} 个文件:")
            for file in downloaded_files:
                print(f"   - {file.name}")
                
            return True
        else:
            print("❌ 下载失败:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 下载过程中出现错误: {e}")
        return False

def create_offline_install_script():
    """创建离线安装脚本"""
    
    current_dir = Path(__file__).parent
    dist_dir = current_dir / "dist"
    
    # 创建离线安装的批处理文件
    install_offline_bat = dist_dir / "install_offline.bat"
    
    bat_content = """@echo off
chcp 65001 >nul
echo 🚀 开始离线安装依赖包...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python，请先安装Python并添加到PATH
    pause
    exit /b 1
)

REM 检查wheels文件夹是否存在
if not exist "wheels" (
    echo ❌ 错误: 找不到wheels文件夹，请先运行下载脚本
    pause
    exit /b 1
)

echo 📦 从本地安装依赖包...
python -m pip install --find-links wheels --no-index --requirement requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo ✅ 依赖安装成功！
    echo 🎉 现在可以双击 start.bat 启动程序了
) else (
    echo.
    echo ❌ 安装失败，请检查错误信息
)

echo.
pause
"""
    
    with open(install_offline_bat, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    print(f"✅ 创建离线安装脚本: {install_offline_bat}")

if __name__ == "__main__":
    print("=" * 50)
    print("CP数据分析工具 - 依赖包下载器")
    print("=" * 50)
    
    # 下载依赖包
    if download_dependencies():
        # 创建离线安装脚本
        create_offline_install_script()
        print("\n🎉 所有操作完成!")
        print("📁 用户现在可以使用 install_offline.bat 进行离线安装")
    else:
        print("\n❌ 下载失败，请检查网络连接和Python环境")
    
    input("\n按回车键退出...") 