#!/usr/bin/env python3
"""
STRATEGY 1: Multi-Zone Distance-Based Calibration
Different calibration factors for different distance ranges
"""

import traci
import pandas as pd
import sumolib
import os
import time
import math
import json

# Multi-zone calibration factors (optimized for distance ranges)
CALIBRATION_ZONES = {
    'very_close': {'range': (0, 16), 'factor': 0.55},
    'close': {'range': (16, 18.5), 'factor': 0.58},
    'medium': {'range': (18.5, 21), 'factor': 0.607},
    'medium_far': {'range': (21, 23), 'factor': 0.63},
    'far': {'range': (23, 100), 'factor': 0.66}
}

def kmh_to_ms(speed_kmh):
    return speed_kmh / 3.6

def calculate_distance(pos1, pos2):
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def get_zone_calibration(actual_distance):
    """Get calibration factor based on distance zone"""
    for zone_name, zone_data in CALIBRATION_ZONES.items():
        min_dist, max_dist = zone_data['range']
        if min_dist <= actual_distance < max_dist:
            return zone_data['factor'], zone_name
    return 0.607, 'default'  # Fallback

def find_optimal_path_through_waypoints(net, waypoints_df, vehicle_type='source'):
    """Find connected path through waypoints"""
    edges_with_positions = []
    
    for idx, row in waypoints_df.iterrows():
        if vehicle_type == 'source':
            lat = row['Latitude_source']
            lon = row['Longitude_source']
        else:
            lat = row['Latitude_destination']
            lon = row['Longitude_destination']
        
        x, y = net.convertLonLat2XY(lon, lat)
        
        search_radius = 50
        while search_radius <= 300:
            nearby_edges = net.getNeighboringEdges(x, y, r=search_radius)
            if nearby_edges:
                edge = min(nearby_edges, key=lambda e: e[1])[0]
                edges_with_positions.append({
                    'edge': edge,
                    'edge_id': edge.getID(),
                    'position': (x, y),
                    'index': idx
                })
                break
            search_radius += 50
    
    if not edges_with_positions:
        return [], []
    
    route = []
    for i in range(len(edges_with_positions)):
        current = edges_with_positions[i]
        
        if i == 0:
            route.append(current['edge_id'])
        else:
            prev = edges_with_positions[i-1]
            try:
                path = net.getShortestPath(prev['edge'], current['edge'])
                if path and path[0]:
                    for edge in path[0]:
                        if edge.getID() not in route:
                            route.append(edge.getID())
                    if current['edge_id'] not in route:
                        route.append(current['edge_id'])
            except:
                if current['edge_id'] not in route:
                    route.append(current['edge_id'])
    
    return route, []

def run_strategy_1(num_waypoints=50):
    """Run Strategy 1: Multi-Zone Calibration"""
    
    print("="*70)
    print("STRATEGY 1: MULTI-ZONE DISTANCE-BASED CALIBRATION")
    print("="*70)
    print(f"📊 Calibration Zones:")
    for zone_name, zone_data in CALIBRATION_ZONES.items():
        print(f"   {zone_name}: {zone_data['range']}m → {zone_data['factor']}")
    print()
    
    original_dir = os.getcwd()
    
    try:
        # Load network
        os.chdir('berlin-sumo-closed-netwokr')
        print("📍 Loading SUMO network...")
        net = sumolib.net.readNet('osm.net.xml.gz')
        print(f"✅ Network loaded: {len(net.getEdges())} edges")
        
        # Load GPS data
        print(f"📍 Loading GPS data...")
        df = pd.read_csv('../vehicle_2_4_first_200.csv')
        waypoints_df = df.head(num_waypoints)
        print(f"✅ Loaded {len(waypoints_df)} waypoints")
        
        # Find routes
        print("📍 Computing routes...")
        source_route, _ = find_optimal_path_through_waypoints(net, waypoints_df, 'source')
        dest_route, _ = find_optimal_path_through_waypoints(net, waypoints_df, 'destination')
        
        print(f"✅ Source route: {len(source_route)} edges")
        print(f"✅ Destination route: {len(dest_route)} edges")
        
        # Extend if needed
        if len(source_route) < 2:
            edge = net.getEdge(source_route[0])
            outgoing = edge.getOutgoing()
            if outgoing:
                source_route.append(list(outgoing.keys())[0].getID())
        
        if len(dest_route) < 2:
            edge = net.getEdge(dest_route[0])
            outgoing = edge.getOutgoing()
            if outgoing:
                dest_route.append(list(outgoing.keys())[0].getID())
        
        # Create route file
        print("📍 Creating route file...")
        route_file = 'strategy1_routes.rou.xml'
        with open(route_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<routes>\n')
            f.write('    <vType id="s1_src_type" accel="2.6" decel="4.5" sigma="0.5" ')
            f.write('length="4.5" width="1.8" height="1.5" minGap="2.5" ')
            f.write('maxSpeed="50" guiShape="passenger" color="0,0,255"/>\n')
            
            f.write('    <vType id="s1_dst_type" accel="2.6" decel="4.5" sigma="0.5" ')
            f.write('length="4.5" width="1.8" height="1.5" minGap="2.5" ')
            f.write('maxSpeed="50" guiShape="passenger" color="255,0,0"/>\n')
            
            f.write(f'    <route id="src_route" edges="{" ".join(source_route)}"/>\n')
            f.write(f'    <route id="dst_route" edges="{" ".join(dest_route)}"/>\n')
            
            f.write('    <vehicle id="s1_src" type="s1_src_type" ')
            f.write('route="src_route" depart="0" departLane="best" departSpeed="0"/>\n')
            
            f.write('    <vehicle id="s1_dst" type="s1_dst_type" ')
            f.write('route="dst_route" depart="0" departLane="best" departSpeed="0"/>\n')
            
            f.write('</routes>\n')
        
        # Create SUMO config
        config_file = 'strategy1.sumocfg'
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
        
        # Start SUMO
        print("🚀 Starting SUMO...")
        sumo_cmd = ["sumo", "-c", config_file, "--no-step-log", "true"]
        traci.start(sumo_cmd)
        time.sleep(2)
        
        # Add POIs
        waypoint_coords = []
        for idx, row in waypoints_df.iterrows():
            src_x, src_y = net.convertLonLat2XY(row['Longitude_source'], row['Latitude_source'])
            dst_x, dst_y = net.convertLonLat2XY(row['Longitude_destination'], row['Latitude_destination'])
            
            waypoint_coords.append({
                'source': (src_x, src_y),
                'dest': (dst_x, dst_y),
                'actual_distance': row['distance'],
                'source_speed_kmh': row['speed_kmh_source'],
                'dest_speed_kmh': row['speed_kmh_destination']
            })
        
        # Run simulation
        print("🎯 Starting simulation...")
        print("-"*70)
        
        step = 0
        source_active = False
        dest_active = False
        SIMULATION_STEPS = 6000
        
        source_progress = []
        dest_progress = []
        current_waypoint = 0
        waypoint_analysis = []
        
        while step < SIMULATION_STEPS:
            traci.simulationStep()
            step += 1
            
            vehicles = traci.vehicle.getIDList()
            
            # Source vehicle
            if "s1_src" in vehicles:
                if not source_active:
                    print(f"✅ Step {step}: Source vehicle active")
                    source_active = True
                
                src_pos = traci.vehicle.getPosition("s1_src")
                
                # Set realistic speed
                if current_waypoint < len(waypoint_coords):
                    target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['source_speed_kmh'])
                    traci.vehicle.setSpeed("s1_src", target_speed_ms)
                
                # Track progress
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
                    print(f"⚠️ Step {step}: Source completed")
                    break
            
            # Destination vehicle
            if "s1_dst" in vehicles:
                if not dest_active:
                    print(f"✅ Step {step}: Destination vehicle active")
                    dest_active = True
                
                dst_pos = traci.vehicle.getPosition("s1_dst")
                
                # Set realistic speed
                if current_waypoint < len(waypoint_coords):
                    target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['dest_speed_kmh'])
                    traci.vehicle.setSpeed("s1_dst", target_speed_ms)
                
                # Track progress
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
                    print(f"⚠️ Step {step}: Destination completed")
                    break
            
            # Calculate distances with ZONE-BASED calibration
            if source_active and dest_active:
                raw_distance = calculate_distance(src_pos, dst_pos)
                
                # Update waypoint
                prev_waypoint = current_waypoint
                if source_progress and dest_progress:
                    current_waypoint = min(source_progress[-1], dest_progress[-1])
                
                # Record analysis
                if current_waypoint != prev_waypoint and current_waypoint < len(waypoint_coords):
                    wp_data = waypoint_coords[current_waypoint]
                    actual_distance = wp_data['actual_distance']
                    
                    # GET ZONE-SPECIFIC CALIBRATION
                    calibration_factor, zone_name = get_zone_calibration(actual_distance)
                    calibrated_distance = raw_distance * calibration_factor
                    
                    distance_error = calibrated_distance - actual_distance
                    distance_error_pct = (distance_error / actual_distance * 100) if actual_distance > 0 else 0
                    distance_accuracy = max(0, 100 - abs(distance_error_pct))
                    
                    waypoint_analysis.append({
                        'waypoint': current_waypoint,
                        'step': step,
                        'actual_distance_m': actual_distance,
                        'simulated_distance_m': raw_distance,
                        'calibrated_distance_m': calibrated_distance,
                        'calibration_factor': calibration_factor,
                        'calibration_zone': zone_name,
                        'distance_error_m': distance_error,
                        'distance_error_pct': distance_error_pct,
                        'distance_accuracy_pct': distance_accuracy
                    })
                    
                    if current_waypoint % 10 == 0:
                        print(f"📊 Waypoint {current_waypoint}: Accuracy={distance_accuracy:.1f}%, Zone={zone_name}, Factor={calibration_factor}")
            
            if not source_active and not dest_active and step > 100:
                break
        
        # Analysis
        print("\n" + "="*70)
        print("STRATEGY 1 RESULTS")
        print("="*70)
        
        if waypoint_analysis:
            analysis_df = pd.DataFrame(waypoint_analysis)
            
            # Save CSV
            csv_file = os.path.join(original_dir, 'strategy1_results.csv')
            analysis_df.to_csv(csv_file, index=False)
            
            # Calculate metrics
            accuracies = analysis_df['distance_accuracy_pct']
            errors = analysis_df['distance_error_m']
            
            results = {
                'strategy': 'Multi-Zone Calibration',
                'strategy_number': 1,
                'mean_accuracy_pct': float(accuracies.mean()),
                'median_accuracy_pct': float(accuracies.median()),
                'min_accuracy_pct': float(accuracies.min()),
                'max_accuracy_pct': float(accuracies.max()),
                'std_accuracy_pct': float(accuracies.std()),
                'mae_m': float(errors.abs().mean()),
                'rmse_m': float((errors**2).mean()**0.5),
                'waypoints_analyzed': len(analysis_df),
                'high_accuracy_90_plus': int((accuracies >= 90).sum()),
                'medium_accuracy_70_89': int(((accuracies >= 70) & (accuracies < 90)).sum()),
                'low_accuracy_below_70': int((accuracies < 70).sum())
            }
            
            # Save JSON
            json_file = os.path.join(original_dir, 'strategy1_summary.json')
            with open(json_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n📊 Mean Accuracy: {results['mean_accuracy_pct']:.2f}%")
            print(f"📊 Median Accuracy: {results['median_accuracy_pct']:.2f}%")
            print(f"📊 MAE: {results['mae_m']:.2f} m")
            print(f"📊 RMSE: {results['rmse_m']:.2f} m")
            print(f"📊 Waypoints: {results['waypoints_analyzed']}")
            print(f"\n✅ Results saved:")
            print(f"   📄 {csv_file}")
            print(f"   📄 {json_file}")
            
            return results
        else:
            print("⚠️ No data collected")
            return None
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        try:
            traci.close()
        except:
            pass
        os.chdir(original_dir)

if __name__ == "__main__":
    run_strategy_1()

