#!/usr/bin/env python3
"""
Create a standalone SUMO simulation from PC2 data
This approach generates all simulation files and runs SUMO without TraCI
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

def create_standalone_network():
    """Create a standalone network file"""
    print("Creating standalone network...")
    
    network_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<net version="1.9" junctionCornerDetail="5" limitTurnSpeed="5.5" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/net_file.xsd">
    <location netOffset="0.0,0.0" convBoundary="0.0,0.0,2000.0,2000.0" origBoundary="-10000000000.0,-10000000000.0,10000000000.0,10000000000.0" projParameter="+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"/>
    
    <!-- Junctions -->
    <junction id="junction_1" type="priority" x="0.0" y="0.0" incLanes="" intLanes="" shape="0.0,0.0 0.0,0.0"/>
    <junction id="junction_2" type="priority" x="500.0" y="0.0" incLanes="" intLanes="" shape="500.0,0.0 500.0,0.0"/>
    <junction id="junction_3" type="priority" x="1000.0" y="0.0" incLanes="" intLanes="" shape="1000.0,0.0 1000.0,0.0"/>
    <junction id="junction_4" type="priority" x="1500.0" y="0.0" incLanes="" intLanes="" shape="1500.0,0.0 1500.0,0.0"/>
    <junction id="junction_5" type="priority" x="2000.0" y="0.0" incLanes="" intLanes="" shape="2000.0,0.0 2000.0,0.0"/>
    
    <!-- Edges -->
    <edge id="edge_1" from="junction_1" to="junction_2" priority="1">
        <lane id="edge_1_0" index="0" speed="13.89" length="500.0" shape="0.0,0.0 500.0,0.0"/>
    </edge>
    <edge id="edge_2" from="junction_2" to="junction_3" priority="1">
        <lane id="edge_2_0" index="0" speed="13.89" length="500.0" shape="500.0,0.0 1000.0,0.0"/>
    </edge>
    <edge id="edge_3" from="junction_3" to="junction_4" priority="1">
        <lane id="edge_3_0" index="0" speed="13.89" length="500.0" shape="1000.0,0.0 1500.0,0.0"/>
    </edge>
    <edge id="edge_4" from="junction_4" to="junction_5" priority="1">
        <lane id="edge_4_0" index="0" speed="13.89" length="500.0" shape="1500.0,0.0 2000.0,0.0"/>
    </edge>
    
    <!-- Connections -->
    <connection from="edge_1" to="edge_2" fromLane="0" toLane="0" dir="s" state="M"/>
    <connection from="edge_2" to="edge_3" fromLane="0" toLane="0" dir="s" state="M"/>
    <connection from="edge_3" to="edge_4" fromLane="0" toLane="0" dir="s" state="M"/>
</net>'''
    
    with open('standalone_network.net.xml', 'w') as f:
        f.write(network_xml)
    
    print("✅ Standalone network created")
    return True

def create_vehicle_routes_from_pc2():
    """Create vehicle routes based on PC2 data"""
    print("Creating vehicle routes from PC2 data...")
    
    # Load PC2 data
    df = pd.read_csv('pc2_parsed.csv')
    df = df.dropna(subset=['lat', 'lon', 'speed_kmh'])
    
    # Sample data (every 100th point for performance)
    df = df.iloc[::100].reset_index(drop=True)
    
    print(f"Using {len(df)} data points for route generation")
    
    # Create routes XML
    routes_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    <!-- Vehicle types -->
    <vType id="PC2_Vehicle" accel="2.5" decel="4.5" sigma="0.5" length="4.3" maxSpeed="50"/>
    
    <!-- Main route -->
    <route id="main_route" edges="edge_1 edge_2 edge_3 edge_4"/>
    
    <!-- Vehicles with speeds from PC2 data -->
'''
    
    # Add vehicles with different speeds
    for i, (idx, row) in enumerate(df.iterrows()):
        if i >= 50:  # Limit to 50 vehicles for performance
            break
        
        speed_kmh = row['speed_kmh']
        speed_ms = max(0.1, speed_kmh / 3.6)  # Convert to m/s, minimum 0.1
        
        # Calculate departure time (spread vehicles over time)
        depart_time = i * 2  # 2 seconds between vehicles
        
        routes_xml += f'    <vehicle id="pc2_vehicle_{i}" type="PC2_Vehicle" route="main_route" depart="{depart_time}" departSpeed="{speed_ms}"/>\n'
    
    routes_xml += '</routes>'
    
    with open('standalone_routes.rou.xml', 'w') as f:
        f.write(routes_xml)
    
    print(f"✅ Created routes for {min(50, len(df))} vehicles")
    return True

def create_standalone_config():
    """Create standalone SUMO configuration"""
    print("Creating standalone configuration...")
    
    config_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
    <input>
        <net-file value="standalone_network.net.xml"/>
        <route-files value="standalone_routes.rou.xml"/>
    </input>
    
    <time>
        <begin value="0"/>
        <end value="200"/>
        <step-length value="1"/>
    </time>
    
    <processing>
        <ignore-route-errors value="true"/>
        <ignore-junction-blocker value="true"/>
    </processing>
    
    <report>
        <verbose value="true"/>
        <no-step-log value="true"/>
    </report>
    
    <gui_only>
        <start value="true"/>
    </gui_only>
</configuration>'''
    
    with open('standalone_simulation.sumocfg', 'w') as f:
        f.write(config_xml)
    
    print("✅ Standalone configuration created")
    return True

def run_standalone_simulation():
    """Run the standalone simulation"""
    print("Running standalone SUMO simulation...")
    
    import subprocess
    
    try:
        # Run SUMO GUI with the standalone configuration
        result = subprocess.run([
            'sumo-gui',
            '-c', 'standalone_simulation.sumocfg',
            '--start', 'true'
        ])
        
        if result.returncode == 0:
            print("✅ Simulation completed successfully")
        else:
            print("❌ Simulation had issues")
            
    except Exception as e:
        print(f"❌ Error running simulation: {e}")

def main():
    """Main function"""
    print("=== Creating Standalone SUMO Simulation from PC2 Data ===\n")
    
    # Check if PC2 data exists
    if not os.path.exists('pc2_parsed.csv'):
        print("❌ PC2 data file not found!")
        return False
    
    # Create all files
    create_standalone_network()
    create_vehicle_routes_from_pc2()
    create_standalone_config()
    
    print("\n✅ All files created successfully!")
    print("\nFiles created:")
    print("- standalone_network.net.xml")
    print("- standalone_routes.rou.xml") 
    print("- standalone_simulation.sumocfg")
    
    print("\nTo run the simulation:")
    print("sumo-gui -c standalone_simulation.sumocfg --start true")
    
    # Ask if user wants to run simulation
    response = input("\nDo you want to run the simulation now? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        run_standalone_simulation()
    
    return True

if __name__ == "__main__":
    main()
