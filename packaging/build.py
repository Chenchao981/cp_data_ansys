import os
import shutil
import zipapp
import subprocess
import sys
from pathlib import Path

# --- 配置 ---
# 需要打包进 .pyz 文件的源代码目录
SOURCE_DIRS = [
    'cp_data_processor',
    'app',
    'utils',
    'readers',
    'processing',
    'plotting',
    'exporters',
    'analysis',
    'frontend',
    'gui',
    'data_models'
]
# 临时的构建目录
BUILD_DIR = 'build_temp'
# 最终生成物存放目录
DIST_DIR = 'packaging/dist'
# 最终的 .pyz 文件名
PYZ_FILENAME = 'app.pyz'

# GUI 启动入口代码
# 这部分代码会被写入到 .pyz 包的 __main__.py 中，作为程序的启动入口
MAIN_APP_CODE = """
import tkinter as tk
from cp_data_processor.app import CPDataProcessorApp

def main():
    '''应用程序主入口'''
    try:
        root = tk.Tk()
        app = CPDataProcessorApp(root)
        root.mainloop()
    except Exception as e:
        print(f"启动失败，发生错误: {e}")
        input("按 Enter 键退出...")

if __name__ == "__main__":
    main()
"""

def download_dependencies():
    """下载依赖包到wheels文件夹"""
    print("📦 正在下载依赖包...")
    
    wheels_dir = Path(DIST_DIR) / "wheels"
    requirements_file = Path(DIST_DIR) / "requirements.txt"
    
    # 创建wheels目录
    wheels_dir.mkdir(exist_ok=True)
    
    if not requirements_file.exists():
        print(f"⚠️ 警告: 找不到 {requirements_file}，跳过依赖下载")
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
            print(f"📦 共下载 {len(downloaded_files)} 个文件")
            
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
    print("📝 正在创建离线安装脚本...")
    
    install_offline_bat = Path(DIST_DIR) / "install_offline.bat"
    
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

# --- 执行构建 ---
def build():
    """执行打包过程"""
    print("🚀 开始构建可执行 .pyz 文件...")

    # 1. 清理旧的构建文件
    print("🧹 清理旧的构建文件...")
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    if not os.path.exists(DIST_DIR):
        os.makedirs(DIST_DIR)
    
    target_pyz_path = os.path.join(DIST_DIR, PYZ_FILENAME)
    if os.path.exists(target_pyz_path):
        os.remove(target_pyz_path)

    os.makedirs(BUILD_DIR)

    # 2. 拷贝所有源代码到构建目录
    print("📦 正在拷贝源代码...")
    for src_dir in SOURCE_DIRS:
        if os.path.exists(src_dir):
            shutil.copytree(src_dir, os.path.join(BUILD_DIR, src_dir))
        else:
            print(f"⚠️ 警告：目录 '{src_dir}' 不存在，已跳过。")

    # 3. 创建 GUI 入口文件 __main__.py
    print("✍️  正在创建程序入口...")
    main_py_path = os.path.join(BUILD_DIR, '__main__.py')
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(MAIN_APP_CODE)

    # 4. 使用 zipapp 打包
    print(f"🎁 正在打包成 {PYZ_FILENAME}...")
    zipapp.create_archive(
        BUILD_DIR,
        target_pyz_path,
        interpreter='/usr/bin/env python' # 这会让脚本在用户的Python环境下运行
    )

    # 5. 下载依赖包
    print("📦 正在准备离线安装包...")
    download_success = download_dependencies()
    
    # 6. 创建离线安装脚本
    create_offline_install_script()

    # 7. 清理临时目录
    print("🧹 正在清理临时文件...")
    shutil.rmtree(BUILD_DIR)

    print(f"\n🎉 构建成功！\n✅ 可执行文件已保存至: {target_pyz_path}")
    if download_success:
        print("✅ 离线依赖包已准备完成")
        print("📁 用户现在可以选择在线安装或离线安装依赖")
    else:
        print("⚠️ 离线依赖包下载失败，用户只能使用在线安装")
    print("现在，您可以将整个 dist 目录分发给用户。")

if __name__ == '__main__':
    build() 