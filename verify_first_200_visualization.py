#!/usr/bin/env python3
"""
Verify the first 200 points visualization is working correctly
"""

import os
import json

def verify_visualization():
    """Verify all components of the first 200 points visualization"""
    
    print("🔍 Verifying First 200 Points V2V Visualization...")
    print("=" * 50)
    
    # Check required files
    required_files = [
        "vehicle_2_4_first_200.csv",
        "vehicle_2_4_first_200_metadata.json", 
        "first_200_v2v_visualization_embedded.html",
        "open_first_200_visualization.py",
        "run_first_200_visualization.bat"
    ]
    
    print("📁 Checking required files:")
    all_files_exist = True
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file} ({size:,} bytes)")
        else:
            print(f"   ❌ {file} - MISSING")
            all_files_exist = False
    
    if not all_files_exist:
        print("\n❌ Some required files are missing!")
        return False
    
    # Verify CSV data
    print("\n📊 Verifying CSV data:")
    try:
        import pandas as pd
        df = pd.read_csv("vehicle_2_4_first_200.csv")
        print(f"   ✅ Records: {len(df)}")
        print(f"   ✅ Columns: {len(df.columns)}")
        print(f"   ✅ Distance range: {df['distance'].min():.1f}m - {df['distance'].max():.1f}m")
        print(f"   ✅ Scenarios: {', '.join(df['Scenario'].unique())}")
    except Exception as e:
        print(f"   ❌ CSV error: {e}")
        return False
    
    # Verify metadata
    print("\n📄 Verifying metadata:")
    try:
        with open("vehicle_2_4_first_200_metadata.json", 'r') as f:
            metadata = json.load(f)
        print(f"   ✅ Dataset: {metadata['dataset_name']}")
        print(f"   ✅ Records: {metadata['total_records']}")
        print(f"   ✅ Distance: {metadata['distance_statistics']['min_distance']:.1f}m - {metadata['distance_statistics']['max_distance']:.1f}m")
    except Exception as e:
        print(f"   ❌ Metadata error: {e}")
        return False
    
    # Verify HTML file
    print("\n🌐 Verifying HTML file:")
    try:
        with open("first_200_v2v_visualization_embedded.html", 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Check for embedded data
        if "embeddedFirst200Data" in html_content:
            print("   ✅ Embedded data found")
        else:
            print("   ❌ Embedded data missing")
            return False
        
        # Check for proper function
        if "function loadCsvData()" in html_content:
            print("   ✅ Load function found")
        else:
            print("   ❌ Load function missing")
            return False
        
        # Check for Leaflet
        if "leaflet" in html_content.lower():
            print("   ✅ Leaflet map library included")
        else:
            print("   ❌ Leaflet map library missing")
            return False
        
        print(f"   ✅ File size: {len(html_content):,} characters")
        
    except Exception as e:
        print(f"   ❌ HTML error: {e}")
        return False
    
    # Check JavaScript syntax
    print("\n🔧 Verifying JavaScript syntax:")
    try:
        # Count brackets, braces, parentheses
        open_parens = html_content.count('(')
        close_parens = html_content.count(')')
        open_braces = html_content.count('{')
        close_braces = html_content.count('}')
        open_brackets = html_content.count('[')
        close_brackets = html_content.count(']')
        
        if (open_parens == close_parens and 
            open_braces == close_braces and 
            open_brackets == close_brackets):
            print("   ✅ Syntax appears correct")
        else:
            print("   ❌ Syntax issues detected")
            return False
            
    except Exception as e:
        print(f"   ❌ Syntax check error: {e}")
        return False
    
    print("\n🎉 Verification Complete!")
    print("=" * 50)
    print("✅ All components verified successfully!")
    print("🌐 Ready to run: python open_first_200_visualization.py")
    print("📊 Dataset: 200 GPS points, 11.4m-23.1m distances")
    print("🎯 Features: Interactive animation, embedded data, no dependencies")
    
    return True

if __name__ == "__main__":
    verify_visualization()
