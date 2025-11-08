#!/usr/bin/env python3
"""
Visualize Vehicle 1-2 Waypoints on SUMO Map
Loads waypoints from CSV and marks them as POIs on SUMO network
"""

import traci
import pandas as pd
import sumolib
import os
import time
import json

# Configuration
SCENARIO_CSV = 'scenarios/vehicle_1_2_first_2000.csv'
SUMO_CONFIG_DIR = 'veh_1_2_sumo_config'
SUMO_CONFIG_FILE = 'osm.sumocfg'
NUM_WAYPOINTS = 2000  # Use first 2000 points
MAX_POIS_TO_DISPLAY = 500  # Limit POIs for performance (show every Nth waypoint)

def load_waypoints(original_dir):
    """Load waypoints from CSV"""
    # Use absolute path or relative to original directory
    csv_path = os.path.join(original_dir, SCENARIO_CSV)
    if not os.path.exists(csv_path):
        # Try relative path
        csv_path = SCENARIO_CSV
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {SCENARIO_CSV}. Please create it first.")
    
    print(f"📋 Loading waypoints from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Use first NUM_WAYPOINTS
    waypoints_df = df.head(NUM_WAYPOINTS)
    print(f"✅ Loaded {len(waypoints_df)} waypoints")
    
    # Load metadata
    metadata_file = os.path.join(original_dir, 'scenarios/vehicle_1_2_metadata.json')
    if not os.path.exists(metadata_file):
        metadata_file = 'scenarios/vehicle_1_2_metadata.json'
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    vehicle1_id = metadata['source_vehicle']
    vehicle2_id = metadata['destination_vehicle']
    
    print(f"📊 Vehicle Pair: {vehicle1_id} ↔ {vehicle2_id}")
    print(f"📍 Coordinate bounds:")
    print(f"   Lat: {metadata['coordinate_bounds']['min_lat']:.6f} to {metadata['coordinate_bounds']['max_lat']:.6f}")
    print(f"   Lon: {metadata['coordinate_bounds']['min_lon']:.6f} to {metadata['coordinate_bounds']['max_lon']:.6f}")
    
    return waypoints_df, vehicle1_id, vehicle2_id

def convert_gps_to_sumo_coords(net, lat, lon):
    """Convert GPS coordinates to SUMO coordinates"""
    try:
        x, y = net.convertLonLat2XY(lon, lat)
        return x, y
    except Exception as e:
        print(f"⚠️ GPS conversion error: {e}")
        return None, None

def visualize_waypoints():
    """Main visualization function"""
    print("="*70)
    print("VEHICLE 1-2 WAYPOINT VISUALIZATION")
    print("="*70)
    
    # Store original directory
    original_dir = os.getcwd()
    
    try:
        # Load waypoints BEFORE changing directory
        print(f"\n📂 Loading from: {os.getcwd()}")
        waypoints_df, vehicle1_id, vehicle2_id = load_waypoints(original_dir)
        
        # Change to SUMO config directory
        os.chdir(SUMO_CONFIG_DIR)
        print(f"\n📂 Working directory: {os.getcwd()}")
        
        # Load SUMO network
        print(f"\n🗺️ Loading SUMO network...")
        net = sumolib.net.readNet('osm.net.xml.gz')
        print(f"✅ Network loaded: {len(net.getEdges())} edges")
        
        # Start SUMO
        print(f"\n🚀 Starting SUMO-GUI...")
        sumo_cmd = ["sumo-gui", "-c", SUMO_CONFIG_FILE, "--start", "--quit-on-end"]
        traci.start(sumo_cmd)
        time.sleep(3)
        print("✅ SUMO-GUI started")
        
        # Convert waypoints and add POIs
        print(f"\n📍 Converting waypoints and adding POIs...")
        print(f"   Note: Showing every {len(waypoints_df) // MAX_POIS_TO_DISPLAY}th waypoint for performance")
        source_pois = []
        dest_pois = []
        
        poi_step = max(1, len(waypoints_df) // MAX_POIS_TO_DISPLAY)
        
        for idx, row in waypoints_df.iterrows():
            # Sample waypoints for POI display (too many POIs slow down SUMO)
            if idx % poi_step != 0:
                continue
            # Source vehicle waypoints (Vehicle 1)
            src_lat = row['Latitude_source']
            src_lon = row['Longitude_source']
            src_x, src_y = convert_gps_to_sumo_coords(net, src_lat, src_lon)
            
            if src_x is not None and src_y is not None:
                poi_id = f"src_wp_{idx}"
                traci.poi.add(poi_id, src_x, src_y, 
                             color=(0, 0, 255, 200),  # Blue for source
                             poiType="source_waypoint", 
                             layer=100)
                source_pois.append((idx, src_x, src_y, src_lat, src_lon))
            
            # Destination vehicle waypoints (Vehicle 2)
            dest_lat = row['Latitude_destination']
            dest_lon = row['Longitude_destination']
            dest_x, dest_y = convert_gps_to_sumo_coords(net, dest_lat, dest_lon)
            
            if dest_x is not None and dest_y is not None:
                poi_id = f"dest_wp_{idx}"
                traci.poi.add(poi_id, dest_x, dest_y,
                             color=(255, 0, 0, 200),  # Red for destination
                             poiType="destination_waypoint",
                             layer=100)
                dest_pois.append((idx, dest_x, dest_y, dest_lat, dest_lon))
            
            # Progress indicator
            if (idx + 1) % 100 == 0:
                print(f"   Processed {idx + 1}/{len(waypoints_df)} waypoints...")
        
        print(f"\n✅ Added {len(source_pois)} source waypoints (Vehicle {vehicle1_id} - Blue)")
        print(f"✅ Added {len(dest_pois)} destination waypoints (Vehicle {vehicle2_id} - Red)")
        
        # Add trajectory lines (optional - can be commented out for performance)
        print(f"\n📈 Adding trajectory lines...")
        if len(source_pois) > 1:
            # Source trajectory (blue line)
            source_coords = [(x, y) for _, x, y, _, _ in source_pois]
            traci.polygon.add(f"src_trajectory", source_coords,
                             color=(0, 0, 255, 100),  # Semi-transparent blue
                             fill=False,
                             lineWidth=2,
                             layer=50)
            print(f"   ✅ Source trajectory line added")
        
        if len(dest_pois) > 1:
            # Destination trajectory (red line)
            dest_coords = [(x, y) for _, x, y, _, _ in dest_pois]
            traci.polygon.add(f"dest_trajectory", dest_coords,
                             color=(255, 0, 0, 100),  # Semi-transparent red
                             fill=False,
                             lineWidth=2,
                             layer=50)
            print(f"   ✅ Destination trajectory line added")
        
        # Calculate and display statistics
        print(f"\n📊 Waypoint Statistics:")
        distances = []
        for i in range(min(len(source_pois), len(dest_pois))):
            src_x, src_y = source_pois[i][1], source_pois[i][2]
            dest_x, dest_y = dest_pois[i][1], dest_pois[i][2]
            dist = ((src_x - dest_x)**2 + (src_y - dest_y)**2)**0.5
            distances.append(dist)
        
        if distances:
            print(f"   Distance range: {min(distances):.1f}m - {max(distances):.1f}m")
            print(f"   Mean distance: {sum(distances)/len(distances):.1f}m")
        
        # Fit view to waypoints
        print(f"\n🔍 Adjusting view to waypoints...")
        if source_pois and dest_pois:
            all_x = [p[1] for p in source_pois + dest_pois]
            all_y = [p[2] for p in source_pois + dest_pois]
            
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            
            # Set view (this might not work in all SUMO versions, but try)
            try:
                traci.gui.setOffset("View #0", center_x, center_y)
                traci.gui.setZoom("View #0", -5000)  # Adjust zoom level
                print(f"   ✅ View adjusted to center: ({center_x:.1f}, {center_y:.1f})")
            except:
                print(f"   ⚠️ Could not programmatically adjust view - please zoom manually")
        
        print(f"\n" + "="*70)
        print("✅ VISUALIZATION COMPLETE")
        print("="*70)
        print(f"\n📋 Summary:")
        print(f"   • Source waypoints (Vehicle {vehicle1_id}): {len(source_pois)} points (Blue)")
        print(f"   • Destination waypoints (Vehicle {vehicle2_id}): {len(dest_pois)} points (Red)")
        print(f"   • Trajectory lines: Added")
        print(f"\n💡 Tips:")
        print(f"   • Blue dots = Vehicle {vehicle1_id} waypoints")
        print(f"   • Red dots = Vehicle {vehicle2_id} waypoints")
        print(f"   • Zoom in/out to see details")
        print(f"   • POIs are on layer 100, trajectories on layer 50")
        print(f"\n⏸ Keeping SUMO-GUI open... Press Ctrl+C to exit")
        
        # Keep simulation running
        step = 0
        while step < 100:  # Run for a few steps to keep GUI open
            try:
                traci.simulationStep()
                step += 1
                time.sleep(0.1)
            except KeyboardInterrupt:
                print("\n\n⏹ Stopping visualization...")
                break
            except Exception as e:
                print(f"\n⚠️ Error: {e}")
                break
        
        # Keep GUI open until user closes
        print("\n✅ Visualization ready. SUMO-GUI will stay open.")
        print("   Close SUMO-GUI window when done viewing waypoints.")
        
        while traci.simulation.getMinExpectedNumber() > 0:
            try:
                traci.simulationStep()
                time.sleep(0.1)
            except:
                break
                
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        try:
            traci.close()
        except:
            pass
        os.chdir(original_dir)
        print("\n✅ Cleanup complete")

if __name__ == "__main__":
    visualize_waypoints()

