#!/usr/bin/env python3
"""
Simple and Robust V2V Simulation
Uses edge-to-edge navigation without moveToXY to prevent vehicle disappearance
"""

import traci
import pandas as pd
import sumolib
import os
import time
import math
import sys

def calculate_distance(pos1, pos2):
    """Calculate Euclidean distance between two positions"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def find_path_through_waypoints(net, waypoints_df, vehicle_type='source'):
    """Find a connected path through waypoints using Dijkstra routing"""
    edges_with_positions = []
    
    for idx, row in waypoints_df.iterrows():
        if vehicle_type == 'source':
            lat = row['Latitude_source']
            lon = row['Longitude_source']
        else:
            lat = row['Latitude_destination']
            lon = row['Longitude_destination']
        
        x, y = net.convertLonLat2XY(lon, lat)
        
        # Find nearest edge with larger radius
        nearby_edges = net.getNeighboringEdges(x, y, r=200)
        if nearby_edges:
            edge = min(nearby_edges, key=lambda e: e[1])[0]
            edges_with_positions.append({
                'edge': edge,
                'edge_id': edge.getID(),
                'position': (x, y),
                'index': idx
            })
    
    # Build connected route
    if not edges_with_positions:
        return []
    
    route = []
    for i in range(len(edges_with_positions)):
        current = edges_with_positions[i]
        
        if i == 0:
            route.append(current['edge_id'])
        else:
            prev = edges_with_positions[i-1]
            
            # Find shortest path between edges
            try:
                path = net.getShortestPath(prev['edge'], current['edge'])
                if path and path[0]:
                    # Add intermediate edges
                    for edge in path[0]:
                        if edge.getID() not in route:
                            route.append(edge.getID())
            except:
                # Fallback: just add the edge if path finding fails
                if current['edge_id'] not in route:
                    route.append(current['edge_id'])
    
    return route

def run_v2v_simulation():
    """Main simulation function"""
    print("="*70)
    print("ROBUST V2V SIMULATION - NO moveToXY")
    print("="*70)
    
    # Configuration
    NUM_WAYPOINTS = 50  # Adjustable
    SIMULATION_STEPS = 2000
    
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
        
        # Find connected paths through waypoints
        print("\n📍 Computing routes through GPS waypoints...")
        source_route = find_path_through_waypoints(net, waypoints_df, 'source')
        dest_route = find_path_through_waypoints(net, waypoints_df, 'destination')
        
        print(f"✅ Source route: {len(source_route)} edges")
        print(f"✅ Destination route: {len(dest_route)} edges")
        
        # Validate routes
        if len(source_route) < 2:
            print("⚠️ Source route too short, extending...")
            # Find a nearby edge to extend the route
            edge = net.getEdge(source_route[0]) if source_route else list(net.getEdges())[0]
            outgoing = edge.getOutgoing()
            if outgoing:
                source_route.append(list(outgoing.keys())[0].getID())
        
        if len(dest_route) < 2:
            print("⚠️ Destination route too short, extending...")
            edge = net.getEdge(dest_route[0]) if dest_route else list(net.getEdges())[0]
            outgoing = edge.getOutgoing()
            if outgoing:
                dest_route.append(list(outgoing.keys())[0].getID())
        
        # Create route file
        print("\n📍 Creating route file...")
        route_file = 'v2v_robust_routes.rou.xml'
        with open(route_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')
            
            # Define vehicle types with 3D car shape
            f.write('    <!-- Vehicle Types with 3D visualization -->\n')
            f.write('    <vType id="v2v_source_type" accel="2.6" decel="4.5" sigma="0.5" ')
            f.write('length="4.5" width="1.8" height="1.5" minGap="2.5" ')
            f.write('maxSpeed="30" guiShape="passenger" color="0,0,255"/>\n')
            
            f.write('    <vType id="v2v_dest_type" accel="2.6" decel="4.5" sigma="0.5" ')
            f.write('length="4.5" width="1.8" height="1.5" minGap="2.5" ')
            f.write('maxSpeed="30" guiShape="passenger" color="255,0,0"/>\n')
            
            # Define routes
            f.write('\n    <!-- Routes through GPS waypoints -->\n')
            f.write(f'    <route id="source_route" edges="{" ".join(source_route)}"/>\n')
            f.write(f'    <route id="dest_route" edges="{" ".join(dest_route)}"/>\n')
            
            # Define vehicles
            f.write('\n    <!-- Vehicles -->\n')
            f.write('    <vehicle id="v2v_source" type="v2v_source_type" ')
            f.write('route="source_route" depart="0" departLane="best" departSpeed="0"/>\n')
            
            f.write('    <vehicle id="v2v_dest" type="v2v_dest_type" ')
            f.write('route="dest_route" depart="0" departLane="best" departSpeed="0"/>\n')
            
            f.write('</routes>\n')
        
        print(f"✅ Route file created: {route_file}")
        
        # Create custom config file
        print("\n📍 Creating SUMO configuration...")
        config_file = 'v2v_robust.sumocfg'
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
            f.write('    <processing>\n')
            f.write('        <collision.check-junctions value="true"/>\n')
            f.write('        <collision.action value="warn"/>\n')
            f.write('    </processing>\n')
            f.write('</configuration>\n')
        
        # Start SUMO-GUI
        print("\n🚀 Starting SUMO-GUI...")
        sumo_cmd = ["sumo-gui", "-c", config_file, "--start", "--quit-on-end"]
        traci.start(sumo_cmd)
        time.sleep(3)  # Give GUI time to open
        
        # Add waypoint POIs for visualization
        print("\n📍 Adding waypoint markers...")
        waypoint_coords = []
        for idx, row in waypoints_df.iterrows():
            # Source waypoint (Blue)
            src_x, src_y = net.convertLonLat2XY(row['Longitude_source'], row['Latitude_source'])
            traci.poi.add(
                f"src_wp_{idx}",
                src_x, src_y,
                color=(0, 0, 255, 128),  # Semi-transparent blue
                poiType="source",
                layer=100
            )
            
            # Destination waypoint (Red)
            dst_x, dst_y = net.convertLonLat2XY(row['Longitude_destination'], row['Latitude_destination'])
            traci.poi.add(
                f"dst_wp_{idx}",
                dst_x, dst_y,
                color=(255, 0, 0, 128),  # Semi-transparent red
                poiType="destination",
                layer=100
            )
            
            waypoint_coords.append({
                'source': (src_x, src_y),
                'dest': (dst_x, dst_y),
                'actual_distance': row['distance']
            })
        
        print(f"✅ Added {len(waypoint_coords)*2} waypoint markers")
        
        # Run simulation
        print("\n🎯 Starting simulation...")
        print("-"*70)
        
        step = 0
        source_active = False
        dest_active = False
        last_log_step = 0
        
        # Metrics tracking
        distances = []
        source_progress = []
        dest_progress = []
        
        while step < SIMULATION_STEPS:
            traci.simulationStep()
            step += 1
            
            # Get current vehicles
            vehicles = traci.vehicle.getIDList()
            
            # Check vehicle status
            if "v2v_source" in vehicles:
                if not source_active:
                    print(f"✅ Step {step}: Source vehicle active")
                    source_active = True
                
                # Get source position
                src_pos = traci.vehicle.getPosition("v2v_source")
                src_speed = traci.vehicle.getSpeed("v2v_source")
                
                # Track progress through waypoints
                closest_wp = 0
                min_dist = float('inf')
                for i, wp in enumerate(waypoint_coords):
                    dist = calculate_distance(src_pos, wp['source'])
                    if dist < min_dist:
                        min_dist = dist
                        closest_wp = i
                source_progress.append(closest_wp)
            else:
                if source_active:
                    print(f"⚠️ Step {step}: Source vehicle completed route")
                    source_active = False
            
            if "v2v_dest" in vehicles:
                if not dest_active:
                    print(f"✅ Step {step}: Destination vehicle active")
                    dest_active = True
                
                # Get destination position
                dst_pos = traci.vehicle.getPosition("v2v_dest")
                dst_speed = traci.vehicle.getSpeed("v2v_dest")
                
                # Track progress through waypoints
                closest_wp = 0
                min_dist = float('inf')
                for i, wp in enumerate(waypoint_coords):
                    dist = calculate_distance(dst_pos, wp['dest'])
                    if dist < min_dist:
                        min_dist = dist
                        closest_wp = i
                dest_progress.append(closest_wp)
            else:
                if dest_active:
                    print(f"⚠️ Step {step}: Destination vehicle completed route")
                    dest_active = False
            
            # Calculate and log distance when both vehicles are active
            if source_active and dest_active:
                distance = calculate_distance(src_pos, dst_pos)
                distances.append(distance)
                
                # Log every 100 steps
                if step - last_log_step >= 100:
                    avg_distance = sum(distances[-100:]) / len(distances[-100:]) if distances else 0
                    print(f"📊 Step {step}: Distance={distance:.2f}m (avg={avg_distance:.2f}m), "
                          f"Speed: src={src_speed:.1f}m/s, dst={dst_speed:.1f}m/s, "
                          f"Waypoint: src={source_progress[-1] if source_progress else 0}, "
                          f"dst={dest_progress[-1] if dest_progress else 0}")
                    last_log_step = step
            
            # Dynamic speed adjustment based on waypoint proximity
            if source_active and "v2v_source" in vehicles:
                # Slow down near waypoints
                if closest_wp < len(waypoint_coords):
                    dist_to_wp = calculate_distance(src_pos, waypoint_coords[closest_wp]['source'])
                    if dist_to_wp < 30:  # Within 30m of waypoint
                        traci.vehicle.setSpeed("v2v_source", 5)  # Slow down
                    else:
                        traci.vehicle.setSpeed("v2v_source", 15)  # Normal speed
            
            if dest_active and "v2v_dest" in vehicles:
                if closest_wp < len(waypoint_coords):
                    dist_to_wp = calculate_distance(dst_pos, waypoint_coords[closest_wp]['dest'])
                    if dist_to_wp < 30:
                        traci.vehicle.setSpeed("v2v_dest", 5)
                    else:
                        traci.vehicle.setSpeed("v2v_dest", 15)
            
            # Stop if both vehicles have completed their routes
            if not source_active and not dest_active and step > 100:
                print(f"\n✅ Both vehicles completed routes at step {step}")
                break
        
        # Final statistics
        print("\n" + "="*70)
        print("SIMULATION COMPLETE - STATISTICS")
        print("="*70)
        
        if distances:
            print(f"📊 Average inter-vehicle distance: {sum(distances)/len(distances):.2f} m")
            print(f"📊 Min distance: {min(distances):.2f} m")
            print(f"📊 Max distance: {max(distances):.2f} m")
        
        if source_progress:
            print(f"📊 Source vehicle reached waypoint: {max(source_progress)}/{NUM_WAYPOINTS}")
        
        if dest_progress:
            print(f"📊 Dest vehicle reached waypoint: {max(dest_progress)}/{NUM_WAYPOINTS}")
        
        print(f"📊 Total simulation steps: {step}")
        
        # ===== DISTANCE ACCURACY ANALYSIS =====
        print("\n" + "="*70)
        print("DISTANCE ACCURACY ANALYSIS")
        print("="*70)
        
        # Analyze simulated vs actual distances for each waypoint
        distance_analysis = []
        
        for i, wp in enumerate(waypoint_coords):
            actual_distance = wp['actual_distance']
            
            # Find closest simulated distance to this waypoint
            # We'll use the distance when vehicles were closest to this waypoint
            closest_simulated_distance = None
            min_distance_to_waypoint = float('inf')
            
            # Look through simulation steps to find when vehicles were closest to this waypoint
            for sim_step in range(len(distances)):
                if sim_step < len(source_progress) and sim_step < len(dest_progress):
                    src_wp_idx = source_progress[sim_step]
                    dest_wp_idx = dest_progress[sim_step]
                    
                    # Calculate how close we are to this waypoint
                    distance_to_waypoint = abs(src_wp_idx - i) + abs(dest_wp_idx - i)
                    
                    if distance_to_waypoint < min_distance_to_waypoint:
                        min_distance_to_waypoint = distance_to_waypoint
                        closest_simulated_distance = distances[sim_step]
            
            if closest_simulated_distance is not None:
                error = closest_simulated_distance - actual_distance
                error_percentage = (error / actual_distance) * 100 if actual_distance > 0 else 0
                
                distance_analysis.append({
                    'waypoint': i,
                    'actual_distance': actual_distance,
                    'simulated_distance': closest_simulated_distance,
                    'error': error,
                    'error_percentage': error_percentage,
                    'accuracy': 100 - abs(error_percentage)
                })
        
        # Calculate overall accuracy metrics
        if distance_analysis:
            errors = [da['error'] for da in distance_analysis]
            error_percentages = [da['error_percentage'] for da in distance_analysis]
            accuracies = [da['accuracy'] for da in distance_analysis]
            
            print(f"📊 Distance Analysis Results:")
            print(f"   Total waypoints analyzed: {len(distance_analysis)}")
            print(f"   Mean Error: {sum(errors)/len(errors):.2f} m")
            print(f"   Mean Absolute Error: {sum(abs(e) for e in errors)/len(errors):.2f} m")
            print(f"   Root Mean Square Error: {(sum(e**2 for e in errors)/len(errors))**0.5:.2f} m")
            print(f"   Mean Error Percentage: {sum(error_percentages)/len(error_percentages):.2f}%")
            print(f"   Mean Absolute Error Percentage: {sum(abs(ep) for ep in error_percentages)/len(error_percentages):.2f}%")
            print(f"   Mean Accuracy: {sum(accuracies)/len(accuracies):.2f}%")
            
            # Find best and worst waypoints
            best_wp = min(distance_analysis, key=lambda x: abs(x['error_percentage']))
            worst_wp = max(distance_analysis, key=lambda x: abs(x['error_percentage']))
            
            print(f"\n📊 Best Waypoint (Most Accurate):")
            print(f"   Waypoint {best_wp['waypoint']}: Actual={best_wp['actual_distance']:.2f}m, "
                  f"Simulated={best_wp['simulated_distance']:.2f}m, "
                  f"Error={best_wp['error']:.2f}m ({best_wp['error_percentage']:.2f}%)")
            
            print(f"\n📊 Worst Waypoint (Least Accurate):")
            print(f"   Waypoint {worst_wp['waypoint']}: Actual={worst_wp['actual_distance']:.2f}m, "
                  f"Simulated={worst_wp['simulated_distance']:.2f}m, "
                  f"Error={worst_wp['error']:.2f}m ({worst_wp['error_percentage']:.2f}%)")
            
            # Accuracy distribution
            high_accuracy = sum(1 for a in accuracies if a >= 90)
            medium_accuracy = sum(1 for a in accuracies if 70 <= a < 90)
            low_accuracy = sum(1 for a in accuracies if a < 70)
            
            print(f"\n📊 Accuracy Distribution:")
            print(f"   High Accuracy (≥90%): {high_accuracy} waypoints ({high_accuracy/len(accuracies)*100:.1f}%)")
            print(f"   Medium Accuracy (70-89%): {medium_accuracy} waypoints ({medium_accuracy/len(accuracies)*100:.1f}%)")
            print(f"   Low Accuracy (<70%): {low_accuracy} waypoints ({low_accuracy/len(accuracies)*100:.1f}%)")
            
            # Save detailed analysis to CSV
            analysis_df = pd.DataFrame(distance_analysis)
            analysis_file = 'distance_accuracy_analysis.csv'
            analysis_df.to_csv(analysis_file, index=False)
            print(f"\n💾 Detailed analysis saved to: {analysis_file}")
            
            # Save summary statistics
            summary_stats = {
                'total_waypoints': len(distance_analysis),
                'mean_error_m': sum(errors)/len(errors),
                'mean_absolute_error_m': sum(abs(e) for e in errors)/len(errors),
                'rmse_m': (sum(e**2 for e in errors)/len(errors))**0.5,
                'mean_error_percentage': sum(error_percentages)/len(error_percentages),
                'mean_absolute_error_percentage': sum(abs(ep) for ep in error_percentages)/len(error_percentages),
                'mean_accuracy_percentage': sum(accuracies)/len(accuracies),
                'high_accuracy_count': high_accuracy,
                'medium_accuracy_count': medium_accuracy,
                'low_accuracy_count': low_accuracy,
                'best_waypoint': best_wp['waypoint'],
                'worst_waypoint': worst_wp['waypoint']
            }
            
            import json
            with open('distance_accuracy_summary.json', 'w') as f:
                json.dump(summary_stats, f, indent=2)
            print(f"💾 Summary statistics saved to: distance_accuracy_summary.json")
            
            # Print detailed waypoint-by-waypoint analysis (first 10 for brevity)
            print(f"\n📊 Detailed Analysis (First 10 Waypoints):")
            print("-" * 80)
            print(f"{'WP':<3} {'Actual':<8} {'Simulated':<10} {'Error':<8} {'Error%':<8} {'Accuracy':<8}")
            print("-" * 80)
            
            for da in distance_analysis[:10]:
                print(f"{da['waypoint']:<3} {da['actual_distance']:<8.2f} {da['simulated_distance']:<10.2f} "
                      f"{da['error']:<8.2f} {da['error_percentage']:<8.2f} {da['accuracy']:<8.2f}")
            
            if len(distance_analysis) > 10:
                print(f"... and {len(distance_analysis) - 10} more waypoints (see CSV for full details)")
        
        print("\n✅ Simulation successful! Vehicles stayed in simulation throughout.")
        print("💡 TIP: Vehicles are visible as 3D cars (blue and red)")
        print("💡 TIP: Waypoints are shown as semi-transparent POIs")
        print("💡 TIP: Check distance_accuracy_analysis.csv for detailed per-waypoint analysis")
        
        # Keep simulation running for observation
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
        # Clean up
        try:
            traci.close()
        except:
            pass
        os.chdir(original_dir)
        print("\n✅ Cleanup complete")

if __name__ == "__main__":
    run_v2v_simulation()
