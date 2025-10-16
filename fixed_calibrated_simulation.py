#!/usr/bin/env python3
"""
Fixed Calibrated Dynamic V2V Simulation

CORRECTED APPROACH:
1. Use RAW GPS → SUMO conversion (for valid edge mapping)
2. Place vehicles at RAW SUMO coordinates (feasible placement)
3. Calculate RAW distances as vehicles move
4. Apply calibration factor ONLY to distance calculation (not coordinates)

This fixes the edge placement issue while maintaining distance accuracy.
"""

import traci
import pandas as pd
import numpy as np
import math
import json
import time
from datetime import datetime
from typing import List, Tuple, Dict, Optional

class FixedCalibratedDynamicSimulator:
    """Fixed simulator: raw coordinates + calibrated distances"""
    
    def __init__(self, config_path: str = "osm_headless.sumocfg"):
        self.config_path = config_path
        self.CALIBRATION_FACTOR = 0.607  # Apply to distances only
        self.simulation_data = []
        self.vehicle_tracking = {}
        
    def start_sumo(self) -> bool:
        """Start SUMO simulation"""
        try:
            sumo_cmd = ["sumo", "-c", self.config_path, "--no-step-log"]
            print("🚀 Starting fixed calibrated dynamic SUMO simulation...")
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
    
    def gps_to_raw_sumo_coordinates(self, lat: float, lon: float) -> Optional[Tuple[float, float]]:
        """Convert GPS to RAW SUMO coordinates (for edge placement)"""
        try:
            try:
                from sumolib import net
                net_file = net.readNet('osm.net.xml.gz')
                x, y = net_file.convertLonLat2XY(lon, lat)
            except ImportError:
                x, y = traci.simulation.convertGeo(lon, lat)
            return x, y  # Return RAW coordinates for edge placement
        except Exception as e:
            print(f"❌ GPS conversion failed: {e}")
            return None
    
    def find_closest_edge(self, x: float, y: float, max_distance: float = 2000) -> Optional[str]:
        """Find edge closest to raw SUMO position"""
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
    
    def create_simple_route(self, edge_id: str, vehicle_id: str) -> Optional[str]:
        """Create simple route with slight variation for different vehicles"""
        try:
            # Create unique route with small variation
            import random
            variation = random.uniform(-0.00001, 0.00001)
            
            route_id = f"fixed_route_{vehicle_id}_{edge_id.replace('#', '_').replace('-', '_')}"
            
            traci.route.add(route_id, [edge_id])
            return route_id
            
        except Exception as e:
            print(f"⚠️  Route creation failed: {e}")
            return None
    
    def add_fixed_calibrated_vehicle(self, vehicle_id: str, src_gps: Tuple[float, float], 
                                   dst_gps: Tuple[float, float], expected_distance: float) -> bool:
        """Add vehicle with RAW positioning + calibrated distance calculation"""
        
        print(f"\n🚗 Adding fixed calibrated vehicle: {vehicle_id}")
        print(f"   Expected dataset distance: {expected_distance:.2f}m")
        
        # Convert GPS to RAW SUMO coordinates (feasible for edge placement)
        src_raw = self.gps_to_raw_sumo_coordinates(src_gps[0], src_gps[1])
        dst_raw = self.gps_to_raw_sumo_coordinates(dst_gps[0], dst_gps[1])
        
        if not all([src_raw, dst_raw]):
            return False
        
        print(f"   Raw source: ({src_raw[0]:.1f}, {src_raw[1]:.1f})")
        print(f"   Raw destination: ({dst_raw[0]:.1f}, {dst_raw[1]:.1f})")
        
        # Find edges using RAW coordinates
        src_edge = self.find_closest_edge(src_raw[0], src_raw[1])
        
        # Use source edge for vehicle placement (easier than multi-edge routing)
        if not src_edge:
            dst_edge = self.find_closest_edge(dst_raw[0], dst_raw[1])
            if dst_edge:
                src_edge = dst_edge
            else:
                print(f"❌ No valid edge found for vehicle {vehicle_id}")
                return False
        
        print(f"   Using edge: {src_edge}")
        
        # Store tracking data with CALIBRATION method
        self.vehicle_tracking[vehicle_id] = {
            'src_gps': src_gps,
            'dst_gps': dst_gps,
            'expected_dataset_distance': expected_distance,
            'src_raw_sumo': src_raw,
            'dst_raw_sumo': dst_raw,
            'primary_edge': src_edge,
            'distance_calibration_history': []
        }
        
        # Create route
        route_id = self.create_simple_route(src_edge, vehicle_id)
        if not route_id:
            return False
        
        try:
            # Add vehicle
            traci.vehicle.add(vehicle_id, route_id)
            traci.vehicle.setSpeedMode(vehicle_id, 31)
            traci.vehicle.setMaxSpeed(vehicle_id, 13.89)
            traci.vehicle.setSpeed(vehicle_id, 11.11)
            
            print(f"✅ Fixed calibrated vehicle {vehicle_id} added successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add vehicle {vehicle_id}: {e}")
            return False
    
    def calculate_fixed_calibrated_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> Dict:
        """Calculate calibrated distance using FIXED approach"""
        
        # Step 1: Calculate RAW distance
        raw_distance = math.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)
        
        # Step 2: Apply calibration factor to distance ONLY
        calibrated_distance = raw_distance * self.CALIBRATION_FACTOR
        
        return {
            'raw_distance': raw_distance,
            'calibrated_distance': calibrated_distance,
            'calibration_applied': True
        }
    
    def run_fixed_calibrated_simulation(self, sample_data: List[pd.Series], 
                                      duration_seconds: int = 120) -> Dict:
        """Run fixed calibrated simulation"""
        
        print("🚀 FIXED CALIBRATED DYNAMIC V2V SIMULATION")
        print("=" * 48)
        print("CORRECTED APPROACH:")
        print("  1. RAW GPS→SUMO coordinates (for edge placement)")
        print("  2. Vehicle placement on RAW coordinates")
        print("  3. CALIBRATED distance calculation")
        print(f"Calibration factor: {self.CALIBRATION_FACTOR}")
        print("=" * 48)
        
        try:
            # Add vehicles with fixed approach
            vehicles_added = 0
            for i, (_, row) in enumerate(sample_data.head(3).iterrows()):
                vehicle_id = f"fixed_calibrated_veh_{i+1}"
                
                if self.add_fixed_calibrated_vehicle(
                    vehicle_id,
                    (row['Latitude_source'], row['Longitude_source']),
                    (row['Latitude_destination'], row['Longitude_destination']),
                    row['distance']
                ):
                    vehicles_added += 1
            
            print(f"\n🎯 Added {vehicles_added} fixed calibrated vehicles")
            
            if vehicles_added >= 2:
                # Run simulation
                results = self.simulate_fixed_calibrated_movement(duration_seconds)
                
                # Analyze results
                analysis = self.analyze_fixed_results(results)
                
                # Save results
                self.save_fixed_results(results, analysis)
                
                return {
                    'success': True,
                    'vehicles': vehicles_added,
                    'simulation_steps': len(results['simulation_data']),
                    'distance_validations': len(results['distance_history']),
                    'analysis': analysis
                }
            else:
                print("❌ Need at least 2 vehicles")
                return {'success': False, 'reason': 'insufficient_vehicles'}
                
        finally:
            self.stop_sumo()
    
    def simulate_fixed_calibrated_movement(self, duration: int) -> Dict:
        """Simulate movement with fixed calibrated distance calculation"""
        
        print(f"\n🎯 Starting fixed calibrated simulation for {duration} seconds...")
        
        simulation_data = []
        distance_history = []
        
        for step in range(duration):
            # Advance simulation
            traci.simulation.step()
            
            # Calculate calibrated distances between vehicles
            distance_validation = self.validate_fixed_calibrated_distances(step)
            
            # Capture movement data
            movement_data = self.capture_fixed_movement_data(step)
            
            # Combine data
            step_data = {
                'step': step,
                'timestamp': step,
                'movement_data': movement_data,
                'calibrated_distance_validation': distance_validation
            }
            
            simulation_data.append(step_data)
            
            if distance_validation['vehicle_pairs']:
                distance_history.append(distance_validation)
            
            # Progress update
            if step % 30 == 0 and distance_history:
                latest = distance_history[-1]
                if 'calibration_summary' in latest:
                    avg_error = latest['calibration_summary'].get('mean_error_percentage', 0)
                    pairs = latest['calibration_summary'].get('total_pairs', 0)
                    print(f"   Step {step}/{duration}: {pairs} pairs, avg error: {avg_error:.1f}%")
        
        print(f"✅ Fixed calibrated simulation completed!")
        print(f"   Captured {len(simulation_data)} steps")
        print(f"   Validated distances at {len(distance_history)} steps")
        
        return {
            'simulation_data': simulation_data,
            'distance_history': distance_history
        }
    
    def validate_fixed_calibrated_distances(self, step: int) -> Dict:
        """Validate distances using fixed calibrated approach"""
        
        validation = {
            'step': step,
            'vehicle_pairs': {},
            'calibration_summary': {}
        }
        
        active_vehicles = [v_id for v_id in self.vehicle_tracking.keys() 
                          if v_id in traci.vehicle.getIDList()]
        
        if len(active_vehicles) < 2:
            return validation
        
        pair_count = 0
        all_errors = []
        
        for i in range(len(active_vehicles)):
            for j in range(i + 1, len(active_vehicles)):
                veh1_id = active_vehicles[i]
                veh2_id = active_vehicles[j]
                
                pair_count += 1
                try:
                    # Get real-time positions
                    pos1 = traci.vehicle.getPosition(veh1_id)
                    pos2 = traci.vehicle.getPosition(veh2_id)
                    
                    # Calculate FIXED calibrated distance
                    distance_info = self.calculate_fixed_calibrated_distance(pos1, pos2)
                    
                    # Get expected distance from dataset
                    veh1_data = self.vehicle_tracking[veh1_id]
                    veh2_data = self.vehicle_tracking[veh2_id]
                    
                    # Simple expected distance (should improve with better calculation)
                    expected_distance = veh1_data['expected_dataset_distance']
                    
                    # Calculate accuracy
                    error = abs(distance_info['calibrated_distance'] - expected_distance)
                    error_percentage = (error / expected_distance) * 100 if expected_distance > 0 else 0
                    
                    pair_key = f"fixed_pair_{pair_count}_{veh1_id}_{veh2_id}"
                    validation['vehicle_pairs'][pair_key] = {
                        'vehicle1': veh1_id,
                        'vehicle2': veh2_id,
                        'raw_distance': distance_info['raw_distance'],
                        'calibrated_distance': distance_info['calibrated_distance'],
                        'expected_distance': expected_distance,
                        'error': error,
                        'error_percentage': error_percentage,
                        'positions': {'veh1': pos1, 'veh2': pos2}
                    }
                    
                    all_errors.append(error_percentage)
                    
                except Exception as e:
                    print(f"⚠️  Error validating pair: {e}")
                    continue
        
        # Summary statistics
        if all_errors:
            validation['calibration_summary'] = {
                'total_pairs': len(all_errors),
                'mean_error_percentage': np.mean(all_errors),
                'median_error_percentage': np.median(all_errors),
                'std_error_percentage': np.std(all_errors),
                'calibration_factor_applied': self.CALIBRATION_FACTOR
            }
        
        return validation
    
    def capture_fixed_movement_data(self, step: int) -> Dict:
        """Capture movement and communication data using fixed calibrated approach"""
        
        active_vehicles = [v_id for v_id in self.vehicle_tracking.keys() 
                          if v_id in traci.vehicle.getIDList()]
        
        movement_data = {
            'vehicles': {},
            'calibrated_distances': {},
            'communication': {}
        }
        
        # Capture vehicle data
        for vehicle_id in active_vehicles:
            try:
                position = traci.vehicle.getPosition(vehicle_id)
                speed = traci.vehicle.getSpeed(vehicle_id)
                
                movement_data['vehicles'][vehicle_id] = {
                    'position': position,
                    'speed': speed,
                    'step': step
                }
            except Exception as e:
                continue
        
        # Calculate calibrated distances and communication
        if len(active_vehicles) >= 2:
            for i in range(len(active_vehicles)):
                for j in range(i + 1, len(active_vehicles)):
                    veh1_id = active_vehicles[i]
                    veh2_id = active_vehicles[j]
                    
                    pos1 = movement_data['vehicles'][veh1_id]['position']
                    pos2 = movement_data['vehicles'][veh2_id]['position']
                    
                    # Fixed calibrated distance
                    distance_info = self.calculate_fixed_calibrated_distance(pos1, pos2)
                    
                    pair_key = f"{veh1_id}_{veh2_id}"
                    movement_data['calibrated_distances'][pair_key] = distance_info
                    
                    # Communication based on calibrated distance
                    calibrated_dist = distance_info['calibrated_distance']
                    snr = self.calculate_fixed_snr(calibrated_dist)
                    
                    movement_data['communication'][pair_key] = {
                        'snr': snr,
                        'rsrp': snr - 20,
                        'rssi': snr - 5,
                        'communication_success': snr > 5,
                        'calibrated_distance': calibrated_dist
                    }
        
        return movement_data
    
    def calculate_fixed_snr(self, calibrated_distance: float) -> float:
        """Calculate SNR based on calibrated distance"""
        base_snr = 20.0
        path_loss = 20 * math.log10(max(calibrated_distance, 1) / 10)
        snr = max(base_snr - path_loss, -10)
        return snr
    
    def analyze_fixed_results(self, results: Dict) -> Dict:
        """Analyze fixed calibrated simulation results"""
        
        print("\n📊 Analyzing Fixed Calibrated Results")
        print("-" * 37)
        
        distance_history = results['distance_history']
        simulation_data = results['simulation_data']
        
        # Extract all accuracy data
        all_calibrated_distances = []
        all_errors = []
        all_communication_data = []
        
        for validation in distance_history:
            for pair_data in validation['vehicle_pairs'].values():
                all_calibrated_distances.append(pair_data['calibrated_distance'])
                all_errors.append(pair_data['error_percentage'])
        
        for step_data in simulation_data:
            comm_data = step_data['movement_data'].get('communication', {})
            for pair_data in comm_data.values():
                all_communication_data.append(pair_data)
        
        analysis = {
            'fixed_calibrated_distance_accuracy': {
                'mean_error_percentage': np.mean(all_errors) if all_errors else 0,
                'median_error_percentage': np.median(all_errors) if all_errors else 0,
                'std_error_percentage': np.std(all_errors) if all_errors else 0,
                'total_validations': len(all_errors),
                'distance_range': f"{np.min(all_calibrated_distances):.1f}m - {np.max(all_calibrated_distances):.1f}m" if all_calibrated_distances else "N/A"
            },
            'fixed_calibrated_communication': {
                'mean_snr': np.mean([comm['snr'] for comm in all_communication_data]) if all_communication_data else 0,
                'communication_success_rate': np.mean([comm['communication_success'] for comm in all_communication_data]) * 100 if all_communication_data else 0,
                'total_measurements': len(all_communication_data)
            },
            'simulation_performance': {
                'total_steps': len(simulation_data),
                'vehicles_tracked': len(self.vehicle_tracking),
                'distance_validations': len(distance_history)
            }
        }
        
        # Print summary
        print(f"✅ Fixed calibrated analysis completed!")
        print(f"   Distance accuracy: {analysis['fixed_calibrated_distance_accuracy']['mean_error_percentage']:.1f}%")
        print(f"   Calibration factor: {self.CALIBRATION_FACTOR}")
        print(f"   Distance range: {analysis['fixed_calibrated_distance_accuracy']['distance_range']}")
        print(f"   Communication success: {analysis['fixed_calibrated_communication']['communication_success_rate']:.1f}%")
        
        return analysis
    
    def save_fixed_results(self, results: Dict, analysis: Dict):
        """Save fixed calibrated simulation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        summary_file = f"fixed_calibrated_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("FIXED CALIBRATED DYNAMIC V2V SIMULATION SUMMARY\n")
            f.write("=" * 49 + "\n\n")
            f.write(f"Corrected approach: GPS calibration for distances only\n")
            f.write(f"Calibration factor: {self.CALIBRATION_FACTOR}\n")
            f.write(f"Simulation steps: {analysis['simulation_performance']['total_steps']}\n")
            f.write(f"Vehicles tracked: {analysis['simulation_performance']['vehicles_tracked']}\n")
            f.write(f"Distance validations: {analysis['simulation_performance']['distance_validations']}\n")
            f.write(f"Distance accuracy: {analysis['fixed_calibrated_distance_accuracy']['mean_error_percentage']:.1f}%\n")
            f.write(f"Distance range: {analysis['fixed_calibrated_distance_accuracy']['distance_range']}\n")
            f.write(f"Communication success: {analysis['fixed_calibrated_communication']['communication_success_rate']:.1f}%\n")
            f.write(f"Average SNR: {analysis['fixed_calibrated_communication']['mean_snr']:.1f}dB\n")
        
        print(f"\n💾 Fixed calibrated results saved: {summary_file}")

def main():
    """Main function for fixed calibrated simulation"""
    
    print("Fixed Calibrated Dynamic V2V Simulation")
    print("=" * 37)
    print("CORRECTED APPROACH: Raw coordinates + Calibrated distances")
    print()
    
    # Load dataset
    df = pd.read_csv('sidelink_parsed.csv')
    sample_data = df.dropna(subset=[
        'Latitude_source', 'Longitude_source',
        'Latitude_destination', 'Longitude_destination', 
        'distance'
    ]).head(3)
    
    print(f"📋 Loaded {len(df)} records, selected {len(sample_data)} samples")
    
    # Initialize fixed simulator
    simulator = FixedCalibratedDynamicSimulator()
    
    if simulator.start_sumo():
        # Run fixed calibrated simulation
        results = simulator.run_fixed_calibrated_simulation(sample_data, duration_seconds=120)
        
        if results.get('success'):
            print("\n🎉 Fixed calibrated simulation completed!")
            print(f"   Vehicles: {results['vehicles']}")
            print(f"   Simulation steps: {results['simulation_steps']}")
            print(f"   Distance validations: {results['distance_validations']}")
        else:
            print(f"\n❌ Fixed simulation failed: {results.get('reason', 'Unknown')}")
    else:
        print("\n❌ Failed to start SUMO")

if __name__ == "__main__":
    main()
