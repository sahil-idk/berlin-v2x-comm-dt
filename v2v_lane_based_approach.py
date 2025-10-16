#!/usr/bin/env python3
"""
V2V Lane-Based Simulation Approach
==================================

This approach focuses on lane-based positioning to prevent vehicles from going off-road.
Key improvements:
1. GPS coordinates mapped to specific lanes (not just edges)
2. Lane-based vehicle positioning using lane IDs and positions
3. Route validation to ensure connectivity
4. No moveToXY - pure route-based movement
5. Lane-aware waypoint following

Author: AI Assistant
Date: 2024
"""

import os
import sys
import time
import math
import json
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import subprocess
import traci
import sumolib
from sumolib.net import Net

# Configuration
SIMULATION_STEPS = 6000
CALIBRATION_FACTOR = 0.607

def kmh_to_ms(speed_kmh):
    """Convert km/h to m/s"""
    return speed_kmh / 3.6

def calculate_distance(pos1, pos2):
    """Calculate Euclidean distance"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def find_lane_for_gps(net, lat, lon, search_radius=100):
    """
    Find the best lane for GPS coordinates with lane-based positioning
    """
    x, y = net.convertLonLat2XY(lon, lat)
    
    # Get all edges within search radius
    nearby_edges = net.getNeighboringEdges(x, y, r=search_radius)
    
    if not nearby_edges:
        return None, None, float('inf')
    
    best_lane = None
    best_distance = float('inf')
    best_lane_pos = None
    
    for edge, edge_distance in nearby_edges:
        # Get all lanes on this edge
        lanes = edge.getLanes()
        
        for lane in lanes:
            # Get lane shape (list of points)
            lane_shape = lane.getShape()
            
            # Find closest point on lane to GPS coordinates
            for point in lane_shape:
                distance = calculate_distance((x, y), point)
                if distance < best_distance:
                    best_distance = distance
                    best_lane = lane
                    best_lane_pos = point
    
    return best_lane, best_lane_pos, best_distance

def create_lane_based_route(net, waypoints_df, vehicle_type='source'):
    """
    Create a route based on lane mapping for each waypoint
    """
    print(f"🗺️ Creating lane-based route for {vehicle_type}...")
    
    # Sample waypoints (every 3rd point for better coverage)
    sample_indices = range(0, len(waypoints_df), 3)
    sampled_waypoints = waypoints_df.iloc[sample_indices]
    
    print(f"📊 Original waypoints: {len(waypoints_df)}, Sampled: {len(sampled_waypoints)}")
    
    lane_waypoints = []
    
    for idx, row in sampled_waypoints.iterrows():
        if vehicle_type == 'source':
            lat = row['Latitude_source']
            lon = row['Longitude_source']
        else:
            lat = row['Latitude_destination']
            lon = row['Longitude_destination']
        
        # Find the best lane for this GPS point
        lane, lane_pos, distance = find_lane_for_gps(net, lat, lon)
        
        if lane and distance < 50:  # Only accept lanes within 50m
            lane_waypoints.append({
                'lane_id': lane.getID(),
                'edge_id': lane.getEdge().getID(),
                'lane_index': lane.getIndex(),
                'position': lane_pos,
                'distance': distance,
                'original_idx': idx
            })
            print(f"   ✅ Found lane: {lane.getID()} at distance {distance:.2f}m")
        else:
            print(f"   ❌ No suitable lane found for waypoint {idx}")
    
    if len(lane_waypoints) < 2:
        print("❌ Not enough valid lane waypoints found")
        return []
    
    # Create route from lane waypoints
    route_edges = []
    for i, wp in enumerate(lane_waypoints):
        edge_id = wp['edge_id']
        if edge_id not in route_edges:
            route_edges.append(edge_id)
    
    # Validate route connectivity
    if not validate_route_connectivity(net, route_edges):
        print("❌ Route connectivity validation failed")
        return []
    
    print(f"✅ Lane-based route created: {len(route_edges)} edges")
    return route_edges

def validate_route_connectivity(net, route_edges):
    """
    Validate that all edges in the route are connected
    """
    if len(route_edges) < 2:
        return True
    
    for i in range(len(route_edges) - 1):
        current_edge = net.getEdge(route_edges[i])
        next_edge = net.getEdge(route_edges[i + 1])
        
        # Check if next edge is reachable from current edge
        outgoing_edges = [edge.getID() for edge in current_edge.getOutgoing().keys()]
        
        if next_edge.getID() not in outgoing_edges:
            # Try to find a path between them
            try:
                path = net.getShortestPath(current_edge, next_edge)
                if not path or len(path[0]) == 0:
                    print(f"⚠️ No path found between {route_edges[i]} and {route_edges[i + 1]}")
                    return False
            except:
                print(f"⚠️ Path finding failed between {route_edges[i]} and {route_edges[i + 1]}")
                return False
    
    return True

def extend_route_safely(net, route):
    """
    Safely extend a route to ensure it has enough edges for proper vehicle movement
    """
    if len(route) >= 5:
        return route
    
    try:
        extended_route = route.copy()
        
        # Extend from the beginning
        if len(extended_route) > 0:
            first_edge = net.getEdge(extended_route[0])
            incoming_edges = [edge.getID() for edge in first_edge.getIncoming().keys()]
            if incoming_edges:
                extended_route.insert(0, incoming_edges[0])
        
        # Extend from the end
        if len(extended_route) > 0:
            last_edge = net.getEdge(extended_route[-1])
            outgoing_edges = [edge.getID() for edge in last_edge.getOutgoing().keys()]
            if outgoing_edges:
                extended_route.append(outgoing_edges[0])
        
        # Keep extending until we have enough edges
        while len(extended_route) < 5 and len(extended_route) > 0:
            last_edge = net.getEdge(extended_route[-1])
            outgoing_edges = [edge.getID() for edge in last_edge.getOutgoing().keys()]
            if outgoing_edges:
                extended_route.append(outgoing_edges[0])
            else:
                break
        
        return extended_route
    except Exception as e:
        print(f"⚠️ Route extension failed: {e}")
        return route

class V2VLaneBasedSimulation:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("V2V Lane-Based Simulation")
        self.root.geometry("800x700")
        
        # Variables
        self.num_waypoints = tk.IntVar(value=30)
        self.use_realistic_speed = tk.BooleanVar(value=True)
        self.simulation_running = False
        self.simulation_thread = None
        self.analysis_data = None
        self.analysis_complete = False
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="V2V Lane-Based Simulation", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Number of waypoints
        ttk.Label(config_frame, text="Number of Waypoints:").grid(row=0, column=0, sticky=tk.W)
        waypoints_scale = ttk.Scale(config_frame, from_=5, to=200, variable=self.num_waypoints, 
                                   orient=tk.HORIZONTAL, length=300)
        waypoints_scale.grid(row=0, column=1, padx=(10, 0))
        
        waypoints_value = ttk.Label(config_frame, textvariable=self.num_waypoints)
        waypoints_value.grid(row=0, column=2, padx=(10, 0))
        
        # Realistic speed option
        speed_check = ttk.Checkbutton(config_frame, text="Use Realistic Speed from Dataset", 
                                     variable=self.use_realistic_speed)
        speed_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="Start Simulation", 
                                      command=self.start_simulation)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop Simulation", 
                                     command=self.stop_simulation, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        self.export_button = ttk.Button(control_frame, text="Export Analysis", 
                                      command=self.export_analysis, state=tk.DISABLED)
        self.export_button.grid(row=0, column=2)
        
        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(progress_frame, text="Progress:").grid(row=0, column=0, sticky=tk.W)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))
        
        # Status and log
        log_frame = ttk.LabelFrame(main_frame, text="Status & Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        progress_frame.columnconfigure(1, weight=1)
        
    def log_message(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_simulation(self):
        """Start the simulation in a separate thread"""
        if not self.simulation_running:
            self.simulation_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.simulation_thread = threading.Thread(target=self.run_simulation)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            
    def stop_simulation(self):
        """Stop the simulation"""
        self.simulation_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
    def export_analysis(self):
        """Export analysis results to additional formats"""
        if not self.analysis_complete or self.analysis_data is None:
            self.log_message("❌ No analysis data available to export")
            return
        
        try:
            import tkinter.filedialog as fd
            
            # Save analysis data as Excel with multiple sheets
            filename = fd.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Analysis Results"
            )
            
            if filename:
                if filename.endswith('.xlsx'):
                    # Export as Excel with multiple sheets
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        # Main analysis data
                        analysis_df = pd.DataFrame(self.analysis_data)
                        analysis_df.to_excel(writer, sheet_name='Analysis_Data', index=False)
                        
                        # Summary statistics
                        summary_data = {
                            'Metric': ['Mean Accuracy (%)', 'Median Accuracy (%)', 'RMSE (m)', 'MAE (m)', 
                                     'Correlation', 'Calibrated Correlation', 'Total Waypoints'],
                            'Value': [analysis_df['accuracy'].mean(), analysis_df['accuracy'].median(),
                                    np.sqrt(np.mean(analysis_df['error']**2)), np.mean(np.abs(analysis_df['error'])),
                                    analysis_df['actual_distance'].corr(analysis_df['simulated_distance']),
                                    analysis_df['actual_distance'].corr(analysis_df['calibrated_distance']),
                                    len(analysis_df)]
                        }
                        summary_df = pd.DataFrame(summary_data)
                        summary_df.to_excel(writer, sheet_name='Summary', index=False)
                        
                        # Accuracy distribution
                        acc_ranges = ['Excellent (≥95%)', 'Very Good (90-94%)', 'Good (80-89%)', 
                                    'Fair (70-79%)', 'Poor (50-69%)', 'Very Poor (<50%)']
                        acc_counts = [
                            (analysis_df['accuracy'] >= 95).sum(),
                            ((analysis_df['accuracy'] >= 90) & (analysis_df['accuracy'] < 95)).sum(),
                            ((analysis_df['accuracy'] >= 80) & (analysis_df['accuracy'] < 90)).sum(),
                            ((analysis_df['accuracy'] >= 70) & (analysis_df['accuracy'] < 80)).sum(),
                            ((analysis_df['accuracy'] >= 50) & (analysis_df['accuracy'] < 70)).sum(),
                            (analysis_df['accuracy'] < 50).sum()
                        ]
                        acc_percentages = [count/len(analysis_df)*100 for count in acc_counts]
                        
                        dist_data = {
                            'Accuracy Range': acc_ranges,
                            'Count': acc_counts,
                            'Percentage': acc_percentages
                        }
                        dist_df = pd.DataFrame(dist_data)
                        dist_df.to_excel(writer, sheet_name='Distribution', index=False)
                    
                    self.log_message(f"✅ Analysis exported to Excel: {filename}")
                    
                elif filename.endswith('.csv'):
                    # Export as CSV
                    analysis_df = pd.DataFrame(self.analysis_data)
                    analysis_df.to_csv(filename, index=False)
                    self.log_message(f"✅ Analysis exported to CSV: {filename}")
                
        except Exception as e:
            self.log_message(f"❌ Export failed: {e}")
        
    def run_simulation(self):
        """Run the lane-based V2V simulation"""
        try:
            # Store original directory
            original_dir = os.getcwd()
            
            # Change to SUMO directory
            sumo_dir = "berlin-sumo-closed-netwokr"
            if not os.path.exists(sumo_dir):
                self.log_message("❌ SUMO directory not found")
                return
            
            os.chdir(sumo_dir)
            self.log_message(f"📂 Working in: {os.getcwd()}")
            
            # Load GPS data
            self.log_message("📋 Loading GPS data...")
            waypoints_df = pd.read_csv("../vehicle_2_4_first_200.csv")
            num_waypoints = min(self.num_waypoints.get(), len(waypoints_df))
            waypoints_df = waypoints_df.head(num_waypoints)
            self.log_message(f"✅ Loaded {len(waypoints_df)} GPS waypoints")
            
            # Load SUMO network
            self.log_message("🗺️ Loading SUMO network...")
            net = sumolib.net.readNet("osm.net.xml.gz")
            self.log_message(f"✅ Network loaded: {len(net.getEdges())} edges")
            
            # Create lane-based routes
            self.log_message(f"\n🔧 Creating lane-based routes...")
            source_route = create_lane_based_route(net, waypoints_df, 'source')
            dest_route = create_lane_based_route(net, waypoints_df, 'destination')
            
            if not source_route or not dest_route:
                self.log_message("❌ Failed to create lane-based routes")
                return
            
            # Extend routes safely
            source_route = extend_route_safely(net, source_route)
            dest_route = extend_route_safely(net, dest_route)
            
            self.log_message(f"✅ Source route: {len(source_route)} edges")
            self.log_message(f"✅ Destination route: {len(dest_route)} edges")
            
            # Create route files
            with open('lane_based_source_route.rou.xml', 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<routes>\n')
                f.write('  <route id="lane_source_route" edges="' + ' '.join(source_route) + '"/>\n')
                f.write('  <vType id="lane_source_vType" accel="2.0" decel="4.5" sigma="0.5" length="4.5" maxSpeed="50" guiShape="passenger" color="blue"/>\n')
                f.write('</routes>\n')
            
            with open('lane_based_dest_route.rou.xml', 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<routes>\n')
                f.write('  <route id="lane_dest_route" edges="' + ' '.join(dest_route) + '"/>\n')
                f.write('  <vType id="lane_dest_vType" accel="2.0" decel="4.5" sigma="0.5" length="4.5" maxSpeed="50" guiShape="passenger" color="red"/>\n')
                f.write('</routes>\n')
            
            # Create SUMO config
            with open('lane_based.sumocfg', 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<configuration>\n')
                f.write('  <input>\n')
                f.write('    <net-file value="osm.net.xml.gz"/>\n')
                f.write('    <route-files value="lane_based_source_route.rou.xml,lane_based_dest_route.rou.xml"/>\n')
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
            sumo_cmd = ["sumo-gui", "-c", "lane_based.sumocfg"]
            self.log_message(f"\n🚀 Starting SUMO-GUI with lane-based approach...")
            
            traci.start(sumo_cmd)
            time.sleep(3)  # Wait for SUMO to initialize
            
            # Add vehicles with lane-based positioning
            self.log_message("🚗 Adding vehicles with lane-based positioning...")
            
            # Add source vehicle
            traci.vehicle.add("lane_v2v_source", "lane_source_route", typeID="lane_source_vType", depart=0)
            
            # Add destination vehicle  
            traci.vehicle.add("lane_v2v_dest", "lane_dest_route", typeID="lane_dest_vType", depart=0)
            
            # Wait for vehicles to be added
            time.sleep(2)
            
            # Set vehicle properties
            traci.vehicle.setColor("lane_v2v_source", (0, 0, 255, 255))  # Blue
            traci.vehicle.setColor("lane_v2v_dest", (255, 0, 0, 255))    # Red
            
            # Set vehicle control modes to prevent stalling
            traci.vehicle.setSpeedMode("lane_v2v_source", 0)  # No speed adaptation
            traci.vehicle.setSpeedMode("lane_v2v_dest", 0)    # No speed adaptation
            traci.vehicle.setLaneChangeMode("lane_v2v_source", 0)  # No lane changes
            traci.vehicle.setLaneChangeMode("lane_v2v_dest", 0)    # No lane changes
            
            self.log_message(f"✅ Vehicles added with lane-based approach")
            
            # Prepare waypoint coordinates for analysis
            waypoint_coords = []
            for idx, row in waypoints_df.iterrows():
                src_x, src_y = net.convertLonLat2XY(row['Longitude_source'], row['Latitude_source'])
                dst_x, dst_y = net.convertLonLat2XY(row['Longitude_destination'], row['Latitude_destination'])
                
                waypoint_coords.append({
                    'source': (src_x, src_y),
                    'dest': (dst_x, dst_y),
                    'actual_distance': row['distance'],
                    'source_speed_kmh': row['speed_kmh_source'],
                    'dest_speed_kmh': row['speed_kmh_destination']
                })
            
            # Simulation loop with lane-based approach
            self.log_message(f"\n🎯 Starting simulation with lane-based approach...")
            
            step = 0
            current_waypoint = 0
            source_active = False
            dest_active = False
            
            # Analysis data
            analysis_data = []
            self.analysis_data = analysis_data
            self.analysis_complete = False
            
            while step < SIMULATION_STEPS and self.simulation_running:
                traci.simulationStep()
                step += 1
                
                progress = min(100, (step / SIMULATION_STEPS) * 100)
                self.progress_var.set(progress)
                
                vehicles = traci.vehicle.getIDList()
                
                # Source vehicle
                if "lane_v2v_source" in vehicles:
                    if not source_active:
                        self.log_message(f"✅ Step {step}: Source vehicle active")
                        source_active = True
                    
                    src_pos = traci.vehicle.getPosition("lane_v2v_source")
                    src_speed = traci.vehicle.getSpeed("lane_v2v_source")
                    
                    # Set realistic speed from dataset
                    if self.use_realistic_speed.get() and current_waypoint < len(waypoint_coords):
                        target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['source_speed_kmh'])
                        traci.vehicle.setSpeed("lane_v2v_source", target_speed_ms)
                    else:
                        # Ensure minimum speed to prevent stalling
                        traci.vehicle.setSpeed("lane_v2v_source", 5.0)  # 5 m/s minimum
                
                # Destination vehicle
                if "lane_v2v_dest" in vehicles:
                    if not dest_active:
                        self.log_message(f"✅ Step {step}: Destination vehicle active")
                        dest_active = True
                    
                    dst_pos = traci.vehicle.getPosition("lane_v2v_dest")
                    dst_speed = traci.vehicle.getSpeed("lane_v2v_dest")
                    
                    # Set realistic speed from dataset
                    if self.use_realistic_speed.get() and current_waypoint < len(waypoint_coords):
                        target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['dest_speed_kmh'])
                        traci.vehicle.setSpeed("lane_v2v_dest", target_speed_ms)
                    else:
                        # Ensure minimum speed to prevent stalling
                        traci.vehicle.setSpeed("lane_v2v_dest", 5.0)  # 5 m/s minimum
                
                # Calculate distances and analyze every 50 steps
                if step % 50 == 0 and source_active and dest_active and current_waypoint < len(waypoint_coords):
                    wp = waypoint_coords[current_waypoint]
                    
                    # Calculate simulated distance
                    simulated_distance = calculate_distance(src_pos, dst_pos)
                    
                    # Apply calibration factor
                    calibrated_distance = simulated_distance * CALIBRATION_FACTOR
                    actual_distance = wp['actual_distance']
                    
                    # Calculate error and accuracy
                    error = calibrated_distance - actual_distance
                    error_percentage = (error / actual_distance) * 100 if actual_distance > 0 else 0
                    accuracy = max(0, 100 - abs(error_percentage))
                    
                    analysis_data.append({
                        'waypoint': current_waypoint,
                        'actual_distance': actual_distance,
                        'simulated_distance': simulated_distance,
                        'calibrated_distance': calibrated_distance,
                        'error': error,
                        'error_percentage': error_percentage,
                        'accuracy': accuracy,
                        'source_speed_kmh': wp['source_speed_kmh'],
                        'dest_speed_kmh': wp['dest_speed_kmh']
                    })
                    
                    current_waypoint += 1
                    
                    if current_waypoint % 10 == 0:
                        self.log_message(f"📊 Processed {current_waypoint}/{len(waypoint_coords)} waypoints")
                    
                    # Stop simulation when all waypoints are processed
                    if current_waypoint >= len(waypoint_coords):
                        self.log_message(f"✅ All {len(waypoint_coords)} waypoints processed!")
                        break
                
                time.sleep(0.05)  # Slower simulation for better observation
            
            # Save analysis results
            if analysis_data:
                analysis_df = pd.DataFrame(analysis_data)
                
                # Save to main project directory
                analysis_file = os.path.join(original_dir, "lane_based_distance_accuracy_analysis.csv")
                analysis_df.to_csv(analysis_file, index=False)
                
                # Calculate comprehensive summary statistics
                mean_accuracy = analysis_df['accuracy'].mean()
                median_accuracy = analysis_df['accuracy'].median()
                std_accuracy = analysis_df['accuracy'].std()
                min_accuracy = analysis_df['accuracy'].min()
                max_accuracy = analysis_df['accuracy'].max()
                
                rmse = np.sqrt(np.mean(analysis_df['error']**2))
                mae = np.mean(np.abs(analysis_df['error']))
                mean_error = analysis_df['error'].mean()
                std_error = analysis_df['error'].std()
                
                # Correlation analysis
                correlation = analysis_df['actual_distance'].corr(analysis_df['simulated_distance'])
                calibrated_correlation = analysis_df['actual_distance'].corr(analysis_df['calibrated_distance'])
                
                # Accuracy distribution
                excellent_count = int((analysis_df['accuracy'] >= 95).sum())
                very_good_count = int(((analysis_df['accuracy'] >= 90) & (analysis_df['accuracy'] < 95)).sum())
                good_count = int(((analysis_df['accuracy'] >= 80) & (analysis_df['accuracy'] < 90)).sum())
                fair_count = int(((analysis_df['accuracy'] >= 70) & (analysis_df['accuracy'] < 80)).sum())
                poor_count = int(((analysis_df['accuracy'] >= 50) & (analysis_df['accuracy'] < 70)).sum())
                very_poor_count = int((analysis_df['accuracy'] < 50).sum())
                
                # Best and worst waypoints
                best_waypoint_idx = analysis_df['accuracy'].idxmax()
                worst_waypoint_idx = analysis_df['accuracy'].idxmin()
                best_waypoint = analysis_df.loc[best_waypoint_idx]
                worst_waypoint = analysis_df.loc[worst_waypoint_idx]
                
                summary = {
                    'approach': 'Lane-Based',
                    'total_waypoints': len(analysis_data),
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                    
                    # Accuracy statistics
                    'mean_accuracy': float(mean_accuracy),
                    'median_accuracy': float(median_accuracy),
                    'std_accuracy': float(std_accuracy),
                    'min_accuracy': float(min_accuracy),
                    'max_accuracy': float(max_accuracy),
                    
                    # Error statistics
                    'mean_error': float(mean_error),
                    'median_error': float(analysis_df['error'].median()),
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'std_error': float(std_error),
                    'min_error': float(analysis_df['error'].min()),
                    'max_error': float(analysis_df['error'].max()),
                    
                    # Correlation
                    'correlation': float(correlation),
                    'calibrated_correlation': float(calibrated_correlation),
                    
                    # Accuracy distribution
                    'excellent_count': excellent_count,
                    'very_good_count': very_good_count,
                    'good_count': good_count,
                    'fair_count': fair_count,
                    'poor_count': poor_count,
                    'very_poor_count': very_poor_count,
                    
                    # Best/worst waypoints
                    'best_waypoint': {
                        'waypoint': int(best_waypoint['waypoint']),
                        'accuracy': float(best_waypoint['accuracy']),
                        'actual_distance': float(best_waypoint['actual_distance']),
                        'simulated_distance': float(best_waypoint['simulated_distance']),
                        'calibrated_distance': float(best_waypoint['calibrated_distance']),
                        'error': float(best_waypoint['error'])
                    },
                    'worst_waypoint': {
                        'waypoint': int(worst_waypoint['waypoint']),
                        'accuracy': float(worst_waypoint['accuracy']),
                        'actual_distance': float(worst_waypoint['actual_distance']),
                        'simulated_distance': float(worst_waypoint['simulated_distance']),
                        'calibrated_distance': float(worst_waypoint['calibrated_distance']),
                        'error': float(worst_waypoint['error'])
                    },
                    
                    # Configuration
                    'calibration_factor': CALIBRATION_FACTOR,
                    'simulation_steps': SIMULATION_STEPS,
                    'realistic_speed_enabled': self.use_realistic_speed.get()
                }
                
                summary_file = os.path.join(original_dir, "lane_based_simulation_summary.json")
                with open(summary_file, 'w') as f:
                    json.dump(summary, f, indent=2)
                
                # Overall assessment
                if mean_accuracy >= 90:
                    assessment = "EXCELLENT"
                    emoji = "🟢"
                elif mean_accuracy >= 80:
                    assessment = "VERY GOOD"
                    emoji = "🟡"
                elif mean_accuracy >= 70:
                    assessment = "GOOD"
                    emoji = "🟠"
                elif mean_accuracy >= 50:
                    assessment = "FAIR"
                    emoji = "🔴"
                else:
                    assessment = "POOR"
                    emoji = "⚫"
                
                self.log_message(f"\n📊 COMPREHENSIVE DISTANCE ACCURACY ANALYSIS:")
                self.log_message(f"   {emoji} Overall Assessment: {assessment} - {mean_accuracy:.2f}% Mean Accuracy")
                self.log_message(f"")
                self.log_message(f"📈 ACCURACY STATISTICS:")
                self.log_message(f"   Mean Accuracy: {mean_accuracy:.2f}%")
                self.log_message(f"   Median Accuracy: {median_accuracy:.2f}%")
                self.log_message(f"   Standard Deviation: {std_accuracy:.2f}%")
                self.log_message(f"   Min Accuracy: {min_accuracy:.2f}%")
                self.log_message(f"   Max Accuracy: {max_accuracy:.2f}%")
                self.log_message(f"")
                self.log_message(f"📏 ERROR ANALYSIS:")
                self.log_message(f"   Mean Error: {mean_error:.2f} m")
                self.log_message(f"   Mean Absolute Error (MAE): {mae:.2f} m")
                self.log_message(f"   Root Mean Square Error (RMSE): {rmse:.2f} m")
                self.log_message(f"   Error Standard Deviation: {std_error:.2f} m")
                self.log_message(f"")
                self.log_message(f"🔗 CORRELATION ANALYSIS:")
                self.log_message(f"   Actual vs Simulated Distance: {correlation:.4f}")
                self.log_message(f"   Actual vs Calibrated Distance: {calibrated_correlation:.4f}")
                self.log_message(f"")
                self.log_message(f"📊 ACCURACY DISTRIBUTION:")
                self.log_message(f"   Excellent (≥95%): {excellent_count} waypoints ({excellent_count/len(analysis_data)*100:.1f}%)")
                self.log_message(f"   Very Good (90-94%): {very_good_count} waypoints ({very_good_count/len(analysis_data)*100:.1f}%)")
                self.log_message(f"   Good (80-89%): {good_count} waypoints ({good_count/len(analysis_data)*100:.1f}%)")
                self.log_message(f"   Fair (70-79%): {fair_count} waypoints ({fair_count/len(analysis_data)*100:.1f}%)")
                self.log_message(f"   Poor (50-69%): {poor_count} waypoints ({poor_count/len(analysis_data)*100:.1f}%)")
                self.log_message(f"   Very Poor (<50%): {very_poor_count} waypoints ({very_poor_count/len(analysis_data)*100:.1f}%)")
                self.log_message(f"")
                self.log_message(f"🏆 BEST PERFORMING WAYPOINT:")
                self.log_message(f"   Waypoint #{best_waypoint['waypoint']}: {best_waypoint['accuracy']:.2f}% accuracy")
                self.log_message(f"   Actual: {best_waypoint['actual_distance']:.2f}m, Simulated: {best_waypoint['simulated_distance']:.2f}m")
                self.log_message(f"   Calibrated: {best_waypoint['calibrated_distance']:.2f}m, Error: {best_waypoint['error']:.2f}m")
                self.log_message(f"")
                self.log_message(f"⚠️ WORST PERFORMING WAYPOINT:")
                self.log_message(f"   Waypoint #{worst_waypoint['waypoint']}: {worst_waypoint['accuracy']:.2f}% accuracy")
                self.log_message(f"   Actual: {worst_waypoint['actual_distance']:.2f}m, Simulated: {worst_waypoint['simulated_distance']:.2f}m")
                self.log_message(f"   Calibrated: {worst_waypoint['calibrated_distance']:.2f}m, Error: {worst_waypoint['error']:.2f}m")
                
                self.log_message(f"\n✅ Analysis complete! Files saved to:")
                self.log_message(f"   📄 CSV: {analysis_file}")
                self.log_message(f"   📄 JSON: {summary_file}")
                
                # Enable export button
                self.analysis_complete = True
                self.export_button.config(state=tk.NORMAL)
            
            # Keep SUMO-GUI open for inspection
            self.log_message(f"\n🔍 Simulation complete. Keeping SUMO-GUI open for inspection...")
            self.log_message(f"   Press 'Stop Simulation' to close SUMO-GUI")
            
            # Show final vehicle positions
            if source_active and dest_active:
                final_src_pos = traci.vehicle.getPosition("lane_v2v_source")
                final_dst_pos = traci.vehicle.getPosition("lane_v2v_dest")
                final_distance = calculate_distance(final_src_pos, final_dst_pos)
                self.log_message(f"📍 Final vehicle positions:")
                self.log_message(f"   Source: {final_src_pos}")
                self.log_message(f"   Destination: {final_dst_pos}")
                self.log_message(f"   Final distance: {final_distance:.2f}m")
            
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
    app = V2VLaneBasedSimulation()
    app.run()
