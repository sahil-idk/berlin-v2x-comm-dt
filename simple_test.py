#!/usr/bin/env python3
"""
Simple test for SUMO configuration
"""

import subprocess
import os

def test_files():
    """Test if all required files exist"""
    print("=== Testing Required Files ===\n")
    
    files = [
        'berlin_network.net.xml',
        'berlin_simulation.sumocfg', 
        'berlin_routes.rou.xml',
        'berlin_additional.add.xml',
        'pc2_parsed.csv'
    ]
    
    all_exist = True
    for file in files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} missing")
            all_exist = False
    
    return all_exist

def test_sumo():
    """Test SUMO installation"""
    print("\n=== Testing SUMO Installation ===\n")
    
    try:
        result = subprocess.run(['sumo', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ SUMO is installed")
            print(f"Version: {result.stdout.split('Version')[1].split('Build')[0].strip()}")
            return True
        else:
            print("❌ SUMO not working")
            return False
    except FileNotFoundError:
        print("❌ SUMO not found in PATH")
        return False

def main():
    """Main test function"""
    print("Simple SUMO Test\n")
    
    files_ok = test_files()
    sumo_ok = test_sumo()
    
    if files_ok and sumo_ok:
        print("\n✅ All tests passed!")
        print("You can now run: python working_sumo_traci.py")
    else:
        print("\n❌ Some tests failed. Please fix the issues.")
    
    return files_ok and sumo_ok

if __name__ == "__main__":
    main()
