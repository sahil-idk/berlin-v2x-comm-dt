#!/usr/bin/env python3
"""
V2V Communication Simulation using SUMO TraCI
Simulates 50 V2V scenarios from sidelink_parsed.csv using existing SUMO Web Wizard project
"""

import traci
import pandas as pd
import numpy as np
import json
import os
import sys
import time
import random
from typing import Dict, List, Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class V2VSumoSimulator:
    """V2V Communication Simulator using SUMO TraCI"""
    
    def __init__(self, csv_file: str, sumo_config: str):
        self.csv_file = csv_file
        self.sumo_config = sumo_config
        self.simulation_data = None
        self.vehicle_pairs = []
        self.simulation_results = []
        
        # Load and prepare data
        self._load_csv_data()
        self._select_v2v_scenarios()
        
    def _load_csv_data(self):
        """Load CSV data and prepare for V2V simulation"""
        logger.info(f"Loading CSV data from {self.csv_file}...")
        
        try:
            # Load CSV in chunks to handle large file
            chunk_size = 10000
            chunks = []
            
            for chunk in pd.read_csv(self.csv_file, chunksize=chunk_size):
                chunks.append(chunk)
                if len(chunks) * chunk_size > 100000:  # Limit to first 100k rows
                    break
                    
            df = pd.concat(chunks, ignore_index=True)
            logger.info(f"Loaded {len(df)} records from CSV")
            
            # Filter for valid GPS coordinates
            valid_data = df.dropna(subset=['lat', 'lon'])
            
            # Group by Source-Destination pairs to create V2V scenarios
            self.simulation_data = valid_data.groupby(['Source', 'Destination']).first().reset_index()
            
            logger.info(f"Found {len(self.simulation_data)} unique Source-Destination pairs")
            
        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            raise
            
    def _select_v2v_scenarios(self, n_scenarios: int = 50):
        """Select V2V scenarios for simulation"""
        logger.info(f"Selecting {n_scenarios} V2V scenarios...")
        
        # Filter out self-communication (Source == Destination)
        valid_scenarios = self.simulation_data[
            self.simulation_data['Source'] != self.simulation_data['Destination']
        ]
        
        if len(valid_scenarios) < n_scenarios:
            logger.warning(f"Only {len(valid_scenarios)} valid scenarios found, using all")
            n_scenarios = len(valid_scenarios)
            
        # Select diverse scenarios
        selected_scenarios = valid_scenarios.sample(n=n_scenarios, random_state=42)
        
        # Create vehicle pairs for each scenario
        self.vehicle_pairs = []
        for idx, row in selected_scenarios.iterrows():
            # For each scenario, we need to find source and destination coordinates
            # We'll use the current row's coordinates as starting points
            source_coords = (row['lat'], row['lon'])
            
            # Find destination coordinates from the same Source-Destination pair
            dest_data = self.simulation_data[
                (self.simulation_data['Source'] == row['Source']) & 
                (self.simulation_data['Destination'] == row['Destination'])
            ]
            
            if len(dest_data) > 1:
                # Use different coordinates for destination
                dest_coords = (dest_data.iloc[1]['lat'], dest_data.iloc[1]['lon'])
            else:
                # Generate nearby coordinates for destination
                dest_coords = (
                    source_coords[0] + random.uniform(-0.001, 0.001),
                    source_coords[1] + random.uniform(-0.001, 0.001)
                )
            
            self.vehicle_pairs.append({
                'scenario_id': idx,
                'source_id': f"source_{row['Source']}_{idx}",
                'dest_id': f"dest_{row['Destination']}_{idx}",
                'source_coords': source_coords,
                'dest_coords': dest_coords,
                'snr': row.get('SNR', 15.0),
                'rsrp': row.get('RSRP', -70.0),
                'rssi': row.get('RSSI', -45.0),
                'mcs': row.get('MCS', 10),
                'scenario': row.get('Scenario', 'S1')
            })
            
        logger.info(f"Created {len(self.vehicle_pairs)} V2V vehicle pairs")
        
    def _gps_to_sumo_coords(self, lat: float, lon: float) -> Tuple[float, float]:
        """Convert GPS coordinates to SUMO coordinates"""
        # Berlin area mapping to SUMO network bounds
        # Network bounds: ((0.0, -0.0), (19873.71, 12467.71))
        
        # Berlin approximate bounds: lat 52.3-52.7, lon 13.0-13.8
        lat_norm = (lat - 52.3) / 0.4  # 0 to 1
        lon_norm = (lon - 13.0) / 0.8  # 0 to 1
        
        x = lon_norm * 19873.71
        y = lat_norm * 12467.71
        
        return x, y
        
    def _find_nearest_edge(self, x: float, y: float) -> Optional[str]:
        """Find nearest edge to coordinates"""
        try:
            edges = traci.edge.getIDList()
            if not edges:
                return None
                
            # Filter for valid edges (avoid edges starting with '-')
            valid_edges = [edge for edge in edges if not edge.startswith('-')]
            if not valid_edges:
                valid_edges = edges
                
            # For now, return a random valid edge
            # In a more sophisticated implementation, you'd calculate actual distances
            return random.choice(valid_edges)
            
        except Exception as e:
            logger.warning(f"Error finding edge: {e}")
            return None
            
    def _create_vehicle_type(self, vehicle_id: str, max_speed: float = 50.0) -> str:
        """Create custom vehicle type for V2V communication"""
        vtype_id = f"v2v_{vehicle_id}"
        
        try:
            # Copy default vehicle type
            traci.vehicletype.copy("DEFAULT_VEHTYPE", vtype_id)
            traci.vehicletype.setMaxSpeed(vtype_id, max_speed)
            traci.vehicletype.setLength(vtype_id, 4.5)
            traci.vehicletype.setWidth(vtype_id, 1.8)
            
            # Add V2V communication device
            traci.vehicletype.setParameter(vtype_id, "has.rerouting.device", "true")
            
            return vtype_id
        except Exception as e:
            logger.warning(f"Error creating vehicle type {vtype_id}: {e}")
            return "DEFAULT_VEHTYPE"
            
    def _place_v2v_vehicles(self):
        """Place V2V vehicle pairs in the simulation"""
        logger.info("Placing V2V vehicle pairs...")
        
        placed_count = 0
        
        for pair in self.vehicle_pairs:
            try:
                # Convert coordinates
                src_x, src_y = self._gps_to_sumo_coords(*pair['source_coords'])
                dst_x, dst_y = self._gps_to_sumo_coords(*pair['dest_coords'])
                
                # Find edges
                src_edge = self._find_nearest_edge(src_x, src_y)
                dst_edge = self._find_nearest_edge(dst_x, dst_y)
                
                if not src_edge or not dst_edge:
                    logger.warning(f"Skipping pair {pair['scenario_id']} - no valid edges")
                    continue
                    
                if src_edge == dst_edge:
                    logger.warning(f"Skipping pair {pair['scenario_id']} - same edge")
                    continue
                
                # Create vehicle types
                src_vtype = self._create_vehicle_type(pair['source_id'])
                dst_vtype = self._create_vehicle_type(pair['dest_id'])
                
                # Add source vehicle
                traci.vehicle.add(
                    vehID=pair['source_id'],
                    typeID=src_vtype,
                    routeID="",
                    depart=placed_count * 0.5,  # Staggered departure
                    departLane="best"
                )
                
                # Set source vehicle destination
                traci.vehicle.changeTarget(pair['source_id'], dst_edge)
                
                # Add destination vehicle
                traci.vehicle.add(
                    vehID=pair['dest_id'],
                    typeID=dst_vtype,
                    routeID="",
                    depart=placed_count * 0.5 + 0.1,  # Slightly offset
                    departLane="best"
                )
                
                # Set destination vehicle target
                traci.vehicle.changeTarget(pair['dest_id'], src_edge)
                
                # Store vehicle data
                pair['source_edge'] = src_edge
                pair['dest_edge'] = dst_edge
                pair['placed'] = True
                
                placed_count += 1
                logger.info(f"Placed V2V pair {pair['scenario_id']}: {pair['source_id']} -> {pair['dest_id']}")
                
            except Exception as e:
                logger.warning(f"Failed to place V2V pair {pair['scenario_id']}: {e}")
                continue
                
        logger.info(f"Successfully placed {placed_count} V2V vehicle pairs")
        
    def _simulate_v2v_communication(self, step: int):
        """Simulate V2V communication between vehicle pairs"""
        communication_range = 500  # meters
        
        for pair in self.vehicle_pairs:
            if not pair.get('placed', False):
                continue
                
            try:
                # Check if both vehicles are still in simulation
                if (pair['source_id'] not in traci.vehicle.getIDList() or 
                    pair['dest_id'] not in traci.vehicle.getIDList()):
                    continue
                    
                # Get vehicle positions
                src_pos = traci.vehicle.getPosition(pair['source_id'])
                dest_pos = traci.vehicle.getPosition(pair['dest_id'])
                
                # Calculate distance
                distance = np.sqrt((src_pos[0] - dest_pos[0])**2 + (src_pos[1] - dest_pos[1])**2)
                
                # Check if vehicles are within communication range
                if distance <= communication_range:
                    # Simulate V2V communication
                    success = self._simulate_packet_transmission(pair, distance)
                    
                    if success:
                        self.simulation_results.append({
                            'step': step,
                            'scenario_id': pair['scenario_id'],
                            'source_id': pair['source_id'],
                            'dest_id': pair['dest_id'],
                            'distance': distance,
                            'src_pos': src_pos,
                            'dest_pos': dest_pos,
                            'snr': pair['snr'],
                            'rsrp': pair['rsrp'],
                            'rssi': pair['rssi'],
                            'mcs': pair['mcs']
                        })
                        
            except Exception as e:
                logger.warning(f"Error in V2V communication simulation: {e}")
                continue
                
    def _simulate_packet_transmission(self, pair: Dict, distance: float) -> bool:
        """Simulate packet transmission success"""
        # Use SNR and distance to determine success probability
        snr = pair['snr']
        
        # Distance-based path loss
        path_loss = 20 * np.log10(distance) + 20 * np.log10(2400) - 147.55
        
        # Calculate SINR
        sinr = snr - path_loss
        
        # Success probability based on SINR
        if sinr > 20:
            success_prob = 0.95
        elif sinr > 10:
            success_prob = 0.85
        elif sinr > 0:
            success_prob = 0.70
        else:
            success_prob = 0.30
            
        return random.random() < success_prob
        
    def run_simulation(self, max_steps: int = 1800, gui: bool = False):
        """Run the V2V simulation"""
        logger.info("Starting V2V simulation...")
        
        # SUMO command
        sumo_cmd = [
            "sumo-gui" if gui else "sumo",
            "-c", self.sumo_config,
            "--tripinfo-output", "v2v_tripinfos.xml",
            "--fcd-output", "v2v_fcd.xml",
            "--device.fcd.period", "100",
            "--no-step-log"
        ]
        
        try:
            # Start TraCI
            traci.start(sumo_cmd)
            logger.info("SUMO started successfully")
            
            # Place V2V vehicles
            self._place_v2v_vehicles()
            
            # Run simulation
            step = 0
            while step < max_steps and traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                
                # Simulate V2V communication every 10 steps
                if step % 10 == 0:
                    self._simulate_v2v_communication(step)
                    
                step += 1
                
                if step % 100 == 0:
                    active_vehicles = len(traci.vehicle.getIDList())
                    comm_events = len(self.simulation_results)
                    logger.info(f"Step {step}: {active_vehicles} vehicles, {comm_events} V2V events")
                    
            logger.info(f"Simulation completed after {step} steps")
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            raise
        finally:
            traci.close()
            
    def save_results(self):
        """Save simulation results"""
        logger.info("Saving simulation results...")
        
        # Create results directory
        os.makedirs("v2v_simulation_results", exist_ok=True)
        
        # Save V2V communication events
        if self.simulation_results:
            comm_df = pd.DataFrame(self.simulation_results)
            comm_df.to_csv("v2v_simulation_results/v2v_communication_events.csv", index=False)
            
            # Statistics
            stats = {
                'total_v2v_events': len(self.simulation_results),
                'unique_scenarios': len(set([e['scenario_id'] for e in self.simulation_results])),
                'average_distance': np.mean([e['distance'] for e in self.simulation_results]),
                'max_distance': np.max([e['distance'] for e in self.simulation_results]),
                'min_distance': np.min([e['distance'] for e in self.simulation_results]),
                'simulation_steps': max([e['step'] for e in self.simulation_results]) if self.simulation_results else 0
            }
            
            with open("v2v_simulation_results/v2v_stats.json", 'w') as f:
                json.dump(stats, f, indent=2)
                
        # Save vehicle pair data
        pairs_df = pd.DataFrame(self.vehicle_pairs)
        pairs_df.to_csv("v2v_simulation_results/vehicle_pairs.csv", index=False)
        
        logger.info("Results saved to v2v_simulation_results/")


def main():
    """Main function to run V2V simulation"""
    
    # Configuration
    csv_file = "sidelink_parsed.csv"
    sumo_config = "sumo-config/osm.sumocfg"
    
    # Check if files exist
    if not os.path.exists(csv_file):
        logger.error(f"CSV file not found: {csv_file}")
        return
        
    if not os.path.exists(sumo_config):
        logger.error(f"SUMO config not found: {sumo_config}")
        return
    
    try:
        # Create simulator
        simulator = V2VSumoSimulator(csv_file, sumo_config)
        
        # Run simulation with GUI
        simulator.run_simulation(max_steps=1800, gui=True)
        
        # Save results
        simulator.save_results()
        
        logger.info("V2V simulation completed successfully!")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
