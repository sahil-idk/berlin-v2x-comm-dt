#!/usr/bin/env python3
"""
Continuous replay controller for digital twin V2V simulation
"""

import traci
import time
import math
from typing import Dict, List, Tuple, Optional
import numpy as np

class ContinuousReplayer:
    """Continuous replay controller using moveToXY and route following"""
    
    def __init__(self, mapper, calibration_factor: float = 0.607):
        self.mapper = mapper
        self.calibration_factor = calibration_factor
        self.vehicles = {}
        self.routes = {}
        
    def initialize_vehicles(self, source_id: int, destination_id: int) -> bool:
        """Initialize two vehicles for continuous replay"""
        
        print(f"🚗 Initializing vehicles: source_id={source_id}, destination_id={destination_id}")
        
        # Create vehicle IDs
        src_vehicle_id = f"src_{source_id}"
        dst_vehicle_id = f"dst_{destination_id}"
        
        # Create initial routes (short seed edges)
        src_route_id = f"route_{src_vehicle_id}"
        dst_route_id = f"route_{dst_vehicle_id}"
        
        try:
            # Get some initial edges for routes
            edge_ids = traci.edge.getIDList()
            drivable_edges = [e for e in edge_ids if not e.startswith(':') and not e.startswith('-')]
            
            if len(drivable_edges) < 2:
                print("❌ Not enough drivable edges")
                return False
            
            # Create routes
            traci.route.add(src_route_id, [drivable_edges[0]])
            traci.route.add(dst_route_id, [drivable_edges[1]])
            
            # Add vehicles
            traci.vehicle.add(src_vehicle_id, src_route_id)
            traci.vehicle.add(dst_vehicle_id, dst_route_id)
            
            # Set vehicle parameters
            for vehicle_id in [src_vehicle_id, dst_vehicle_id]:
                traci.vehicle.setSpeedMode(vehicle_id, 31)  # Permissive speed mode
                traci.vehicle.setMaxSpeed(vehicle_id, 50.0)  # High max speed
                traci.vehicle.setSpeed(vehicle_id, 30.0)    # Initial speed
            
            # Store vehicle info
            self.vehicles = {
                'source': src_vehicle_id,
                'destination': dst_vehicle_id
            }
            
            self.routes = {
                'source': src_route_id,
                'destination': dst_route_id
            }
            
            print(f"✅ Vehicles initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize vehicles: {e}")
            return False
    
    def update_vehicle_positions(self, src_lat: float, src_lon: float, 
                                dst_lat: float, dst_lon: float) -> bool:
        """Update vehicle positions using moveToXY"""
        
        try:
            # Convert GPS to SUMO coordinates
            src_sumo = self.mapper.gps_to_sumo_xy(src_lat, src_lon)
            dst_sumo = self.mapper.gps_to_sumo_xy(dst_lat, dst_lon)
            
            if not src_sumo or not dst_sumo:
                return False
            
            # Find closest edges
            src_edge = self.mapper.find_closest_edge(src_sumo[0], src_sumo[1])
            dst_edge = self.mapper.find_closest_edge(dst_sumo[0], dst_sumo[1])
            
            if not src_edge or not dst_edge:
                return False
            
            # Move vehicles to positions
            src_vehicle_id = self.vehicles['source']
            dst_vehicle_id = self.vehicles['destination']
            
            # Use moveToXY with keepRoute=2 for flexible positioning
            traci.vehicle.moveToXY(
                src_vehicle_id, src_edge, 0, 
                src_sumo[0], src_sumo[1], 
                keepRoute=2, matchThreshold=100
            )
            
            traci.vehicle.moveToXY(
                dst_vehicle_id, dst_edge, 0,
                dst_sumo[0], dst_sumo[1],
                keepRoute=2, matchThreshold=100
            )
            
            return True
            
        except Exception as e:
            print(f"⚠️  Position update failed: {e}")
            return False
    
    def get_vehicle_positions(self) -> Dict[str, Tuple[float, float]]:
        """Get current vehicle positions"""
        
        positions = {}
        
        try:
            for role, vehicle_id in self.vehicles.items():
                if vehicle_id in traci.vehicle.getIDList():
                    position = traci.vehicle.getPosition(vehicle_id)
                    positions[role] = position
                else:
                    positions[role] = None
            
            return positions
            
        except Exception as e:
            print(f"❌ Failed to get positions: {e}")
            return {}
    
    def calculate_calibrated_distance(self, pos1: Tuple[float, float], 
                                    pos2: Tuple[float, float]) -> Dict[str, float]:
        """Calculate raw and calibrated distance between vehicles"""
        
        if not pos1 or not pos2:
            return {'raw_distance': 0, 'calibrated_distance': 0}
        
        # Calculate raw Euclidean distance
        raw_distance = self.mapper.calculate_distance(pos1, pos2)
        
        # Apply calibration factor
        calibrated_distance = raw_distance * self.calibration_factor
        
        return {
            'raw_distance': raw_distance,
            'calibrated_distance': calibrated_distance
        }
    
    def run_continuous_replay(self, timestamps: np.ndarray,
                             src_lats: np.ndarray, src_lons: np.ndarray,
                             dst_lats: np.ndarray, dst_lons: np.ndarray,
                             evaluation_indices: List[int],
                             tick_size: float = 0.5) -> Dict:
        """Run continuous replay simulation"""
        
        print(f"🎯 Starting continuous replay for {len(timestamps)} timestamps")
        print(f"   Evaluation points: {len(evaluation_indices)}")
        print(f"   Tick size: {tick_size}s")
        
        replay_data = []
        evaluation_data = []
        
        # Initialize simulation time
        sim_time = 0.0
        data_index = 0
        
        while data_index < len(timestamps):
            current_timestamp = timestamps[data_index]
            
            # Update vehicle positions
            success = self.update_vehicle_positions(
                src_lats[data_index], src_lons[data_index],
                dst_lats[data_index], dst_lons[data_index]
            )
            
            # Get current positions (even if update failed, try to get positions)
            positions = self.get_vehicle_positions()
            
            # Calculate distance if both vehicles are present
            distance_info = {'raw_distance': 0, 'calibrated_distance': 0}
            if positions.get('source') and positions.get('destination'):
                distance_info = self.calculate_calibrated_distance(
                    positions['source'], positions['destination']
                )
            
            # Store replay data
            replay_data.append({
                'timestamp': current_timestamp,
                'sim_time': sim_time,
                'data_index': data_index,
                'positions': positions,
                'distance_info': distance_info,
                'success': success
            })
            
            # Check if this is an evaluation timestamp
            if data_index in evaluation_indices:
                evaluation_data.append({
                    'timestamp': current_timestamp,
                    'sim_time': sim_time,
                    'data_index': data_index,
                    'positions': positions,
                    'distance_info': distance_info,
                    'evaluation': True
                })
            
            # Advance simulation
            traci.simulation.step()
            sim_time += tick_size
            
            # Move to next data point
            data_index += 1
            
            # Progress update
            if data_index % 100 == 0:
                print(f"   Progress: {data_index}/{len(timestamps)} ({data_index/len(timestamps)*100:.1f}%)")
        
        print(f"✅ Continuous replay completed")
        print(f"   Replay steps: {len(replay_data)}")
        print(f"   Evaluation points: {len(evaluation_data)}")
        
        return {
            'replay_data': replay_data,
            'evaluation_data': evaluation_data,
            'total_steps': len(replay_data),
            'evaluation_steps': len(evaluation_data)
        }
    
    def cleanup(self):
        """Clean up vehicles and routes"""
        
        try:
            # Remove vehicles
            for vehicle_id in self.vehicles.values():
                if vehicle_id in traci.vehicle.getIDList():
                    traci.vehicle.remove(vehicle_id)
            
            # Remove routes
            for route_id in self.routes.values():
                try:
                    traci.route.remove(route_id)
                except:
                    pass
            
            print("✅ Cleanup completed")
            
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")
