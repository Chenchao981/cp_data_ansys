#!/usr/bin/env python3

import pandas as pd
import numpy as np

# Read the latest files
cleaned_df = pd.read_csv('output/combined_cleaned_20250722_1611.csv')
yield_df = pd.read_csv('output/combined_yield_20250722_1611.csv')

print('=== Verification of Fixed Yield Calculation ===')
print('Wafer 1 Analysis:')

# Filter for wafer 1 data
wafer1_cleaned = cleaned_df[cleaned_df['Wafer_ID'] == 1]
wafer1_yield = yield_df[yield_df['Wafer_ID'] == 1].iloc[0]

print(f'Total chips: {len(wafer1_cleaned)}')
print(f'Good chips (Bin=1): {len(wafer1_cleaned[wafer1_cleaned["Bin"] == 1])}')
print(f'Bad chips (Bin!=1): {len(wafer1_cleaned[wafer1_cleaned["Bin"] != 1])}')
print()

# Test key parameters
test_params = ['IGSSF_5', 'DC_KELVIN_B1', 'VTH1', 'RDSON']

for param in test_params:
    # Calculate from good chips only, excluding fail values
    good_chips = wafer1_cleaned[(wafer1_cleaned['Bin'] == 1) & (wafer1_cleaned[param] < 9999)]
    if len(good_chips) > 0:
        expected_avg = good_chips[param].mean()
    else:
        expected_avg = 0
    
    actual_yield_value = wafer1_yield[param]
    
    print(f'{param}:')
    print(f'  Expected (good chips avg): {expected_avg:.4f}')
    print(f'  Actual (from yield.csv):   {actual_yield_value:.4f}')
    print(f'  Match: {"✓" if abs(expected_avg - actual_yield_value) < 0.001 else "✗"}')
    print()

print('=== Overall Verification Results ===')
all_match = True
for param in test_params:
    good_chips = wafer1_cleaned[(wafer1_cleaned['Bin'] == 1) & (wafer1_cleaned[param] < 9999)]
    expected_avg = good_chips[param].mean() if len(good_chips) > 0 else 0
    actual_yield_value = wafer1_yield[param]
    
    if abs(expected_avg - actual_yield_value) >= 0.001:
        all_match = False
        break

print(f'✅ All parameters match expected values: {all_match}')