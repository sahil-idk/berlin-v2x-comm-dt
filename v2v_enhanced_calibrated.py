#!/usr/bin/env python3
"""
Enhanced Calibrated V2V Simulation with GUI Controls
Based on v2v_enhanced_robust.py with calibration factor applied
Uses route-based navigation (proven to work!) with distance calibration
"""

import traci
import pandas as pd
import sumolib
import os
import time
import math
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json

# ===== CALIBRATION CONFIGURATION =====
CALIBRATION_FACTOR = 0.607  # Derived from previous analysis

def calculate_distance(pos1, pos2):
    """Calculate Euclidean distance between two positions"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def apply_calibration(distance):
    """Apply calibration factor to distance"""
    return distance * CALIBRATION_FACTOR

def find_optimal_path_through_waypoints(net, waypoints_df, vehicle_type='source', max_search_radius=300):
    """Find an optimal connected path through waypoints using improved routing"""
    edges_with_positions = []
    
    for idx, row in waypoints_df.iterrows():
        if vehicle_type == 'source':
            lat = row['Latitude_source']
            lon = row['Longitude_source']
        else:
            lat = row['Latitude_destination']
            lon = row['Longitude_destination']
        
        x, y = net.convertLonLat2XY(lon, lat)
        
        # Find nearest edge with progressive radius increase
        edge_found = False
        search_radius = 50
        while search_radius <= max_search_radius and not edge_found:
            nearby_edges = net.getNeighboringEdges(x, y, r=search_radius)
            if nearby_edges:
                edge = min(nearby_edges, key=lambda e: e[1])[0]
                edges_with_positions.append({
                    'edge': edge,
                    'edge_id': edge.getID(),
                    'position': (x, y),
                    'index': idx,
                    'search_radius': search_radius
                })
                edge_found = True
            else:
                search_radius += 50
        
        if not edge_found:
            print(f"⚠️ Warning: Could not find edge for waypoint {idx} within {max_search_radius}m")
    
    # Build optimized route
    if not edges_with_positions:
        return [], []
    
    route = []
    waypoint_edges = []
    
    for i in range(len(edges_with_positions)):
        current = edges_with_positions[i]
        
        if i == 0:
            route.append(current['edge_id'])
            waypoint_edges.append(current['edge_id'])
        else:
            prev = edges_with_positions[i-1]
            
            # Find shortest path between edges
            try:
                path = net.getShortestPath(prev['edge'], current['edge'])
                if path and path[0]:
                    for edge in path[0]:
                        if edge.getID() not in route:
                            route.append(edge.getID())
                    if current['edge_id'] not in route:
                        route.append(current['edge_id'])
                    waypoint_edges.append(current['edge_id'])
                else:
                    if current['edge_id'] not in route:
                        route.append(current['edge_id'])
                    waypoint_edges.append(current['edge_id'])
            except Exception as e:
                print(f"⚠️ Path finding failed: {e}")
                if current['edge_id'] not in route:
                    route.append(current['edge_id'])
                waypoint_edges.append(current['edge_id'])
    
    return route, waypoint_edges

class CalibratedV2VSimulationGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced Calibrated V2V Simulation Control")
        self.root.geometry("600x550")
        
        # Simulation state
        self.simulation_running = False
        self.simulation_thread = None
        self.sumo_process = None
        
        # Configuration variables
        self.num_waypoints = tk.IntVar(value=30)
        self.simulation_speed = tk.DoubleVar(value=1.0)
        self.vehicle_speed = tk.IntVar(value=15)
        self.calibration_enabled = tk.BooleanVar(value=True)
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI interface"""
        # Title
        title_label = tk.Label(self.root, text="Enhanced Calibrated V2V Simulation", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Calibration info
        calib_label = tk.Label(self.root, text=f"Calibration Factor: {CALIBRATION_FACTOR}", 
                              font=("Arial", 10), fg="blue")
        calib_label.pack()
        
        # Configuration frame
        config_frame = ttk.LabelFrame(self.root, text="Simulation Configuration", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        # Number of waypoints
        ttk.Label(config_frame, text="Number of Waypoints:").grid(row=0, column=0, sticky="w", pady=2)
        waypoints_scale = ttk.Scale(config_frame, from_=5, to=100, variable=self.num_waypoints, 
                                   orient="horizontal", length=200)
        waypoints_scale.grid(row=0, column=1, padx=5)
        waypoints_label = ttk.Label(config_frame, textvariable=self.num_waypoints)
        waypoints_label.grid(row=0, column=2, padx=5)
        
        # Vehicle speed
        ttk.Label(config_frame, text="Vehicle Speed (m/s):").grid(row=1, column=0, sticky="w", pady=2)
        speed_scale = ttk.Scale(config_frame, from_=5, to=30, variable=self.vehicle_speed, 
                               orient="horizontal", length=200)
        speed_scale.grid(row=1, column=1, padx=5)
        speed_label = ttk.Label(config_frame, textvariable=self.vehicle_speed)
        speed_label.grid(row=1, column=2, padx=5)
        
        # Simulation speed
        ttk.Label(config_frame, text="Simulation Speed:").grid(row=2, column=0, sticky="w", pady=2)
        sim_speed_scale = ttk.Scale(config_frame, from_=0.1, to=5.0, variable=self.simulation_speed, 
                                   orient="horizontal", length=200)
        sim_speed_scale.grid(row=2, column=1, padx=5)
        sim_speed_label = ttk.Label(config_frame, textvariable=self.simulation_speed)
        sim_speed_label.grid(row=2, column=2, padx=5)
        
        # Calibration checkbox
        calib_check = ttk.Checkbutton(config_frame, text="Apply Calibration (0.607)", 
                                     variable=self.calibration_enabled)
        calib_check.grid(row=3, column=0, columnspan=3, sticky="w", pady=5)
        
        # Control buttons frame
        control_frame = ttk.LabelFrame(self.root, text="Simulation Control", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Buttons
        self.start_button = ttk.Button(control_frame, text="Start Simulation", 
                                      command=self.start_simulation)
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", 
                                     command=self.stop_simulation, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(self.root, text="Simulation Status", padding=10)
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Status text
        self.status_text = tk.Text(status_frame, height=15, width=70)
        scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        
    def log_message(self, message):
        """Add message to status text"""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_simulation(self):
        """Start the simulation in a separate thread"""
        if self.simulation_running:
            return
            
        self.simulation_running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        # Clear status
        self.status_text.delete(1.0, tk.END)
        
        # Start simulation thread
        self.simulation_thread = threading.Thread(target=self.run_simulation)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
    def stop_simulation(self):
        """Stop the simulation"""
        self.simulation_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        # Clean up SUMO
        try:
            traci.close()
        except:
            pass
            
        self.log_message("🛑 Simulation stopped by user")
        
    def run_simulation(self):
        """Main simulation function - SAME FLOW as v2v_enhanced_robust.py"""
        try:
            self.log_message("="*70)
            self.log_message("ENHANCED CALIBRATED V2V SIMULATION")
            self.log_message("="*70)
            self.log_message(f"📊 Calibration: {'ENABLED' if self.calibration_enabled.get() else 'DISABLED'} (Factor: {CALIBRATION_FACTOR})")
            
            # Configuration
            NUM_WAYPOINTS = self.num_waypoints.get()
            VEHICLE_SPEED = self.vehicle_speed.get()
            SIMULATION_STEPS = 3000
            
            original_dir = os.getcwd()
            self.log_message(f"📁 Output files will be saved to: {original_dir}")
            
            # Change to SUMO directory
            os.chdir('berlin-sumo-closed-netwokr')
            self.log_message(f"📁 Changed to SUMO directory")
            
            # Load network
            self.log_message("📍 Loading SUMO network...")
            net = sumolib.net.readNet('osm.net.xml.gz')
            self.log_message(f"✅ Network loaded: {len(net.getEdges())} edges")
            
            # Load GPS data
            self.log_message(f"📍 Loading GPS data (first {NUM_WAYPOINTS} waypoints)...")
            df = pd.read_csv('../vehicle_2_4_first_200.csv')
            waypoints_df = df.head(NUM_WAYPOINTS)
            self.log_message(f"✅ Loaded {len(waypoints_df)} GPS waypoints")
            
            # Find optimal paths - SAME AS ENHANCED ROBUST
            self.log_message("📍 Computing optimal routes through GPS waypoints...")
            source_route, source_waypoint_edges = find_optimal_path_through_waypoints(net, waypoints_df, 'source')
            dest_route, dest_waypoint_edges = find_optimal_path_through_waypoints(net, waypoints_df, 'destination')
            
            self.log_message(f"✅ Source route: {len(source_route)} edges")
            self.log_message(f"✅ Destination route: {len(dest_route)} edges")
            
            # Validate routes - SAME AS ENHANCED ROBUST
            if len(source_route) < 2:
                self.log_message("⚠️ Source route too short, extending...")
                edge = net.getEdge(source_route[0]) if source_route else list(net.getEdges())[0]
                outgoing = edge.getOutgoing()
                if outgoing:
                    source_route.append(list(outgoing.keys())[0].getID())
            
            if len(dest_route) < 2:
                self.log_message("⚠️ Destination route too short, extending...")
                edge = net.getEdge(dest_route[0]) if dest_route else list(net.getEdges())[0]
                outgoing = edge.getOutgoing()
                if outgoing:
                    dest_route.append(list(outgoing.keys())[0].getID())
            
            # Create route file - SAME AS ENHANCED ROBUST
            self.log_message("📍 Creating route file...")
            route_file = 'v2v_enhanced_calibrated_routes.rou.xml'
            with open(route_file, 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')
                
                # Define vehicle types with 3D car shape
                f.write('    <!-- Vehicle Types with 3D visualization -->\n')
                f.write(f'    <vType id="v2v_source_type" accel="2.6" decel="4.5" sigma="0.5" ')
                f.write(f'length="4.5" width="1.8" height="1.5" minGap="2.5" ')
                f.write(f'maxSpeed="{VEHICLE_SPEED}" guiShape="passenger" color="0,0,255"/>\n')
                
                f.write(f'    <vType id="v2v_dest_type" accel="2.6" decel="4.5" sigma="0.5" ')
                f.write(f'length="4.5" width="1.8" height="1.5" minGap="2.5" ')
                f.write(f'maxSpeed="{VEHICLE_SPEED}" guiShape="passenger" color="255,0,0"/>\n')
                
                # Define routes
                f.write('\n    <!-- Routes through GPS waypoints -->\n')
                f.write(f'    <route id="source_route" edges="{" ".join(source_route)}"/>\n')
                f.write(f'    <route id="dest_route" edges="{" ".join(dest_route)}"/>\n')
                
                # Define vehicles
                f.write('\n    <!-- Vehicles -->\n')
                f.write('    <vehicle id="v2v_source" type="v2v_source_type" ')
                f.write('route="source_route" depart="0" departLane="best" departSpeed="0"/>\n')
                
                f.write('    <vehicle id="v2v_dest" type="v2v_dest_type" ')
                f.write('route="dest_route" depart="0" departLane="best" departSpeed="0"/>\n')
                
                f.write('</routes>\n')
            
            self.log_message(f"✅ Route file created: {route_file}")
            
            # Create SUMO config - SAME AS ENHANCED ROBUST
            self.log_message("📍 Creating SUMO configuration...")
            config_file = 'v2v_enhanced_calibrated.sumocfg'
            with open(config_file, 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<configuration>\n')
                f.write('    <input>\n')
                f.write('        <net-file value="osm.net.xml.gz"/>\n')
                f.write(f'        <route-files value="{route_file}"/>\n')
                f.write('        <additional-files value="osm.poly.xml.gz"/>\n')
                f.write('    </input>\n')
                f.write('    <time>\n')
                f.write('        <begin value="0"/>\n')
                f.write('        <step-length value="0.1"/>\n')
                f.write('    </time>\n')
                f.write('    <processing>\n')
                f.write('        <collision.check-junctions value="true"/>\n')
                f.write('        <collision.action value="warn"/>\n')
                f.write('    </processing>\n')
                f.write('</configuration>\n')
            
            # Start SUMO-GUI - SAME AS ENHANCED ROBUST
            self.log_message("🚀 Starting SUMO-GUI...")
            sumo_cmd = ["sumo-gui", "-c", config_file, "--start", "--quit-on-end"]
            traci.start(sumo_cmd)
            time.sleep(3)
            
            # Add waypoint POIs - SAME AS ENHANCED ROBUST
            self.log_message("📍 Adding waypoint markers...")
            waypoint_coords = []
            for idx, row in waypoints_df.iterrows():
                src_x, src_y = net.convertLonLat2XY(row['Longitude_source'], row['Latitude_source'])
                traci.poi.add(
                    f"src_wp_{idx}",
                    src_x, src_y,
                    color=(0, 0, 255, 128),
                    poiType="source",
                    layer=100
                )
                
                dst_x, dst_y = net.convertLonLat2XY(row['Longitude_destination'], row['Latitude_destination'])
                traci.poi.add(
                    f"dst_wp_{idx}",
                    dst_x, dst_y,
                    color=(255, 0, 0, 128),
                    poiType="destination",
                    layer=100
                )
                
                waypoint_coords.append({
                    'source': (src_x, src_y),
                    'dest': (dst_x, dst_y),
                    'actual_distance': row['distance']
                })
            
            self.log_message(f"✅ Added {len(waypoint_coords)*2} waypoint markers")
            
            # Run simulation - SAME AS ENHANCED ROBUST
            self.log_message("🎯 Starting simulation...")
            self.log_message("-"*70)
            
            step = 0
            source_active = False
            dest_active = False
            last_log_step = 0
            
            # Metrics tracking (WITH CALIBRATION)
            distances_raw = []
            distances_calibrated = []
            source_progress = []
            dest_progress = []
            
            while step < SIMULATION_STEPS and self.simulation_running:
                traci.simulationStep()
                step += 1
                
                # Update progress
                progress = min(100, (step / SIMULATION_STEPS) * 100)
                self.progress_var.set(progress)
                
                # Get current vehicles
                vehicles = traci.vehicle.getIDList()
                
                # Check vehicle status
                if "v2v_source" in vehicles:
                    if not source_active:
                        self.log_message(f"✅ Step {step}: Source vehicle active")
                        source_active = True
                    
                    src_pos = traci.vehicle.getPosition("v2v_source")
                    src_speed = traci.vehicle.getSpeed("v2v_source")
                    
                    # Track progress
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
                        self.log_message(f"⚠️ Step {step}: Source vehicle completed route")
                        source_active = False
                
                if "v2v_dest" in vehicles:
                    if not dest_active:
                        self.log_message(f"✅ Step {step}: Destination vehicle active")
                        dest_active = True
                    
                    dst_pos = traci.vehicle.getPosition("v2v_dest")
                    dst_speed = traci.vehicle.getSpeed("v2v_dest")
                    
                    # Track progress
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
                        self.log_message(f"⚠️ Step {step}: Destination vehicle completed route")
                        dest_active = False
                
                # Calculate distances WITH CALIBRATION
                if source_active and dest_active:
                    raw_distance = calculate_distance(src_pos, dst_pos)
                    distances_raw.append(raw_distance)
                    
                    # Apply calibration if enabled
                    if self.calibration_enabled.get():
                        calibrated_distance = apply_calibration(raw_distance)
                        distances_calibrated.append(calibrated_distance)
                    else:
                        distances_calibrated.append(raw_distance)
                    
                    # Log every 200 steps
                    if step - last_log_step >= 200:
                        avg_raw = sum(distances_raw[-200:]) / len(distances_raw[-200:])
                        avg_calib = sum(distances_calibrated[-200:]) / len(distances_calibrated[-200:])
                        
                        self.log_message(f"📊 Step {step}: Raw={raw_distance:.2f}m, "
                                        f"Calibrated={calibrated_distance if self.calibration_enabled.get() else raw_distance:.2f}m "
                                        f"(avg={avg_calib:.2f}m), "
                                        f"Speed: src={src_speed:.1f}m/s, dst={dst_speed:.1f}m/s, "
                                        f"WP: src={source_progress[-1] if source_progress else 0}, "
                                        f"dst={dest_progress[-1] if dest_progress else 0}")
                        last_log_step = step
                
                # Stop if both completed
                if not source_active and not dest_active and step > 100:
                    self.log_message(f"\n✅ Both vehicles completed routes at step {step}")
                    break
                
                time.sleep(0.01)
            
            # Final statistics WITH CALIBRATION COMPARISON
            self.log_message("\n" + "="*70)
            self.log_message("SIMULATION COMPLETE - STATISTICS")
            self.log_message("="*70)
            
            if distances_raw:
                self.log_message(f"📊 Raw Distance Statistics:")
                self.log_message(f"   Average: {sum(distances_raw)/len(distances_raw):.2f} m")
                self.log_message(f"   Min: {min(distances_raw):.2f} m")
                self.log_message(f"   Max: {max(distances_raw):.2f} m")
                
                if self.calibration_enabled.get():
                    self.log_message(f"\n📊 Calibrated Distance Statistics:")
                    self.log_message(f"   Average: {sum(distances_calibrated)/len(distances_calibrated):.2f} m")
                    self.log_message(f"   Min: {min(distances_calibrated):.2f} m")
                    self.log_message(f"   Max: {max(distances_calibrated):.2f} m")
                    self.log_message(f"   Calibration reduction: {((sum(distances_raw)-sum(distances_calibrated))/sum(distances_raw)*100):.1f}%")
            
            if source_progress:
                self.log_message(f"\n📊 Source vehicle reached waypoint: {max(source_progress)}/{NUM_WAYPOINTS}")
            
            if dest_progress:
                self.log_message(f"📊 Dest vehicle reached waypoint: {max(dest_progress)}/{NUM_WAYPOINTS}")
            
            self.log_message(f"📊 Total simulation steps: {step}")
            
            # DISTANCE ACCURACY ANALYSIS WITH CALIBRATION
            self.log_message("\n" + "="*70)
            self.log_message("DISTANCE ACCURACY ANALYSIS")
            self.log_message("="*70)
            
            distance_analysis = []
            
            for i, wp in enumerate(waypoint_coords):
                actual_distance = wp['actual_distance']
                
                closest_simulated_distance = None
                min_distance_to_waypoint = float('inf')
                
                for sim_step in range(len(distances_calibrated)):
                    if sim_step < len(source_progress) and sim_step < len(dest_progress):
                        src_wp_idx = source_progress[sim_step]
                        dest_wp_idx = dest_progress[sim_step]
                        distance_to_waypoint = abs(src_wp_idx - i) + abs(dest_wp_idx - i)
                        
                        if distance_to_waypoint < min_distance_to_waypoint:
                            min_distance_to_waypoint = distance_to_waypoint
                            closest_simulated_distance = distances_calibrated[sim_step]
                
                if closest_simulated_distance is not None:
                    error = closest_simulated_distance - actual_distance
                    error_percentage = (error / actual_distance) * 100 if actual_distance > 0 else 0
                    
                    distance_analysis.append({
                        'waypoint': i,
                        'actual_distance': actual_distance,
                        'simulated_distance': closest_simulated_distance,
                        'error': error,
                        'error_percentage': error_percentage,
                        'accuracy': 100 - abs(error_percentage)
                    })
            
            # Calculate accuracy metrics
            if distance_analysis:
                errors = [da['error'] for da in distance_analysis]
                error_percentages = [da['error_percentage'] for da in distance_analysis]
                accuracies = [da['accuracy'] for da in distance_analysis]
                
                self.log_message(f"📊 {'Calibrated' if self.calibration_enabled.get() else 'Raw'} Distance Analysis Results:")
                self.log_message(f"   Total waypoints analyzed: {len(distance_analysis)}")
                self.log_message(f"   Mean Error: {sum(errors)/len(errors):.2f} m")
                self.log_message(f"   Mean Absolute Error: {sum(abs(e) for e in errors)/len(errors):.2f} m")
                self.log_message(f"   Root Mean Square Error: {(sum(e**2 for e in errors)/len(errors))**0.5:.2f} m")
                self.log_message(f"   Mean Error Percentage: {sum(error_percentages)/len(error_percentages):.2f}%")
                self.log_message(f"   Mean Absolute Error Percentage: {sum(abs(ep) for ep in error_percentages)/len(error_percentages):.2f}%")
                self.log_message(f"   Mean Accuracy: {sum(accuracies)/len(accuracies):.2f}%")
                
                # Find best/worst
                best_wp = min(distance_analysis, key=lambda x: abs(x['error_percentage']))
                worst_wp = max(distance_analysis, key=lambda x: abs(x['error_percentage']))
                
                self.log_message(f"\n📊 Best Waypoint: #{best_wp['waypoint']} - "
                                f"Actual={best_wp['actual_distance']:.2f}m, "
                                f"Sim={best_wp['simulated_distance']:.2f}m, "
                                f"Error={best_wp['error']:.2f}m ({best_wp['error_percentage']:.2f}%)")
                
                self.log_message(f"📊 Worst Waypoint: #{worst_wp['waypoint']} - "
                                f"Actual={worst_wp['actual_distance']:.2f}m, "
                                f"Sim={worst_wp['simulated_distance']:.2f}m, "
                                f"Error={worst_wp['error']:.2f}m ({worst_wp['error_percentage']:.2f}%)")
                
                # Accuracy distribution
                high_acc = sum(1 for a in accuracies if a >= 90)
                medium_acc = sum(1 for a in accuracies if 70 <= a < 90)
                low_acc = sum(1 for a in accuracies if a < 70)
                
                self.log_message(f"\n📊 Accuracy Distribution:")
                self.log_message(f"   High (≥90%): {high_acc} waypoints ({high_acc/len(accuracies)*100:.1f}%)")
                self.log_message(f"   Medium (70-89%): {medium_acc} waypoints ({medium_acc/len(accuracies)*100:.1f}%)")
                self.log_message(f"   Low (<70%): {low_acc} waypoints ({low_acc/len(accuracies)*100:.1f}%)")
                
                # Save results - Ensure we save to MAIN project directory (not SUMO subfolder)
                analysis_df = pd.DataFrame(distance_analysis)
                
                # Build absolute path to main project directory
                analysis_file = os.path.join(original_dir, 'calibrated_distance_accuracy_analysis.csv')
                
                # Create directory if needed and save
                try:
                    os.makedirs(os.path.dirname(analysis_file), exist_ok=True)
                    analysis_df.to_csv(analysis_file, index=False)
                    self.log_message(f"\n💾 Detailed analysis saved to: {analysis_file}")
                    self.log_message(f"   📂 File location: {os.path.abspath(analysis_file)}")
                except Exception as e:
                    self.log_message(f"\n❌ Error saving CSV: {e}")
                    self.log_message(f"   Current directory: {os.getcwd()}")
                    self.log_message(f"   Attempted path: {analysis_file}")
                
                summary_stats = {
                    'calibration_enabled': self.calibration_enabled.get(),
                    'calibration_factor': CALIBRATION_FACTOR if self.calibration_enabled.get() else 1.0,
                    'num_waypoints': NUM_WAYPOINTS,
                    'total_waypoints_analyzed': len(distance_analysis),
                    'mean_error_m': sum(errors)/len(errors),
                    'mean_absolute_error_m': sum(abs(e) for e in errors)/len(errors),
                    'rmse_m': (sum(e**2 for e in errors)/len(errors))**0.5,
                    'mean_accuracy_percentage': sum(accuracies)/len(accuracies),
                    'high_accuracy_count': high_acc,
                    'medium_accuracy_count': medium_acc,
                    'low_accuracy_count': low_acc,
                    'best_waypoint': best_wp['waypoint'],
                    'worst_waypoint': worst_wp['waypoint']
                }
                
                # Save JSON summary to main project directory
                summary_file = os.path.join(original_dir, 'calibrated_simulation_summary.json')
                
                try:
                    with open(summary_file, 'w') as f:
                        json.dump(summary_stats, f, indent=2)
                    self.log_message(f"💾 Summary saved to: {summary_file}")
                    self.log_message(f"   📂 File location: {os.path.abspath(summary_file)}")
                except Exception as e:
                    self.log_message(f"❌ Error saving JSON: {e}")
                
                # Print first 10 waypoints
                self.log_message(f"\n📊 Detailed Analysis (First 10 Waypoints):")
                self.log_message("-" * 80)
                self.log_message(f"{'WP':<3} {'Actual':<8} {'Simulated':<10} {'Error':<8} {'Error%':<8} {'Accuracy':<8}")
                self.log_message("-" * 80)
                
                for da in distance_analysis[:10]:
                    self.log_message(f"{da['waypoint']:<3} {da['actual_distance']:<8.2f} "
                                    f"{da['simulated_distance']:<10.2f} "
                                    f"{da['error']:<8.2f} {da['error_percentage']:<8.2f} "
                                    f"{da['accuracy']:<8.2f}")
                
                if len(distance_analysis) > 10:
                    self.log_message(f"... and {len(distance_analysis) - 10} more waypoints (see CSV)")
            
            self.log_message("\n✅ Calibrated simulation complete!")
            self.log_message("💡 Vehicles are visible as 3D cars (blue/red)")
            self.log_message("💡 Waypoints shown as semi-transparent POIs")
            self.log_message(f"💡 Calibration: {'APPLIED' if self.calibration_enabled.get() else 'NOT APPLIED'}")
            
            # Keep SUMO running
            self.log_message("\n⏸ Keeping SUMO-GUI open for inspection...")
            self.log_message("Close SUMO-GUI window or click Stop to end")
            
            while self.simulation_running and traci.simulation.getMinExpectedNumber() > 0:
                try:
                    traci.simulationStep()
                    time.sleep(0.1)
                except:
                    break
            
        except Exception as e:
            self.log_message(f"\n❌ ERROR: {str(e)}")
            import traceback
            self.log_message(traceback.format_exc())
        
        finally:
            try:
                traci.close()
            except:
                pass
            os.chdir(original_dir)
            self.log_message("\n✅ Cleanup complete")
            
            self.simulation_running = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.progress_var.set(0)
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    app = CalibratedV2VSimulationGUI()
    app.run()

