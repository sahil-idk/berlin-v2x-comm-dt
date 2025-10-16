#!/usr/bin/env python3
"""
GPS Waypoint Visualization on SUMO OSM Map
Display 200 GPS waypoints from vehicle_2_4_first_200.csv as colored dots
"""

import traci
import pandas as pd
import sumolib
import os
import time
import sys

def gps_to_sumo_coordinates(lat, lon, net_file):
    """Convert GPS to SUMO coordinates"""
    net = sumolib.net.readNet(net_file)
    x, y = net.convertLonLat2XY(lon, lat)
    return x, y

def visualize_gps_waypoints():
    """Visualize GPS waypoints on SUMO OSM map"""
    
    print("=" * 60)
    print("GPS Waypoint Visualization on SUMO OSM Map")
    print("=" * 60)
    
    # Save original directory
    original_dir = os.getcwd()
    
    # Change to berlin-sumo-closed-netwokr directory
    sumo_dir = 'berlin-sumo-closed-netwokr'
    if not os.path.exists(sumo_dir):
        print(f"❌ Error: Directory '{sumo_dir}' not found!")
        print(f"   Current directory: {original_dir}")
        return
    
    os.chdir(sumo_dir)
    print(f"✅ Changed to directory: {os.getcwd()}")
    
    # Check required files
    if not os.path.exists('osm.sumocfg'):
        print("❌ Error: osm.sumocfg not found!")
        os.chdir(original_dir)
        return
    
    if not os.path.exists('osm.net.xml.gz'):
        print("❌ Error: osm.net.xml.gz not found!")
        os.chdir(original_dir)
        return
    
    # Start SUMO-GUI with existing configuration
    sumo_cmd = [
        "sumo-gui",
        "-c", "osm.sumocfg",
        "--start",  # Auto-start simulation
        "--quit-on-end"  # Keep GUI open after simulation ends
    ]
    
    print("\n🚀 Starting SUMO-GUI with osm.sumocfg...")
    try:
        traci.start(sumo_cmd)
        time.sleep(2)
        print("✅ SUMO-GUI started successfully")
    except Exception as e:
        print(f"❌ Failed to start SUMO-GUI: {e}")
        os.chdir(original_dir)
        return
    
    try:
        # Load GPS data
        csv_file = '../vehicle_2_4_first_200.csv'
        print(f"\n📋 Loading GPS data from {csv_file}...")
        
        if not os.path.exists(csv_file):
            print(f"❌ Error: {csv_file} not found!")
            traci.close()
            os.chdir(original_dir)
            return
        
        df = pd.read_csv(csv_file)
        print(f"✅ Loaded {len(df)} GPS points")
        print(f"   Columns: {', '.join(df.columns[:10])}...")
        
        # Get network file path
        net_file = 'osm.net.xml.gz'
        
        # Pre-load network for coordinate conversion
        print(f"\n🗺️  Loading SUMO network: {net_file}")
        net = sumolib.net.readNet(net_file)
        print("✅ Network loaded successfully")
        
        # Add waypoints as POIs
        print(f"\n📍 Adding {len(df)} GPS waypoint pairs as visual dots...")
        print("   Blue dots = Vehicle 2 (Source)")
        print("   Red dots = Vehicle 4 (Destination)")
        
        added_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Source vehicle (Vehicle 2) - Blue dots
                src_lat = row['Latitude_source']
                src_lon = row['Longitude_source']
                src_x, src_y = net.convertLonLat2XY(src_lon, src_lat)
                
                # Add POI for Vehicle 2 waypoint
                traci.poi.add(
                    f"v2_waypoint_{idx}",
                    src_x, src_y,
                    color=(0, 0, 255, 255),  # Blue
                    poiType="Vehicle_2_Waypoint",
                    layer=100,
                    width=3.0,
                    height=3.0
                )
                
                # Destination vehicle (Vehicle 4) - Red dots
                dst_lat = row['Latitude_destination']
                dst_lon = row['Longitude_destination']
                dst_x, dst_y = net.convertLonLat2XY(dst_lon, dst_lat)
                
                # Add POI for Vehicle 4 waypoint
                traci.poi.add(
                    f"v4_waypoint_{idx}",
                    dst_x, dst_y,
                    color=(255, 0, 0, 255),  # Red
                    poiType="Vehicle_4_Waypoint",
                    layer=100,
                    width=3.0,
                    height=3.0
                )
                
                added_count += 2
                
                if (idx + 1) % 50 == 0:
                    print(f"   Progress: {idx+1}/{len(df)} waypoint pairs added")
                    
            except Exception as e:
                print(f"⚠️  Warning: Failed to add waypoint {idx}: {e}")
                continue
        
        print(f"✅ Added all {added_count} waypoints ({added_count//2} pairs)")
        
        # Run simulation for a few steps to render everything
        print("\n🎨 Rendering waypoints in SUMO-GUI...")
        for step in range(10):
            traci.simulationStep()
            time.sleep(0.1)
        
        print("\n" + "=" * 60)
        print("✅ Visualization Complete!")
        print("=" * 60)
        print("\n📺 SUMO-GUI is now showing:")
        print("   ✓ Berlin OSM map with roads")
        print("   ✓ Blue dots: Vehicle 2 GPS waypoints (200 points)")
        print("   ✓ Red dots: Vehicle 4 GPS waypoints (200 points)")
        print("   ✓ Background traffic (if simulation time allows)")
        print("\n🔍 You can:")
        print("   • Zoom in/out to inspect waypoint density")
        print("   • Pan around to see the trajectory path")
        print("   • Verify waypoints are on/near roads")
        print("\n⏸️  Keeping simulation running...")
        print("   Close SUMO-GUI window when done inspecting")
        
        # Keep simulation running until user closes GUI
        try:
            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                time.sleep(0.1)
        except traci.exceptions.FatalTraCIError:
            pass
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
        
        traci.close()
        print("\n✅ Visualization closed")
        
    except Exception as e:
        print(f"\n❌ Error during visualization: {e}")
        import traceback
        traceback.print_exc()
        try:
            traci.close()
        except:
            pass
    finally:
        # Return to original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    visualize_gps_waypoints()

