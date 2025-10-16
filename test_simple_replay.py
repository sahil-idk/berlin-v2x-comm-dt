#!/usr/bin/env python3
"""
Simple test for digital twin V2V replay
"""

import traci
import pandas as pd
import time
from utils.dataset import DatasetProcessor
from utils.mapping import GPSSumoMapper
from simulation.replayer import ContinuousReplayer

def test_simple_replay():
    """Test simple replay functionality"""
    
    print("🧪 Testing Simple Digital Twin Replay")
    print("=" * 40)
    
    # Start SUMO
    try:
        sumo_cmd = ["sumo", "-c", "osm_headless.sumocfg", "--no-step-log"]
        print("🚀 Starting SUMO...")
        traci.start(sumo_cmd)
        time.sleep(2)
        print("✅ SUMO started")
    except Exception as e:
        print(f"❌ Failed to start SUMO: {e}")
        return
    
    try:
        # Load dataset
        print("\n📋 Loading dataset...")
        processor = DatasetProcessor()
        df = processor.load_and_filter(source_id=2, destination_id=4)
        print(f"✅ Loaded {len(df)} records")
        
        # Get first 100 records for testing
        test_data = df.head(100)
        timestamps, src_lats, src_lons, dst_lats, dst_lons, distances = \
            processor.get_trajectory_data()
        
        # Take first 100 points
        timestamps = timestamps[:100]
        src_lats = src_lats[:100]
        src_lons = src_lons[:100]
        dst_lats = dst_lats[:100]
        dst_lons = dst_lons[:100]
        distances = distances[:100]
        
        print(f"📊 Test data: {len(timestamps)} points")
        print(f"   Time range: {timestamps[0]:.1f}s - {timestamps[-1]:.1f}s")
        print(f"   Distance range: {distances.min():.1f}m - {distances.max():.1f}m")
        
        # Initialize mapper and replayer
        mapper = GPSSumoMapper()
        replayer = ContinuousReplayer(mapper)
        
        # Initialize vehicles
        print("\n🚗 Initializing vehicles...")
        if not replayer.initialize_vehicles(2, 4):
            print("❌ Failed to initialize vehicles")
            return
        
        # Test a few position updates
        print("\n🎯 Testing position updates...")
        for i in range(min(10, len(timestamps))):
            print(f"   Step {i}: timestamp={timestamps[i]:.1f}s")
            
            # Convert GPS to SUMO
            src_sumo = mapper.gps_to_sumo_xy(src_lats[i], src_lons[i])
            dst_sumo = mapper.gps_to_sumo_xy(dst_lats[i], dst_lons[i])
            
            print(f"     Source GPS: ({src_lats[i]:.6f}, {src_lons[i]:.6f})")
            print(f"     Source SUMO: {src_sumo}")
            print(f"     Dest GPS: ({dst_lats[i]:.6f}, {dst_lons[i]:.6f})")
            print(f"     Dest SUMO: {dst_sumo}")
            
            if src_sumo and dst_sumo:
                # Find edges
                src_edge = mapper.find_closest_edge(src_sumo[0], src_sumo[1])
                dst_edge = mapper.find_closest_edge(dst_sumo[0], dst_sumo[1])
                print(f"     Source edge: {src_edge}")
                print(f"     Dest edge: {dst_edge}")
                
                # Update positions
                success = replayer.update_vehicle_positions(
                    src_lats[i], src_lons[i], dst_lats[i], dst_lons[i]
                )
                print(f"     Update success: {success}")
                
                # Get positions
                positions = replayer.get_vehicle_positions()
                print(f"     Current positions: {positions}")
                
                if positions.get('source') and positions.get('destination'):
                    distance_info = replayer.calculate_calibrated_distance(
                        positions['source'], positions['destination']
                    )
                    print(f"     Distance: {distance_info}")
            else:
                print("     ❌ GPS conversion failed")
            
            print()
            
            # Step simulation
            traci.simulation.step()
        
        print("✅ Test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            traci.close()
            print("✅ SUMO stopped")
        except:
            pass

if __name__ == "__main__":
    test_simple_replay()
