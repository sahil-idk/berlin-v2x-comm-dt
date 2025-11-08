#!/usr/bin/env python3
"""
V2V Communication Digital Twin - Complete Solution
Extends baseline with path loss models and communication parameter validation

Features:
- Inter-vehicular distance simulation (78% accuracy baseline)
- Path loss models (FSPL + 3GPP Urban Macro)
- SNR calculation
- Packet Reception Rate (PRR) estimation
- Communication parameter accuracy validation
- Comprehensive reporting
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
CALIBRATION_FACTOR = 0.607  # Baseline calibration for first_200 dataset

def get_adaptive_calibration(actual_distance_m, dataset_type="continuous"):
    """Adaptive calibration based on distance ranges and dataset type"""
    if dataset_type == "baseline":
        return CALIBRATION_FACTOR  # Use baseline calibration
    
    # For continuous dataset, use distance-based calibration
    if actual_distance_m < 15:
        return 1.0000  # Short distances - no calibration needed
    elif actual_distance_m < 25:
        return 1.0000  # Medium distances - no calibration needed  
    elif actual_distance_m < 40:
        return 1.0000  # Long distances - no calibration needed
    else:
        return 1.0000  # Very long distances - no calibration needed

# V2V Communication Parameters (CORRECTED for SNR accuracy)
CARRIER_FREQUENCY_GHZ = 5.9  # V2V frequency (5.9 GHz)
CARRIER_FREQUENCY_MHZ = 5900
TX_POWER_DBM = 23  # ✅ FIXED: Standard V2V/PC5 Sidelink TX power (was 20)
BANDWIDTH_MHZ = 10  # Channel bandwidth
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

# ============================================================================
# COMMUNICATION MODELS
# ============================================================================

def calculate_fspl(distance_m, frequency_ghz=5.9):
    """
    Calculate Free Space Path Loss (FSPL)
    
    FSPL(dB) = 20*log10(d) + 20*log10(f) + 32.45
    where d is in meters, f is in MHz
    """
    if distance_m <= 0:
        return 0
    
    frequency_mhz = frequency_ghz * 1000
    fspl_db = 20 * math.log10(distance_m) + 20 * math.log10(frequency_mhz) + 32.45
    return fspl_db

def calculate_3gpp_urban_macro_path_loss(distance_m, frequency_ghz=5.9):
    """
    Calculate path loss using 3GPP Urban Macro model
    
    PL = 38.46 + 20*log10(d) + 20*log10(f/5)
    where d is in meters, f is in GHz
    """
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
    """
    Calculate Packet Reception Rate (PRR) from SNR
    
    Uses sigmoid model:
    PRR = 1 / (1 + exp(-k*(SNR - SNR_threshold)))
    
    Typical V2V thresholds:
    - SNR > 10 dB: Excellent (PRR > 95%)
    - SNR 5-10 dB: Good (PRR 70-95%)
    - SNR 0-5 dB: Fair (PRR 30-70%)
    - SNR < 0 dB: Poor (PRR < 30%)
    """
    snr_threshold = 5.0  # dB
    k = 0.5  # Steepness factor
    
    prr = 1.0 / (1.0 + math.exp(-k * (snr_db - snr_threshold)))
    return prr * 100  # Return as percentage

def calculate_communication_range(tx_power_dbm, noise_floor_dbm, snr_threshold_db=10,
                                 model='FSPL', frequency_ghz=5.9,
                                 tx_antenna_gain_db=3, rx_antenna_gain_db=3):
    """
    Calculate maximum communication range

    Range where SNR drops below threshold
    """
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

def extend_route_to_target_distance(net, initial_route, target_distance_m, max_attempts=100):
    """
    Extend a route by adding edges until it reaches target distance.
    This ensures vehicles cover the full GPS trajectory distance.
    """
    if not initial_route:
        return initial_route
    
    # Calculate initial route distance
    current_distance = 0
    for edge_id in initial_route:
        try:
            edge = net.getEdge(edge_id)
            current_distance += edge.getLength()
        except:
            pass
    
    if current_distance >= target_distance_m:
        return initial_route  # Already long enough
    
    extended_route = initial_route.copy()
    visited = set(extended_route)
    attempts = 0
    
    while current_distance < target_distance_m and attempts < max_attempts:
        attempts += 1
        
        try:
            last_edge = net.getEdge(extended_route[-1])
            outgoing = last_edge.getOutgoing()
            
            if not outgoing:
                break  # Dead end
            
            # Choose longest unvisited outgoing edge
            candidates = []
            for next_edge in outgoing.keys():
                edge_id = next_edge.getID()
                if edge_id not in visited:
                    candidates.append((next_edge, next_edge.getLength()))
            
            if not candidates:
                # All outgoing edges visited, allow revisiting
                candidates = [(e, e.getLength()) for e in outgoing.keys()]
            
            if not candidates:
                break
            
            # Pick the longest edge to maximize coverage
            next_edge = max(candidates, key=lambda x: x[1])[0]
            edge_id = next_edge.getID()
            
            extended_route.append(edge_id)
            visited.add(edge_id)
            current_distance += next_edge.getLength()
            
        except Exception as e:
            break  # Error accessing edges
    
    return extended_route

def find_optimal_path_through_waypoints(net, waypoints_df, vehicle_type='source', sample_step=None):
    """Find connected path through waypoints"""
    edges_with_positions = []
    
    # Sample waypoints intelligently based on dataset size
    # Use denser sampling to create longer routes that cover full GPS trajectory
    num_waypoints = len(waypoints_df)
    
    if sample_step is None:
        # Default sampling logic
        if num_waypoints <= 50:
            sample_step = 1  # Use all waypoints
        elif num_waypoints <= 100:
            sample_step = 1  # Use all for better coverage
        elif num_waypoints <= 200:
            sample_step = 2  # Use every 2nd (was 4th - now denser for longer routes)
        else:
            sample_step = 3  # Use every 3rd (was 5th - now denser)
    
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

# ============================================================================
# MAIN GUI CLASS
# ============================================================================

class V2VCommunicationDigitalTwin:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("V2V Communication Digital Twin")
        self.root.geometry("700x700")
        
        self.simulation_running = False
        self.simulation_thread = None
        
        self.num_waypoints = tk.IntVar(value=50)
        self.calibration_enabled = tk.BooleanVar(value=True)
        self.use_realistic_speed = tk.BooleanVar(value=True)
        self.path_loss_model = tk.StringVar(value='FSPL')
        self.dataset_file = tk.StringVar(value='vehicle_2_4_first_200.csv')
        self.use_all_waypoints = tk.BooleanVar(value=False)  # New option
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup GUI"""
        # Title
        title_label = tk.Label(self.root, text="V2V Communication Digital Twin", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        info_label = tk.Label(self.root, text="Distance + Path Loss + SNR + PRR Validation", 
                             font=("Arial", 10), fg="blue")
        info_label.pack()
        
        # Configuration Frame
        config_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(config_frame, text="Waypoints:").grid(row=0, column=0, sticky="w")
        ttk.Scale(config_frame, from_=5, to=1000, variable=self.num_waypoints, 
                 orient="horizontal", length=200).grid(row=0, column=1)
        ttk.Label(config_frame, textvariable=self.num_waypoints).grid(row=0, column=2)
        
        # Dataset selector
        ttk.Label(config_frame, text="Dataset:").grid(row=1, column=0, sticky="w")
        dataset_combo = ttk.Combobox(config_frame, textvariable=self.dataset_file, 
                                    values=['vehicle_2_4_first_200.csv',
                                            'vehicle_2_4_continuous_200.csv',
                                            'vehicle_2_4_continuous_300.csv',
                                            'vehicle_2_4_continuous_400.csv',
                                            'vehicle_2_4_continuous_500.csv'],
                                    state='readonly', width=28)
        dataset_combo.grid(row=1, column=1, columnspan=2, sticky="ew")
        
        ttk.Checkbutton(config_frame, text="✅ Use Realistic Speed from Dataset", 
                       variable=self.use_realistic_speed).grid(row=2, column=0, columnspan=3, sticky="w")
        
        ttk.Checkbutton(config_frame, text="✅ Apply Calibration (0.607)", 
                       variable=self.calibration_enabled).grid(row=3, column=0, columnspan=3, sticky="w")
        
        ttk.Checkbutton(config_frame, text="✅ Use All Waypoints (Smart Sampling)", 
                       variable=self.use_all_waypoints).grid(row=4, column=0, columnspan=3, sticky="w")
        
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
        
        params_text = f"Frequency: {CARRIER_FREQUENCY_GHZ} GHz | Tx Power: {TX_POWER_DBM} dBm | Noise: {NOISE_FLOOR_DBM} dBm"
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
        """Main simulation with communication models"""
        try:
            self.log_message("="*70)
            self.log_message("V2V COMMUNICATION DIGITAL TWIN")
            self.log_message("="*70)
            self.log_message(f"🚗 Speed Mode: {'REALISTIC (from GPS data)' if self.use_realistic_speed.get() else 'CONSTANT (15 m/s)'}")
            self.log_message(f"📊 Calibration: {'ENABLED (Adaptive)' if self.calibration_enabled.get() else 'DISABLED'}")
            self.log_message(f"📡 Path Loss Model: {self.path_loss_model.get()}")
            self.log_message(f"🎯 Waypoint Sampling: {'SMART SAMPLING' if self.use_all_waypoints.get() else 'INTELLIGENT SAMPLING'}")
            
            NUM_WAYPOINTS = self.num_waypoints.get()
            # Dynamic simulation steps based on waypoints
            # Routes follow GPS trajectory naturally without artificial extension
            SIMULATION_STEPS = max(8000, NUM_WAYPOINTS * 60)  # Balanced for GPS-based routes
            
            original_dir = os.getcwd()
            
            # Load network
            os.chdir('berlin-sumo-closed-netwokr')
            self.log_message("\n📍 Loading SUMO network...")
            net = sumolib.net.readNet('osm.net.xml.gz')
            self.log_message(f"✅ Network loaded: {len(net.getEdges())} edges")
            
            # Load GPS data from selected dataset
            dataset_name = self.dataset_file.get()
            self.log_message(f"\n📍 Loading GPS data from {dataset_name}...")
            df = pd.read_csv(f'../{dataset_name}')
            waypoints_df = df.head(NUM_WAYPOINTS)
            self.log_message(f"✅ Loaded {len(waypoints_df)} waypoints from {dataset_name}")
            
            # Check if dataset has actual communication parameters
            has_snr = 'SNR' in waypoints_df.columns
            has_rsrp = 'RSRP' in waypoints_df.columns
            has_rssi = 'RSSI' in waypoints_df.columns
            
            if has_snr:
                self.log_message(f"✅ Dataset contains SNR values (mean: {waypoints_df['SNR'].mean():.2f} dB)")
            if has_rsrp:
                self.log_message(f"✅ Dataset contains RSRP values (mean: {waypoints_df['RSRP'].mean():.2f} dBm)")
            if has_rssi:
                self.log_message(f"✅ Dataset contains RSSI values (mean: {waypoints_df['RSSI'].mean():.2f} dBm)")
            
            # Find routes
            self.log_message(f"\n📍 Computing routes for {NUM_WAYPOINTS} waypoints...")
            
            # Determine sampling for route generation
            if self.use_all_waypoints.get():
                # Use all waypoints but cap at reasonable limit to prevent SUMO crashes
                if NUM_WAYPOINTS <= 100:
                    sample_step = 1  # Use all waypoints for small datasets
                    self.log_message(f"📊 Using ALL waypoints for route generation (no sampling)")
                else:
                    # For large datasets, use intelligent sampling to prevent SUMO crashes
                    sample_step = max(2, NUM_WAYPOINTS // 50)  # Cap at ~50 route points
                    self.log_message(f"📊 Large dataset detected ({NUM_WAYPOINTS} waypoints)")
                    self.log_message(f"📊 Using every {sample_step}th waypoint to prevent SUMO crashes (~{NUM_WAYPOINTS // sample_step} route points)")
            else:
                # Use intelligent sampling based on dataset size
                if NUM_WAYPOINTS <= 50:
                    sample_step = 1
                elif NUM_WAYPOINTS <= 100:
                    sample_step = 1  # Use all for better coverage
                elif NUM_WAYPOINTS <= 200:
                    sample_step = 2  # Denser sampling for longer routes
                else:
                    sample_step = 3  # Denser sampling
                
                route_waypoints = NUM_WAYPOINTS // sample_step
                self.log_message(f"📊 Using every {sample_step}th waypoint for route (~{route_waypoints} route points)")
            
            source_route, _ = find_optimal_path_through_waypoints(net, waypoints_df, 'source', sample_step)
            dest_route, _ = find_optimal_path_through_waypoints(net, waypoints_df, 'destination', sample_step)
            
            # Validate routes to prevent SUMO crashes
            if len(source_route) == 0 or len(dest_route) == 0:
                self.log_message(f"❌ ERROR: Could not generate routes")
                self.log_message(f"⚠️ Source route: {len(source_route)} edges")
                self.log_message(f"⚠️ Destination route: {len(dest_route)} edges")
                self.log_message(f"⚠️ Try reducing waypoints or using different sampling")
                return
            
            # Check for reasonable route complexity
            if len(source_route) > 50 or len(dest_route) > 50:
                self.log_message(f"⚠️ WARNING: Complex routes detected")
                self.log_message(f"⚠️ Source route: {len(source_route)} edges")
                self.log_message(f"⚠️ Destination route: {len(dest_route)} edges")
                self.log_message(f"⚠️ This may cause SUMO performance issues")
            
            # Calculate initial route distances
            source_route_dist = sum([net.getEdge(edge_id).getLength() for edge_id in source_route])
            dest_route_dist = sum([net.getEdge(edge_id).getLength() for edge_id in dest_route])
            
            self.log_message(f"✅ Initial source route: {len(source_route)} edges ({source_route_dist:.1f}m)")
            self.log_message(f"✅ Initial destination route: {len(dest_route)} edges ({dest_route_dist:.1f}m)")
            
            # NOTE: Route extension disabled - causes vehicles to backtrack/loop
            # Instead, we rely on natural GPS waypoint-based routing
            # The initial route follows GPS trajectory correctly
            
            self.log_message(f"\n📏 Route coverage: Source {source_route_dist:.0f}m, Dest {dest_route_dist:.0f}m")
            self.log_message(f"⚠️ Note: Routes may be shorter than full GPS trajectory ({NUM_WAYPOINTS} points)")
            self.log_message(f"   This ensures accurate distance matching without backtracking")
            
            # Validate routes
            if len(source_route) == 0:
                self.log_message(f"❌ ERROR: Could not generate source route")
                self.log_message(f"⚠️ The GPS waypoints may be too far apart or outside the network")
                self.log_message(f"⚠️ Current: {NUM_WAYPOINTS} waypoints from {dataset_name}")
                self.log_message(f"💡 Recommended: Try 50-100 waypoints for this dataset")
                os.chdir(original_dir)
                return
            
            if len(dest_route) == 0:
                self.log_message(f"❌ ERROR: Could not generate destination route")
                self.log_message(f"⚠️ The GPS waypoints may be too far apart or outside the network")
                self.log_message(f"⚠️ Current: {NUM_WAYPOINTS} waypoints from {dataset_name}")
                self.log_message(f"💡 Recommended: Try 50-100 waypoints for this dataset")
                os.chdir(original_dir)
                return
            
            # Extend if needed
            if len(source_route) < 2:
                try:
                    edge = net.getEdge(source_route[0])
                    outgoing = edge.getOutgoing()
                    if outgoing:
                        source_route.append(list(outgoing.keys())[0].getID())
                        self.log_message(f"⚠️ Extended short source route to {len(source_route)} edges")
                except Exception as e:
                    self.log_message(f"⚠️ Could not extend source route: {e}")
            
            if len(dest_route) < 2:
                try:
                    edge = net.getEdge(dest_route[0])
                    outgoing = edge.getOutgoing()
                    if outgoing:
                        dest_route.append(list(outgoing.keys())[0].getID())
                        self.log_message(f"⚠️ Extended short destination route to {len(dest_route)} edges")
                except Exception as e:
                    self.log_message(f"⚠️ Could not extend destination route: {e}")
            
            # Create route file
            self.log_message("\n📍 Creating route file...")
            route_file = 'v2v_communication_routes.rou.xml'
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
            config_file = 'v2v_communication.sumocfg'
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
            
            # Start SUMO
            self.log_message("\n🚀 Starting SUMO-GUI...")
            sumo_cmd = ["sumo-gui", "-c", config_file, "--start", "--quit-on-end"]
            traci.start(sumo_cmd)
            time.sleep(3)
            
            # Add POIs
            self.log_message("📍 Adding waypoint markers...")
            waypoint_coords = []
            for idx, row in waypoints_df.iterrows():
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
                
                # Add actual communication params if available
                if has_snr:
                    wp_data['SNR'] = row['SNR']
                if has_rsrp:
                    wp_data['RSRP'] = row['RSRP']
                if 'RSSI' in waypoints_df.columns and pd.notna(row['RSSI']):
                    wp_data['RSSI'] = row['RSSI']
                if 'NOISE POWER' in waypoints_df.columns and pd.notna(row['NOISE POWER']):
                    wp_data['NOISE POWER'] = row['NOISE POWER']
                if 'Rx_power' in waypoints_df.columns and pd.notna(row['Rx_power']):
                    wp_data['Rx_power'] = row['Rx_power']
                
                waypoint_coords.append(wp_data)
            
            self.log_message(f"✅ Added {len(waypoint_coords)*2} POIs")
            
            # Run simulation
            self.log_message("\n🎯 Starting communication digital twin...")
            self.log_message("-"*70)
            
            step = 0
            source_active = False
            dest_active = False
            last_log_step = 0
            
            distances_raw = []
            distances_calibrated = []
            source_progress = []
            dest_progress = []
            
            current_waypoint = 0
            
            # Communication analysis storage
            communication_analysis = []
            
            while step < SIMULATION_STEPS and self.simulation_running:
                try:
                    traci.simulationStep()
                    step += 1
                except traci.exceptions.FatalTraCIError as e:
                    self.log_message(f"❌ SUMO Connection Error: {e}")
                    self.log_message(f"⚠️ This usually means:")
                    self.log_message(f"   - Route file is too complex for SUMO")
                    self.log_message(f"   - Too many waypoints causing route generation issues")
                    self.log_message(f"   - SUMO ran out of memory")
                    self.log_message(f"💡 Try reducing waypoints or using intelligent sampling")
                    break
                except Exception as e:
                    self.log_message(f"❌ Simulation Error: {e}")
                    break
                
                progress = min(100, (step / SIMULATION_STEPS) * 100)
                self.progress_var.set(progress)
                
                vehicles = traci.vehicle.getIDList()
                
                # Source vehicle
                if "v2v_source" in vehicles:
                    if not source_active:
                        self.log_message(f"✅ Step {step}: Source vehicle active")
                        source_active = True
                    
                    src_pos = traci.vehicle.getPosition("v2v_source")
                    src_speed = traci.vehicle.getSpeed("v2v_source")
                    
                    # SET REALISTIC SPEED
                    if self.use_realistic_speed.get() and current_waypoint < len(waypoint_coords):
                        target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['source_speed_kmh'])
                        traci.vehicle.setSpeed("v2v_source", target_speed_ms)
                    
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
                if "v2v_dest" in vehicles:
                    if not dest_active:
                        self.log_message(f"✅ Step {step}: Destination vehicle active")
                        dest_active = True
                    
                    dst_pos = traci.vehicle.getPosition("v2v_dest")
                    dst_speed = traci.vehicle.getSpeed("v2v_dest")
                    
                    # SET REALISTIC SPEED
                    if self.use_realistic_speed.get() and current_waypoint < len(waypoint_coords):
                        target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['dest_speed_kmh'])
                        traci.vehicle.setSpeed("v2v_dest", target_speed_ms)
                    
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
                
                # Calculate distances and communication parameters
                if source_active and dest_active:
                    raw_distance = calculate_distance(src_pos, dst_pos)
                    distances_raw.append(raw_distance)
                    
                    if self.calibration_enabled.get():
                        # Determine dataset type based on filename
                        dataset_type = "continuous" if "continuous" in self.dataset_file.get() else "baseline"
                        
                        # Get actual distance for adaptive calibration
                        actual_distance = None
                        if current_waypoint < len(waypoint_coords):
                            actual_distance = calculate_distance(
                                waypoint_coords[current_waypoint]['source'], 
                                waypoint_coords[current_waypoint]['dest']
                            )
                        
                        # Use adaptive calibration
                        if actual_distance is not None:
                            calibration_factor = get_adaptive_calibration(actual_distance, dataset_type)
                        else:
                            calibration_factor = CALIBRATION_FACTOR  # Fallback
                        
                        calibrated_distance = raw_distance * calibration_factor
                        distances_calibrated.append(calibrated_distance)
                    else:
                        distances_calibrated.append(raw_distance)
                    
                    # Update current waypoint
                    prev_waypoint = current_waypoint
                    if source_progress and dest_progress:
                        current_waypoint = min(source_progress[-1], dest_progress[-1])
                    
                    # Calculate communication parameters when we move to a new waypoint
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
                        
                        # Get dataset communication params if available (using correct column names)
                        dataset_snr = wp_data.get('SNR', None)
                        dataset_rsrp = wp_data.get('RSRP', None)
                        dataset_rssi = wp_data.get('RSSI', None)
                        dataset_noise_power = wp_data.get('NOISE POWER', None)
                        dataset_rx_power = wp_data.get('Rx_power', None)
                        
                        # Calculate RSRP and RSSI from simulated and actual distances
                        # RSRP ≈ Tx_Power - Path_Loss
                        sim_rsrp = TX_POWER_DBM - sim_path_loss
                        actual_rsrp = TX_POWER_DBM - actual_path_loss
                        
                        # RSSI ≈ RSRP + noise contribution (simplified)
                        # RSSI = 10*log10(10^(RSRP/10) + 10^(Noise/10))
                        sim_rssi = 10 * math.log10(10**(sim_rsrp/10) + 10**(NOISE_FLOOR_DBM/10))
                        actual_rssi = 10 * math.log10(10**(actual_rsrp/10) + 10**(NOISE_FLOOR_DBM/10))
                        
                        # Calculate RSRP and RSSI accuracy if dataset values available
                        rsrp_error = None
                        rsrp_accuracy = None
                        rssi_error = None
                        rssi_accuracy = None
                        
                        if dataset_rsrp is not None:
                            rsrp_error = sim_rsrp - dataset_rsrp
                            rsrp_error_pct = (rsrp_error / abs(dataset_rsrp) * 100) if dataset_rsrp != 0 else 0
                            rsrp_accuracy = max(0, 100 - abs(rsrp_error_pct))
                        
                        if dataset_rssi is not None:
                            rssi_error = sim_rssi - dataset_rssi
                            rssi_error_pct = (rssi_error / abs(dataset_rssi) * 100) if dataset_rssi != 0 else 0
                            rssi_accuracy = max(0, 100 - abs(rssi_error_pct))
                        
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
                        if dataset_rssi is not None:
                            analysis_entry['dataset_rssi_dbm'] = dataset_rssi
                            if rssi_error is not None:
                                analysis_entry['rssi_error_dbm'] = rssi_error
                                analysis_entry['rssi_accuracy_pct'] = rssi_accuracy
                        if dataset_noise_power is not None:
                            analysis_entry['dataset_noise_power'] = dataset_noise_power
                        if dataset_rx_power is not None:
                            analysis_entry['dataset_rx_power_dbm'] = dataset_rx_power
                        
                        communication_analysis.append(analysis_entry)
                    
                    # Log every 200 steps
                    if step - last_log_step >= 200:
                        avg_dist = sum(distances_calibrated[-200:]) / len(distances_calibrated[-200:])

                        # Calculate current communication params
                        temp_snr, temp_pl = calculate_snr(avg_dist, TX_POWER_DBM, NOISE_FLOOR_DBM,
                                                         self.path_loss_model.get(), CARRIER_FREQUENCY_GHZ,
                                                         TX_ANTENNA_GAIN_DB, RX_ANTENNA_GAIN_DB)
                        temp_prr = calculate_prr(temp_snr)
                        
                        # Calculate progress percentage
                        progress_pct = (current_waypoint / NUM_WAYPOINTS) * 100 if NUM_WAYPOINTS > 0 else 0
                        
                        self.log_message(f"📊 Step {step}: Dist={avg_dist:.2f}m, PL={temp_pl:.1f}dB, "
                                        f"SNR={temp_snr:.1f}dB, PRR={temp_prr:.1f}%, "
                                        f"WP={current_waypoint}/{NUM_WAYPOINTS} ({progress_pct:.1f}%)")
                        last_log_step = step
                
                if not source_active and not dest_active and step > 100:
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
                csv_file = os.path.join(original_dir, 'v2v_communication_analysis.csv')
                
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
                        'antenna_gain_db': ANTENNA_GAIN_DB,
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
                json_file = os.path.join(original_dir, 'v2v_communication_summary.json')
                
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
                
                if 'dataset_rssi_dbm' in analysis_df.columns:
                    dataset_rssi_mean = analysis_df['dataset_rssi_dbm'].mean()
                    simulated_rssi_mean = analysis_df['simulated_rssi_dbm'].mean()
                    self.log_message(f"   RSSI:")
                    self.log_message(f"      Dataset (mean): {dataset_rssi_mean:.2f} dBm")
                    self.log_message(f"      Simulated (mean): {simulated_rssi_mean:.2f} dBm")
                    
                    if 'rssi_accuracy_pct' in analysis_df.columns:
                        rssi_acc_mean = analysis_df['rssi_accuracy_pct'].mean()
                        rssi_error_mean = analysis_df['rssi_error_dbm'].mean()
                        self.log_message(f"      Accuracy: {rssi_acc_mean:.2f}%")
                        self.log_message(f"      Error: {rssi_error_mean:.2f} dBm")
                
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
                self.log_message(f"   📄 CSV: v2v_communication_analysis.csv")
                self.log_message(f"   📄 JSON: v2v_communication_summary.json")
                self.log_message(f"   📂 Location: {original_dir}")
                self.log_message("="*70)
            else:
                self.log_message("\n⚠️ No communication analysis data collected")
            
            # Keep open
            self.log_message("\n⏸ Keeping SUMO-GUI open...")
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
        """Start GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    app = V2VCommunicationDigitalTwin()
    app.run()

