#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据分析工具 - MSI安装包构建器
使用cx_Freeze创建专业的Windows MSI安装包
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from datetime import datetime
import tempfile

class MSIBuilder:
    """MSI安装包构建器"""
    
    def __init__(self):
        self.project_root = Path.cwd().parent  # packaging的上级目录
        self.packaging_root = Path.cwd()       # packaging目录
        self.build_dir = self.packaging_root / "msi_build"
        self.dist_dir = self.packaging_root / "distribution"
        
        self.app_name = "CP数据分析工具"
        self.version = "1.0.0"
        self.company = "半导体数据分析团队"
        self.description = "专业的半导体测试数据分析工具"
        
        # 创建构建目录
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        
        print(f"🎯 MSI构建器初始化")
        print(f"📁 项目根目录: {self.project_root}")
        print(f"📁 构建目录: {self.build_dir}")
    
    def check_requirements(self):
        """检查构建要求"""
        print("\n🔍 检查构建环境...")
        
        # 检查Python
        python_version = sys.version_info
        if python_version.major != 3 or python_version.minor < 8:
            print("❌ 需要Python 3.8+")
            return False
        print(f"✅ Python版本: {sys.version}")
        
        # 检查cx_Freeze
        try:
            import cx_Freeze
            # 尝试获取版本信息，如果没有version属性则使用其他方法
            try:
                version = cx_Freeze.version
            except AttributeError:
                try:
                    version = cx_Freeze.__version__
                except AttributeError:
                    version = "已安装"
            print(f"✅ cx_Freeze版本: {version}")
        except ImportError:
            print("❌ 未找到cx_Freeze，正在安装...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "cx_Freeze"], check=True)
                print("✅ cx_Freeze安装成功")
            except subprocess.CalledProcessError:
                print("❌ cx_Freeze安装失败")
                return False
        
        # 检查核心依赖
        required_packages = ["pandas", "numpy", "plotly", "matplotlib", "openpyxl"]
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ 缺少依赖包: {package}")
                return False
        
        return True
    
    def create_setup_script(self):
        """创建setup.py脚本"""
        print("\n📝 创建setup.py脚本...")
        
        setup_script = self.build_dir / "setup.py"
        
        # 主程序入口
        main_script = self.project_root / "chart_generator.py"
        if not main_script.exists():
            print(f"❌ 未找到主程序: {main_script}")
            return None
        
        setup_content = f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CP数据分析工具 - MSI安装包配置
"""

import sys
from cx_Freeze import setup, Executable
from pathlib import Path

# 构建选项
build_exe_options = {{
    # 包含的包
    "packages": [
        "pandas", "numpy", "plotly", "matplotlib", "seaborn", 
        "openpyxl", "pathlib2", "datetime", "json", "csv",
        "tkinter", "threading", "webbrowser", "urllib",
        "encodings", "encodings.utf_8", "encodings.gbk"
    ],
    
    # 包含的模块
    "includes": [
        "pandas.plotting._matplotlib",
        "matplotlib.backends.backend_tkagg",
        "plotly.graph_objects",
        "plotly.express",
        "plotly.io",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.ttk"
    ],
    
    # 排除的模块（减小体积）
    "excludes": [
        "test", "unittest", "email", "html", "http", "urllib3",
        "xml", "pydoc", "doctest", "argparse", "sqlite3",
        "tkinter.test", "matplotlib.tests", "pandas.tests"
    ],
    
    # 包含的文件
    "include_files": [
        # 应用程序文件
        (r"{str(self.project_root / 'frontend')}", "frontend"),
        (r"{str(self.project_root / 'cp_data_processor')}", "cp_data_processor"),
        (r"{str(self.project_root / 'output')}", "output"),
        (r"{str(self.project_root / 'demo_output')}", "demo_output"),
        
        # 文档文件
        (r"{str(self.project_root / 'README.md')}", "README.md"),
        
        # 示例数据（如果存在）
        # (r"example_data", "example_data"),
    ],
    
    # 优化选项
    "optimize": 2,
}}

# MSI构建选项
bdist_msi_options = {{
    "upgrade_code": "{{12345678-1234-5678-9ABC-123456789012}}",  # 固定的升级代码
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\\{self.app_name}",
}}

# 可执行文件配置
executables = [
    Executable(
        script=r"{str(main_script)}",
        base="Win32GUI" if sys.platform == "win32" else None,  # Windows GUI应用
        target_name="CP数据分析工具.exe",
        copyright="© 2024 {self.company}",
    )
]

# 设置配置
setup(
    name="{self.app_name}",
    version="{self.version}",
    description="{self.description}",
    author="{self.company}",
    options={{
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options
    }},
    executables=executables
)
'''
        
        with open(setup_script, 'w', encoding='utf-8') as f:
            f.write(setup_content)
        
        print(f"✅ setup.py已创建: {setup_script}")
        return setup_script
    
    def build_msi(self, setup_script):
        """构建MSI安装包"""
        print("\n🔨 开始构建MSI安装包...")
        
        # 切换到构建目录
        original_cwd = os.getcwd()
        os.chdir(self.build_dir)
        
        try:
            # 清理之前的构建
            if (self.build_dir / "build").exists():
                shutil.rmtree(self.build_dir / "build")
            if (self.build_dir / "dist").exists():
                shutil.rmtree(self.build_dir / "dist")
            
            # 运行cx_Freeze构建
            print("🔄 运行cx_Freeze构建...")
            result = subprocess.run([
                sys.executable, "setup.py", "bdist_msi"
            ], capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode != 0:
                print(f"❌ MSI构建失败:")
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
                return None
            
            print("✅ MSI构建完成")
            
            # 查找生成的MSI文件
            dist_dir = self.build_dir / "dist"
            msi_files = list(dist_dir.glob("*.msi"))
            
            if not msi_files:
                print("❌ 未找到生成的MSI文件")
                return None
            
            msi_file = msi_files[0]
            print(f"✅ MSI文件已生成: {msi_file}")
            
            # 移动到distribution目录
            final_name = f"{self.app_name}_{self.version}_Windows_x64.msi"
            final_path = self.dist_dir / final_name
            
            shutil.copy2(msi_file, final_path)
            
            # 获取文件大小
            file_size = final_path.stat().st_size / 1024 / 1024
            print(f"📊 MSI包大小: {file_size:.1f} MB")
            
            return final_path
            
        except Exception as e:
            print(f"❌ 构建过程出错: {e}")
            return None
            
        finally:
            os.chdir(original_cwd)
    
    def create_installer_readme(self, msi_path):
        """创建安装包说明"""
        print("\n📚 创建安装说明...")
        
        readme_file = self.dist_dir / "MSI安装包说明.txt"
        readme_content = f'''{self.app_name} MSI安装包
============================

📦 安装包信息:
- 文件名: {msi_path.name}
- 版本: {self.version}
- 大小: {msi_path.stat().st_size / 1024 / 1024:.1f} MB
- 构建时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

🛠️ 系统要求:
- 操作系统: Windows 10/11 (64位)
- 磁盘空间: 约300MB可用空间
- 内存: 建议4GB以上

📋 安装步骤:
1. 双击运行 {msi_path.name}
2. 按照安装向导提示完成安装
3. 安装完成后可从开始菜单启动

💻 使用方法:
1. 从开始菜单启动 "{self.app_name}"
2. 或直接运行安装目录下的 "CP数据分析工具.exe"
3. 将数据文件放在程序目录的 output 文件夹中
4. 程序会自动分析并生成图表

📁 默认安装路径:
C:\\Program Files\\{self.app_name}\\

🗑️ 卸载方法:
- 通过Windows"添加或删除程序"卸载
- 或运行: msiexec /x {msi_path.name}

⚠️ 注意事项:
- 首次运行可能需要稍等片刻初始化
- 如遇到权限问题，请以管理员身份安装
- 卸载后用户数据不会被删除

🔧 故障排除:
- 如果启动失败，检查是否有其他Python程序冲突
- 确认Windows版本兼容性
- 检查杀毒软件是否误报

📞 技术支持:
如有问题请联系开发团队
版本: {self.version}
构建日期: {datetime.now().strftime("%Y-%m-%d")}
'''
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✅ 安装说明已创建: {readme_file}")
        return readme_file
    
    def run_full_build(self):
        """运行完整MSI构建流程"""
        print(f"🚀 开始构建MSI安装包: {self.app_name} {self.version}")
        print("=" * 60)
        
        try:
            # 1. 检查构建环境
            if not self.check_requirements():
                return False
            
            # 2. 创建setup.py脚本
            setup_script = self.create_setup_script()
            if not setup_script:
                return False
            
            # 3. 构建MSI
            msi_path = self.build_msi(setup_script)
            if not msi_path:
                return False
            
            # 4. 创建说明文档
            self.create_installer_readme(msi_path)
            
            print(f"\n🎉 MSI安装包构建成功！")
            print(f"📁 MSI文件: {msi_path}")
            print(f"📁 分发目录: {self.dist_dir}")
            print(f"\n💡 使用方法:")
            print(f"1. 将 {msi_path.name} 复制到目标电脑")
            print(f"2. 双击运行MSI文件进行安装")
            print(f"3. 安装完成后从开始菜单启动程序")
            
            return True
            
        except Exception as e:
            print(f"❌ 构建失败: {e}")
            return False

def main():
    """主函数"""
    builder = MSIBuilder()
    success = builder.run_full_build()
    
    if success:
        print("\n✅ MSI构建完成！")
        print("💡 现在可以将MSI文件复制到其他Windows电脑安装")
        input("按回车键退出...")
    else:
        print("\n❌ MSI构建失败，请检查错误信息")
        input("按回车键退出...")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 