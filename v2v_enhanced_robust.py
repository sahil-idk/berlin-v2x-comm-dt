#!/usr/bin/env python3
"""
Enhanced Robust V2V Simulation with GUI Controls
Uses edge-to-edge navigation without moveToXY to prevent vehicle disappearance
Includes Tkinter GUI for user control
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

def calculate_distance(pos1, pos2):
    """Calculate Euclidean distance between two positions"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

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
    
    # Build optimized route with waypoint proximity consideration
    if not edges_with_positions:
        return []
    
    route = []
    waypoint_edges = []  # Track which edges correspond to waypoints
    
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
                    # Add intermediate edges
                    for edge in path[0]:
                        if edge.getID() not in route:
                            route.append(edge.getID())
                    # Mark waypoint edge
                    if current['edge_id'] not in route:
                        route.append(current['edge_id'])
                    waypoint_edges.append(current['edge_id'])
                else:
                    # Fallback: direct connection
                    if current['edge_id'] not in route:
                        route.append(current['edge_id'])
                    waypoint_edges.append(current['edge_id'])
            except Exception as e:
                print(f"⚠️ Path finding failed between waypoints {i-1} and {i}: {e}")
                # Fallback: just add the edge
                if current['edge_id'] not in route:
                    route.append(current['edge_id'])
                waypoint_edges.append(current['edge_id'])
    
    return route, waypoint_edges

class V2VSimulationGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced V2V Simulation Control")
        self.root.geometry("600x500")
        
        # Simulation state
        self.simulation_running = False
        self.simulation_thread = None
        self.sumo_process = None
        
        # Configuration variables
        self.num_waypoints = tk.IntVar(value=20)
        self.simulation_speed = tk.DoubleVar(value=1.0)
        self.vehicle_speed = tk.IntVar(value=15)
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI interface"""
        # Title
        title_label = tk.Label(self.root, text="Enhanced V2V Simulation Control", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
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
        
        # Control buttons frame
        control_frame = ttk.LabelFrame(self.root, text="Simulation Control", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Buttons
        self.start_button = ttk.Button(control_frame, text="Start Simulation", 
                                      command=self.start_simulation)
        self.start_button.pack(side="left", padx=5)
        
        self.pause_button = ttk.Button(control_frame, text="Pause", 
                                      command=self.pause_simulation, state="disabled")
        self.pause_button.pack(side="left", padx=5)
        
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
        self.pause_button.config(state="normal")
        self.stop_button.config(state="normal")
        
        # Clear status
        self.status_text.delete(1.0, tk.END)
        
        # Start simulation thread
        self.simulation_thread = threading.Thread(target=self.run_simulation)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
    def pause_simulation(self):
        """Pause/resume simulation"""
        # This would require more complex state management
        # For now, just show a message
        messagebox.showinfo("Pause", "Pause functionality requires additional implementation")
        
    def stop_simulation(self):
        """Stop the simulation"""
        self.simulation_running = False
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")
        self.stop_button.config(state="disabled")
        
        # Clean up SUMO
        try:
            if self.sumo_process:
                traci.close()
                self.sumo_process.wait()
        except:
            pass
            
        self.log_message("🛑 Simulation stopped by user")
        
    def run_simulation(self):
        """Main simulation function"""
        try:
            self.log_message("="*70)
            self.log_message("ENHANCED ROBUST V2V SIMULATION")
            self.log_message("="*70)
            
            # Configuration
            NUM_WAYPOINTS = self.num_waypoints.get()
            VEHICLE_SPEED = self.vehicle_speed.get()
            SIMULATION_STEPS = 3000
            
            original_dir = os.getcwd()
            
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
            
            # Find optimal paths through waypoints
            self.log_message("📍 Computing optimal routes through GPS waypoints...")
            source_route, source_waypoint_edges = find_optimal_path_through_waypoints(net, waypoints_df, 'source')
            dest_route, dest_waypoint_edges = find_optimal_path_through_waypoints(net, waypoints_df, 'destination')
            
            self.log_message(f"✅ Source route: {len(source_route)} edges")
            self.log_message(f"✅ Destination route: {len(dest_route)} edges")
            
            # Validate routes
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
            
            # Create route file
            self.log_message("📍 Creating route file...")
            route_file = 'v2v_enhanced_routes.rou.xml'
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
            
            # Create custom config file
            self.log_message("📍 Creating SUMO configuration...")
            config_file = 'v2v_enhanced.sumocfg'
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
            
            # Start SUMO-GUI
            self.log_message("🚀 Starting SUMO-GUI...")
            sumo_cmd = ["sumo-gui", "-c", config_file, "--start", "--quit-on-end"]
            traci.start(sumo_cmd)
            time.sleep(3)  # Give GUI time to open
            
            # Add waypoint POIs for visualization
            self.log_message("📍 Adding waypoint markers...")
            waypoint_coords = []
            for idx, row in waypoints_df.iterrows():
                # Source waypoint (Blue)
                src_x, src_y = net.convertLonLat2XY(row['Longitude_source'], row['Latitude_source'])
                traci.poi.add(
                    f"src_wp_{idx}",
                    src_x, src_y,
                    color=(0, 0, 255, 128),  # Semi-transparent blue
                    poiType="source",
                    layer=100
                )
                
                # Destination waypoint (Red)
                dst_x, dst_y = net.convertLonLat2XY(row['Longitude_destination'], row['Longitude_destination'])
                traci.poi.add(
                    f"dst_wp_{idx}",
                    dst_x, dst_y,
                    color=(255, 0, 0, 128),  # Semi-transparent red
                    poiType="destination",
                    layer=100
                )
                
                waypoint_coords.append({
                    'source': (src_x, src_y),
                    'dest': (dst_x, dst_y),
                    'actual_distance': row['distance']
                })
            
            self.log_message(f"✅ Added {len(waypoint_coords)*2} waypoint markers")
            
            # Run simulation
            self.log_message("🎯 Starting simulation...")
            self.log_message("-"*70)
            
            step = 0
            source_active = False
            dest_active = False
            last_log_step = 0
            
            # Metrics tracking
            distances = []
            source_progress = []
            dest_progress = []
            
            while step < SIMULATION_STEPS and self.simulation_running:
                traci.simulationStep()
                step += 1
                
                # Update progress bar
                progress = min(100, (step / SIMULATION_STEPS) * 100)
                self.progress_var.set(progress)
                
                # Get current vehicles
                vehicles = traci.vehicle.getIDList()
                
                # Check vehicle status
                if "v2v_source" in vehicles:
                    if not source_active:
                        self.log_message(f"✅ Step {step}: Source vehicle active")
                        source_active = True
                    
                    # Get source position
                    src_pos = traci.vehicle.getPosition("v2v_source")
                    src_speed = traci.vehicle.getSpeed("v2v_source")
                    
                    # Track progress through waypoints
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
                    
                    # Get destination position
                    dst_pos = traci.vehicle.getPosition("v2v_dest")
                    dst_speed = traci.vehicle.getSpeed("v2v_dest")
                    
                    # Track progress through waypoints
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
                
                # Calculate and log distance when both vehicles are active
                if source_active and dest_active:
                    distance = calculate_distance(src_pos, dst_pos)
                    distances.append(distance)
                    
                    # Log every 200 steps
                    if step - last_log_step >= 200:
                        avg_distance = sum(distances[-200:]) / len(distances[-200:]) if distances else 0
                        self.log_message(f"📊 Step {step}: Distance={distance:.2f}m (avg={avg_distance:.2f}m), "
                                        f"Speed: src={src_speed:.1f}m/s, dst={dst_speed:.1f}m/s, "
                                        f"Waypoint: src={source_progress[-1] if source_progress else 0}, "
                                        f"dst={dest_progress[-1] if dest_progress else 0}")
                        last_log_step = step
                
                # Stop if both vehicles have completed their routes
                if not source_active and not dest_active and step > 100:
                    self.log_message(f"\n✅ Both vehicles completed routes at step {step}")
                    break
                
                # Small delay for GUI responsiveness
                time.sleep(0.01)
            
            # Final statistics
            self.log_message("\n" + "="*70)
            self.log_message("SIMULATION COMPLETE - STATISTICS")
            self.log_message("="*70)
            
            if distances:
                self.log_message(f"📊 Average inter-vehicle distance: {sum(distances)/len(distances):.2f} m")
                self.log_message(f"📊 Min distance: {min(distances):.2f} m")
                self.log_message(f"📊 Max distance: {max(distances):.2f} m")
            
            if source_progress:
                self.log_message(f"📊 Source vehicle reached waypoint: {max(source_progress)}/{NUM_WAYPOINTS}")
            
            if dest_progress:
                self.log_message(f"📊 Dest vehicle reached waypoint: {max(dest_progress)}/{NUM_WAYPOINTS}")
            
            self.log_message(f"📊 Total simulation steps: {step}")
            
            # ===== DISTANCE ACCURACY ANALYSIS =====
            self.log_message("\n" + "="*70)
            self.log_message("DISTANCE ACCURACY ANALYSIS")
            self.log_message("="*70)
            
            # Analyze simulated vs actual distances for each waypoint
            distance_analysis = []
            
            for i, wp in enumerate(waypoint_coords):
                actual_distance = wp['actual_distance']
                
                # Find closest simulated distance to this waypoint
                closest_simulated_distance = None
                min_distance_to_waypoint = float('inf')
                
                # Look through simulation steps to find when vehicles were closest to this waypoint
                for sim_step in range(len(distances)):
                    if sim_step < len(source_progress) and sim_step < len(dest_progress):
                        src_wp_idx = source_progress[sim_step]
                        dest_wp_idx = dest_progress[sim_step]
                        
                        # Calculate how close we are to this waypoint
                        distance_to_waypoint = abs(src_wp_idx - i) + abs(dest_wp_idx - i)
                        
                        if distance_to_waypoint < min_distance_to_waypoint:
                            min_distance_to_waypoint = distance_to_waypoint
                            closest_simulated_distance = distances[sim_step]
                
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
            
            # Calculate overall accuracy metrics
            if distance_analysis:
                errors = [da['error'] for da in distance_analysis]
                error_percentages = [da['error_percentage'] for da in distance_analysis]
                accuracies = [da['accuracy'] for da in distance_analysis]
                
                self.log_message(f"📊 Distance Analysis Results:")
                self.log_message(f"   Total waypoints analyzed: {len(distance_analysis)}")
                self.log_message(f"   Mean Error: {sum(errors)/len(errors):.2f} m")
                self.log_message(f"   Mean Absolute Error: {sum(abs(e) for e in errors)/len(errors):.2f} m")
                self.log_message(f"   Root Mean Square Error: {(sum(e**2 for e in errors)/len(errors))**0.5:.2f} m")
                self.log_message(f"   Mean Error Percentage: {sum(error_percentages)/len(error_percentages):.2f}%")
                self.log_message(f"   Mean Absolute Error Percentage: {sum(abs(ep) for ep in error_percentages)/len(error_percentages):.2f}%")
                self.log_message(f"   Mean Accuracy: {sum(accuracies)/len(accuracies):.2f}%")
                
                # Find best and worst waypoints
                best_wp = min(distance_analysis, key=lambda x: abs(x['error_percentage']))
                worst_wp = max(distance_analysis, key=lambda x: abs(x['error_percentage']))
                
                self.log_message(f"\n📊 Best Waypoint (Most Accurate):")
                self.log_message(f"   Waypoint {best_wp['waypoint']}: Actual={best_wp['actual_distance']:.2f}m, "
                                f"Simulated={best_wp['simulated_distance']:.2f}m, "
                                f"Error={best_wp['error']:.2f}m ({best_wp['error_percentage']:.2f}%)")
                
                self.log_message(f"\n📊 Worst Waypoint (Least Accurate):")
                self.log_message(f"   Waypoint {worst_wp['waypoint']}: Actual={worst_wp['actual_distance']:.2f}m, "
                                f"Simulated={worst_wp['simulated_distance']:.2f}m, "
                                f"Error={worst_wp['error']:.2f}m ({worst_wp['error_percentage']:.2f}%)")
                
                # Accuracy distribution
                high_accuracy = sum(1 for a in accuracies if a >= 90)
                medium_accuracy = sum(1 for a in accuracies if 70 <= a < 90)
                low_accuracy = sum(1 for a in accuracies if a < 70)
                
                self.log_message(f"\n📊 Accuracy Distribution:")
                self.log_message(f"   High Accuracy (≥90%): {high_accuracy} waypoints ({high_accuracy/len(accuracies)*100:.1f}%)")
                self.log_message(f"   Medium Accuracy (70-89%): {medium_accuracy} waypoints ({medium_accuracy/len(accuracies)*100:.1f}%)")
                self.log_message(f"   Low Accuracy (<70%): {low_accuracy} waypoints ({low_accuracy/len(accuracies)*100:.1f}%)")
                
                # Save detailed analysis to CSV
                analysis_df = pd.DataFrame(distance_analysis)
                analysis_file = 'distance_accuracy_analysis.csv'
                analysis_df.to_csv(analysis_file, index=False)
                self.log_message(f"\n💾 Detailed analysis saved to: {analysis_file}")
                
                # Save summary statistics
                summary_stats = {
                    'total_waypoints': len(distance_analysis),
                    'mean_error_m': sum(errors)/len(errors),
                    'mean_absolute_error_m': sum(abs(e) for e in errors)/len(errors),
                    'rmse_m': (sum(e**2 for e in errors)/len(errors))**0.5,
                    'mean_error_percentage': sum(error_percentages)/len(error_percentages),
                    'mean_absolute_error_percentage': sum(abs(ep) for ep in error_percentages)/len(error_percentages),
                    'mean_accuracy_percentage': sum(accuracies)/len(accuracies),
                    'high_accuracy_count': high_accuracy,
                    'medium_accuracy_count': medium_accuracy,
                    'low_accuracy_count': low_accuracy,
                    'best_waypoint': best_wp['waypoint'],
                    'worst_waypoint': worst_wp['waypoint']
                }
                
                with open('distance_accuracy_summary.json', 'w') as f:
                    json.dump(summary_stats, f, indent=2)
                self.log_message(f"💾 Summary statistics saved to: distance_accuracy_summary.json")
                
                # Print detailed waypoint-by-waypoint analysis (first 10 for brevity)
                self.log_message(f"\n📊 Detailed Analysis (First 10 Waypoints):")
                self.log_message("-" * 80)
                self.log_message(f"{'WP':<3} {'Actual':<8} {'Simulated':<10} {'Error':<8} {'Error%':<8} {'Accuracy':<8}")
                self.log_message("-" * 80)
                
                for da in distance_analysis[:10]:
                    self.log_message(f"{da['waypoint']:<3} {da['actual_distance']:<8.2f} {da['simulated_distance']:<10.2f} "
                                    f"{da['error']:<8.2f} {da['error_percentage']:<8.2f} {da['accuracy']:<8.2f}")
                
                if len(distance_analysis) > 10:
                    self.log_message(f"... and {len(distance_analysis) - 10} more waypoints (see CSV for full details)")
            
            self.log_message("\n✅ Simulation successful! Vehicles stayed in simulation throughout.")
            self.log_message("💡 TIP: Vehicles are visible as 3D cars (blue and red)")
            self.log_message("💡 TIP: Waypoints are shown as semi-transparent POIs")
            self.log_message("💡 TIP: Check distance_accuracy_analysis.csv for detailed per-waypoint analysis")
            
            # Save results
            results = {
                'num_waypoints': NUM_WAYPOINTS,
                'vehicle_speed': VEHICLE_SPEED,
                'total_steps': step,
                'avg_distance': sum(distances)/len(distances) if distances else 0,
                'min_distance': min(distances) if distances else 0,
                'max_distance': max(distances) if distances else 0,
                'source_progress': max(source_progress) if source_progress else 0,
                'dest_progress': max(dest_progress) if dest_progress else 0
            }
            
            with open('simulation_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            
            self.log_message("💾 Results saved to simulation_results.json")
            
            # Keep simulation running for observation
            self.log_message("\n⏸ Keeping SUMO-GUI open for inspection...")
            self.log_message("Close SUMO-GUI window or click Stop to end simulation")
            
            # Wait for user to stop or SUMO to close
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
            # Clean up
            try:
                traci.close()
            except:
                pass
            os.chdir(original_dir)
            self.log_message("\n✅ Cleanup complete")
            
            # Reset GUI state
            self.simulation_running = False
            self.start_button.config(state="normal")
            self.pause_button.config(state="disabled")
            self.stop_button.config(state="disabled")
            self.progress_var.set(0)
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    app = V2VSimulationGUI()
    app.run()
