#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证Lion GUI打包结果
检查app.pyz是否包含完整的Lion功能
"""

import zipfile
import sys
from pathlib import Path

def verify_pyz_contents():
    """验证app.pyz包含的内容"""
    print("🦁 验证Lion GUI打包结果")
    print("=" * 60)
    
    pyz_path = "packaging/release/app.pyz"
    
    if not Path(pyz_path).exists():
        print("❌ app.pyz文件不存在")
        return False
    
    try:
        with zipfile.ZipFile(pyz_path, 'r') as zip_file:
            files = zip_file.namelist()
            
        print(f"📦 app.pyz文件大小: {Path(pyz_path).stat().st_size / 1024:.1f} KB")
        print(f"📊 包含文件总数: {len(files)}")
        
        # 检查必要的Lion文件
        required_files = [
            # Lion模块文件
            "lion/__init__.py",
            "lion/lion_reader.py", 
            "lion/lion_adapter.py",
            "lion/lion_chart_generator.py",
            
            # Lion根文件
            "clean_lion_data.py",
            "lion_batch_processor.py",
            
            # GUI文件
            "gui/multi_company_main.py",
            "gui/multi_company_gui.py",
            "gui/widgets/lion_widget.py",
            
            # 入口点
            "__main__.py"
        ]
        
        print(f"\n🔍 检查必要的Lion文件:")
        missing_files = []
        for required_file in required_files:
            if required_file in files:
                print(f"   ✅ {required_file}")
            else:
                print(f"   ❌ {required_file} - 缺失")
                missing_files.append(required_file)
        
        # 检查Lion功能相关的依赖
        dependencies = [
            "cp_data_processor/",
            "frontend/",
            "jt_data_processor/"
        ]
        
        print(f"\n🔍 检查依赖模块:")
        for dep in dependencies:
            dep_files = [f for f in files if f.startswith(dep)]
            if dep_files:
                print(f"   ✅ {dep} ({len(dep_files)} 个文件)")
            else:
                print(f"   ❌ {dep} - 缺失")
                missing_files.append(dep)
        
        # 统计各模块文件数量
        print(f"\n📊 模块文件统计:")
        modules = {
            "lion/": [f for f in files if f.startswith("lion/")],
            "gui/": [f for f in files if f.startswith("gui/")],  
            "cp_data_processor/": [f for f in files if f.startswith("cp_data_processor/")],
            "frontend/": [f for f in files if f.startswith("frontend/")],
            "jt_data_processor/": [f for f in files if f.startswith("jt_data_processor/")]
        }
        
        for module_name, module_files in modules.items():
            print(f"   {module_name}: {len(module_files)} 个文件")
        
        if not missing_files:
            print(f"\n✅ 所有必要的Lion文件都已包含在app.pyz中")
            return True
        else:
            print(f"\n❌ 发现 {len(missing_files)} 个缺失文件")
            return False
            
    except Exception as e:
        print(f"❌ 验证过程出现错误: {e}")
        return False

def verify_entry_point():
    """验证入口点配置"""
    print(f"\n🔍 验证入口点配置:")
    
    # 检查create_pyz.py中的配置
    try:
        with open("packaging/create_pyz.py", 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "main_entry_point = 'gui.multi_company_main:main'" in content:
            print("   ✅ 入口点配置正确: gui.multi_company_main:main")
            return True
        else:
            print("   ❌ 入口点配置不正确")
            return False
            
    except Exception as e:
        print(f"   ❌ 无法验证入口点配置: {e}")
        return False

def verify_packaging_config():
    """验证打包配置"""
    print(f"\n🔍 验证打包配置:")
    
    try:
        with open("packaging/create_pyz.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含Lion相关配置
        checks = [
            ("Lion模块", "'lion'" in content),
            ("Lion数据清洗", "'clean_lion_data.py'" in content),
            ("Lion批次处理", "'lion_batch_processor.py'" in content),
            ("多公司GUI", "'gui'" in content)
        ]
        
        all_good = True
        for check_name, check_result in checks:
            if check_result:
                print(f"   ✅ {check_name}: 已配置")
            else:
                print(f"   ❌ {check_name}: 未配置")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"   ❌ 无法验证打包配置: {e}")
        return False

def main():
    """主函数"""
    print("🔧 Lion GUI打包验证工具")
    print("=" * 80)
    
    # 验证1: app.pyz内容
    contents_ok = verify_pyz_contents()
    
    # 验证2: 入口点配置
    entry_point_ok = verify_entry_point()
    
    # 验证3: 打包配置
    config_ok = verify_packaging_config()
    
    print(f"\n{'='*80}")
    print("📊 验证结果总结")
    print("=" * 80)
    print(f"app.pyz内容: {'✅ 正确' if contents_ok else '❌ 有问题'}")
    print(f"入口点配置: {'✅ 正确' if entry_point_ok else '❌ 有问题'}")
    print(f"打包配置: {'✅ 正确' if config_ok else '❌ 有问题'}")
    
    if all([contents_ok, entry_point_ok, config_ok]):
        print("\n🎉 验证通过！")
        print("\n✅ Lion GUI打包成功:")
        print("   - app.pyz已包含完整的Lion功能")
        print("   - 支持HuaHong、JeTech、Lion三家公司")
        print("   - 入口点配置为多公司GUI")
        print("   - 包含所有必要的依赖模块")
        
        print(f"\n🚀 使用方法:")
        print("   Windows环境下双击 packaging/release/start.bat")
        print("   或者运行: python packaging/release/app.pyz")
        
        print(f"\n📁 发布文件位置:")
        print("   packaging/release/app.pyz (已覆盖原版本)")
        
        return 0
    else:
        print("\n❌ 验证失败，需要检查打包配置")
        return 1

if __name__ == "__main__":
    exit(main())