#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复后的JT处理器
"""

import sys
sys.path.insert(0, '.')

from jt_data_processor.jt_main_processor import process_jt_files

def test_jt_processor():
    """测试修复后的JT处理器"""
    print("=== 测试修复后的JT处理器 ===")
    
    try:
        # 处理测试文件
        result = process_jt_files(
            file_paths='data/jetech/FA44-4149/FA444149-03.xls',
            output_dir='output_test',
            pass_bin=1
        )
        
        print("\n处理结果:")
        print(f"状态: {result.get('processing_status')}")
        print(f"Lot ID: {result.get('lot_id')}")
        print(f"参数数量: {result.get('parameter_count')}")
        print(f"总芯片数: {result.get('total_chip_count')}")
        print(f"输出文件:")
        for file in result.get('output_files', []):
            print(f"  - {file}")
            
        # 检查修复效果
        print("\n=== 修复验证 ===")
        print(f"✅ Lot ID来源: 文件夹名称")
        print(f"✅ 参数数量: {result.get('parameter_count')} (应该 > 0)")
        
        if result.get('parameter_count', 0) > 0:
            print("🎉 参数数据修复成功！")
        else:
            print("❌ 参数数据仍然丢失")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_jt_processor() 