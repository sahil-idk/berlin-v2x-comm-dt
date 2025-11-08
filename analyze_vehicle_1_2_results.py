#!/usr/bin/env python3
"""Analyze Vehicle 1-2 communication analysis results"""

import pandas as pd
import numpy as np

df = pd.read_csv('vehicle_1_2_communication_analysis.csv')

print('='*70)
print('VEHICLE 1-2 ANALYSIS DIAGNOSTICS')
print('='*70)

print(f'\n📊 Basic Stats:')
print(f'   Total waypoints analyzed: {len(df)}')
print(f'   Waypoint range: {df["waypoint"].min()} to {df["waypoint"].max()}')

print(f'\n📏 Distance Analysis:')
print(f'   Actual distance range: {df["actual_distance_m"].min():.2f}m to {df["actual_distance_m"].max():.2f}m')
print(f'   Simulated distance range: {df["simulated_distance_m"].min():.2f}m to {df["simulated_distance_m"].max():.2f}m')
print(f'   Distance error range: {df["distance_error_m"].min():.2f}m to {df["distance_error_m"].max():.2f}m')
print(f'   Mean actual distance: {df["actual_distance_m"].mean():.2f}m')
print(f'   Mean simulated distance: {df["simulated_distance_m"].mean():.2f}m')
print(f'   Mean error: {df["distance_error_m"].mean():.2f}m')

# Calculate optimal calibration
actual_mean = df['actual_distance_m'].mean()
simulated_mean = df['simulated_distance_m'].mean()
optimal_calibration = actual_mean / simulated_mean if simulated_mean > 0 else 1.0

print(f'\n🔧 Calibration Analysis:')
print(f'   Current calibration: 1.0 (no calibration)')
print(f'   Optimal calibration factor: {optimal_calibration:.4f}')
print(f'   Old calibration factor: 0.607')

# Check if calibration helps
df['calibrated_distance'] = df['simulated_distance_m'] * 0.607
df['calibrated_error'] = df['calibrated_distance'] - df['actual_distance_m']
df['calibrated_error_pct'] = (df['calibrated_error'] / df['actual_distance_m'] * 100)
df['calibrated_accuracy'] = np.maximum(0, 100 - np.abs(df['calibrated_error_pct']))

df['optimal_calibrated_distance'] = df['simulated_distance_m'] * optimal_calibration
df['optimal_calibrated_error'] = df['optimal_calibrated_distance'] - df['actual_distance_m']
df['optimal_calibrated_error_pct'] = (df['optimal_calibrated_error'] / df['actual_distance_m'] * 100)
df['optimal_calibrated_accuracy'] = np.maximum(0, 100 - np.abs(df['optimal_calibrated_error_pct']))

print(f'\n📈 Accuracy Comparison:')
print(f'   Current (no calibration): {df["distance_accuracy_pct"].mean():.2f}%')
print(f'   With 0.607 calibration: {df["calibrated_accuracy"].mean():.2f}%')
print(f'   With optimal calibration ({optimal_calibration:.4f}): {df["optimal_calibrated_accuracy"].mean():.2f}%')

print(f'\n📋 Sample Data (first 10 waypoints):')
print(df[['waypoint', 'actual_distance_m', 'simulated_distance_m', 'distance_error_m', 
          'distance_accuracy_pct', 'calibrated_accuracy', 'optimal_calibrated_accuracy']].head(10).to_string(index=False))

print(f'\n💡 Recommendations:')
if optimal_calibration < 0.8:
    print(f'   ✅ Apply calibration factor: {optimal_calibration:.4f}')
elif optimal_calibration > 1.2:
    print(f'   ⚠️ Simulated distances are much smaller than actual - check route generation')
else:
    print(f'   ℹ️  Current calibration seems reasonable, accuracy issues may be from other factors')

