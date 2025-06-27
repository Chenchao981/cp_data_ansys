#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试JT Excel文件结构
"""

import pandas as pd

def debug_jt_excel():
    """调试JT Excel文件的结构"""
    file_path = 'data/jetech/FA44-4149/FA444149-03.xls'
    
    print("=== 调试JT Excel文件结构 ===")
    print(f"文件路径: {file_path}")
    
    try:
        # 1. 检查所有工作表
        xls = pd.ExcelFile(file_path)
        print(f"\n工作表列表: {xls.sheet_names}")
        
        # 2. 检查DUT_DATA工作表的原始结构
        print("\n=== DUT_DATA工作表原始结构 ===")
        full_df = pd.read_excel(file_path, sheet_name='DUT_DATA', header=None)
        
        print(f"总行数: {len(full_df)}")
        print(f"总列数: {len(full_df.columns)}")
        
        # 显示前10行
        print("\n前10行数据:")
        for i in range(min(10, len(full_df))):
            print(f"第{i+1}行: {full_df.iloc[i].tolist()[:15]}...")  # 只显示前15列
        
        # 3. 分析列名和数据结构
        print("\n=== 列名分析 ===")
        headers = full_df.iloc[0].tolist()
        print(f"列名数量: {len(headers)}")
        print(f"列名列表: {headers}")
        
        # 4. 找到TEST_NUM列的位置
        if 'TEST_NUM' in headers:
            test_num_idx = headers.index('TEST_NUM')
            print(f"\nTEST_NUM列位置: {test_num_idx}")
            print(f"TEST_NUM及右边的列: {headers[test_num_idx:]}")
        else:
            print("\n❌ 未找到TEST_NUM列")
        
        # 5. 检查基础列
        basic_columns = ['DUT_NO', 'SOFT_BIN', 'X_COORD', 'Y_COORD', 'TEST_NUM']
        print(f"\n=== 基础列检查 ===")
        for col in basic_columns:
            if col in headers:
                idx = headers.index(col)
                print(f"✅ {col}: 位置 {idx}")
            else:
                print(f"❌ {col}: 未找到")
        
        # 6. 检查Summary information工作表
        print("\n=== Summary information工作表 ===")
        try:
            summary_df = pd.read_excel(file_path, sheet_name='Summary information', header=None)
            print(f"Summary information行数: {len(summary_df)}")
            
            if len(summary_df) > 8:
                print(f"第8行: {summary_df.iloc[7].tolist()}")
                print(f"第9行: {summary_df.iloc[8].tolist()}")
            else:
                print("❌ Summary information行数不足")
                
        except Exception as e:
            print(f"❌ 读取Summary information失败: {e}")
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_jt_excel() 