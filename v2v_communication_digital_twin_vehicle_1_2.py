#!/usr/bin/env python3
"""
V2V Communication Digital Twin for Vehicle 1-2 Scenario
Based on v2v_communication_digital_twin.py but customized for Vehicle 1-2
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
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

# Distance calibration
CALIBRATION_FACTOR = 0.607  # Baseline calibration

def get_adaptive_calibration(actual_distance_m, dataset_type="continuous"):
    """Adaptive calibration based on distance ranges and dataset type"""
    if dataset_type == "baseline":
        return CALIBRATION_FACTOR
    
    # For Vehicle 1-2, analysis shows simulated distances are close to actual
    # But we may still need slight calibration
    # Try no calibration first, but allow override
    return 1.0000  # Start with no calibration
    
    # Alternative: Apply slight calibration if distances are systematically off
    # return 0.85  # If simulated distances tend to be larger than actual

# V2V Communication Parameters (CORRECTED for SNR accuracy)
CARRIER_FREQUENCY_GHZ = 5.9
TX_POWER_DBM = 23  # ✅ FIXED: Standard V2V/PC5 Sidelink TX power (was 20)
BANDWIDTH_MHZ = 10
BANDWIDTH_HZ = BANDWIDTH_MHZ * 1e6  # Convert to Hz for noise calculation

# Antenna gains (both TX and RX)
TX_ANTENNA_GAIN_DB = 3
RX_ANTENNA_GAIN_DB = 3
TOTAL_ANTENNA_GAIN_DB = TX_ANTENNA_GAIN_DB + RX_ANTENNA_GAIN_DB  # = 6 dB

# ✅ FIXED: Correct thermal noise calculation
# Thermal noise = -174 dBm/Hz + 10*log10(Bandwidth)
# For 10 MHz: -174 + 10*log10(10e6) = -174 + 70 = -104 dBm
THERMAL_NOISE_DENSITY_DBM_HZ = -174
NOISE_FLOOR_DBM = THERMAL_NOISE_DENSITY_DBM_HZ + 10 * math.log10(BANDWIDTH_HZ)
# Result: -104 dBm (was incorrectly -90 dBm, causing 14 dB SNR underestimation)

# 3GPP Urban Macro Parameters
URBAN_MACRO_PARAMS = {
    'path_loss_exponent': 3.75,
    'shadowing_std_db': 8.0,
    'base_path_loss_db': 38.46
}

# Scenario-specific configuration
SCENARIO_NAME = "vehicle_1_2"
SCENARIO_CSV = "scenarios/vehicle_1_2_first_2000.csv"
SUMO_CONFIG_DIR = "veh_1_2_sumo_config"
SUMO_CONFIG_FILE = "osm.sumocfg"

# ============================================================================
# COMMUNICATION MODELS (Same as original)
# ============================================================================

def calculate_fspl(distance_m, frequency_ghz=5.9):
    """Calculate Free Space Path Loss"""
    if distance_m <= 0:
        return 0
    frequency_mhz = frequency_ghz * 1000
    fspl_db = 20 * math.log10(distance_m) + 20 * math.log10(frequency_mhz) + 32.45
    return fspl_db

def calculate_3gpp_urban_macro_path_loss(distance_m, frequency_ghz=5.9):
    """Calculate path loss using 3GPP Urban Macro model"""
    if distance_m <= 0:
        return 0
    pl = (URBAN_MACRO_PARAMS['base_path_loss_db'] + 
          URBAN_MACRO_PARAMS['path_loss_exponent'] * 10 * math.log10(distance_m) + 
          20 * math.log10(frequency_ghz / 5.0))
    return pl

def calculate_snr(distance_m, tx_power_dbm, noise_floor_dbm, model='FSPL',
                  frequency_ghz=5.9, tx_antenna_gain_db=3, rx_antenna_gain_db=3):
    """
    Calculate Signal-to-Noise Ratio (CORRECTED)

    Args:
        distance_m: Distance in meters
        tx_power_dbm: Transmit power in dBm
        noise_floor_dbm: Noise floor in dBm
        model: Path loss model ('FSPL' or '3GPP')
        frequency_ghz: Carrier frequency in GHz
        tx_antenna_gain_db: Transmitter antenna gain in dB
        rx_antenna_gain_db: Receiver antenna gain in dB

    Returns:
        tuple: (snr_db, path_loss)
    """
    if model == 'FSPL':
        path_loss = calculate_fspl(distance_m, frequency_ghz)
    elif model == '3GPP':
        path_loss = calculate_3gpp_urban_macro_path_loss(distance_m, frequency_ghz)
    else:
        path_loss = calculate_fspl(distance_m, frequency_ghz)

    # ✅ FIXED: Correct SNR calculation
    # Include both TX and RX antenna gains
    total_antenna_gain = tx_antenna_gain_db + rx_antenna_gain_db
    received_power_dbm = tx_power_dbm + total_antenna_gain - path_loss
    snr_db = received_power_dbm - noise_floor_dbm

    return snr_db, path_loss

def calculate_prr(snr_db):
    """Calculate Packet Reception Rate from SNR"""
    snr_threshold = 5.0
    k = 0.5
    prr = 1.0 / (1.0 + math.exp(-k * (snr_db - snr_threshold)))
    return prr * 100

def calculate_communication_range(tx_power_dbm, noise_floor_dbm, snr_threshold_db=10,
                                 model='FSPL', frequency_ghz=5.9,
                                 tx_antenna_gain_db=3, rx_antenna_gain_db=3):
    """Calculate maximum communication range"""
    # Binary search for range
    min_range = 1
    max_range = 1000
    target_range = 100

    for _ in range(20):  # 20 iterations for convergence
        snr, _ = calculate_snr(target_range, tx_power_dbm, noise_floor_dbm,
                              model, frequency_ghz, tx_antenna_gain_db, rx_antenna_gain_db)
        if snr > snr_threshold_db:
            min_range = target_range
            target_range = (target_range + max_range) / 2
        else:
            max_range = target_range
            target_range = (min_range + target_range) / 2

    return target_range

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def kmh_to_ms(speed_kmh):
    """Convert km/h to m/s"""
    return speed_kmh / 3.6

def calculate_distance(pos1, pos2):
    """Calculate Euclidean distance"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def find_optimal_path_through_waypoints(net, waypoints_df, vehicle_type='source', sample_step=None):
    """Find connected path through waypoints"""
    edges_with_positions = []
    
    num_waypoints = len(waypoints_df)
    
    if sample_step is None:
        if num_waypoints <= 50:
            sample_step = 1
        elif num_waypoints <= 100:
            sample_step = 1
        elif num_waypoints <= 200:
            sample_step = 2
        else:
            sample_step = 3
    
    sampled_waypoints = waypoints_df.iloc[::sample_step]
    
    for idx, row in sampled_waypoints.iterrows():
        if vehicle_type == 'source':
            lat = row['Latitude_source']
            lon = row['Longitude_source']
        else:
            lat = row['Latitude_destination']
            lon = row['Longitude_destination']
        
        x, y = net.convertLonLat2XY(lon, lat)
        
        search_radius = 50
        while search_radius <= 300:
            nearby_edges = net.getNeighboringEdges(x, y, r=search_radius)
            if nearby_edges:
                edge = min(nearby_edges, key=lambda e: e[1])[0]
                edges_with_positions.append({
                    'edge': edge,
                    'edge_id': edge.getID(),
                    'position': (x, y),
                    'index': idx
                })
                break
            search_radius += 50
    
    if not edges_with_positions:
        return [], []
    
    route = []
    for i in range(len(edges_with_positions)):
        current = edges_with_positions[i]
        
        if i == 0:
            route.append(current['edge_id'])
        else:
            prev = edges_with_positions[i-1]
            try:
                path = net.getShortestPath(prev['edge'], current['edge'])
                if path and path[0]:
                    for edge in path[0]:
                        if edge.getID() not in route:
                            route.append(edge.getID())
                    if current['edge_id'] not in route:
                        route.append(current['edge_id'])
            except:
                if current['edge_id'] not in route:
                    route.append(current['edge_id'])
    
    return route, []

def validate_and_repair_route(net, route):
    """Validate route connectivity and repair gaps"""
    if len(route) < 2:
        return route
    
    validated_route = [route[0]]  # Start with first edge
    
    for i in range(len(route) - 1):
        current_edge_id = validated_route[-1]
        next_edge_id = route[i + 1]
        
        try:
            current_edge = net.getEdge(current_edge_id)
            next_edge = net.getEdge(next_edge_id)
            
            # Check if edges are directly connected
            outgoing_ids = [edge.getID() for edge in current_edge.getOutgoing().keys()]
            
            if next_edge_id in outgoing_ids:
                # Directly connected, add it
                validated_route.append(next_edge_id)
            else:
                # Not directly connected, find path
                try:
                    path = net.getShortestPath(current_edge, next_edge)
                    if path and path[0] and len(path[0]) > 0:
                        # Add all intermediate edges
                        for edge in path[0]:
                            edge_id = edge.getID()
                            if edge_id != current_edge_id:  # Don't duplicate current edge
                                validated_route.append(edge_id)
                        # Ensure next_edge is added
                        if next_edge_id not in validated_route:
                            validated_route.append(next_edge_id)
                    else:
                        # Path not found, try to find any outgoing edge that can reach next_edge
                        found_connection = False
                        for out_edge_id in outgoing_ids:
                            try:
                                out_edge = net.getEdge(out_edge_id)
                                test_path = net.getShortestPath(out_edge, next_edge)
                                if test_path and test_path[0] and len(test_path[0]) > 0:
                                    validated_route.append(out_edge_id)
                                    for edge in test_path[0]:
                                        edge_id = edge.getID()
                                        if edge_id not in validated_route:
                                            validated_route.append(edge_id)
                                    found_connection = True
                                    break
                            except:
                                continue
                        
                        if not found_connection:
                            # Skip this edge, can't connect to it
                            pass
                except Exception as e:
                    # Skip this edge if path finding fails
                    pass
        except Exception as e:
            # Edge not found, skip
            pass
    
    return validated_route

# ============================================================================
# MAIN GUI CLASS
# ============================================================================

class V2VCommunicationDigitalTwinVehicle12:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("V2V Communication Digital Twin - Vehicle 1-2")
        self.root.geometry("700x700")
        
        self.simulation_running = False
        self.simulation_thread = None
        
        self.num_waypoints = tk.IntVar(value=2000)
        self.calibration_enabled = tk.BooleanVar(value=True)
        self.use_realistic_speed = tk.BooleanVar(value=True)
        self.path_loss_model = tk.StringVar(value='FSPL')
        self.use_all_waypoints = tk.BooleanVar(value=False)
        self.use_old_calibration = tk.BooleanVar(value=False)  # Option to use 0.607 calibration
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup GUI"""
        title_label = tk.Label(self.root, text="V2V Digital Twin - Vehicle 1 ↔ Vehicle 2", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        info_label = tk.Label(self.root, text="Distance + Path Loss + SNR + PRR Validation", 
                             font=("Arial", 10), fg="blue")
        info_label.pack()
        
        # Configuration Frame
        config_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(config_frame, text="Waypoints:").grid(row=0, column=0, sticky="w")
        ttk.Scale(config_frame, from_=100, to=2000, variable=self.num_waypoints, 
                 orient="horizontal", length=200).grid(row=0, column=1)
        ttk.Label(config_frame, textvariable=self.num_waypoints).grid(row=0, column=2)
        
        ttk.Label(config_frame, text="Dataset:").grid(row=1, column=0, sticky="w")
        dataset_label = ttk.Label(config_frame, text=SCENARIO_CSV, font=("Arial", 9))
        dataset_label.grid(row=1, column=1, columnspan=2, sticky="w")
        
        ttk.Checkbutton(config_frame, text="✅ Use Realistic Speed from Dataset", 
                       variable=self.use_realistic_speed).grid(row=2, column=0, columnspan=3, sticky="w")
        
        ttk.Checkbutton(config_frame, text="✅ Apply Calibration (Adaptive)", 
                       variable=self.calibration_enabled).grid(row=3, column=0, columnspan=3, sticky="w")
        
        ttk.Checkbutton(config_frame, text="✅ Use Old Calibration (0.607) - if accuracy low", 
                       variable=self.use_old_calibration).grid(row=4, column=0, columnspan=3, sticky="w")
        
        ttk.Checkbutton(config_frame, text="✅ Use All Waypoints (Smart Sampling)", 
                       variable=self.use_all_waypoints).grid(row=5, column=0, columnspan=3, sticky="w")
        
        # Path Loss Model Selection
        model_frame = ttk.LabelFrame(self.root, text="Path Loss Model", padding=10)
        model_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Radiobutton(model_frame, text="Free Space Path Loss (FSPL)", 
                       variable=self.path_loss_model, value='FSPL').pack(anchor='w')
        ttk.Radiobutton(model_frame, text="3GPP Urban Macro", 
                       variable=self.path_loss_model, value='3GPP').pack(anchor='w')
        
        # Communication Parameters Display
        comm_frame = ttk.LabelFrame(self.root, text="V2V Parameters", padding=10)
        comm_frame.pack(fill="x", padx=10, pady=5)

        params_text = f"Frequency: {CARRIER_FREQUENCY_GHZ} GHz | Tx Power: {TX_POWER_DBM} dBm | Noise: {NOISE_FLOOR_DBM:.1f} dBm | Ant Gain: {TOTAL_ANTENNA_GAIN_DB} dB"
        ttk.Label(comm_frame, text=params_text, font=("Arial", 9)).pack()
        
        # Control Frame
        control_frame = ttk.LabelFrame(self.root, text="Control", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        self.start_button = ttk.Button(control_frame, text="Start Digital Twin Simulation", 
                                      command=self.start_simulation)
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", 
                                     command=self.stop_simulation, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        # Status Frame
        status_frame = ttk.LabelFrame(self.root, text="Status", padding=10)
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_text = tk.Text(status_frame, height=20, width=80)
        scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        
    def log_message(self, message):
        """Log message to status"""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_simulation(self):
        """Start simulation"""
        if self.simulation_running:
            return
            
        self.simulation_running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        self.status_text.delete(1.0, tk.END)
        
        self.simulation_thread = threading.Thread(target=self.run_simulation)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
    def stop_simulation(self):
        """Stop simulation"""
        self.simulation_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        try:
            traci.close()
        except:
            pass
            
        self.log_message("🛑 Simulation stopped")
        
    def run_simulation(self):
        """Main simulation - adapted for Vehicle 1-2"""
        try:
            self.log_message("="*70)
            self.log_message("V2V COMMUNICATION DIGITAL TWIN - VEHICLE 1-2")
            self.log_message("="*70)
            self.log_message(f"🚗 Speed Mode: {'REALISTIC (from GPS data)' if self.use_realistic_speed.get() else 'CONSTANT (15 m/s)'}")
            if self.calibration_enabled.get():
                calib_type = f"OLD (0.607)" if self.use_old_calibration.get() else "ADAPTIVE"
                self.log_message(f"📊 Calibration: ENABLED ({calib_type})")
            else:
                self.log_message(f"📊 Calibration: DISABLED")
            self.log_message(f"📡 Path Loss Model: {self.path_loss_model.get()}")
            self.log_message(f"📂 Scenario: {SCENARIO_NAME}")
            self.log_message(f"📂 Dataset: {SCENARIO_CSV}")
            
            NUM_WAYPOINTS = min(self.num_waypoints.get(), 2000)  # Cap at 2000
            SIMULATION_STEPS = max(8000, NUM_WAYPOINTS * 60)
            
            original_dir = os.getcwd()
            
            # Load network from Vehicle 1-2 SUMO config directory
            os.chdir(SUMO_CONFIG_DIR)
            self.log_message(f"\n📍 Loading SUMO network from {SUMO_CONFIG_DIR}...")
            net = sumolib.net.readNet('osm.net.xml.gz')
            self.log_message(f"✅ Network loaded: {len(net.getEdges())} edges")
            
            # Load GPS data
            self.log_message(f"\n📍 Loading GPS data from {SCENARIO_CSV}...")
            df = pd.read_csv(f'../{SCENARIO_CSV}')
            waypoints_df = df.head(NUM_WAYPOINTS)
            self.log_message(f"✅ Loaded {len(waypoints_df)} waypoints")
            
            # Load metadata
            metadata_file = f'../scenarios/{SCENARIO_NAME}_metadata.json'
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            vehicle1_id = metadata['source_vehicle']
            vehicle2_id = metadata['destination_vehicle']
            self.log_message(f"📊 Vehicle Pair: {vehicle1_id} ↔ {vehicle2_id}")
            
            # Check communication parameters
            has_snr = 'SNR' in waypoints_df.columns
            has_rsrp = 'RSRP' in waypoints_df.columns
            if has_snr:
                self.log_message(f"✅ Dataset contains SNR values (mean: {waypoints_df['SNR'].mean():.2f} dB)")
            if has_rsrp:
                self.log_message(f"✅ Dataset contains RSRP values (mean: {waypoints_df['RSRP'].mean():.2f} dBm)")
            
            # Find routes
            self.log_message(f"\n📍 Computing routes for {NUM_WAYPOINTS} waypoints...")
            
            if self.use_all_waypoints.get():
                if NUM_WAYPOINTS <= 100:
                    sample_step = 1
                else:
                    sample_step = max(1, NUM_WAYPOINTS // 100)  # Use more waypoints
                self.log_message(f"📊 Using every {sample_step}th waypoint (~{NUM_WAYPOINTS // sample_step} route points)")
            else:
                # Use denser sampling for better route coverage
                if NUM_WAYPOINTS <= 50:
                    sample_step = 1
                elif NUM_WAYPOINTS <= 100:
                    sample_step = 1  # Use all for small datasets
                elif NUM_WAYPOINTS <= 200:
                    sample_step = 2  # Every 2nd waypoint
                elif NUM_WAYPOINTS <= 500:
                    sample_step = 3  # Every 3rd waypoint
                else:
                    sample_step = 4  # Every 4th waypoint for very large datasets
                self.log_message(f"📊 Using every {sample_step}th waypoint for route (~{NUM_WAYPOINTS // sample_step} route points)")
            
            source_route, _ = find_optimal_path_through_waypoints(net, waypoints_df, 'source', sample_step)
            dest_route, _ = find_optimal_path_through_waypoints(net, waypoints_df, 'destination', sample_step)
            
            if len(source_route) == 0 or len(dest_route) == 0:
                self.log_message(f"❌ ERROR: Could not generate routes")
                return
            
            # Validate and repair routes to ensure connectivity
            self.log_message(f"\n🔧 Validating and repairing routes...")
            self.log_message(f"   Source route before: {len(source_route)} edges")
            self.log_message(f"   Dest route before: {len(dest_route)} edges")
            
            source_route = validate_and_repair_route(net, source_route)
            dest_route = validate_and_repair_route(net, dest_route)
            
            self.log_message(f"   Source route after: {len(source_route)} edges")
            self.log_message(f"   Dest route after: {len(dest_route)} edges")
            
            if len(source_route) < 2 or len(dest_route) < 2:
                self.log_message(f"❌ ERROR: Routes too short after validation")
                return
            
            # Final connectivity check
            self.log_message(f"\n🔍 Final connectivity check...")
            source_valid = True
            dest_valid = True
            
            for i in range(len(source_route) - 1):
                try:
                    edge1 = net.getEdge(source_route[i])
                    edge2_id = source_route[i + 1]
                    outgoing = [e.getID() for e in edge1.getOutgoing().keys()]
                    if edge2_id not in outgoing:
                        # Check if path exists
                        edge2 = net.getEdge(edge2_id)
                        path = net.getShortestPath(edge1, edge2)
                        if not path or not path[0]:
                            self.log_message(f"⚠️ Source route gap: {source_route[i]} -> {source_route[i+1]}")
                            source_valid = False
                except:
                    source_valid = False
            
            for i in range(len(dest_route) - 1):
                try:
                    edge1 = net.getEdge(dest_route[i])
                    edge2_id = dest_route[i + 1]
                    outgoing = [e.getID() for e in edge1.getOutgoing().keys()]
                    if edge2_id not in outgoing:
                        edge2 = net.getEdge(edge2_id)
                        path = net.getShortestPath(edge1, edge2)
                        if not path or not path[0]:
                            self.log_message(f"⚠️ Dest route gap: {dest_route[i]} -> {dest_route[i+1]}")
                            dest_valid = False
                except:
                    dest_valid = False
            
            if not source_valid or not dest_valid:
                self.log_message(f"❌ ERROR: Routes still have connectivity issues")
                self.log_message(f"   Consider reducing waypoints or using different sampling")
                return
            
            source_route_dist = sum([net.getEdge(edge_id).getLength() for edge_id in source_route])
            dest_route_dist = sum([net.getEdge(edge_id).getLength() for edge_id in dest_route])
            
            self.log_message(f"✅ Source route: {len(source_route)} edges ({source_route_dist:.1f}m)")
            self.log_message(f"✅ Destination route: {len(dest_route)} edges ({dest_route_dist:.1f}m)")
            
            # Create route file
            self.log_message("\n📍 Creating route file...")
            route_file = 'v2v_vehicle_1_2_routes.rou.xml'
            with open(route_file, 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<routes>\n')
                f.write('    <vType id="v2v_source_type" accel="2.6" decel="4.5" sigma="0.5" ')
                f.write('length="4.5" width="1.8" height="1.5" minGap="2.5" ')
                f.write('maxSpeed="50" guiShape="passenger" color="0,0,255"/>\n')
                
                f.write('    <vType id="v2v_dest_type" accel="2.6" decel="4.5" sigma="0.5" ')
                f.write('length="4.5" width="1.8" height="1.5" minGap="2.5" ')
                f.write('maxSpeed="50" guiShape="passenger" color="255,0,0"/>\n')
                
                f.write(f'    <route id="source_route" edges="{" ".join(source_route)}"/>\n')
                f.write(f'    <route id="dest_route" edges="{" ".join(dest_route)}"/>\n')
                
                f.write('    <vehicle id="v2v_source" type="v2v_source_type" ')
                f.write('route="source_route" depart="0" departLane="best" departSpeed="0"/>\n')
                
                f.write('    <vehicle id="v2v_dest" type="v2v_dest_type" ')
                f.write('route="dest_route" depart="0" departLane="best" departSpeed="0"/>\n')
                
                f.write('</routes>\n')
            
            # Create SUMO config
            config_file = 'v2v_vehicle_1_2.sumocfg'
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
                f.write('</configuration>\n')
            
            # Validate routes before starting SUMO
            self.log_message("\n🔍 Validating routes...")
            all_edges = set(net.getEdges())
            all_edge_ids = {edge.getID() for edge in all_edges}
            
            source_invalid = [e for e in source_route if e not in all_edge_ids]
            dest_invalid = [e for e in dest_route if e not in all_edge_ids]
            
            if source_invalid:
                self.log_message(f"⚠️ WARNING: {len(source_invalid)} invalid edges in source route:")
                self.log_message(f"   First 5: {source_invalid[:5]}")
            if dest_invalid:
                self.log_message(f"⚠️ WARNING: {len(dest_invalid)} invalid edges in destination route:")
                self.log_message(f"   First 5: {dest_invalid[:5]}")
            
            if source_invalid or dest_invalid:
                self.log_message("❌ ERROR: Routes contain invalid edges. Cannot start simulation.")
                return
            
            # Start SUMO (remove --quit-on-end to keep it open)
            self.log_message("\n🚀 Starting SUMO-GUI...")
            self.log_message(f"   Config file: {config_file}")
            self.log_message(f"   Route file: {route_file}")
            
            sumo_cmd = ["sumo-gui", "-c", config_file, "--start"]
            try:
                traci.start(sumo_cmd)
                self.log_message("✅ TraCI connection established")
            except Exception as e:
                self.log_message(f"❌ ERROR: Failed to start SUMO: {e}")
                import traceback
                self.log_message(traceback.format_exc())
                return
            
            # Wait for SUMO to initialize
            time.sleep(5)
            
            # Check connection status
            try:
                step_count = traci.simulation.getCurrentTime()
                self.log_message(f"✅ SUMO initialized at step {step_count}")
            except Exception as e:
                self.log_message(f"⚠️ WARNING: Could not get simulation step: {e}")
            
            # Check if vehicles exist
            try:
                vehicles_before = traci.vehicle.getIDList()
                self.log_message(f"📊 Vehicles before insertion: {len(vehicles_before)}")
                if vehicles_before:
                    self.log_message(f"   Vehicle IDs: {vehicles_before[:5]}")
            except Exception as e:
                self.log_message(f"⚠️ WARNING: Could not get vehicle list: {e}")
            
            # Add POIs for waypoints (limit for performance)
            self.log_message("📍 Adding waypoint markers...")
            waypoint_coords = []
            poi_count = 0
            max_pois = 500  # Limit POIs to prevent slowdown
            
            for idx, row in waypoints_df.iterrows():
                if poi_count >= max_pois:
                    break
                
                try:
                    src_x, src_y = net.convertLonLat2XY(row['Longitude_source'], row['Latitude_source'])
                    traci.poi.add(f"src_wp_{idx}", src_x, src_y, color=(0, 0, 255, 128), 
                                 poiType="source", layer=100)
                    
                    dst_x, dst_y = net.convertLonLat2XY(row['Longitude_destination'], row['Latitude_destination'])
                    traci.poi.add(f"dst_wp_{idx}", dst_x, dst_y, color=(255, 0, 0, 128), 
                                 poiType="destination", layer=100)
                    
                    wp_data = {
                        'source': (src_x, src_y),
                        'dest': (dst_x, dst_y),
                        'actual_distance': row['distance'],
                        'source_speed_kmh': row['speed_kmh_source'],
                        'dest_speed_kmh': row['speed_kmh_destination']
                    }
                    
                    if has_snr:
                        wp_data['SNR'] = row['SNR']
                    if has_rsrp:
                        wp_data['RSRP'] = row['RSRP']
                    
                    waypoint_coords.append(wp_data)
                    poi_count += 1
                except Exception as e:
                    self.log_message(f"⚠️ Warning: Could not add POI {idx}: {e}")
                    # Still add waypoint data even if POI fails
                    try:
                        src_x, src_y = net.convertLonLat2XY(row['Longitude_source'], row['Latitude_source'])
                        dst_x, dst_y = net.convertLonLat2XY(row['Longitude_destination'], row['Latitude_destination'])
                        wp_data = {
                            'source': (src_x, src_y),
                            'dest': (dst_x, dst_y),
                            'actual_distance': row['distance'],
                            'source_speed_kmh': row['speed_kmh_source'],
                            'dest_speed_kmh': row['speed_kmh_destination']
                        }
                        if has_snr:
                            wp_data['SNR'] = row['SNR']
                        if has_rsrp:
                            wp_data['RSRP'] = row['RSRP']
                        waypoint_coords.append(wp_data)
                    except:
                        pass
            
            self.log_message(f"✅ Added {poi_count*2} POIs (limited to {max_pois} waypoints for performance)")
            self.log_message(f"✅ Prepared {len(waypoint_coords)} waypoint coordinates")
            
            # Check vehicles after a few steps
            self.log_message("\n🔍 Checking vehicle insertion...")
            try:
                # Step forward a few times to let vehicles insert
                for i in range(10):
                    traci.simulationStep()
                
                vehicles_after = traci.vehicle.getIDList()
                self.log_message(f"📊 Vehicles after insertion: {len(vehicles_after)}")
                if vehicles_after:
                    self.log_message(f"   Vehicle IDs: {vehicles_after}")
                else:
                    self.log_message("⚠️ WARNING: No vehicles found! Routes may be invalid.")
                    self.log_message("   Checking route validity...")
                    
                    # Check if routes are valid
                    try:
                        route_ids = traci.route.getIDList()
                        self.log_message(f"   Available routes: {route_ids}")
                    except:
                        pass
                    
                    # Try to get more info
                    try:
                        pending_vehicles = traci.simulation.getPendingVehicles()
                        self.log_message(f"   Pending vehicles: {pending_vehicles}")
                    except:
                        pass
                        
            except Exception as e:
                self.log_message(f"⚠️ WARNING: Error checking vehicles: {e}")
                import traceback
                self.log_message(traceback.format_exc())
            
            # Run simulation (rest of the simulation logic same as original)
            self.log_message("\n🎯 Starting communication digital twin...")
            self.log_message("-"*70)
            
            step = 10  # Start from 10 since we already stepped
            source_active = False
            dest_active = False
            current_waypoint = 0
            
            distances_raw = []
            distances_calibrated = []
            source_progress = []
            dest_progress = []
            communication_analysis = []
            
            last_error_log = 0
            
            while step < SIMULATION_STEPS and self.simulation_running:
                try:
                    # Check connection
                    try:
                        traci.simulationStep()
                        step += 1
                    except traci.exceptions.FatalTraCIError as e:
                        self.log_message(f"❌ Fatal TraCI Error at step {step}: {e}")
                        self.log_message("   SUMO connection closed unexpectedly")
                        break
                    except traci.exceptions.TraCIException as e:
                        if step - last_error_log > 100:  # Log every 100 steps
                            self.log_message(f"⚠️ TraCI Exception at step {step}: {e}")
                            last_error_log = step
                except Exception as e:
                    self.log_message(f"❌ Simulation Error at step {step}: {e}")
                    import traceback
                    self.log_message(traceback.format_exc())
                    break
                
                progress = min(100, (step / SIMULATION_STEPS) * 100)
                self.progress_var.set(progress)
                
                try:
                    vehicles = traci.vehicle.getIDList()
                except Exception as e:
                    if step % 100 == 0:
                        self.log_message(f"⚠️ Could not get vehicle list at step {step}: {e}")
                    vehicles = []
                
                # Source vehicle (Vehicle 1)
                if "v2v_source" in vehicles:
                    if not source_active:
                        self.log_message(f"✅ Step {step}: Source vehicle (Vehicle {vehicle1_id}) active")
                        source_active = True
                    
                    src_pos = traci.vehicle.getPosition("v2v_source")
                    src_speed = traci.vehicle.getSpeed("v2v_source")
                    
                    if self.use_realistic_speed.get() and current_waypoint < len(waypoint_coords):
                        target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['source_speed_kmh'])
                        traci.vehicle.setSpeed("v2v_source", target_speed_ms)
                    
                    # Improved waypoint tracking: track sequential progress
                    closest_wp = 0
                    min_dist = float('inf')
                    
                    # Start search from current waypoint to avoid jumping backwards
                    search_start = max(0, current_waypoint - 5)
                    search_end = min(len(waypoint_coords), current_waypoint + 20)
                    
                    for i in range(search_start, search_end):
                        wp = waypoint_coords[i]
                        dist = calculate_distance(src_pos, wp['source'])
                        if dist < min_dist:
                            min_dist = dist
                            closest_wp = i
                    
                    # Only update if we've moved forward or very close
                    if closest_wp >= current_waypoint or min_dist < 50:
                        source_progress.append(closest_wp)
                    else:
                        source_progress.append(current_waypoint)
                
                # Destination vehicle (Vehicle 2)
                if "v2v_dest" in vehicles:
                    if not dest_active:
                        self.log_message(f"✅ Step {step}: Destination vehicle (Vehicle {vehicle2_id}) active")
                        dest_active = True
                    
                    dst_pos = traci.vehicle.getPosition("v2v_dest")
                    dst_speed = traci.vehicle.getSpeed("v2v_dest")
                    
                    if self.use_realistic_speed.get() and current_waypoint < len(waypoint_coords):
                        target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['dest_speed_kmh'])
                        traci.vehicle.setSpeed("v2v_dest", target_speed_ms)
                    
                    # Improved waypoint tracking: track sequential progress
                    closest_wp = 0
                    min_dist = float('inf')
                    
                    # Start search from current waypoint to avoid jumping backwards
                    search_start = max(0, current_waypoint - 5)
                    search_end = min(len(waypoint_coords), current_waypoint + 20)
                    
                    for i in range(search_start, search_end):
                        wp = waypoint_coords[i]
                        dist = calculate_distance(dst_pos, wp['dest'])
                        if dist < min_dist:
                            min_dist = dist
                            closest_wp = i
                    
                    # Only update if we've moved forward or very close
                    if closest_wp >= current_waypoint or min_dist < 50:
                        dest_progress.append(closest_wp)
                    else:
                        dest_progress.append(current_waypoint)
                
                # Calculate distances and communication
                if source_active and dest_active:
                    raw_distance = calculate_distance(src_pos, dst_pos)
                    distances_raw.append(raw_distance)
                    
                    if self.calibration_enabled.get():
                        # Use old calibration if option is enabled
                        if self.use_old_calibration.get():
                            calibration_factor = CALIBRATION_FACTOR  # 0.607
                        else:
                            actual_distance = None
                            if current_waypoint < len(waypoint_coords):
                                actual_distance = calculate_distance(
                                    waypoint_coords[current_waypoint]['source'], 
                                    waypoint_coords[current_waypoint]['dest']
                                )
                            
                            if actual_distance is not None:
                                calibration_factor = get_adaptive_calibration(actual_distance, "continuous")
                            else:
                                calibration_factor = 1.0  # No calibration
                        
                        calibrated_distance = raw_distance * calibration_factor
                        distances_calibrated.append(calibrated_distance)
                    else:
                        distances_calibrated.append(raw_distance)
                    
                    # Update current waypoint - use average of both vehicles' progress
                    prev_waypoint = current_waypoint
                    if source_progress and dest_progress:
                        # Use average progress, but ensure we don't go backwards
                        avg_progress = (source_progress[-1] + dest_progress[-1]) / 2
                        new_waypoint = int(avg_progress)
                        # Only advance waypoint if we've made progress
                        if new_waypoint > current_waypoint:
                            current_waypoint = new_waypoint
                        elif new_waypoint >= current_waypoint - 2:  # Allow small backward jumps
                            current_waypoint = new_waypoint
                    
                    # Communication analysis when waypoint changes
                    if current_waypoint != prev_waypoint and current_waypoint < len(waypoint_coords):
                        wp_data = waypoint_coords[current_waypoint]
                        
                        # Distance metrics
                        actual_distance = wp_data['actual_distance']
                        simulated_distance = calibrated_distance if self.calibration_enabled.get() else raw_distance
                        
                        distance_error = simulated_distance - actual_distance
                        distance_error_pct = (distance_error / actual_distance * 100) if actual_distance > 0 else 0
                        distance_accuracy = max(0, 100 - abs(distance_error_pct))
                        
                        # Communication parameters based on SIMULATED distance
                        model = self.path_loss_model.get()
                        sim_snr, sim_path_loss = calculate_snr(simulated_distance, TX_POWER_DBM,
                                                              NOISE_FLOOR_DBM, model,
                                                              CARRIER_FREQUENCY_GHZ,
                                                              TX_ANTENNA_GAIN_DB, RX_ANTENNA_GAIN_DB)
                        sim_prr = calculate_prr(sim_snr)

                        # Communication parameters based on ACTUAL distance (ground truth)
                        actual_snr, actual_path_loss = calculate_snr(actual_distance, TX_POWER_DBM,
                                                                    NOISE_FLOOR_DBM, model,
                                                                    CARRIER_FREQUENCY_GHZ,
                                                                    TX_ANTENNA_GAIN_DB, RX_ANTENNA_GAIN_DB)
                        actual_prr = calculate_prr(actual_snr)
                        
                        # Communication accuracy metrics
                        path_loss_error = sim_path_loss - actual_path_loss
                        path_loss_error_pct = (path_loss_error / actual_path_loss * 100) if actual_path_loss != 0 else 0
                        path_loss_accuracy = max(0, 100 - abs(path_loss_error_pct))
                        
                        snr_error = sim_snr - actual_snr
                        snr_error_pct = (snr_error / actual_snr * 100) if actual_snr != 0 else 0
                        snr_accuracy = max(0, 100 - abs(snr_error_pct))
                        
                        prr_error = sim_prr - actual_prr
                        prr_error_pct = (prr_error / actual_prr * 100) if actual_prr > 0 else 0
                        prr_accuracy = max(0, 100 - abs(prr_error_pct))
                        
                        # Get dataset communication params if available
                        dataset_snr = wp_data.get('SNR', None)
                        dataset_rsrp = wp_data.get('RSRP', None)

                        # Calculate RSRP and RSSI from simulated and actual distances
                        # RSRP = Tx_Power + Total_Antenna_Gain - Path_Loss
                        # ✅ FIXED: Include antenna gains in RSRP calculation
                        sim_rsrp = TX_POWER_DBM + TOTAL_ANTENNA_GAIN_DB - sim_path_loss
                        actual_rsrp = TX_POWER_DBM + TOTAL_ANTENNA_GAIN_DB - actual_path_loss

                        # RSSI ≈ RSRP + noise contribution (simplified)
                        sim_rssi = 10 * math.log10(10**(sim_rsrp/10) + 10**(NOISE_FLOOR_DBM/10))
                        actual_rssi = 10 * math.log10(10**(actual_rsrp/10) + 10**(NOISE_FLOOR_DBM/10))
                        
                        # Calculate RSRP accuracy if dataset values available
                        rsrp_error = None
                        rsrp_accuracy = None
                        
                        if dataset_rsrp is not None:
                            rsrp_error = sim_rsrp - dataset_rsrp
                            rsrp_error_pct = (rsrp_error / abs(dataset_rsrp) * 100) if dataset_rsrp != 0 else 0
                            rsrp_accuracy = max(0, 100 - abs(rsrp_error_pct))
                        
                        # Speed metrics
                        actual_src_speed_kmh = wp_data['source_speed_kmh']
                        actual_dst_speed_kmh = wp_data['dest_speed_kmh']
                        simulated_src_speed_kmh = src_speed * 3.6
                        simulated_dst_speed_kmh = dst_speed * 3.6
                        
                        analysis_entry = {
                            'waypoint': current_waypoint,
                            'step': step,
                            # Distance
                            'actual_distance_m': actual_distance,
                            'simulated_distance_m': simulated_distance,
                            'distance_error_m': distance_error,
                            'distance_error_pct': distance_error_pct,
                            'distance_accuracy_pct': distance_accuracy,
                            # Path Loss
                            'actual_path_loss_db': actual_path_loss,
                            'simulated_path_loss_db': sim_path_loss,
                            'path_loss_error_db': path_loss_error,
                            'path_loss_error_pct': path_loss_error_pct,
                            'path_loss_accuracy_pct': path_loss_accuracy,
                            'path_loss_model': model,
                            # SNR
                            'actual_snr_db': actual_snr,
                            'simulated_snr_db': sim_snr,
                            'snr_error_db': snr_error,
                            'snr_error_pct': snr_error_pct,
                            'snr_accuracy_pct': snr_accuracy,
                            # RSRP
                            'actual_rsrp_dbm': actual_rsrp,
                            'simulated_rsrp_dbm': sim_rsrp,
                            # RSSI
                            'actual_rssi_dbm': actual_rssi,
                            'simulated_rssi_dbm': sim_rssi,
                            # PRR
                            'actual_prr_pct': actual_prr,
                            'simulated_prr_pct': sim_prr,
                            'prr_error_pct': prr_error,
                            'prr_accuracy_pct': prr_accuracy,
                            # Speed
                            'actual_speed_src_kmh': actual_src_speed_kmh,
                            'simulated_speed_src_kmh': simulated_src_speed_kmh,
                            'actual_speed_dst_kmh': actual_dst_speed_kmh,
                            'simulated_speed_dst_kmh': simulated_dst_speed_kmh,
                            # Config
                            'calibration_enabled': self.calibration_enabled.get(),
                            'realistic_speed_enabled': self.use_realistic_speed.get()
                        }
                        
                        # Add dataset communication parameters if available
                        if dataset_snr is not None:
                            analysis_entry['dataset_snr_db'] = dataset_snr
                            analysis_entry['dataset_snr_vs_calculated'] = dataset_snr - actual_snr
                        if dataset_rsrp is not None:
                            analysis_entry['dataset_rsrp_dbm'] = dataset_rsrp
                            if rsrp_error is not None:
                                analysis_entry['rsrp_error_dbm'] = rsrp_error
                                analysis_entry['rsrp_accuracy_pct'] = rsrp_accuracy
                        
                        communication_analysis.append(analysis_entry)
                
                # Log progress periodically
                if step % 500 == 0:
                    self.log_message(f"📊 Step {step}: Vehicles={len(vehicles)}, Source={source_active}, Dest={dest_active}, WP={current_waypoint}")
                
                if not source_active and not dest_active and step > 200:
                    self.log_message(f"⚠️ No vehicles active after step {step}. Simulation may have ended.")
                    break
                
                time.sleep(0.01)
            
            # Final statistics and reporting
            self.log_message("\n" + "="*70)
            self.log_message("SIMULATION COMPLETE - GENERATING COMMUNICATION REPORTS")
            self.log_message("="*70)
            
            if communication_analysis:
                self.log_message("\n📊 Saving comprehensive communication analysis...")
                
                analysis_df = pd.DataFrame(communication_analysis)
                
                # Save to MAIN project directory
                csv_file = os.path.join(original_dir, f'{SCENARIO_NAME}_communication_analysis.csv')
                
                try:
                    analysis_df.to_csv(csv_file, index=False)
                    self.log_message(f"\n💾 Communication CSV saved to:")
                    self.log_message(f"   {os.path.abspath(csv_file)}")
                    self.log_message(f"   📂 Location: Main project folder")
                    self.log_message(f"   📊 Rows: {len(analysis_df)}")
                except Exception as e:
                    self.log_message(f"\n❌ Error saving CSV: {e}")
                
                # Calculate overall metrics
                distance_accuracies = analysis_df['distance_accuracy_pct']
                path_loss_accuracies = analysis_df['path_loss_accuracy_pct']
                snr_accuracies = analysis_df['snr_accuracy_pct']
                prr_accuracies = analysis_df['prr_accuracy_pct']
                
                path_loss_errors = analysis_df['path_loss_error_db']
                snr_errors = analysis_df['snr_error_db']
                
                overall_metrics = {
                    'simulation_settings': {
                        'num_waypoints': NUM_WAYPOINTS,
                        'calibration_enabled': self.calibration_enabled.get(),
                        'calibration_type': 'adaptive' if self.calibration_enabled.get() else 'none',
                        'realistic_speed_enabled': self.use_realistic_speed.get(),
                        'path_loss_model': self.path_loss_model.get(),
                        'use_all_waypoints': self.use_all_waypoints.get(),
                        'total_steps': int(step)
                    },
                    'v2v_parameters': {
                        'carrier_frequency_ghz': CARRIER_FREQUENCY_GHZ,
                        'tx_power_dbm': TX_POWER_DBM,
                        'noise_floor_dbm': NOISE_FLOOR_DBM,
                        'tx_antenna_gain_db': TX_ANTENNA_GAIN_DB,
                        'rx_antenna_gain_db': RX_ANTENNA_GAIN_DB,
                        'total_antenna_gain_db': TOTAL_ANTENNA_GAIN_DB,
                        'bandwidth_mhz': BANDWIDTH_MHZ
                    },
                    'distance_accuracy': {
                        'mean_accuracy_pct': float(distance_accuracies.mean()),
                        'median_accuracy_pct': float(distance_accuracies.median()),
                        'std_dev_pct': float(distance_accuracies.std())
                    },
                    'path_loss_accuracy': {
                        'mean_accuracy_pct': float(path_loss_accuracies.mean()),
                        'median_accuracy_pct': float(path_loss_accuracies.median()),
                        'mean_error_db': float(path_loss_errors.mean()),
                        'mean_absolute_error_db': float(path_loss_errors.abs().mean()),
                        'rmse_db': float((path_loss_errors**2).mean()**0.5),
                        'std_dev_db': float(path_loss_errors.std())
                    },
                    'snr_accuracy': {
                        'mean_accuracy_pct': float(snr_accuracies.mean()),
                        'mean_error_db': float(snr_errors.mean()),
                        'mean_absolute_error_db': float(snr_errors.abs().mean()),
                        'rmse_db': float((snr_errors**2).mean()**0.5),
                        'std_dev_db': float(snr_errors.std())
                    },
                    'prr_accuracy': {
                        'mean_accuracy_pct': float(prr_accuracies.mean()),
                        'median_accuracy_pct': float(prr_accuracies.median()),
                        'std_dev_pct': float(prr_accuracies.std())
                    },
                    'communication_range': {
                        'estimated_range_m': float(calculate_communication_range(
                            TX_POWER_DBM, NOISE_FLOOR_DBM, 10,
                            self.path_loss_model.get(), CARRIER_FREQUENCY_GHZ,
                            TX_ANTENNA_GAIN_DB, RX_ANTENNA_GAIN_DB))
                    }
                }
                
                # Save JSON summary
                json_file = os.path.join(original_dir, f'{SCENARIO_NAME}_communication_summary.json')
                
                try:
                    with open(json_file, 'w') as f:
                        json.dump(overall_metrics, f, indent=2)
                    self.log_message(f"💾 Summary JSON saved to:")
                    self.log_message(f"   {os.path.abspath(json_file)}")
                except Exception as e:
                    self.log_message(f"❌ Error saving JSON: {e}")
                
                # Display comprehensive report
                self.log_message("\n" + "="*70)
                self.log_message("DIGITAL TWIN COMMUNICATION ACCURACY REPORT")
                self.log_message("="*70)
                
                self.log_message(f"\n📊 Distance Accuracy:")
                self.log_message(f"   Mean Accuracy: {overall_metrics['distance_accuracy']['mean_accuracy_pct']:.2f}%")
                self.log_message(f"   Median Accuracy: {overall_metrics['distance_accuracy']['median_accuracy_pct']:.2f}%")
                self.log_message(f"   Std Deviation: {overall_metrics['distance_accuracy']['std_dev_pct']:.2f}%")
                
                self.log_message(f"\n📡 Path Loss Accuracy ({self.path_loss_model.get()}):")
                self.log_message(f"   Mean Accuracy: {overall_metrics['path_loss_accuracy']['mean_accuracy_pct']:.2f}%")
                self.log_message(f"   Median Accuracy: {overall_metrics['path_loss_accuracy']['median_accuracy_pct']:.2f}%")
                self.log_message(f"   Mean Absolute Error: {overall_metrics['path_loss_accuracy']['mean_absolute_error_db']:.2f} dB")
                self.log_message(f"   RMSE: {overall_metrics['path_loss_accuracy']['rmse_db']:.2f} dB")
                
                self.log_message(f"\n📶 SNR Accuracy:")
                self.log_message(f"   Mean Accuracy: {overall_metrics['snr_accuracy']['mean_accuracy_pct']:.2f}%")
                self.log_message(f"   Mean Absolute Error: {overall_metrics['snr_accuracy']['mean_absolute_error_db']:.2f} dB")
                self.log_message(f"   RMSE: {overall_metrics['snr_accuracy']['rmse_db']:.2f} dB")
                
                self.log_message(f"\n📨 Packet Reception Rate Accuracy:")
                self.log_message(f"   Mean Accuracy: {overall_metrics['prr_accuracy']['mean_accuracy_pct']:.2f}%")
                self.log_message(f"   Median Accuracy: {overall_metrics['prr_accuracy']['median_accuracy_pct']:.2f}%")
                
                self.log_message(f"\n📏 Estimated Communication Range:")
                self.log_message(f"   Max Range (SNR > 10dB): {overall_metrics['communication_range']['estimated_range_m']:.1f}m")
                
                # Dataset communication parameters comparison
                if 'dataset_snr_db' in analysis_df.columns:
                    dataset_snr_mean = analysis_df['dataset_snr_db'].mean()
                    calculated_snr_mean = analysis_df['actual_snr_db'].mean()
                    snr_diff = dataset_snr_mean - calculated_snr_mean
                    
                    self.log_message(f"\n📊 Dataset vs Calculated Communication Parameters:")
                    self.log_message(f"   SNR:")
                    self.log_message(f"      Dataset (mean): {dataset_snr_mean:.2f} dB")
                    self.log_message(f"      Calculated (mean): {calculated_snr_mean:.2f} dB")
                    self.log_message(f"      Difference: {snr_diff:.2f} dB")
                
                if 'dataset_rsrp_dbm' in analysis_df.columns:
                    dataset_rsrp_mean = analysis_df['dataset_rsrp_dbm'].mean()
                    simulated_rsrp_mean = analysis_df['simulated_rsrp_dbm'].mean()
                    self.log_message(f"   RSRP:")
                    self.log_message(f"      Dataset (mean): {dataset_rsrp_mean:.2f} dBm")
                    self.log_message(f"      Simulated (mean): {simulated_rsrp_mean:.2f} dBm")
                    
                    if 'rsrp_accuracy_pct' in analysis_df.columns:
                        rsrp_acc_mean = analysis_df['rsrp_accuracy_pct'].mean()
                        rsrp_error_mean = analysis_df['rsrp_error_dbm'].mean()
                        self.log_message(f"      Accuracy: {rsrp_acc_mean:.2f}%")
                        self.log_message(f"      Error: {rsrp_error_mean:.2f} dBm")
                
                # Overall assessment
                dist_acc = overall_metrics['distance_accuracy']['mean_accuracy_pct']
                pl_acc = overall_metrics['path_loss_accuracy']['mean_accuracy_pct']
                snr_acc = overall_metrics['snr_accuracy']['mean_accuracy_pct']
                prr_acc = overall_metrics['prr_accuracy']['mean_accuracy_pct']
                
                overall_comm_acc = (dist_acc + pl_acc + snr_acc + prr_acc) / 4
                
                if overall_comm_acc >= 80:
                    assessment = "EXCELLENT ✅"
                elif overall_comm_acc >= 70:
                    assessment = "GOOD ✓"
                elif overall_comm_acc >= 60:
                    assessment = "FAIR ⚠️"
                else:
                    assessment = "NEEDS IMPROVEMENT ❌"
                
                self.log_message(f"\n📊 Overall Communication Digital Twin Quality: {overall_comm_acc:.2f}% - {assessment}")
                
                self.log_message("\n" + "="*70)
                self.log_message(f"✅ Analysis complete! Files saved to:")
                self.log_message(f"   📄 CSV: {SCENARIO_NAME}_communication_analysis.csv")
                self.log_message(f"   📄 JSON: {SCENARIO_NAME}_communication_summary.json")
                self.log_message(f"   📂 Location: {original_dir}")
                self.log_message("="*70)
            else:
                self.log_message("\n⚠️ No communication analysis data collected")
            
            self.log_message("\n✅ Simulation complete!")
            
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
            self.simulation_running = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.progress_var.set(0)
    
    def run(self):
        """Start GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    app = V2VCommunicationDigitalTwinVehicle12()
    app.run()

