#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复当前output目录中的spec文件
交换LimitL和LimitU的数值，因为它们被颠倒了
"""

import pandas as pd
import glob
from pathlib import Path

def fix_spec_files():
    """
    修复所有output目录中的spec文件
    """
    print("🔧 修复JT公司spec文件中的LimitL和LimitU颠倒问题")
    print("=" * 60)
    
    # 查找output目录中的spec文件
    spec_files = glob.glob("output/*_spec_*.csv")
    
    if not spec_files:
        print("❌ 未找到需要修复的spec文件")
        return
    
    for spec_file in spec_files:
        print(f"🔍 处理文件: {spec_file}")
        
        try:
            # 读取CSV文件
            df = pd.read_csv(spec_file)
            
            # 检查是否有LimitL和LimitU行
            if 'Parameter' not in df.columns:
                print(f"  ⚠️ 跳过: 文件格式不匹配")
                continue
            
            # 查找LimitL和LimitU的行索引
            limit_l_idx = None
            limit_u_idx = None
            
            for idx, row in df.iterrows():
                if row['Parameter'] == 'LimitL':
                    limit_l_idx = idx
                elif row['Parameter'] == 'LimitU':
                    limit_u_idx = idx
            
            if limit_l_idx is None or limit_u_idx is None:
                print(f"  ⚠️ 跳过: 未找到LimitL或LimitU行")
                continue
            
            # 备份原文件
            backup_file = spec_file.replace('.csv', '_backup.csv')
            df.to_csv(backup_file, index=False)
            print(f"  💾 备份已保存: {backup_file}")
            
            # 显示修复前的部分数据
            print(f"  📊 修复前示例:")
            print(f"    UIS_KELVIN: LimitL={df.loc[limit_l_idx, 'UIS_KELVIN']}, LimitU={df.loc[limit_u_idx, 'UIS_KELVIN']}")
            print(f"    UIS_BVDSS:  LimitL={df.loc[limit_l_idx, 'UIS_BVDSS']}, LimitU={df.loc[limit_u_idx, 'UIS_BVDSS']}")
            
            # 交换LimitL和LimitU的数值 (保留Parameter列)
            df_fixed = df.copy()
            
            # 获取所有非Parameter列的列名
            value_columns = [col for col in df.columns if col != 'Parameter']
            
            # 交换数值
            for col in value_columns:
                limit_l_value = df.loc[limit_l_idx, col]
                limit_u_value = df.loc[limit_u_idx, col]
                
                df_fixed.loc[limit_l_idx, col] = limit_u_value  # 原来的LimitU值现在是LimitL
                df_fixed.loc[limit_u_idx, col] = limit_l_value  # 原来的LimitL值现在是LimitU
            
            # 显示修复后的部分数据
            print(f"  ✅ 修复后示例:")
            print(f"    UIS_KELVIN: LimitL={df_fixed.loc[limit_l_idx, 'UIS_KELVIN']}, LimitU={df_fixed.loc[limit_u_idx, 'UIS_KELVIN']}")
            print(f"    UIS_BVDSS:  LimitL={df_fixed.loc[limit_l_idx, 'UIS_BVDSS']}, LimitU={df_fixed.loc[limit_u_idx, 'UIS_BVDSS']}")
            
            # 保存修复后的文件
            df_fixed.to_csv(spec_file, index=False)
            print(f"  💾 修复完成，已保存到: {spec_file}")
            print()
            
        except Exception as e:
            print(f"  ❌ 修复失败: {e}")
    
    print("🎉 所有spec文件修复完成!")

def verify_fix():
    """
    验证修复结果
    """
    print("\n🔍 验证修复结果:")
    print("=" * 30)
    
    spec_files = glob.glob("output/*_spec_*.csv")
    
    for spec_file in spec_files:
        if "_backup" in spec_file:
            continue
            
        print(f"📄 验证文件: {spec_file}")
        
        try:
            df = pd.read_csv(spec_file)
            
            # 查找LimitL和LimitU行
            limit_l_row = df[df['Parameter'] == 'LimitL']
            limit_u_row = df[df['Parameter'] == 'LimitU']
            
            if not limit_l_row.empty and not limit_u_row.empty:
                print("  主要参数验证:")
                
                # 检查UIS_KELVIN (应该是下限-1, 上限1)
                if 'UIS_KELVIN' in df.columns:
                    l_val = limit_l_row['UIS_KELVIN'].iloc[0]
                    u_val = limit_u_row['UIS_KELVIN'].iloc[0]
                    print(f"    UIS_KELVIN: LimitL={l_val}, LimitU={u_val} {'✅' if l_val < u_val else '❌'}")
                
                # 检查UIS_BVDSS (应该是下限20, 上限80)
                if 'UIS_BVDSS' in df.columns:
                    l_val = limit_l_row['UIS_BVDSS'].iloc[0]
                    u_val = limit_u_row['UIS_BVDSS'].iloc[0]
                    print(f"    UIS_BVDSS:  LimitL={l_val}, LimitU={u_val} {'✅' if l_val < u_val else '❌'}")
            
            print()
            
        except Exception as e:
            print(f"  ❌ 验证失败: {e}")

if __name__ == "__main__":
    fix_spec_files()
    verify_fix()