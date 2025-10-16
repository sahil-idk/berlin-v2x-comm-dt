#!/usr/bin/env python3
"""
Test script for Sidelink V2V Simulation
Verifies that all components are working correctly
"""

import os
import sys
import pandas as pd
import numpy as np
from gps_to_sumo_converter import GPSToSUMOConverter

def test_data_loading():
    """Test loading of sidelink data"""
    print("Testing data loading...")
    
    if not os.path.exists("sidelink_dataframe.parquet"):
        print("❌ sidelink_dataframe.parquet not found")
        return False
        
    try:
        df = pd.read_parquet("sidelink_dataframe.parquet")
        print(f"✅ Loaded {len(df)} records")
        
        # Check required columns
        required_cols = [
            'Latitude_source', 'Longitude_source',
            'Latitude_destination', 'Longitude_destination',
            'SNR', 'RSRP', 'RSSI', 'MCS'
        ]
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"❌ Missing columns: {missing_cols}")
            return False
            
        print("✅ All required columns present")
        return True
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
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
        # Test with sample coordinates from sumo_points.csv
        test_coords = [
            (52.494875, 13.304918333333331),
            (52.50987666666666, 13.360006666666669),
            (52.51278666666666, 13.286895)
        ]
        
        converter = GPSToSUMOConverter("sumo-config/osm.net.xml.gz")
        
        for lat, lon in test_coords:
            x, y = converter.gps_to_sumo(lat, lon)
            print(f"✅ GPS ({lat:.6f}, {lon:.6f}) -> SUMO ({x:.2f}, {y:.2f})")
            
        return True
        
    except Exception as e:
        print(f"❌ Coordinate conversion error: {e}")
        return False

def test_data_selection():
    """Test data selection for simulation"""
    print("\nTesting data selection...")
    
    try:
        df = pd.read_parquet("sidelink_dataframe.parquet")
        
        # Filter valid data
        valid_data = df.dropna(subset=[
            'Latitude_source', 'Longitude_source',
            'Latitude_destination', 'Longitude_destination'
        ])
        
        print(f"✅ {len(valid_data)} valid records found")
        
        # Test sampling
        sample_data = valid_data.sample(n=min(50, len(valid_data)), random_state=42)
        print(f"✅ Selected {len(sample_data)} records for simulation")
        
        # Check data ranges
        lat_range = (sample_data['Latitude_source'].min(), sample_data['Latitude_source'].max())
        lon_range = (sample_data['Longitude_source'].min(), sample_data['Longitude_source'].max())
        
        print(f"✅ Latitude range: {lat_range[0]:.6f} to {lat_range[1]:.6f}")
        print(f"✅ Longitude range: {lon_range[0]:.6f} to {lon_range[1]:.6f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data selection error: {e}")
        return False

def test_dependencies():
    """Test Python dependencies"""
    print("\nTesting dependencies...")
    
    required_packages = ['pandas', 'numpy', 'matplotlib', 'traci']
    
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
    print("Sidelink V2V Simulation - Component Tests")
    print("=" * 50)
    
    tests = [
        test_dependencies,
        test_data_loading,
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
        print("🎉 All tests passed! Ready to run simulation.")
        print("\nTo run the simulation:")
        print("  Windows: run_sidelink_simulation.bat")
        print("  Linux/Mac: python simple_sidelink_simulation.py")
    else:
        print("⚠️  Some tests failed. Please fix issues before running simulation.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
