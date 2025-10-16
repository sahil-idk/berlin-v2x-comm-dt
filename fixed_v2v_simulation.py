#!/usr/bin/env python3
"""
Fixed V2V Simulation - Works with Actual SUMO Vehicle IDs
This version adapts to whatever vehicle IDs SUMO actually creates
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

def start_sumo_with_vehicles():
    """Start SUMO-GUI and wait for vehicles to be inserted"""
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

def run_fixed_v2v_simulation():
    """Run V2V simulation that works with actual SUMO vehicle IDs"""
    print("=" * 60)
    print("Fixed V2V Simulation - Working with Real Vehicle IDs")
    print("=" * 60)
    
    # Load GPS data
    print("📋 Loading GPS data...")
    try:
        df = pd.read_csv('vehicle_2_4_first_200.csv')
        waypoints = df.head(15).to_dict('records')  # Use first 15 points
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
    
    # Start SUMO
    if not start_sumo_with_vehicles():
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
        
        # Wait for vehicles to be inserted and get their actual IDs
        print("⏳ Waiting for vehicles to be inserted...")
        vehicle_ids = []
        
        for step in range(100):
            traci.simulationStep()
            current_vehicles = traci.vehicle.getIDList()
            
            if len(current_vehicles) >= 2 and len(vehicle_ids) == 0:
                # Take the first two vehicles
                vehicle_ids = current_vehicles[:2]
                print(f"✅ Found vehicles: {vehicle_ids}")
                break
            time.sleep(0.1)
        
        if len(vehicle_ids) < 2:
            print("❌ Not enough vehicles found in simulation")
            print(f"Available vehicles: {traci.vehicle.getIDList()}")
            return
        
        # Use the actual vehicle IDs
        source_vehicle_id = vehicle_ids[0]
        dest_vehicle_id = vehicle_ids[1]
        
        print(f"🚗 Using vehicles:")
        print(f"   Source (Blue): {source_vehicle_id}")
        print(f"   Destination (Red): {dest_vehicle_id}")
        
        # Set vehicle properties for better visibility
        print("🎨 Setting vehicle properties...")
        try:
            traci.vehicle.setLength(source_vehicle_id, 4.5)
            traci.vehicle.setWidth(source_vehicle_id, 1.8)
            traci.vehicle.setColor(source_vehicle_id, (0, 0, 255, 255))  # Blue
            print(f"✅ Set properties for {source_vehicle_id}")
        except Exception as e:
            print(f"⚠️ Could not set properties for {source_vehicle_id}: {e}")
        
        try:
            traci.vehicle.setLength(dest_vehicle_id, 4.5)
            traci.vehicle.setWidth(dest_vehicle_id, 1.8)
            traci.vehicle.setColor(dest_vehicle_id, (255, 0, 0, 255))  # Red
            print(f"✅ Set properties for {dest_vehicle_id}")
        except Exception as e:
            print(f"⚠️ Could not set properties for {dest_vehicle_id}: {e}")
        
        # Move vehicles through waypoints
        print("🎯 Starting vehicle movement simulation...")
        current_waypoint = 0
        step_count = 0
        max_steps = 2000
        
        while step_count < max_steps and current_waypoint < len(waypoints):
            traci.simulationStep()
            step_count += 1
            
            # Move vehicles every 40 steps
            if step_count % 40 == 0 and current_waypoint < len(waypoints):
                wp = waypoints[current_waypoint]
                
                # Move source vehicle
                src_lat, src_lon = float(wp['Latitude_source']), float(wp['Longitude_source'])
                src_x, src_y = gps_to_sumo_coordinates(net, src_lat, src_lon)
                
                try:
                    traci.vehicle.moveToXY(
                        source_vehicle_id, "dummy", 0,
                        src_x, src_y,
                        angle=0, keepRoute=0, matchThreshold=300
                    )
                    print(f"📍 Step {step_count}: Moved {source_vehicle_id} to waypoint {current_waypoint}")
                except Exception as e:
                    print(f"⚠️ Failed to move {source_vehicle_id}: {e}")
                
                # Move destination vehicle
                dest_lat, dest_lon = float(wp['Latitude_destination']), float(wp['Longitude_destination'])
                dest_x, dest_y = gps_to_sumo_coordinates(net, dest_lat, dest_lon)
                
                try:
                    traci.vehicle.moveToXY(
                        dest_vehicle_id, "dummy", 0,
                        dest_x, dest_y,
                        angle=0, keepRoute=0, matchThreshold=300
                    )
                    print(f"📍 Step {step_count}: Moved {dest_vehicle_id} to waypoint {current_waypoint}")
                except Exception as e:
                    print(f"⚠️ Failed to move {dest_vehicle_id}: {e}")
                
                current_waypoint += 1
            
            # Calculate and display distance every 60 steps
            if step_count % 60 == 0:
                try:
                    src_pos = traci.vehicle.getPosition(source_vehicle_id)
                    dest_pos = traci.vehicle.getPosition(dest_vehicle_id)
                    distance = math.sqrt((src_pos[0] - dest_pos[0])**2 + (src_pos[1] - dest_pos[1])**2)
                    print(f"📏 Step {step_count}: Distance between vehicles: {distance:.2f}m")
                except Exception as e:
                    print(f"⚠️ Could not calculate distance: {e}")
            
            time.sleep(0.05)  # Small delay for visibility
        
        print("✅ Simulation completed!")
        print("🔍 Check SUMO-GUI:")
        print(f"   - {source_vehicle_id} (Blue) should be visible and moving")
        print(f"   - {dest_vehicle_id} (Red) should be visible and moving")
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
    run_fixed_v2v_simulation()
