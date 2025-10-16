#!/usr/bin/env python3
"""Check if dataset contains speed data"""

import pandas as pd

df = pd.read_csv('vehicle_2_4_first_200.csv')

print("=" * 70)
print("DATASET SPEED DATA CHECK")
print("=" * 70)

print(f"\n📊 Dataset Info:")
print(f"   Total Rows: {len(df)}")
print(f"   Total Columns: {len(df.columns)}")

print(f"\n📊 All Columns (first 30):")
for i, col in enumerate(df.columns[:30], 1):
    print(f"   {i}. {col}")

if len(df.columns) > 30:
    print(f"   ... and {len(df.columns) - 30} more columns")

# Search for speed-related columns
speed_cols = [col for col in df.columns if 'speed' in col.lower() or 'velocity' in col.lower()]

print(f"\n📊 Speed-Related Columns:")
if speed_cols:
    for col in speed_cols:
        print(f"   ✅ {col}")
        sample = df[col].head(5)
        print(f"      Sample values: {sample.tolist()}")
        print(f"      Mean: {df[col].mean():.2f}, Min: {df[col].min():.2f}, Max: {df[col].max():.2f}")
else:
    print("   ❌ No speed-related columns found")

# Also check for time-related columns to calculate speed
time_cols = [col for col in df.columns if 'time' in col.lower() or 'timestamp' in col.lower()]
print(f"\n📊 Time-Related Columns:")
if time_cols:
    for col in time_cols[:3]:
        print(f"   ✅ {col}")
        print(f"      Sample: {df[col].head(3).tolist()}")
else:
    print("   ❌ No time-related columns found")

# Check position columns
pos_cols = [col for col in df.columns if 'latitude' in col.lower() or 'longitude' in col.lower()]
print(f"\n📊 Position Columns:")
for col in pos_cols[:4]:
    print(f"   ✅ {col}")

print("\n" + "=" * 70)

