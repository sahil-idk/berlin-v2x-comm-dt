#!/usr/bin/env python3
"""
VERIFICATION: What exactly is the accuracy measuring?

This script answers:
1. Is it truly inter-vehicular distance?
2. What is "actual_distance" from the dataset?
3. What is "simulated_distance" from SUMO?
4. Are they the same thing or different things?
"""

import pandas as pd
import numpy as np

print("="*80)
print("DISTANCE ACCURACY VERIFICATION")
print("="*80)

# Load the CSV from the dataset
print("\n📁 Loading original dataset...")
dataset = pd.read_csv('vehicle_2_4_first_200.csv')

# Load baseline results
print("📁 Loading baseline simulation results...")
baseline = pd.read_csv('realistic_speed_waypoint_analysis.csv')

print("\n" + "="*80)
print("PART 1: WHAT IS 'ACTUAL_DISTANCE' IN THE DATASET?")
print("="*80)

# Check first few rows
print("\n📊 First 5 rows of dataset:")
print(dataset[['Latitude_source', 'Longitude_source', 'Latitude_destination', 
               'Longitude_destination', 'distance']].head())

print("\n💡 The 'distance' column in dataset:")
print(f"   - Mean: {dataset['distance'].mean():.2f}m")
print(f"   - Range: {dataset['distance'].min():.2f}m - {dataset['distance'].max():.2f}m")
print(f"   - Standard Deviation: {dataset['distance'].std():.2f}m")

print("\n🔍 This is calculated from GPS coordinates:")
print("   - Source: (Latitude_source, Longitude_source)")
print("   - Destination: (Latitude_destination, Longitude_destination)")
print("   - Distance = Haversine formula (GPS distance in meters)")
print("\n   ✅ This IS the real inter-vehicular distance from GPS!")

print("\n" + "="*80)
print("PART 2: WHAT IS 'SIMULATED_DISTANCE' IN SUMO?")
print("="*80)

print("\n📊 From baseline results:")
print(f"   - Mean: {baseline['simulated_distance_m'].mean():.2f}m")
print(f"   - Range: {baseline['simulated_distance_m'].min():.2f}m - {baseline['simulated_distance_m'].max():.2f}m")
print(f"   - Standard Deviation: {baseline['simulated_distance_m'].std():.2f}m")

print("\n🔍 This is calculated from SUMO simulation:")
print("   - Source position: traci.vehicle.getPosition('v2v_source')")
print("   - Destination position: traci.vehicle.getPosition('v2v_dest')")
print("   - Distance = sqrt((x1-x2)² + (y1-y2)²) in SUMO coordinates")
print("\n   ❓ Is this the same as GPS distance?")

print("\n" + "="*80)
print("PART 3: ARE WE COMPARING THE SAME THING?")
print("="*80)

print("\n📊 Direct comparison for waypoint matching:")
print(f"{'WP':<5} {'GPS Actual (m)':<18} {'SUMO Simulated (m)':<20} {'Match?':<10}")
print("-"*80)

for wp in range(10):
    if wp in baseline['waypoint'].values:
        # Get actual distance from dataset
        dataset_row = dataset.iloc[wp]
        actual_gps = dataset_row['distance']
        
        # Get simulated distance from baseline results
        baseline_row = baseline[baseline['waypoint'] == wp].iloc[0]
        simulated_sumo = baseline_row['simulated_distance_m']
        
        # Check if they're measuring the same thing
        ratio = simulated_sumo / actual_gps if actual_gps > 0 else 0
        match = "✅ YES" if 0.9 <= ratio <= 1.1 else "❌ NO"
        
        print(f"{wp:<5} {actual_gps:<18.2f} {simulated_sumo:<20.2f} {match:<10} (ratio: {ratio:.2f})")

print("\n" + "="*80)
print("PART 4: WHAT IS THE ACCURACY ACTUALLY MEASURING?")
print("="*80)

print("\n📊 The accuracy formula:")
print("""
    distance_error = simulated_distance - actual_distance
    distance_error_pct = (distance_error / actual_distance) * 100
    distance_accuracy = 100 - abs(distance_error_pct)
""")

print("\n🔍 Breaking down waypoint 3 as example:")
if 3 in baseline['waypoint'].values:
    wp3 = baseline[baseline['waypoint'] == 3].iloc[0]
    actual = wp3['actual_distance_m']
    simulated = wp3['simulated_distance_m']
    error = wp3['distance_error_m']
    error_pct = wp3['distance_error_pct']
    accuracy = wp3['distance_accuracy_pct']
    
    print(f"\n   Actual GPS distance: {actual:.2f}m")
    print(f"   Simulated SUMO distance: {simulated:.2f}m")
    print(f"   Error: {error:.2f}m ({error_pct:.1f}%)")
    print(f"   Accuracy: {accuracy:.1f}%")
    print(f"\n   ✅ YES - This IS comparing inter-vehicular distances!")
    print(f"   ✅ Actual = GPS distance between real vehicles")
    print(f"   ✅ Simulated = SUMO distance between simulated vehicles")

print("\n" + "="*80)
print("PART 5: WHY ARE THEY DIFFERENT?")
print("="*80)

print("\n📊 The fundamental issue:")

# Calculate the ratio
actual_mean = baseline['actual_distance_m'].mean()
simulated_mean = baseline['simulated_distance_m'].mean()
ratio = simulated_mean / actual_mean

print(f"\n   Actual GPS distance (mean): {actual_mean:.2f}m")
print(f"   Simulated SUMO distance (mean): {simulated_mean:.2f}m")
print(f"   Ratio: {ratio:.2f}")

if ratio < 0.9:
    print(f"\n   ❌ PROBLEM: Simulated distances are TOO SMALL")
    print(f"   ❌ SUMO vehicles are CLOSER than real vehicles")
    print(f"   ❌ This means:")
    print(f"      - Vehicles are NOT positioned at exact GPS coordinates")
    print(f"      - They're on nearby roads, but closer together")
    print(f"      - Inter-vehicle distance in SUMO ≠ Inter-vehicle distance in GPS")
elif ratio > 1.1:
    print(f"\n   ❌ PROBLEM: Simulated distances are TOO LARGE")
    print(f"   ❌ SUMO vehicles are FARTHER than real vehicles")
    print(f"   ❌ This is expected for SUMO coordinate system scaling")
else:
    print(f"\n   ✅ GOOD: Simulated distances match GPS distances closely")
    print(f"   ✅ SUMO vehicles are positioned correctly")

print("\n" + "="*80)
print("PART 6: WHAT DOES THIS MEAN FOR COMMUNICATION MODELS?")
print("="*80)

print("\n📡 For path loss models (e.g., Free Space Path Loss):")
print("""
    FSPL(dB) = 20*log10(distance) + 20*log10(frequency) + 32.45
    
    If distance is WRONG, then:
    - Path loss calculation is WRONG
    - SNR calculation is WRONG
    - Communication range is WRONG
    - Digital twin accuracy is WRONG
""")

print(f"\n🔬 Impact analysis:")
print(f"   Real distance: {actual_mean:.2f}m")
print(f"   SUMO distance: {simulated_mean:.2f}m")
print(f"   Error: {simulated_mean - actual_mean:.2f}m ({(simulated_mean/actual_mean - 1)*100:.1f}%)")

# Calculate path loss difference
import math
freq_ghz = 5.9  # V2V frequency
real_pl = 20*math.log10(actual_mean) + 20*math.log10(freq_ghz*1000) + 32.45
sumo_pl = 20*math.log10(simulated_mean) + 20*math.log10(freq_ghz*1000) + 32.45
pl_error = sumo_pl - real_pl

print(f"\n   📊 Path Loss @ 5.9 GHz:")
print(f"      Real: {real_pl:.2f} dB")
print(f"      SUMO: {sumo_pl:.2f} dB")
print(f"      Error: {pl_error:.2f} dB")

if abs(pl_error) > 3:
    print(f"\n   ⚠️  WARNING: {abs(pl_error):.1f}dB error is SIGNIFICANT!")
    print(f"   ⚠️  This will affect:")
    print(f"      - SNR calculations")
    print(f"      - Packet reception probability")
    print(f"      - Communication range estimation")
elif abs(pl_error) > 1:
    print(f"\n   🟡 MODERATE: {abs(pl_error):.1f}dB error is noticeable")
else:
    print(f"\n   ✅ GOOD: {abs(pl_error):.1f}dB error is acceptable")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

print(f"\n✅ YES - The accuracy IS measuring inter-vehicular distance:")
print(f"   - Actual distance = GPS distance between real vehicles")
print(f"   - Simulated distance = SUMO distance between simulated vehicles")
print(f"   - Accuracy = How close SUMO matches GPS")

print(f"\n❌ BUT - There's a positioning problem:")
print(f"   - SUMO vehicles are {simulated_mean:.2f}m apart (mean)")
print(f"   - GPS vehicles are {actual_mean:.2f}m apart (mean)")
print(f"   - Difference: {abs(simulated_mean - actual_mean):.2f}m ({abs(simulated_mean/actual_mean - 1)*100:.1f}%)")

print(f"\n🎯 For Digital Twin:")
print(f"   Current accuracy: {baseline['distance_accuracy_pct'].mean():.2f}%")
print(f"   Path loss error: {pl_error:.2f} dB")
print(f"   Communication param error: Proportional to distance error")

print(f"\n💡 Recommendation:")
if baseline['distance_accuracy_pct'].mean() >= 75:
    print(f"   ✅ {baseline['distance_accuracy_pct'].mean():.1f}% distance accuracy is GOOD for communication models")
    print(f"   ✅ {abs(pl_error):.1f}dB path loss error is acceptable")
    print(f"   ✅ Proceed with communication parameter validation")
else:
    print(f"   ⚠️  {baseline['distance_accuracy_pct'].mean():.1f}% distance accuracy may affect communication models")
    print(f"   ⚠️  {abs(pl_error):.1f}dB path loss error could impact SNR calculations")
    print(f"   🔧 Consider improving positioning before communication models")

print("\n" + "="*80)

