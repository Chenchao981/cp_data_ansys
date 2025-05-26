import pandas as pd

# 读取数据
df = pd.read_csv("output/FA54-5339-327A-250501@203_cleaned_20250523_153916.csv")

print("=== 基本信息 ===")
print(f"总行数: {len(df)}")
print(f"Lot_ID数量: {df['Lot_ID'].nunique()}")

print("\n=== Lot_ID列表 ===")
lots = df['Lot_ID'].unique()
for i, lot in enumerate(lots, 1):
    print(f"{i}. {lot}")

print("\n=== 每个Lot的Wafer分布 ===")
for lot in lots:
    lot_data = df[df['Lot_ID'] == lot]
    wafer_ids = sorted(lot_data['Wafer_ID'].unique())
    print(f"{lot}:")
    print(f"  Wafer_ID: {wafer_ids[0]} ~ {wafer_ids[-1]} (共{len(wafer_ids)}片)")
    
print("\n=== 测试参数 ===")
params = [col for col in df.columns if col not in ['Lot_ID', 'Wafer_ID', 'Seq', 'Bin', 'X', 'Y']]
print(f"参数列表: {params}") 