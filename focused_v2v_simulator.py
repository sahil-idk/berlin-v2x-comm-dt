#!/usr/bin/env python3
"""
Focused V2V Simulation - Only 2 vehicles with proper TraCI execution
Shows V2V communication with zoom and highlighting
"""

import traci
import pandas as pd
import numpy as np
import json
import os
import random
import logging
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import math

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class V2VControlPanel:
    """Enhanced Tkinter GUI Control Panel for V2V Simulation"""
    
    def __init__(self, simulator):
        self.simulator = simulator
        self.root = tk.Tk()
        self.root.title("Enhanced V2V Simulation Control Panel")
        self.root.geometry("600x800")
        
        # Current CSV row data
        self.current_row_data = None
        self.row_index = 0
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the enhanced GUI controls with scrollable panel"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Enhanced V2V Communication Control", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Left panel for controls
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Right panel for CSV data display
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Vehicle information
        info_frame = ttk.LabelFrame(left_panel, text="V2V Vehicles", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.source_label = ttk.Label(info_frame, text="Source: Not placed")
        self.source_label.grid(row=0, column=0, sticky=tk.W)
        
        self.dest_label = ttk.Label(info_frame, text="Destination: Not placed")
        self.dest_label.grid(row=1, column=0, sticky=tk.W)
        
        # Camera controls
        camera_frame = ttk.LabelFrame(left_panel, text="Camera Controls", padding="10")
        camera_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Zoom to source vehicle
        self.zoom_source_btn = ttk.Button(camera_frame, text="Zoom to Source", 
                                        command=self.zoom_to_source, state="disabled")
        self.zoom_source_btn.grid(row=0, column=0, pady=2)
        
        # Zoom to destination vehicle
        self.zoom_dest_btn = ttk.Button(camera_frame, text="Zoom to Destination", 
                                      command=self.zoom_to_destination, state="disabled")
        self.zoom_dest_btn.grid(row=1, column=0, pady=2)
        
        # Zoom to both vehicles
        self.zoom_both_btn = ttk.Button(camera_frame, text="Zoom to Both", 
                                      command=self.zoom_to_both, state="disabled")
        self.zoom_both_btn.grid(row=2, column=0, pady=2)
        
        # Follow vehicles
        self.follow_btn = ttk.Button(camera_frame, text="Follow Vehicles", 
                                   command=self.toggle_follow, state="disabled")
        self.follow_btn.grid(row=3, column=0, pady=2)
        
        # Rotate camera
        self.rotate_btn = ttk.Button(camera_frame, text="Rotate Camera", 
                                   command=self.toggle_rotation, state="disabled")
        self.rotate_btn.grid(row=4, column=0, pady=2)
        
        # Simulation controls
        sim_frame = ttk.LabelFrame(left_panel, text="Simulation Controls", padding="10")
        sim_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Start button
        self.start_btn = ttk.Button(sim_frame, text="Start Simulation", 
                                  command=self.start_simulation, state="normal")
        self.start_btn.grid(row=0, column=0, pady=2)
        
        # Pause/Resume button
        self.pause_btn = ttk.Button(sim_frame, text="Pause Simulation", 
                                  command=self.toggle_pause, state="disabled")
        self.pause_btn.grid(row=1, column=0, pady=2)
        
        # Step button
        self.step_btn = ttk.Button(sim_frame, text="Single Step", 
                                 command=self.single_step, state="disabled")
        self.step_btn.grid(row=2, column=0, pady=2)
        
        # Next row button
        self.next_row_btn = ttk.Button(sim_frame, text="Next CSV Row", 
                                     command=self.next_csv_row, state="disabled")
        self.next_row_btn.grid(row=3, column=0, pady=2)
        
        # Status information
        status_frame = ttk.LabelFrame(left_panel, text="Status", padding="10")
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Simulation not started")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.distance_label = ttk.Label(status_frame, text="Distance: N/A")
        self.distance_label.grid(row=1, column=0, sticky=tk.W)
        
        self.comm_label = ttk.Label(status_frame, text="Communication: N/A")
        self.comm_label.grid(row=2, column=0, sticky=tk.W)
        
        self.v2v_link_label = ttk.Label(status_frame, text="V2V Link: N/A")
        self.v2v_link_label.grid(row=3, column=0, sticky=tk.W)
        
        # Distance comparison display
        self.simulated_distance_label = ttk.Label(status_frame, text="Simulated Distance: N/A")
        self.simulated_distance_label.grid(row=4, column=0, sticky=tk.W)
        
        self.actual_distance_label = ttk.Label(status_frame, text="Actual Distance: N/A")
        self.actual_distance_label.grid(row=5, column=0, sticky=tk.W)
        
        self.accuracy_label = ttk.Label(status_frame, text="Accuracy: N/A")
        self.accuracy_label.grid(row=6, column=0, sticky=tk.W)
        
        # CSV Data Display Panel (Right side)
        csv_frame = ttk.LabelFrame(right_panel, text="Current CSV Row Data", padding="10")
        csv_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollable text area for CSV data
        self.csv_text = scrolledtext.ScrolledText(csv_frame, width=40, height=25, wrap=tk.WORD)
        self.csv_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        left_panel.columnconfigure(0, weight=1)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        csv_frame.columnconfigure(0, weight=1)
        csv_frame.rowconfigure(0, weight=1)
        
    def update_vehicle_info(self, vehicle_pair):
        """Update vehicle information display"""
        if vehicle_pair:
            self.source_label.config(text=f"Source: {vehicle_pair['source_id']} (Red)")
            self.dest_label.config(text=f"Destination: {vehicle_pair['dest_id']} (Blue)")
            
            # Enable buttons
            self.zoom_source_btn.config(state="normal")
            self.zoom_dest_btn.config(state="normal")
            self.zoom_both_btn.config(state="normal")
            self.follow_btn.config(state="normal")
            self.rotate_btn.config(state="normal")
            self.pause_btn.config(state="normal")
            self.step_btn.config(state="normal")
            self.next_row_btn.config(state="normal")
            
    def start_simulation(self):
        """Start the simulation"""
        if hasattr(self.simulator, 'start_simulation'):
            self.simulator.start_simulation()
            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal")
            self.step_btn.config(state="normal")
            self.status_label.config(text="Simulation started")
        else:
            messagebox.showinfo("Info", "Simulation not ready")
            
    def update_csv_display(self, row_data, row_index):
        """Update the CSV data display panel"""
        self.current_row_data = row_data
        self.row_index = row_index
        
        # Clear previous content
        self.csv_text.delete(1.0, tk.END)
        
        # Display CSV row information
        display_text = f"CSV Row Index: {row_index}\n"
        display_text += f"Total Rows Available: {len(self.simulator.csv_data) if self.simulator.csv_data is not None else 0}\n"
        display_text += "=" * 50 + "\n\n"
        
        if row_data is not None:
            # Basic vehicle information
            display_text += "VEHICLE INFORMATION:\n"
            display_text += f"Source ID: {row_data.get('Source', 'N/A')}\n"
            display_text += f"Destination ID: {row_data.get('Destination', 'N/A')}\n"
            display_text += f"Scenario: {row_data.get('Scenario', 'N/A')}\n\n"
            
            # GPS coordinates
            display_text += "GPS COORDINATES:\n"
            display_text += f"Source Lat: {row_data.get('lat', 'N/A')}\n"
            display_text += f"Source Lon: {row_data.get('lon', 'N/A')}\n"
            display_text += f"Destination Lat: {row_data.get('lat', 'N/A')}\n"
            display_text += f"Destination Lon: {row_data.get('lon', 'N/A')}\n\n"
            
            # Communication parameters
            display_text += "V2V COMMUNICATION:\n"
            display_text += f"SNR: {row_data.get('SNR', 'N/A')} dB\n"
            display_text += f"RSRP: {row_data.get('RSRP', 'N/A')} dBm\n"
            display_text += f"RSSI: {row_data.get('RSSI', 'N/A')} dBm\n"
            display_text += f"MCS: {row_data.get('MCS', 'N/A')}\n"
            display_text += f"RX Gain: {row_data.get('RX_GAIN', 'N/A')} dB\n"
            display_text += f"Noise Power: {row_data.get('NOISE_POWER', 'N/A')}\n"
            display_text += f"Rx Power: {row_data.get('Rx_power', 'N/A')}\n\n"
            
            # Network performance
            display_text += "NETWORK PERFORMANCE:\n"
            display_text += f"Received Packets: {row_data.get('Received_Packets', 'N/A')}\n"
            display_text += f"Packet TX Rate: {row_data.get('Packet_TX_Rate', 'N/A')} Hz\n"
            display_text += f"Packet Error Ratio: {row_data.get('Packet_Error_Ratio', 'N/A')}\n"
            display_text += f"SubFrame Number: {row_data.get('SubFrame_NUMBER', 'N/A')}\n"
            display_text += f"SubFrame Length: {row_data.get('SubFrame_LENGHT', 'N/A')}\n\n"
            
            # Vehicle telemetry
            display_text += "VEHICLE TELEMETRY:\n"
            display_text += f"Source Altitude: {row_data.get('Source_Altitude', 'N/A')} m\n"
            display_text += f"Source Speed: {row_data.get('Source_Speed', 'N/A')} m/s\n"
            display_text += f"Source COG: {row_data.get('Source_COG', 'N/A')}°\n"
            display_text += f"Destination Altitude: {row_data.get('Destination_Altitude', 'N/A')} m\n"
            display_text += f"Destination Speed: {row_data.get('Destination_Speed', 'N/A')} m/s\n"
            display_text += f"Destination COG: {row_data.get('Destination_COG', 'N/A')}°\n\n"
            
            # Weather and traffic
            display_text += "ENVIRONMENTAL DATA:\n"
            display_text += f"Wind Speed: {row_data.get('Wind_Speed', 'N/A')} m/s\n"
            display_text += f"Traffic Jam Factor: {row_data.get('Traffic_Jam_Factor', 'N/A')}\n"
            display_text += f"Traffic Street: {row_data.get('Traffic_Street_Name', 'N/A')}\n"
            display_text += f"Traffic Distance: {row_data.get('Traffic_Distance', 'N/A')} m\n"
        else:
            display_text += "No data available for this row.\n"
        
        # Insert the text
        self.csv_text.insert(1.0, display_text)
            
    def zoom_to_source(self):
        """Zoom extremely close to source vehicle"""
        try:
            if self.simulator.vehicle_pair and self.simulator.vehicle_pair['source_id'] in traci.vehicle.getIDList():
                traci.gui.trackVehicle("View #0", self.simulator.vehicle_pair['source_id'])
                traci.gui.setZoom("View #0", 2000)  # Very close zoom (higher value = closer)
                self.status_label.config(text="Zoomed extremely close to source vehicle")
            else:
                messagebox.showwarning("Warning", "Source vehicle not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to zoom to source: {e}")
            
    def zoom_to_destination(self):
        """Zoom extremely close to destination vehicle"""
        try:
            if self.simulator.vehicle_pair and self.simulator.vehicle_pair['dest_id'] in traci.vehicle.getIDList():
                traci.gui.trackVehicle("View #0", self.simulator.vehicle_pair['dest_id'])
                traci.gui.setZoom("View #0", 2000)  # Very close zoom (higher value = closer)
                self.status_label.config(text="Zoomed extremely close to destination vehicle")
            else:
                messagebox.showwarning("Warning", "Destination vehicle not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to zoom to destination: {e}")
            
    def zoom_to_both(self):
        """Zoom extremely close to both vehicles with V2V link visible"""
        try:
            if (self.simulator.vehicle_pair and 
                self.simulator.vehicle_pair['source_id'] in traci.vehicle.getIDList() and
                self.simulator.vehicle_pair['dest_id'] in traci.vehicle.getIDList()):
                
                # Get positions of both vehicles
                pos1 = traci.vehicle.getPosition(self.simulator.vehicle_pair['source_id'])
                pos2 = traci.vehicle.getPosition(self.simulator.vehicle_pair['dest_id'])
                
                # Calculate center point
                center_x = (pos1[0] + pos2[0]) / 2
                center_y = (pos1[1] + pos2[1]) / 2
                
                # Calculate zoom level based on distance - very close
                distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                zoom = max(1000, min(3000, 2000 - distance * 2))  # Very close zoom (higher value = closer)
                
                # Set camera view
                traci.gui.setOffset("View #0", center_x, center_y)
                traci.gui.setZoom("View #0", zoom)
                
                self.status_label.config(text=f"Zoomed extremely close to both vehicles (distance: {distance:.1f}m)")
            else:
                messagebox.showwarning("Warning", "V2V vehicles not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to zoom to both vehicles: {e}")
            
    def toggle_pause(self):
        """Toggle simulation pause"""
        if hasattr(self.simulator, 'paused'):
            self.simulator.paused = not self.simulator.paused
            if self.simulator.paused:
                self.pause_btn.config(text="Resume Simulation")
                self.status_label.config(text="Simulation paused")
            else:
                self.pause_btn.config(text="Pause Simulation")
                self.status_label.config(text="Simulation running")
        else:
            messagebox.showinfo("Info", "Simulation not running")
            
    def single_step(self):
        """Execute single simulation step"""
        if hasattr(self.simulator, 'single_step_mode'):
            self.simulator.single_step_mode = True
            self.status_label.config(text="Single step executed")
        else:
            messagebox.showinfo("Info", "Simulation not running")
            
    def toggle_follow(self):
        """Toggle vehicle following mode"""
        if hasattr(self.simulator, 'follow_mode'):
            self.simulator.follow_mode = not self.simulator.follow_mode
            if self.simulator.follow_mode:
                self.follow_btn.config(text="Stop Following")
                self.status_label.config(text="Following vehicles")
            else:
                self.follow_btn.config(text="Follow Vehicles")
                self.status_label.config(text="Following stopped")
        else:
            messagebox.showinfo("Info", "Simulation not running")
            
    def toggle_rotation(self):
        """Toggle camera rotation mode"""
        if hasattr(self.simulator, 'rotation_mode'):
            self.simulator.rotation_mode = not self.simulator.rotation_mode
            if self.simulator.rotation_mode:
                self.rotate_btn.config(text="Stop Rotation")
                self.status_label.config(text="Camera rotating")
            else:
                self.rotate_btn.config(text="Rotate Camera")
                self.status_label.config(text="Rotation stopped")
        else:
            messagebox.showinfo("Info", "Simulation not running")
            
    def next_csv_row(self):
        """Move to next CSV row"""
        if hasattr(self.simulator, 'next_row_mode'):
            self.simulator.next_row_mode = True
            self.status_label.config(text="Moving to next CSV row")
        else:
            messagebox.showinfo("Info", "Simulation not running")
            
    def update_status(self, step, distance, communication_active, v2v_link_status, simulated_distance=None, actual_distance=None, accuracy=None):
        """Update status information"""
        self.status_label.config(text=f"Step: {step}")
        self.distance_label.config(text=f"Distance: {distance:.1f}m")
        self.comm_label.config(text=f"Communication: {'Active' if communication_active else 'Inactive'}")
        self.v2v_link_label.config(text=f"V2V Link: {v2v_link_status}")
        
        # Update distance comparison
        if simulated_distance is not None:
            self.simulated_distance_label.config(text=f"Simulated Distance: {simulated_distance:.1f}m")
        if actual_distance is not None:
            self.actual_distance_label.config(text=f"Actual Distance: {actual_distance:.1f}m")
        if accuracy is not None:
            self.accuracy_label.config(text=f"Accuracy: {accuracy:.1f}%")
        
    def setup_control_callbacks(self):
        """Setup control callbacks for the simulator"""
        pass
        
    def run(self):
        """Run the GUI"""
        try:
            self.root.mainloop()
        except RuntimeError as e:
            logger.warning(f"GUI threading error: {e}")
            
    def start_mainloop(self):
        """Start the GUI mainloop in a separate thread"""
        try:
            gui_thread = threading.Thread(target=self.run, daemon=True)
            gui_thread.start()
            time.sleep(1)  # Give GUI time to initialize
            logger.info("Control panel GUI started")
        except Exception as e:
            logger.warning(f"Failed to start GUI: {e}")


class FocusedV2VSimulator:
    """Enhanced V2V Communication Simulator with CSV integration and advanced features"""
    
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.vehicle_pair = None
        self.results = []
        self.communication_line = None
        self.paused = False
        self.single_step_mode = False
        self.follow_mode = False
        self.rotation_mode = False
        self.next_row_mode = False
        self.control_panel = None
        self.simulation_started = False
        
        # CSV data management
        self.csv_data = None
        self.current_row_index = 0
        self.max_rows = 50
        self.rotation_angle = 0
        
        # Distance tracking for comparison
        self.initial_positions = {}
        
        # Initialize data
        self._load_data()
        
        # Initialize distance tracking
        self.simulated_distances = {}
        self.actual_distances = {}
        
        # V2V link simulation
        self.v2v_link_active = False
        self.link_quality = 0.0
        
        # Create control panel immediately (GUI will be started later)
        self.control_panel = V2VControlPanel(self)
        
        # Color changing for vehicle identification
        self.color_change_step = 0
        
        # Load data
        self._load_data()
        
    def _load_data(self):
        """Load CSV data for multiple V2V scenarios with both source and destination coordinates"""
        logger.info(f"Loading data from {self.csv_file}...")
        
        try:
            # Load first 2000 rows for processing
            df = pd.read_csv(self.csv_file, nrows=2000)
            
            # Filter for valid coordinates
            df = df.dropna(subset=['lat', 'lon'])
            
            # Find rows with both source and destination coordinates
            # Look for rows where we have different Source and Destination values
            # and both have valid GPS coordinates
            valid_rows = df[
                (df['Source'] != df['Destination']) & 
                df['Latitude_destination'].notna() & 
                df['Longitude_destination'].notna()
            ].copy()
            
            if not valid_rows.empty:
                # Group by Source-Destination pairs and take the first occurrence of each
                pairs = valid_rows.groupby(['Source', 'Destination']).first().reset_index()
                
                # Select up to max_rows valid pairs
                selected_pairs = pairs.head(self.max_rows)
                self.csv_data = selected_pairs
                
                # Create first vehicle pair
                self._create_vehicle_pair_from_row(0)
                
                logger.info(f"Loaded {len(selected_pairs)} V2V scenarios from CSV with both source and destination GPS coordinates")
            else:
                logger.error("No valid V2V pairs found with both source and destination coordinates")
                
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            
    def _create_vehicle_pair_from_row(self, row_index):
        """Create vehicle pair from CSV row with direct GPS mapping"""
        if self.csv_data is None or row_index >= len(self.csv_data):
            return False
            
        row = self.csv_data.iloc[row_index]
        
        # Use actual GPS coordinates from CSV for both source and destination
        src_lat, src_lon = row['lat'], row['lon']
        dst_lat, dst_lon = row['Latitude_destination'], row['Longitude_destination']
        
        self.vehicle_pair = {
            'source_id': f"src_{row['Source']}_{row_index}",
            'dest_id': f"dst_{row['Destination']}_{row_index}",
            'src_coords': (src_lat, src_lon),
            'dst_coords': (dst_lat, dst_lon),
            'snr': row.get('SNR', 15.0),
            'rsrp': row.get('RSRP', -70.0),
            'scenario': row.get('Scenario', 'S1'),
            'row_data': row.to_dict(),
            'row_index': row_index
        }
        
        logger.info(f"Created V2V pair {row_index}: {self.vehicle_pair['source_id']} <-> {self.vehicle_pair['dest_id']}")
        logger.info(f"Source coords: ({src_lat:.6f}, {src_lon:.6f})")
        logger.info(f"Destination coords: ({dst_lat:.6f}, {dst_lon:.6f})")
        return True
            
    def _get_simple_edges(self):
        """Get two simple, connected edges for vehicle placement"""
        try:
            edges = traci.edge.getIDList()
            
            # Filter for simple edges (avoid complex edge names)
            simple_edges = []
            for edge in edges:
                if (not edge.startswith('-') and 
                    not edge.startswith(':') and 
                    not 'cluster' in edge and
                    not '#' in edge and
                    len(edge) < 20):  # Simple edge names
                    simple_edges.append(edge)
                    
            if len(simple_edges) < 2:
                # Fallback to any valid edges
                simple_edges = [e for e in edges if not e.startswith('-') and not e.startswith(':')]
                
            logger.info(f"Found {len(simple_edges)} simple edges")
            
            if len(simple_edges) >= 2:
                # Try to find connected edges
                for i in range(min(5, len(simple_edges))):
                    for j in range(min(5, len(simple_edges))):
                        if i != j:
                            src_edge = simple_edges[i]
                            dst_edge = simple_edges[j]
                            
                            try:
                                # Check if edges are connected
                                route = traci.simulation.findRoute(src_edge, dst_edge)
                                if len(route.edges) > 0:
                                    logger.info(f"Found connected edges: {src_edge} -> {dst_edge}")
                                    return src_edge, dst_edge
                            except:
                                continue
                                
                # Fallback: use first two edges
                logger.warning("No connected edges found, using first two simple edges")
                return simple_edges[0], simple_edges[1]
            else:
                logger.error("Not enough simple edges found")
                return None, None
                
        except Exception as e:
            logger.error(f"Error finding edges: {e}")
            return None, None
            
    def _gps_to_sumo_coordinates(self, lat, lon):
        """Convert GPS coordinates to SUMO network coordinates"""
        try:
            # Use TraCI's convertGeo function for accurate GPS to SUMO conversion
            x, y = traci.simulation.convertGeo(lon, lat)
            return x, y
        except Exception as e:
            logger.error(f"Error converting GPS coordinates: {e}")
            return None, None
            
    def _find_closest_edge_to_gps(self, lat, lon):
        """Find the closest SUMO edge to GPS coordinates using improved algorithm"""
        try:
            x, y = self._gps_to_sumo_coordinates(lat, lon)
            if x is None or y is None:
                logger.error(f"Failed to convert GPS coordinates ({lat}, {lon}) to SUMO coordinates")
                return None
                
            min_distance = float('inf')
            closest_edge = None
            
            # Method 1: Use edge junctions (more reliable)
            for edge_id in traci.edge.getIDList():
                # Skip internal edges
                if edge_id.startswith(':') or edge_id.startswith('-') or 'cluster' in edge_id:
                    continue
                    
                try:
                    # Get edge from/to junctions
                    from_junction = traci.edge.getFromJunction(edge_id)
                    to_junction = traci.edge.getToJunction(edge_id)
                    
                    from_pos = traci.junction.getPosition(from_junction)
                    to_pos = traci.junction.getPosition(to_junction)
                    
                    # Calculate distance to edge center
                    edge_center_x = (from_pos[0] + to_pos[0]) / 2
                    edge_center_y = (from_pos[1] + to_pos[1]) / 2
                    
                    distance = np.sqrt((x - edge_center_x)**2 + (y - edge_center_y)**2)
                    
                    if distance < min_distance and distance < 2000:  # Reasonable limit
                        min_distance = distance
                        closest_edge = edge_id
                        
                except Exception:
                    continue
                        
            if closest_edge:
                logger.info(f"Found closest edge: {closest_edge} at distance {min_distance:.2f}m (junction method)")
                return closest_edge
                
            # Method 2: Try any edge without constraints if method 1 fails
            logger.info("Junction method failed, trying broad search...")
            min_distance = float('inf')
            
            for edge_id in traci.edge.getIDList():
                try:
                    from_junction = traci.edge.getFromJunction(edge_id)
                    from_pos = traci.junction.getPosition(from_junction)
                    
                    distance = np.sqrt((x - from_pos[0])**2 + (y - from_pos[1])**2)
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_edge = edge_id
                        
                except Exception:
                    continue
                    
            if closest_edge:
                logger.info(f"Found edge: {closest_edge} at distance {min_distance:.2f}m (fallback)")
                
            return closest_edge
            
        except Exception as e:
            logger.error(f"Error finding closest edge: {e}")
            return None
            
    def _get_gps_based_edges(self, src_lat, src_lon, dst_lat, dst_lon):
        """Get edges based on GPS coordinates for precise vehicle placement"""
        try:
            # Find closest edges to GPS coordinates
            src_edge = self._find_closest_edge_to_gps(src_lat, src_lon)
            dst_edge = self._find_closest_edge_to_gps(dst_lat, dst_lon)
            
            if src_edge and dst_edge:
                logger.info(f"GPS-based edge selection: {src_edge} (source) → {dst_edge} (destination)")
                
                # If both vehicles map to same edge, find a different nearby edge for destination
                if src_edge == dst_edge:
                    logger.warning("Both vehicles mapped to same edge, finding alternative")
                    dst_edge = self._find_different_nearby_edge(src_edge, dst_lat, dst_lon)
                    logger.info(f"Updated selection: {src_edge} → {dst_edge}")
                
                return src_edge, dst_edge
            else:
                logger.error("Could not find edges for GPS coordinates")
                return None, None
                
        except Exception as e:
            logger.error(f"Error getting GPS-based edges: {e}")
            return None, None
            
    def _find_different_nearby_edge(self, avoid_edge, dst_lat, dst_lon):
        """Find a different edge near the destination GPS coordinates"""
        try:
            dst_x, dst_y = self._gps_to_sumo_coordinates(dst_lat, dst_lon)
            if dst_x is None or dst_y is None:
                return avoid_edge
                
            min_distance = float('inf')
            closest_edge = None
            
            # Find the closest edge that's different from avoid_edge
            for edge_id in traci.edge.getIDList():
                if edge_id == avoid_edge or edge_id.startswith(':') or edge_id.startswith('-') or 'cluster' in edge_id:
                    continue
                    
                try:
                    from_junction = traci.edge.getFromJunction(edge_id)
                    from_pos = traci.junction.getPosition(from_junction)
                    
                    distance = np.sqrt((dst_x - from_pos[0])**2 + (dst_y - from_pos[1])**2)
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_edge = edge_id
                        
                except Exception:
                    continue
                    
            if closest_edge:
                logger.info(f"Found alternative edge: {closest_edge} at {min_distance:.2f}m")
            else:
                logger.warning("No alternative edge found, keeping original")
                closest_edge = avoid_edge
                
            return closest_edge
            
        except Exception as e:
            logger.error(f"Error finding different edge: {e}")
            return avoid_edge
            
    def start_simulation(self):
        """Start the simulation"""
        self.simulation_started = True
        self.paused = False
        
    def run_simulation(self):
        """Run the focused V2V simulation with GUI control panel"""
        logger.info("Starting focused V2V simulation with GUI control...")
        
        if not self.vehicle_pair:
            logger.error("No vehicle pair available")
            return
            
        # Create control panel (GUI will be handled in main thread to avoid Tkinter threading issues)
        self.control_panel = V2VControlPanel(self)
        
        # Initialize GUI components but don't start mainloop yet
        self.control_panel.setup_control_callbacks()
        
        # SUMO command with minimal traffic - only our 2 vehicles
        sumo_cmd = [
            "sumo-gui",
            "-c", "sumo-config/osm.sumocfg",
            "--tripinfo-output", "focused_v2v_trips.xml",
            "--fcd-output", "focused_v2v_fcd.xml",
            "--no-step-log",
            "--start",  # Start simulation immediately
            "--step-length", "0.5",  # Slower simulation steps for better visualization
            "--ignore-route-errors",  # Ignore route errors
            "--no-warnings"  # Suppress warnings
        ]
        
        try:
            # Start SUMO
            traci.start(sumo_cmd)
            logger.info("SUMO started successfully")
            
            # Wait a moment for SUMO to initialize
            time.sleep(2)
            
            try:
                # Get GPS-based edges for precise vehicle placement
                src_lat, src_lon = self.vehicle_pair['src_coords']
                dst_lat, dst_lon = self.vehicle_pair['dst_coords']
                
                src_edge, dst_edge = self._get_gps_based_edges(src_lat, src_lon, dst_lat, dst_lon)
                
                if not src_edge or not dst_edge:
                    logger.error("Could not find suitable edges for GPS coordinates")
                    logger.info("Falling back to simple edge selection")
                    src_edge, dst_edge = self._get_simple_edges()
                    
                # Place vehicles using GPS positioning with fallback
                self._place_vehicles_simple_with_fallback(src_edge, dst_edge)
                
                # Verify vehicles are actually placed
                active_vehicles = traci.vehicle.getIDList()
                if (self.vehicle_pair['source_id'] not in active_vehicles or 
                    self.vehicle_pair['dest_id'] not in active_vehicles):
                    logger.error("Vehicle placement verification failed")
                    return
                    
            except Exception as placement_error:
                logger.error(f"Vehicle placement error: {placement_error}")
                # Final fallback - restart SUMO with simple edges
                logger.info("Restarting SUMO with simple edge placement")
                traci.close()
                time.sleep(1)
                traci.start(sumo_cmd)
                time.sleep(2)
                src_edge, dst_edge = self._get_simple_edges()
                if src_edge and dst_edge:
                    self._place_vehicles_simple(src_edge, dst_edge)
                else:
                    logger.error("Complete vehicle placement failure")
                return
            
            # Start the control panel GUI
            self.control_panel.start_mainloop()
                
            # Wait for vehicles to be placed
            time.sleep(2)
            
            # Verify vehicles are actually running
            active_vehicles = traci.vehicle.getIDList()
            logger.info(f"Active vehicles after placement: {active_vehicles}")
            
            # Update control panel with vehicle info
            if self.control_panel:
                self.control_panel.update_vehicle_info(self.vehicle_pair)
                self.control_panel.update_csv_display(self.vehicle_pair['row_data'], self.current_row_index)
            
            # Initial zoom to vehicles
            self._zoom_to_vehicles()
            
            logger.info("Starting slowed simulation for monitoring...")
            
            # Run simulation
            step = 0
            max_steps = 1000  # Increased for better testing
            
            while step < max_steps:
                try:
                    # Check if SUMO is still running
                    remaining_vehicles = traci.simulation.getMinExpectedNumber()
                except Exception as conn_error:
                    logger.error(f"SUMO connection lost: {conn_error}")
                    break
                
                if remaining_vehicles <= 0:
                    logger.info("Simulation naturally completed - no more vehicles")
                    break
                    
                # Wait for simulation to start
                if not self.simulation_started:
                    if self.control_panel:
                        self.control_panel.root.update()
                    time.sleep(0.5)  # Slower for GUI responsiveness
                    continue
                    
                # Handle pause
                while self.paused and not self.single_step_mode:
                    time.sleep(0.1)
                    if self.control_panel:
                        self.control_panel.root.update()
                    
                # Handle single step
                if self.single_step_mode:
                    self.single_step_mode = False
                
                # Handle next row request
                if self.next_row_mode:
                    self._move_to_next_row()
                    self.next_row_mode = False
                
                traci.simulationStep()
                
                # Slow down simulation for monitoring (1 second per step)
                time.sleep(1.0)
                
                # Check V2V communication every step for real-time monitoring
                self._check_v2v_communication(step)
                    
                # Update communication highlighting every step
                self._update_communication_line()
                # Update radius circles to follow vehicles
                if self.vehicle_pair:
                    try:
                        src_pos = traci.vehicle.getPosition(self.vehicle_pair['source_id'])
                        dst_pos = traci.vehicle.getPosition(self.vehicle_pair['dest_id'])
                        self._create_vehicle_radius(self.vehicle_pair['source_id'], src_pos)
                        self._create_vehicle_radius(self.vehicle_pair['dest_id'], dst_pos)
                    except:
                        pass
                # Update distance comparison display
                self._update_distance_comparison()
                    
                # Update camera following and rotation
                self._update_camera_view()
                    
                # Update vehicle colors for identification
                self._update_vehicle_colors(step)
                    
                # Update control panel status every step for real-time monitoring
                distance = 0
                communication_active = False
                v2v_link_status = "Inactive"
                simulated_distance = 0
                actual_distance = 0
                accuracy = 0
                
                if (self.vehicle_pair and 
                    self.vehicle_pair['source_id'] in traci.vehicle.getIDList() and
                    self.vehicle_pair['dest_id'] in traci.vehicle.getIDList()):
                    
                    src_pos = traci.vehicle.getPosition(self.vehicle_pair['source_id'])
                    dst_pos = traci.vehicle.getPosition(self.vehicle_pair['dest_id'])
                    distance = np.sqrt((src_pos[0] - dst_pos[0])**2 + (src_pos[1] - dst_pos[1])**2)
                    communication_active = distance <= 500
                    v2v_link_status = "Active" if self.v2v_link_active else "Inactive"
                    
                    # Calculate distance comparison
                    simulated_distance = distance
                    actual_distance = self.actual_distances.get(self.vehicle_pair['source_id'], 0.0)
                    if actual_distance > 0:
                        accuracy = (1 - abs(simulated_distance - actual_distance) / actual_distance) * 100
                        accuracy = max(0, min(100, accuracy))
                
                if self.control_panel:
                    self.control_panel.update_status(step, distance, communication_active, v2v_link_status, 
                                                   simulated_distance, actual_distance, accuracy)
                    
                step += 1
                
                if step % 50 == 0:
                    active = len(traci.vehicle.getIDList())
                    events = len(self.results)
                    logger.info(f"Step {step}: {active} vehicles, {events} V2V events")
                    
                # Update GUI every step for real-time monitoring
                if self.control_panel:
                    try:
                        self.control_panel.root.update()
                    except Exception as gui_error:
                        logger.warning(f"GUI update error: {gui_error}")
                    
            logger.info(f"Simulation completed after {step} steps")
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                # Clear highlights before closing
                self._clear_highlights()
                traci.close()
            except:
                pass
            
    def _place_vehicles_with_gps(self, src_edge: str, dst_edge: str, src_lat: float, src_lon: float, dst_lat: float, dst_lon: float):
        """Place vehicles at exact GPS coordinates using moveToXY for Digital Twin precision"""
        logger.info(f"Placing vehicles at GPS coordinates for Digital Twin accuracy")
        
        try:
            # Convert GPS coordinates to SUMO coordinates
            src_x, src_y = self._gps_to_sumo_coordinates(src_lat, src_lon)
            dst_x, dst_y = self._gps_to_sumo_coordinates(dst_lat, dst_lon)
            
            if src_x is None or src_y is None or dst_x is None or dst_y is None:
                logger.error("Failed to convert GPS coordinates to SUMO coordinates")
                return
            
            # Add source vehicle
            traci.vehicle.add(
                vehID=self.vehicle_pair['source_id'],
                typeID="DEFAULT_VEHTYPE",
                routeID="",
                depart=0.0,
                departLane="best"
            )
            
            # Add destination vehicle
            traci.vehicle.add(
                vehID=self.vehicle_pair['dest_id'],
                typeID="DEFAULT_VEHTYPE",
                routeID="",
                depart=0.1,
                departLane="best"
            )
            
            # Position vehicles at exact GPS coordinates using moveToXY
            # This ensures Digital Twin-level precision
            traci.vehicle.moveToXY(
                vehID=self.vehicle_pair['source_id'],
                edgeID=src_edge,
                laneIndex=-1,  # Let SUMO find the best lane
                x=src_x,
                y=src_y,
                angle=traci.constants.INVALID_DOUBLE_VALUE,  # Let SUMO determine angle
                keepRoute=2  # Keep exact position mapping
            )
            
            traci.vehicle.moveToXY(
                vehID=self.vehicle_pair['dest_id'],
                edgeID=dst_edge,
                laneIndex=-1,  # Let SUMO find the best lane
                x=dst_x,
                y=dst_y,
                angle=traci.constants.INVALID_DOUBLE_VALUE,  # Let SUMO determine angle
                keepRoute=2  # Keep exact position mapping
            )
            
            # Set routes for both vehicles (for movement simulation)
            traci.vehicle.changeTarget(self.vehicle_pair['source_id'], dst_edge)
            traci.vehicle.changeTarget(self.vehicle_pair['dest_id'], src_edge)
            
            self.vehicle_pair['src_edge'] = src_edge
            self.vehicle_pair['dst_edge'] = dst_edge
            self.vehicle_pair['placed'] = True
            
            # Set vehicles to different colors for identification
            traci.vehicle.setColor(self.vehicle_pair['source_id'], (255, 0, 0, 255))    # Red for source
            traci.vehicle.setColor(self.vehicle_pair['dest_id'], (0, 0, 255, 255))     # Blue for destination
            
            # Add labels to identify our vehicles
            traci.vehicle.setParameter(self.vehicle_pair['source_id'], "v2v_type", "source")
            traci.vehicle.setParameter(self.vehicle_pair['dest_id'], "v2v_type", "destination")
            
            # Store initial positions for distance tracking
            self.initial_positions[self.vehicle_pair['source_id']] = traci.vehicle.getPosition(self.vehicle_pair['source_id'])
            self.initial_positions[self.vehicle_pair['dest_id']] = traci.vehicle.getPosition(self.vehicle_pair['dest_id'])
            
            # Calculate actual distance from CSV coordinates
            actual_distance = self._calculate_gps_distance(src_lat, src_lon, dst_lat, dst_lon)
            self.actual_distances[self.vehicle_pair['source_id']] = actual_distance
            self.actual_distances[self.vehicle_pair['dest_id']] = actual_distance
            
            # Log GPS positioning details for Digital Twin validation
            logger.info(f"Digital Twin GPS Positioning:")
            logger.info(f"  Source: GPS({src_lat:.6f}, {src_lon:.6f}) -> SUMO({src_x:.2f}, {src_y:.2f})")
            logger.info(f"  Destination: GPS({dst_lat:.6f}, {dst_lon:.6f}) -> SUMO({dst_x:.2f}, {dst_y:.2f})")
            logger.info(f"  Actual Distance: {actual_distance:.2f}m")
            logger.info(f"  Vehicles placed: {self.vehicle_pair['source_id']} (red) and {self.vehicle_pair['dest_id']} (blue)")
            
        except Exception as e:
            logger.error(f"Failed to place vehicles with GPS positioning: {e}")
            
    def _place_vehicles_simple(self, src_edge: str, dst_edge: str):
        """Place vehicles using simple edge placement (fallback when GPS positioning fails)"""
        logger.info(f"Placing vehicles on edges: {src_edge} -> {dst_edge}")
        
        try:
            # Add source vehicle
            traci.vehicle.add(
                vehID=self.vehicle_pair['source_id'],
                typeID="DEFAULT_VEHTYPE",
                routeID="",
                depart=0.0,
                departLane="best"
            )
            
            # Add destination vehicle
            traci.vehicle.add(
                vehID=self.vehicle_pair['dest_id'],
                typeID="DEFAULT_VEHTYPE",
                routeID="",
                depart=0.1,
                departLane="best"
            )
            
            # Set routes for both vehicles
            traci.vehicle.changeTarget(self.vehicle_pair['source_id'], dst_edge)
            traci.vehicle.changeTarget(self.vehicle_pair['dest_id'], src_edge)
            
            self.vehicle_pair['src_edge'] = src_edge
            self.vehicle_pair['dst_edge'] = dst_edge
            self.vehicle_pair['placed'] = True
            
            # Set vehicles to different colors for identification
            traci.vehicle.setColor(self.vehicle_pair['source_id'], (255, 0, 0, 255))    # Red for source
            traci.vehicle.setColor(self.vehicle_pair['dest_id'], (0, 0, 255, 255))     # Blue for destination
            
            # Add labels to identify our vehicles
            traci.vehicle.setParameter(self.vehicle_pair['source_id'], "v2v_type", "source")
            traci.vehicle.setParameter(self.vehicle_pair['dest_id'], "v2v_type", "destination")
            
            # Store initial positions for distance tracking
            self.initial_positions[self.vehicle_pair['source_id']] = traci.vehicle.getPosition(self.vehicle_pair['source_id'])
            self.initial_positions[self.vehicle_pair['dest_id']] = traci.vehicle.getPosition(self.vehicle_pair['dest_id'])
            
            # Calculate actual distance from CSV coordinates
            src_lat, src_lon = self.vehicle_pair['src_coords']
            dst_lat, dst_lon = self.vehicle_pair['dst_coords']
            actual_distance = self._calculate_gps_distance(src_lat, src_lon, dst_lat, dst_lon)
            self.actual_distances[self.vehicle_pair['source_id']] = actual_distance
            self.actual_distances[self.vehicle_pair['dest_id']] = actual_distance
            
            logger.info(f"Successfully placed V2V vehicles (simple placement): {self.vehicle_pair['source_id']} and {self.vehicle_pair['dest_id']}")
            
        except Exception as e:
            logger.error(f"Failed to place vehicles (simple placement): {e}")
            
    def _place_vehicles_simple_with_fallback(self, src_edge, dst_edge):
        """Fallback method for GPS-based placement"""
        try:
            # If both edges are the same or one is problematic, use simple edges
            if src_edge == dst_edge or src_edge.startswith(':') or dst_edge.startswith(':'):
                logger.warning("Edge selection problems detected, using simple edge placement")
                src_edge, dst_edge = self._get_simple_edges()
                if not src_edge or not dst_edge:
                    logger.error("Could not find suitable alternative edges")
                    return
                self._place_vehicles_simple(src_edge, dst_edge)
                return
            
            src_lat, src_lon = self.vehicle_pair['src_coords']
            dst_lat, dst_lon = self.vehicle_pair['dst_coords']
            
            # Try GPS-based placement first
            self._place_vehicles_with_gps(src_edge, dst_edge, src_lat, src_lon, dst_lat, dst_lon)
            
            # Check if vehicles are actually placed and routes are valid
            active_vehicles = traci.vehicle.getIDList()
            if (self.vehicle_pair['source_id'] in active_vehicles and 
                self.vehicle_pair['dest_id'] in active_vehicles):
                
                # Verify routes are valid
                try:
                    src_route = traci.vehicle.getRoute(self.vehicle_pair['source_id'])
                    dst_route = traci.vehicle.getRoute(self.vehicle_pair['dest_id'])
                    if len(src_route) > 0 and len(dst_route) > 0:
                        logger.info("GPS-based vehicle placement successful")
                        return
                    else:
                        logger.warning("Vehicle routes are invalid")
                except Exception as route_error:
                    logger.warning(f"Route verification failed: {route_error}")
                
                # Fallback to simple placement
                logger.warning("GPS-based placement verification failed, using simple placement")
                self._place_vehicles_simple(src_edge, dst_edge)
            else:
                # Fallback to simple placement
                logger.warning("GPS-based placement failed, using simple placement")
                self._place_vehicles_simple(src_edge, dst_edge)
                
        except Exception as e:
            logger.error(f"Error in vehicle placement: {e}")
            # Final fallback
            try:
                src_edge, dst_edge = self._get_simple_edges()
                self._place_vehicles_simple(src_edge, dst_edge)
            except:
                logger.error("All vehicle placement methods failed")
            
    def _zoom_to_vehicles(self):
        """Zoom camera to focus on the two vehicles"""
        try:
            active_vehicles = traci.vehicle.getIDList()
            if len(active_vehicles) >= 2:
                # Get positions of the two vehicles
                pos1 = traci.vehicle.getPosition(active_vehicles[0])
                pos2 = traci.vehicle.getPosition(active_vehicles[1])
                
                # Calculate center point
                center_x = (pos1[0] + pos2[0]) / 2
                center_y = (pos1[1] + pos2[1]) / 2
                
                # Calculate zoom level based on distance
                distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                zoom = max(300, min(1000, distance * 2))  # Adaptive zoom
                
                # Set camera view
                traci.gui.setOffset("View #0", center_x, center_y)
                traci.gui.setZoom("View #0", zoom)
                
                logger.info(f"Zoomed to vehicles at center ({center_x:.1f}, {center_y:.1f}) with zoom {zoom:.1f}")
                
        except Exception as e:
            logger.warning(f"Error zooming to vehicles: {e}")
            
    def _update_communication_line(self):
        """Update the communication line between vehicles using path highlighting and vehicle indicators"""
        try:
            # Check if our V2V vehicles exist
            if (self.vehicle_pair['source_id'] not in traci.vehicle.getIDList() or 
                self.vehicle_pair['dest_id'] not in traci.vehicle.getIDList()):
                return
                
            # Get positions of our V2V vehicles
            src_pos = traci.vehicle.getPosition(self.vehicle_pair['source_id'])
            dst_pos = traci.vehicle.getPosition(self.vehicle_pair['dest_id'])
            
            # Calculate distance
            distance = np.sqrt((src_pos[0] - dst_pos[0])**2 + (src_pos[1] - dst_pos[1])**2)
            
            # Highlight our V2V vehicles with bright colors
            if distance <= 500:  # Within communication range
                # Green highlight for V2V communication
                traci.vehicle.setColor(self.vehicle_pair['source_id'], (0, 255, 0, 255))  # Bright Green
                traci.vehicle.setColor(self.vehicle_pair['dest_id'], (0, 255, 0, 255))  # Bright Green
                
            else:
                # Red highlight for out of range
                traci.vehicle.setColor(self.vehicle_pair['source_id'], (255, 0, 0, 255))  # Bright Red
                traci.vehicle.setColor(self.vehicle_pair['dest_id'], (255, 0, 0, 255))  # Bright Red
            
            # Highlight the path between vehicles
            self._highlight_vehicle_path()
                    
        except Exception as e:
            logger.warning(f"Error updating communication highlighting: {e}")
            
    def _highlight_vehicle_path(self):
        """Highlight the path between the two V2V vehicles with thick line visualization and radius"""
        try:
            # Get current edges of both vehicles
            src_edge = traci.vehicle.getRoadID(self.vehicle_pair['source_id'])
            dst_edge = traci.vehicle.getRoadID(self.vehicle_pair['dest_id'])
            
            # Add path information as vehicle parameters for identification
            traci.vehicle.setParameter(self.vehicle_pair['source_id'], "current_edge", src_edge)
            traci.vehicle.setParameter(self.vehicle_pair['dest_id'], "current_edge", dst_edge)
            
            # Get vehicle positions for link visualization
            src_pos = traci.vehicle.getPosition(self.vehicle_pair['source_id'])
            dst_pos = traci.vehicle.getPosition(self.vehicle_pair['dest_id'])
            
            # Calculate distance
            distance = np.sqrt((src_pos[0] - dst_pos[0])**2 + (src_pos[1] - dst_pos[1])**2)
            
            # Create thick line visualization between vehicles
            self._create_v2v_link_line(src_pos, dst_pos, distance)
            
            # Create circular radius around both vehicles
            self._create_vehicle_radius(self.vehicle_pair['source_id'], src_pos, radius=30)
            self._create_vehicle_radius(self.vehicle_pair['dest_id'], dst_pos, radius=30)
            
            # Add communication status
            if distance <= 500:
                traci.vehicle.setParameter(self.vehicle_pair['source_id'], "v2v_status", "connected")
                traci.vehicle.setParameter(self.vehicle_pair['dest_id'], "v2v_status", "connected")
            else:
                traci.vehicle.setParameter(self.vehicle_pair['source_id'], "v2v_status", "disconnected")
                traci.vehicle.setParameter(self.vehicle_pair['dest_id'], "v2v_status", "disconnected")
                
        except Exception as e:
            logger.warning(f"Error highlighting vehicle path: {e}")
            
    def _create_v2v_link_line(self, src_pos, dst_pos, distance):
        """Create a thick line visualization between the two V2V vehicles"""
        try:
            # Remove existing link line if it exists
            try:
                if "v2v_link_line" in traci.polygon.getIDList():
                    traci.polygon.remove("v2v_link_line")
            except:
                pass
                
            # Calculate line properties
            x1, y1 = src_pos[0], src_pos[1]
            x2, y2 = dst_pos[0], dst_pos[1]
            
            # Determine line color based on distance and communication status
            if distance <= 100:
                color = (0, 255, 0, 255)  # Green for close range
                width = 15  # Much thicker line
            elif distance <= 300:
                color = (255, 255, 0, 255)  # Yellow for medium range
                width = 12
            elif distance <= 500:
                color = (255, 165, 0, 255)  # Orange for far range
                width = 8
            else:
                color = (255, 0, 0, 255)  # Red for out of range
                width = 5
                
            # Create a thick line using polygon
            # Calculate perpendicular offset for line thickness
            dx = x2 - x1
            dy = y2 - y1
            length = np.sqrt(dx*dx + dy*dy)
            
            if length > 0:
                # Normalize direction vector
                dx_norm = dx / length
                dy_norm = dy / length
                
                # Calculate perpendicular vector
                perp_x = -dy_norm
                perp_y = dx_norm
                
                # Calculate line thickness offset
                thickness = width / 2.0
                
                # Create rectangle points for thick line
                p1_x = x1 + perp_x * thickness
                p1_y = y1 + perp_y * thickness
                p2_x = x2 + perp_x * thickness
                p2_y = y2 + perp_y * thickness
                p3_x = x2 - perp_x * thickness
                p3_y = y2 - perp_y * thickness
                p4_x = x1 - perp_x * thickness
                p4_y = y1 - perp_y * thickness
                
                # Create polygon for thick line - use list format
                shape = [(p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y), (p4_x, p4_y)]
                
                traci.polygon.add(
                    "v2v_link_line",
                    shape,
                    color,
                    fill=True,
                    layer=1
                )
                
        except Exception as e:
            logger.warning(f"Error creating V2V link line: {e}")
            
    def _create_vehicle_radius(self, vehicle_id, position, radius=80):
        """Create filled circular radius around a vehicle"""
        try:
            # Remove existing radius if it exists
            try:
                if f"radius_{vehicle_id}" in traci.polygon.getIDList():
                    traci.polygon.remove(f"radius_{vehicle_id}")
            except:
                pass
                
            x, y = position[0], position[1]
            
            # Create circle using polygon (approximated with many points)
            points = []
            num_points = 32  # More points for smoother circle
            
            for i in range(num_points):
                angle = 2 * math.pi * i / num_points
                px = x + radius * math.cos(angle)
                py = y + radius * math.sin(angle)
                points.append((px, py))
                
            # Determine color based on vehicle type
            if "src_" in vehicle_id:
                color = (255, 0, 0, 80)  # Semi-transparent red for source
            else:
                color = (0, 0, 255, 80)  # Semi-transparent blue for destination
                
            # Create filled radius polygon
            traci.polygon.add(
                f"radius_{vehicle_id}",
                points,
                color,
                fill=True,  # Filled circle
                layer=0
            )
            
        except Exception as e:
            logger.warning(f"Error creating vehicle radius: {e}")
            
    def _calculate_gps_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two GPS coordinates in meters"""
        try:
            # Convert to radians
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            # Haversine formula
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Earth's radius in meters
            earth_radius = 6371000
            distance = earth_radius * c
            
            return distance
        except Exception as e:
            logger.warning(f"Error calculating GPS distance: {e}")
            return 0.0
            
    def _update_distance_comparison(self):
        """Update distance comparison display in SUMO GUI"""
        try:
            if not self.vehicle_pair:
                return
                
            # Remove existing distance comparison text
            try:
                if "distance_comparison" in traci.gui.getIDList("View #0"):
                    traci.gui.remove("View #0", "distance_comparison")
            except:
                pass
                
            # Calculate simulated distance between vehicles
            if (self.vehicle_pair['source_id'] in traci.vehicle.getIDList() and 
                self.vehicle_pair['dest_id'] in traci.vehicle.getIDList()):
                
                src_pos = traci.vehicle.getPosition(self.vehicle_pair['source_id'])
                dst_pos = traci.vehicle.getPosition(self.vehicle_pair['dest_id'])
                
                # Calculate simulated distance
                simulated_distance = np.sqrt((src_pos[0] - dst_pos[0])**2 + (src_pos[1] - dst_pos[1])**2)
                
                # Get actual distance
                actual_distance = self.actual_distances.get(self.vehicle_pair['source_id'], 0.0)
                
                # Calculate accuracy percentage
                if actual_distance > 0:
                    accuracy = (1 - abs(simulated_distance - actual_distance) / actual_distance) * 100
                    accuracy = max(0, min(100, accuracy))  # Clamp between 0-100%
                else:
                    accuracy = 0.0
                
                # Create comparison text
                comparison_text = (
                    f"Distance Comparison:\n"
                    f"Simulated: {simulated_distance:.1f}m\n"
                    f"Actual: {actual_distance:.1f}m\n"
                    f"Accuracy: {accuracy:.1f}%"
                )
                
                # Calculate position for text (above the vehicles)
                center_x = (src_pos[0] + dst_pos[0]) / 2
                center_y = (src_pos[1] + dst_pos[1]) / 2
                text_y = center_y + 100  # Position above vehicles
                
                # Add text to GUI using polygon instead of addText (not supported in this TraCI version)
                try:
                    # Create a text polygon as workaround
                    text_polygon_id = "distance_comparison_text"
                    
                    # Remove existing text polygon
                    if text_polygon_id in traci.polygon.getIDList():
                        traci.polygon.remove(text_polygon_id)
                    
                    # Create background rectangle for text
                    text_w, text_h = len(comparison_text.split('\n')[0]) * 8, len(comparison_text.split('\n')) * 15
                    bg_points = [
                        (center_x - text_w/2, text_y - text_h/2),
                        (center_x + text_w/2, text_y - text_h/2),
                        (center_x + text_w/2, text_y + text_h/2),
                        (center_x - text_w/2, text_y + text_h/2)
                    ]
                    
                    traci.polygon.add(
                        text_polygon_id,
                        bg_points,
                        (0, 0, 0, 150),  # Semi-transparent black background
                        fill=True,
                        layer=0
                    )
                    
                except Exception as e:
                    logger.warning(f"Error creating text display: {e}")
                
        except Exception as e:
            logger.warning(f"Error updating distance comparison: {e}")
            
    def _update_vehicle_colors(self, step):
        """Update vehicle colors dynamically for better identification"""
        try:
            if not self.vehicle_pair:
                return
                
            # Check if vehicles still exist before updating colors
            active_vehicles = traci.vehicle.getIDList()
            if self.vehicle_pair['source_id'] not in active_vehicles or self.vehicle_pair['dest_id'] not in active_vehicles:
                return
                
            # Change colors every 50 steps for visual effect
            if step % 50 == 0:
                self.color_change_step = (self.color_change_step + 1) % 4
                
                if self.color_change_step == 0:
                    # Red and Blue
                    traci.vehicle.setColor(self.vehicle_pair['source_id'], (255, 0, 0, 255))    # Red
                    traci.vehicle.setColor(self.vehicle_pair['dest_id'], (0, 0, 255, 255))     # Blue
                elif self.color_change_step == 1:
                    # Green and Yellow
                    traci.vehicle.setColor(self.vehicle_pair['source_id'], (0, 255, 0, 255))   # Green
                    traci.vehicle.setColor(self.vehicle_pair['dest_id'], (255, 255, 0, 255))   # Yellow
                elif self.color_change_step == 2:
                    # Magenta and Cyan
                    traci.vehicle.setColor(self.vehicle_pair['source_id'], (255, 0, 255, 255)) # Magenta
                    traci.vehicle.setColor(self.vehicle_pair['dest_id'], (0, 255, 255, 255))   # Cyan
                else:
                    # Orange and Purple
                    traci.vehicle.setColor(self.vehicle_pair['source_id'], (255, 165, 0, 255)) # Orange
                    traci.vehicle.setColor(self.vehicle_pair['dest_id'], (128, 0, 128, 255))   # Purple
                    
        except Exception as e:
            logger.warning(f"Error updating vehicle colors: {e}")
            
    def _move_to_next_row(self):
        """Move to next CSV row and create new vehicle pair"""
        if self.csv_data is None:
            return
            
        # Remove current vehicles
        try:
            if self.vehicle_pair:
                if self.vehicle_pair['source_id'] in traci.vehicle.getIDList():
                    traci.vehicle.remove(self.vehicle_pair['source_id'])
                if self.vehicle_pair['dest_id'] in traci.vehicle.getIDList():
                    traci.vehicle.remove(self.vehicle_pair['dest_id'])
        except:
            pass
            
        # Move to next row
        self.current_row_index = (self.current_row_index + 1) % len(self.csv_data)
        
        # Create new vehicle pair
        if self._create_vehicle_pair_from_row(self.current_row_index):
            # Get new edges and place vehicles
            src_edge, dst_edge = self._get_simple_edges()
            if src_edge and dst_edge:
                self._place_vehicles(src_edge, dst_edge)
                
                # Update GUI
                self.control_panel.update_vehicle_info(self.vehicle_pair)
                self.control_panel.update_csv_display(self.vehicle_pair['row_data'], self.current_row_index)
                
                logger.info(f"Moved to CSV row {self.current_row_index}")
                
    def _update_camera_view(self):
        """Update camera view based on follow and rotation modes with very close zoom"""
        try:
            if not self.vehicle_pair:
                return
                
            if (self.vehicle_pair['source_id'] not in traci.vehicle.getIDList() or 
                self.vehicle_pair['dest_id'] not in traci.vehicle.getIDList()):
                return
                
            # Get vehicle positions
            src_pos = traci.vehicle.getPosition(self.vehicle_pair['source_id'])
            dst_pos = traci.vehicle.getPosition(self.vehicle_pair['dest_id'])
            
            # Calculate center point
            center_x = (src_pos[0] + dst_pos[0]) / 2
            center_y = (src_pos[1] + dst_pos[1]) / 2
            
            # Calculate distance for zoom - very close
            distance = np.sqrt((src_pos[0] - dst_pos[0])**2 + (src_pos[1] - dst_pos[1])**2)
            zoom = max(1000, min(3000, 2000 - distance * 2))  # Very close zoom (higher value = closer)
            
            if self.follow_mode:
                # Follow the vehicles with very close zoom
                traci.gui.setOffset("View #0", center_x, center_y)
                traci.gui.setZoom("View #0", zoom)
                
            if self.rotation_mode:
                # Rotate camera around the center
                self.rotation_angle = (self.rotation_angle + 5) % 360
                traci.gui.setAngle("View #0", self.rotation_angle)
                
        except Exception as e:
            logger.warning(f"Error updating camera view: {e}")
            
    def _simulate_v2v_link(self, distance: float) -> bool:
        """Simulate V2V communication link with quality assessment"""
        if not self.vehicle_pair:
            return False
            
        # Get communication parameters from CSV data
        snr = self.vehicle_pair.get('snr', 15.0)
        rsrp = self.vehicle_pair.get('rsrp', -70.0)
        
        # Calculate link quality based on distance and signal parameters
        if distance <= 100:
            # Very close - high quality
            quality_factor = 1.0
        elif distance <= 300:
            # Medium distance - good quality
            quality_factor = 0.8
        elif distance <= 500:
            # Far distance - moderate quality
            quality_factor = 0.6
        else:
            # Too far - poor quality
            quality_factor = 0.2
            
        # Adjust for signal quality
        if snr > 20:
            quality_factor *= 1.2
        elif snr < 10:
            quality_factor *= 0.8
            
        if rsrp > -60:
            quality_factor *= 1.1
        elif rsrp < -80:
            quality_factor *= 0.9
            
        # Simulate link success
        self.link_quality = min(1.0, quality_factor)
        success_probability = self.link_quality
        
        # Update V2V link status
        self.v2v_link_active = (distance <= 500 and random.random() < success_probability)
        
        return self.v2v_link_active
            
    def _clear_highlights(self):
        """Clear all vehicle highlights, V2V link lines, and radius circles"""
        try:
            # Reset vehicle colors to original
            if self.vehicle_pair:
                traci.vehicle.setColor(self.vehicle_pair['source_id'], (255, 0, 0, 255))    # Red for source
                traci.vehicle.setColor(self.vehicle_pair['dest_id'], (0, 0, 255, 255))     # Blue for destination
                
            # Remove V2V link line
            try:
                if "v2v_link_line" in traci.polygon.getIDList():
                    traci.polygon.remove("v2v_link_line")
            except:
                pass
                
            # Remove distance label
            try:
                if "v2v_distance_label" in traci.polygon.getIDList():
                    traci.polygon.remove("v2v_distance_label")
            except:
                pass
                
            # Remove distance comparison text
            try:
                if "distance_comparison_text" in traci.polygon.getIDList():
                    traci.polygon.remove("distance_comparison_text")
                if "distance_comparison" in traci.polygon.getIDList():
                    traci.polygon.remove("distance_comparison")
            except:
                pass
                
            # Remove vehicle radius circles
            if self.vehicle_pair:
                try:
                    if f"radius_{self.vehicle_pair['source_id']}" in traci.polygon.getIDList():
                        traci.polygon.remove(f"radius_{self.vehicle_pair['source_id']}")
                except:
                    pass
                try:
                    if f"radius_{self.vehicle_pair['dest_id']}" in traci.polygon.getIDList():
                        traci.polygon.remove(f"radius_{self.vehicle_pair['dest_id']}")
                except:
                    pass
                
        except:
            pass
        
    def _check_v2v_communication(self, step: int):
        """Check V2V communication between the two vehicles with enhanced link simulation"""
        if not self.vehicle_pair.get('placed', False):
            return
            
        range_m = 500  # Communication range
        
        try:
            # Check if both vehicles exist
            if (self.vehicle_pair['source_id'] not in traci.vehicle.getIDList() or 
                self.vehicle_pair['dest_id'] not in traci.vehicle.getIDList()):
                return
                
            # Get positions
            src_pos = traci.vehicle.getPosition(self.vehicle_pair['source_id'])
            dst_pos = traci.vehicle.getPosition(self.vehicle_pair['dest_id'])
            
            # Calculate distance
            dist = np.sqrt((src_pos[0] - dst_pos[0])**2 + (src_pos[1] - dst_pos[1])**2)
            
            # Simulate V2V link
            link_success = self._simulate_v2v_link(dist)
            
            # Check communication range
            if dist <= range_m and link_success:
                self.results.append({
                    'step': step,
                    'source': self.vehicle_pair['source_id'],
                    'dest': self.vehicle_pair['dest_id'],
                    'distance': dist,
                    'src_pos': src_pos,
                    'dst_pos': dst_pos,
                    'snr': self.vehicle_pair['snr'],
                    'rsrp': self.vehicle_pair['rsrp'],
                    'link_quality': self.link_quality,
                    'row_index': self.current_row_index
                })
                
                logger.info(f"V2V communication at step {step}: distance {dist:.1f}m, quality {self.link_quality:.2f}")
                    
        except Exception as e:
            logger.warning(f"Communication check error: {e}")
                
    def _simulate_communication(self, distance: float) -> bool:
        """Legacy V2V communication simulation (replaced by _simulate_v2v_link)"""
        return self._simulate_v2v_link(distance)
        
    def save_results(self):
        """Save simulation results"""
        logger.info("Saving results...")
        
        os.makedirs("focused_v2v_results", exist_ok=True)
        
        # Save communication events
        if self.results:
            df = pd.DataFrame(self.results)
            df.to_csv("focused_v2v_results/communication_events.csv", index=False)
            
            # Statistics
            stats = {
                'total_events': len(self.results),
                'avg_distance': np.mean([r['distance'] for r in self.results]),
                'min_distance': np.min([r['distance'] for r in self.results]),
                'max_distance': np.max([r['distance'] for r in self.results]),
                'avg_snr': np.mean([r['snr'] for r in self.results])
            }
            
            with open("focused_v2v_results/stats.json", 'w') as f:
                json.dump(stats, f, indent=2)
                
        # Save vehicle pair info
        if self.vehicle_pair:
            with open("focused_v2v_results/vehicle_pair.json", 'w') as f:
                json.dump(self.vehicle_pair, f, indent=2)
        
        logger.info("Results saved to focused_v2v_results/")


def main():
    """Main function"""
    
    csv_file = "sidelink_parsed.csv"
    
    if not os.path.exists(csv_file):
        logger.error(f"CSV file not found: {csv_file}")
        return
        
    if not os.path.exists("sumo-config/osm.sumocfg"):
        logger.error("SUMO config not found!")
        return
        
    try:
        # Create and run focused simulator
        simulator = FocusedV2VSimulator(csv_file)
        simulator.run_simulation()
        simulator.save_results()
        
        logger.info("Focused V2V simulation completed!")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
