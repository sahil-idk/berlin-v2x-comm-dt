#!/usr/bin/env python3
"""
Simplified Sidelink V2V Simulation using SUMO TraCI
This version focuses on core functionality and is easier to run
"""

import traci
import pandas as pd
import numpy as np
import json
import os
import sys
import time
from typing import Dict, List, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleSidelinkSimulator:
    """Simplified V2V communication simulator"""
    
    def __init__(self, sidelink_data_path: str):
        self.sidelink_data_path = sidelink_data_path
        self.simulation_data = None
        self.vehicle_data = {}
        self.communication_events = []
        
        # Load data
        self._load_and_prepare_data()
        
    def _load_and_prepare_data(self):
        """Load and prepare sidelink data"""
        logger.info("Loading sidelink data...")
        
        # Load dataframe
        df = pd.read_parquet(self.sidelink_data_path)
        
        # Select 50 diverse datapoints
        # Filter valid coordinates
        valid_data = df.dropna(subset=[
            'Latitude_source', 'Longitude_source', 
            'Latitude_destination', 'Longitude_destination'
        ])
        
        # Sample 50 points with different SNR ranges
        self.simulation_data = valid_data.sample(n=50, random_state=42)
        
        logger.info(f"Selected {len(self.simulation_data)} datapoints")
        
    def _simple_gps_to_sumo(self, lat: float, lon: float) -> Tuple[float, float]:
        """Simple GPS to SUMO coordinate conversion for Berlin area"""
        # Network bounds: ((0.0, -0.0), (19873.71, 12467.71))
        # Berlin approximate bounds: lat 52.3-52.7, lon 13.0-13.8
        
        # Map GPS coordinates to SUMO network bounds
        # Berlin lat range: 52.3 to 52.7 (0.4 degrees)
        # Berlin lon range: 13.0 to 13.8 (0.8 degrees)
        
        # Normalize coordinates to 0-1 range
        lat_norm = (lat - 52.3) / 0.4  # 0 to 1
        lon_norm = (lon - 13.0) / 0.8  # 0 to 1
        
        # Map to SUMO network bounds
        x = lon_norm * 19873.71  # 0 to 19873.71
        y = lat_norm * 12467.71  # 0 to 12467.71
        
        return x, y
        
    def _find_closest_edge(self, x: float, y: float) -> str:
        """Find a valid edge for vehicle placement"""
        try:
            edges = traci.edge.getIDList()
            if not edges:
                logger.warning("No edges found in network")
                return None
                
            # For now, use a simple approach - select edges that are likely to be valid
            # Filter edges that don't have special characters that might cause issues
            valid_edges = [edge for edge in edges if not edge.startswith('-') and '#' in edge]
            
            if not valid_edges:
                # Fallback to any edge
                valid_edges = edges
                
            # Return a random valid edge
            import random
            return random.choice(valid_edges)
            
        except Exception as e:
            logger.error(f"Error in _find_closest_edge: {e}")
            return None
            
    def run_simulation(self):
        """Run the simulation"""
        logger.info("Starting simulation...")
        
        # SUMO command
        sumo_cmd = [
            "sumo", "-c", "sumo-config/osm.sumocfg",
            "--tripinfo-output", "tripinfo.xml",
            "--fcd-output", "fcd.xml",
            "--device.fcd.period", "100"
        ]
        
        try:
            # Start TraCI
            traci.start(sumo_cmd)
            logger.info("SUMO started successfully")
            
            # Place vehicles
            self._place_vehicles()
            
            # Run simulation
            step = 0
            max_steps = 1800  # 30 minutes
            
            while step < max_steps and traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                
                # Check V2V communication every 10 steps
                if step % 10 == 0:
                    self._check_v2v_communication(step)
                    
                step += 1
                
                if step % 100 == 0:
                    active_vehicles = len(traci.vehicle.getIDList())
                    logger.info(f"Step {step}: {active_vehicles} vehicles active")
                    
            logger.info(f"Simulation completed after {step} steps")
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
        finally:
            traci.close()
            
    def _place_vehicles(self):
        """Place vehicles in the simulation"""
        logger.info("Placing vehicles...")
        
        # Get all available edges first
        all_edges = traci.edge.getIDList()
        if not all_edges:
            logger.error("No edges available in the network!")
            return
            
        logger.info(f"Found {len(all_edges)} edges in network")
        
        # Filter for valid edges (avoid edges starting with '-')
        valid_edges = [edge for edge in all_edges if not edge.startswith('-')]
        if not valid_edges:
            valid_edges = all_edges
            
        logger.info(f"Using {len(valid_edges)} valid edges")
        
        placed_count = 0
        
        for idx, (timestamp, row) in enumerate(self.simulation_data.iterrows()):
            vehicle_id = f"v2v_{idx}"
            
            try:
                # Convert coordinates (for logging purposes)
                src_x, src_y = self._simple_gps_to_sumo(
                    row['Latitude_source'], row['Longitude_source']
                )
                dst_x, dst_y = self._simple_gps_to_sumo(
                    row['Latitude_destination'], row['Longitude_destination']
                )
                
                # Select different edges for source and destination
                import random
                src_edge = random.choice(valid_edges)
                dst_edge = random.choice(valid_edges)
                
                # Ensure source and destination are different
                attempts = 0
                while src_edge == dst_edge and attempts < 10:
                    dst_edge = random.choice(valid_edges)
                    attempts += 1
                
                # Skip if we can't find different edges
                if src_edge == dst_edge:
                    logger.warning(f"Skipping vehicle {vehicle_id} - cannot find different edges")
                    continue
                
                # Add vehicle
                traci.vehicle.add(
                    vehID=vehicle_id,
                    typeID="DEFAULT_VEHTYPE",
                    routeID="",
                    depart=idx * 0.5,  # Staggered departure
                    departLane="best"
                )
                
                # Set destination
                traci.vehicle.changeTarget(vehicle_id, dst_edge)
                
                # Store data
                self.vehicle_data[vehicle_id] = {
                    'source': (src_x, src_y),
                    'destination': (dst_x, dst_y),
                    'source_edge': src_edge,
                    'dest_edge': dst_edge,
                    'snr': row['SNR'],
                    'rsrp': row['RSRP'],
                    'rssi': row['RSSI'],
                    'speed': max(row['speed_kmh_source'], row['speed_kmh_destination'])
                }
                
                placed_count += 1
                logger.info(f"Successfully placed vehicle {vehicle_id} from {src_edge} to {dst_edge}")
                
            except Exception as e:
                logger.warning(f"Failed to add vehicle {vehicle_id}: {e}")
                continue
                
        logger.info(f"Successfully placed {placed_count} vehicles out of {len(self.simulation_data)} attempted")
        
    def _check_v2v_communication(self, step: int):
        """Check V2V communication between vehicles"""
        vehicle_ids = list(self.vehicle_data.keys())
        communication_range = 500  # meters
        
        for i, v1 in enumerate(vehicle_ids):
            if v1 not in traci.vehicle.getIDList():
                continue
                
            try:
                pos1 = traci.vehicle.getPosition(v1)
                
                for j, v2 in enumerate(vehicle_ids[i+1:], i+1):
                    if v2 not in traci.vehicle.getIDList():
                        continue
                        
                    try:
                        pos2 = traci.vehicle.getPosition(v2)
                        
                        # Calculate distance
                        distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                        
                        # Check if in range
                        if distance <= communication_range:
                            # Simulate communication
                            success = self._simulate_communication(
                                self.vehicle_data[v1], self.vehicle_data[v2], distance
                            )
                            
                            if success:
                                self.communication_events.append({
                                    'step': step,
                                    'vehicle1': v1,
                                    'vehicle2': v2,
                                    'distance': distance,
                                    'snr1': self.vehicle_data[v1]['snr'],
                                    'snr2': self.vehicle_data[v2]['snr']
                                })
                                
                    except:
                        continue
                        
            except:
                continue
                
    def _simulate_communication(self, v1_data: Dict, v2_data: Dict, distance: float) -> bool:
        """Simulate communication success"""
        # Use average SNR
        avg_snr = (v1_data['snr'] + v2_data['snr']) / 2
        
        # Simple success probability based on SNR and distance
        if avg_snr > 15 and distance < 200:
            success_prob = 0.9
        elif avg_snr > 5 and distance < 400:
            success_prob = 0.7
        elif avg_snr > 0 and distance < 500:
            success_prob = 0.5
        else:
            success_prob = 0.2
            
        return np.random.random() < success_prob
        
    def save_results(self):
        """Save simulation results"""
        logger.info("Saving results...")
        
        # Create results directory
        os.makedirs("simulation_results", exist_ok=True)
        
        # Save communication events
        if self.communication_events:
            comm_df = pd.DataFrame(self.communication_events)
            comm_df.to_csv("simulation_results/communication_events.csv", index=False)
            
            # Statistics
            stats = {
                'total_events': len(self.communication_events),
                'unique_pairs': len(set([(e['vehicle1'], e['vehicle2']) for e in self.communication_events])),
                'avg_distance': np.mean([e['distance'] for e in self.communication_events]),
                'avg_snr': np.mean([(e['snr1'] + e['snr2'])/2 for e in self.communication_events])
            }
            
            with open("simulation_results/stats.json", 'w') as f:
                json.dump(stats, f, indent=2)
                
        # Save vehicle data
        vehicle_df = pd.DataFrame.from_dict(self.vehicle_data, orient='index')
        vehicle_df.to_csv("simulation_results/vehicle_data.csv")
        
        logger.info("Results saved to simulation_results/")


def main():
    """Main function"""
    
    # Check if sidelink data exists
    if not os.path.exists("sidelink_dataframe.parquet"):
        logger.error("sidelink_dataframe.parquet not found!")
        return
        
    # Check if SUMO config exists
    if not os.path.exists("sumo-config/osm.sumocfg"):
        logger.error("sumo-config/osm.sumocfg not found!")
        return
        
    try:
        # Create and run simulator
        simulator = SimpleSidelinkSimulator("sidelink_dataframe.parquet")
        simulator.run_simulation()
        simulator.save_results()
        
        logger.info("Simulation completed successfully!")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
