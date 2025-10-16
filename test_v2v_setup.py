#!/usr/bin/env python3
"""
Test script for V2V Simulation Setup
Verifies that all components are working correctly
"""

import os
import sys
import pandas as pd
import numpy as np

def test_csv_loading():
    """Test loading of CSV data"""
    print("Testing CSV data loading...")
    
    if not os.path.exists("sidelink_parsed.csv"):
        print("❌ sidelink_parsed.csv not found")
        return False
        
    try:
        # Load first 1000 rows to test
        df = pd.read_csv("sidelink_parsed.csv", nrows=1000)
        print(f"✅ Loaded {len(df)} records")
        
        # Check required columns
        required_cols = ['lat', 'lon', 'Source', 'Destination', 'SNR', 'RSRP']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"❌ Missing columns: {missing_cols}")
            return False
            
        print("✅ All required columns present")
        
        # Check for valid coordinates
        valid_coords = df.dropna(subset=['lat', 'lon'])
        print(f"✅ {len(valid_coords)} records with valid coordinates")
        
        # Check Source-Destination pairs
        pairs = df.groupby(['Source', 'Destination']).size()
        print(f"✅ Found {len(pairs)} unique Source-Destination pairs")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return False

def test_sumo_config():
    """Test SUMO configuration"""
    print("\nTesting SUMO configuration...")
    
    config_files = [
        "sumo-config/osm.sumocfg",
        "sumo-config/osm.net.xml.gz"
    ]
    
    for file_path in config_files:
        if not os.path.exists(file_path):
            print(f"❌ {file_path} not found")
            return False
        print(f"✅ {file_path} exists")
        
    return True

def test_coordinate_conversion():
    """Test GPS to SUMO coordinate conversion"""
    print("\nTesting coordinate conversion...")
    
    try:
        # Test coordinates from Berlin area
        test_coords = [
            (52.513440, 13.332978),  # From CSV
            (52.513383, 13.332535),  # From CSV
            (52.520000, 13.405000)   # Berlin center
        ]
        
        def gps_to_sumo(lat, lon):
            lat_norm = (lat - 52.3) / 0.4
            lon_norm = (lon - 13.0) / 0.8
            x = lon_norm * 19873.71
            y = lat_norm * 12467.71
            return x, y
        
        for lat, lon in test_coords:
            x, y = gps_to_sumo(lat, lon)
            print(f"✅ GPS ({lat:.6f}, {lon:.6f}) -> SUMO ({x:.2f}, {y:.2f})")
            
        return True
        
    except Exception as e:
        print(f"❌ Coordinate conversion error: {e}")
        return False

def test_data_selection():
    """Test V2V scenario selection"""
    print("\nTesting V2V scenario selection...")
    
    try:
        # Load sample data
        df = pd.read_csv("sidelink_parsed.csv", nrows=5000)
        
        # Filter valid coordinates
        valid_data = df.dropna(subset=['lat', 'lon'])
        
        # Group by Source-Destination pairs
        pairs = valid_data.groupby(['Source', 'Destination']).first().reset_index()
        
        # Filter out self-communication
        valid_pairs = pairs[pairs['Source'] != pairs['Destination']]
        
        print(f"✅ {len(valid_pairs)} valid V2V pairs found")
        
        # Test selecting 50 scenarios
        selected = valid_pairs.sample(n=min(50, len(valid_pairs)), random_state=42)
        print(f"✅ Selected {len(selected)} scenarios for simulation")
        
        return True
        
    except Exception as e:
        print(f"❌ Data selection error: {e}")
        return False

def test_dependencies():
    """Test Python dependencies"""
    print("\nTesting dependencies...")
    
    required_packages = ['pandas', 'numpy', 'traci']
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            print(f"❌ {package} not available")
            return False
            
    return True

def main():
    """Run all tests"""
    print("V2V Simulation Setup - Component Tests")
    print("=" * 50)
    
    tests = [
        test_dependencies,
        test_csv_loading,
        test_sumo_config,
        test_coordinate_conversion,
        test_data_selection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Ready to run V2V simulation.")
        print("\nTo run the simulation:")
        print("  Windows: run_v2v_simulation.bat")
        print("  Linux/Mac: python simple_v2v_simulator.py")
    else:
        print("⚠️  Some tests failed. Please fix issues before running simulation.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
