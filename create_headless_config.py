#!/usr/bin/env python3
"""
Create Headless SUMO Configuration

Modifies the existing SUMO configuration for headless simulation
by removing GUI-specific settings and optimizing for background operation.
"""

import os
import xml.etree.ElementTree as ET

def create_headless_config(input_config_path="sumo-config/osm.sumocfg", 
                          output_config_path="sumo-config/osm_headless.sumocfg"):
    """Create a headless version of SUMO configuration"""
    
    if not os.path.exists(input_config_path):
        raise FileNotFoundError(f"Input config not found: {input_config_path}")
    
    # Read existing config
    tree = ET.parse(input_config_path)
    root = tree.getroot()
    
    # Remove GUI-only section
    gui_only = root.find('gui_only')
    if gui_only is not None:
        root.remove(gui_only)
    
    # Modify report settings for headless mode
    report = root.find('report')
    if report is not None:
        report.set('verbose', 'false')
        report.set('no-step-log', 'true')
        report.set('duration-log.statistics', 'false')
    
    # Add headless-specific optimizations
    processing = root.find('processing')
    if processing is not None:
        processing.set('ignore-route-errors', 'true')
        processing.set('no-warnings', 'true')
    
    # Save headless config
    tree.write(output_config_path)
    print(f"✅ Created headless config: {output_config_path}")
    
    # Read and verify the output
    with open(output_config_path, 'r') as f:
        content = f.read()
        print("\n📋 Headless Configuration Contents:")
        print(content)
    
    return output_config_path

def verify_sumo_files():
    """Verify required SUMO files exist"""

    required_files = [
        "sumo-config/osm.net.xml.gz",
        "sumo-config/osm_pt.rou.xml",
        "sumo-config/osm.bicycle.trips.xml",
        "sumo-config/osm.bus.trips.xml",
        "sumo-config/osm.motorcycle.trips.xml",
        "sumo-config/osm.passenger.trips.xml",
        "sumo-config/osm.pedestrian.rou.xml",
        "sumo-config/osm.truck.trips.xml"
    ]
    
    print("\n🔍 Verifying SUMO Files:")

    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️ Missing files: {missing_files}")
        return False
    
    print("\n✅ All required SUMO files found")
    return True

if __name__ == "__main__":
    
    print("🚀 Creating Headless SUMO Configuration")
    
    try:
        # Create headless config
        config_path = create_headless_config()
        
        # Verify files
        if verify_sumo_files():
            print("\n🎯 Headless simulation ready!")
            print(f"   Configuration: {config_path}")
        else:
            print("\n⚠️ Some files missing - check your SUMO installation")
            
    except Exception as e:
        print(f"❌ Error: {e}")