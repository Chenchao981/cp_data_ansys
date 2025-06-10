#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据分析工具 - Conda环境打包器
使用conda-pack创建包含完整Python环境的本地安装包
"""

import os
import sys
import subprocess
import shutil
import json
import yaml
from pathlib import Path
from datetime import datetime
import zipfile
import tempfile

class CondaPackBuilder:
    """基于conda-pack的环境打包器"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.build_dir = self.project_root / "build_output"
        self.dist_dir = self.project_root / "distribution"
        self.app_name = "CP数据分析工具"
        self.version = "1.0.0"
        
        # 创建构建目录
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        
        # 构建信息
        self.build_info = {
            "app_name": self.app_name,
            "version": self.version,
            "build_time": datetime.now().isoformat(),
            "python_version": sys.version,
            "platform": "win-64"
        }
    
    def create_minimal_environment_yaml(self):
        """创建最小化的环境配置文件"""
        # 核心依赖包列表
        core_dependencies = [
            "python=3.12",
            "pandas>=1.3.0",
            "numpy>=1.21.0", 
            "plotly>=5.0.0",
            "openpyxl>=3.0.0",
            "matplotlib>=3.0.0",
            "seaborn>=0.10.0",
            "pathlib2>=2.3.0",
            # 可选GUI依赖
            # "pyqt5>=5.15.0",  # 根据需要取消注释
        ]
        
        pip_dependencies = [
            # 如果有pypi特有的包
        ]
        
        env_config = {
            "name": f"{self.app_name.replace(' ', '_').lower()}_env",
            "channels": ["conda-forge", "defaults"],
            "dependencies": core_dependencies
        }
        
        if pip_dependencies:
            env_config["dependencies"].append({"pip": pip_dependencies})
        
        # 保存环境配置
        env_file = self.build_dir / "environment.yml"
        with open(env_file, 'w', encoding='utf-8') as f:
            yaml.dump(env_config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"✅ 环境配置文件已创建: {env_file}")
        return env_file
    
    def create_clean_environment(self):
        """创建干净的conda环境用于打包"""
        env_name = f"{self.app_name.replace(' ', '_').lower()}_build"
        
        print(f"🔄 创建临时构建环境: {env_name}")
        
        # 删除已存在的环境
        try:
            subprocess.run([
                "conda", "env", "remove", "-n", env_name, "-y"
            ], check=False, capture_output=True)
        except:
            pass
        
        # 创建新环境
        env_file = self.create_minimal_environment_yaml()
        result = subprocess.run([
            "conda", "env", "create", "-n", env_name, "-f", str(env_file)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ 环境创建失败: {result.stderr}")
            return None, None
        
        # 获取环境路径
        result = subprocess.run([
            "conda", "info", "--envs", "--json"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            envs_info = json.loads(result.stdout)
            for env_path in envs_info["envs"]:
                if env_name in env_path:
                    print(f"✅ 构建环境已创建: {env_path}")
                    return env_name, Path(env_path)
        
        print("❌ 无法获取环境路径")
        return None, None
    
    def pack_environment(self, env_name, env_path):
        """使用conda-pack打包环境"""
        print(f"📦 开始打包环境: {env_name}")
        
        packed_env_path = self.build_dir / f"{env_name}.tar.gz"
        
        # 使用conda-pack打包
        result = subprocess.run([
            "conda-pack", 
            "-n", env_name,
            "-o", str(packed_env_path),
            "--compress-level", "6",  # 压缩级别
            "--exclude", "*.pyc",     # 排除编译文件
            "--exclude", "__pycache__",
            "--exclude", "*.a",       # 排除静态库
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ 环境打包失败: {result.stderr}")
            return None
        
        print(f"✅ 环境已打包: {packed_env_path}")
        print(f"📊 打包大小: {packed_env_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        return packed_env_path
    
    def create_application_bundle(self, packed_env_path):
        """创建应用程序包"""
        print("🎁 创建应用程序包...")
        
        app_bundle_dir = self.build_dir / "app_bundle"
        if app_bundle_dir.exists():
            shutil.rmtree(app_bundle_dir)
        app_bundle_dir.mkdir()
        
        # 1. 复制打包的环境
        env_dir = app_bundle_dir / "python_env"
        env_dir.mkdir()
        shutil.copy2(packed_env_path, env_dir / "environment.tar.gz")
        
        # 2. 复制应用程序代码
        app_code_dir = app_bundle_dir / "app"
        app_code_dir.mkdir()
        
        # 复制核心文件
        core_files = [
            "cp_data_processor_gui.py",  # GUI主程序
            "chart_generator.py",
            "README.md",
            "requirements.txt",
        ]
        
        for file_name in core_files:
            src_file = self.project_root / file_name
            if src_file.exists():
                shutil.copy2(src_file, app_code_dir)
        
        # 复制核心目录
        core_dirs = [
            "frontend",
            "cp_data_processor", 
            "output",
            "demo_output",
        ]
        
        for dir_name in core_dirs:
            src_dir = self.project_root / dir_name
            if src_dir.exists():
                shutil.copytree(src_dir, app_code_dir / dir_name, 
                              ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git*'))
        
        # 3. 创建启动脚本
        self.create_launcher_scripts(app_bundle_dir)
        
        # 4. 创建安装脚本
        self.create_installer_scripts(app_bundle_dir)
        
        # 5. 创建配置和文档
        self.create_documentation(app_bundle_dir)
        
        print(f"✅ 应用程序包已创建: {app_bundle_dir}")
        return app_bundle_dir
    
    def create_launcher_scripts(self, bundle_dir):
        """创建启动脚本"""
        scripts_dir = bundle_dir / "scripts"
        scripts_dir.mkdir()
        
        # Windows批处理启动脚本
        launcher_bat = scripts_dir / "start_app.bat"
        launcher_content = '''@echo off
setlocal EnableDelayedExpansion

echo CP Data Analysis Tool Starting...
echo.

REM Set application directories
set "APP_DIR=%~dp0.."
set "ENV_DIR=%APP_DIR%\\python_env"
set "APP_CODE_DIR=%APP_DIR%\\app"

REM Check if environment is unpacked
if not exist "%ENV_DIR%\\python.exe" (
    echo First run detected. Initializing Python environment...
    echo This may take a few minutes, please wait...
    echo.
    
    REM Extract Python environment
    cd /d "%ENV_DIR%"
    if exist "environment.tar.gz" (
        echo Extracting Python environment...
        tar -xzf environment.tar.gz
        if errorlevel 1 (
            echo ERROR: Environment extraction failed. Please check if tar command is available.
            echo NOTE: Windows 10 1903+ includes tar command by default.
            pause
            exit /b 1
        )
        
        REM Activate environment
        call conda-unpack.exe
        if errorlevel 1 (
            echo WARNING: Environment activation may have issues, but will try to continue.
        )
        
        echo Python environment initialization completed.
        echo.
    ) else (
        echo ERROR: Environment package file not found.
        pause
        exit /b 1
    )
)

REM Set Python paths
set "PATH=%ENV_DIR%;%ENV_DIR%\\Scripts;%ENV_DIR%\\Library\\bin;%PATH%"
set "PYTHONPATH=%APP_CODE_DIR%;%PYTHONPATH%"

REM Change to application directory
cd /d "%APP_CODE_DIR%"

REM Start application
echo Starting CP Data Analysis Tool GUI...
python cp_data_processor_gui.py

REM Check execution result
if errorlevel 1 (
    echo.
    echo ERROR: Application execution failed.
    echo Please check for permission issues or missing dependencies.
    pause
) else (
    echo.
    echo Application execution completed.
    pause
)
'''
        
        with open(launcher_bat, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        
        # Python启动脚本（备选）
        launcher_py = scripts_dir / "start_app.py"
        launcher_py_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP Data Analysis Tool Launcher
"""

import os
import sys
import subprocess
import tempfile
import tarfile
from pathlib import Path

def main():
    """Main launcher function"""
    print("CP Data Analysis Tool Launcher")
    print("=" * 40)
    
    # 获取路径
    script_dir = Path(__file__).parent
    app_dir = script_dir.parent
    env_dir = app_dir / "python_env"
    app_code_dir = app_dir / "app"
    
    # 检查并初始化环境
    if not (env_dir / "python.exe").exists():
        print("First run detected. Initializing Python environment...")
        initialize_environment(env_dir)
    
    # 设置环境变量
    env_path = str(env_dir)
    env_scripts = str(env_dir / "Scripts")
    
    new_env = os.environ.copy()
    new_env["PATH"] = f"{env_path};{env_scripts};" + new_env.get("PATH", "")
    new_env["PYTHONPATH"] = str(app_code_dir) + ";" + new_env.get("PYTHONPATH", "")
    
    # 启动应用程序
    print("Starting CP Data Analysis Tool GUI...")
    python_exe = env_dir / "python.exe"
    app_script = app_code_dir / "cp_data_processor_gui.py"
    
    try:
        result = subprocess.run([
            str(python_exe), str(app_script)
        ], env=new_env, cwd=str(app_code_dir))
        
        if result.returncode == 0:
            print("Application execution completed.")
        else:
            print(f"Application exited with code: {result.returncode}")
            
    except Exception as e:
        print(f"Launch failed: {e}")
        return 1
    
    return 0

def initialize_environment(env_dir):
    """Initialize Python environment"""
    env_archive = env_dir / "environment.tar.gz"
    
    if not env_archive.exists():
        print("ERROR: Environment package file not found.")
        return False
    
    print("Extracting Python environment...")
    try:
        with tarfile.open(env_archive, 'r:gz') as tar:
            tar.extractall(path=env_dir)
        
        # 运行conda-unpack
        conda_unpack = env_dir / "Scripts" / "conda-unpack.exe"
        if conda_unpack.exists():
            subprocess.run([str(conda_unpack)], cwd=str(env_dir), check=True)
        
        print("Python environment initialization completed.")
        return True
        
    except Exception as e:
        print(f"Environment initialization failed: {e}")
        return False

if __name__ == "__main__":
    sys.exit(main())
'''
        
        with open(launcher_py, 'w', encoding='utf-8') as f:
            f.write(launcher_py_content)
        
        print(f"✅ 启动脚本已创建: {scripts_dir}")
    
    def create_installer_scripts(self, bundle_dir):
        """创建安装脚本"""
        # 简单的安装脚本
        install_bat = bundle_dir / "install.bat"
        install_content = '''@echo off
echo CP Data Analysis Tool Installer
echo ===============================
echo.

REM Check administrator privileges
net session >nul 2>&1
if errorlevel 1 (
    echo WARNING: Administrator privileges recommended for best experience.
    echo You can continue with normal installation...
    echo.
    pause
)

set "INSTALL_DIR=%ProgramFiles%\\CP Data Analysis Tool"
set "CURRENT_DIR=%~dp0"

echo Install Directory: %INSTALL_DIR%
echo Source Directory: %CURRENT_DIR%
echo.

REM Create installation directory
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    if errorlevel 1 (
        echo ERROR: Cannot create installation directory. Administrator privileges may be required.
        set "INSTALL_DIR=%USERPROFILE%\\CP Data Analysis Tool"
        echo Switching to user directory installation: !INSTALL_DIR!
        mkdir "!INSTALL_DIR!"
    )
)

REM Copy files
echo Copying application files...
xcopy "%CURRENT_DIR%*" "%INSTALL_DIR%\\" /E /I /Y /Q
if errorlevel 1 (
    echo ERROR: File copy failed.
    pause
    exit /b 1
)

REM Create desktop shortcut
echo Creating desktop shortcut...
set "SHORTCUT=%USERPROFILE%\\Desktop\\CP Data Analysis Tool.lnk"
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\scripts\\start_app.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'CP Data Analysis Tool'; $Shortcut.Save()"

REM Create start menu shortcut
echo Creating start menu shortcut...
set "START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs"
if not exist "%START_MENU%\\CP Data Analysis Tool" mkdir "%START_MENU%\\CP Data Analysis Tool"
set "START_SHORTCUT=%START_MENU%\\CP Data Analysis Tool\\CP Data Analysis Tool.lnk"
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\scripts\\start_app.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'CP Data Analysis Tool'; $Shortcut.Save()"

echo.
echo Installation completed successfully!
echo Install Location: %INSTALL_DIR%
echo Desktop Shortcut: CP Data Analysis Tool
echo Start Menu: CP Data Analysis Tool
echo.
echo NOTE: First run will automatically initialize Python environment. Please be patient.
pause
'''
        
        with open(install_bat, 'w', encoding='utf-8') as f:
            f.write(install_content)
        
        # 卸载脚本
        uninstall_bat = bundle_dir / "uninstall.bat"
        uninstall_content = '''@echo off
echo CP Data Analysis Tool Uninstaller
echo ===============================
echo.

set "INSTALL_DIR=%ProgramFiles%\\CP Data Analysis Tool"
if not exist "%INSTALL_DIR%" (
    set "INSTALL_DIR=%USERPROFILE%\\CP Data Analysis Tool"
)

echo Detected installation directory: %INSTALL_DIR%
echo.
echo WARNING: Are you sure you want to uninstall CP Data Analysis Tool?
echo This will remove all program files (excluding user data).
pause

if exist "%INSTALL_DIR%" (
    echo Removing program files...
    rmdir /s /q "%INSTALL_DIR%"
    if errorlevel 1 (
        echo ERROR: Removal failed. Some files may be in use.
    ) else (
        echo Program files removed successfully.
    )
)

REM Remove shortcuts
echo Cleaning up shortcuts...
del "%USERPROFILE%\\Desktop\\CP Data Analysis Tool.lnk" 2>nul
rmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\CP Data Analysis Tool" 2>nul

echo.
echo Uninstallation completed!
pause
'''
        
        with open(uninstall_bat, 'w', encoding='utf-8') as f:
            f.write(uninstall_content)
        
        print("✅ 安装/卸载脚本已创建")
    
    def create_documentation(self, bundle_dir):
        """创建文档和配置"""
        docs_dir = bundle_dir / "docs"
        docs_dir.mkdir()
        
        # 用户手册
        user_manual = docs_dir / "用户手册.md"
        manual_content = f'''# CP数据分析工具 用户手册

## 软件介绍

CP数据分析工具是一款专业的半导体测试数据分析软件，支持：
- 多种数据格式读取（DCP、CW、MEX等）
- 专业图表生成（箱体图、散点图、良率图等）
- 数据统计分析
- 报告导出功能

## 系统要求

- Windows 10/11 (64位)
- 磁盘空间：约500MB
- 内存：建议4GB以上

## 安装说明

1. 双击运行 `install.bat`
2. 选择安装目录（默认安装到Program Files）
3. 等待安装完成
4. 首次运行时会自动初始化Python环境（约2-3分钟）

## 使用方法

### 启动软件
- 双击桌面快捷方式"CP数据分析工具"
- 或从开始菜单启动

### 基本操作
1. 准备数据文件放在 `output` 目录
2. 运行软件，程序会自动加载数据
3. 生成的图表保存在 `demo_output/generated_charts` 目录

### 数据文件要求
软件支持以下格式的数据文件：
- `*_yield_*.csv` - 良率数据
- `*_spec_*.csv` - 规格数据  
- `*_cleaned_*.csv` - 清理后的测试数据

## 常见问题

### Q: 首次启动很慢？
A: 首次运行需要初始化Python环境，这是正常现象，后续启动会很快。

### Q: 提示缺少数据文件？
A: 请确保在 `output` 目录中放置正确格式的CSV文件。

### Q: 图表无法生成？
A: 请检查数据文件格式是否正确，参数列是否包含数值数据。

## 技术支持

如有问题请联系技术支持团队。

## 版本信息

- 版本：{self.version}
- 构建时间：{self.build_info["build_time"]}
- Python版本：{self.build_info["python_version"]}
'''
        
        with open(user_manual, 'w', encoding='utf-8') as f:
            f.write(manual_content)
        
        # 构建信息
        build_info_file = bundle_dir / "build_info.json"
        with open(build_info_file, 'w', encoding='utf-8') as f:
            json.dump(self.build_info, f, indent=2, ensure_ascii=False)
        
        print("✅ 文档已创建")
    
    def create_final_package(self, bundle_dir):
        """创建最终的分发包"""
        print("📦 创建最终分发包...")
        
        package_name = f"{self.app_name}_{self.version}_Windows_x64"
        package_path = self.dist_dir / f"{package_name}.zip"
        
        # 创建ZIP包
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for root, dirs, files in os.walk(bundle_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(bundle_dir)
                    zipf.write(file_path, arcname)
        
        package_size = package_path.stat().st_size / 1024 / 1024
        
        print(f"✅ 最终包已创建: {package_path}")
        print(f"📊 包大小: {package_size:.1f} MB")
        
        # 创建发布说明
        self.create_release_notes(package_path, package_size)
        
        return package_path
    
    def create_release_notes(self, package_path, package_size):
        """创建发布说明"""
        release_notes = self.dist_dir / "发布说明.txt"
        
        notes_content = f'''CP数据分析工具 {self.version} 发布包

📦 包信息：
- 文件名：{package_path.name}
- 大小：{package_size:.1f} MB
- 构建时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

🛠️ 安装步骤：
1. 解压到任意目录
2. 运行 install.bat 进行安装
3. 首次启动会自动初始化环境

📋 包含内容：
- 完整Python环境（无需联网安装）
- 所有依赖包
- 应用程序代码
- 启动和安装脚本
- 用户文档

💡 注意事项：
- 首次运行需要2-3分钟初始化
- 建议以管理员身份安装
- 支持Windows 10/11 64位系统

🔧 技术信息：
- Python版本：{self.build_info["python_version"].split()[0]}
- 核心依赖：pandas, plotly, matplotlib, numpy
- 打包工具：conda-pack
'''
        
        with open(release_notes, 'w', encoding='utf-8') as f:
            f.write(notes_content)
        
        print(f"✅ 发布说明已创建: {release_notes}")
    
    def cleanup_build_environment(self, env_name):
        """清理构建环境"""
        if env_name:
            print(f"🧹 清理构建环境: {env_name}")
            subprocess.run([
                "conda", "env", "remove", "-n", env_name, "-y"
            ], check=False, capture_output=True)
    
    def run_full_build(self):
        """运行完整构建流程"""
        print(f"🚀 开始构建 {self.app_name} {self.version}")
        print("=" * 60)
        
        env_name = None
        try:
            # 1. 创建干净的构建环境
            env_name, env_path = self.create_clean_environment()
            if not env_name:
                return False
            
            # 2. 打包环境
            packed_env = self.pack_environment(env_name, env_path)
            if not packed_env:
                return False
            
            # 3. 创建应用程序包
            app_bundle = self.create_application_bundle(packed_env)
            
            # 4. 创建最终分发包
            final_package = self.create_final_package(app_bundle)
            
            print("\n🎉 构建成功完成！")
            print(f"📁 分发包位置: {final_package}")
            print(f"📁 构建输出目录: {self.dist_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ 构建失败: {e}")
            return False
            
        finally:
            # 清理构建环境
            if env_name:
                self.cleanup_build_environment(env_name)

def main():
    """主函数"""
    builder = CondaPackBuilder()
    success = builder.run_full_build()
    
    if success:
        print("\n✅ 所有任务完成！")
        input("按回车键退出...")
    else:
        print("\n❌ 构建失败，请检查错误信息")
        input("按回车键退出...")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 