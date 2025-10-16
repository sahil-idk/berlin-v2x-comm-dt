#!/usr/bin/env python3
"""
Simplified Digital Twin using existing working approach
"""

import traci
import pandas as pd
import time
import math
from datetime import datetime

def run_simplified_digital_twin():
    """Run simplified digital twin using existing working approach"""
    
    print("🎯 Simplified Digital Twin V2V Simulation")
    print("=" * 45)
    
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
        df = pd.read_csv('sidelink_parsed.csv')
        filtered_df = df[(df['Source'] == 2) & (df['Destination'] == 4)]
        print(f"✅ Loaded {len(filtered_df)} records for Source=2, Destination=4")
        
        # Take first 100 records for testing
        test_data = filtered_df.head(100)
        print(f"📊 Using {len(test_data)} records for testing")
        
        # Use the existing working GPS-to-SUMO conversion approach
        def gps_to_sumo_coordinates(lat, lon):
            """Convert GPS to SUMO coordinates using existing working method"""
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
        
        # Initialize vehicles using existing working approach
        print("\n🚗 Initializing vehicles...")
        
        # Get some edges for initial routes
        edge_ids = traci.edge.getIDList()
        drivable_edges = [e for e in edge_ids if not e.startswith(':') and not e.startswith('-')]
        
        if len(drivable_edges) < 2:
            print("❌ Not enough drivable edges")
            return
        
        # Create routes
        src_route_id = "src_route_2"
        dst_route_id = "dst_route_4"
        
        traci.route.add(src_route_id, [drivable_edges[0]])
        traci.route.add(dst_route_id, [drivable_edges[1]])
        
        # Add vehicles
        src_vehicle_id = "src_2"
        dst_vehicle_id = "dst_4"
        
        traci.vehicle.add(src_vehicle_id, src_route_id)
        traci.vehicle.add(dst_vehicle_id, dst_route_id)
        
        # Set vehicle parameters
        for vehicle_id in [src_vehicle_id, dst_vehicle_id]:
            traci.vehicle.setSpeedMode(vehicle_id, 31)
            traci.vehicle.setMaxSpeed(vehicle_id, 50.0)
            traci.vehicle.setSpeed(vehicle_id, 30.0)
        
        print("✅ Vehicles initialized")
        
        # Step simulation a few times to ensure vehicles are properly placed
        print("\n🔄 Warming up simulation...")
        for _ in range(3):
            traci.simulation.step()
        
        # Verify vehicles are in simulation
        active_vehicles = traci.vehicle.getIDList()
        print(f"Active vehicles: {active_vehicles}")
        
        if src_vehicle_id not in active_vehicles or dst_vehicle_id not in active_vehicles:
            print(f"❌ Vehicles not properly initialized")
            return
        
        # Run TRUE vehicle simulation with actual movement
        print("\n🎬 Running TRUE vehicle simulation with movement...")
        
        calibration_factor = 0.607
        simulation_data = []
        
        for i, (_, row) in enumerate(test_data.iterrows()):
            timestamp = row['timestamp']
            
            # Convert GPS to SUMO coordinates
            src_sumo = gps_to_sumo_coordinates(row['Latitude_source'], row['Longitude_source'])
            dst_sumo = gps_to_sumo_coordinates(row['Latitude_destination'], row['Longitude_destination'])
            
            if src_sumo and dst_sumo:
                print(f"   Step {i}: GPS src=({row['Latitude_source']:.6f}, {row['Longitude_source']:.6f})")
                print(f"            GPS dst=({row['Latitude_destination']:.6f}, {row['Longitude_destination']:.6f})")
                print(f"            SUMO src=({src_sumo[0]:.1f}, {src_sumo[1]:.1f})")
                print(f"            SUMO dst=({dst_sumo[0]:.1f}, {dst_sumo[1]:.1f})")
                
                # ACTUALLY MOVE VEHICLES TO GPS COORDINATES
                try:
                    # Check if vehicles exist before moving
                    if src_vehicle_id not in traci.vehicle.getIDList() or dst_vehicle_id not in traci.vehicle.getIDList():
                        print(f"            ⚠️  Vehicles not found in simulation")
                        raise Exception("Vehicles not in simulation")
                    
                    # Move source vehicle to GPS position with larger threshold
                    traci.vehicle.moveToXY(
                        src_vehicle_id, "", 0, 
                        src_sumo[0], src_sumo[1], 
                        keepRoute=2, matchThreshold=500
                    )
                    
                    # Move destination vehicle to GPS position with larger threshold
                    traci.vehicle.moveToXY(
                        dst_vehicle_id, "", 0,
                        dst_sumo[0], dst_sumo[1],
                        keepRoute=2, matchThreshold=500
                    )
                    
                    # Get ACTUAL vehicle positions after movement
                    src_actual_pos = traci.vehicle.getPosition(src_vehicle_id)
                    dst_actual_pos = traci.vehicle.getPosition(dst_vehicle_id)
                    
                    # Check if positions are valid (not error values)
                    if (src_actual_pos[0] < -1000000 or src_actual_pos[1] < -1000000 or
                        dst_actual_pos[0] < -1000000 or dst_actual_pos[1] < -1000000):
                        print(f"            ⚠️  Invalid positions after movement")
                        raise Exception("Invalid vehicle positions")
                    
                    print(f"            ACTUAL src pos: ({src_actual_pos[0]:.1f}, {src_actual_pos[1]:.1f})")
                    print(f"            ACTUAL dst pos: ({dst_actual_pos[0]:.1f}, {dst_actual_pos[1]:.1f})")
                    
                    # Calculate distance between ACTUAL vehicle positions
                    actual_raw_distance = math.sqrt(
                        (dst_actual_pos[0] - src_actual_pos[0])**2 + 
                        (dst_actual_pos[1] - src_actual_pos[1])**2
                    )
                    actual_calibrated_distance = actual_raw_distance * calibration_factor
                    
                    # Also calculate theoretical distance (for comparison)
                    theoretical_raw_distance = math.sqrt((dst_sumo[0] - src_sumo[0])**2 + (dst_sumo[1] - src_sumo[1])**2)
                    theoretical_calibrated_distance = theoretical_raw_distance * calibration_factor
                    
                    expected_distance = row['distance']
                    
                    # Calculate errors
                    actual_error = abs(actual_calibrated_distance - expected_distance)
                    actual_error_percentage = (actual_error / expected_distance) * 100 if expected_distance > 0 else 0
                    
                    theoretical_error = abs(theoretical_calibrated_distance - expected_distance)
                    theoretical_error_percentage = (theoretical_error / expected_distance) * 100 if expected_distance > 0 else 0
                    
                    print(f"            Theoretical: {theoretical_calibrated_distance:.2f}m (Error: {theoretical_error_percentage:.1f}%)")
                    print(f"            ACTUAL: {actual_calibrated_distance:.2f}m (Error: {actual_error_percentage:.1f}%)")
                    print(f"            Expected: {expected_distance:.2f}m")
                    
                    # Store data
                    simulation_data.append({
                        'timestamp': timestamp,
                        'step': i,
                        'src_gps': (row['Latitude_source'], row['Longitude_source']),
                        'dst_gps': (row['Latitude_destination'], row['Longitude_destination']),
                        'src_sumo': src_sumo,
                        'dst_sumo': dst_sumo,
                        'src_actual_pos': src_actual_pos,
                        'dst_actual_pos': dst_actual_pos,
                        'theoretical_raw_distance': theoretical_raw_distance,
                        'theoretical_calibrated_distance': theoretical_calibrated_distance,
                        'actual_raw_distance': actual_raw_distance,
                        'actual_calibrated_distance': actual_calibrated_distance,
                        'expected_distance': expected_distance,
                        'theoretical_error': theoretical_error,
                        'theoretical_error_percentage': theoretical_error_percentage,
                        'actual_error': actual_error,
                        'actual_error_percentage': actual_error_percentage
                    })
                    
                except Exception as e:
                    print(f"            ❌ Vehicle movement failed: {e}")
                    # Fallback to theoretical calculation
                    theoretical_raw_distance = math.sqrt((dst_sumo[0] - src_sumo[0])**2 + (dst_sumo[1] - src_sumo[1])**2)
                    theoretical_calibrated_distance = theoretical_raw_distance * calibration_factor
                    expected_distance = row['distance']
                    theoretical_error = abs(theoretical_calibrated_distance - expected_distance)
                    theoretical_error_percentage = (theoretical_error / expected_distance) * 100 if expected_distance > 0 else 0
                    
                    simulation_data.append({
                        'timestamp': timestamp,
                        'step': i,
                        'src_gps': (row['Latitude_source'], row['Longitude_source']),
                        'dst_gps': (row['Latitude_destination'], row['Longitude_destination']),
                        'src_sumo': src_sumo,
                        'dst_sumo': dst_sumo,
                        'src_actual_pos': None,
                        'dst_actual_pos': None,
                        'theoretical_raw_distance': theoretical_raw_distance,
                        'theoretical_calibrated_distance': theoretical_calibrated_distance,
                        'actual_raw_distance': None,
                        'actual_calibrated_distance': None,
                        'expected_distance': expected_distance,
                        'theoretical_error': theoretical_error,
                        'theoretical_error_percentage': theoretical_error_percentage,
                        'actual_error': None,
                        'actual_error_percentage': None
                    })
                
                print()
            
            # Step simulation
            traci.simulation.step()
            
            # Limit to first 10 steps for testing
            if i >= 9:
                break
        
        # Analyze results with detailed accuracy metrics
        print("\n📊 DETAILED ACCURACY ANALYSIS:")
        print("=" * 40)
        
        if simulation_data:
            # Separate theoretical and actual data
            theoretical_errors = [d['theoretical_error_percentage'] for d in simulation_data if d['theoretical_error_percentage'] is not None]
            actual_errors = [d['actual_error_percentage'] for d in simulation_data if d['actual_error_percentage'] is not None]
            
            theoretical_distances = [d['theoretical_calibrated_distance'] for d in simulation_data if d['theoretical_calibrated_distance'] is not None]
            actual_distances = [d['actual_calibrated_distance'] for d in simulation_data if d['actual_calibrated_distance'] is not None]
            
            # Calculate movement validation
            successful_movements = len([d for d in simulation_data if d['actual_error_percentage'] is not None])
            movement_success_rate = (successful_movements / len(simulation_data)) * 100
            
            print(f"📈 OVERALL STATISTICS:")
            print(f"   Total datapoints processed: {len(simulation_data)}")
            print(f"   Successful vehicle movements: {successful_movements}/{len(simulation_data)} ({movement_success_rate:.1f}%)")
            print(f"   Calibration factor: {calibration_factor}")
            
            print(f"\n🎯 THEORETICAL ACCURACY (GPS→SUMO conversion):")
            if theoretical_errors:
                print(f"   Mean error: {sum(theoretical_errors)/len(theoretical_errors):.2f}%")
                print(f"   Median error: {sorted(theoretical_errors)[len(theoretical_errors)//2]:.2f}%")
                print(f"   Min error: {min(theoretical_errors):.2f}%")
                print(f"   Max error: {max(theoretical_errors):.2f}%")
                print(f"   Std deviation: {(sum([(x-sum(theoretical_errors)/len(theoretical_errors))**2 for x in theoretical_errors])/len(theoretical_errors))**0.5:.2f}%")
            
            print(f"\n🚗 ACTUAL VEHICLE SIMULATION ACCURACY:")
            if actual_errors:
                print(f"   Mean error: {sum(actual_errors)/len(actual_errors):.2f}%")
                print(f"   Median error: {sorted(actual_errors)[len(actual_errors)//2]:.2f}%")
                print(f"   Min error: {min(actual_errors):.2f}%")
                print(f"   Max error: {max(actual_errors):.2f}%")
                print(f"   Std deviation: {(sum([(x-sum(actual_errors)/len(actual_errors))**2 for x in actual_errors])/len(actual_errors))**0.5:.2f}%")
                
                # Accuracy categories
                excellent = len([e for e in actual_errors if e <= 5.0])
                good = len([e for e in actual_errors if 5.0 < e <= 15.0])
                acceptable = len([e for e in actual_errors if 15.0 < e <= 30.0])
                poor = len([e for e in actual_errors if e > 30.0])
                
                print(f"\n   ACCURACY DISTRIBUTION:")
                print(f"   Excellent (≤5%): {excellent}/{len(actual_errors)} ({excellent/len(actual_errors)*100:.1f}%)")
                print(f"   Good (5-15%): {good}/{len(actual_errors)} ({good/len(actual_errors)*100:.1f}%)")
                print(f"   Acceptable (15-30%): {acceptable}/{len(actual_errors)} ({acceptable/len(actual_errors)*100:.1f}%)")
                print(f"   Poor (>30%): {poor}/{len(actual_errors)} ({poor/len(actual_errors)*100:.1f}%)")
            else:
                print("   No successful vehicle movements recorded")
            
            print(f"\n📏 DISTANCE RANGES:")
            if theoretical_distances:
                print(f"   Theoretical: {min(theoretical_distances):.1f}m - {max(theoretical_distances):.1f}m")
            if actual_distances:
                print(f"   Actual: {min(actual_distances):.1f}m - {max(actual_distances):.1f}m")
            
            # Vehicle movement validation
            print(f"\n🚀 VEHICLE MOVEMENT VALIDATION:")
            if successful_movements > 0:
                # Check if vehicles are actually moving between points
                position_changes = 0
                for i in range(1, len(simulation_data)):
                    prev_data = simulation_data[i-1]
                    curr_data = simulation_data[i]
                    
                    if (prev_data['src_actual_pos'] and curr_data['src_actual_pos'] and
                        prev_data['dst_actual_pos'] and curr_data['dst_actual_pos']):
                        
                        src_moved = abs(curr_data['src_actual_pos'][0] - prev_data['src_actual_pos'][0]) > 1.0
                        dst_moved = abs(curr_data['dst_actual_pos'][0] - prev_data['dst_actual_pos'][0]) > 1.0
                        
                        if src_moved or dst_moved:
                            position_changes += 1
                
                movement_rate = (position_changes / max(1, len(simulation_data)-1)) * 100
                print(f"   Position changes detected: {position_changes}/{len(simulation_data)-1} ({movement_rate:.1f}%)")
                
                if movement_rate > 50:
                    print(f"   ✅ VEHICLES ARE ACTUALLY MOVING through GPS datapoints!")
                elif movement_rate > 25:
                    print(f"   ⚠️  Partial vehicle movement detected")
                else:
                    print(f"   ❌ Limited vehicle movement detected")
            else:
                print("   ❌ No vehicle movement data available")
            
            # Save detailed results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_file = f"detailed_accuracy_analysis_{timestamp}.txt"
            
            with open(summary_file, 'w') as f:
                f.write("DETAILED VEHICLE SIMULATION ACCURACY ANALYSIS\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Approach: True vehicle movement with moveToXY\n")
                f.write(f"Calibration factor: {calibration_factor}\n")
                f.write(f"Total datapoints: {len(simulation_data)}\n")
                f.write(f"Successful movements: {successful_movements}/{len(simulation_data)} ({movement_success_rate:.1f}%)\n\n")
                
                if theoretical_errors:
                    f.write(f"THEORETICAL ACCURACY:\n")
                    f.write(f"  Mean error: {sum(theoretical_errors)/len(theoretical_errors):.2f}%\n")
                    f.write(f"  Median error: {sorted(theoretical_errors)[len(theoretical_errors)//2]:.2f}%\n")
                    f.write(f"  Min error: {min(theoretical_errors):.2f}%\n")
                    f.write(f"  Max error: {max(theoretical_errors):.2f}%\n\n")
                
                if actual_errors:
                    f.write(f"ACTUAL VEHICLE SIMULATION ACCURACY:\n")
                    f.write(f"  Mean error: {sum(actual_errors)/len(actual_errors):.2f}%\n")
                    f.write(f"  Median error: {sorted(actual_errors)[len(actual_errors)//2]:.2f}%\n")
                    f.write(f"  Min error: {min(actual_errors):.2f}%\n")
                    f.write(f"  Max error: {max(actual_errors):.2f}%\n\n")
                    
                    excellent = len([e for e in actual_errors if e <= 5.0])
                    good = len([e for e in actual_errors if 5.0 < e <= 15.0])
                    acceptable = len([e for e in actual_errors if 15.0 < e <= 30.0])
                    poor = len([e for e in actual_errors if e > 30.0])
                    
                    f.write(f"ACCURACY DISTRIBUTION:\n")
                    f.write(f"  Excellent (<=5%): {excellent}/{len(actual_errors)} ({excellent/len(actual_errors)*100:.1f}%)\n")
                    f.write(f"  Good (5-15%): {good}/{len(actual_errors)} ({good/len(actual_errors)*100:.1f}%)\n")
                    f.write(f"  Acceptable (15-30%): {acceptable}/{len(actual_errors)} ({acceptable/len(actual_errors)*100:.1f}%)\n")
                    f.write(f"  Poor (>30%): {poor}/{len(actual_errors)} ({poor/len(actual_errors)*100:.1f}%)\n\n")
                
                f.write("DETAILED STEP-BY-STEP RESULTS:\n")
                for data in simulation_data:
                    f.write(f"Step {data['step']}: ")
                    f.write(f"Theoretical: {data['theoretical_error_percentage']:.1f}%")
                    if data['actual_error_percentage'] is not None:
                        f.write(f", Actual: {data['actual_error_percentage']:.1f}%")
                        f.write(f", Expected: {data['expected_distance']:.1f}m")
                        f.write(f", Actual: {data['actual_calibrated_distance']:.1f}m")
                    else:
                        f.write(f", Actual: Movement failed")
                    f.write("\n")
            
            print(f"\n💾 Detailed analysis saved: {summary_file}")
            
            # Overall assessment
            print(f"\n🏆 OVERALL ASSESSMENT:")
            if actual_errors and len(actual_errors) > 0:
                mean_actual_error = sum(actual_errors)/len(actual_errors)
                if mean_actual_error <= 10.0:
                    print(f"   ✅ EXCELLENT: Mean error {mean_actual_error:.1f}% - Digital twin is highly accurate!")
                elif mean_actual_error <= 20.0:
                    print(f"   ✅ GOOD: Mean error {mean_actual_error:.1f}% - Digital twin is accurate")
                elif mean_actual_error <= 50.0:
                    print(f"   ⚠️  ACCEPTABLE: Mean error {mean_actual_error:.1f}% - Digital twin needs improvement")
                else:
                    print(f"   ❌ POOR: Mean error {mean_actual_error:.1f}% - Digital twin needs significant improvement")
            else:
                print(f"   ❌ FAILED: No successful vehicle movements")
                
        else:
            print("❌ No valid simulation data")
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            traci.close()
            print("\n✅ SUMO stopped")
        except:
            pass

if __name__ == "__main__":
    run_simplified_digital_twin()
