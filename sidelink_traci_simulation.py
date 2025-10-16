#!/usr/bin/env python3
"""
Sidelink V2V Communication Simulation using SUMO TraCI
Simulates 50 datapoints from sidelink dataframe with realistic V2V communication
"""

import traci
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import os
import sys
from datetime import datetime
import subprocess
import time
from typing import Dict, List, Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SidelinkTraCISimulator:
    """Main class for simulating V2V communication using SUMO TraCI"""
    
    def __init__(self, sumo_config_path: str, sidelink_data_path: str):
        self.sumo_config_path = sumo_config_path
        self.sidelink_data_path = sidelink_data_path
        self.simulation_data = None
        self.vehicle_data = {}
        self.communication_events = []
        self.sumo_process = None
        
        # V2V Communication parameters
        self.communication_range = 500  # meters
        self.packet_size = 1024  # bytes
        self.transmission_power = 23  # dBm
        self.noise_floor = -95  # dBm
        
        # Load and preprocess data
        self._load_sidelink_data()
        self._select_simulation_datapoints()
        
    def _load_sidelink_data(self):
        """Load sidelink dataframe and preprocess"""
        logger.info("Loading sidelink dataframe...")
        self.sidelink_df = pd.read_parquet(self.sidelink_data_path)
        
        # Convert timestamp to datetime if needed
        if not isinstance(self.sidelink_df.index, pd.DatetimeIndex):
            self.sidelink_df.index = pd.to_datetime(self.sidelink_df.index)
            
        logger.info(f"Loaded {len(self.sidelink_df)} records from sidelink dataframe")
        
    def _select_simulation_datapoints(self, n_points: int = 50):
        """Select representative datapoints for simulation"""
        logger.info(f"Selecting {n_points} datapoints for simulation...")
        
        # Filter out invalid coordinates
        valid_data = self.sidelink_df.dropna(subset=[
            'Latitude_source', 'Longitude_source', 
            'Latitude_destination', 'Longitude_destination'
        ])
        
        # Select diverse datapoints based on different criteria
        # 1. Different SNR ranges
        snr_ranges = [
            (valid_data['SNR'] >= -10) & (valid_data['SNR'] < 0),  # Poor
            (valid_data['SNR'] >= 0) & (valid_data['SNR'] < 10),   # Fair
            (valid_data['SNR'] >= 10) & (valid_data['SNR'] < 20),  # Good
            (valid_data['SNR'] >= 20)                               # Excellent
        ]
        
        selected_indices = []
        points_per_range = n_points // len(snr_ranges)
        
        for snr_range in snr_ranges:
            range_data = valid_data[snr_range]
            if len(range_data) > 0:
                # Randomly sample from each SNR range
                sample_size = min(points_per_range, len(range_data))
                sampled = range_data.sample(n=sample_size, random_state=42)
                selected_indices.extend(sampled.index.tolist())
        
        # If we need more points, fill with random selection
        if len(selected_indices) < n_points:
            remaining_needed = n_points - len(selected_indices)
            remaining_data = valid_data[~valid_data.index.isin(selected_indices)]
            if len(remaining_data) > 0:
                additional = remaining_data.sample(n=min(remaining_needed, len(remaining_data)), random_state=42)
                selected_indices.extend(additional.index.tolist())
        
        # Take exactly n_points
        self.simulation_data = valid_data.loc[selected_indices[:n_points]].copy()
        
        logger.info(f"Selected {len(self.simulation_data)} datapoints for simulation")
        
    def _convert_gps_to_sumo_coords(self, lat: float, lon: float) -> Tuple[float, float]:
        """Convert GPS coordinates to SUMO coordinates"""
        # Simple conversion - in practice, you'd use proper projection
        # For Berlin area, this is a rough approximation
        x = (lon - 13.0) * 111320 * np.cos(np.radians(lat))
        y = (lat - 52.5) * 111320
        return x, y
        
    def _find_nearest_edge(self, x: float, y: float) -> Optional[str]:
        """Find nearest edge to given coordinates"""
        try:
            # Get all edges
            edges = traci.edge.getIDList()
            min_distance = float('inf')
            nearest_edge = None
            
            for edge_id in edges:
                # Get edge coordinates
                edge_coords = traci.edge.getShape(edge_id)
                if edge_coords:
                    # Calculate distance to edge
                    for coord in edge_coords:
                        edge_x, edge_y = coord
                        distance = np.sqrt((x - edge_x)**2 + (y - edge_y)**2)
                        if distance < min_distance:
                            min_distance = distance
                            nearest_edge = edge_id
                            
            return nearest_edge
        except Exception as e:
            logger.warning(f"Error finding nearest edge: {e}")
            return None
            
    def _create_vehicle_type(self, vehicle_id: str, max_speed: float = 50.0) -> str:
        """Create custom vehicle type for V2V communication"""
        vtype_id = f"v2v_{vehicle_id}"
        
        # Define vehicle type parameters
        traci.vehicletype.copy("DEFAULT_VEHTYPE", vtype_id)
        traci.vehicletype.setMaxSpeed(vtype_id, max_speed)
        traci.vehicletype.setLength(vtype_id, 4.5)
        traci.vehicletype.setWidth(vtype_id, 1.8)
        traci.vehicletype.setHeight(vtype_id, 1.5)
        
        # Add V2V communication device
        traci.vehicletype.setParameter(vtype_id, "has.rerouting.device", "true")
        traci.vehicletype.setParameter(vtype_id, "has.v2v.device", "true")
        
        return vtype_id
        
    def _setup_simulation(self):
        """Setup SUMO simulation with TraCI"""
        logger.info("Setting up SUMO simulation...")
        
        # Start SUMO with TraCI
        sumo_cmd = [
            "sumo", "-c", self.sumo_config_path,
            "--tripinfo-output", "tripinfo.xml",
            "--fcd-output", "fcd.xml",
            "--device.fcd.period", "100",
            "--device.rerouting.adaptation-steps", "18",
            "--device.rerouting.adaptation-interval", "10"
        ]
        
        try:
            traci.start(sumo_cmd)
            logger.info("SUMO simulation started successfully")
            
            # Get simulation bounds
            self.simulation_bounds = traci.simulation.getNetBoundary()
            logger.info(f"Simulation bounds: {self.simulation_bounds}")
            
        except Exception as e:
            logger.error(f"Failed to start SUMO simulation: {e}")
            raise
            
    def _place_vehicles(self):
        """Place vehicles at source coordinates and set destinations"""
        logger.info("Placing vehicles in simulation...")
        
        for idx, (timestamp, row) in enumerate(self.simulation_data.iterrows()):
            vehicle_id = f"v2v_vehicle_{idx}"
            
            try:
                # Convert GPS coordinates to SUMO coordinates
                src_x, src_y = self._convert_gps_to_sumo_coords(
                    row['Latitude_source'], row['Longitude_source']
                )
                dst_x, dst_y = self._convert_gps_to_sumo_coords(
                    row['Latitude_destination'], row['Longitude_destination']
                )
                
                # Find nearest edges
                src_edge = self._find_nearest_edge(src_x, src_y)
                dst_edge = self._find_nearest_edge(dst_x, dst_y)
                
                if src_edge and dst_edge:
                    # Create vehicle type
                    max_speed = max(row['speed_kmh_source'], row['speed_kmh_destination']) / 3.6  # km/h to m/s
                    vtype_id = self._create_vehicle_type(vehicle_id, max_speed)
                    
                    # Add vehicle to simulation
                    traci.vehicle.add(
                        vehID=vehicle_id,
                        typeID=vtype_id,
                        routeID="",  # Will be computed automatically
                        depart=idx * 0.1,  # Staggered departure times
                        departLane="best",
                        departPos="random"
                    )
                    
                    # Set destination
                    traci.vehicle.changeTarget(vehicle_id, dst_edge)
                    
                    # Store vehicle data
                    self.vehicle_data[vehicle_id] = {
                        'source_coords': (src_x, src_y),
                        'dest_coords': (dst_x, dst_y),
                        'source_edge': src_edge,
                        'dest_edge': dst_edge,
                        'snr': row['SNR'],
                        'rsrp': row['RSRP'],
                        'rssi': row['RSSI'],
                        'mcs': row['MCS'],
                        'max_speed': max_speed,
                        'original_data': row.to_dict()
                    }
                    
                    logger.info(f"Added vehicle {vehicle_id} from {src_edge} to {dst_edge}")
                    
            except Exception as e:
                logger.warning(f"Failed to add vehicle {vehicle_id}: {e}")
                continue
                
        logger.info(f"Successfully placed {len(self.vehicle_data)} vehicles")
        
    def _simulate_v2v_communication(self, step: int):
        """Simulate V2V communication between vehicles"""
        vehicle_ids = list(self.vehicle_data.keys())
        
        for i, vehicle_id1 in enumerate(vehicle_ids):
            if not traci.vehicle.getIDList().__contains__(vehicle_id1):
                continue
                
            try:
                pos1 = traci.vehicle.getPosition(vehicle_id1)
                vehicle1_data = self.vehicle_data[vehicle_id1]
                
                for j, vehicle_id2 in enumerate(vehicle_ids[i+1:], i+1):
                    if not traci.vehicle.getIDList().__contains__(vehicle_id2):
                        continue
                        
                    try:
                        pos2 = traci.vehicle.getPosition(vehicle_id2)
                        vehicle2_data = self.vehicle_data[vehicle_id2]
                        
                        # Calculate distance between vehicles
                        distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                        
                        # Check if vehicles are within communication range
                        if distance <= self.communication_range:
                            # Simulate packet transmission
                            success = self._simulate_packet_transmission(
                                vehicle1_data, vehicle2_data, distance, step
                            )
                            
                            if success:
                                self.communication_events.append({
                                    'step': step,
                                    'vehicle1': vehicle_id1,
                                    'vehicle2': vehicle_id2,
                                    'distance': distance,
                                    'pos1': pos1,
                                    'pos2': pos2,
                                    'snr1': vehicle1_data['snr'],
                                    'snr2': vehicle2_data['snr'],
                                    'rsrp1': vehicle1_data['rsrp'],
                                    'rsrp2': vehicle2_data['rsrp']
                                })
                                
                    except Exception as e:
                        logger.warning(f"Error processing vehicle {vehicle_id2}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Error processing vehicle {vehicle_id1}: {e}")
                continue
                
    def _simulate_packet_transmission(self, vehicle1_data: Dict, vehicle2_data: Dict, 
                                   distance: float, step: int) -> bool:
        """Simulate packet transmission success based on channel conditions"""
        
        # Use average SNR from both vehicles
        avg_snr = (vehicle1_data['snr'] + vehicle2_data['snr']) / 2
        
        # Calculate path loss (simplified model)
        path_loss = 20 * np.log10(distance) + 20 * np.log10(2400) - 147.55  # 2.4 GHz
        
        # Calculate received power
        received_power = self.transmission_power - path_loss
        
        # Calculate SINR
        sinr = received_power - self.noise_floor
        
        # Packet success probability based on MCS and SINR
        mcs = int((vehicle1_data['mcs'] + vehicle2_data['mcs']) / 2)
        
        # Simplified success probability (in practice, use proper MCS tables)
        if sinr > 20:
            success_prob = 0.95
        elif sinr > 10:
            success_prob = 0.85
        elif sinr > 0:
            success_prob = 0.70
        else:
            success_prob = 0.30
            
        # Add some randomness
        success_prob *= (0.8 + 0.4 * np.random.random())
        
        return np.random.random() < success_prob
        
    def run_simulation(self, max_steps: int = 3600):
        """Run the complete simulation"""
        logger.info("Starting simulation...")
        
        try:
            # Setup simulation
            self._setup_simulation()
            
            # Place vehicles
            self._place_vehicles()
            
            # Run simulation steps
            step = 0
            while step < max_steps and traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                
                # Simulate V2V communication every 10 steps
                if step % 10 == 0:
                    self._simulate_v2v_communication(step)
                    
                step += 1
                
                # Log progress
                if step % 100 == 0:
                    active_vehicles = len(traci.vehicle.getIDList())
                    logger.info(f"Step {step}: {active_vehicles} active vehicles, "
                              f"{len(self.communication_events)} communication events")
                    
            logger.info(f"Simulation completed after {step} steps")
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            raise
        finally:
            traci.close()
            
    def generate_results(self):
        """Generate simulation results and visualizations"""
        logger.info("Generating simulation results...")
        
        # Create results directory
        results_dir = "sidelink_simulation_results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Save communication events
        if self.communication_events:
            comm_df = pd.DataFrame(self.communication_events)
            comm_df.to_csv(f"{results_dir}/communication_events.csv", index=False)
            
            # Generate statistics
            stats = {
                'total_communication_events': len(self.communication_events),
                'unique_vehicle_pairs': len(set([(e['vehicle1'], e['vehicle2']) for e in self.communication_events])),
                'average_distance': np.mean([e['distance'] for e in self.communication_events]),
                'max_distance': np.max([e['distance'] for e in self.communication_events]),
                'min_distance': np.min([e['distance'] for e in self.communication_events]),
                'simulation_steps': max([e['step'] for e in self.communication_events]) if self.communication_events else 0
            }
            
            with open(f"{results_dir}/simulation_stats.json", 'w') as f:
                json.dump(stats, f, indent=2)
                
        # Save vehicle data
        vehicle_df = pd.DataFrame.from_dict(self.vehicle_data, orient='index')
        vehicle_df.to_csv(f"{results_dir}/vehicle_data.csv")
        
        # Generate visualization
        self._create_visualization(results_dir)
        
        logger.info(f"Results saved to {results_dir}/")
        
    def _create_visualization(self, results_dir: str):
        """Create visualization plots"""
        if not self.communication_events:
            logger.warning("No communication events to visualize")
            return
            
        comm_df = pd.DataFrame(self.communication_events)
        
        # Create plots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Distance distribution
        axes[0, 0].hist(comm_df['distance'], bins=20, alpha=0.7, color='blue')
        axes[0, 0].set_xlabel('Distance (m)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('V2V Communication Distance Distribution')
        axes[0, 0].grid(True, alpha=0.3)
        
        # SNR distribution
        snr_data = np.concatenate([comm_df['snr1'], comm_df['snr2']])
        axes[0, 1].hist(snr_data, bins=20, alpha=0.7, color='green')
        axes[0, 1].set_xlabel('SNR (dB)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('SNR Distribution')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Communication events over time
        axes[1, 0].plot(comm_df['step'], comm_df['distance'], 'o', alpha=0.6, markersize=3)
        axes[1, 0].set_xlabel('Simulation Step')
        axes[1, 0].set_ylabel('Distance (m)')
        axes[1, 0].set_title('Communication Distance Over Time')
        axes[1, 0].grid(True, alpha=0.3)
        
        # RSRP distribution
        rsrp_data = np.concatenate([comm_df['rsrp1'], comm_df['rsrp2']])
        axes[1, 1].hist(rsrp_data, bins=20, alpha=0.7, color='red')
        axes[1, 1].set_xlabel('RSRP (dBm)')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].set_title('RSRP Distribution')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{results_dir}/simulation_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("Visualization plots created")


def main():
    """Main function to run the simulation"""
    
    # Configuration paths
    sumo_config = "sumo-config/osm.sumocfg"
    sidelink_data = "sidelink_dataframe.parquet"
    
    # Check if files exist
    if not os.path.exists(sumo_config):
        logger.error(f"SUMO config file not found: {sumo_config}")
        return
        
    if not os.path.exists(sidelink_data):
        logger.error(f"Sidelink data file not found: {sidelink_data}")
        return
    
    try:
        # Create simulator
        simulator = SidelinkTraCISimulator(sumo_config, sidelink_data)
        
        # Run simulation
        simulator.run_simulation(max_steps=1800)  # 30 minutes simulation
        
        # Generate results
        simulator.generate_results()
        
        logger.info("Simulation completed successfully!")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise


if __name__ == "__main__":
    main()
