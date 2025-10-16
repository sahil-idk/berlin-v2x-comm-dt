#!/usr/bin/env python3
"""
Simple V2V Simulation using SUMO TraCI
Loads sidelink_parsed.csv and simulates 50 V2V scenarios using existing SUMO setup
"""

import traci
import pandas as pd
import numpy as np
import json
import os
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleV2VSimulator:
    """Simple V2V Communication Simulator"""
    
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.vehicle_pairs = []
        self.results = []
        
        # Load data
        self._load_data()
        
    def _load_data(self):
        """Load CSV data and create V2V scenarios"""
        logger.info(f"Loading data from {self.csv_file}...")
        
        # Load first 10000 rows to avoid memory issues
        df = pd.read_csv(self.csv_file, nrows=10000)
        
        # Filter for valid coordinates
        df = df.dropna(subset=['lat', 'lon'])
        
        # Group by Source-Destination pairs
        pairs = df.groupby(['Source', 'Destination']).first().reset_index()
        
        # Filter out self-communication
        pairs = pairs[pairs['Source'] != pairs['Destination']]
        
        # Select 50 scenarios
        selected = pairs.sample(n=min(50, len(pairs)), random_state=42)
        
        logger.info(f"Selected {len(selected)} V2V scenarios")
        
        # Create vehicle pairs
        for idx, row in selected.iterrows():
            # Generate destination coordinates near source
            src_lat, src_lon = row['lat'], row['lon']
            dst_lat = src_lat + random.uniform(-0.001, 0.001)
            dst_lon = src_lon + random.uniform(-0.001, 0.001)
            
            self.vehicle_pairs.append({
                'id': idx,
                'source_id': f"src_{row['Source']}_{idx}",
                'dest_id': f"dst_{row['Destination']}_{idx}",
                'src_coords': (src_lat, src_lon),
                'dst_coords': (dst_lat, dst_lon),
                'snr': row.get('SNR', 15.0),
                'rsrp': row.get('RSRP', -70.0),
                'scenario': row.get('Scenario', 'S1')
            })
            
    def _gps_to_sumo(self, lat: float, lon: float):
        """Convert GPS to SUMO coordinates"""
        # Berlin area mapping
        lat_norm = (lat - 52.3) / 0.4
        lon_norm = (lon - 13.0) / 0.8
        x = lon_norm * 19873.71
        y = lat_norm * 12467.71
        return x, y
        
    def _get_valid_edge(self):
        """Get a valid edge from the network"""
        edges = traci.edge.getIDList()
        
        # Filter for edges that are likely to be reachable
        # Avoid edges starting with '-' (incoming edges) and ':' (internal edges)
        valid_edges = [e for e in edges if not e.startswith('-') and not e.startswith(':')]
        
        if not valid_edges:
            # Fallback to any edge that doesn't start with ':'
            valid_edges = [e for e in edges if not e.startswith(':')]
            
        if not valid_edges:
            # Last resort - use any edge
            valid_edges = edges
            
        return random.choice(valid_edges)
        
    def run_simulation(self):
        """Run the V2V simulation"""
        logger.info("Starting V2V simulation...")
        
        # SUMO command
        sumo_cmd = [
            "sumo-gui",
            "-c", "sumo-config/osm.sumocfg",
            "--tripinfo-output", "v2v_trips.xml",
            "--fcd-output", "v2v_fcd.xml",
            "--no-step-log"
        ]
        
        try:
            # Start SUMO
            traci.start(sumo_cmd)
            logger.info("SUMO started successfully")
            
            # Place vehicles
            self._place_vehicles()
            
            # Run simulation
            step = 0
            max_steps = 1800
            
            while step < max_steps and traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                
                # Check V2V communication every 10 steps
                if step % 10 == 0:
                    self._check_v2v_communication(step)
                    
                step += 1
                
                if step % 100 == 0:
                    active = len(traci.vehicle.getIDList())
                    events = len(self.results)
                    logger.info(f"Step {step}: {active} vehicles, {events} V2V events")
                    
                # Zoom to vehicles every 50 steps
                if step % 50 == 0 and step > 0:
                    self._zoom_to_vehicles()
                    
            logger.info(f"Simulation completed after {step} steps")
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
        finally:
            traci.close()
            
    def _place_vehicles(self):
        """Place V2V vehicle pairs"""
        logger.info("Placing V2V vehicles...")
        
        # Get all valid edges first
        all_edges = traci.edge.getIDList()
        valid_edges = [e for e in all_edges if not e.startswith('-') and not e.startswith(':')]
        
        if not valid_edges:
            valid_edges = [e for e in all_edges if not e.startswith(':')]
            
        logger.info(f"Found {len(valid_edges)} valid edges out of {len(all_edges)} total edges")
        
        placed = 0
        
        for pair in self.vehicle_pairs:
            try:
                # Get edges
                src_edge = random.choice(valid_edges)
                dst_edge = random.choice(valid_edges)
                
                # Ensure different edges
                attempts = 0
                while src_edge == dst_edge and attempts < 10:
                    dst_edge = random.choice(valid_edges)
                    attempts += 1
                    
                if src_edge == dst_edge:
                    logger.warning(f"Skipping pair {pair['id']} - same edge")
                    continue
                
                # Check if edges are connected
                if not self._are_edges_connected(src_edge, dst_edge):
                    logger.warning(f"Edges {src_edge} and {dst_edge} not connected, trying different edges")
                    # Try to find connected edges
                    connected_edges = self._find_connected_edges(src_edge, valid_edges)
                    if connected_edges:
                        dst_edge = random.choice(connected_edges)
                    else:
                        logger.warning(f"No connected edges found for {src_edge}, skipping pair {pair['id']}")
                        continue
                
                # Add source vehicle
                traci.vehicle.add(
                    vehID=pair['source_id'],
                    typeID="DEFAULT_VEHTYPE",
                    routeID="",
                    depart=placed * 0.5,
                    departLane="best"
                )
                traci.vehicle.changeTarget(pair['source_id'], dst_edge)
                
                # Add destination vehicle
                traci.vehicle.add(
                    vehID=pair['dest_id'],
                    typeID="DEFAULT_VEHTYPE",
                    routeID="",
                    depart=placed * 0.5 + 0.1,
                    departLane="best"
                )
                traci.vehicle.changeTarget(pair['dest_id'], src_edge)
                
                pair['src_edge'] = src_edge
                pair['dst_edge'] = dst_edge
                pair['placed'] = True
                
                placed += 1
                logger.info(f"Placed pair {pair['id']}: {pair['source_id']} ({src_edge}) -> {pair['dest_id']} ({dst_edge})")
                
            except Exception as e:
                logger.warning(f"Failed to place pair {pair['id']}: {e}")
                continue
                
        logger.info(f"Placed {placed} V2V vehicle pairs")
        
    def _are_edges_connected(self, edge1: str, edge2: str) -> bool:
        """Check if two edges are connected"""
        try:
            # Try to find a route between the edges
            route = traci.simulation.findRoute(edge1, edge2)
            return len(route.edges) > 0
        except:
            return False
            
    def _find_connected_edges(self, source_edge: str, valid_edges: list) -> list:
        """Find edges connected to the source edge"""
        connected = []
        for edge in valid_edges:
            if edge != source_edge and self._are_edges_connected(source_edge, edge):
                connected.append(edge)
        return connected
        
    def _zoom_to_vehicles(self):
        """Zoom camera to focus on V2V vehicles"""
        try:
            active_vehicles = traci.vehicle.getIDList()
            if len(active_vehicles) >= 2:
                # Get positions of first two vehicles
                pos1 = traci.vehicle.getPosition(active_vehicles[0])
                pos2 = traci.vehicle.getPosition(active_vehicles[1])
                
                # Calculate center point
                center_x = (pos1[0] + pos2[0]) / 2
                center_y = (pos1[1] + pos2[1]) / 2
                
                # Calculate zoom level based on distance
                distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                zoom = max(100, min(1000, distance * 2))  # Adaptive zoom
                
                # Set camera view
                traci.gui.setOffset("View #0", center_x, center_y)
                traci.gui.setZoom("View #0", zoom)
                
        except Exception as e:
            logger.warning(f"Error zooming to vehicles: {e}")
        
    def _check_v2v_communication(self, step: int):
        """Check V2V communication between vehicles"""
        range_m = 500  # Communication range
        
        for pair in self.vehicle_pairs:
            if not pair.get('placed', False):
                continue
                
            try:
                # Check if vehicles exist
                if (pair['source_id'] not in traci.vehicle.getIDList() or 
                    pair['dest_id'] not in traci.vehicle.getIDList()):
                    continue
                    
                # Get positions
                src_pos = traci.vehicle.getPosition(pair['source_id'])
                dst_pos = traci.vehicle.getPosition(pair['dest_id'])
                
                # Calculate distance
                dist = np.sqrt((src_pos[0] - dst_pos[0])**2 + (src_pos[1] - dst_pos[1])**2)
                
                # Check communication range
                if dist <= range_m:
                    # Simulate communication success
                    success = self._simulate_communication(pair, dist)
                    
                    if success:
                        self.results.append({
                            'step': step,
                            'pair_id': pair['id'],
                            'source': pair['source_id'],
                            'dest': pair['dest_id'],
                            'distance': dist,
                            'snr': pair['snr'],
                            'rsrp': pair['rsrp']
                        })
                        
            except Exception as e:
                logger.warning(f"Communication check error: {e}")
                
    def _simulate_communication(self, pair: dict, distance: float) -> bool:
        """Simulate V2V communication success"""
        snr = pair['snr']
        
        # Simple success probability based on SNR and distance
        if snr > 20 and distance < 200:
            prob = 0.9
        elif snr > 10 and distance < 400:
            prob = 0.7
        elif snr > 5 and distance < 500:
            prob = 0.5
        else:
            prob = 0.2
            
        return random.random() < prob
        
    def save_results(self):
        """Save simulation results"""
        logger.info("Saving results...")
        
        os.makedirs("v2v_results", exist_ok=True)
        
        # Save communication events
        if self.results:
            df = pd.DataFrame(self.results)
            df.to_csv("v2v_results/communication_events.csv", index=False)
            
            # Statistics
            stats = {
                'total_events': len(self.results),
                'unique_pairs': len(set([r['pair_id'] for r in self.results])),
                'avg_distance': np.mean([r['distance'] for r in self.results]),
                'avg_snr': np.mean([r['snr'] for r in self.results])
            }
            
            with open("v2v_results/stats.json", 'w') as f:
                json.dump(stats, f, indent=2)
                
        # Save vehicle pairs
        pairs_df = pd.DataFrame(self.vehicle_pairs)
        pairs_df.to_csv("v2v_results/vehicle_pairs.csv", index=False)
        
        logger.info("Results saved to v2v_results/")


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
        # Create and run simulator
        simulator = SimpleV2VSimulator(csv_file)
        simulator.run_simulation()
        simulator.save_results()
        
        logger.info("V2V simulation completed!")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
