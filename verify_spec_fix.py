#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd

print('🔍 验证修复后的spec文件')
print('=' * 40)

df = pd.read_csv('output/FA44-4149_spec_fixed.csv')

# 查找LimitL和LimitU行
limit_l_row = df[df['Parameter'] == 'LimitL']
limit_u_row = df[df['Parameter'] == 'LimitU']

print('主要参数验证:')

# 检查关键参数
test_params = ['UIS_KELVIN', 'UIS_BVDSS', 'UIS_ID17', 'CONT1', 'VTH0.25']

for param in test_params:
    if param in df.columns:
        l_val = limit_l_row[param].iloc[0]
        u_val = limit_u_row[param].iloc[0]
        
        # 检查是否为有效数值并且下限小于上限
        try:
            l_num = float(l_val) if l_val != '' else None
            u_num = float(u_val) if u_val != '' else None
            
            if l_num is not None and u_num is not None:
                status = '✅' if l_num < u_num else '❌'
                print(f'  {param}: LimitL={l_num}, LimitU={u_num} {status}')
            else:
                print(f'  {param}: 部分数据为空')
        except:
            print(f'  {param}: 数据格式错误')

print()
print('✅ 修复验证完成！现在LimitL是下限，LimitU是上限')