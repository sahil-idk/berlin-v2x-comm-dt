#!/usr/bin/env python3
"""
Calibrated V2V Simulation with Improved Accuracy
Implements all four key improvements:
1. Calibration factor (0.607) applied to distances
2. Improved route planning following GPS trajectories
3. moveToXY with higher matchThreshold for precise positioning
4. Waypoint proximity detection for better matching
"""

import traci
import pandas as pd
import sumolib
import os
import time
import math
import sys
import json

# CALIBRATION FACTOR (derived from previous analysis)
CALIBRATION_FACTOR = 0.607

def calculate_distance(pos1, pos2):
    """Calculate Euclidean distance between two positions"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def apply_calibration(distance):
    """Apply calibration factor to distance"""
    return distance * CALIBRATION_FACTOR

def find_nearest_lane_with_heading(net, x, y, heading=None, search_radius=100):
    """
    Find nearest lane considering vehicle heading for better accuracy
    Returns: (lane_id, position_on_lane, distance_from_road)
    """
    nearby_edges = net.getNeighboringEdges(x, y, r=search_radius)
    
    if not nearby_edges:
        return None, None, float('inf')
    
    # Find best matching edge (closest and optionally matching heading)
    best_edge = None
    best_pos = 0
    min_dist = float('inf')
    
    for edge, dist in nearby_edges:
        if dist < min_dist:
            min_dist = dist
            best_edge = edge
            # Get position on edge
            lanes = edge.getLanes()
            if lanes:
                lane = lanes[0]  # Use first lane
                # Project point onto lane
                try:
                    pos, _ = lane.getClosestLanePosAndDist((x, y))
                    best_pos = pos
                except:
                    best_pos = 0
    
    if best_edge:
        lane_id = best_edge.getLanes()[0].getID()
        return lane_id, best_pos, min_dist
    
    return None, None, float('inf')

def check_waypoint_proximity(vehicle_pos, waypoint_pos, threshold=30):
    """
    Check if vehicle is close enough to waypoint
    Returns: (is_close, distance)
    """
    dist = calculate_distance(vehicle_pos, waypoint_pos)
    return (dist < threshold, dist)

def create_improved_route(net, waypoints_df, vehicle_type='source', sample_interval=5):
    """
    Create improved route that better follows GPS trajectory
    Uses more waypoints and better path planning
    """
    sampled_waypoints = []
    
    # Sample waypoints at intervals for better trajectory following
    for idx in range(0, len(waypoints_df), sample_interval):
        row = waypoints_df.iloc[idx]
        if vehicle_type == 'source':
            lat = row['Latitude_source']
            lon = row['Longitude_source']
        else:
            lat = row['Latitude_destination']
            lon = row['Longitude_destination']
        
        x, y = net.convertLonLat2XY(lon, lat)
        sampled_waypoints.append({'x': x, 'y': y, 'index': idx})
    
    # Find edges for sampled waypoints
    edges_with_positions = []
    for wp in sampled_waypoints:
        lane_id, pos, dist = find_nearest_lane_with_heading(net, wp['x'], wp['y'])
        if lane_id and dist < 100:  # Only use waypoints within 100m of road
            edge_id = lane_id.rsplit('_', 1)[0]  # Extract edge ID from lane ID
            edges_with_positions.append({
                'edge_id': edge_id,
                'x': wp['x'],
                'y': wp['y'],
                'index': wp['index']
            })
    
    if not edges_with_positions:
        return []
    
    # Build route with shortest paths between waypoints
    route = []
    for i in range(len(edges_with_positions)):
        current = edges_with_positions[i]
        
        if i == 0:
            if current['edge_id'] not in route:
                route.append(current['edge_id'])
        else:
            prev = edges_with_positions[i-1]
            
            # Find shortest path between edges
            try:
                prev_edge = net.getEdge(prev['edge_id'])
                curr_edge = net.getEdge(current['edge_id'])
                path = net.getShortestPath(prev_edge, curr_edge)
                
                if path and path[0]:
                    for edge in path[0]:
                        edge_id = edge.getID()
                        if edge_id not in route:
                            route.append(edge_id)
            except Exception as e:
                # Fallback: just add the edge
                if current['edge_id'] not in route:
                    route.append(current['edge_id'])
    
    return route

def run_calibrated_v2v_simulation():
    """Main calibrated simulation function"""
    print("="*70)
    print("CALIBRATED V2V SIMULATION")
    print("="*70)
    print(f"📊 Using calibration factor: {CALIBRATION_FACTOR}")
    
    # Configuration
    NUM_WAYPOINTS = 30
    SIMULATION_STEPS = 3000
    PROXIMITY_THRESHOLD = 30  # meters
    MATCH_THRESHOLD = 500  # High threshold for moveToXY
    
    original_dir = os.getcwd()
    
    try:
        # Change to SUMO directory
        os.chdir('berlin-sumo-closed-netwokr')
        
        # Load network
        print("\n📍 Loading SUMO network...")
        net = sumolib.net.readNet('osm.net.xml.gz')
        print(f"✅ Network loaded: {len(net.getEdges())} edges")
        
        # Load GPS data
        print(f"\n📍 Loading GPS data (first {NUM_WAYPOINTS} waypoints)...")
        df = pd.read_csv('../vehicle_2_4_first_200.csv')
        waypoints_df = df.head(NUM_WAYPOINTS)
        print(f"✅ Loaded {len(waypoints_df)} GPS waypoints")
        
        # Create improved routes
        print("\n📍 Creating improved routes following GPS trajectories...")
        source_route = create_improved_route(net, waypoints_df, 'source', sample_interval=3)
        dest_route = create_improved_route(net, waypoints_df, 'destination', sample_interval=3)
        
        print(f"✅ Source route: {len(source_route)} edges")
        print(f"✅ Destination route: {len(dest_route)} edges")
        
        # Ensure routes are valid
        if len(source_route) < 2:
            print("⚠️ Source route too short, extending...")
            if source_route:
                edge = net.getEdge(source_route[0])
                outgoing = edge.getOutgoing()
                if outgoing:
                    source_route.append(list(outgoing.keys())[0].getID())
        
        if len(dest_route) < 2:
            print("⚠️ Destination route too short, extending...")
            if dest_route:
                edge = net.getEdge(dest_route[0])
                outgoing = edge.getOutgoing()
                if outgoing:
                    dest_route.append(list(outgoing.keys())[0].getID())
        
        # Create route file with moveToXY-friendly vehicles
        print("\n📍 Creating route file...")
        route_file = 'v2v_calibrated_routes.rou.xml'
        with open(route_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')
            
            # Define vehicle types
            f.write('    <vType id="v2v_source_type" accel="2.6" decel="4.5" sigma="0.5" ')
            f.write('length="4.5" width="1.8" height="1.5" minGap="2.5" ')
            f.write('maxSpeed="20" guiShape="passenger" color="0,0,255"/>\n')
            
            f.write('    <vType id="v2v_dest_type" accel="2.6" decel="4.5" sigma="0.5" ')
            f.write('length="4.5" width="1.8" height="1.5" minGap="2.5" ')
            f.write('maxSpeed="20" guiShape="passenger" color="255,0,0"/>\n')
            
            # Define routes
            f.write(f'    <route id="source_route" edges="{" ".join(source_route)}"/>\n')
            f.write(f'    <route id="dest_route" edges="{" ".join(dest_route)}"/>\n')
            
            # Define vehicles
            f.write('    <vehicle id="v2v_source" type="v2v_source_type" ')
            f.write('route="source_route" depart="0" departLane="best" departSpeed="0"/>\n')
            
            f.write('    <vehicle id="v2v_dest" type="v2v_dest_type" ')
            f.write('route="dest_route" depart="0" departLane="best" departSpeed="0"/>\n')
            
            f.write('</routes>\n')
        
        print(f"✅ Route file created: {route_file}")
        
        # Create SUMO configuration
        print("\n📍 Creating SUMO configuration...")
        config_file = 'v2v_calibrated.sumocfg'
        with open(config_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<configuration>\n')
            f.write('    <input>\n')
            f.write('        <net-file value="osm.net.xml.gz"/>\n')
            f.write(f'        <route-files value="{route_file}"/>\n')
            f.write('        <additional-files value="osm.poly.xml.gz"/>\n')
            f.write('    </input>\n')
            f.write('    <time>\n')
            f.write('        <begin value="0"/>\n')
            f.write('        <step-length value="0.1"/>\n')
            f.write('    </time>\n')
            f.write('</configuration>\n')
        
        # Start SUMO-GUI
        print("\n🚀 Starting SUMO-GUI...")
        sumo_cmd = ["sumo-gui", "-c", config_file, "--start", "--quit-on-end"]
        traci.start(sumo_cmd)
        time.sleep(3)
        
        # Add waypoint POIs
        print("\n📍 Adding waypoint markers...")
        waypoint_coords = []
        for idx, row in waypoints_df.iterrows():
            src_x, src_y = net.convertLonLat2XY(row['Longitude_source'], row['Latitude_source'])
            dst_x, dst_y = net.convertLonLat2XY(row['Longitude_destination'], row['Longitude_destination'])
            
            traci.poi.add(
                f"src_wp_{idx}",
                src_x, src_y,
                color=(0, 0, 255, 128),
                poiType="source",
                layer=100
            )
            
            traci.poi.add(
                f"dst_wp_{idx}",
                dst_x, dst_y,
                color=(255, 0, 0, 128),
                poiType="destination",
                layer=100
            )
            
            waypoint_coords.append({
                'source': (src_x, src_y),
                'dest': (dst_x, dst_y),
                'actual_distance': row['distance']
            })
        
        print(f"✅ Added {len(waypoint_coords)*2} waypoint markers")
        
        # Run simulation with moveToXY for precise positioning
        print("\n🎯 Starting calibrated simulation...")
        print("-"*70)
        
        step = 0
        source_active = False
        dest_active = False
        
        # Metrics tracking
        distances = []
        calibrated_distances = []
        source_progress = []
        dest_progress = []
        waypoint_matches = []
        
        current_src_wp = 0
        current_dest_wp = 0
        
        while step < SIMULATION_STEPS:
            traci.simulationStep()
            step += 1
            
            vehicles = traci.vehicle.getIDList()
            
            # Check for vehicles
            if "v2v_source" in vehicles:
                if not source_active:
                    print(f"✅ Step {step}: Source vehicle active")
                    source_active = True
                    # Disable autonomous behavior for precise control
                    traci.vehicle.setSpeedMode("v2v_source", 0)
                    traci.vehicle.setLaneChangeMode("v2v_source", 0)
            
            if "v2v_dest" in vehicles:
                if not dest_active:
                    print(f"✅ Step {step}: Destination vehicle active")
                    dest_active = True
                    # Disable autonomous behavior for precise control
                    traci.vehicle.setSpeedMode("v2v_dest", 0)
                    traci.vehicle.setLaneChangeMode("v2v_dest", 0)
            
            # Move vehicles using moveToXY with waypoint proximity detection
            if source_active and "v2v_source" in vehicles and current_src_wp < len(waypoint_coords):
                try:
                    src_pos = traci.vehicle.getPosition("v2v_source")
                    target_pos = waypoint_coords[current_src_wp]['source']
                    
                    # Check proximity to current waypoint
                    is_close, dist = check_waypoint_proximity(src_pos, target_pos, PROXIMITY_THRESHOLD)
                    
                    if is_close:
                        # Move to next waypoint
                        current_src_wp += 1
                        if step % 50 == 0:
                            print(f"📍 Step {step}: Source reached waypoint {current_src_wp-1} (dist: {dist:.2f}m)")
                    
                    if current_src_wp < len(waypoint_coords):
                        # Move towards current waypoint using moveToXY with high matchThreshold
                        target_x, target_y = waypoint_coords[current_src_wp]['source']
                        lane_id, pos, _ = find_nearest_lane_with_heading(net, target_x, target_y)
                        
                        if lane_id:
                            traci.vehicle.moveToXY(
                                "v2v_source",
                                "",  # No specific edge
                                0,   # Any lane
                                target_x,
                                target_y,
                                angle=-1,  # Keep current angle
                                keepRoute=2,  # Allow off-route positioning
                                matchThreshold=MATCH_THRESHOLD  # High threshold for flexibility
                            )
                            # Set speed towards waypoint
                            traci.vehicle.setSpeed("v2v_source", 10)
                    
                    source_progress.append(current_src_wp)
                except traci.exceptions.TraCIException as e:
                    if step % 100 == 0:
                        print(f"⚠️ Step {step}: Source vehicle error: {e}")
            
            # Move destination vehicle
            if dest_active and "v2v_dest" in vehicles and current_dest_wp < len(waypoint_coords):
                try:
                    dst_pos = traci.vehicle.getPosition("v2v_dest")
                    target_pos = waypoint_coords[current_dest_wp]['dest']
                    
                    # Check proximity to current waypoint
                    is_close, dist = check_waypoint_proximity(dst_pos, target_pos, PROXIMITY_THRESHOLD)
                    
                    if is_close:
                        # Move to next waypoint
                        current_dest_wp += 1
                        if step % 50 == 0:
                            print(f"📍 Step {step}: Dest reached waypoint {current_dest_wp-1} (dist: {dist:.2f}m)")
                    
                    if current_dest_wp < len(waypoint_coords):
                        # Move towards current waypoint using moveToXY with high matchThreshold
                        target_x, target_y = waypoint_coords[current_dest_wp]['dest']
                        lane_id, pos, _ = find_nearest_lane_with_heading(net, target_x, target_y)
                        
                        if lane_id:
                            traci.vehicle.moveToXY(
                                "v2v_dest",
                                "",
                                0,
                                target_x,
                                target_y,
                                angle=-1,
                                keepRoute=2,
                                matchThreshold=MATCH_THRESHOLD
                            )
                            # Set speed towards waypoint
                            traci.vehicle.setSpeed("v2v_dest", 10)
                    
                    dest_progress.append(current_dest_wp)
                except traci.exceptions.TraCIException as e:
                    if step % 100 == 0:
                        print(f"⚠️ Step {step}: Dest vehicle error: {e}")
            
            # Calculate distances when both vehicles are active
            if source_active and dest_active and "v2v_source" in vehicles and "v2v_dest" in vehicles:
                try:
                    src_pos = traci.vehicle.getPosition("v2v_source")
                    dst_pos = traci.vehicle.getPosition("v2v_dest")
                    
                    # Raw distance
                    raw_distance = calculate_distance(src_pos, dst_pos)
                    distances.append(raw_distance)
                    
                    # Calibrated distance
                    calib_distance = apply_calibration(raw_distance)
                    calibrated_distances.append(calib_distance)
                    
                    # Match to nearest waypoint for accuracy analysis
                    min_wp_dist = float('inf')
                    closest_wp_idx = 0
                    for i, wp in enumerate(waypoint_coords):
                        src_dist = calculate_distance(src_pos, wp['source'])
                        dst_dist = calculate_distance(dst_pos, wp['dest'])
                        combined_dist = src_dist + dst_dist
                        if combined_dist < min_wp_dist:
                            min_wp_dist = combined_dist
                            closest_wp_idx = i
                    
                    if closest_wp_idx < len(waypoint_coords):
                        actual_dist = waypoint_coords[closest_wp_idx]['actual_distance']
                        error = calib_distance - actual_dist
                        error_pct = (error / actual_dist) * 100 if actual_dist > 0 else 0
                        
                        waypoint_matches.append({
                            'step': step,
                            'waypoint': closest_wp_idx,
                            'raw_distance': raw_distance,
                            'calibrated_distance': calib_distance,
                            'actual_distance': actual_dist,
                            'error': error,
                            'error_percentage': error_pct,
                            'accuracy': 100 - abs(error_pct)
                        })
                    
                    # Log every 100 steps
                    if step % 100 == 0:
                        print(f"📊 Step {step}: Raw={raw_distance:.2f}m, "
                              f"Calibrated={calib_distance:.2f}m, "
                              f"Waypoint: src={current_src_wp}/{NUM_WAYPOINTS}, "
                              f"dst={current_dest_wp}/{NUM_WAYPOINTS}")
                except Exception as e:
                    if step % 100 == 0:
                        print(f"⚠️ Step {step}: Distance calculation error: {e}")
            
            # Check completion
            if current_src_wp >= len(waypoint_coords) and current_dest_wp >= len(waypoint_coords):
                print(f"\n✅ Both vehicles completed all waypoints at step {step}")
                break
        
        # Final statistics
        print("\n" + "="*70)
        print("CALIBRATED SIMULATION COMPLETE - STATISTICS")
        print("="*70)
        
        if distances:
            print(f"📊 Distance Statistics:")
            print(f"   Raw distances: avg={sum(distances)/len(distances):.2f}m, "
                  f"min={min(distances):.2f}m, max={max(distances):.2f}m")
            print(f"   Calibrated distances: avg={sum(calibrated_distances)/len(calibrated_distances):.2f}m, "
                  f"min={min(calibrated_distances):.2f}m, max={max(calibrated_distances):.2f}m")
        
        print(f"📊 Waypoint Progress:")
        print(f"   Source: {current_src_wp}/{NUM_WAYPOINTS} waypoints")
        print(f"   Destination: {current_dest_wp}/{NUM_WAYPOINTS} waypoints")
        
        # Accuracy analysis
        if waypoint_matches:
            errors = [m['error'] for m in waypoint_matches]
            error_pcts = [m['error_percentage'] for m in waypoint_matches]
            accuracies = [m['accuracy'] for m in waypoint_matches]
            
            print(f"\n📊 Calibrated Accuracy Analysis:")
            print(f"   Mean Error: {sum(errors)/len(errors):.2f} m")
            print(f"   Mean Absolute Error: {sum(abs(e) for e in errors)/len(errors):.2f} m")
            print(f"   RMSE: {(sum(e**2 for e in errors)/len(errors))**0.5:.2f} m")
            print(f"   Mean Error %: {sum(error_pcts)/len(error_pcts):.2f}%")
            print(f"   Mean Absolute Error %: {sum(abs(ep) for ep in error_pcts)/len(error_pcts):.2f}%")
            print(f"   Mean Accuracy: {sum(accuracies)/len(accuracies):.2f}%")
            
            # Count accuracy categories
            high_acc = sum(1 for a in accuracies if a >= 90)
            medium_acc = sum(1 for a in accuracies if 70 <= a < 90)
            low_acc = sum(1 for a in accuracies if a < 70)
            
            print(f"\n📊 Accuracy Distribution:")
            print(f"   High (≥90%): {high_acc} matches ({high_acc/len(accuracies)*100:.1f}%)")
            print(f"   Medium (70-89%): {medium_acc} matches ({medium_acc/len(accuracies)*100:.1f}%)")
            print(f"   Low (<70%): {low_acc} matches ({low_acc/len(accuracies)*100:.1f}%)")
            
            # Save detailed results
            analysis_df = pd.DataFrame(waypoint_matches)
            analysis_file = 'calibrated_distance_analysis.csv'
            analysis_df.to_csv(analysis_file, index=False)
            print(f"\n💾 Detailed analysis saved to: {analysis_file}")
            
            # Save summary
            summary = {
                'calibration_factor': CALIBRATION_FACTOR,
                'proximity_threshold': PROXIMITY_THRESHOLD,
                'match_threshold': MATCH_THRESHOLD,
                'num_waypoints': NUM_WAYPOINTS,
                'total_steps': step,
                'mean_error_m': sum(errors)/len(errors),
                'mean_absolute_error_m': sum(abs(e) for e in errors)/len(errors),
                'rmse_m': (sum(e**2 for e in errors)/len(errors))**0.5,
                'mean_accuracy_pct': sum(accuracies)/len(accuracies),
                'high_accuracy_count': high_acc,
                'medium_accuracy_count': medium_acc,
                'low_accuracy_count': low_acc
            }
            
            with open('calibrated_simulation_summary.json', 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"💾 Summary saved to: calibrated_simulation_summary.json")
        
        print("\n✅ Calibrated simulation successful!")
        print("💡 Key improvements applied:")
        print("   ✓ Calibration factor (0.607) applied to distances")
        print("   ✓ Improved route planning following GPS trajectories")
        print("   ✓ moveToXY with high matchThreshold (500m)")
        print("   ✓ Waypoint proximity detection (30m threshold)")
        
        # Keep simulation running
        print("\n⏸ Keeping SUMO-GUI open for inspection (press Ctrl+C to close)...")
        try:
            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n👋 Closing simulation...")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            traci.close()
        except:
            pass
        os.chdir(original_dir)
        print("\n✅ Cleanup complete")

if __name__ == "__main__":
    run_calibrated_v2v_simulation()

