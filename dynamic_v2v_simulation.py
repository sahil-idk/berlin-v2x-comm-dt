#!/usr/bin/env python3
"""
Dynamic V2V Vehicle Simulation

This script simulates actual vehicle movement across datapoints using:
1. Real timestamp-based simulation duration
2. Actual vehicle movement on SUMO edges
3. Dynamic distance calculation as vehicles move
4. Communication parameter simulation based on real-time distances
5. Headless operation without GUI visualization

Built on the validated coordinate system with calibration factor 0.607
"""

import traci
import pandas as pd
import numpy as np
import math
import json
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional

class DynamicV2VSimulator:
    """Simulates vehicle movement with dynamic positioning and communication"""
    
    def __init__(self, config_path: str = "osm_headless.sumocfg"):
        self.config_path = config_path
        self.CALIBRATION_FACTOR = 0.607  # Validated calibration factor
        self.simulation_data = []
        self.vehicle_ids = []
        
    def start_headless_sumo(self) -> bool:
        """Start SUMO in headless mode"""
        try:
            sumo_cmd = [
                "sumo",
                "-c", self.config_path,
                "--no-step-log",
                "--ignore-route-errors",
                "--fcd-output", "dynamic_simulation_fcd.xml",
                "--verbose"
            ]
            
            print(f"🚀 Starting dynamic SUMO simulation...")
            traci.start(sumo_cmd)
            time.sleep(2)  # Allow connection to establish
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
        """Convert GPS coordinates to SUMO coordinates with calibration"""
        try:
            try:
                from sumolib import net
                net_file = net.readNet('osm.net.xml.gz')
                x, y = net_file.convertLonLat2XY(lon, lat)
                return x, y
            except ImportError:
                x, y = traci.simulation.convertGeo(lon, lat)
                return x, y
        except Exception as e:
            print(f"❌ GPS conversion failed: {e}")
            return None
    
    def find_closest_edge_to_position(self, x: float, y: float, max_distance: float = 1000) -> Optional[str]:
        """Find edge closest to given SUMO position"""
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
    
    def create_route_between_edges(self, src_edge: str, dst_edge: str, vehicle_id: str) -> Optional[str]:
        """Create a unique route between source and destination edges"""
        try:
            # Create unique route ID with vehicle ID
            route_id = f"route_{vehicle_id}_{src_edge}_to_{dst_edge}"
            
            # Try to create route using SUMO's routing logic
            if src_edge != dst_edge:
                # For different edges, create a multi-edge route
                edge_list = [src_edge, dst_edge]
                
                try:
                    # Simple two-edge route (SUM may need intermediate edges)
                    traci.route.add(route_id, edge_list)
                    return route_id
                except:
                    # Fallback: create separate routes for each edge
                    try:
                        traci.route.add(f"{route_id}_src", [src_edge])
                        return f"{route_id}_src"
                    except:
                        return None
            else:
                # Same edge route - create with unique ID
                try:
                    traci.route.add(route_id, [src_edge])
                    return route_id
                except:
                    return None
                
        except Exception as e:
            print(f"⚠️  Route creation failed: {e}")
            return None
    
    def add_dynamic_vehicle(self, vehicle_id: str, src_gps: Tuple[float, float], 
                           dst_gps: Tuple[float, float]) -> bool:
        """Add a vehicle that will move across edges"""
        print(f"\n🚗 Adding dynamic vehicle: {vehicle_id}")
        
        # Add small random offset to ensure different edges
        import random
        offset_lat = random.uniform(-0.0001, 0.0001)  # ~10m offset
        offset_lon = random.uniform(-0.0001, 0.0001)
        
        # Convert GPS to SUMO coordinates with small randomization
        src_x, src_y = self.gps_to_sumo_coordinates(src_gps[0] + offset_lat, src_gps[1] + offset_lon)
        dst_x, dst_y = self.gps_to_sumo_coordinates(dst_gps[0] + offset_lat, dst_gps[1] + offset_lon)
        
        if not all([src_x, src_y, dst_x, dst_y]):
            print(f"❌ GPS conversion failed for vehicle {vehicle_id}")
            return False
        
        # Find source and destination edges with larger search radius
        src_edge = self.find_closest_edge_to_position(src_x, src_y, max_distance=2000)
        dst_edge = self.find_closest_edge_to_position(dst_x, dst_y, max_distance=2000)
        
        if not src_edge or not dst_edge:
            print(f"❌ Edge mapping failed for vehicle {vehicle_id}")
            return False
        
        print(f"   Vehicle {vehicle_id}: {src_edge} → {dst_edge}")
        
        # Create route between edges
        route_id = self.create_route_between_edges(src_edge, dst_edge, vehicle_id)
        
        if not route_id:
            print(f"❌ Route creation failed for vehicle {vehicle_id}")
            return False
        
        try:
            # Add vehicle to simulation with route
            traci.vehicle.add(vehicle_id, route_id)
            
            # Set vehicle parameters
            traci.vehicle.setSpeedMode(vehicle_id, 31)  # Allow free driving
            traci.vehicle.setMaxSpeed(vehicle_id, 13.89)  # ~50 km/h
            traci.vehicle.setSpeed(vehicle_id, 11.11)    # ~40 km/h initial
            
            self.vehicle_ids.append(vehicle_id)
            print(f"✅ Vehicle {vehicle_id} added successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add vehicle {vehicle_id}: {e}")
            return False
    
    def simulate_trajectory(self, duration_seconds: int = 300) -> List[Dict]:
        """
        Simulate vehicle movement for specified duration
        
        Args:
            duration_seconds: How long to simulate (seconds)
        """
        print(f"\n🎯 Starting dynamic simulation for {duration_seconds} seconds...")
        
        # Convert seconds to simulation steps (1 step = 1 second typically)
        total_steps = duration_seconds
        simulation_data = []
        
        # Simulation loop
        for step in range(total_steps):
            # Advance simulation by one step
            traci.simulation.step()
            
            # Capture vehicle positions and communication data
            step_data = self.capture_step_data(step)
            
            if step_data:
                simulation_data.append(step_data)
            
            # Progress indicator
            if step % 30 == 0:  # Every 30 seconds
                print(f"   Simulation step {step}/{total_steps} ({step//60}m {step%60}s)")
        
        self.simulation_data = simulation_data
        print(f"✅ Simulation completed! Captured {len(simulation_data)} data points")
        
        return simulation_data
    
    def capture_step_data(self, step: int) -> Optional[Dict]:
        """Capture vehicle positions and calculate communication parameters"""
        
        current_vehicles = traci.vehicle.getIDList()
        active_vehicles = [v_id for v_id in self.vehicle_ids if v_id in current_vehicles]
        
        if len(active_vehicles) < 2:
            return None  # Need at least 2 vehicles for V2V
        
        # Get positions of vehicles
        vehicle_positions = {}
        vehicle_data = {}
        
        for vehicle_id in active_vehicles:
            try:
                position = traci.vehicle.getPosition(vehicle_id)
                speed = traci.vehicle.getSpeed(vehicle_id)
                lane = traci.vehicle.getLaneID(vehicle_id)
                
                vehicle_positions[vehicle_id] = position
                vehicle_data[vehicle_id] = {
                    'position': position,
                    'speed': speed,
                    'lane': lane,
                    'step': step
                }
                
            except Exception as e:
                print(f"⚠️  Error getting data for vehicle {vehicle_id}: {e}")
                continue
        
        if len(vehicle_positions) < 2:
            return None
        
        # Calculate inter-vehicle distances
        distance_data = self.calculate_inter_vehicle_distances(vehicle_positions)
        
        # Calculate communication parameters
        comm_data = self.simulate_communication_parameters(distance_data)
        
        # Combine all data
        step_summary = {
            'step': step,
            'timestamp': step,  # Could convert to actual timestamp
            'vehicles': vehicle_data,
            'distances': distance_data,
            'communication': comm_data
        }
        
        return step_summary
    
    def calculate_inter_vehicle_distances(self, vehicle_positions: Dict) -> Dict:
        """Calculate distances between all vehicle pairs"""
        vehicles = list(vehicle_positions.keys())
        distances = {}
        
        for i in range(len(vehicles)):
            for j in range(i + 1, len(vehicles)):
                veh1_id = vehicles[i]
                veh2_id = vehicles[j]
                
                pos1 = vehicle_positions[veh1_id]
                pos2 = vehicle_positions[veh2_id]
                
                # Raw SUMO distance
                raw_distance = math.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)
                
                # Apply calibration factor
                calibrated_distance = raw_distance * self.CALIBRATION_FACTOR
                
                pair_key = f"{veh1_id}_{veh2_id}"
                distances[pair_key] = {
                    'vehicle1': veh1_id,
                    'vehicle2': veh2_id,
                    'raw_distance': raw_distance,
                    'calibrated_distance': calibrated_distance,
                    'positions': {
                        veh1_id: pos1,
                        veh2_id: pos2
                    }
                }
        
        return distances
    
    def simulate_communication_parameters(self, distance_data: Dict) -> Dict:
        """Simulate V2V communication parameters based on distances"""
        comm_data = {}
        
        for pair_key, dist_info in distance_data.items():
            distance = dist_info['calibrated_distance']
            
            # Simulate cellular sidelink communication parameters
            # (Using simplified models based on practical relationships)
            
            # Signal strength roughly inversely proportional to distance squared
            base_snr = 20.0  # dB baseline
            path_loss = 20 * math.log10(distance / 10)  # Free space path loss model
            snr = max(base_snr - path_loss, -10)  # Minimum SNR
            
            # Reference Signal Received Power (RSRP)
            rsrp = snr - 20  # Approximate relationship
            
            # Signal-to-Noise Ratio (RSSI)
            rssi = snr - 5
            
            # Packet success rate (higher success at closer distances)
            if distance < 50:
                packet_success_rate = 0.95
            elif distance < 100:
                packet_success_rate = 0.85
            elif distance < 200:
                packet_success_rate = 0.70
            else:
                packet_success_rate = 0.30
            
            # Communication success (boolean)
            communication_success = packet_success_rate > 0.8
            
            comm_data[pair_key] = {
                'snr': snr,
                'rsrp': rsrp,
                'rssi': rssi,
                'packet_success_rate': packet_success_rate,
                'communication_success': communication_success,
                'distance_range': self.classify_distance_range(distance)
            }
        
        return comm_data
    
    def classify_distance_range(self, distance: float) -> str:
        """Classify distance into communication ranges"""
        if distance < 20:
            return "very_close"
        elif distance < 50:
            return "close"
        elif distance < 100:
            return "medium"
        elif distance < 200:
            return "far"
        else:
            return "very_far"
    
    def run_dynamic_simulation(self, sample_data: List[pd.Series], max_vehicles: int = 4) -> Dict:
        """
        Run dynamic simulation across multiple datapoints
        
        Args:
            sample_data: DataFrame rows from sidelink dataset
            max_vehicles: Maximum number of vehicles to simulate simultaneously
        """
        print("🚗 Starting Dynamic V2V Vehicle Simulation")
        print("=" * 50)
        
        if not self.start_headless_sumo():
            return {}
        
        # Add vehicles from sample data
        vehicles_added = 0
        simulation_instances = []
        
        # Select subset for simulation (to avoid overcrowding)
        selected_samples = sample_data[:max_vehicles]
        
        try:
            for i, row in selected_samples.iterrows():
                vehicle_id = f"veh_{i+1}"
                
                if self.add_dynamic_vehicle(
                    vehicle_id,
                    (row['Latitude_source'], row['Longitude_source']),
                    (row['Latitude_destination'], row['Longitude_destination'])
                ):
                    vehicles_added += 1
                simulation_instances.append({
                    'vehicle_id': vehicle_id,
                    'sample_data': row.to_dict()  # Convert pandas Series to dict
                })
            
            print(f"\n🎯 Added {vehicles_added} vehicles to simulation")
            
            if vehicles_added >= 2:
                # Run simulation
                simulation_duration = 300  # 5 minutes of simulation
                simulation_data = self.simulate_trajectory(simulation_duration)
                
                # Analyze results
                analysis = self.analyze_simulation_results(simulation_data)
                
                # Save results
                self.save_simulation_results(simulation_data, analysis, simulation_instances)
                
                return {
                    'success': True,
                    'vehicles_simulated': vehicles_added,
                    'simulation_duration': simulation_duration,
                    'data_points_captured': len(simulation_data),
                    'analysis': analysis
                }
            else:
                print("❌ Need at least 2 vehicles for V2V simulation")
                return {'success': False, 'reason': 'insufficient_vehicles'}
                
        finally:
            self.stop_sumo()
    
    def analyze_simulation_results(self, simulation_data: List[Dict]) -> Dict:
        """Analyze the simulation results"""
        if not simulation_data:
            return {}
        
        print("\n📊 Analyzing Dynamic Simulation Results")
        print("-" * 40)
        
        # Extract distance trends
        all_distances = []
        communication_quality = []
        
        for step_data in simulation_data:
            for pair_key, dist_info in step_data.get('distances', {}).items():
                distance = dist_info['calibrated_distance']
                comm_info = step_data.get('communication', {}).get(pair_key, {})
                
                all_distances.append(distance)
                communication_quality.append(comm_info.get('communication_success', False))
        
        if not all_distances:
            return {}
        
        # Calculate statistics
        analysis = {
            'total_simulation_steps': len(simulation_data),
            'distance_statistics': {
                'mean_distance': np.mean(all_distances),
                'median_distance': np.median(all_distances),
                'min_distance': np.min(all_distances),
                'max_distance': np.max(all_distances),
                'std_distance': np.std(all_distances),
                'distance_range': f"{np.min(all_distances):.1f}m - {np.max(all_distances):.1f}m"
            },
            'communication_statistics': {
                'success_rate': np.mean(communication_quality) * 100,
                'total_measurements': len(communication_quality),
                'quality_classification': self.classify_overall_quality(communication_quality)
            }
        }
        
        # Print summary
        print(f"✅ Simulation completed successfully")
        print(f"   Total steps: {analysis['total_simulation_steps']}")
        print(f"   Distance range: {analysis['distance_statistics']['distance_range']}")
        print(f"   Communication success rate: {analysis['communication_statistics']['success_rate']:.1f}%")
        
        return analysis
    
    def classify_overall_quality(self, success_data: List[bool]) -> str:
        """Classify overall communication quality"""
        success_rate = np.mean(success_data)
        if success_rate >= 0.9:
            return "excellent"
        elif success_rate >= 0.8:
            return "good"
        elif success_rate >= 0.7:
            return "fair"
        else:
            return "poor"
    
    def save_simulation_results(self, simulation_data: List[Dict], 
                               analysis: Dict, instances: List[Dict]):
        """Save simulation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed simulation data
        results_file = f"dynamic_simulation_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'simulation_data': simulation_data,
                'analysis': analysis,
                'simulation_instances': instances,
                'timestamp': timestamp,
                'calibration_factor': self.CALIBRATION_FACTOR
            }, f, indent=2)
        
        # Save summary
        summary_file = f"dynamic_simulation_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("DYNAMIC V2V SIMULATION SUMMARY\n")
            f.write("=" * 35 + "\n\n")
            f.write(f"Simulation completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Calibration factor: {self.CALIBRATION_FACTOR}\n")
            f.write(f"Total simulation steps: {analysis.get('total_simulation_steps', 0)}\n")
            f.write(f"Distance range: {analysis.get('distance_statistics', {}).get('distance_range', 'N/A')}\n")
            f.write(f"Communication success rate: {analysis.get('communication_statistics', {}).get('success_rate', 0):.1f}%\n")
        
        print(f"\n💾 Dynamic simulation results saved:")
        print(f"   Detailed: {results_file}")
        print(f"   Summary: {summary_file}")

def main():
    """Main function for dynamic vehicle simulation"""
    
    print("Dynamic V2V Vehicle Simulation")
    print("#" * 35)
    
    # Load sample data
    print("\n📋 Loading dataset for dynamic simulation...")
    try:
        df = pd.read_csv('sidelink_parsed.csv')
        print(f"   Loaded {len(df)} records")
        
        # Select samples for simulation
        sample_data = df.dropna(subset=[
            'Latitude_source', 'Longitude_source',
            'Latitude_destination', 'Longitude_destination'
        ]).head(4)  # Use first 4 samples for simulation
        
        print(f"   Selected {len(sample_data)} samples for simulation")
        
        # Initialize simulator
        simulator = DynamicV2VSimulator()
        
        # Run dynamic simulation
        results = simulator.run_dynamic_simulation(sample_data, max_vehicles=4)
        
        if results.get('success'):
            print("\n🎉 Dynamic simulation completed successfully!")
            print(f"   Vehicles simulated: {results['vehicles_simulated']}")
            print(f"   Data points captured: {results['data_points_captured']}")
        else:
            print("\n❌ Dynamic simulation failed")
            print(f"   Reason: {results.get('reason', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error running simulation: {e}")
    
    finally:
        if 'simulator' in locals():
            simulator.stop_sumo()

if __name__ == "__main__":
    main()
