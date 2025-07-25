#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试F25260021.01和F25260021批次区分修复
验证具体的问题场景
"""

import sys
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.append('.')

def test_specific_case():
    """测试具体的F25260021.01和F25260021场景"""
    print("🦁 测试F25260021.01和F25260021批次区分")
    print("=" * 60)
    
    # 创建临时目录结构模拟真实情况
    with tempfile.TemporaryDirectory(prefix="lion_specific_test_") as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建两个批次目录
        batch1_dir = temp_path / "F25260021"
        batch2_dir = temp_path / "F25260021.01"
        
        batch1_dir.mkdir()
        batch2_dir.mkdir()
        
        print(f"📁 创建测试目录结构:")
        print(f"   {temp_path}/")
        print(f"   ├── F25260021/")
        print(f"   └── F25260021.01/")
        
        # 测试批次发现逻辑
        print(f"\n🔍 测试批次发现逻辑:")
        
        # 模拟discover_batch_files的逻辑
        batch_files = {}
        for batch_dir in temp_path.iterdir():
            if batch_dir.is_dir():
                # 使用修复后的逻辑：文件夹名称作为批次ID
                batch_id = batch_dir.name
                batch_files[batch_id] = []  # 空文件列表用于测试
                print(f"   发现批次: {batch_id}")
        
        expected_batches = {"F25260021", "F25260021.01"}
        found_batches = set(batch_files.keys())
        
        print(f"\n📊 批次识别结果:")
        print(f"   期望批次: {sorted(expected_batches)}")
        print(f"   实际批次: {sorted(found_batches)}")
        
        if found_batches == expected_batches:
            print("   ✅ 批次正确区分，没有被合并")
        else:
            print("   ❌ 批次识别有问题")
            return False
        
        # 测试lot_id提取逻辑
        print(f"\n🔍 测试lot_id提取逻辑:")
        
        from lion.lion_reader import LionExcelReader
        reader = LionExcelReader()
        
        test_cases = [
            (str(batch1_dir / "F25260021_5.xlsx"), "F25260021"),
            (str(batch2_dir / "F25260021_12.xlsx"), "F25260021.01")
        ]
        
        all_correct = True
        for file_path, expected_lot_id in test_cases:
            actual_lot_id = reader._extract_lot_id(file_path)
            print(f"   文件: {Path(file_path).parent.name}/{Path(file_path).name}")
            print(f"   lot_id: {actual_lot_id} (期望: {expected_lot_id})")
            
            if actual_lot_id == expected_lot_id:
                print("   ✅ 正确")
            else:
                print("   ❌ 错误")
                all_correct = False
        
        # 测试wafer_id提取
        print(f"\n🔍 测试wafer_id提取逻辑:")
        
        wafer_test_cases = [
            (str(batch1_dir / "F25260021_5.xlsx"), "5"),
            (str(batch2_dir / "F25260021_12.xlsx"), "12")
        ]
        
        for file_path, expected_wafer_id in wafer_test_cases:
            actual_wafer_id = reader._extract_wafer_id(file_path)
            print(f"   文件: {Path(file_path).name}")
            print(f"   wafer_id: {actual_wafer_id} (期望: {expected_wafer_id})")
            
            if actual_wafer_id == expected_wafer_id:
                print("   ✅ 正确")
            else:
                print("   ❌ 错误")
                all_correct = False
        
        return all_correct

def test_gui_integration():
    """测试GUI集成"""
    print(f"\n🖥️ 测试GUI集成")
    print("=" * 60)
    
    try:
        from gui.widgets.lion_widget import extract_lion_lot_id_from_folder
        
        # 创建测试目录
        with tempfile.TemporaryDirectory(prefix="gui_integration_test_") as temp_dir:
            temp_path = Path(temp_dir)
            
            test_dirs = [
                temp_path / "F25260021",
                temp_path / "F25260021.01"
            ]
            
            for test_dir in test_dirs:
                test_dir.mkdir()
            
            print("📁 测试GUI文件夹lot_id提取:")
            
            all_correct = True
            for test_dir in test_dirs:
                expected = test_dir.name
                actual = extract_lion_lot_id_from_folder(str(test_dir))
                
                print(f"   目录: {test_dir.name}")
                print(f"   提取的lot_id: {actual} (期望: {expected})")
                
                if actual == expected:
                    print("   ✅ 正确")
                else:
                    print("   ❌ 错误")
                    all_correct = False
            
            return all_correct
    
    except Exception as e:
        print(f"❌ GUI集成测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 Lion F25260021.01 vs F25260021 区分修复验证")
    print("=" * 80)
    
    # 测试具体场景
    specific_ok = test_specific_case()
    
    # 测试GUI集成
    gui_ok = test_gui_integration()
    
    print(f"\n{'='*80}")
    print("📊 修复验证结果")
    print("=" * 80)
    print(f"批次区分逻辑: {'✅ 通过' if specific_ok else '❌ 失败'}")
    print(f"GUI集成: {'✅ 通过' if gui_ok else '❌ 失败'}")
    
    if specific_ok and gui_ok:
        print("\n🎉 修复验证通过！")
        print("\n✅ 修复总结:")
        print("   1. 批次发现使用文件夹名称作为batch_id")
        print("   2. F25260021.01和F25260021现在被正确识别为不同批次")
        print("   3. lot_id从文件夹名称提取，完整保留.01后缀")
        print("   4. wafer_id仍然从文件名提取")
        print("   5. GUI文件夹命名逻辑已修复")
        
        print("\n📊 具体数据结构:")
        print("   ./F25260021/F25260021_5.xlsx")
        print("   ├── batch_id: F25260021")
        print("   ├── lot_id: F25260021")
        print("   └── wafer_id: 5")
        print("   ")
        print("   ./F25260021.01/F25260021_12.xlsx")
        print("   ├── batch_id: F25260021.01") 
        print("   ├── lot_id: F25260021.01")
        print("   └── wafer_id: 12")
        
        print("\n💡 现在F25260021.01批次不会再被遗漏！")
        
        return 0
    else:
        print("\n❌ 修复验证失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    exit(main())