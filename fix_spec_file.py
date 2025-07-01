#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复现有spec文件的脚本

将重复参数去除，并转换为正确的HH格式
"""

import pandas as pd
import sys
from pathlib import Path

def fix_spec_file(input_file: str, output_file: str):
    """修复spec文件，去除重复参数并转换格式"""
    
    print(f"🔧 开始修复spec文件: {input_file}")
    
    # 读取现有的spec文件
    try:
        df = pd.read_csv(input_file)
        print(f"📊 原始spec文件: {len(df)} 行参数")
        
        # 显示原始列名
        print(f"原始列名: {df.columns.tolist()}")
        
        # 去除重复参数（基于param列）
        if 'param' in df.columns:
            df_unique = df.drop_duplicates(subset=['param'], keep='first')
            print(f"✅ 去重后: {len(df_unique)} 行参数 (去除了 {len(df) - len(df_unique)} 个重复)")
        else:
            print("❌ 未找到param列，无法去重")
            return
        
        # 转换为HH标准格式
        if 'param' in df_unique.columns:
            # 重命名列为HH标准格式
            column_mapping = {
                'param': 'Parameter',
                'unit': 'Unit', 
                'lsl': 'LimitL',
                'usl': 'LimitU',
                'target': 'TestCond'
            }
            
            df_fixed = df_unique.rename(columns=column_mapping)
            
            # 确保列顺序正确
            expected_columns = ['Parameter', 'Unit', 'LimitL', 'LimitU', 'TestCond']
            df_fixed = df_fixed[expected_columns]
            
            print(f"🔄 转换为HH格式，列名: {df_fixed.columns.tolist()}")
        else:
            df_fixed = df_unique
        
        # 保存修复后的文件
        df_fixed.to_csv(output_file, index=False)
        print(f"✅ 修复完成，保存到: {output_file}")
        
        # 显示前几行作为验证
        print("\n📋 修复后的spec文件预览:")
        print(df_fixed.head(10).to_string(index=False))
        
        # 显示统计信息
        print(f"\n📈 统计信息:")
        print(f"- 总参数数: {len(df_fixed)}")
        print(f"- 有单位的参数: {df_fixed['Unit'].notna().sum()}")
        print(f"- 有下限的参数: {df_fixed['LimitL'].notna().sum()}")
        print(f"- 有上限的参数: {df_fixed['LimitU'].notna().sum()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

def main():
    """主函数"""
    
    # 输入文件路径
    input_file = "output/FA44-4149_spec_20250701_132617.csv"
    
    # 输出文件路径（新的时间戳）
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output/FA44-4149_spec_fixed_{timestamp}.csv"
    
    print("🚀 JT规格文件修复工具")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print("-" * 50)
    
    # 检查输入文件是否存在
    if not Path(input_file).exists():
        print(f"❌ 输入文件不存在: {input_file}")
        return 1
    
    # 执行修复
    success = fix_spec_file(input_file, output_file)
    
    if success:
        print("\n🎉 修复成功！")
        print(f"请检查修复后的文件: {output_file}")
        return 0
    else:
        print("\n💥 修复失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())