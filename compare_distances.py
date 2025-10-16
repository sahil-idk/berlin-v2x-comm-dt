#!/usr/bin/env python3
"""Compare baseline vs combined optimal simulated distances"""

import pandas as pd
import numpy as np

print("="*80)
print("DISTANCE COMPARISON: Baseline vs Combined Optimal")
print("="*80)

# Load baseline
baseline = pd.read_csv('realistic_speed_waypoint_analysis.csv')
print("\n📊 BASELINE (v2v_realistic_speed_simulation.py - 66.52% accuracy):")
print(f"   Simulated Distance Mean: {baseline['simulated_distance_m'].mean():.2f}m")
print(f"   Simulated Distance Range: {baseline['simulated_distance_m'].min():.2f}m - {baseline['simulated_distance_m'].max():.2f}m")
print(f"   Simulated Distance Std: {baseline['simulated_distance_m'].std():.2f}m")

# Load combined optimal
combined = pd.read_csv('combined_optimal_results.csv')
print("\n📊 COMBINED OPTIMAL (72.78% accuracy):")
print(f"   Simulated Distance Mean: {combined['simulated_distance_m'].mean():.2f}m")
print(f"   Simulated Distance Range: {combined['simulated_distance_m'].min():.2f}m - {combined['simulated_distance_m'].max():.2f}m")
print(f"   Simulated Distance Std: {combined['simulated_distance_m'].std():.2f}m")

# Actual distance stats
print("\n📊 ACTUAL GPS DISTANCE (from dataset):")
print(f"   Actual Distance Mean: {baseline['actual_distance_m'].mean():.2f}m")
print(f"   Actual Distance Range: {baseline['actual_distance_m'].min():.2f}m - {baseline['actual_distance_m'].max():.2f}m")

# Side-by-side comparison for first 10 waypoints
print("\n" + "="*80)
print("FIRST 10 WAYPOINTS COMPARISON:")
print("="*80)
print(f"{'WP':<4} {'Actual':<10} {'Baseline Sim':<15} {'Combined Sim':<15} {'Difference':<12}")
print("-"*80)

# Find matching waypoints
for wp in range(10):
    if wp in baseline['waypoint'].values and wp in combined['waypoint'].values:
        actual = baseline[baseline['waypoint']==wp]['actual_distance_m'].iloc[0]
        base_sim = baseline[baseline['waypoint']==wp]['simulated_distance_m'].iloc[0]
        comb_sim = combined[combined['waypoint']==wp]['simulated_distance_m'].iloc[0]
        diff = comb_sim - base_sim
        print(f"{wp:<4} {actual:<10.2f} {base_sim:<15.2f} {comb_sim:<15.2f} {diff:<12.2f}")

# Analysis
print("\n" + "="*80)
print("DIAGNOSIS:")
print("="*80)

base_mean = baseline['simulated_distance_m'].mean()
comb_mean = combined['simulated_distance_m'].mean()
actual_mean = baseline['actual_distance_m'].mean()

print(f"\n1. Expected Simulated Distance (uncalibrated SUMO): ~35-40m")
print(f"2. Actual Baseline Simulated: {base_mean:.2f}m")
print(f"3. Actual Combined Simulated: {comb_mean:.2f}m")
print(f"4. Actual GPS Distance: {actual_mean:.2f}m")

print(f"\n📌 KEY FINDINGS:")

if base_mean < 30:
    print(f"   ⚠️  BOTH simulations have low simulated distances (~{base_mean:.0f}m)")
    print(f"   ⚠️  This is a POSITIONING issue, not a calibration issue")
    print(f"   ⚠️  Vehicles are NOT at GPS coordinates - they're just on nearby roads")
    print(f"\n   💡 ROOT CAUSE:")
    print(f"      - Vehicles follow routes through the area")
    print(f"      - But don't align to exact GPS waypoints")
    print(f"      - Inter-vehicle distance is based on route positions, not GPS positions")
    print(f"\n   🎯 TO FIX:")
    print(f"      - Use moveToXY() to force GPS positions (hard - vehicles disappear)")
    print(f"      - OR accept route-based simulation (easier - different metric)")
else:
    print(f"   ✅ Baseline has correct simulated distances (~{base_mean:.0f}m)")
    if comb_mean < 30:
        print(f"   ❌ Combined Optimal broke something (only ~{comb_mean:.0f}m)")
        print(f"   🔧 Need to debug route generation or vehicle positioning")

# Check calibration effectiveness
print(f"\n📊 CALIBRATION EFFECTIVENESS:")
base_calib_dist = baseline['simulated_distance_m'] * 0.607
comb_calib_dist = combined['calibrated_distance_m']

base_calib_mean = base_calib_dist.mean()
comb_calib_mean = comb_calib_dist.mean()

print(f"   Baseline after calibration (0.607): {base_calib_mean:.2f}m")
print(f"   Combined after calibration (adaptive): {comb_calib_mean:.2f}m")
print(f"   Actual GPS distance (target): {actual_mean:.2f}m")

print(f"\n   Baseline error: {abs(base_calib_mean - actual_mean):.2f}m")
print(f"   Combined error: {abs(comb_calib_mean - actual_mean):.2f}m")

if abs(comb_calib_mean - actual_mean) < abs(base_calib_mean - actual_mean):
    print(f"   ✅ Combined Optimal calibration is better!")
else:
    print(f"   ❌ Baseline calibration is better (simpler is better when base is wrong)")

print("\n" + "="*80)

