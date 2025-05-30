#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据分析工具 - 演示构建脚本
创建一个简化版本用于测试打包流程
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from datetime import datetime

class DemoBuilder:
    """演示构建器 - 简化版测试"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.demo_dir = self.project_root / "demo_build"
        self.app_name = "CP数据分析工具_演示版"
        self.version = "1.0.0-demo"
        
        # 创建演示目录
        self.demo_dir.mkdir(exist_ok=True)
        
        print(f"🎯 演示构建器初始化")
        print(f"📁 项目根目录: {self.project_root}")
        print(f"📁 演示构建目录: {self.demo_dir}")
    
    def create_demo_environment(self):
        """创建演示环境（使用当前环境的子集）"""
        print("\n🔄 创建演示环境...")
        
        # 创建基本的目录结构
        demo_app_dir = self.demo_dir / "demo_app"
        if demo_app_dir.exists():
            shutil.rmtree(demo_app_dir)
        demo_app_dir.mkdir()
        
        # 1. 复制核心应用文件
        print("📋 复制应用程序文件...")
        app_files = [
            "chart_generator.py",
            "README.md",
        ]
        
        for file_name in app_files:
            src_file = self.project_root / file_name
            if src_file.exists():
                shutil.copy2(src_file, demo_app_dir)
                print(f"  ✅ {file_name}")
            else:
                print(f"  ⚠️ {file_name} 未找到")
        
        # 2. 复制关键目录（简化版）
        app_dirs = ["frontend"]  # 只复制最重要的
        
        for dir_name in app_dirs:
            src_dir = self.project_root / dir_name
            if src_dir.exists():
                shutil.copytree(src_dir, demo_app_dir / dir_name,
                              ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                print(f"  ✅ {dir_name}/")
            else:
                print(f"  ⚠️ {dir_name}/ 未找到")
        
        return demo_app_dir
    
    def create_simple_launcher(self, app_dir):
        """创建简单的启动脚本"""
        print("\n🚀 创建启动脚本...")
        
        # 创建启动脚本
        launcher_bat = app_dir / "start_demo.bat"
        launcher_content = '''@echo off
chcp 65001 >nul
echo 🔬 CP数据分析工具 - 演示版
echo ========================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python
    echo 💡 请确保已安装Python 3.7+并添加到PATH
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

REM 检查关键依赖
echo 🔍 检查依赖包...
python -c "import pandas, numpy, plotly, matplotlib" 2>nul
if errorlevel 1 (
    echo ❌ 缺少必需的依赖包
    echo 💡 请运行: pip install pandas numpy plotly matplotlib openpyxl
    pause
    exit /b 1
)

echo ✅ 依赖包检查通过
echo.

REM 启动程序
echo 🚀 启动应用程序...
python chart_generator.py

if errorlevel 1 (
    echo.
    echo ❌ 程序运行出错
    pause
) else (
    echo.
    echo ✅ 程序运行完成
    pause
)
'''
        
        with open(launcher_bat, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        
        print(f"✅ 启动脚本已创建: {launcher_bat.name}")
        return launcher_bat
    
    def create_demo_installer(self, app_dir):
        """创建演示安装脚本"""
        print("\n🛠️ 创建安装脚本...")
        
        installer_bat = app_dir / "install_demo.bat"
        installer_content = '''@echo off
chcp 65001 >nul
echo 🛠️ CP数据分析工具演示版 - 安装程序
echo ===================================
echo.

set "INSTALL_DIR=%USERPROFILE%\\Desktop\\CP数据分析工具_演示版"
set "CURRENT_DIR=%~dp0"

echo 📁 安装目录: %INSTALL_DIR%
echo.

REM 创建安装目录
if exist "%INSTALL_DIR%" (
    echo 🔄 清理旧版本...
    rmdir /s /q "%INSTALL_DIR%"
)

mkdir "%INSTALL_DIR%"
if errorlevel 1 (
    echo ❌ 无法创建安装目录
    pause
    exit /b 1
)

REM 复制文件
echo 📋 复制文件...
xcopy "%CURRENT_DIR%*" "%INSTALL_DIR%\\" /E /I /Y /Q
if errorlevel 1 (
    echo ❌ 文件复制失败
    pause
    exit /b 1
)

REM 创建桌面快捷方式
echo 🔗 创建桌面快捷方式...
set "SHORTCUT=%USERPROFILE%\\Desktop\\CP数据分析工具_演示版.lnk"
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\start_demo.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'CP数据分析工具演示版'; $Shortcut.Save()"

echo.
echo ✅ 演示版安装完成！
echo 📍 安装位置: %INSTALL_DIR%
echo 🖥️ 桌面快捷方式: CP数据分析工具_演示版
echo.
echo 💡 提示：请确保已安装Python和相关依赖包
echo    pip install pandas numpy plotly matplotlib openpyxl
pause
'''
        
        with open(installer_bat, 'w', encoding='utf-8') as f:
            f.write(installer_content)
        
        print(f"✅ 安装脚本已创建: {installer_bat.name}")
        return installer_bat
    
    def create_demo_docs(self, app_dir):
        """创建演示文档"""
        print("\n📚 创建文档...")
        
        readme_file = app_dir / "README_演示版.txt"
        readme_content = f'''CP数据分析工具 - 演示版
=========================

版本: {self.version}
构建时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

这是一个简化的演示版本，用于测试打包和部署流程。

系统要求:
- Windows 10/11
- Python 3.7+
- 依赖包: pandas, numpy, plotly, matplotlib, openpyxl

安装步骤:
1. 运行 install_demo.bat 进行安装
2. 双击桌面快捷方式启动

或者直接运行:
- 双击 start_demo.bat

注意事项:
- 演示版需要用户系统已安装Python和依赖包
- 完整版会包含独立的Python环境，无需用户安装

技术支持:
如有问题请联系开发团队
'''
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✅ 文档已创建: {readme_file.name}")
        return readme_file
    
    def create_demo_package(self, app_dir):
        """创建演示包"""
        print("\n📦 创建演示包...")
        
        import zipfile
        
        package_name = f"{self.app_name}_{self.version}"
        package_path = self.demo_dir / f"{package_name}.zip"
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(app_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(app_dir)
                    zipf.write(file_path, arcname)
        
        package_size = package_path.stat().st_size / 1024 / 1024
        print(f"✅ 演示包已创建: {package_path.name}")
        print(f"📊 包大小: {package_size:.1f} MB")
        
        return package_path
    
    def run_demo_build(self):
        """运行演示构建"""
        print(f"🚀 开始构建演示版: {self.app_name} {self.version}")
        print("=" * 60)
        
        try:
            # 1. 创建演示环境
            app_dir = self.create_demo_environment()
            
            # 2. 创建启动脚本
            self.create_simple_launcher(app_dir)
            
            # 3. 创建安装脚本
            self.create_demo_installer(app_dir)
            
            # 4. 创建文档
            self.create_demo_docs(app_dir)
            
            # 5. 创建最终包
            package_path = self.create_demo_package(app_dir)
            
            print(f"\n🎉 演示版构建成功！")
            print(f"📁 演示包位置: {package_path}")
            print(f"📁 演示目录: {self.demo_dir}")
            
            print(f"\n📋 测试步骤:")
            print(f"1. 解压 {package_path.name}")
            print(f"2. 运行 install_demo.bat")
            print(f"3. 双击桌面快捷方式测试")
            
            return True
            
        except Exception as e:
            print(f"❌ 演示构建失败: {e}")
            return False

def main():
    """主函数"""
    builder = DemoBuilder()
    success = builder.run_demo_build()
    
    if success:
        print("\n✅ 演示构建完成！")
        print("💡 这个演示版展示了打包的基本流程")
        print("💡 完整版会使用conda-pack包含独立Python环境")
        input("\n按回车键退出...")
    else:
        print("\n❌ 演示构建失败")
        input("按回车键退出...")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 