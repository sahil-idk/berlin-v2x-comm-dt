#!/usr/bin/env python3
"""
V2V Approach 4: Hybrid Route + GPS Correction
Combines improved routing with selective GPS forcing for best accuracy
"""

import traci
import pandas as pd
import sumolib
import os
import time
import math
import tkinter as tk
from tkinter import ttk
import threading
import json

# Calibration factor
CALIBRATION_FACTOR = 0.607

def kmh_to_ms(speed_kmh):
    """Convert km/h to m/s"""
    return speed_kmh / 3.6

def calculate_distance(pos1, pos2):
    """Calculate Euclidean distance"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def extend_route(net, route):
    """Extend a short route to ensure proper vehicle movement"""
    if len(route) >= 3:
        return route
    
    try:
        if len(route) == 0:
            # Find any connected edge pair
            edges = list(net.getEdges())
            if len(edges) >= 2:
                return [edges[0].getID(), edges[1].getID()]
            return route
        
        # Extend from the last edge
        last_edge = net.getEdge(route[-1])
        outgoing = list(last_edge.getOutgoing().keys())
        
        extended_route = route.copy()
        for out_edge in outgoing:
            extended_route.append(out_edge.getID())
            if len(extended_route) >= 3:
                break
        
        return extended_route
    except Exception as e:
        print(f"⚠️ Route extension failed: {e}")
        return route

def find_optimal_path_through_waypoints_hybrid(net, waypoints_df, vehicle_type='source'):
    """HYBRID: Improved route planning with better waypoint sampling"""
    edges_with_positions = []
    
    # IMPROVEMENT 1: Sample every 5th point instead of current sampling strategy
    sample_indices = range(0, len(waypoints_df), 5)  # Every 5th point
    sampled_waypoints = waypoints_df.iloc[sample_indices]
    
    print(f"📊 Original waypoints: {len(waypoints_df)}, Sampled: {len(sampled_waypoints)}")
    
    for idx, row in sampled_waypoints.iterrows():
        if vehicle_type == 'source':
            lat = row['Latitude_source']
            lon = row['Longitude_source']
        else:
            lat = row['Latitude_destination']
            lon = row['Longitude_destination']
        
        x, y = net.convertLonLat2XY(lon, lat)
        
        # IMPROVED: Better edge finding with lane-based positioning
        search_radius = 30  # Start smaller
        best_edge = None
        best_distance = float('inf')
        
        while search_radius <= 200:
            nearby_edges = net.getNeighboringEdges(x, y, r=search_radius)
            if nearby_edges:
                for edge, distance in nearby_edges:
                    if distance < best_distance:
                        best_distance = distance
                        best_edge = edge
                
                if best_edge:
                    # Find the closest lane on this edge
                    lanes = best_edge.getLanes()
                    if lanes:
                        closest_lane = min(lanes, key=lambda lane: 
                            abs(lane.getShape()[0][0] - x) + abs(lane.getShape()[0][1] - y))
                        
                        edges_with_positions.append({
                            'edge': best_edge,
                            'edge_id': best_edge.getID(),
                            'lane_id': closest_lane.getID(),
                            'position': (x, y),
                            'original_idx': idx,
                            'distance': best_distance
                        })
                        print(f"   ✅ Found edge: {best_edge.getID()} at distance {best_distance:.2f}m")
                        break
            search_radius += 30
    
    if not edges_with_positions:
        return []
    
    # IMPROVEMENT 2: Use all intermediate edges in Dijkstra path
    route = []
    for i in range(len(edges_with_positions) - 1):
        start_edge = edges_with_positions[i]['edge']
        end_edge = edges_with_positions[i + 1]['edge']
        
        try:
            # Find shortest path using Dijkstra
            path = net.getShortestPath(start_edge, end_edge)
            if path and len(path) > 0 and path[0] is not None:
                # IMPROVEMENT 2: Keep ALL edges in path, but avoid duplicates
                for edge in path[0]:
                    if edge.getID() not in route:  # Avoid duplicates
                        route.append(edge.getID())
            else:
                print(f"   ⚠️ Empty or invalid path returned - skipping this segment")
        except Exception as e:
            print(f"⚠️ Path finding failed between edges: {e}")
            continue
    
    # IMPROVEMENT 3: Add edge extensions at start/end for smoother entry/exit
    if len(route) > 0:
        try:
            # Extend route by adding incoming/outgoing edges
            first_edge = net.getEdge(route[0])
            incoming = list(first_edge.getIncoming().keys())
            if incoming:
                route.insert(0, incoming[0].getID())
                print(f"✅ Extended start with incoming edge: {incoming[0].getID()}")
            
            last_edge = net.getEdge(route[-1])
            outgoing = list(last_edge.getOutgoing().keys())
            if outgoing:
                route.append(outgoing[0].getID())
                print(f"✅ Extended end with outgoing edge: {outgoing[0].getID()}")
        except Exception as e:
            print(f"⚠️ Edge extension failed: {e}")
    
    # Validate route connectivity
    if len(route) < 2:
        print("❌ Route too short - need at least 2 edges")
        return []
    
    # Check if route is connected
    try:
        for i in range(len(route) - 1):
            current_edge = net.getEdge(route[i])
            next_edge = net.getEdge(route[i + 1])
            
            # Check if edges are connected
            outgoing_edges = [edge.getID() for edge in current_edge.getOutgoing().keys()]
            if route[i + 1] not in outgoing_edges:
                print(f"⚠️ Route disconnected at edge {i}: {route[i]} -> {route[i + 1]}")
                print(f"   Available outgoing edges: {outgoing_edges}")
                # Try to find a connecting edge
                for out_edge in outgoing_edges:
                    if net.getEdge(out_edge).getOutgoing():
                        connecting_edges = [edge.getID() for edge in net.getEdge(out_edge).getOutgoing().keys()]
                        if route[i + 1] in connecting_edges:
                            print(f"   ✅ Found connecting edge: {out_edge}")
                            route.insert(i + 1, out_edge)
                            break
                else:
                    print(f"   ❌ No connecting edge found - removing disconnected segment")
                    route = route[:i + 1]  # Keep only connected part
                    break
    except Exception as e:
        print(f"❌ Error during route connectivity validation: {e}")
        return []
    
    # If route is still too short or disconnected, create a simple fallback route
    if len(route) < 3:
        print("⚠️ Route too short, creating simple fallback route...")
        # Find a simple connected path using just the first and last edges
        if len(edges_with_positions) >= 2:
            first_edge = edges_with_positions[0]['edge']
            last_edge = edges_with_positions[-1]['edge']
            try:
                fallback_path = net.getShortestPath(first_edge, last_edge)
                if fallback_path and len(fallback_path) > 0 and fallback_path[0] is not None:
                    route = [edge.getID() for edge in fallback_path[0]]
                    print(f"✅ Created fallback route with {len(route)} edges")
                else:
                    print("❌ Even fallback route failed")
                    return []
            except Exception as e:
                print(f"❌ Fallback route creation failed: {e}")
                return []
    
    print(f"✅ HYBRID Route created: {len(route)} edges")
    return route

class V2VHybridSimulation:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("V2V Approach 4: Hybrid Route + GPS Correction")
        self.root.geometry("600x550")
        
        self.simulation_running = False
        self.simulation_thread = None
        
        self.num_waypoints = tk.IntVar(value=50)
        self.calibration_enabled = tk.BooleanVar(value=True)
        self.use_realistic_speed = tk.BooleanVar(value=True)
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup GUI components"""
        title_label = tk.Label(self.root, text="V2V Approach 4: Hybrid Route + GPS Correction", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        info_label = tk.Label(self.root, text="Best of both worlds: improved routing + selective GPS forcing!", 
                             font=("Arial", 10), fg="blue")
        info_label.pack()
        
        config_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(config_frame, text="Waypoints:").grid(row=0, column=0, sticky="w")
        ttk.Scale(config_frame, from_=5, to=200, variable=self.num_waypoints, 
                 orient="horizontal", length=200).grid(row=0, column=1)
        ttk.Label(config_frame, textvariable=self.num_waypoints).grid(row=0, column=2)
        
        ttk.Checkbutton(config_frame, text="✅ Use Realistic Speed from Dataset", 
                       variable=self.use_realistic_speed).grid(row=1, column=0, columnspan=3, sticky="w")
        
        ttk.Checkbutton(config_frame, text="✅ Apply Calibration (0.607)", 
                       variable=self.calibration_enabled).grid(row=2, column=0, columnspan=3, sticky="w")
        
        control_frame = ttk.LabelFrame(self.root, text="Control", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        self.start_button = ttk.Button(control_frame, text="Start Simulation", 
                                      command=self.start_simulation)
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", 
                                     command=self.stop_simulation, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        status_frame = ttk.LabelFrame(self.root, text="Status", padding=10)
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_text = tk.Text(status_frame, height=15, width=70)
        scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        
    def log_message(self, message):
        """Log message to status"""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update()
        
    def start_simulation(self):
        """Start simulation in separate thread"""
        if not self.simulation_running:
            self.simulation_running = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.simulation_thread = threading.Thread(target=self.run_simulation)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            
    def stop_simulation(self):
        """Stop simulation"""
        self.simulation_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
    def run_simulation(self):
        """Main simulation with HYBRID approach"""
        try:
            self.log_message("="*70)
            self.log_message("V2V APPROACH 4: HYBRID ROUTE + GPS CORRECTION")
            self.log_message("="*70)
            self.log_message(f"🚗 Speed Mode: {'REALISTIC (from GPS data)' if self.use_realistic_speed.get() else 'CONSTANT (15 m/s)'}")
            self.log_message(f"📊 Calibration: {'ENABLED (0.607)' if self.calibration_enabled.get() else 'DISABLED'}")
            self.log_message("🔧 Route Planning: IMPROVED (every 5th point, all edges, extensions)")
            self.log_message("🎯 GPS Forcing: SELECTIVE (>30m deviation threshold)")
            
            NUM_WAYPOINTS = self.num_waypoints.get()
            SIMULATION_STEPS = 6000
            
            original_dir = os.getcwd()
            
            # Load network
            os.chdir('berlin-sumo-closed-netwokr')
            self.log_message("\n📍 Loading SUMO network...")
            net = sumolib.net.readNet('osm.net.xml.gz')
            self.log_message(f"✅ Network loaded: {len(net.getEdges())} edges")
            
            # Load GPS data with SPEED
            self.log_message(f"\n📍 Loading GPS data with speed information...")
            df = pd.read_csv('../vehicle_2_4_first_200.csv')
            waypoints_df = df.head(NUM_WAYPOINTS)
            self.log_message(f"✅ Loaded {len(waypoints_df)} waypoints")
            
            # Speed statistics
            src_speeds_kmh = waypoints_df['speed_kmh_source']
            dst_speeds_kmh = waypoints_df['speed_kmh_destination']
            
            self.log_message(f"\n📊 Speed Statistics:")
            self.log_message(f"   Source: {src_speeds_kmh.min():.1f}-{src_speeds_kmh.max():.1f} km/h (avg: {src_speeds_kmh.mean():.1f})")
            self.log_message(f"   Destination: {dst_speeds_kmh.min():.1f}-{dst_speeds_kmh.max():.1f} km/h (avg: {dst_speeds_kmh.mean():.1f})")
            
            # HYBRID: Create improved routes
            self.log_message(f"\n🔧 Creating HYBRID improved routes...")
            source_route = find_optimal_path_through_waypoints_hybrid(net, waypoints_df, 'source')
            dest_route = find_optimal_path_through_waypoints_hybrid(net, waypoints_df, 'destination')
            
            # Debug: Print route details
            self.log_message(f"🔍 Source route edges: {source_route}")
            self.log_message(f"🔍 Destination route edges: {dest_route}")
            
            if not source_route or not dest_route:
                self.log_message("❌ Failed to create routes")
                return
            
            # Ensure routes are long enough for proper movement
            if len(source_route) < 3:
                self.log_message("⚠️ Source route too short, extending...")
                source_route = extend_route(net, source_route)
            
            if len(dest_route) < 3:
                self.log_message("⚠️ Destination route too short, extending...")
                dest_route = extend_route(net, dest_route)
                
            self.log_message(f"✅ Source route: {len(source_route)} edges")
            self.log_message(f"✅ Destination route: {len(dest_route)} edges")
            
            # Create separate route files for each vehicle with unique vehicle types
            with open('hybrid_source_route.rou.xml', 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<routes>\n')
                f.write('  <route id="hybrid_source_route" edges="' + ' '.join(source_route) + '"/>\n')
                f.write('  <vType id="hybrid_source_vType" accel="2.0" decel="4.5" sigma="0.5" length="4.5" maxSpeed="50" guiShape="passenger" color="blue"/>\n')
                f.write('</routes>\n')
            
            with open('hybrid_dest_route.rou.xml', 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<routes>\n')
                f.write('  <route id="hybrid_dest_route" edges="' + ' '.join(dest_route) + '"/>\n')
                f.write('  <vType id="hybrid_dest_vType" accel="2.0" decel="4.5" sigma="0.5" length="4.5" maxSpeed="50" guiShape="passenger" color="red"/>\n')
                f.write('</routes>\n')
            
            # Create SUMO config
            with open('hybrid.sumocfg', 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<configuration>\n')
                f.write('  <input>\n')
                f.write('    <net-file value="osm.net.xml.gz"/>\n')
                f.write('    <route-files value="hybrid_source_route.rou.xml,hybrid_dest_route.rou.xml"/>\n')
                f.write('  </input>\n')
                f.write('  <time>\n')
                f.write('    <begin value="0"/>\n')
                f.write('    <end value="10000"/>\n')
                f.write('  </time>\n')
                f.write('  <gui_only>\n')
                f.write('    <gui-settings-file value="osm.view.xml"/>\n')
                f.write('  </gui_only>\n')
                f.write('</configuration>\n')
            
            # Start SUMO
            sumo_cmd = ["sumo-gui", "-c", "hybrid.sumocfg"]
            self.log_message(f"\n🚀 Starting SUMO-GUI with hybrid approach...")
            
            traci.start(sumo_cmd)
            time.sleep(5)  # Wait longer for SUMO to initialize
            
            # Check if vehicles are loaded
            vehicle_ids = traci.vehicle.getIDList()
            self.log_message(f"Initial vehicle check: {vehicle_ids}")
            
            # Wait a bit more if no vehicles found
            if not vehicle_ids:
                self.log_message("Waiting for vehicles to load...")
                time.sleep(3)
                vehicle_ids = traci.vehicle.getIDList()
                self.log_message(f"Second vehicle check: {vehicle_ids}")
            
            # Add vehicles if not already loaded
            if "hybrid_v2v_source" not in vehicle_ids:
                traci.vehicle.add("hybrid_v2v_source", "hybrid_source_route", typeID="hybrid_source_vType")
            if "hybrid_v2v_dest" not in vehicle_ids:
                traci.vehicle.add("hybrid_v2v_dest", "hybrid_dest_route", typeID="hybrid_dest_vType")
            
            # Set vehicle properties
            traci.vehicle.setColor("hybrid_v2v_source", (0, 0, 255, 255))  # Blue
            traci.vehicle.setColor("hybrid_v2v_dest", (255, 0, 0, 255))    # Red
            
            # Set vehicle control modes to prevent stalling
            traci.vehicle.setSpeedMode("hybrid_v2v_source", 0)  # No speed adaptation
            traci.vehicle.setSpeedMode("hybrid_v2v_dest", 0)    # No speed adaptation
            traci.vehicle.setLaneChangeMode("hybrid_v2v_source", 0)  # No lane changes
            traci.vehicle.setLaneChangeMode("hybrid_v2v_dest", 0)    # No lane changes
            
            self.log_message(f"✅ Vehicles added with hybrid approach")
            
            # Prepare waypoint coordinates for hybrid analysis
            waypoint_coords = []
            for idx, row in waypoints_df.iterrows():
                src_x, src_y = net.convertLonLat2XY(row['Longitude_source'], row['Latitude_source'])
                dst_x, dst_y = net.convertLonLat2XY(row['Longitude_destination'], row['Latitude_destination'])
                
                # Find edges for this waypoint
                src_edge = None
                dst_edge = None
                
                # Find source edge
                nearby_edges = net.getNeighboringEdges(src_x, src_y, r=50)
                if nearby_edges:
                    src_edge = min(nearby_edges, key=lambda e: e[1])[0]
                
                # Find destination edge
                nearby_edges = net.getNeighboringEdges(dst_x, dst_y, r=50)
                if nearby_edges:
                    dst_edge = min(nearby_edges, key=lambda e: e[1])[0]
                
                waypoint_coords.append({
                    'source': (src_x, src_y),
                    'dest': (dst_x, dst_y),
                    'actual_distance': row['distance'],
                    'source_speed_kmh': row['speed_kmh_source'],
                    'dest_speed_kmh': row['speed_kmh_destination'],
                    'edge_id': src_edge.getID() if src_edge else None,
                    'dest_edge_id': dst_edge.getID() if dst_edge else None
                })
            
            # Simulation loop with HYBRID approach
            self.log_message(f"\n🎯 Starting simulation with hybrid approach...")
            
            step = 0
            current_waypoint = 0
            source_active = False
            dest_active = False
            source_progress = []
            dest_progress = []
            distances_raw = []
            distances_calibrated = []
            last_log_step = 0
            
            # HYBRID: GPS forcing counters
            gps_corrections_source = 0
            gps_corrections_dest = 0
            
            # HYBRID: Dynamic calibration zones
            CALIBRATION_ZONES = {
                'zone_1': {'waypoints': range(0, 50), 'factor': 0.58},
                'zone_2': {'waypoints': range(50, 100), 'factor': 0.62},
                'zone_3': {'waypoints': range(100, 150), 'factor': 0.61},
                'zone_4': {'waypoints': range(150, 200), 'factor': 0.59}
            }
            
            # Detailed waypoint analysis storage
            waypoint_analysis = []
            
            while step < SIMULATION_STEPS and self.simulation_running:
                traci.simulationStep()
                step += 1
                
                progress = min(100, (step / SIMULATION_STEPS) * 100)
                self.progress_var.set(progress)
                
                vehicles = traci.vehicle.getIDList()
                
                # Source vehicle
                if "hybrid_v2v_source" in vehicles:
                    if not source_active:
                        self.log_message(f"✅ Step {step}: Source vehicle active")
                        source_active = True
                    
                    src_pos = traci.vehicle.getPosition("hybrid_v2v_source")
                    src_speed = traci.vehicle.getSpeed("hybrid_v2v_source")
                    
                    # SET REALISTIC SPEED from dataset
                    if self.use_realistic_speed.get() and current_waypoint < len(waypoint_coords):
                        target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['source_speed_kmh'])
                        traci.vehicle.setSpeed("hybrid_v2v_source", target_speed_ms)
                    else:
                        # Ensure minimum speed to prevent stalling
                        traci.vehicle.setSpeed("hybrid_v2v_source", 5.0)  # 5 m/s minimum
                    
                    # HYBRID: Selective GPS forcing only when deviation >30m
                    if current_waypoint < len(waypoint_coords):
                        wp = waypoint_coords[current_waypoint]
                        deviation = calculate_distance(src_pos, wp['source'])
                        
                        if deviation > 30:  # SELECTIVE threshold
                            try:
                                # Find the closest edge and lane for this waypoint
                                closest_edge = None
                                closest_lane = None
                                min_dist = float('inf')
                                
                                # Search for the best edge and lane
                                for edge_info in waypoint_coords:
                                    if edge_info.get('edge_id'):
                                        edge = net.getEdge(edge_info['edge_id'])
                                        lanes = edge.getLanes()
                                        for lane in lanes:
                                            lane_pos = lane.getShape()[0]
                                            dist = calculate_distance(src_pos, lane_pos)
                                            if dist < min_dist:
                                                min_dist = dist
                                                closest_edge = edge
                                                closest_lane = lane
                                
                                if closest_edge and closest_lane:
                                    traci.vehicle.moveToXY(
                                        "hybrid_v2v_source", 
                                        edgeID=closest_edge.getID(), 
                                        laneIndex=0,  # Use lane index instead of lane ID
                                        x=wp['source'][0], 
                                        y=wp['source'][1],
                                        angle=traci.constants.INVALID_DOUBLE_VALUE,
                                        keepRoute=2,  # Allow route changes
                                        matchThreshold=200  # Reduced threshold
                                    )
                                    gps_corrections_source += 1
                                    if gps_corrections_source % 25 == 0:  # Log every 25 corrections
                                        self.log_message(f"🎯 Selective GPS correction #{gps_corrections_source} for source (deviation: {deviation:.1f}m)")
                                else:
                                    self.log_message(f"⚠️ Could not find suitable edge/lane for GPS correction")
                            except Exception as e:
                                self.log_message(f"⚠️ Selective GPS correction failed for source: {e}")
                        # else: Let natural routing handle it
                    
                    # PROXIMITY DETECTION: Advance waypoint when within 20m
                    if current_waypoint < len(waypoint_coords):
                        wp_pos = waypoint_coords[current_waypoint]['source']
                        dist_to_wp = calculate_distance(src_pos, wp_pos)
                        if dist_to_wp < 20:  # Within 20m of waypoint
                            current_waypoint += 1
                            if current_waypoint < len(waypoint_coords):
                                self.log_message(f"📍 Step {step}: Source advanced to waypoint {current_waypoint}")
                    
                    closest_wp = 0
                    min_dist = float('inf')
                    for i, wp in enumerate(waypoint_coords):
                        dist = calculate_distance(src_pos, wp['source'])
                        if dist < min_dist:
                            min_dist = dist
                            closest_wp = i
                    source_progress.append(closest_wp)
                else:
                    if source_active:
                        self.log_message(f"⚠️ Step {step}: Source completed")
                        source_active = False
                
                # Destination vehicle
                if "hybrid_v2v_dest" in vehicles:
                    if not dest_active:
                        self.log_message(f"✅ Step {step}: Destination vehicle active")
                        dest_active = True
                    
                    dst_pos = traci.vehicle.getPosition("hybrid_v2v_dest")
                    dst_speed = traci.vehicle.getSpeed("hybrid_v2v_dest")
                    
                    # SET REALISTIC SPEED from dataset
                    if self.use_realistic_speed.get() and current_waypoint < len(waypoint_coords):
                        target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['dest_speed_kmh'])
                        traci.vehicle.setSpeed("hybrid_v2v_dest", target_speed_ms)
                    else:
                        # Ensure minimum speed to prevent stalling
                        traci.vehicle.setSpeed("hybrid_v2v_dest", 5.0)  # 5 m/s minimum
                    
                    # HYBRID: Selective GPS forcing only when deviation >30m
                    if current_waypoint < len(waypoint_coords):
                        wp = waypoint_coords[current_waypoint]
                        deviation = calculate_distance(dst_pos, wp['dest'])
                        
                        if deviation > 30:  # SELECTIVE threshold
                            try:
                                # Find the closest edge and lane for this waypoint
                                closest_edge = None
                                closest_lane = None
                                min_dist = float('inf')
                                
                                # Search for the best edge and lane
                                for edge_info in waypoint_coords:
                                    if edge_info.get('edge_id'):
                                        edge = net.getEdge(edge_info['edge_id'])
                                        lanes = edge.getLanes()
                                        for lane in lanes:
                                            lane_pos = lane.getShape()[0]
                                            dist = calculate_distance(dst_pos, lane_pos)
                                            if dist < min_dist:
                                                min_dist = dist
                                                closest_edge = edge
                                                closest_lane = lane
                                
                                if closest_edge and closest_lane:
                                    traci.vehicle.moveToXY(
                                        "hybrid_v2v_dest", 
                                        edgeID=closest_edge.getID(), 
                                        laneIndex=0,  # Use lane index instead of lane ID
                                        x=wp['dest'][0], 
                                        y=wp['dest'][1],
                                        angle=traci.constants.INVALID_DOUBLE_VALUE,
                                        keepRoute=2,  # Allow route changes
                                        matchThreshold=200  # Reduced threshold
                                    )
                                    gps_corrections_dest += 1
                                    if gps_corrections_dest % 25 == 0:  # Log every 25 corrections
                                        self.log_message(f"🎯 Selective GPS correction #{gps_corrections_dest} for destination (deviation: {deviation:.1f}m)")
                                else:
                                    self.log_message(f"⚠️ Could not find suitable edge/lane for GPS correction")
                            except Exception as e:
                                self.log_message(f"⚠️ Selective GPS correction failed for destination: {e}")
                        # else: Let natural routing handle it
                    
                    # PROXIMITY DETECTION: Advance waypoint when within 20m
                    if current_waypoint < len(waypoint_coords):
                        wp_pos = waypoint_coords[current_waypoint]['dest']
                        dist_to_wp = calculate_distance(dst_pos, wp_pos)
                        if dist_to_wp < 20:  # Within 20m of waypoint
                            # Don't advance waypoint here, let source control it
                            pass
                    
                    closest_wp = 0
                    min_dist = float('inf')
                    for i, wp in enumerate(waypoint_coords):
                        dist = calculate_distance(dst_pos, wp['dest'])
                        if dist < min_dist:
                            min_dist = dist
                            closest_wp = i
                    dest_progress.append(closest_wp)
                else:
                    if dest_active:
                        self.log_message(f"⚠️ Step {step}: Destination completed")
                        dest_active = False
                
                # Calculate distances
                if source_active and dest_active:
                    raw_distance = calculate_distance(src_pos, dst_pos)
                    distances_raw.append(raw_distance)
                    
                    # HYBRID: Dynamic calibration based on waypoint region
                    if self.calibration_enabled.get():
                        # Determine which zone the current waypoint belongs to
                        current_calibration = CALIBRATION_FACTOR  # Default
                        for zone_name, zone_info in CALIBRATION_ZONES.items():
                            if current_waypoint in zone_info['waypoints']:
                                current_calibration = zone_info['factor']
                                break
                        
                        calibrated_distance = raw_distance * current_calibration
                        distances_calibrated.append(calibrated_distance)
                    else:
                        distances_calibrated.append(raw_distance)
                    
                    # Update current waypoint
                    prev_waypoint = current_waypoint
                    if source_progress and dest_progress:
                        current_waypoint = min(source_progress[-1], dest_progress[-1])
                    
                    # Record waypoint analysis when we move to a new waypoint
                    if current_waypoint != prev_waypoint and current_waypoint < len(waypoint_coords):
                        wp_data = waypoint_coords[current_waypoint]
                        
                        # Get actual speeds from dataset
                        actual_src_speed_kmh = wp_data['source_speed_kmh']
                        actual_dst_speed_kmh = wp_data['dest_speed_kmh']
                        
                        # Get simulated speeds
                        simulated_src_speed_kmh = src_speed * 3.6
                        simulated_dst_speed_kmh = dst_speed * 3.6
                        
                        # Calculate actual distance from dataset
                        actual_distance = wp_data['actual_distance']
                        
                        # Calculate simulated distance
                        simulated_distance = calibrated_distance if self.calibration_enabled.get() else raw_distance
                        
                        # Calculate accuracy metrics
                        distance_error = simulated_distance - actual_distance
                        distance_error_pct = (distance_error / actual_distance * 100) if actual_distance > 0 else 0
                        distance_accuracy = max(0, 100 - abs(distance_error_pct))
                        
                        speed_error_src = simulated_src_speed_kmh - actual_src_speed_kmh
                        speed_error_dst = simulated_dst_speed_kmh - actual_dst_speed_kmh
                        
                        # Determine calibration zone
                        calibration_zone = "default"
                        calibration_factor_used = CALIBRATION_FACTOR
                        for zone_name, zone_info in CALIBRATION_ZONES.items():
                            if current_waypoint in zone_info['waypoints']:
                                calibration_zone = zone_name
                                calibration_factor_used = zone_info['factor']
                                break
                        
                        waypoint_analysis.append({
                            'waypoint': current_waypoint,
                            'step': step,
                            'actual_distance_m': actual_distance,
                            'simulated_distance_m': simulated_distance,
                            'distance_error_m': distance_error,
                            'distance_error_pct': distance_error_pct,
                            'distance_accuracy_pct': distance_accuracy,
                            'actual_speed_src_kmh': actual_src_speed_kmh,
                            'simulated_speed_src_kmh': simulated_src_speed_kmh,
                            'speed_error_src_kmh': speed_error_src,
                            'actual_speed_dst_kmh': actual_dst_speed_kmh,
                            'simulated_speed_dst_kmh': simulated_dst_speed_kmh,
                            'speed_error_dst_kmh': speed_error_dst,
                            'calibration_enabled': self.calibration_enabled.get(),
                            'realistic_speed_enabled': self.use_realistic_speed.get(),
                            'approach': 'hybrid',
                            'gps_corrections_source': gps_corrections_source,
                            'gps_corrections_dest': gps_corrections_dest,
                            'calibration_zone': calibration_zone,
                            'calibration_factor_used': calibration_factor_used
                        })
                    
                    # Log every 200 steps
                    if step - last_log_step >= 200:
                        avg_calib = sum(distances_calibrated[-200:]) / len(distances_calibrated[-200:])
                        
                        src_speed_kmh = src_speed * 3.6
                        dst_speed_kmh = dst_speed * 3.6
                        
                        self.log_message(f"📊 Step {step}: Distance={avg_calib:.2f}m, "
                                        f"Speeds: src={src_speed_kmh:.1f}km/h, dst={dst_speed_kmh:.1f}km/h, "
                                        f"WP={current_waypoint}/{NUM_WAYPOINTS}, "
                                        f"Selective GPS: src={gps_corrections_source}, dst={gps_corrections_dest}")
                        last_log_step = step
                
                if not source_active and not dest_active and step > 100:
                    break
                
                time.sleep(0.01)
            
            # Final statistics and reporting
            self.log_message("\n" + "="*70)
            self.log_message("SIMULATION COMPLETE - GENERATING REPORTS")
            self.log_message("="*70)
            
            if distances_raw:
                self.log_message(f"\n📊 Distance Statistics:")
                self.log_message(f"   Raw: avg={sum(distances_raw)/len(distances_raw):.2f}m")
                self.log_message(f"   Calibrated: avg={sum(distances_calibrated)/len(distances_calibrated):.2f}m")
            
            self.log_message(f"📊 Total steps: {step}")
            self.log_message(f"✅ Speed mode: {'REALISTIC from dataset' if self.use_realistic_speed.get() else 'CONSTANT 15 m/s'}")
            self.log_message(f"🔧 Route planning: IMPROVED (every 5th point, all edges, extensions)")
            self.log_message(f"🎯 GPS forcing: SELECTIVE (>30m deviation threshold)")
            self.log_message(f"📊 Selective GPS corrections: Source={gps_corrections_source}, Destination={gps_corrections_dest}")
            
            # Save detailed waypoint analysis to CSV
            if waypoint_analysis:
                self.log_message("\n📊 Generating detailed analysis...")
                
                analysis_df = pd.DataFrame(waypoint_analysis)
                
                # Save to MAIN project directory (not SUMO subfolder)
                csv_file = os.path.join(original_dir, 'approach_4_hybrid_analysis.csv')
                
                try:
                    analysis_df.to_csv(csv_file, index=False)
                    self.log_message(f"\n💾 Detailed CSV saved to:")
                    self.log_message(f"   {os.path.abspath(csv_file)}")
                    self.log_message(f"   📂 Location: Main project folder")
                    self.log_message(f"   📊 Rows: {len(analysis_df)}")
                except Exception as e:
                    self.log_message(f"\n❌ Error saving CSV: {e}")
                
                # Calculate overall accuracy metrics
                distance_errors = analysis_df['distance_error_m']
                distance_accuracies = analysis_df['distance_accuracy_pct']
                speed_errors_src = analysis_df['speed_error_src_kmh']
                speed_errors_dst = analysis_df['speed_error_dst_kmh']
                
                overall_metrics = {
                    'simulation_settings': {
                        'num_waypoints': NUM_WAYPOINTS,
                        'calibration_enabled': self.calibration_enabled.get(),
                        'calibration_factor': CALIBRATION_FACTOR if self.calibration_enabled.get() else 1.0,
                        'realistic_speed_enabled': self.use_realistic_speed.get(),
                        'total_steps': int(step),
                        'approach': 'hybrid',
                        'gps_corrections_source': int(gps_corrections_source),
                        'gps_corrections_dest': int(gps_corrections_dest),
                        'deviation_threshold': 30
                    },
                    'distance_accuracy': {
                        'mean_accuracy_pct': float(distance_accuracies.mean()),
                        'median_accuracy_pct': float(distance_accuracies.median()),
                        'min_accuracy_pct': float(distance_accuracies.min()),
                        'max_accuracy_pct': float(distance_accuracies.max()),
                        'mean_error_m': float(distance_errors.mean()),
                        'mean_absolute_error_m': float(distance_errors.abs().mean()),
                        'rmse_m': float((distance_errors**2).mean()**0.5),
                        'std_dev_m': float(distance_errors.std())
                    },
                    'speed_accuracy': {
                        'source_vehicle': {
                            'mean_error_kmh': float(speed_errors_src.mean()),
                            'mean_absolute_error_kmh': float(speed_errors_src.abs().mean()),
                            'rmse_kmh': float((speed_errors_src**2).mean()**0.5),
                            'std_dev_kmh': float(speed_errors_src.std())
                        },
                        'destination_vehicle': {
                            'mean_error_kmh': float(speed_errors_dst.mean()),
                            'mean_absolute_error_kmh': float(speed_errors_dst.abs().mean()),
                            'rmse_kmh': float((speed_errors_dst**2).mean()**0.5),
                            'std_dev_kmh': float(speed_errors_dst.std())
                        }
                    },
                    'waypoint_distribution': {
                        'high_accuracy_90_plus': int((distance_accuracies >= 90).sum()),
                        'medium_accuracy_70_89': int(((distance_accuracies >= 70) & (distance_accuracies < 90)).sum()),
                        'low_accuracy_below_70': int((distance_accuracies < 70).sum()),
                        'total_waypoints_analyzed': int(len(analysis_df))
                    },
                    'best_waypoint': {
                        'waypoint': int(analysis_df.loc[distance_accuracies.idxmax(), 'waypoint']),
                        'accuracy_pct': float(distance_accuracies.max()),
                        'distance_error_m': float(analysis_df.loc[distance_accuracies.idxmax(), 'distance_error_m'])
                    },
                    'worst_waypoint': {
                        'waypoint': int(analysis_df.loc[distance_accuracies.idxmin(), 'waypoint']),
                        'accuracy_pct': float(distance_accuracies.min()),
                        'distance_error_m': float(analysis_df.loc[distance_accuracies.idxmin(), 'distance_error_m'])
                    }
                }
                
                # Save JSON summary to main project directory
                json_file = os.path.join(original_dir, 'approach_4_hybrid_summary.json')
                
                try:
                    with open(json_file, 'w') as f:
                        json.dump(overall_metrics, f, indent=2)
                    self.log_message(f"💾 Summary JSON saved to:")
                    self.log_message(f"   {os.path.abspath(json_file)}")
                except Exception as e:
                    self.log_message(f"❌ Error saving JSON: {e}")
                
                # Display overall accuracy report
                self.log_message("\n" + "="*70)
                self.log_message("APPROACH 4: HYBRID - ACCURACY REPORT")
                self.log_message("="*70)
                
                self.log_message(f"\n📊 Distance Accuracy:")
                self.log_message(f"   Mean Accuracy: {overall_metrics['distance_accuracy']['mean_accuracy_pct']:.2f}%")
                self.log_message(f"   Median Accuracy: {overall_metrics['distance_accuracy']['median_accuracy_pct']:.2f}%")
                self.log_message(f"   Mean Absolute Error: {overall_metrics['distance_accuracy']['mean_absolute_error_m']:.2f} m")
                self.log_message(f"   RMSE: {overall_metrics['distance_accuracy']['rmse_m']:.2f} m")
                
                self.log_message(f"\n📊 Speed Accuracy (Source Vehicle):")
                self.log_message(f"   Mean Absolute Error: {overall_metrics['speed_accuracy']['source_vehicle']['mean_absolute_error_kmh']:.2f} km/h")
                self.log_message(f"   RMSE: {overall_metrics['speed_accuracy']['source_vehicle']['rmse_kmh']:.2f} km/h")
                
                self.log_message(f"\n📊 Speed Accuracy (Destination Vehicle):")
                self.log_message(f"   Mean Absolute Error: {overall_metrics['speed_accuracy']['destination_vehicle']['mean_absolute_error_kmh']:.2f} km/h")
                self.log_message(f"   RMSE: {overall_metrics['speed_accuracy']['destination_vehicle']['rmse_kmh']:.2f} km/h")
                
                self.log_message(f"\n📊 Waypoint Distribution:")
                self.log_message(f"   High Accuracy (≥90%): {overall_metrics['waypoint_distribution']['high_accuracy_90_plus']} waypoints")
                self.log_message(f"   Medium Accuracy (70-89%): {overall_metrics['waypoint_distribution']['medium_accuracy_70_89']} waypoints")
                self.log_message(f"   Low Accuracy (<70%): {overall_metrics['waypoint_distribution']['low_accuracy_below_70']} waypoints")
                
                self.log_message(f"\n📊 Best Waypoint: #{overall_metrics['best_waypoint']['waypoint']}")
                self.log_message(f"   Accuracy: {overall_metrics['best_waypoint']['accuracy_pct']:.2f}%")
                
                self.log_message(f"\n📊 Worst Waypoint: #{overall_metrics['worst_waypoint']['waypoint']}")
                self.log_message(f"   Accuracy: {overall_metrics['worst_waypoint']['accuracy_pct']:.2f}%")
                
                # Overall assessment
                mean_acc = overall_metrics['distance_accuracy']['mean_accuracy_pct']
                if mean_acc >= 80:
                    assessment = "EXCELLENT ✅"
                elif mean_acc >= 60:
                    assessment = "GOOD ✓"
                elif mean_acc >= 40:
                    assessment = "FAIR ⚠️"
                else:
                    assessment = "NEEDS IMPROVEMENT ❌"
                
                self.log_message(f"\n📊 Overall Assessment: {mean_acc:.2f}% - {assessment}")
                
                self.log_message("\n" + "="*70)
                self.log_message(f"✅ Analysis complete! Files saved to:")
                self.log_message(f"   📄 CSV: approach_4_hybrid_analysis.csv")
                self.log_message(f"   📄 JSON: approach_4_hybrid_summary.json")
                self.log_message(f"   📂 Location: {original_dir}")
                self.log_message("="*70)
            else:
                self.log_message("\n⚠️ No waypoint analysis data collected (vehicles may not have reached waypoints)")
            
            # Keep SUMO-GUI open for inspection
            self.log_message("\n🔍 Check SUMO-GUI:")
            self.log_message("   - Blue vehicle should follow hybrid trajectory")
            self.log_message("   - Red vehicle should follow hybrid trajectory")
            self.log_message("   - Both vehicles should stay on roads")
            self.log_message("   - Processed waypoints with hybrid approach")
            self.log_message("⏸️ Close SUMO-GUI when done inspecting...")
            
            # Keep simulation running for inspection
            while self.simulation_running:
                try:
                    traci.simulationStep()
                    time.sleep(0.1)
                except:
                    break
                    
        except Exception as e:
            self.log_message(f"❌ Simulation error: {e}")
        finally:
            try:
                traci.close()
                self.log_message("✅ SUMO simulation stopped")
            except:
                pass
            os.chdir(original_dir)
            
    def run(self):
        """Run the GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    app = V2VHybridSimulation()
    app.run()
