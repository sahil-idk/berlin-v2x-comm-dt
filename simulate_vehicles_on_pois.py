#!/usr/bin/env python3
"""
TraCI Vehicle Simulation on Lane-Mapped POIs
Simulates vehicles directly on GPS waypoints that are mapped to lanes
"""

import traci
import pandas as pd
import sumolib
import os
import time
import json
import math

def find_nearest_lane(net, x, y, max_radius=50):
    """Find nearest lane to given x,y coordinates"""
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
                best_pos, best_dist = edge.getClosestLanePosDist((x, y))
                best_lane_idx = 0  # Use first lane by default
            except:
                best_pos = edge.getLength() / 2
    
    if closest_edge:
        return closest_edge.getID(), best_lane_idx, best_pos, min_dist
    
    return None, None, None, float('inf')

def simulate_vehicles_on_pois():
    """Simulate vehicles directly on lane-mapped POI points"""
    
    print("=" * 70)
    print("TraCI Vehicle Simulation on Lane-Mapped POIs")
    print("=" * 70)
    
    original_dir = os.getcwd()
    os.chdir('berlin-sumo-closed-netwokr')
    
    # Load network
    print("\n🗺️  Loading SUMO network...")
    net_file = 'osm.net.xml.gz'
    net = sumolib.net.readNet(net_file)
    print(f"✅ Network loaded: {len(net.getEdges())} edges")
    
    # Load GPS data - FIRST 10 POINTS
    print("\n📋 Loading GPS data (first 10 points)...")
    df = pd.read_csv('../vehicle_2_4_first_200.csv')
    waypoints_df = df.head(10)
    print(f"✅ Loaded {len(waypoints_df)} GPS waypoints")
    
    # Start SUMO-GUI with simple config
    sumo_cmd = ["sumo-gui", "-c", "osm.sumocfg", "--start"]
    print("\n🚀 Starting SUMO-GUI...")
    traci.start(sumo_cmd)
    time.sleep(3)
    
    print("\n📍 Mapping GPS coordinates to lanes and adding POIs...")
    print("-" * 70)
    
    lane_mapped_points = []
    
    for idx, row in waypoints_df.iterrows():
        print(f"\nPoint {idx + 1}/10:")
        
        # Vehicle 2 (Source) - Blue
        src_lat = row['Latitude_source']
        src_lon = row['Longitude_source']
        src_x, src_y = net.convertLonLat2XY(src_lon, src_lat)
        
        print(f"  Vehicle 2 (Blue):")
        print(f"    GPS: ({src_lat:.6f}, {src_lon:.6f})")
        print(f"    SUMO coords: ({src_x:.2f}, {src_y:.2f})")
        
        # Find nearest lane
        edge_id, lane_idx, pos, dist = find_nearest_lane(net, src_x, src_y)
        
        if edge_id and dist < 50:  # Only use points close to roads
            lane_id = f"{edge_id}_{lane_idx}"
            print(f"    ✅ Mapped to lane: {lane_id}")
            print(f"       Position: {pos:.2f}m along lane")
            print(f"       Distance from road: {dist:.2f}m")
            
            # Add POI at mapped position
            traci.poi.add(
                f"src_poi_{idx}",
                src_x, src_y,
                color=(0, 0, 255, 255),  # Blue
                poiType="Source_Waypoint",
                layer=100
            )
            
            lane_mapped_points.append({
                'index': idx,
                'vehicle': 2,
                'gps_lat': src_lat,
                'gps_lon': src_lon,
                'sumo_x': src_x,
                'sumo_y': src_y,
                'edge_id': edge_id,
                'lane_id': lane_id,
                'position': pos,
                'distance_from_road': dist,
                'mapped': True
            })
        else:
            print(f"    ❌ Too far from road (distance: {dist:.2f}m)")
        
        # Vehicle 4 (Destination) - Red
        dst_lat = row['Latitude_destination']
        dst_lon = row['Longitude_destination']
        dst_x, dst_y = net.convertLonLat2XY(dst_lon, dst_lat)
        
        print(f"  Vehicle 4 (Red):")
        print(f"    GPS: ({dst_lat:.6f}, {dst_lon:.6f})")
        print(f"    SUMO coords: ({dst_x:.2f}, {dst_y:.2f})")
        
        edge_id, lane_idx, pos, dist = find_nearest_lane(net, dst_x, dst_y)
        
        if edge_id and dist < 50:  # Only use points close to roads
            lane_id = f"{edge_id}_{lane_idx}"
            print(f"    ✅ Mapped to lane: {lane_id}")
            print(f"       Position: {pos:.2f}m along lane")
            print(f"       Distance from road: {dist:.2f}m")
            
            # Add POI at mapped position
            traci.poi.add(
                f"dst_poi_{idx}",
                dst_x, dst_y,
                color=(255, 0, 0, 255),  # Red
                poiType="Dest_Waypoint",
                layer=100
            )
            
            lane_mapped_points.append({
                'index': idx,
                'vehicle': 4,
                'gps_lat': dst_lat,
                'gps_lon': dst_lon,
                'sumo_x': dst_x,
                'sumo_y': dst_y,
                'edge_id': edge_id,
                'lane_id': lane_id,
                'position': pos,
                'distance_from_road': dist,
                'mapped': True
            })
        else:
            print(f"    ❌ Too far from road (distance: {dist:.2f}m)")
    
    print(f"\n✅ Added {len(lane_mapped_points)} lane-mapped POIs")
    
    # Now simulate vehicles using moveToXY on the lane-mapped points
    print("\n🚗 Adding vehicles and simulating movement...")
    
    # Add vehicles
    traci.vehicle.add("sourceVehicle", "route0", typeID="vType1")
    traci.vehicle.add("destVehicle", "route0", typeID="vType1")
    
    # Set vehicle colors
    traci.vehicle.setColor("sourceVehicle", (0, 0, 255, 255))  # Blue
    traci.vehicle.setColor("destVehicle", (255, 0, 0, 255))   # Red
    
    # Set vehicle sizes
    traci.vehicle.setLength("sourceVehicle", 4.5)
    traci.vehicle.setWidth("sourceVehicle", 1.8)
    traci.vehicle.setLength("destVehicle", 4.5)
    traci.vehicle.setWidth("destVehicle", 1.8)
    
    print("✅ Vehicles added to simulation")
    
    # Simulate movement through lane-mapped points
    print("\n🎯 Starting vehicle movement simulation...")
    
    step = 0
    max_steps = 300
    point_index = 0
    
    while step < max_steps and point_index < len(lane_mapped_points):
        traci.simulationStep()
        step += 1
        
        # Move vehicles to next waypoint every 30 steps
        if step % 30 == 0 and point_index < len(lane_mapped_points):
            current_point = lane_mapped_points[point_index]
            
            if current_point['vehicle'] == 2:  # Source vehicle
                try:
                    # Move source vehicle to waypoint
                    traci.vehicle.moveToXY(
                        "sourceVehicle",
                        "dummy",  # edge
                        0,  # lane
                        current_point['sumo_x'],
                        current_point['sumo_y'],
                        angle=0,
                        keepRoute=0,
                        matchThreshold=100
                    )
                    print(f"Step {step}: Moved source vehicle to point {point_index}")
                except Exception as e:
                    print(f"Step {step}: Failed to move source vehicle: {e}")
            
            elif current_point['vehicle'] == 4:  # Destination vehicle
                try:
                    # Move destination vehicle to waypoint
                    traci.vehicle.moveToXY(
                        "destVehicle",
                        "dummy",  # edge
                        0,  # lane
                        current_point['sumo_x'],
                        current_point['sumo_y'],
                        angle=0,
                        keepRoute=0,
                        matchThreshold=100
                    )
                    print(f"Step {step}: Moved dest vehicle to point {point_index}")
                except Exception as e:
                    print(f"Step {step}: Failed to move dest vehicle: {e}")
            
            point_index += 1
        
        # Calculate distance between vehicles every 10 steps
        if step % 10 == 0:
            try:
                src_pos = traci.vehicle.getPosition("sourceVehicle")
                dest_pos = traci.vehicle.getPosition("destVehicle")
                
                distance = math.sqrt((src_pos[0] - dest_pos[0])**2 + (src_pos[1] - dest_pos[1])**2)
                print(f"Step {step}: Distance between vehicles: {distance:.2f}m")
            except:
                pass
        
        time.sleep(0.1)
    
    print("\n✅ Simulation completed!")
    print("🔍 Check SUMO-GUI:")
    print("  - Blue vehicle should follow blue POI markers")
    print("  - Red vehicle should follow red POI markers")
    print("  - Both vehicles should stay on roads")
    print(f"  - Processed {point_index} waypoints")
    
    # Keep GUI open for inspection
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
    
    # Save results
    with open('lane_mapped_simulation_results.json', 'w') as f:
        json.dump(lane_mapped_points, f, indent=2)
    print(f"\n💾 Results saved to: lane_mapped_simulation_results.json")

if __name__ == "__main__":
    simulate_vehicles_on_pois()
