#!/usr/bin/env python3
"""
Corrected Dynamic V2V Simulation

CORRECTED APPROACH:
1. Use 2 vehicles per validation (source and destination)
2. Place vehicles at actual GPS-mapped positions
3. Compare static GPS distance vs static SUMO distance (not dynamic)
4. Apply calibration factor correctly
"""

import traci
import pandas as pd
import numpy as np
import math
import json
import time
from datetime import datetime
from typing import List, Tuple, Dict, Optional

class CorrectedDynamicSimulator:
    """Corrected simulator with proper 2-vehicle validation"""
    
    def __init__(self, config_path: str = "osm_headless.sumocfg"):
        self.config_path = config_path
        self.CALIBRATION_FACTOR = 0.607
        self.simulation_data = []
        self.vehicle_pairs = {}  # Store vehicle pairs for validation
        
    def start_sumo(self) -> bool:
        """Start SUMO simulation"""
        try:
            sumo_cmd = ["sumo", "-c", self.config_path, "--no-step-log"]
            print("🚀 Starting corrected dynamic SUMO simulation...")
            traci.start(sumo_cmd)
            time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Failed to start SUMO: {e}")
            return False
    
    def stop_sumo(self):
        """Stop SUMO simulation"""
        try:
            traci.close()
            print("✅ SUMO simulation stopped")
        except Exception as e:
            print(f"⚠️  Error stopping SUMO: {e}")
    
    def gps_to_sumo_coordinates(self, lat: float, lon: float) -> Optional[Tuple[float, float]]:
        """Convert GPS to SUMO coordinates"""
        try:
            try:
                from sumolib import net
                net_file = net.readNet('osm.net.xml.gz')
                x, y = net_file.convertLonLat2XY(lon, lat)
            except ImportError:
                x, y = traci.simulation.convertGeo(lon, lat)
            return x, y
        except Exception as e:
            print(f"❌ GPS conversion failed: {e}")
            return None
    
    def find_closest_edge(self, x: float, y: float, max_distance: float = 2000) -> Optional[str]:
        """Find edge closest to SUMO position"""
        min_distance = float('inf')
        closest_edge = None
        
        for edge_id in traci.edge.getIDList():
            if edge_id.startswith(':') or edge_id.startswith('-'):
                continue
                
            try:
                from_junction = traci.edge.getFromJunction(edge_id)
                from_pos = traci.junction.getPosition(from_junction)
                
                distance = math.sqrt((x - from_pos[0])**2 + (y - from_pos[1])**2)
                
                if distance < min_distance and distance < max_distance:
                    min_distance = distance
                    closest_edge = edge_id
                    
            except:
                continue
                
        return closest_edge
    
    def create_route(self, edge_id: str, vehicle_id: str) -> Optional[str]:
        """Create route for vehicle"""
        try:
            route_id = f"corrected_route_{vehicle_id}_{edge_id.replace('#', '_').replace('-', '_')}"
            traci.route.add(route_id, [edge_id])
            return route_id
        except Exception as e:
            print(f"⚠️  Route creation failed: {e}")
            return None
    
    def add_vehicle_pair(self, pair_id: str, src_gps: Tuple[float, float], 
                        dst_gps: Tuple[float, float], expected_distance: float) -> bool:
        """Add a pair of vehicles (source and destination)"""
        
        print(f"\n🚗 Adding vehicle pair: {pair_id}")
        print(f"   Expected GPS distance: {expected_distance:.2f}m")
        
        # Convert GPS to SUMO coordinates
        src_sumo = self.gps_to_sumo_coordinates(src_gps[0], src_gps[1])
        dst_sumo = self.gps_to_sumo_coordinates(dst_gps[0], dst_gps[1])
        
        if not all([src_sumo, dst_sumo]):
            return False
        
        print(f"   Source SUMO: ({src_sumo[0]:.1f}, {src_sumo[1]:.1f})")
        print(f"   Destination SUMO: ({dst_sumo[0]:.1f}, {dst_sumo[1]:.1f})")
        
        # Find edges
        src_edge = self.find_closest_edge(src_sumo[0], src_sumo[1])
        dst_edge = self.find_closest_edge(dst_sumo[0], dst_sumo[1])
        
        if not src_edge or not dst_edge:
            print(f"❌ No valid edges found for pair {pair_id}")
            return False
        
        print(f"   Source edge: {src_edge}")
        print(f"   Destination edge: {dst_edge}")
        
        # Calculate raw SUMO distance
        raw_sumo_distance = math.sqrt((dst_sumo[0] - src_sumo[0])**2 + (dst_sumo[1] - src_sumo[1])**2)
        calibrated_distance = raw_sumo_distance * self.CALIBRATION_FACTOR
        
        print(f"   Raw SUMO distance: {raw_sumo_distance:.2f}m")
        print(f"   Calibrated distance: {calibrated_distance:.2f}m")
        
        # Calculate accuracy
        error = abs(calibrated_distance - expected_distance)
        error_percentage = (error / expected_distance) * 100 if expected_distance > 0 else 0
        
        print(f"   Error: {error:.2f}m ({error_percentage:.1f}%)")
        
        # Store pair data
        self.vehicle_pairs[pair_id] = {
            'src_gps': src_gps,
            'dst_gps': dst_gps,
            'src_sumo': src_sumo,
            'dst_sumo': dst_sumo,
            'src_edge': src_edge,
            'dst_edge': dst_edge,
            'expected_distance': expected_distance,
            'raw_sumo_distance': raw_sumo_distance,
            'calibrated_distance': calibrated_distance,
            'error': error,
            'error_percentage': error_percentage
        }
        
        # Add vehicles
        src_vehicle_id = f"{pair_id}_src"
        dst_vehicle_id = f"{pair_id}_dst"
        
        # Create routes
        src_route = self.create_route(src_edge, src_vehicle_id)
        dst_route = self.create_route(dst_edge, dst_vehicle_id)
        
        if not src_route or not dst_route:
            return False
        
        try:
            # Add source vehicle
            traci.vehicle.add(src_vehicle_id, src_route)
            traci.vehicle.setSpeedMode(src_vehicle_id, 31)
            traci.vehicle.setMaxSpeed(src_vehicle_id, 13.89)
            traci.vehicle.setSpeed(src_vehicle_id, 11.11)
            
            # Add destination vehicle
            traci.vehicle.add(dst_vehicle_id, dst_route)
            traci.vehicle.setSpeedMode(dst_vehicle_id, 31)
            traci.vehicle.setMaxSpeed(dst_vehicle_id, 13.89)
            traci.vehicle.setSpeed(dst_vehicle_id, 11.11)
            
            print(f"✅ Vehicle pair {pair_id} added successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add vehicle pair {pair_id}: {e}")
            return False
    
    def run_corrected_simulation(self, sample_data: List[pd.Series], 
                                duration_seconds: int = 60) -> Dict:
        """Run corrected simulation with proper 2-vehicle validation"""
        
        print("🚀 CORRECTED DYNAMIC V2V SIMULATION")
        print("=" * 40)
        print("CORRECTED APPROACH:")
        print("  1. 2 vehicles per validation (source + destination)")
        print("  2. Static distance validation (GPS vs SUMO)")
        print("  3. Calibration factor applied to distances")
        print(f"Calibration factor: {self.CALIBRATION_FACTOR}")
        print("=" * 40)
        
        try:
            # Add vehicle pairs
            pairs_added = 0
            for i, (_, row) in enumerate(sample_data.head(2).iterrows()):
                pair_id = f"pair_{i+1}"
                
                if self.add_vehicle_pair(
                    pair_id,
                    (row['Latitude_source'], row['Longitude_source']),
                    (row['Latitude_destination'], row['Longitude_destination']),
                    row['distance']
                ):
                    pairs_added += 1
            
            print(f"\n🎯 Added {pairs_added} vehicle pairs ({pairs_added * 2} vehicles)")
            
            if pairs_added > 0:
                # Run simulation
                results = self.simulate_corrected_movement(duration_seconds)
                
                # Analyze results
                analysis = self.analyze_corrected_results(results)
                
                # Save results
                self.save_corrected_results(results, analysis)
                
                return {
                    'success': True,
                    'pairs': pairs_added,
                    'vehicles': pairs_added * 2,
                    'simulation_steps': len(results['simulation_data']),
                    'analysis': analysis
                }
            else:
                print("❌ No vehicle pairs added")
                return {'success': False, 'reason': 'no_pairs_added'}
                
        finally:
            self.stop_sumo()
    
    def simulate_corrected_movement(self, duration: int) -> Dict:
        """Simulate movement with corrected validation"""
        
        print(f"\n🎯 Starting corrected simulation for {duration} seconds...")
        
        simulation_data = []
        
        for step in range(duration):
            # Advance simulation
            traci.simulation.step()
            
            # Capture movement data
            movement_data = self.capture_corrected_movement_data(step)
            
            step_data = {
                'step': step,
                'timestamp': step,
                'movement_data': movement_data
            }
            
            simulation_data.append(step_data)
            
            # Progress update
            if step % 30 == 0:
                active_vehicles = len([v_id for v_id in traci.vehicle.getIDList() 
                                     if any(v_id.startswith(pair) for pair in self.vehicle_pairs.keys())])
                print(f"   Step {step}/{duration}: {active_vehicles} vehicles active")
        
        print(f"✅ Corrected simulation completed!")
        print(f"   Captured {len(simulation_data)} steps")
        
        return {
            'simulation_data': simulation_data
        }
    
    def capture_corrected_movement_data(self, step: int) -> Dict:
        """Capture movement data for corrected simulation"""
        
        movement_data = {
            'vehicles': {},
            'pairs': {}
        }
        
        # Capture vehicle data
        for pair_id, pair_data in self.vehicle_pairs.items():
            src_vehicle_id = f"{pair_id}_src"
            dst_vehicle_id = f"{pair_id}_dst"
            
            pair_movement = {}
            
            for vehicle_id in [src_vehicle_id, dst_vehicle_id]:
                if vehicle_id in traci.vehicle.getIDList():
                    try:
                        position = traci.vehicle.getPosition(vehicle_id)
                        speed = traci.vehicle.getSpeed(vehicle_id)
                        
                        movement_data['vehicles'][vehicle_id] = {
                            'position': position,
                            'speed': speed,
                            'step': step
                        }
                        
                        pair_movement[vehicle_id] = {
                            'position': position,
                            'speed': speed
                        }
                    except Exception as e:
                        continue
            
            # Calculate real-time distance if both vehicles are active
            if len(pair_movement) == 2:
                pos1 = pair_movement[src_vehicle_id]['position']
                pos2 = pair_movement[dst_vehicle_id]['position']
                
                raw_distance = math.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)
                calibrated_distance = raw_distance * self.CALIBRATION_FACTOR
                
                movement_data['pairs'][pair_id] = {
                    'raw_distance': raw_distance,
                    'calibrated_distance': calibrated_distance,
                    'expected_distance': pair_data['expected_distance'],
                    'error': abs(calibrated_distance - pair_data['expected_distance']),
                    'error_percentage': abs(calibrated_distance - pair_data['expected_distance']) / pair_data['expected_distance'] * 100
                }
        
        return movement_data
    
    def analyze_corrected_results(self, results: Dict) -> Dict:
        """Analyze corrected simulation results"""
        
        print("\n📊 Analyzing Corrected Results")
        print("-" * 32)
        
        simulation_data = results['simulation_data']
        
        # Extract all accuracy data
        all_errors = []
        all_distances = []
        
        for step_data in simulation_data:
            pairs_data = step_data['movement_data'].get('pairs', {})
            for pair_data in pairs_data.values():
                all_errors.append(pair_data['error_percentage'])
                all_distances.append(pair_data['calibrated_distance'])
        
        # Static validation (from initial placement)
        static_errors = []
        for pair_data in self.vehicle_pairs.values():
            static_errors.append(pair_data['error_percentage'])
        
        analysis = {
            'static_validation': {
                'mean_error_percentage': np.mean(static_errors) if static_errors else 0,
                'median_error_percentage': np.median(static_errors) if static_errors else 0,
                'std_error_percentage': np.std(static_errors) if static_errors else 0,
                'total_validations': len(static_errors)
            },
            'dynamic_validation': {
                'mean_error_percentage': np.mean(all_errors) if all_errors else 0,
                'median_error_percentage': np.median(all_errors) if all_errors else 0,
                'std_error_percentage': np.std(all_errors) if all_errors else 0,
                'total_measurements': len(all_errors),
                'distance_range': f"{np.min(all_distances):.1f}m - {np.max(all_distances):.1f}m" if all_distances else "N/A"
            },
            'simulation_performance': {
                'total_steps': len(simulation_data),
                'vehicle_pairs': len(self.vehicle_pairs),
                'total_vehicles': len(self.vehicle_pairs) * 2
            }
        }
        
        # Print summary
        print(f"✅ Corrected analysis completed!")
        print(f"   Static validation accuracy: {analysis['static_validation']['mean_error_percentage']:.1f}%")
        print(f"   Dynamic validation accuracy: {analysis['dynamic_validation']['mean_error_percentage']:.1f}%")
        print(f"   Calibration factor: {self.CALIBRATION_FACTOR}")
        print(f"   Vehicle pairs: {analysis['simulation_performance']['vehicle_pairs']}")
        
        return analysis
    
    def save_corrected_results(self, results: Dict, analysis: Dict):
        """Save corrected simulation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        summary_file = f"corrected_simulation_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("CORRECTED DYNAMIC V2V SIMULATION SUMMARY\n")
            f.write("=" * 42 + "\n\n")
            f.write(f"Approach: 2 vehicles per validation (source + destination)\n")
            f.write(f"Calibration factor: {self.CALIBRATION_FACTOR}\n")
            f.write(f"Simulation steps: {analysis['simulation_performance']['total_steps']}\n")
            f.write(f"Vehicle pairs: {analysis['simulation_performance']['vehicle_pairs']}\n")
            f.write(f"Total vehicles: {analysis['simulation_performance']['total_vehicles']}\n")
            f.write(f"Static validation accuracy: {analysis['static_validation']['mean_error_percentage']:.1f}%\n")
            f.write(f"Dynamic validation accuracy: {analysis['dynamic_validation']['mean_error_percentage']:.1f}%\n")
            f.write(f"Distance range: {analysis['dynamic_validation']['distance_range']}\n")
        
        print(f"\n💾 Corrected results saved: {summary_file}")

def main():
    """Main function for corrected simulation"""
    
    print("Corrected Dynamic V2V Simulation")
    print("=" * 33)
    print("CORRECTED APPROACH: 2 vehicles per validation")
    print()
    
    # Load dataset
    df = pd.read_csv('sidelink_parsed.csv')
    sample_data = df.dropna(subset=[
        'Latitude_source', 'Longitude_source',
        'Latitude_destination', 'Longitude_destination', 
        'distance'
    ]).head(2)  # Only 2 pairs for validation
    
    print(f"📋 Loaded {len(df)} records, selected {len(sample_data)} pairs")
    
    # Initialize corrected simulator
    simulator = CorrectedDynamicSimulator()
    
    if simulator.start_sumo():
        # Run corrected simulation
        results = simulator.run_corrected_simulation(sample_data, duration_seconds=60)
        
        if results.get('success'):
            print("\n🎉 Corrected simulation completed!")
            print(f"   Vehicle pairs: {results['pairs']}")
            print(f"   Total vehicles: {results['vehicles']}")
            print(f"   Simulation steps: {results['simulation_steps']}")
        else:
            print(f"\n❌ Corrected simulation failed: {results.get('reason', 'Unknown')}")
    else:
        print("\n❌ Failed to start SUMO")

if __name__ == "__main__":
    main()
