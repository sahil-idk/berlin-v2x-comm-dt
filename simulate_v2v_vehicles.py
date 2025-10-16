#!/usr/bin/env python3
"""
V2V Vehicle Simulation with 10 Waypoints
Creates two vehicles (blue source, red destination) that follow GPS waypoints
"""

import traci
import pandas as pd
import sumolib
import os
import time
import json
import xml.etree.ElementTree as ET

def create_vehicle_routes(net, waypoints_df, output_file="v2v_routes.rou.xml"):
    """Create SUMO route file for the two vehicles"""
    
    print("🚗 Creating vehicle routes...")
    
    # Create routes XML
    routes = ET.Element("routes")
    
    # Define vehicle types with colors
    vtype_source = ET.SubElement(routes, "vType")
    vtype_source.set("id", "sourceType")
    vtype_source.set("color", "0,0,255")  # Blue
    vtype_source.set("length", "4.5")
    vtype_source.set("width", "1.8")
    
    vtype_dest = ET.SubElement(routes, "vType")
    vtype_dest.set("id", "destType")
    vtype_dest.set("color", "255,0,0")  # Red
    vtype_dest.set("length", "4.5")
    vtype_dest.set("width", "1.8")
    
    # Process waypoints to create edge sequences
    source_edges = []
    dest_edges = []
    
    for idx, row in waypoints_df.iterrows():
        # Source vehicle waypoint
        src_lat = row['Latitude_source']
        src_lon = row['Longitude_source']
        src_x, src_y = net.convertLonLat2XY(src_lon, src_lat)
        
        # Find nearest edge for source
        edges = net.getNeighboringEdges(src_x, src_y, r=50)
        if edges:
            closest_edge = min(edges, key=lambda x: x[1])[0]
            source_edges.append(closest_edge.getID())
        
        # Destination vehicle waypoint
        dst_lat = row['Latitude_destination']
        dst_lon = row['Longitude_destination']
        dst_x, dst_y = net.convertLonLat2XY(dst_lon, dst_lat)
        
        # Find nearest edge for destination
        edges = net.getNeighboringEdges(dst_x, dst_y, r=50)
        if edges:
            closest_edge = min(edges, key=lambda x: x[1])[0]
            dest_edges.append(closest_edge.getID())
    
    # Remove duplicates while preserving order
    source_edges = list(dict.fromkeys(source_edges))
    dest_edges = list(dict.fromkeys(dest_edges))
    
    print(f"  Source route: {len(source_edges)} edges")
    print(f"  Destination route: {len(dest_edges)} edges")
    
    # Create routes
    if source_edges:
        route_source = ET.SubElement(routes, "route")
        route_source.set("id", "sourceRoute")
        route_source.set("edges", " ".join(source_edges))
    
    if dest_edges:
        route_dest = ET.SubElement(routes, "route")
        route_dest.set("id", "destRoute")
        route_dest.set("edges", " ".join(dest_edges))
    
    # Create vehicles
    if source_edges:
        vehicle_source = ET.SubElement(routes, "vehicle")
        vehicle_source.set("id", "sourceVehicle")
        vehicle_source.set("type", "sourceType")
        vehicle_source.set("route", "sourceRoute")
        vehicle_source.set("depart", "0")
    
    if dest_edges:
        vehicle_dest = ET.SubElement(routes, "vehicle")
        vehicle_dest.set("id", "destVehicle")
        vehicle_dest.set("type", "destType")
        vehicle_dest.set("route", "destRoute")
        vehicle_dest.set("depart", "0")
    
    # Save routes file
    tree = ET.ElementTree(routes)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"✅ Routes saved to: {output_file}")
    
    return source_edges, dest_edges

def create_v2v_config(route_file="v2v_routes.rou.xml"):
    """Create SUMO configuration for V2V simulation"""
    
    print("⚙️  Creating V2V simulation configuration...")
    
    config = ET.Element("configuration")
    
    # Input section
    input_elem = ET.SubElement(config, "input")
    
    net_file = ET.SubElement(input_elem, "net-file")
    net_file.set("value", "osm.net.xml.gz")
    
    route_files = ET.SubElement(input_elem, "route-files")
    route_files.set("value", f"{route_file},osm.passenger.trips.xml")
    
    additional_files = ET.SubElement(input_elem, "additional-files")
    additional_files.set("value", "osm.poly.xml.gz,osm_stops.add.xml,output.add.xml")
    
    # Time section
    time_elem = ET.SubElement(config, "time")
    
    begin = ET.SubElement(time_elem, "begin")
    begin.set("value", "0")
    
    end = ET.SubElement(time_elem, "end")
    end.set("value", "300")
    
    # Processing section
    processing = ET.SubElement(config, "processing")
    
    ignore_route_errors = ET.SubElement(processing, "ignore-route-errors")
    ignore_route_errors.set("value", "true")
    
    # Output section
    output_elem = ET.SubElement(config, "output")
    
    tripinfo = ET.SubElement(output_elem, "tripinfo-output")
    tripinfo.set("value", "v2v_tripinfos.xml")
    
    fcd_output = ET.SubElement(output_elem, "fcd-output")
    fcd_output.set("value", "v2v_fcd.xml")
    
    # GUI section
    gui_elem = ET.SubElement(config, "gui_only")
    
    gui_settings = ET.SubElement(gui_elem, "gui-settings-file")
    gui_settings.set("value", "osm.view.xml")
    
    # Save config
    tree = ET.ElementTree(config)
    config_file = "v2v_simulation.sumocfg"
    tree.write(config_file, encoding="utf-8", xml_declaration=True)
    print(f"✅ Configuration saved to: {config_file}")
    
    return config_file

def simulate_v2v_vehicles():
    """Run V2V simulation with 2 vehicles following 10 waypoints"""
    
    print("=" * 70)
    print("V2V Vehicle Simulation - 10 Waypoints")
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
    waypoints_df = df.head(10)  # First 10 points
    print(f"✅ Loaded {len(waypoints_df)} GPS waypoints")
    
    # Create routes and config
    source_edges, dest_edges = create_vehicle_routes(net, waypoints_df)
    config_file = create_v2v_config()
    
    # Start SUMO-GUI
    sumo_cmd = ["sumo-gui", "-c", config_file, "--start"]
    print("\n🚀 Starting SUMO-GUI simulation...")
    traci.start(sumo_cmd)
    time.sleep(3)
    
    print("\n🎮 Simulation Controls:")
    print("  - Press 'Play' to start simulation")
    print("  - Blue vehicle = Source (Vehicle 2)")
    print("  - Red vehicle = Destination (Vehicle 4)")
    print("  - Vehicles will follow GPS waypoint routes")
    
    # Add waypoint markers as POIs for reference
    print("\n📍 Adding waypoint markers...")
    for idx, row in waypoints_df.iterrows():
        # Source waypoint (blue marker)
        src_lat = row['Latitude_source']
        src_lon = row['Longitude_source']
        src_x, src_y = net.convertLonLat2XY(src_lon, src_lat)
        
        traci.poi.add(
            f"waypoint_src_{idx}",
            src_x, src_y,
            color=(0, 0, 255, 200),  # Semi-transparent blue
            poiType="Source_Waypoint",
            layer=50
        )
        
        # Destination waypoint (red marker)
        dst_lat = row['Latitude_destination']
        dst_lon = row['Longitude_destination']
        dst_x, dst_y = net.convertLonLat2XY(dst_lon, dst_lat)
        
        traci.poi.add(
            f"waypoint_dst_{idx}",
            dst_x, dst_y,
            color=(255, 0, 0, 200),  # Semi-transparent red
            poiType="Dest_Waypoint",
            layer=50
        )
    
    print(f"✅ Added {len(waypoints_df) * 2} waypoint markers")
    
    # Simulation loop with metrics
    print("\n🎯 Starting simulation...")
    step = 0
    max_steps = 300
    
    while step < max_steps:
        traci.simulationStep()
        step += 1
        
        # Check vehicle positions every 30 steps
        if step % 30 == 0:
            try:
                # Get vehicle positions
                vehicle_ids = traci.vehicle.getIDList()
                if "sourceVehicle" in vehicle_ids and "destVehicle" in vehicle_ids:
                    src_pos = traci.vehicle.getPosition("sourceVehicle")
                    dest_pos = traci.vehicle.getPosition("destVehicle")
                    
                    # Calculate distance
                    import math
                    distance = math.sqrt((src_pos[0] - dest_pos[0])**2 + (src_pos[1] - dest_pos[1])**2)
                    
                    print(f"Step {step}: Distance between vehicles: {distance:.2f}m")
            except:
                pass
        
        time.sleep(0.1)
    
    print("\n✅ Simulation completed!")
    print("🔍 Check SUMO-GUI:")
    print("  - Blue vehicle should follow blue waypoint markers")
    print("  - Red vehicle should follow red waypoint markers")
    print("  - Both vehicles should stay on roads")
    
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
    
    print(f"\n💾 Simulation files created:")
    print(f"  - Routes: v2v_routes.rou.xml")
    print(f"  - Config: v2v_simulation.sumocfg")
    print(f"  - Trip info: v2v_tripinfos.xml")
    print(f"  - FCD data: v2v_fcd.xml")

if __name__ == "__main__":
    simulate_v2v_vehicles()
