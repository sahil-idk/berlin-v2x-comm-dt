#!/usr/bin/env python3
"""
Simplified V2V Simulation - Focus on Getting Vehicles to Appear and Move
This version prioritizes vehicle visibility and movement over complex GUI controls
"""

import traci
import pandas as pd
import sumolib
import os
import time
import math
import subprocess
import sys

def gps_to_sumo_coordinates(net, lat, lon):
    """Convert GPS coordinates to SUMO coordinates"""
    return net.convertLonLat2XY(lon, lat)

def find_nearest_lane(net, sumo_x, sumo_y, search_radius=50):
    """Find the nearest lane to given SUMO coordinates"""
    try:
        edges = net.getNeighboringEdges(sumo_x, sumo_y, r=search_radius)
        if not edges:
            return None, 0, float('inf')
        
        # Get the closest edge
        closest_edge, min_dist = min(edges, key=lambda x: x[1])
        edge_id = closest_edge.getID()
        
        # Use first lane of the edge
        lane_id = f"{edge_id}_0"
        
        # Calculate position along the lane
        pos_on_lane = closest_edge.getClosestLanePosDist(sumo_x, sumo_y)[1]
        
        return lane_id, pos_on_lane, min_dist
    except Exception as e:
        print(f"Error finding nearest lane: {e}")
        return None, 0, float('inf')

def start_sumo_simple():
    """Start SUMO-GUI with proper configuration"""
    print("🚀 Starting SUMO-GUI...")
    
    # Change to SUMO directory
    original_dir = os.getcwd()
    os.chdir('berlin-sumo-closed-netwokr')
    
    try:
        # Start SUMO-GUI
        sumo_cmd = ["sumo-gui", "-c", "osm.sumocfg", "--start"]
        traci.start(sumo_cmd)
        time.sleep(3)  # Give SUMO time to initialize
        print("✅ SUMO-GUI started successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to start SUMO: {e}")
        return False
    finally:
        os.chdir(original_dir)

def create_simple_vehicle_routes():
    """Create simple vehicle routes for our V2V vehicles"""
    print("🚗 Creating simple vehicle routes...")
    
    # Change to SUMO directory
    original_dir = os.getcwd()
    os.chdir('berlin-sumo-closed-netwokr')
    
    try:
        # Create a simple route file
        route_content = '''<routes>
    <vType id="v2v_car" accel="2.0" decel="4.5" sigma="0.5" length="4.5" minGap="2.5" maxSpeed="50" color="0,0,255"/>
    <vType id="v2v_car_dest" accel="2.0" decel="4.5" sigma="0.5" length="4.5" minGap="2.5" maxSpeed="50" color="255,0,0"/>
    <route id="simple_route" edges="-279549312"/>
    <vehicle id="sourceVehicle" type="v2v_car" route="simple_route" depart="0" departPos="0" departSpeed="max" departLane="best"/>
    <vehicle id="destVehicle" type="v2v_car_dest" route="simple_route" depart="0" departPos="10" departSpeed="max" departLane="best"/>
</routes>'''
        
        with open("v2v_simple_routes.rou.xml", "w") as f:
            f.write(route_content)
        
        print("✅ Simple routes created")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create routes: {e}")
        return False
    finally:
        os.chdir(original_dir)

def run_simple_v2v_simulation():
    """Run a simple V2V simulation with visible vehicles"""
    print("=" * 60)
    print("Simple V2V Simulation - Vehicle Visibility Focus")
    print("=" * 60)
    
    # Load GPS data
    print("📋 Loading GPS data...")
    try:
        df = pd.read_csv('vehicle_2_4_first_200.csv')
        waypoints = df.head(20).to_dict('records')  # Use first 20 points
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
    
    # Create simple routes
    if not create_simple_vehicle_routes():
        return
    
    # Start SUMO
    if not start_sumo_simple():
        return
    
    try:
        # Add POI markers for waypoints
        print("📍 Adding POI markers...")
        for i, wp in enumerate(waypoints):
            # Source waypoint (blue)
            src_lat, src_lon = float(wp['Latitude_source']), float(wp['Longitude_source'])
            src_x, src_y = gps_to_sumo_coordinates(net, src_lat, src_lon)
            traci.poi.add(f"src_poi_{i}", src_x, src_y, (0, 0, 255, 255), "circle", 3.0, 100)
            
            # Destination waypoint (red)
            dest_lat, dest_lon = float(wp['Latitude_destination']), float(wp['Longitude_destination'])
            dest_x, dest_y = gps_to_sumo_coordinates(net, dest_lat, dest_lon)
            traci.poi.add(f"dest_poi_{i}", dest_x, dest_y, (255, 0, 0, 255), "circle", 3.0, 100)
        
        print(f"✅ Added {len(waypoints) * 2} POI markers")
        
        # Wait for vehicles to be inserted
        print("⏳ Waiting for vehicles to be inserted...")
        for step in range(50):
            traci.simulationStep()
            vehicle_ids = traci.vehicle.getIDList()
            if "sourceVehicle" in vehicle_ids and "destVehicle" in vehicle_ids:
                print("✅ Both vehicles inserted successfully!")
                break
            time.sleep(0.1)
        
        # Check if vehicles are present
        vehicle_ids = traci.vehicle.getIDList()
        print(f"Current vehicles: {vehicle_ids}")
        
        if "sourceVehicle" not in vehicle_ids or "destVehicle" not in vehicle_ids:
            print("❌ Vehicles not found in simulation")
            print("Available vehicles:", vehicle_ids)
            return
        
        # Set vehicle properties for better visibility
        print("🎨 Setting vehicle properties...")
        traci.vehicle.setLength("sourceVehicle", 4.5)
        traci.vehicle.setWidth("sourceVehicle", 1.8)
        traci.vehicle.setColor("sourceVehicle", (0, 0, 255, 255))  # Blue
        
        traci.vehicle.setLength("destVehicle", 4.5)
        traci.vehicle.setWidth("destVehicle", 1.8)
        traci.vehicle.setColor("destVehicle", (255, 0, 0, 255))  # Red
        
        print("✅ Vehicle properties set")
        
        # Move vehicles through waypoints
        print("🎯 Starting vehicle movement simulation...")
        current_waypoint = 0
        step_count = 0
        max_steps = 1000
        
        while step_count < max_steps and current_waypoint < len(waypoints):
            traci.simulationStep()
            step_count += 1
            
            # Move vehicles every 30 steps
            if step_count % 30 == 0 and current_waypoint < len(waypoints):
                wp = waypoints[current_waypoint]
                
                # Move source vehicle
                src_lat, src_lon = float(wp['Latitude_source']), float(wp['Longitude_source'])
                src_x, src_y = gps_to_sumo_coordinates(net, src_lat, src_lon)
                
                try:
                    traci.vehicle.moveToXY(
                        "sourceVehicle", "dummy", 0,
                        src_x, src_y,
                        angle=0, keepRoute=0, matchThreshold=200
                    )
                    print(f"📍 Step {step_count}: Moved source vehicle to waypoint {current_waypoint}")
                except Exception as e:
                    print(f"⚠️ Failed to move source vehicle: {e}")
                
                # Move destination vehicle
                dest_lat, dest_lon = float(wp['Latitude_destination']), float(wp['Longitude_destination'])
                dest_x, dest_y = gps_to_sumo_coordinates(net, dest_lat, dest_lon)
                
                try:
                    traci.vehicle.moveToXY(
                        "destVehicle", "dummy", 0,
                        dest_x, dest_y,
                        angle=0, keepRoute=0, matchThreshold=200
                    )
                    print(f"📍 Step {step_count}: Moved dest vehicle to waypoint {current_waypoint}")
                except Exception as e:
                    print(f"⚠️ Failed to move dest vehicle: {e}")
                
                current_waypoint += 1
            
            # Calculate and display distance every 50 steps
            if step_count % 50 == 0:
                try:
                    src_pos = traci.vehicle.getPosition("sourceVehicle")
                    dest_pos = traci.vehicle.getPosition("destVehicle")
                    distance = math.sqrt((src_pos[0] - dest_pos[0])**2 + (src_pos[1] - dest_pos[1])**2)
                    print(f"📏 Step {step_count}: Distance between vehicles: {distance:.2f}m")
                except Exception as e:
                    print(f"⚠️ Could not calculate distance: {e}")
            
            time.sleep(0.05)  # Small delay for visibility
        
        print("✅ Simulation completed!")
        print("🔍 Check SUMO-GUI:")
        print("   - Blue vehicle should be visible and moving")
        print("   - Red vehicle should be visible and moving")
        print("   - Both should follow the blue and red POI markers")
        print("   - Vehicles should appear as 3D car models")
        
        # Keep simulation running for inspection
        print("\n⏸️ Keeping simulation running for inspection...")
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
        print("✅ SUMO simulation stopped")

if __name__ == "__main__":
    run_simple_v2v_simulation()
