#!/usr/bin/env python3
"""
Enhanced V2V Simulation with GUI Controls
Features: Adjustable waypoints, play/pause controls, car visualization, vehicle control
"""

import tkinter as tk
from tkinter import ttk, messagebox
import traci
import pandas as pd
import sumolib
import os
import time
import json
import math
import threading
from datetime import datetime

class V2VSimulationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("V2V Simulation Controller")
        self.root.geometry("800x600")
        
        # Simulation state
        self.simulation_running = False
        self.simulation_paused = False
        self.traci_connected = False
        self.current_step = 0
        self.max_steps = 1000
        self.waypoint_count = 50  # Default: 50 waypoints
        self.point_index = 0
        self.lane_mapped_points = []
        
        # Vehicle state
        self.source_vehicle_added = False
        self.dest_vehicle_added = False
        
        # Setup GUI
        self.setup_gui()
        
        # Load data
        self.load_gps_data()
        
    def setup_gui(self):
        """Setup the GUI interface"""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="V2V Simulation Controller", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Waypoint Control Section
        waypoint_frame = ttk.LabelFrame(main_frame, text="Waypoint Control", padding="10")
        waypoint_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(waypoint_frame, text="Number of Waypoints:").grid(row=0, column=0, padx=(0, 10))
        
        self.waypoint_var = tk.IntVar(value=50)
        waypoint_spinbox = ttk.Spinbox(waypoint_frame, from_=10, to=200, width=10,
                                      textvariable=self.waypoint_var, command=self.update_waypoint_count)
        waypoint_spinbox.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(waypoint_frame, text="Load Waypoints", 
                  command=self.load_waypoints).grid(row=0, column=2, padx=(10, 0))
        
        # Simulation Control Section
        control_frame = ttk.LabelFrame(main_frame, text="Simulation Control", padding="10")
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Control buttons
        self.start_button = ttk.Button(control_frame, text="Start SUMO", 
                                      command=self.start_sumo_simulation)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.play_button = ttk.Button(control_frame, text="Play", 
                                     command=self.play_simulation, state="disabled")
        self.play_button.grid(row=0, column=1, padx=(0, 10))
        
        self.pause_button = ttk.Button(control_frame, text="Pause", 
                                      command=self.pause_simulation, state="disabled")
        self.pause_button.grid(row=0, column=2, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop", 
                                     command=self.stop_simulation, state="disabled")
        self.stop_button.grid(row=0, column=3, padx=(0, 10))
        
        # Vehicle Control Section
        vehicle_frame = ttk.LabelFrame(main_frame, text="Vehicle Control", padding="10")
        vehicle_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Source vehicle controls
        ttk.Label(vehicle_frame, text="Source Vehicle (Blue):").grid(row=0, column=0, sticky=tk.W)
        self.source_speed_var = tk.DoubleVar(value=50.0)
        ttk.Scale(vehicle_frame, from_=0, to=100, variable=self.source_speed_var, 
                 orient=tk.HORIZONTAL, length=150).grid(row=0, column=1, padx=(10, 0))
        ttk.Label(vehicle_frame, text="Speed (km/h)").grid(row=0, column=2, padx=(5, 0))
        
        # Destination vehicle controls
        ttk.Label(vehicle_frame, text="Destination Vehicle (Red):").grid(row=1, column=0, sticky=tk.W)
        self.dest_speed_var = tk.DoubleVar(value=50.0)
        ttk.Scale(vehicle_frame, from_=0, to=100, variable=self.dest_speed_var, 
                 orient=tk.HORIZONTAL, length=150).grid(row=1, column=1, padx=(10, 0))
        ttk.Label(vehicle_frame, text="Speed (km/h)").grid(row=1, column=2, padx=(5, 0))
        
        # Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Simulation Status", padding="10")
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_text = tk.Text(status_frame, height=8, width=70)
        self.status_text.grid(row=0, column=0, columnspan=3)
        
        # Scrollbar for status text
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.grid(row=0, column=3, sticky=(tk.N, tk.S))
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        # Progress Section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(progress_frame, text="Progress:").grid(row=0, column=0, padx=(0, 10))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=300)
        self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
    def log_status(self, message):
        """Add message to status log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def load_gps_data(self):
        """Load GPS data from CSV"""
        try:
            self.df = pd.read_csv('vehicle_2_4_first_200.csv')
            self.log_status(f"✅ Loaded {len(self.df)} GPS records")
        except Exception as e:
            self.log_status(f"❌ Error loading GPS data: {e}")
            messagebox.showerror("Error", f"Failed to load GPS data: {e}")
            
    def update_waypoint_count(self):
        """Update waypoint count from spinbox"""
        self.waypoint_count = self.waypoint_var.get()
        self.log_status(f"Waypoint count set to: {self.waypoint_count}")
        
    def load_waypoints(self):
        """Load and map waypoints to lanes"""
        if not hasattr(self, 'df'):
            messagebox.showerror("Error", "GPS data not loaded")
            return
            
        self.log_status(f"📍 Loading {self.waypoint_count} waypoints...")
        
        # Change to SUMO directory
        original_dir = os.getcwd()
        os.chdir('berlin-sumo-closed-netwokr')
        
        try:
            # Load network
            net_file = 'osm.net.xml.gz'
            net = sumolib.net.readNet(net_file)
            
            # Get waypoints
            waypoints_df = self.df.head(self.waypoint_count)
            self.lane_mapped_points = []
            
            for idx, row in waypoints_df.iterrows():
                # Source vehicle waypoint
                src_lat = row['Latitude_source']
                src_lon = row['Longitude_source']
                src_x, src_y = net.convertLonLat2XY(src_lon, src_lat)
                
                # Find nearest lane
                edges = net.getNeighboringEdges(src_x, src_y, r=50)
                if edges:
                    closest_edge = min(edges, key=lambda x: x[1])[0]
                    edge_id = closest_edge.getID()
                    lane_id = f"{edge_id}_0"
                    
                    self.lane_mapped_points.append({
                        'index': idx,
                        'vehicle': 2,
                        'gps_lat': src_lat,
                        'gps_lon': src_lon,
                        'sumo_x': src_x,
                        'sumo_y': src_y,
                        'edge_id': edge_id,
                        'lane_id': lane_id,
                        'mapped': True
                    })
                
                # Destination vehicle waypoint
                dst_lat = row['Latitude_destination']
                dst_lon = row['Longitude_destination']
                dst_x, dst_y = net.convertLonLat2XY(dst_lon, dst_lat)
                
                edges = net.getNeighboringEdges(dst_x, dst_y, r=50)
                if edges:
                    closest_edge = min(edges, key=lambda x: x[1])[0]
                    edge_id = closest_edge.getID()
                    lane_id = f"{edge_id}_0"
                    
                    self.lane_mapped_points.append({
                        'index': idx,
                        'vehicle': 4,
                        'gps_lat': dst_lat,
                        'gps_lon': dst_lon,
                        'sumo_x': dst_x,
                        'sumo_y': dst_y,
                        'edge_id': edge_id,
                        'lane_id': lane_id,
                        'mapped': True
                    })
            
            self.log_status(f"✅ Mapped {len(self.lane_mapped_points)} waypoints to lanes")
            
        except Exception as e:
            self.log_status(f"❌ Error mapping waypoints: {e}")
            messagebox.showerror("Error", f"Failed to map waypoints: {e}")
        finally:
            os.chdir(original_dir)
            
    def start_sumo_simulation(self):
        """Start SUMO simulation"""
        if self.simulation_running:
            return
            
        self.log_status("🚀 Starting SUMO-GUI simulation...")
        
        # Change to SUMO directory
        original_dir = os.getcwd()
        os.chdir('berlin-sumo-closed-netwokr')
        
        try:
            # Start SUMO-GUI
            sumo_cmd = ["sumo-gui", "-c", "osm.sumocfg", "--start"]
            traci.start(sumo_cmd)
            time.sleep(3)
            
            self.traci_connected = True
            self.simulation_running = True
            
            # Add POI markers
            self.add_poi_markers()
            
            # Add vehicles with car models
            self.add_vehicles()
            
            # Update button states
            self.start_button.config(state="disabled")
            self.play_button.config(state="normal")
            self.stop_button.config(state="normal")
            
            self.log_status("✅ SUMO-GUI started successfully")
            self.log_status("🎮 Use Play/Pause buttons to control simulation")
            
        except Exception as e:
            self.log_status(f"❌ Failed to start SUMO: {e}")
            messagebox.showerror("Error", f"Failed to start SUMO: {e}")
            self.traci_connected = False
        finally:
            os.chdir(original_dir)
            
    def add_poi_markers(self):
        """Add POI markers for waypoints"""
        if not self.traci_connected:
            return
            
        self.log_status("📍 Adding POI markers...")
        
        for i, point in enumerate(self.lane_mapped_points):
            if point['vehicle'] == 2:  # Source
                traci.poi.add(
                    f"src_poi_{i}",
                    point['sumo_x'], point['sumo_y'],
                    color=(0, 0, 255, 255),  # Blue
                    poiType="Source_Waypoint",
                    layer=100
                )
            else:  # Destination
                traci.poi.add(
                    f"dst_poi_{i}",
                    point['sumo_x'], point['sumo_y'],
                    color=(255, 0, 0, 255),  # Red
                    poiType="Dest_Waypoint",
                    layer=100
                )
        
        self.log_status(f"✅ Added {len(self.lane_mapped_points)} POI markers")
        
    def add_vehicles(self):
        """Add vehicles with car models"""
        if not self.traci_connected:
            return
            
        self.log_status("🚗 Adding vehicles with car models...")
        
        try:
            # Get available vehicle types
            vehicle_types = traci.vehicletype.getIDList()
            routes = traci.route.getIDList()
            
            if vehicle_types and routes:
                default_type = vehicle_types[0]
                default_route = routes[0]
                
                # Add source vehicle
                traci.vehicle.add("sourceVehicle", default_route, typeID=default_type)
                traci.vehicle.setColor("sourceVehicle", (0, 0, 255, 255))  # Blue
                traci.vehicle.setLength("sourceVehicle", 4.5)
                traci.vehicle.setWidth("sourceVehicle", 1.8)
                
                # Add destination vehicle
                traci.vehicle.add("destVehicle", default_route, typeID=default_type)
                traci.vehicle.setColor("destVehicle", (255, 0, 0, 255))  # Red
                traci.vehicle.setLength("destVehicle", 4.5)
                traci.vehicle.setWidth("destVehicle", 1.8)
                
                self.source_vehicle_added = True
                self.dest_vehicle_added = True
                
                self.log_status("✅ Vehicles added successfully")
                self.log_status("🚗 Vehicles will appear as 3D car models in SUMO-GUI")
                
            else:
                self.log_status("⚠️ No vehicle types or routes available")
                
        except Exception as e:
            self.log_status(f"❌ Failed to add vehicles: {e}")
            
    def play_simulation(self):
        """Start/pause simulation"""
        if not self.simulation_running:
            return
            
        if self.simulation_paused:
            self.simulation_paused = False
            self.play_button.config(text="Pause")
            self.log_status("▶️ Simulation resumed")
        else:
            self.simulation_paused = True
            self.play_button.config(text="Play")
            self.log_status("⏸️ Simulation paused")
            
    def pause_simulation(self):
        """Pause simulation (same as play when paused)"""
        self.play_simulation()
        
    def stop_simulation(self):
        """Stop simulation"""
        self.simulation_running = False
        self.simulation_paused = False
        
        if self.traci_connected:
            try:
                traci.close()
                self.traci_connected = False
            except:
                pass
        
        # Update button states
        self.start_button.config(state="normal")
        self.play_button.config(state="disabled", text="Play")
        self.pause_button.config(state="disabled")
        self.stop_button.config(state="disabled")
        
        self.log_status("⏹️ Simulation stopped")
        
    def simulation_loop(self):
        """Main simulation loop (runs in separate thread)"""
        while self.simulation_running:
            if not self.simulation_paused and self.traci_connected:
                try:
                    # Step simulation
                    traci.simulationStep()
                    self.current_step += 1
                    
                    # Move vehicles every 30 steps
                    if self.current_step % 30 == 0 and self.point_index < len(self.lane_mapped_points):
                        self.move_vehicles_to_waypoint()
                    
                    # Update vehicle speeds
                    self.update_vehicle_speeds()
                    
                    # Calculate distance every 10 steps
                    if self.current_step % 10 == 0:
                        self.calculate_distance()
                    
                    # Update progress
                    progress = min(100, (self.current_step / self.max_steps) * 100)
                    self.progress_var.set(progress)
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.log_status(f"❌ Simulation error: {e}")
                    break
            else:
                time.sleep(0.1)
                
    def move_vehicles_to_waypoint(self):
        """Move vehicles to next waypoint"""
        if self.point_index >= len(self.lane_mapped_points):
            return
            
        current_point = self.lane_mapped_points[self.point_index]
        
        try:
            if current_point['vehicle'] == 2 and self.source_vehicle_added:
                traci.vehicle.moveToXY(
                    "sourceVehicle",
                    "dummy", 0,
                    current_point['sumo_x'],
                    current_point['sumo_y'],
                    angle=0, keepRoute=0, matchThreshold=100
                )
                self.log_status(f"📍 Moved source vehicle to waypoint {self.point_index}")
                
            elif current_point['vehicle'] == 4 and self.dest_vehicle_added:
                traci.vehicle.moveToXY(
                    "destVehicle",
                    "dummy", 0,
                    current_point['sumo_x'],
                    current_point['sumo_y'],
                    angle=0, keepRoute=0, matchThreshold=100
                )
                self.log_status(f"📍 Moved dest vehicle to waypoint {self.point_index}")
                
        except Exception as e:
            self.log_status(f"⚠️ Failed to move vehicle: {e}")
            
        self.point_index += 1
        
    def update_vehicle_speeds(self):
        """Update vehicle speeds based on GUI controls"""
        if not self.traci_connected:
            return
            
        try:
            if self.source_vehicle_added:
                speed = self.source_speed_var.get() / 3.6  # Convert km/h to m/s
                traci.vehicle.setSpeed("sourceVehicle", speed)
                
            if self.dest_vehicle_added:
                speed = self.dest_speed_var.get() / 3.6  # Convert km/h to m/s
                traci.vehicle.setSpeed("destVehicle", speed)
                
        except Exception as e:
            pass  # Ignore speed update errors
            
    def calculate_distance(self):
        """Calculate distance between vehicles"""
        if not self.traci_connected or not (self.source_vehicle_added and self.dest_vehicle_added):
            return
            
        try:
            src_pos = traci.vehicle.getPosition("sourceVehicle")
            dest_pos = traci.vehicle.getPosition("destVehicle")
            
            distance = math.sqrt((src_pos[0] - dest_pos[0])**2 + (src_pos[1] - dest_pos[1])**2)
            
            if self.current_step % 50 == 0:  # Log every 50 steps
                self.log_status(f"📏 Distance: {distance:.2f}m")
                
        except Exception as e:
            pass  # Ignore distance calculation errors
            
    def run(self):
        """Start the GUI"""
        # Start simulation loop in separate thread
        simulation_thread = threading.Thread(target=self.simulation_loop, daemon=True)
        simulation_thread.start()
        
        # Start GUI main loop
        self.root.mainloop()

def main():
    root = tk.Tk()
    app = V2VSimulationGUI(root)
    app.run()

if __name__ == "__main__":
    main()
