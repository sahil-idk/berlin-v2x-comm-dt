#!/usr/bin/env python3
"""
Simplified SUMO TraCI simulation using PC2 CSV data
"""

import traci
import pandas as pd
import numpy as np
import sys
import os
import time

class SimpleSUMOSimulation:
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
        
        # Sample data for faster simulation (every 10th point)
        self.df = self.df.iloc[::10].reset_index(drop=True)
        print(f"Using {len(self.df)} sampled data points for simulation")
        
        return True
    
    def add_vehicle(self):
        """Add vehicle to simulation"""
        if self.vehicle_added:
            return True
            
        try:
            # Add vehicle to the first edge
            traci.vehicle.add(
                vehID=self.vehicle_id,
                routeID="route_1",
                typeID="DEFAULT_VEHTYPE",
                depart=0,
                departLane="best",
                departPos=0.0,
                departSpeed=0.0
            )
            
            self.vehicle_added = True
            print(f"Vehicle {self.vehicle_id} added successfully")
            return True
            
        except Exception as e:
            print(f"Error adding vehicle: {e}")
            return False
    
    def update_vehicle_movement(self):
        """Update vehicle movement based on PC2 data"""
        if not self.vehicle_added or self.data_index >= len(self.df):
            return False
        
        # Get current data point
        current_point = self.df.iloc[self.data_index]
        speed_kmh = current_point['speed_kmh']
        speed_ms = speed_kmh / 3.6  # Convert km/h to m/s
        
        try:
            # Set vehicle speed
            traci.vehicle.setSpeed(self.vehicle_id, speed_ms)
            
            # Print progress every 50 steps
            if self.current_step % 50 == 0:
                print(f"Step {self.current_step}: Speed {speed_kmh:.2f} km/h ({speed_ms:.2f} m/s)")
            
            self.data_index += 1
            return True
            
        except Exception as e:
            print(f"Error updating vehicle movement: {e}")
            self.data_index += 1
            return False
    
    def run_simulation(self):
        """Run the SUMO TraCI simulation"""
        print("Starting Simple SUMO TraCI simulation...")
        
        # Load data
        if not self.load_data():
            return False
        
        # Connect to SUMO
        try:
            traci.start([
                'sumo-gui',
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
            max_steps = min(1000, len(self.df))  # Limit simulation steps
            
            while traci.simulation.getMinExpectedNumber() > 0 and self.data_index < max_steps:
                # Add vehicle if not added yet
                if not self.vehicle_added:
                    if not self.add_vehicle():
                        print("Failed to add vehicle, exiting...")
                        break
                
                # Update vehicle movement
                self.update_vehicle_movement()
                
                # Advance simulation
                traci.simulationStep()
                self.current_step += 1
                
                # Add small delay for visualization
                time.sleep(0.05)
            
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
    print("=== Simple SUMO TraCI Simulation with PC2 Data ===\n")
    
    # Check if required files exist
    required_files = ['pc2_parsed.csv', 'berlin_simulation.sumocfg']
    for file in required_files:
        if not os.path.exists(file):
            print(f"ERROR: Required file {file} not found!")
            return False
    
    # Create simple network if it doesn't exist
    if not os.path.exists('berlin_network.net.xml'):
        print("Network file not found. Creating simple Berlin network...")
        from create_simple_berlin_network import create_simple_network
        create_simple_network()
    
    # Create and run simulation
    simulation = SimpleSUMOSimulation('pc2_parsed.csv')
    success = simulation.run_simulation()
    
    if success:
        print("\n✅ Simulation completed successfully!")
    else:
        print("\n❌ Simulation failed!")
    
    return success

if __name__ == "__main__":
    main()
