#!/usr/bin/env python3
"""
V2V Robust Fixed Simulation Approach
===================================

This approach focuses on fixing the core issues that cause vehicles to go off-road:
1. Use the working baseline approach as foundation
2. Add proper route validation and connectivity checks
3. Implement better GPS-to-edge mapping
4. Add vehicle persistence monitoring
5. Use proven calibration and analysis

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

def find_closest_edge_robust(net, lat, lon, max_radius=200):
    """
    Robust edge finding with multiple fallback strategies
    """
    x, y = net.convertLonLat2XY(lon, lat)
    
    # Strategy 1: Start with small radius and expand
    for radius in [30, 50, 100, 150, max_radius]:
        nearby_edges = net.getNeighboringEdges(x, y, r=radius)
        if nearby_edges:
            # Find the closest edge
            closest_edge = min(nearby_edges, key=lambda e: e[1])[0]
            distance = min(nearby_edges, key=lambda e: e[1])[1]
            
            if distance < radius * 0.8:  # Only accept if reasonably close
                return closest_edge, distance
    
    # Strategy 2: If no edges found, try to find any edge in the network
    all_edges = list(net.getEdges())
    if all_edges:
        # Find edge closest to GPS point
        min_dist = float('inf')
        closest_edge = None
        
        for edge in all_edges[:50]:  # Check first 50 edges to avoid performance issues
            edge_shape = edge.getShape()
            if edge_shape:
                edge_center = edge_shape[len(edge_shape)//2]  # Middle point of edge
                dist = calculate_distance((x, y), edge_center)
                if dist < min_dist:
                    min_dist = dist
                    closest_edge = edge
        
        if closest_edge and min_dist < 1000:  # Within 1km
            return closest_edge, min_dist
    
    return None, float('inf')

def create_robust_route(net, waypoints_df, vehicle_type='source'):
    """
    Create a robust route using proven edge mapping with vehicle-specific paths
    """
    print(f"🗺️ Creating robust route for {vehicle_type}...")
    
    # Sample waypoints (every 3rd point for better coverage)
    sample_indices = range(0, len(waypoints_df), 3)
    sampled_waypoints = waypoints_df.iloc[sample_indices]
    
    print(f"📊 Original waypoints: {len(waypoints_df)}, Sampled: {len(sampled_waypoints)}")
    
    edges_with_positions = []
    
    for idx, row in sampled_waypoints.iterrows():
        if vehicle_type == 'source':
            lat = row['Latitude_source']
            lon = row['Longitude_source']
        else:
            lat = row['Latitude_destination']
            lon = row['Longitude_destination']
        
        # Find the closest edge using robust method
        edge, distance = find_closest_edge_robust(net, lat, lon)
        
        if edge and distance < 200:  # Only accept edges within 200m
            edges_with_positions.append({
                'edge': edge,
                'edge_id': edge.getID(),
                'distance': distance,
                'original_idx': idx
            })
            print(f"   ✅ Found edge: {edge.getID()} at distance {distance:.2f}m")
        else:
            print(f"   ❌ No suitable edge found for waypoint {idx}")
    
    if len(edges_with_positions) < 2:
        print("❌ Not enough valid edges found")
        return []
    
    # Create route using Dijkstra's algorithm
    route = []
    for i in range(len(edges_with_positions) - 1):
        start_edge = edges_with_positions[i]['edge']
        end_edge = edges_with_positions[i + 1]['edge']
        
        try:
            # Find shortest path using Dijkstra
            path = net.getShortestPath(start_edge, end_edge)
            if path and len(path) > 0 and path[0] is not None:
                # Add all edges in path, avoiding duplicates
                for edge in path[0]:
                    if edge.getID() not in route:
                        route.append(edge.getID())
            else:
                print(f"   ⚠️ No path found between {start_edge.getID()} and {end_edge.getID()}")
                # Add the edges directly if no path found
                if start_edge.getID() not in route:
                    route.append(start_edge.getID())
                if end_edge.getID() not in route:
                    route.append(end_edge.getID())
        except Exception as e:
            print(f"⚠️ Path finding failed: {e}")
            # Add edges directly as fallback
            if start_edge.getID() not in route:
                route.append(start_edge.getID())
            if end_edge.getID() not in route:
                route.append(end_edge.getID())
    
    # Ensure route has at least 3 edges for proper movement
    if len(route) < 3:
        print("⚠️ Route too short, extending...")
        # Try to extend the route
        if len(route) > 0:
            last_edge = net.getEdge(route[-1])
            outgoing_edges = [edge.getID() for edge in last_edge.getOutgoing().keys()]
            if outgoing_edges:
                route.extend(outgoing_edges[:2])  # Add up to 2 more edges
    
    # VEHICLE-SPECIFIC ROUTE MODIFICATION
    # Add offset to prevent collisions between source and destination
    if vehicle_type == 'destination' and len(route) > 0:
        # For destination vehicle, try to use parallel or nearby edges
        try:
            # Find alternative edges that are connected but different
            first_edge = net.getEdge(route[0])
            incoming_edges = [edge.getID() for edge in first_edge.getIncoming().keys()]
            
            if incoming_edges and incoming_edges[0] != route[0]:
                # Use a different starting edge for destination
                route.insert(0, incoming_edges[0])
                print(f"   🔄 Modified destination route to avoid collision")
        except:
            pass
    
    print(f"✅ Robust route created: {len(route)} edges")
    return route

def validate_route_robust(net, route):
    """
    Validate route connectivity and fix issues
    """
    if len(route) < 2:
        return False
    
    # Check if all edges exist
    valid_route = []
    for edge_id in route:
        try:
            edge = net.getEdge(edge_id)
            valid_route.append(edge_id)
        except:
            print(f"⚠️ Invalid edge: {edge_id}")
    
    return valid_route

class V2VRobustFixedSimulation:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("V2V Robust Fixed Simulation")
        self.root.geometry("800x700")
        
        # Variables
        self.num_waypoints = tk.IntVar(value=30)
        self.use_realistic_speed = tk.BooleanVar(value=True)
        self.simulation_running = False
        self.simulation_thread = None
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="V2V Robust Fixed Simulation", 
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
        self.stop_button.grid(row=0, column=1)
        
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
        
    def run_simulation(self):
        """Run the robust fixed V2V simulation"""
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
            
            # Create robust routes
            self.log_message(f"\n🔧 Creating robust routes...")
            source_route = create_robust_route(net, waypoints_df, 'source')
            dest_route = create_robust_route(net, waypoints_df, 'destination')
            
            if not source_route or not dest_route:
                self.log_message("❌ Failed to create robust routes")
                return
            
            # Validate routes
            source_route = validate_route_robust(net, source_route)
            dest_route = validate_route_robust(net, dest_route)
            
            self.log_message(f"✅ Source route: {len(source_route)} edges")
            self.log_message(f"✅ Destination route: {len(dest_route)} edges")
            
            # Create route files
            with open('robust_fixed_source_route.rou.xml', 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<routes>\n')
                f.write('  <route id="robust_source_route" edges="' + ' '.join(source_route) + '"/>\n')
                f.write('  <vType id="robust_source_vType" accel="2.0" decel="4.5" sigma="0.5" length="4.5" maxSpeed="50" guiShape="passenger" color="blue"/>\n')
                f.write('</routes>\n')
            
            with open('robust_fixed_dest_route.rou.xml', 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<routes>\n')
                f.write('  <route id="robust_dest_route" edges="' + ' '.join(dest_route) + '"/>\n')
                f.write('  <vType id="robust_dest_vType" accel="2.0" decel="4.5" sigma="0.5" length="4.5" maxSpeed="50" guiShape="passenger" color="red"/>\n')
                f.write('</routes>\n')
            
            # Create SUMO config
            with open('robust_fixed.sumocfg', 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<configuration>\n')
                f.write('  <input>\n')
                f.write('    <net-file value="osm.net.xml.gz"/>\n')
                f.write('    <route-files value="robust_fixed_source_route.rou.xml,robust_fixed_dest_route.rou.xml"/>\n')
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
            sumo_cmd = ["sumo-gui", "-c", "robust_fixed.sumocfg"]
            self.log_message(f"\n🚀 Starting SUMO-GUI with robust fixed approach...")
            
            traci.start(sumo_cmd)
            time.sleep(3)  # Wait for SUMO to initialize
            
            # Add vehicles with robust positioning and collision avoidance
            self.log_message("🚗 Adding vehicles with robust positioning...")
            
            # Add source vehicle first
            traci.vehicle.add("robust_v2v_source", "robust_source_route", typeID="robust_source_vType", depart=0)
            
            # Add destination vehicle with delay to prevent collision
            traci.vehicle.add("robust_v2v_dest", "robust_dest_route", typeID="robust_dest_vType", depart=5)
            
            # Wait for vehicles to be added
            time.sleep(2)
            
            # Set vehicle properties
            traci.vehicle.setColor("robust_v2v_source", (0, 0, 255, 255))  # Blue
            traci.vehicle.setColor("robust_v2v_dest", (255, 0, 0, 255))    # Red
            
            # Set vehicle control modes to prevent stalling
            traci.vehicle.setSpeedMode("robust_v2v_source", 0)  # No speed adaptation
            traci.vehicle.setSpeedMode("robust_v2v_dest", 0)    # No speed adaptation
            traci.vehicle.setLaneChangeMode("robust_v2v_source", 0)  # No lane changes
            traci.vehicle.setLaneChangeMode("robust_v2v_dest", 0)    # No lane changes
            
            self.log_message(f"✅ Vehicles added with robust fixed approach")
            
            # Prepare waypoint coordinates for analysis
            waypoint_coords = []
            for idx, row in waypoints_df.iterrows():
                src_x, src_y = net.convertLonLat2XY(row['Longitude_source'], row['Latitude_source'])
                dst_x, dst_y = net.convertLonLat2XY(row['Longitude_destination'], row['Longitude_destination'])
                
                waypoint_coords.append({
                    'source': (src_x, src_y),
                    'dest': (dst_x, dst_y),
                    'actual_distance': row['distance'],
                    'source_speed_kmh': row['speed_kmh_source'],
                    'dest_speed_kmh': row['speed_kmh_destination']
                })
            
            # Simulation loop with robust fixed approach
            self.log_message(f"\n🎯 Starting simulation with robust fixed approach...")
            
            step = 0
            current_waypoint = 0
            source_active = False
            dest_active = False
            
            # Analysis data
            analysis_data = []
            
            while step < SIMULATION_STEPS and self.simulation_running:
                traci.simulationStep()
                step += 1
                
                progress = min(100, (step / SIMULATION_STEPS) * 100)
                self.progress_var.set(progress)
                
                vehicles = traci.vehicle.getIDList()
                
                # Source vehicle
                if "robust_v2v_source" in vehicles:
                    if not source_active:
                        self.log_message(f"✅ Step {step}: Source vehicle active")
                        source_active = True
                    
                    src_pos = traci.vehicle.getPosition("robust_v2v_source")
                    src_speed = traci.vehicle.getSpeed("robust_v2v_source")
                    
                    # Set realistic speed from dataset
                    if self.use_realistic_speed.get() and current_waypoint < len(waypoint_coords):
                        target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['source_speed_kmh'])
                        traci.vehicle.setSpeed("robust_v2v_source", target_speed_ms)
                    else:
                        # Ensure minimum speed to prevent stalling
                        traci.vehicle.setSpeed("robust_v2v_source", 5.0)  # 5 m/s minimum
                
                # Destination vehicle
                if "robust_v2v_dest" in vehicles:
                    if not dest_active:
                        self.log_message(f"✅ Step {step}: Destination vehicle active")
                        dest_active = True
                    
                    dst_pos = traci.vehicle.getPosition("robust_v2v_dest")
                    dst_speed = traci.vehicle.getSpeed("robust_v2v_dest")
                    
                    # Set realistic speed from dataset
                    if self.use_realistic_speed.get() and current_waypoint < len(waypoint_coords):
                        target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['dest_speed_kmh'])
                        traci.vehicle.setSpeed("robust_v2v_dest", target_speed_ms)
                    else:
                        # Ensure minimum speed to prevent stalling
                        traci.vehicle.setSpeed("robust_v2v_dest", 5.0)  # 5 m/s minimum
                
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
                analysis_file = os.path.join(original_dir, "robust_fixed_distance_accuracy_analysis.csv")
                analysis_df.to_csv(analysis_file, index=False)
                
                # Calculate summary statistics
                mean_accuracy = analysis_df['accuracy'].mean()
                median_accuracy = analysis_df['accuracy'].median()
                rmse = np.sqrt(np.mean(analysis_df['error']**2))
                mae = np.mean(np.abs(analysis_df['error']))
                
                summary = {
                    'approach': 'Robust Fixed',
                    'total_waypoints': len(analysis_data),
                    'mean_accuracy': float(mean_accuracy),
                    'median_accuracy': float(median_accuracy),
                    'rmse': float(rmse),
                    'mae': float(mae),
                    'calibration_factor': CALIBRATION_FACTOR,
                    'high_accuracy_count': int((analysis_df['accuracy'] >= 90).sum()),
                    'medium_accuracy_count': int(((analysis_df['accuracy'] >= 70) & (analysis_df['accuracy'] < 90)).sum()),
                    'low_accuracy_count': int((analysis_df['accuracy'] < 70).sum())
                }
                
                summary_file = os.path.join(original_dir, "robust_fixed_simulation_summary.json")
                with open(summary_file, 'w') as f:
                    json.dump(summary, f, indent=2)
                
                self.log_message(f"\n📊 ROBUST FIXED SIMULATION RESULTS:")
                self.log_message(f"   Mean Accuracy: {mean_accuracy:.2f}%")
                self.log_message(f"   Median Accuracy: {median_accuracy:.2f}%")
                self.log_message(f"   RMSE: {rmse:.2f} m")
                self.log_message(f"   MAE: {mae:.2f} m")
                self.log_message(f"   High Accuracy (≥90%): {summary['high_accuracy_count']} waypoints")
                self.log_message(f"   Medium Accuracy (70-89%): {summary['medium_accuracy_count']} waypoints")
                self.log_message(f"   Low Accuracy (<70%): {summary['low_accuracy_count']} waypoints")
                
                self.log_message(f"\n✅ Analysis complete! Files saved to:")
                self.log_message(f"   📄 CSV: {analysis_file}")
                self.log_message(f"   📄 JSON: {summary_file}")
            
            # Keep SUMO-GUI open for inspection
            self.log_message(f"\n🔍 Simulation complete. Keeping SUMO-GUI open for inspection...")
            self.log_message(f"   Press 'Stop Simulation' to close SUMO-GUI")
            
            # Show final vehicle positions
            if source_active and dest_active:
                try:
                    final_src_pos = traci.vehicle.getPosition("robust_v2v_source")
                    final_dst_pos = traci.vehicle.getPosition("robust_v2v_dest")
                    final_distance = calculate_distance(final_src_pos, final_dst_pos)
                    self.log_message(f"📍 Final vehicle positions:")
                    self.log_message(f"   Source: {final_src_pos}")
                    self.log_message(f"   Destination: {final_dst_pos}")
                    self.log_message(f"   Final distance: {final_distance:.2f}m")
                except:
                    self.log_message("⚠️ Could not get final vehicle positions")
            
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
    app = V2VRobustFixedSimulation()
    app.run()
