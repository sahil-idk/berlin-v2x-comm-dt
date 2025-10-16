#!/usr/bin/env python3
"""
Create Berlin network for SUMO from OSM data
"""

import os
import subprocess
import sys

def create_berlin_network():
    """Create Berlin network from OSM data"""
    print("=== CREATING BERLIN NETWORK FOR SUMO ===\n")
    
    # Berlin bounding box (from PC2 data analysis)
    # Latitude: 52.469215 to 52.516930
    # Longitude: 13.236472 to 13.377472
    
    # Extend the bounding box slightly for better coverage
    min_lat = 52.46
    max_lat = 52.52
    min_lon = 13.23
    max_lon = 13.38
    
    print(f"Berlin bounding box:")
    print(f"  Latitude: {min_lat} to {max_lat}")
    print(f"  Longitude: {min_lon} to {max_lon}")
    
    # Check if SUMO tools are available
    try:
        result = subprocess.run(['netconvert', '--version'], capture_output=True, text=True)
        print(f"SUMO netconvert version: {result.stdout.strip()}")
    except FileNotFoundError:
        print("ERROR: SUMO tools not found. Please install SUMO and add to PATH.")
        print("Download from: https://sumo.dlr.de/docs/Downloads.php")
        return False
    
    # Create OSM file using overpass API
    overpass_query = f"""
    [out:xml][timeout:60];
    (
      way["highway"~"^(primary|secondary|tertiary|residential|trunk|motorway)$"]({min_lat},{min_lon},{max_lat},{max_lon});
      relation["highway"~"^(primary|secondary|tertiary|residential|trunk|motorway)$"]({min_lat},{min_lon},{max_lat},{max_lon});
    );
    out geom;
    """
    
    print("\nDownloading OSM data for Berlin...")
    try:
        import requests
        response = requests.post('https://overpass-api.de/api/interpreter', 
                               data={'data': overpass_query}, 
                               timeout=120)
        
        if response.status_code == 200:
            with open('berlin.osm', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("OSM data downloaded successfully!")
        else:
            print(f"Error downloading OSM data: {response.status_code}")
            return False
            
    except ImportError:
        print("ERROR: requests library not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'requests'])
        print("Please run the script again after installation.")
        return False
    except Exception as e:
        print(f"Error downloading OSM data: {e}")
        return False
    
    # Convert OSM to SUMO network
    print("\nConverting OSM to SUMO network...")
    netconvert_cmd = [
        'netconvert',
        '--osm-files', 'berlin.osm',
        '--output-file', 'berlin_network.net.xml',
        '--geometry.remove',
        '--remove-edges.isolated',
        '--roundabouts.guess',
        '--ramps.guess',
        '--junctions.join',
        '--tls.guess-signals',
        '--tls.discard-simple',
        '--tls.set',
        '--tls.default-type', 'actuated'
    ]
    
    try:
        result = subprocess.run(netconvert_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Network conversion successful!")
            print(f"Network file created: berlin_network.net.xml")
        else:
            print(f"Network conversion failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error converting network: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_berlin_network()
    if success:
        print("\n✅ Berlin network created successfully!")
        print("Next steps:")
        print("1. Run the TraCI simulation script")
        print("2. Launch SUMO GUI with the configuration")
    else:
        print("\n❌ Network creation failed!")
