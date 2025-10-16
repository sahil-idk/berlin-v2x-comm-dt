#!/usr/bin/env python3
"""
Sidelink SUMO Visualization Script
Creates SUMO simulation using sidelink communication data without GPS coordinates.
Uses communication patterns, signal strength, and timing to simulate vehicle behavior.
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import traci
import sumolib
from datetime import datetime
import time
import json

class SidelinkSUMOVisualization:
    def __init__(self, sidelink_file, sumo_config="berlin_simulation.sumocfg"):
        self.sidelink_file = sidelink_file
        self.sumo_config = sumo_config
        self.data = None
        self.vehicles = {}
        self.communication_links = {}
        self.signal_quality_data = {}
        
    def load_sidelink_data(self):
        """Load and preprocess sidelink data."""
        print(f"Loading sidelink data from {self.sidelink_file}...")
        
        try:
            self.data = pd.read_parquet(self.sidelink_file)
            print(f"Loaded {len(self.data)} records")
            
            # Extract file information
            file_name = os.path.basename(self.sidelink_file)
            parts = file_name.replace('.parquet', '').split('_')
            self.ue_id = parts[0] if len(parts) > 0 else 'unknown'
            self.session_id = parts[1] if len(parts) > 1 else 'unknown'
            self.date = parts[2] if len(parts) > 2 else 'unknown'
            
            # Preprocess data
            self.preprocess_data()
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
        
        return True
    
    def preprocess_data(self):
        """Preprocess the sidelink data for SUMO visualization."""
        print("Preprocessing data...")
        
        # Filter out rows with missing critical data
        self.data = self.data.dropna(subset=['time_epoch', 'Source'])
        
        # Sort by time
        self.data = self.data.sort_values('time_epoch')
        
        # Create vehicle mapping
        unique_sources = self.data['Source'].unique()
        self.vehicle_mapping = {source: f"vehicle_{source.replace(':', '_')}" for source in unique_sources}
        
        # Calculate communication patterns
        self.calculate_communication_patterns()
        
        # Estimate distances using signal strength
        self.estimate_distances()
        
        print(f"Preprocessed data: {len(self.data)} records, {len(unique_sources)} vehicles")
    
    def calculate_communication_patterns(self):
        """Calculate communication patterns for each vehicle."""
        print("Calculating communication patterns...")
        
        for source in self.data['Source'].unique():
            source_data = self.data[self.data['Source'] == source].copy()
            
            if len(source_data) > 1:
                # Calculate message intervals
                source_data = source_data.sort_values('time_epoch')
                time_diffs = source_data['time_epoch'].diff().dropna()
                
                # Calculate average signal quality
                signal_quality = {
                    'avg_snr': source_data['SNR'].mean() if 'SNR' in source_data.columns else 0,
                    'avg_rsrp': source_data['RSRP'].mean() if 'RSRP' in source_data.columns else -80,
                    'avg_rssi': source_data['RSSI'].mean() if 'RSSI' in source_data.columns else -50,
                    'message_count': len(source_data),
                    'avg_interval': time_diffs.mean(),
                    'communication_rate': 1.0 / time_diffs.mean() if time_diffs.mean() > 0 else 0
                }
                
                self.signal_quality_data[source] = signal_quality
    
    def estimate_distances(self):
        """Estimate distances between vehicles using signal strength."""
        print("Estimating distances from signal strength...")
        
        # Simple path loss model: Distance = 10^((TxPower - RSRP - 30) / 20)
        # Assuming TxPower = 23 dBm (typical for V2X)
        tx_power = 23  # dBm
        
        for source in self.data['Source'].unique():
            source_data = self.data[self.data['Source'] == source]
            if 'RSRP' in source_data.columns:
                # Estimate distance based on RSRP
                avg_rsrp = source_data['RSRP'].mean()
                estimated_distance = 10 ** ((tx_power - avg_rsrp - 30) / 20)
                
                # Cap distance to reasonable range (10m to 1000m)
                estimated_distance = max(10, min(1000, estimated_distance))
                
                if source in self.signal_quality_data:
                    self.signal_quality_data[source]['estimated_distance'] = estimated_distance
    
    def create_sumo_network(self):
        """Create a simple SUMO network for visualization."""
        print("Creating SUMO network...")
        
        # Create a simple grid network
        net_file = "sidelink_network.net.xml"
        
        # Generate network using sumolib
        net = sumolib.net.Net()
        
        # Create nodes (intersections)
        nodes = []
        for i in range(3):
            for j in range(3):
                node_id = f"node_{i}_{j}"
                x = i * 200
                y = j * 200
                nodes.append((node_id, x, y))
        
        # Create edges (roads)
        edges = []
        for i in range(3):
            for j in range(3):
                if i < 2:  # Horizontal edges
                    edge_id = f"edge_h_{i}_{j}"
                    from_node = f"node_{i}_{j}"
                    to_node = f"node_{i+1}_{j}"
                    edges.append((edge_id, from_node, to_node, 200))
                
                if j < 2:  # Vertical edges
                    edge_id = f"edge_v_{i}_{j}"
                    from_node = f"node_{i}_{j}"
                    to_node = f"node_{i}_{j+1}"
                    edges.append((edge_id, from_node, to_node, 200))
        
        # Write network file
        with open(net_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<net version="1.0" junctionCornerDetail="5" limitTurnSpeed="5.5" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/net_file.xsd">\n')
            
            # Write nodes
            for node_id, x, y in nodes:
                f.write(f'    <junction id="{node_id}" type="priority" x="{x}" y="{y}" incLanes="" intLanes="" shape="{x-10},{y-10} {x+10},{y-10} {x+10},{y+10} {x-10},{y+10}"/>\n')
            
            # Write edges
            for edge_id, from_node, to_node, length in edges:
                f.write(f'    <edge id="{edge_id}" from="{from_node}" to="{to_node}" priority="1">\n')
                f.write(f'        <lane id="{edge_id}_0" index="0" speed="13.89" length="{length}" shape="{from_node.split("_")[1]},{from_node.split("_")[2]} {to_node.split("_")[1]},{to_node.split("_")[2]}"/>\n')
                f.write(f'    </edge>\n')
            
            f.write('</net>\n')
        
        print(f"Created network file: {net_file}")
        return net_file
    
    def create_sumo_config(self, net_file):
        """Create SUMO configuration file."""
        print("Creating SUMO configuration...")
        
        config_file = "sidelink_simulation.sumocfg"
        
        with open(config_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">\n')
            f.write('    <input>\n')
            f.write(f'        <net-file value="{net_file}"/>\n')
            f.write('        <route-files value="sidelink_routes.rou.xml"/>\n')
            f.write('    </input>\n')
            f.write('    <time>\n')
            f.write('        <begin value="0"/>\n')
            f.write('        <end value="1000"/>\n')
            f.write('        <step-length value="1"/>\n')
            f.write('    </time>\n')
            f.write('    <processing>\n')
            f.write('        <ignore-junction-blocker value="0"/>\n')
            f.write('    </processing>\n')
            f.write('    <report>\n')
            f.write('        <verbose value="true"/>\n')
            f.write('        <no-step-log value="true"/>\n')
            f.write('    </report>\n')
            f.write('</configuration>\n')
        
        print(f"Created config file: {config_file}")
        return config_file
    
    def create_routes(self):
        """Create vehicle routes based on communication patterns."""
        print("Creating vehicle routes...")
        
        route_file = "sidelink_routes.rou.xml"
        
        with open(route_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n')
            
            # Define vehicle types
            f.write('    <vType id="sidelink_vehicle" accel="2.0" decel="4.5" sigma="0.5" length="4.5" maxSpeed="13.89"/>\n')
            
            # Create routes for each vehicle
            for source in self.data['Source'].unique():
                vehicle_id = self.vehicle_mapping[source]
                
                # Simple route around the network
                route_id = f"route_{source.replace(':', '_')}"
                f.write(f'    <route id="{route_id}" edges="edge_h_0_0 edge_h_1_0 edge_v_1_0 edge_v_1_1 edge_h_1_1 edge_h_0_1 edge_v_0_1 edge_v_0_0"/>\n')
                
                # Vehicle with communication-based timing
                if source in self.signal_quality_data:
                    comm_rate = self.signal_quality_data[source]['communication_rate']
                    # Map communication rate to vehicle speed (higher rate = higher speed)
                    speed_factor = min(2.0, max(0.5, comm_rate / 10.0))
                    f.write(f'    <vehicle id="{vehicle_id}" type="sidelink_vehicle" route="{route_id}" depart="0" speedFactor="{speed_factor}"/>\n')
                else:
                    f.write(f'    <vehicle id="{vehicle_id}" type="sidelink_vehicle" route="{route_id}" depart="0"/>\n')
            
            f.write('</routes>\n')
        
        print(f"Created route file: {route_file}")
        return route_file
    
    def run_simulation(self, config_file):
        """Run the SUMO simulation with TraCI control."""
        print("Starting SUMO simulation...")
        
        try:
            # Start SUMO
            sumo_cmd = ["sumo-gui", "-c", config_file, "--start"]
            traci.start(sumo_cmd)
            
            print("SUMO started successfully!")
            
            # Get simulation info
            step = 0
            max_steps = 1000
            
            print(f"Running simulation for {max_steps} steps...")
            
            while step < max_steps:
                traci.simulationStep()
                
                # Update vehicle positions based on communication data
                self.update_vehicle_positions(step)
                
                # Log progress
                if step % 100 == 0:
                    print(f"Step {step}: {len(traci.vehicle.getIDList())} vehicles active")
                
                step += 1
                
                # Small delay for visualization
                time.sleep(0.01)
            
            print("Simulation completed!")
            
        except Exception as e:
            print(f"Error running simulation: {e}")
        finally:
            traci.close()
    
    def update_vehicle_positions(self, step):
        """Update vehicle positions based on communication data."""
        # This is a simplified approach - in reality, you'd map communication
        # patterns to actual vehicle movement
        
        current_time = step  # Simplified time mapping
        
        # Find relevant data for current time
        time_window = 10  # seconds
        relevant_data = self.data[
            (self.data['time_epoch'] >= current_time) & 
            (self.data['time_epoch'] < current_time + time_window)
        ]
        
        # Update vehicle colors based on signal quality
        for source in relevant_data['Source'].unique():
            vehicle_id = self.vehicle_mapping.get(source)
            if vehicle_id and traci.vehicle.getIDList().__contains__(vehicle_id):
                source_data = relevant_data[relevant_data['Source'] == source]
                
                if len(source_data) > 0:
                    # Color based on signal quality
                    avg_snr = source_data['SNR'].mean() if 'SNR' in source_data.columns else 0
                    
                    if avg_snr > 20:
                        color = (0, 255, 0)  # Green - good signal
                    elif avg_snr > 10:
                        color = (255, 255, 0)  # Yellow - moderate signal
                    else:
                        color = (255, 0, 0)  # Red - poor signal
                    
                    try:
                        traci.vehicle.setColor(vehicle_id, color)
                    except:
                        pass  # Vehicle might not exist yet
    
    def generate_analysis_report(self):
        """Generate analysis report of the sidelink data."""
        print("Generating analysis report...")
        
        report = {
            'file_info': {
                'filename': os.path.basename(self.sidelink_file),
                'ue_id': self.ue_id,
                'session_id': self.session_id,
                'date': self.date,
                'total_records': len(self.data)
            },
            'vehicles': self.signal_quality_data,
            'communication_summary': {
                'total_vehicles': len(self.signal_quality_data),
                'avg_communication_rate': np.mean([v['communication_rate'] for v in self.signal_quality_data.values()]),
                'avg_signal_quality': np.mean([v['avg_snr'] for v in self.signal_quality_data.values()])
            }
        }
        
        # Save report
        report_file = f"sidelink_analysis_{self.ue_id}_{self.session_id}_{self.date}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Analysis report saved: {report_file}")
        return report

def main():
    """Main function."""
    print("=" * 80)
    print("SIDELINK SUMO VISUALIZATION")
    print("=" * 80)
    
    # Check if SUMO is available
    try:
        import traci
        print("SUMO TraCI available")
    except ImportError:
        print("Error: SUMO TraCI not available. Please install SUMO.")
        return
    
    # Find sidelink files
    sidelink_dir = Path("sidelink")
    if not sidelink_dir.exists():
        print("Error: sidelink directory not found!")
        return
    
    parquet_files = list(sidelink_dir.glob("*.parquet"))
    
    if not parquet_files:
        print("No parquet files found in sidelink directory!")
        return
    
    print(f"Found {len(parquet_files)} sidelink files")
    
    # Select a file for visualization (use the first one)
    selected_file = parquet_files[0]
    print(f"Selected file: {selected_file.name}")
    
    # Create visualization
    viz = SidelinkSUMOVisualization(selected_file)
    
    # Load data
    if not viz.load_sidelink_data():
        print("Failed to load data")
        return
    
    # Generate analysis report
    report = viz.generate_analysis_report()
    
    # Create SUMO network
    net_file = viz.create_sumo_network()
    
    # Create routes
    route_file = viz.create_routes()
    
    # Create config
    config_file = viz.create_sumo_config(net_file)
    
    # Run simulation
    viz.run_simulation(config_file)
    
    print("Visualization complete!")

if __name__ == "__main__":
    main()
