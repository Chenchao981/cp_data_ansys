#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Conda-pack测试脚本
验证conda-pack是否能正常工作
"""

import subprocess
import sys
import json
from pathlib import Path

def test_conda_pack():
    """测试conda-pack功能"""
    print("🧪 测试conda-pack功能...")
    
    # 1. 检查conda环境
    try:
        result = subprocess.run(["conda", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Conda版本: {result.stdout.strip()}")
        else:
            print("❌ Conda未找到")
            return False
    except FileNotFoundError:
        print("❌ Conda未找到")
        return False
    
    # 2. 检查conda-pack
    try:
        result = subprocess.run(["conda-pack", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Conda-pack版本: {result.stdout.strip()}")
        else:
            print("❌ Conda-pack未找到，正在安装...")
            install_result = subprocess.run(["conda", "install", "conda-pack", "-y"], 
                                          capture_output=True, text=True)
            if install_result.returncode != 0:
                print(f"❌ Conda-pack安装失败: {install_result.stderr}")
                return False
            print("✅ Conda-pack安装成功")
    except FileNotFoundError:
        print("❌ Conda-pack不可用")
        return False
    
    # 3. 获取当前环境信息
    try:
        result = subprocess.run(["conda", "info", "--json"], capture_output=True, text=True)
        if result.returncode == 0:
            info = json.loads(result.stdout)
            current_env = info.get("active_prefix", "Unknown")
            print(f"✅ 当前环境: {current_env}")
            
            # 获取环境大小估算
            env_path = Path(current_env)
            if env_path.exists():
                # 简单估算（不完全准确，但能给出大概）
                total_size = sum(f.stat().st_size for f in env_path.rglob('*') if f.is_file())
                size_mb = total_size / 1024 / 1024
                print(f"📊 当前环境估算大小: {size_mb:.1f} MB")
        else:
            print("⚠️ 无法获取环境信息")
    except Exception as e:
        print(f"⚠️ 环境信息获取失败: {e}")
    
    # 4. 检查核心依赖包
    core_packages = ["pandas", "numpy", "plotly", "matplotlib", "openpyxl"]
    print("🔍 检查核心依赖包...")
    
    for package in core_packages:
        try:
            result = subprocess.run([sys.executable, "-c", f"import {package}; print({package}.__version__)"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"  ✅ {package}: {version}")
            else:
                print(f"  ❌ {package}: 未安装")
        except Exception:
            print(f"  ❌ {package}: 检查失败")
    
    print("\n✅ Conda-pack测试完成！")
    return True

def estimate_package_size():
    """估算打包后的大小"""
    print("\n📊 估算打包大小...")
    
    # 获取已安装包的信息
    try:
        result = subprocess.run(["conda", "list", "--json"], capture_output=True, text=True)
        if result.returncode == 0:
            packages = json.loads(result.stdout)
            print(f"📦 已安装包数量: {len(packages)}")
            
            # 显示主要的大包
            large_packages = ["numpy", "pandas", "matplotlib", "plotly", "scipy", "mkl"]
            print("🔍 主要依赖包:")
            for pkg in packages:
                if pkg["name"] in large_packages:
                    print(f"  📋 {pkg['name']}: {pkg['version']} ({pkg.get('channel', 'unknown')})")
        
        print("\n💡 预计打包大小:")
        print("  - 最小化环境: ~150-250 MB")
        print("  - 当前完整环境: ~300-500 MB") 
        print("  - 压缩后ZIP包: ~100-200 MB")
        
    except Exception as e:
        print(f"❌ 大小估算失败: {e}")

def main():
    """主函数"""
    print("🔬 CP数据分析工具 - Conda-pack环境测试")
    print("=" * 50)
    
    if test_conda_pack():
        estimate_package_size()
        print("\n🎉 测试通过！可以开始构建过程。")
        print("\n下一步:")
        print("1. 运行 quick_build.bat 开始完整构建")
        print("2. 或运行 python build_scripts/conda_pack_builder.py")
    else:
        print("\n❌ 测试失败，请检查环境配置")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 