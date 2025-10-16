#!/usr/bin/env python3
"""
Advanced Tkinter-based SUMO Simulation Controller
Provides complete control over V2V simulation with row-by-row navigation
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import logging
import pandas as pd
import numpy as np
import traci
import json
from datetime import datetime
import os
import subprocess
from focused_v2v_simulator import FocusedV2VSimulator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')

class TkinterSimulationController:
    """Advanced Tkinter-based control panel for V2V SUMO simulation"""
    
    def __init__(self, csv_file="sidelink_parsed.csv"):
        self.csv_file = csv_file
        self.root = tk.Tk()
        self.root.title("V2V SUMO Simulation Controller")
        self.root.geometry("900x700")
        
        # Simulation control variables
        self.sumo_process = None
        self.simulation_active = False
        self.simulation_paused = False
        self.step_mode = False
        self.focused_simulator = None  # Will hold the FocusedV2VSimulator instance
        
        # Data variables
        self.csv_data = None
        self.current_row = 0
        self.vehicle_pair = None
        self.loaded_pairs = []
        
        # GUI variables
        self.status_var = tk.StringVar(value="Ready")
        self.row_var = tk.StringVar(value="0")
        self.total_rows_var = tk.StringVar(value="0")
        self.coords_var = tk.StringVar(value="Loading...")
        self.distance_var = tk.StringVar(value="0.0 m")
        
        # Simulator variables
        self.results = []
        self.simulation_step = 0
        self.simulator_thread = None
        
        self.setup_gui()
        self.load_csv_data()
        
    def setup_gui(self):
        """Setup the main GUI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="V2V SUMO Simulation Controller", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Control Section
        control_frame = ttk.LabelFrame(main_frame, text="Simulation Control", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(button_frame, text="Start SUMO", 
                                   command=self.start_simulation)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop SUMO", 
                                  command=self.stop_simulation, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = ttk.Button(button_frame, text="Pause", 
                                   command=self.pause_simulation, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.step_btn = ttk.Button(button_frame, text="Step", 
                                  command=self.step_simulation, state=tk.DISABLED)
        self.step_btn.pack(side=tk.LEFT, padx=5)
        
        # Row Navigation
        nav_frame = ttk.Frame(control_frame)
        nav_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(nav_frame, text="Row Navigation:").pack(side=tk.LEFT)
        
        self.prev_row_btn = ttk.Button(nav_frame, text="◀ Previous Row", 
                                       command=self.previous_row, state=tk.DISABLED)
        self.prev_row_btn.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(nav_frame, text="Row:").pack(side=tk.LEFT)
        self.row_entry = ttk.Entry(nav_frame, textvariable=self.row_var, width=5)
        self.row_entry.pack(side=tk.LEFT, padx=5)
        self.row_entry.bind('<Return>', self.load_specific_row)
        
        ttk.Label(nav_frame, text=f"of {len(self.loaded_pairs) if self.loaded_pairs else 0}").pack(side=tk.LEFT)
        
        self.next_row_btn = ttk.Button(nav_frame, text="Next Row ▶", 
                                      command=self.next_row, state=tk.DISABLED)
        self.next_row_btn.pack(side=tk.LEFT, padx=5)
        
        # Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Simulation Status", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        status_info_frame = ttk.Frame(status_frame)
        status_info_frame.pack(fill=tk.X)
        
        # Left side - row info
        left_info = ttk.Frame(status_info_frame)
        left_info.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_info, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(left_info, textvariable=self.status_var, 
                                     font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(left_info, text="Simulation Step:").pack(side=tk.LEFT, padx=(20, 0))
        self.step_label = ttk.Label(left_info, text="0")
        self.step_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Right side - vehicle info
        right_info = ttk.Frame(status_info_frame)
        right_info.pack(side=tk.RIGHT)
        
        ttk.Label(right_info, text="Current Row Step:").pack()
        self.current_step_label = ttk.Label(right_info, text="0/1000")
        self.current_step_label.pack()
        
        # Data Display Section
        data_frame = ttk.LabelFrame(main_frame, text="Current Scenario Data", padding="10")
        data_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(data_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # CSV Data Tab
        csv_frame = ttk.Frame(notebook)
        notebook.add(csv_frame, text="CSV Data")
        
        self.csv_text = scrolledtext.ScrolledText(csv_frame, height=8, width=80)
        self.csv_text.pack(fill=tk.BOTH, expand=True)
        
        # Coordinate Info Tab
        coord_frame = ttk.Frame(notebook)
        notebook.add(coord_frame, text="Vehicle Coordinates")
        
        coord_info_frame = ttk.Frame(coord_frame)
        coord_info_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(coord_info_frame, text="GPS Coordinates:", font=("Arial", 12, "bold")).pack()
        
        self.coords_display = ttk.Label(coord_info_frame, textvariable=self.coords_var, 
                                       font=("Monaco", 10))
        self.coords_display.pack(pady=5)
        
        ttk.Label(coord_info_frame, text="Actual Distance:", font=("Arial", 12, "bold")).pack()
        
        self.distance_display = ttk.Label(coord_info_frame, textvariable=self.distance_var, 
                                         font=("Arial", 14, "bold"))
        self.distance_display.pack(pady=5)
        
        # V2V Info Tab
        v2v_frame = ttk.Frame(notebook)
        notebook.add(v2v_frame, text="V2V Communication")
        
        self.v2v_text = scrolledtext.ScrolledText(v2v_frame, height=6, width=80)
        self.v2v_text.pack(fill=tk.BOTH, expand=True)
        
        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Simulation Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Auto-scroll handler for log
        self.log_text.config(state=tk.DISABLED)
        
    def log_message(self, message):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def load_csv_data(self):
        """Load CSV data and prepare vehicle pairs"""
        try:
            self.log_message("Loading CSV data...")
            
            # Load CSV data
            df = pd.read_csv(self.csv_file, nrows=2000)
            
            # Filter for valid coordinates with both source and destination
            valid_rows = df[
                (df['Source'] != df['Destination']) & 
                df['Latitude_destination'].notna() & 
                df['Longitude_destination'].notna()
            ].copy()
            
            if len(valid_rows) > 0:
                # Group by Source-Destination pairs and take first occurrence
                pairs = valid_rows.groupby(['Source', 'Destination']).first().reset_index()
                
                # Take up to 50 pairs for simulation
                self.loaded_pairs = pairs.head(50)
                
                # Update GUI
                self.total_rows_var.set(str(len(self.loaded_pairs)))
                
                # Setup first row
                self.current_row = 0
                self.load_current_row_data()
                
                self.log_message(f"Loaded {len(self.loaded_pairs)} V2V scenarios")
                
                # Enable navigation if we have data
                if len(self.loaded_pairs) > 1:
                    self.next_row_btn.config(state=tk.NORMAL)
                    
            else:
                self.log_message("No valid V2V scenarios found in CSV")
                
        except Exception as e:
            self.log_message(f"Error loading CSV data: {e}")
            messagebox.showerror("Error", f"Failed to load CSV data: {e}")
    
    def load_current_row_data(self):
        """Load data for current row and update focused_simulator"""
        if not self.loaded_pairs or self.current_row >= len(self.loaded_pairs):
            return
            
        try:
            row_data = self.loaded_pairs.iloc[self.current_row]
            
            # Update GUI variables
            self.row_var.set(str(self.current_row))
            
            # Extract coordinates
            src_lat = row_data['lat']
            src_lon = row_data['lon']
            dst_lat = row_data['Latitude_destination']
            dst_lon = row_data['Longitude_destination']
            
            coord_text = f"Source: ({src_lat:.6f}, {src_lon:.6f})\nDestination: ({dst_lat:.6f}, {dst_lon:.6f})"
            self.coords_var.set(coord_text)
            
            # Calculate actual distance
            actual_distance = self.calculate_gps_distance(src_lat, src_lon, dst_lat, dst_lon)
            self.distance_var.set(f"{actual_distance:.2f} m")
            
            # Create vehicle pair data
            self.vehicle_pair = {
                'source_id': f"src_{row_data['Source']}_{self.current_row}",
                'dest_id': f"dst_{row_data['Destination']}_{self.current_row}",
                'src_coords': (src_lat, src_lon),
                'dst_coords': (dst_lat, dst_lon),
                'actual_distance': actual_distance,
                'row_data': row_data
            }
            
            # Update focused_simulator if it exists
            if self.focused_simulator:
                self.update_focused_simulator_row()
            
            # Update CSV display
            self.update_csv_display(row_data)
            
            self.log_message(f"Loaded row {self.current_row}: {self.vehicle_pair['source_id']} <-> {self.vehicle_pair['dest_id']}")
            
        except Exception as e:
            self.log_message(f"Error loading row data: {e}")
    
    def update_focused_simulator_row(self):
        """Update the focused simulator with current row data"""
        if self.focused_simulator and self.vehicle_pair:
            try:
                # Update the simulator's current row index
                self.focused_simulator.current_row_index = self.current_row
                
                # Update vehicle pair in simulator
                if hasattr(self.focused_simulator, 'vehicle_pair'):
                    self.focused_simulator.vehicle_pair = self.vehicle_pair
                
                # Recreate vehicle pair from row data like the simulator does
                if hasattr(self.focused_simulator, '_create_vehicle_pair_from_row'):
                    self.focused_simulator._create_vehicle_pair_from_row(self.current_row)
                
                self.log_message(f"Updated focused simulator to row {self.current_row}")
                
            except Exception as e:
                self.log_message(f"Error updating focused simulator: {e}")
    
    def calculate_gps_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between GPS coordinates using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in meters
        r = 6371000
        return c * r
    
    def update_csv_display(self, row_data):
        """Update CSV data display"""
        try:
            # Select relevant columns for display
            display_cols = ['Source', 'Destination', 'lat', 'lon', 
                           'Latitude_destination', 'Longitude_destination',
                           'SNR', 'RSRP', 'RSSI']
            
            display_data = row_data[display_cols].to_dict()
            
            # Format for display
            formatted_text = "Current CSV Row Data:\n" + "="*50 + "\n"
            for key, value in display_data.items():
                formatted_text += f"{key}: {value}\n"
            
            self.csv_text.delete(1.0, tk.END)
            self.csv_text.insert(1.0, formatted_text)
            
            # Update V2V communication display
            v2v_text = f"V2V Communication Parameters:\n" + "="*50 + "\n"
            v2v_text += f"SNR: {display_data.get('SNR', 'N/A')} dB\n"
            v2v_text += f"RSRP: {display_data.get('RSRP', 'N/A')} dBm\n"
            v2v_text += f"RSSI: {display_data.get('RSSI', 'N/A')} dBm\n"
            v2v_text += f"Communication Distance: {self.vehicle_pair['actual_distance']:.2f}m\n"
            
            self.v2v_text.delete(1.0, tk.END)
            self.v2v_text.insert(1.0, v2v_text)
            
        except Exception as e:
            self.log_message(f"Error updating display: {e}")
    
    def previous_row(self):
        """Load previous row"""
        if self.current_row > 0:
            self.current_row -= 1
            self.load_current_row_data()
            
            if self.current_row == 0:
                self.prev_row_btn.config(state=tk.DISABLED)
            if self.current_row < len(self.loaded_pairs) - 1:
                self.next_row_btn.config(state=tk.NORMAL)
    
    def next_row(self):
        """Load next row"""
        if self.current_row < len(self.loaded_pairs) - 1:
            self.current_row += 1
            self.load_current_row_data()
            
            if self.current_row == len(self.loaded_pairs) - 1:
                self.next_row_btn.config(state=tk.DISABLED)
            if self.current_row > 0:
                self.prev_row_btn.config(state=tk.NORMAL)
    
    def load_specific_row(self, event=None):
        """Load specific row number"""
        try:
            row_num = int(self.row_var.get())
            if 0 <= row_num < len(self.loaded_pairs):
                self.current_row = row_num
                self.load_current_row_data()
                
                # Update navigation buttons
                self.prev_row_btn.config(state=tk.NORMAL if row_num > 0 else tk.DISABLED)
                self.next_row_btn.config(state=tk.NORMAL if row_num < len(self.loaded_pairs) - 1 else tk.DISABLED)
            else:
                messagebox.showwarning("Invalid Row", f"Row number must be between 0 and {len(self.loaded_pairs)-1}")
                self.row_var.set(str(self.current_row))
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid row number")
            self.row_var.set(str(self.current_row))
    
    def start_simulation(self):
        """Start focused_v2v_simulator"""
        try:
            self.log_message("Starting focused V2V simulator...")
            
            # Create the focused simulator instance
            self.focused_simulator = FocusedV2VSimulator(self.csv_file)
            
            # Connect GUI to simulator's control panel
            self.connect_to_simulator()
            
            # Start simulation in a separate thread
            def run_focused_simulator():
                try:
                    # Set the current row in the simulator
                    if hasattr(self.focused_simulator, 'current_row_index'):
                        self.focused_simulator.current_row_index = self.current_row
                    
                    # Start the simulation
                    self.root.after(0, lambda: self.status_var.set("Starting SUMO..."))
                    self.focused_simulator.run_simulation()
                    self.simulation_active = True
                    self.root.after(0, self.update_gui_after_start)
                except Exception as e:
                    self.root.after(0, lambda: self.log_message(f"Simulator execution error: {e}"))
            
            self.simulator_thread = threading.Thread(target=run_focused_simulator, daemon=True)
            self.simulator_thread.start()
            
        except Exception as e:
            self.log_message(f"Error starting focused simulator: {e}")
            messagebox.showerror("Error", f"Failed to start focused simulator: {e}")
    
    def connect_to_simulator(self):
        """Connect GUI controls to the focused simulator"""
        if self.focused_simulator:
            # Connect our GUI to the simulator's control variables
            self.focused_simulator.paused = False
            
            # Override simulator's control panel if it exists
            if hasattr(self.focused_simulator, 'control_panel'):
                # Replace the simulator's control panel with our own
                pass
                
            self.log_message("Connected GUI to focused simulator")
    
    def update_gui_after_start(self):
        """Update GUI after SUMO starts"""
        self.status_var.set("SUMO Running - Ready to Simulate")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.NORMAL)
        self.step_btn.config(state=tk.NORMAL)
        self.log_message("SUMO simulation started successfully")
    
    def stop_simulation(self):
        """Stop focused_v2v_simulator"""
        try:
            self.log_message("Stopping focused V2V simulator...")
            
            # Stop the focused simulator
            if self.focused_simulator:
                # Set pause flag to stop the simulation loop
                self.focused_simulator.paused = True
                
                # Close TraCI connection
                try:
                    traci.close()
                except:
                    pass
            
            self.simulation_active = False
            self.simulation_paused = False
            
            self.status_var.set("Simulation Stopped")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.DISABLED)
            self.step_btn.config(state=tk.DISABLED)
            
            self.log_message("Focused V2V simulator stopped")
            
        except Exception as e:
            self.log_message(f"Error stopping simulation: {e}")
    
    def pause_simulation(self):
        """Pause/resume focused_simulator"""
        if self.focused_simulator:
            if self.simulation_paused:
                self.simulation_paused = False
                self.focused_simulator.paused = False
                self.pause_btn.config(text="Pause")
                self.status_var.set("SUMO Running - Simulating")
            else:
                self.simulation_paused = True
                self.focused_simulator.paused = True
                self.pause_btn.config(text="Resume")
                self.status_var.set("SUMO Running - Paused")
    
    def step_simulation(self):
        """Step simulation one step"""
        if not self.simulation_active:
            return
            
        try:
            # Place vehicles if not already placed
            if not self.vehicle_pair.get('placed', False):
                self.place_vehicles()
            
            # Run one simulation step
            traci.simulationStep()
            self.simulation_step += 1
            
            # Update display
            self.step_label.config(text=str(self.simulation_step))
            self.current_step_label.config(text=f"{self.simulation_step}/1000")
            
            # Check if vehicles are still active
            active_vehicles = traci.vehicle.getIDList()
            
            if self.vehicle_pair['source_id'] in active_vehicles and self.vehicle_pair['dest_id'] in active_vehicles:
                # Update vehicle positions and communication
                src_pos = traci.vehicle.getPosition(self.vehicle_pair['source_id'])
                dst_pos = traci.vehicle.getPosition(self.vehicle_pair['dest_id'])
                sim_distance = np.sqrt((src_pos[0] - dst_pos[0])**2 + (src_pos[1] - dst_pos[1])**2)
                
                self.log_message(f"Step {self.simulation_step}: Vehicles active, Distance: {sim_distance:.1f}m")
            else:
                self.log_message(f"Step {self.simulation_step}: Vehicles finished/removed")
                
        except Exception as e:
            self.log_message(f"Step simulation error: {e}")
    
    def place_vehicles(self):
        """Place vehicles in SUMO simulation"""
        if not self.simulation_active or not self.vehicle_pair:
            return
            
        try:
            self.log_message("Placing V2V vehicles...")
            
            # Get valid edges
            edges = traci.edge.getIDList()
            road_edges = [e for e in edges if not e.startswith(':') and not e.startswith('-')]
            
            if len(road_edges) < 2:
                self.log_message("Not enough edges for vehicle placement")
                return
            
            # Select source and destination edges
            src_edge = road_edges[0]
            dst_edge = road_edges[1]
            
            # Add vehicles
            traci.vehicle.add(vehID=self.vehicle_pair['source_id'], 
                           typeID="DEFAULT_VEHTYPE", 
                           routeID="", 
                           depart=0.0, 
                           departLane="best")
            
            traci.vehicle.add(vehID=self.vehicle_pair['dest_id'], 
                           typeID="DEFAULT_VEHTYPE", 
                           routeID="", 
                           depart=0.1, 
                           departLane="best")
            
            # Place vehicles on edges
            try:
                # Use moveToXY for precise GPS placement
                src_lat, src_lon = self.vehicle_pair['src_coords']
                dst_lat, dst_lon = self.vehicle_pair['dst_coords']
                
                src_x, src_y = traci.simulation.convertGeo(src_lon, src_lat)
                dst_x, dst_y = traci.simulation.convertGeo(dst_lon, dst_lat)
                
                traci.vehicle.moveToXY(vehID=self.vehicle_pair['source_id'], 
                                     edgeID=src_edge, 
                                     laneIndex=-1, 
                                     x=src_x, y=src_y, 
                                     angle=traci.constants.INVALID_DOUBLE_VALUE, 
                                     keepRoute=2)
                
                traci.vehicle.moveToXY(vehID=self.vehicle_pair['dest_id'], 
                                     edgeID=dst_edge, 
                                     laneIndex=-1, 
                                     x=dst_x, y=dst_y, 
                                     angle=traci.constants.INVALID_DOUBLE_VALUE, 
                                     keepRoute=2)
                
                # Set routes
                traci.vehicle.changeTarget(self.vehicle_pair['source_id'], dst_edge)
                traci.vehicle.changeTarget(self.vehicle_pair['dest_id'], src_edge)
                
                # Set colors
                traci.vehicle.setColor(self.vehicle_pair['source_id'], (255, 0, 0, 255))  # Red
                traci.vehicle.setColor(self.vehicle_pair['dest_id'], (0, 0, 255, 255))   # Blue
                
                self.vehicle_pair['placed'] = True
                
                self.log_message(f"Vehicles placed: {self.vehicle_pair['source_id']} (red) -> {self.vehicle_pair['dest_id']} (blue)")
                
            except Exception as e:
                self.log_message(f"Error with GPS placement, using edge placement: {e}")
                
                # Fallback to edge placement
                traci.vehicle.changeTarget(self.vehicle_pair['source_id'], dst_edge)
                traci.vehicle.changeTarget(self.vehicle_pair['dest_id'], src_edge)
                
                self.vehicle_pair['placed'] = True
            
        except Exception as e:
            self.log_message(f"Error placing vehicles: {e}")
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()
    
    def __del__(self):
        """Cleanup when closing"""
        if hasattr(self, 'simulation_active') and self.simulation_active:
            try:
                traci.simulation.close()
            except:
                pass

def main():
    """Main function to run the controller"""
    try:
        controller = TkinterSimulationController()
        controller.run()
    except Exception as e:
        print(f"Error running controller: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
