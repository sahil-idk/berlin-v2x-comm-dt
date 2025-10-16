#!/usr/bin/env python3
"""
Ultimate V2V Simulation - Direct Vehicle Control Without moveToXY
This version adds custom vehicles that we fully control without relying on moveToXY
"""

import traci
import pandas as pd
import sumolib
import os
import time
import math

def gps_to_sumo_coordinates(net, lat, lon):
    """Convert GPS coordinates to SUMO coordinates"""
    return net.convertLonLat2XY(lon, lat)

def find_valid_edge_near_point(net, x, y, search_radius=100):
    """Find a valid edge near the given coordinates"""
    edges = net.getNeighboringEdges(x, y, r=search_radius)
    if edges:
        # Return the closest edge
        closest_edge = min(edges, key=lambda e: e[1])
        return closest_edge[0].getID()
    return None

def run_ultimate_v2v_simulation():
    """Run V2V simulation with directly added and controlled vehicles"""
    print("=" * 60)
    print("Ultimate V2V Simulation - Direct Vehicle Control")
    print("=" * 60)
    
    # Load GPS data
    print("📋 Loading GPS data...")
    try:
        df = pd.read_csv('vehicle_2_4_first_200.csv')
        waypoints = df.head(30).to_dict('records')  # Use 30 waypoints
        print(f"✅ Loaded {len(waypoints)} GPS waypoints")
    except Exception as e:
        print(f"❌ Error loading GPS data: {e}")
        return
    
    # Load SUMO network
    print("🗺️ Loading SUMO network...")
    try:
        net_file = os.path.join('berlin-sumo-closed-netwokr', 'osm.net.xml.gz')
        net = sumolib.net.readNet(net_file)
        print(f"✅ Network loaded: {len(net.getEdges())} edges")
    except Exception as e:
        print(f"❌ Error loading network: {e}")
        return
    
    # Change to SUMO directory
    original_dir = os.getcwd()
    os.chdir('berlin-sumo-closed-netwokr')
    
    try:
        # Start SUMO-GUI
        print("🚀 Starting SUMO-GUI...")
        sumo_cmd = ["sumo-gui", "-c", "osm.sumocfg"]
        traci.start(sumo_cmd)
        time.sleep(2)
        print("✅ SUMO-GUI started successfully")
        
        # Add POI markers for waypoints
        print("📍 Adding POI markers...")
        for i, wp in enumerate(waypoints):
            # Source waypoint (blue)
            src_lat, src_lon = float(wp['Latitude_source']), float(wp['Longitude_source'])
            src_x, src_y = gps_to_sumo_coordinates(net, src_lat, src_lon)
            traci.poi.add(f"src_poi_{i}", src_x, src_y, (0, 0, 255, 150), "circle", 2.0, 100)
            
            # Destination waypoint (red)
            dest_lat, dest_lon = float(wp['Latitude_destination']), float(wp['Longitude_destination'])
            dest_x, dest_y = gps_to_sumo_coordinates(net, dest_lat, dest_lon)
            traci.poi.add(f"dest_poi_{i}", dest_x, dest_y, (255, 0, 0, 150), "circle", 2.0, 100)
        
        print(f"✅ Added {len(waypoints) * 2} POI markers")
        
        # Get a valid edge from first waypoint
        first_wp = waypoints[0]
        src_lat, src_lon = float(first_wp['Latitude_source']), float(first_wp['Longitude_source'])
        src_x, src_y = gps_to_sumo_coordinates(net, src_lat, src_lon)
        
        valid_edge = find_valid_edge_near_point(net, src_x, src_y)
        
        if not valid_edge:
            print("❌ Could not find valid edge for vehicle placement")
            return
        
        print(f"📍 Using edge: {valid_edge}")
        
        # Create simple route with just this edge
        route_id = "v2v_route"
        traci.route.add(route_id, [valid_edge])
        print(f"✅ Created route: {route_id}")
        
        # Add our custom vehicles
        print("🚗 Adding custom V2V vehicles...")
        
        # Define custom vehicle types
        traci.vehicletype.copy("DEFAULT_VEHTYPE", "v2v_source_type")
        traci.vehicletype.setColor("v2v_source_type", (0, 0, 255, 255))  # Blue
        traci.vehicletype.setLength("v2v_source_type", 4.5)
        traci.vehicletype.setWidth("v2v_source_type", 1.8)
        traci.vehicletype.setMaxSpeed("v2v_source_type", 20.0)  # Slow speed
        
        traci.vehicletype.copy("DEFAULT_VEHTYPE", "v2v_dest_type")
        traci.vehicletype.setColor("v2v_dest_type", (255, 0, 0, 255))  # Red
        traci.vehicletype.setLength("v2v_dest_type", 4.5)
        traci.vehicletype.setWidth("v2v_dest_type", 1.8)
        traci.vehicletype.setMaxSpeed("v2v_dest_type", 20.0)  # Slow speed
        
        # Add source vehicle
        source_vehicle_id = "v2v_source"
        try:
            traci.vehicle.add(source_vehicle_id, route_id, typeID="v2v_source_type", 
                            depart="now", departPos="0", departSpeed="0", 
                            departLane="best")
            print(f"✅ Added source vehicle: {source_vehicle_id}")
        except Exception as e:
            print(f"❌ Failed to add source vehicle: {e}")
            return
        
        # Add destination vehicle
        dest_vehicle_id = "v2v_dest"
        try:
            traci.vehicle.add(dest_vehicle_id, route_id, typeID="v2v_dest_type",
                            depart="now", departPos="20", departSpeed="0",
                            departLane="best")
            print(f"✅ Added destination vehicle: {dest_vehicle_id}")
        except Exception as e:
            print(f"❌ Failed to add destination vehicle: {e}")
            return
        
        # Run simulation steps to insert vehicles
        print("⏳ Inserting vehicles into simulation...")
        for _ in range(10):
            traci.simulationStep()
            time.sleep(0.1)
        
        # Check if vehicles are in simulation
        vehicle_ids = traci.vehicle.getIDList()
        print(f"Current vehicles in simulation: {vehicle_ids}")
        
        if source_vehicle_id not in vehicle_ids or dest_vehicle_id not in vehicle_ids:
            print("❌ Vehicles not found in simulation after insertion")
            return
        
        print("✅ Both vehicles successfully inserted!")
        
        # Set vehicle speeds to very slow for visibility
        traci.vehicle.setSpeed(source_vehicle_id, 5.0)  # 5 m/s
        traci.vehicle.setSpeed(dest_vehicle_id, 4.0)  # 4 m/s (slightly slower)
        
        # Set lane change mode to prevent lane changes
        traci.vehicle.setLaneChangeMode(source_vehicle_id, 0b000000000000)
        traci.vehicle.setLaneChangeMode(dest_vehicle_id, 0b000000000000)
        
        print("🎯 Starting V2V simulation...")
        print("=" * 60)
        
        step_count = 0
        max_steps = 1000
        
        while step_count < max_steps:
            traci.simulationStep()
            step_count += 1
            
            # Check if vehicles still exist
            current_vehicles = traci.vehicle.getIDList()
            
            if source_vehicle_id not in current_vehicles:
                print(f"⚠️ Source vehicle disappeared at step {step_count}")
                break
            
            if dest_vehicle_id not in current_vehicles:
                print(f"⚠️ Dest vehicle disappeared at step {step_count}")
                break
            
            # Calculate distance every 30 steps
            if step_count % 30 == 0:
                try:
                    src_pos = traci.vehicle.getPosition(source_vehicle_id)
                    dest_pos = traci.vehicle.getPosition(dest_vehicle_id)
                    distance = math.sqrt((src_pos[0] - dest_pos[0])**2 + (src_pos[1] - dest_pos[1])**2)
                    
                    src_speed = traci.vehicle.getSpeed(source_vehicle_id)
                    dest_speed = traci.vehicle.getSpeed(dest_vehicle_id)
                    
                    print(f"Step {step_count:4d} | Distance: {distance:6.2f}m | "
                          f"Src Speed: {src_speed:5.2f}m/s | Dest Speed: {dest_speed:5.2f}m/s")
                    
                except Exception as e:
                    print(f"⚠️ Error calculating distance: {e}")
            
            time.sleep(0.03)  # Small delay for better visibility
        
        print("\n✅ Simulation completed!")
        print("=" * 60)
        print("🔍 Check SUMO-GUI:")
        print(f"   - {source_vehicle_id} (BLUE car) should be visible")
        print(f"   - {dest_vehicle_id} (RED car) should be visible")
        print("   - Both cars should be moving slowly on the road")
        print("   - Blue and red dots show the GPS waypoints")
        print("=" * 60)
        
        # Keep simulation running for inspection
        print("\n⏸️ Simulation paused for inspection...")
        print("   Close SUMO-GUI window when done")
        
        try:
            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n⏹️ Simulation stopped by user")
        
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            traci.close()
        except:
            pass
        os.chdir(original_dir)
        print("✅ SUMO simulation stopped")

if __name__ == "__main__":
    run_ultimate_v2v_simulation()

