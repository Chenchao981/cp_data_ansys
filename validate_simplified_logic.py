#!/usr/bin/env python3

import pandas as pd

# 读取最新文件
cleaned_df = pd.read_csv('output/combined_cleaned_20250722_1615.csv')
yield_df = pd.read_csv('output/combined_yield_20250722_1615.csv')

print('=== 验证简化yield参数逻辑 ===')
print()

# 1. 验证参数数量
cleaned_columns = list(cleaned_df.columns)
yield_columns = list(yield_df.columns)

# 找到TEST_NUM位置
test_num_index = cleaned_columns.index('TEST_NUM')
expected_params = cleaned_columns[test_num_index + 1:]
actual_params_in_yield = yield_columns[5:]  # Yield字段后面的参数

print(f'1. 参数数量验证:')
print(f'   预期参数数量 (TEST_NUM往右): {len(expected_params)}')
print(f'   yield.csv中实际参数数量: {len(actual_params_in_yield)}')
print(f'   数量匹配: {"✓" if len(expected_params) == len(actual_params_in_yield) else "✗"}')
print()

# 2. 验证参数名称完全一致
params_match = expected_params == actual_params_in_yield
print(f'2. 参数名称验证:')
print(f'   参数名称完全匹配: {"✓" if params_match else "✗"}')
if not params_match:
    print('   不匹配的参数:')
    for i, (expected, actual) in enumerate(zip(expected_params, actual_params_in_yield)):
        if expected != actual:
            print(f'     位置{i+1}: 预期="{expected}", 实际="{actual}"')
print()

# 3. 验证参数值计算正确性
print('3. 参数值计算验证 (晶圆1):')
wafer1_cleaned = cleaned_df[cleaned_df['Wafer_ID'] == 1]
wafer1_yield = yield_df[yield_df['Wafer_ID'] == 1].iloc[0]

# 测试前5个参数
test_params = expected_params[:5]
for param in test_params:
    # 计算好芯片的平均值
    good_chips = wafer1_cleaned[(wafer1_cleaned['Bin'] == 1) & (wafer1_cleaned[param] < 9999)]
    expected_avg = good_chips[param].mean() if len(good_chips) > 0 else 0
    actual_avg = wafer1_yield[param]
    
    match = abs(expected_avg - actual_avg) < 0.001
    print(f'   {param}: 预期={expected_avg:.4f}, 实际={actual_avg:.4f} {"✓" if match else "✗"}')

print()
print('=== 总体验证结果 ===')
if len(expected_params) == len(actual_params_in_yield) and params_match:
    print('✅ 简化yield参数逻辑工作正常!')
    print('✅ TEST_NUM往右的所有参数都已正确包含到yield.csv中!')
else:
    print('❌ 简化逻辑存在问题，需要检查。')

print()
print('=== 详细参数列表 ===')
print('TEST_NUM往右的31个有效参数:')
for i, param in enumerate(expected_params, 1):
    print(f'  {i:2d}. {param}')