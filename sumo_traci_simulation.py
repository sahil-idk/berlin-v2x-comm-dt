#!/usr/bin/env python3
"""
SUMO TraCI simulation using PC2 CSV data
Simulates vehicle movement based on real GPS trajectory data
"""

import traci
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
import time

class SUMOTraciSimulation:
    def __init__(self, csv_file='pc2_parsed.csv'):
        """Initialize the simulation with PC2 data"""
        self.csv_file = csv_file
        self.df = None
        self.vehicle_id = "PC2_Vehicle"
        self.current_step = 0
        self.data_index = 0
        self.vehicle_added = False
        
    def load_data(self):
        """Load and prepare PC2 data"""
        print("Loading PC2 data...")
        self.df = pd.read_csv(self.csv_file)
        
        # Clean and prepare data
        self.df = self.df.dropna(subset=['lat', 'lon'])
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        
        print(f"Loaded {len(self.df)} data points")
        print(f"Time range: {self.df['timestamp'].iloc[0]} to {self.df['timestamp'].iloc[-1]}")
        print(f"GPS range: Lat {self.df['lat'].min():.6f}-{self.df['lat'].max():.6f}, "
              f"Lon {self.df['lon'].min():.6f}-{self.df['lon'].max():.6f}")
        
        return True
    
    def find_closest_edge(self, lat, lon):
        """Find the closest edge to given GPS coordinates"""
        try:
            # Convert GPS to SUMO coordinates
            x, y = traci.simulation.convertGeo(lon, lat)
            
            # Find closest edge
            edge_id = traci.simulation.convertRoad(lon, lat, True)
            return edge_id
        except:
            return None
    
    def add_vehicle(self):
        """Add vehicle to simulation"""
        if self.vehicle_added:
            return True
            
        # Get first GPS point
        first_point = self.df.iloc[0]
        lat, lon = first_point['lat'], first_point['lon']
        
        # Find closest edge
        edge_id = self.find_closest_edge(lat, lon)
        
        if edge_id and edge_id != "":
            try:
                # Add vehicle to the simulation
                traci.vehicle.add(
                    vehID=self.vehicle_id,
                    routeID="",  # We'll control position directly
                    typeID="DEFAULT_VEHTYPE",
                    depart=0,
                    departLane="best",
                    departPos=0.0,
                    departSpeed=0.0
                )
                
                # Set initial position
                traci.vehicle.moveToXY(
                    vehID=self.vehicle_id,
                    edgeID=edge_id,
                    lane=0,
                    x=traci.simulation.convertGeo(lon, lat)[0],
                    y=traci.simulation.convertGeo(lon, lat)[1],
                    angle=first_point['COG'],
                    keepRoute=0
                )
                
                self.vehicle_added = True
                print(f"Vehicle {self.vehicle_id} added at edge {edge_id}")
                return True
                
            except Exception as e:
                print(f"Error adding vehicle: {e}")
                return False
        else:
            print("Could not find suitable edge for vehicle")
            return False
    
    def update_vehicle_position(self):
        """Update vehicle position based on PC2 data"""
        if not self.vehicle_added or self.data_index >= len(self.df):
            return False
        
        # Get current data point
        current_point = self.df.iloc[self.data_index]
        lat, lon = current_point['lat'], current_point['lon']
        speed = current_point['speed_kmh'] / 3.6  # Convert km/h to m/s
        angle = current_point['COG']
        
        try:
            # Convert GPS to SUMO coordinates
            x, y = traci.simulation.convertGeo(lon, lat)
            
            # Find current edge
            edge_id = self.find_closest_edge(lat, lon)
            
            if edge_id and edge_id != "":
                # Update vehicle position
                traci.vehicle.moveToXY(
                    vehID=self.vehicle_id,
                    edgeID=edge_id,
                    lane=0,
                    x=x,
                    y=y,
                    angle=angle,
                    keepRoute=0
                )
                
                # Set speed
                traci.vehicle.setSpeed(self.vehicle_id, speed)
                
                # Print progress every 100 steps
                if self.current_step % 100 == 0:
                    print(f"Step {self.current_step}: Position ({lat:.6f}, {lon:.6f}), "
                          f"Speed {speed:.2f} m/s, Edge {edge_id}")
                
                self.data_index += 1
                return True
            else:
                print(f"Warning: Could not find edge for position ({lat}, {lon})")
                self.data_index += 1
                return False
                
        except Exception as e:
            print(f"Error updating vehicle position: {e}")
            self.data_index += 1
            return False
    
    def run_simulation(self):
        """Run the SUMO TraCI simulation"""
        print("Starting SUMO TraCI simulation...")
        
        # Load data
        if not self.load_data():
            return False
        
        # Connect to SUMO
        try:
            traci.start([
                'sumo-gui',  # Use GUI version
                '-c', 'berlin_simulation.sumocfg',
                '--start', 'true',
                '--step-length', '1'
            ])
            print("Connected to SUMO successfully!")
        except Exception as e:
            print(f"Error connecting to SUMO: {e}")
            print("Make sure SUMO is installed and the network file exists.")
            return False
        
        try:
            # Simulation loop
            while traci.simulation.getMinExpectedNumber() > 0 and self.data_index < len(self.df):
                # Add vehicle if not added yet
                if not self.vehicle_added:
                    if not self.add_vehicle():
                        print("Failed to add vehicle, exiting...")
                        break
                
                # Update vehicle position
                self.update_vehicle_position()
                
                # Advance simulation
                traci.simulationStep()
                self.current_step += 1
                
                # Add small delay for visualization
                time.sleep(0.1)
            
            print(f"Simulation completed after {self.current_step} steps")
            print(f"Processed {self.data_index} data points")
            
        except KeyboardInterrupt:
            print("\nSimulation interrupted by user")
        except Exception as e:
            print(f"Simulation error: {e}")
        finally:
            traci.close()
        
        return True

def main():
    """Main function"""
    print("=== SUMO TraCI Simulation with PC2 Data ===\n")
    
    # Check if required files exist
    required_files = ['pc2_parsed.csv', 'berlin_simulation.sumocfg']
    for file in required_files:
        if not os.path.exists(file):
            print(f"ERROR: Required file {file} not found!")
            print("Please make sure all required files are present.")
            return False
    
    # Check if network file exists
    if not os.path.exists('berlin_network.net.xml'):
        print("Network file not found. Creating Berlin network...")
        from create_berlin_network import create_berlin_network
        if not create_berlin_network():
            print("Failed to create network. Exiting...")
            return False
    
    # Create and run simulation
    simulation = SUMOTraciSimulation('pc2_parsed.csv')
    success = simulation.run_simulation()
    
    if success:
        print("\n✅ Simulation completed successfully!")
    else:
        print("\n❌ Simulation failed!")
    
    return success

if __name__ == "__main__":
    main()
