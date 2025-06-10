import os
import shutil
import zipapp

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

    # 5. 清理临时目录
    print("🧹 正在清理临时文件...")
    shutil.rmtree(BUILD_DIR)

    print(f"\n🎉 构建成功！\n✅ 可执行文件已保存至: {target_pyz_path}")
    print("现在，您可以将 dist 目录下的 app.pyz 和 requirements.txt、start.bat 一起分发给用户。")

if __name__ == '__main__':
    build() 