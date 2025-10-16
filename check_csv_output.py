#!/usr/bin/env python3
"""
Quick check script to verify CSV output files from calibrated simulation
"""

import os
import pandas as pd
from pathlib import Path

print("="*70)
print("CSV OUTPUT FILE CHECKER")
print("="*70)

# Current directory
current_dir = os.getcwd()
print(f"\n📁 Current directory: {current_dir}")

# Files to check
files_to_check = [
    'calibrated_distance_accuracy_analysis.csv',
    'calibrated_simulation_summary.json',
    'distance_accuracy_analysis.csv',  # From enhanced_robust
    'distance_accuracy_summary.json',   # From enhanced_robust
]

print("\n📊 Checking for output files...")
print("-"*70)

found_files = []
missing_files = []

for filename in files_to_check:
    filepath = os.path.join(current_dir, filename)
    
    if os.path.exists(filepath):
        file_size = os.path.getsize(filepath)
        file_size_kb = file_size / 1024
        
        print(f"✅ {filename}")
        print(f"   Path: {filepath}")
        print(f"   Size: {file_size_kb:.2f} KB")
        
        # If CSV, show row count
        if filename.endswith('.csv'):
            try:
                df = pd.read_csv(filepath)
                print(f"   Rows: {len(df)}")
                print(f"   Columns: {', '.join(df.columns.tolist()[:5])}{'...' if len(df.columns) > 5 else ''}")
            except Exception as e:
                print(f"   ⚠️ Could not read CSV: {e}")
        
        found_files.append(filename)
        print()
    else:
        print(f"❌ {filename} - NOT FOUND")
        missing_files.append(filename)
        print()

# Check berlin-sumo-closed-netwokr folder (old location)
print("\n📁 Checking berlin-sumo-closed-netwokr folder...")
print("-"*70)

sumo_dir = os.path.join(current_dir, 'berlin-sumo-closed-netwokr')
if os.path.exists(sumo_dir):
    for filename in files_to_check:
        filepath = os.path.join(sumo_dir, filename)
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath) / 1024
            print(f"⚠️ Found old file in SUMO folder: {filename} ({file_size:.2f} KB)")
            print(f"   Path: {filepath}")
            print(f"   (Files should now save to main directory)")
            print()

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"✅ Found: {len(found_files)} files")
print(f"❌ Missing: {len(missing_files)} files")

if found_files:
    print(f"\n📊 Found files:")
    for f in found_files:
        print(f"   - {f}")

if missing_files:
    print(f"\n⚠️ Missing files (run simulation to generate):")
    for f in missing_files:
        print(f"   - {f}")

print("\n💡 To generate CSV files:")
print("   1. Run: python v2v_enhanced_calibrated.py")
print("   2. Click 'Start Simulation' in GUI")
print("   3. Wait for simulation to complete")
print("   4. Files will be saved to:", current_dir)

print("\n✅ Check complete!")

