#!/usr/bin/env python3
"""
GPS to Lane Mapping - Two Point Validation
Maps GPS coordinates to actual road lanes in SUMO to ensure on-road placement
"""

import traci
import pandas as pd
import sumolib
import os
import time
import json

def find_nearest_lane(net, x, y, max_radius=50):
    """
    Find nearest lane to given x,y coordinates
    Returns: (edge_id, lane_index, position, distance)
    """
    # Search for nearest edge within radius
    edges = net.getNeighboringEdges(x, y, r=max_radius)
    
    if not edges:
        return None, None, None, float('inf')
    
    # Get closest edge
    closest_edge = None
    min_dist = float('inf')
    best_lane_idx = 0
    best_pos = 0
    
    for edge, dist in edges:
        if dist < min_dist:
            min_dist = dist
            closest_edge = edge
            
            # Find position along edge
            try:
                # Project point onto edge shape to get position
                best_pos, best_dist = edge.getClosestLanePosDist((x, y))
                best_lane_idx = 0  # Use first lane by default
            except:
                # Fallback: use middle of edge
                best_pos = edge.getLength() / 2
    
    if closest_edge:
        return closest_edge.getID(), best_lane_idx, best_pos, min_dist
    
    return None, None, None, float('inf')

def map_gps_to_lanes():
    """Map GPS waypoints to road lanes"""
    
    print("=" * 70)
    print("GPS to Lane Mapping - Two Point Validation")
    print("=" * 70)
    
    original_dir = os.getcwd()
    os.chdir('berlin-sumo-closed-netwokr')
    
    # Load network
    print("\n🗺️  Loading SUMO network...")
    net_file = 'osm.net.xml.gz'
    net = sumolib.net.readNet(net_file)
    print(f"✅ Network loaded: {len(net.getEdges())} edges")
    
    # Load GPS data - ONLY FIRST 2 POINTS
    print("\n📋 Loading GPS data (first 2 points only)...")
    df = pd.read_csv('../vehicle_2_4_first_200.csv')
    test_df = df.head(2)  # Only first 2 points
    print(f"✅ Loaded {len(test_df)} GPS points for testing")
    
    # Start SUMO-GUI
    sumo_cmd = ["sumo-gui", "-c", "osm.sumocfg", "--start"]
    print("\n🚀 Starting SUMO-GUI...")
    traci.start(sumo_cmd)
    time.sleep(3)
    
    # Process each GPS point
    print("\n📍 Mapping GPS coordinates to road lanes...")
    print("-" * 70)
    
    mapping_results = []
    
    for idx, row in test_df.iterrows():
        print(f"\nPoint {idx + 1}/2:")
        
        # Vehicle 2 (Source) - Blue
        src_lat = row['Latitude_source']
        src_lon = row['Longitude_source']
        src_x, src_y = net.convertLonLat2XY(src_lon, src_lat)
        
        print(f"  Vehicle 2 (Blue):")
        print(f"    GPS: ({src_lat:.6f}, {src_lon:.6f})")
        print(f"    SUMO coords: ({src_x:.2f}, {src_y:.2f})")
        
        # Find nearest lane
        edge_id, lane_idx, pos, dist = find_nearest_lane(net, src_x, src_y)
        
        if edge_id:
            lane_id = f"{edge_id}_{lane_idx}"
            print(f"    ✅ Mapped to lane: {lane_id}")
            print(f"       Position: {pos:.2f}m along lane")
            print(f"       Distance from road: {dist:.2f}m")
            
            # Add POI on lane (guaranteed on-road)
            try:
                traci.poi.add(
                    f"v2_point_{idx}",
                    x=0, y=0,  # Not used when lane is specified
                    color=(0, 0, 255, 255),  # Blue
                    poiType="Vehicle_2_Lane_Mapped",
                    layer=100,
                    lane=lane_id,
                    pos=pos
                )
                print(f"    ✅ POI added on road")
                
                mapping_results.append({
                    'point': idx,
                    'vehicle': 2,
                    'gps_lat': src_lat,
                    'gps_lon': src_lon,
                    'sumo_x': src_x,
                    'sumo_y': src_y,
                    'edge': edge_id,
                    'lane': lane_id,
                    'position': pos,
                    'distance_from_road': dist,
                    'mapped': True
                })
            except Exception as e:
                print(f"    ❌ Failed to add POI: {e}")
                mapping_results.append({
                    'point': idx,
                    'vehicle': 2,
                    'gps_lat': src_lat,
                    'gps_lon': src_lon,
                    'mapped': False,
                    'error': str(e)
                })
        else:
            print(f"    ❌ No nearby road found (searched {50}m radius)")
            mapping_results.append({
                'point': idx,
                'vehicle': 2,
                'gps_lat': src_lat,
                'gps_lon': src_lon,
                'mapped': False,
                'reason': 'No nearby road'
            })
        
        # Vehicle 4 (Destination) - Red
        dst_lat = row['Latitude_destination']
        dst_lon = row['Longitude_destination']
        dst_x, dst_y = net.convertLonLat2XY(dst_lon, dst_lat)
        
        print(f"  Vehicle 4 (Red):")
        print(f"    GPS: ({dst_lat:.6f}, {dst_lon:.6f})")
        print(f"    SUMO coords: ({dst_x:.2f}, {dst_y:.2f})")
        
        edge_id, lane_idx, pos, dist = find_nearest_lane(net, dst_x, dst_y)
        
        if edge_id:
            lane_id = f"{edge_id}_{lane_idx}"
            print(f"    ✅ Mapped to lane: {lane_id}")
            print(f"       Position: {pos:.2f}m along lane")
            print(f"       Distance from road: {dist:.2f}m")
            
            try:
                traci.poi.add(
                    f"v4_point_{idx}",
                    x=0, y=0,
                    color=(255, 0, 0, 255),  # Red
                    poiType="Vehicle_4_Lane_Mapped",
                    layer=100,
                    lane=lane_id,
                    pos=pos
                )
                print(f"    ✅ POI added on road")
                
                mapping_results.append({
                    'point': idx,
                    'vehicle': 4,
                    'gps_lat': dst_lat,
                    'gps_lon': dst_lon,
                    'sumo_x': dst_x,
                    'sumo_y': dst_y,
                    'edge': edge_id,
                    'lane': lane_id,
                    'position': pos,
                    'distance_from_road': dist,
                    'mapped': True
                })
            except Exception as e:
                print(f"    ❌ Failed to add POI: {e}")
                mapping_results.append({
                    'point': idx,
                    'vehicle': 4,
                    'gps_lat': dst_lat,
                    'gps_lon': dst_lon,
                    'mapped': False,
                    'error': str(e)
                })
        else:
            print(f"    ❌ No nearby road found")
            mapping_results.append({
                'point': idx,
                'vehicle': 4,
                'gps_lat': dst_lat,
                'gps_lon': dst_lon,
                'mapped': False,
                'reason': 'No nearby road'
            })
    
    # Render
    print("\n🎨 Rendering mapped waypoints...")
    for _ in range(10):
        traci.simulationStep()
        time.sleep(0.1)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Mapping Summary")
    print("=" * 70)
    
    successful = sum(1 for r in mapping_results if r.get('mapped', False))
    total = len(mapping_results)
    
    print(f"Successfully mapped: {successful}/{total} waypoints")
    print(f"Success rate: {successful/total*100:.1f}%")
    
    # Show distance statistics
    distances = [r['distance_from_road'] for r in mapping_results if r.get('mapped')]
    if distances:
        print(f"\nDistance from road statistics:")
        print(f"  Min: {min(distances):.2f}m")
        print(f"  Max: {max(distances):.2f}m")
        print(f"  Avg: {sum(distances)/len(distances):.2f}m")
    
    print("\n✅ Two-point validation complete!")
    print("🔍 Inspect SUMO-GUI:")
    print("   - Blue and red dots should now be ON roads")
    print("   - Zoom in to verify lane placement")
    print("   - Check if mapping distances are acceptable")
    
    # Keep running
    print("\n⏸️  Close SUMO-GUI when done inspecting...")
    try:
        while traci.simulation.getMinExpectedNumber() >= 0:
            traci.simulationStep()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except:
        pass
    
    traci.close()
    os.chdir(original_dir)
    
    # Save mapping results
    with open('lane_mapping_results.json', 'w') as f:
        json.dump(mapping_results, f, indent=2)
    print(f"\n💾 Mapping results saved to: lane_mapping_results.json")

if __name__ == "__main__":
    map_gps_to_lanes()

