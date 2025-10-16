#!/usr/bin/env python3
"""
Minimal V2V Simulation - Only 2 vehicles for testing
Fixes routing issues and focuses on just two vehicles
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

class MinimalV2VSimulator:
    """Minimal V2V Communication Simulator - Only 2 vehicles"""
    
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.vehicle_pair = None
        self.results = []
        
        # Load data
        self._load_data()
        
    def _load_data(self):
        """Load CSV data and create single V2V scenario"""
        logger.info(f"Loading data from {self.csv_file}...")
        
        # Load first 1000 rows
        df = pd.read_csv(self.csv_file, nrows=1000)
        
        # Filter for valid coordinates
        df = df.dropna(subset=['lat', 'lon'])
        
        # Find a good Source-Destination pair
        pairs = df.groupby(['Source', 'Destination']).first().reset_index()
        valid_pairs = pairs[pairs['Source'] != pairs['Destination']]
        
        if len(valid_pairs) > 0:
            # Select first valid pair
            row = valid_pairs.iloc[0]
            
            # Generate destination coordinates near source
            src_lat, src_lon = row['lat'], row['lon']
            dst_lat = src_lat + random.uniform(-0.001, 0.001)
            dst_lon = src_lon + random.uniform(-0.001, 0.001)
            
            self.vehicle_pair = {
                'source_id': f"src_{row['Source']}",
                'dest_id': f"dst_{row['Destination']}",
                'src_coords': (src_lat, src_lon),
                'dst_coords': (dst_lat, dst_lon),
                'snr': row.get('SNR', 15.0),
                'rsrp': row.get('RSRP', -70.0),
                'scenario': row.get('Scenario', 'S1')
            }
            
            logger.info(f"Created V2V pair: {self.vehicle_pair['source_id']} <-> {self.vehicle_pair['dest_id']}")
        else:
            logger.error("No valid V2V pairs found in data")
            
    def _gps_to_sumo(self, lat: float, lon: float):
        """Convert GPS to SUMO coordinates"""
        # Berlin area mapping
        lat_norm = (lat - 52.3) / 0.4
        lon_norm = (lon - 13.0) / 0.8
        x = lon_norm * 19873.71
        y = lat_norm * 12467.71
        return x, y
        
    def _get_connected_edges(self):
        """Get two connected edges for vehicle placement"""
        try:
            edges = traci.edge.getIDList()
            
            # Filter for valid edges
            valid_edges = [e for e in edges if not e.startswith('-') and not e.startswith(':')]
            
            if len(valid_edges) < 2:
                logger.error("Not enough valid edges found")
                return None, None
                
            # Try to find connected edges
            for src_edge in valid_edges[:10]:  # Check first 10 edges
                for dst_edge in valid_edges[:10]:
                    if src_edge != dst_edge:
                        try:
                            # Check if edges are connected
                            route = traci.simulation.findRoute(src_edge, dst_edge)
                            if len(route.edges) > 0:
                                logger.info(f"Found connected edges: {src_edge} -> {dst_edge}")
                                return src_edge, dst_edge
                        except:
                            continue
                            
            # Fallback: use first two valid edges
            logger.warning("No connected edges found, using first two valid edges")
            return valid_edges[0], valid_edges[1]
            
        except Exception as e:
            logger.error(f"Error finding edges: {e}")
            return None, None
            
    def run_simulation(self):
        """Run the minimal V2V simulation"""
        logger.info("Starting minimal V2V simulation...")
        
        if not self.vehicle_pair:
            logger.error("No vehicle pair available")
            return
            
        # SUMO command
        sumo_cmd = [
            "sumo-gui",
            "-c", "sumo-config/osm.sumocfg",
            "--tripinfo-output", "minimal_v2v_trips.xml",
            "--fcd-output", "minimal_v2v_fcd.xml",
            "--no-step-log"
        ]
        
        try:
            # Start SUMO
            traci.start(sumo_cmd)
            logger.info("SUMO started successfully")
            
            # Get connected edges
            src_edge, dst_edge = self._get_connected_edges()
            
            if not src_edge or not dst_edge:
                logger.error("Could not find suitable edges")
                return
                
            # Place vehicles
            self._place_vehicles(src_edge, dst_edge)
            
            # Run simulation
            step = 0
            max_steps = 1800
            
            while step < max_steps and traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                
                # Check V2V communication every 10 steps
                if step % 10 == 0:
                    self._check_v2v_communication(step)
                    
                # Zoom to vehicles every 50 steps
                if step % 50 == 0 and step > 0:
                    self._zoom_to_vehicles()
                    
                step += 1
                
                if step % 100 == 0:
                    active = len(traci.vehicle.getIDList())
                    events = len(self.results)
                    logger.info(f"Step {step}: {active} vehicles, {events} V2V events")
                    
            logger.info(f"Simulation completed after {step} steps")
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
        finally:
            traci.close()
            
    def _place_vehicles(self, src_edge: str, dst_edge: str):
        """Place the two V2V vehicles"""
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
            traci.vehicle.changeTarget(self.vehicle_pair['source_id'], dst_edge)
            
            # Add destination vehicle
            traci.vehicle.add(
                vehID=self.vehicle_pair['dest_id'],
                typeID="DEFAULT_VEHTYPE",
                routeID="",
                depart=0.1,
                departLane="best"
            )
            traci.vehicle.changeTarget(self.vehicle_pair['dest_id'], src_edge)
            
            self.vehicle_pair['src_edge'] = src_edge
            self.vehicle_pair['dst_edge'] = dst_edge
            self.vehicle_pair['placed'] = True
            
            logger.info(f"Successfully placed vehicles: {self.vehicle_pair['source_id']} and {self.vehicle_pair['dest_id']}")
            
        except Exception as e:
            logger.error(f"Failed to place vehicles: {e}")
            
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
                zoom = max(200, min(800, distance * 1.5))  # Adaptive zoom
                
                # Set camera view
                traci.gui.setOffset("View #0", center_x, center_y)
                traci.gui.setZoom("View #0", zoom)
                
                logger.info(f"Zoomed to vehicles at center ({center_x:.1f}, {center_y:.1f}) with zoom {zoom:.1f}")
                
        except Exception as e:
            logger.warning(f"Error zooming to vehicles: {e}")
        
    def _check_v2v_communication(self, step: int):
        """Check V2V communication between the two vehicles"""
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
            
            # Check communication range
            if dist <= range_m:
                # Simulate communication success
                success = self._simulate_communication(dist)
                
                if success:
                    self.results.append({
                        'step': step,
                        'source': self.vehicle_pair['source_id'],
                        'dest': self.vehicle_pair['dest_id'],
                        'distance': dist,
                        'src_pos': src_pos,
                        'dst_pos': dst_pos,
                        'snr': self.vehicle_pair['snr'],
                        'rsrp': self.vehicle_pair['rsrp']
                    })
                    
                    logger.info(f"V2V communication at step {step}: distance {dist:.1f}m")
                    
        except Exception as e:
            logger.warning(f"Communication check error: {e}")
                
    def _simulate_communication(self, distance: float) -> bool:
        """Simulate V2V communication success"""
        snr = self.vehicle_pair['snr']
        
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
        
        os.makedirs("minimal_v2v_results", exist_ok=True)
        
        # Save communication events
        if self.results:
            df = pd.DataFrame(self.results)
            df.to_csv("minimal_v2v_results/communication_events.csv", index=False)
            
            # Statistics
            stats = {
                'total_events': len(self.results),
                'avg_distance': np.mean([r['distance'] for r in self.results]),
                'min_distance': np.min([r['distance'] for r in self.results]),
                'max_distance': np.max([r['distance'] for r in self.results]),
                'avg_snr': np.mean([r['snr'] for r in self.results])
            }
            
            with open("minimal_v2v_results/stats.json", 'w') as f:
                json.dump(stats, f, indent=2)
                
        # Save vehicle pair info
        if self.vehicle_pair:
            with open("minimal_v2v_results/vehicle_pair.json", 'w') as f:
                json.dump(self.vehicle_pair, f, indent=2)
        
        logger.info("Results saved to minimal_v2v_results/")


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
        # Create and run minimal simulator
        simulator = MinimalV2VSimulator(csv_file)
        simulator.run_simulation()
        simulator.save_results()
        
        logger.info("Minimal V2V simulation completed!")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
