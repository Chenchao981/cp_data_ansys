import zipapp
import os
import shutil

# --- 配置 ---
# 项目根目录
source_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# 输出的 app.pyz 文件路径
target_file = os.path.join(os.path.dirname(__file__), 'release', 'app.pyz')
# 打包的入口点
main_entry_point = 'gui.cp_data_gui:main'
# 需要包含在 .pyz 文件中的顶层目录
packages_to_include = ['cp_data_processor', 'gui', 'python_cp', 'utils', 'frontend']
# 需要包含在 .pyz 文件中的根目录下的 .py 文件
files_to_include = [
    'clean_dcp_data.py',
    'clean_csv_data.py',
    'dcp_spec_extractor.py',
    'cp_unit_converter.py'
]

def create_archive():
    """创建 app.pyz 文件"""
    
    # 临时的打包源目录
    temp_source_dir = os.path.join(os.path.dirname(__file__), '_temp_build_src')

    # 清理旧的临时目录和目标文件
    if os.path.exists(temp_source_dir):
        shutil.rmtree(temp_source_dir)
    if os.path.exists(target_file):
        os.remove(target_file)
        print(f"已删除旧的 {os.path.basename(target_file)}")

    os.makedirs(temp_source_dir, exist_ok=True)
    print(f"创建临时目录: {temp_source_dir}")

    # --- 拷贝必要的包到临时目录 ---
    for package_name in packages_to_include:
        src_path = os.path.join(source_root, package_name)
        if os.path.isdir(src_path):
            dest_path = os.path.join(temp_source_dir, package_name)
            shutil.copytree(src_path, dest_path)
            print(f"已拷贝 {package_name} 到临时目录")
        else:
            print(f"警告: 找不到目录 {package_name}，跳过。")
            
    # --- 拷贝必要的 .py 文件到临时目录 ---
    for file_name in files_to_include:
        src_path = os.path.join(source_root, file_name)
        if os.path.isfile(src_path):
            dest_path = os.path.join(temp_source_dir, file_name)
            shutil.copy2(src_path, dest_path)
            print(f"已拷贝 {file_name} 到临时目录")
        else:
            print(f"警告: 找不到文件 {file_name}，跳过。")

    # --- 创建 .pyz 文件 ---
    print(f"正在从 {temp_source_dir} 创建 {os.path.basename(target_file)}...")
    zipapp.create_archive(
        source=temp_source_dir,
        target=target_file,
        interpreter='/usr/bin/env python',
        main=main_entry_point,
        compressed=True
    )
    print(f"成功创建 {target_file}")

    # --- 清理临时目录 ---
    shutil.rmtree(temp_source_dir)
    print(f"已删除临时目录: {temp_source_dir}")

if __name__ == '__main__':
    create_archive()
    print("\\n打包完成！请在 'release' 文件夹中找到 app.pyz。") 