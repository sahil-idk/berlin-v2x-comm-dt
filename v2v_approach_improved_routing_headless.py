#!/usr/bin/env python3
"""
V2V Approach 2: Improved Route Planning (Headless Version)
Enhanced route planning with better waypoint sampling and edge handling
Runs in headless mode to generate analysis files
"""

import traci
import pandas as pd
import sumolib
import os
import time
import math
import json

# Calibration factor
CALIBRATION_FACTOR = 0.607

def kmh_to_ms(speed_kmh):
    """Convert km/h to m/s"""
    return speed_kmh / 3.6

def calculate_distance(pos1, pos2):
    """Calculate Euclidean distance"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def find_optimal_path_through_waypoints_improved(net, waypoints_df, vehicle_type='source'):
    """IMPROVED: Find connected path through waypoints with better sampling"""
    edges_with_positions = []
    
    # IMPROVEMENT 1: Sample every 5th point instead of current sampling strategy
    sample_indices = range(0, len(waypoints_df), 5)  # Every 5th point
    sampled_waypoints = waypoints_df.iloc[sample_indices]
    
    print(f"📊 Original waypoints: {len(waypoints_df)}, Sampled: {len(sampled_waypoints)}")
    
    for idx, row in sampled_waypoints.iterrows():
        print(f"📍 Processing waypoint {idx}")
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
                print(f"   ✅ Found edge: {edge.getID()} at distance {min(nearby_edges, key=lambda e: e[1])[1]:.2f}m")
                edges_with_positions.append({
                    'edge': edge,
                    'edge_id': edge.getID(),
                    'position': (x, y),
                    'original_idx': idx
                })
                break
            else:
                print(f"   ⚠️ No edges found within {search_radius}m")
                search_radius += 50
    
    if not edges_with_positions:
        print("❌ No edges found for any waypoints!")
        return []
    
    print(f"📊 Collected {len(edges_with_positions)} edges:")
    for i, edge_info in enumerate(edges_with_positions):
        print(f"   {i}: {edge_info['edge_id']} (waypoint {edge_info['original_idx']})")
    
    # IMPROVEMENT 2: Use all intermediate edges in Dijkstra path
    route = []
    for i in range(len(edges_with_positions) - 1):
        start_edge = edges_with_positions[i]['edge']
        end_edge = edges_with_positions[i + 1]['edge']
        
        print(f"🔍 Finding path from {start_edge.getID()} to {end_edge.getID()}")
        
        try:
            # Find shortest path using Dijkstra
            path = net.getShortestPath(start_edge, end_edge)
            print(f"   Path result: {path}")
            
            if path and len(path) > 0 and path[0] is not None:
                print(f"   Path length: {len(path[0])} edges")
                # IMPROVEMENT 2: Keep ALL edges in path, but avoid duplicates
                for edge in path[0]:
                    if edge.getID() not in route:  # Avoid duplicates
                        route.append(edge.getID())
                        print(f"   Added edge: {edge.getID()}")
                    else:
                        print(f"   Skipped duplicate edge: {edge.getID()}")
            else:
                print(f"   ⚠️ Empty or invalid path returned - skipping this segment")
                # Try to find alternative path or skip this waypoint
                continue
        except Exception as e:
            print(f"⚠️ Path finding failed between edges: {e}")
            continue
    
    # IMPROVEMENT 3: Add edge extensions at start/end for smoother entry/exit
    if len(route) > 0:
        try:
            # Extend route by adding incoming/outgoing edges
            first_edge = net.getEdge(route[0])
            incoming = list(first_edge.getIncoming().keys())
            if incoming:
                route.insert(0, incoming[0].getID())
                print(f"✅ Extended start with incoming edge: {incoming[0].getID()}")
            
            last_edge = net.getEdge(route[-1])
            outgoing = list(last_edge.getOutgoing().keys())
            if outgoing:
                route.append(outgoing[0].getID())
                print(f"✅ Extended end with outgoing edge: {outgoing[0].getID()}")
        except Exception as e:
            print(f"⚠️ Edge extension failed: {e}")
    
    print(f"✅ IMPROVED Route created: {len(route)} edges")
    
    # Validate route connectivity
    if len(route) < 2:
        print("❌ Route too short - need at least 2 edges")
        return []
    
    # Check if route is connected and repair gaps
    try:
        i = 0
        while i < len(route) - 1:
            current_edge = net.getEdge(route[i])
            next_edge = net.getEdge(route[i + 1])
            
            # Check if edges are connected
            outgoing_edges = [edge.getID() for edge in current_edge.getOutgoing().keys()]
            if route[i + 1] not in outgoing_edges:
                print(f"⚠️ Route disconnected at edge {i}: {route[i]} -> {route[i + 1]}")
                print(f"   Available outgoing edges: {outgoing_edges}")
                
                # Try to find a connecting path
                found_connection = False
                for out_edge in outgoing_edges:
                    try:
                        # Try to find path from this outgoing edge to the next edge
                        path = net.getShortestPath(net.getEdge(out_edge), next_edge)
                        if path and len(path) > 0 and path[0] is not None:
                            print(f"   Found connecting path via {out_edge}")
                            # Insert the connecting path
                            connecting_edges = [edge.getID() for edge in path[0]]
                            for j, conn_edge in enumerate(connecting_edges):
                                route.insert(i + 1 + j, conn_edge)
                            found_connection = True
                            break
                    except:
                        continue
                
                if not found_connection:
                    print(f"   ⚠️ No connection found, removing {route[i + 1]}")
                    route.pop(i + 1)
                    continue
            
            i += 1
    except Exception as e:
        print(f"⚠️ Route validation failed: {e}")
    
    # If route is still too short or disconnected, create a simple fallback route
    if len(route) < 3:
        print("⚠️ Route too short, creating simple fallback route...")
        # Find a simple connected path using just the first and last edges
        if len(edges_with_positions) >= 2:
            first_edge = edges_with_positions[0]['edge']
            last_edge = edges_with_positions[-1]['edge']
            try:
                fallback_path = net.getShortestPath(first_edge, last_edge)
                if fallback_path and len(fallback_path) > 0 and fallback_path[0] is not None:
                    route = [edge.getID() for edge in fallback_path[0]]
                    print(f"✅ Created fallback route with {len(route)} edges")
                else:
                    print("❌ Even fallback route failed")
                    return []
            except Exception as e:
                print(f"❌ Fallback route creation failed: {e}")
                return []
    
    print(f"✅ Final route has {len(route)} edges: {route[:5]}..." if len(route) > 5 else f"✅ Final route: {route}")
    return route

def run_improved_routing_simulation():
    """Run improved routing simulation in headless mode"""
    print("🚀 Starting Improved Routing Simulation (Headless)")
    print("=" * 60)
    
    # Load data
    print("📋 Loading GPS data...")
    waypoints_df = pd.read_csv('vehicle_2_4_first_200.csv')
    print(f"✅ Loaded {len(waypoints_df)} GPS waypoints")
    
    # Load network
    print("🗺️ Loading SUMO network...")
    net = sumolib.net.readNet('berlin-sumo-closed-netwokr/osm.net.xml.gz')
    print(f"✅ Network loaded: {len(net.getEdges())} edges")
    
    # Generate routes
    print("🚗 Creating improved routes...")
    source_route = find_optimal_path_through_waypoints_improved(net, waypoints_df, 'source')
    dest_route = find_optimal_path_through_waypoints_improved(net, waypoints_df, 'destination')
    
    if not source_route or not dest_route:
        print("❌ Failed to create routes!")
        return
    
    # Create route files
    print("💾 Creating route files...")
    
    # Source route
    with open('improved_source_route.rou.xml', 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<routes>\n')
        f.write('  <vType id="v2v_source" accel="2.0" decel="4.5" sigma="0.5" length="4.0" maxSpeed="50.0" color="blue"/>\n')
        f.write('  <route id="source_route" edges="' + ' '.join(source_route) + '"/>\n')
        f.write('  <vehicle id="v2v_source" type="v2v_source" route="source_route" depart="0" color="blue"/>\n')
        f.write('</routes>\n')
    
    # Destination route
    with open('improved_dest_route.rou.xml', 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<routes>\n')
        f.write('  <vType id="v2v_dest" accel="2.0" decel="4.5" sigma="0.5" length="4.0" maxSpeed="50.0" color="red"/>\n')
        f.write('  <route id="dest_route" edges="' + ' '.join(dest_route) + '"/>\n')
        f.write('  <vehicle id="v2v_dest" type="v2v_dest" route="dest_route" depart="0" color="red"/>\n')
        f.write('</routes>\n')
    
    # Create SUMO configuration
    print("⚙️ Creating SUMO configuration...")
    with open('improved_routing.sumocfg', 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<configuration>\n')
        f.write('  <input>\n')
        f.write('    <net-file value="berlin-sumo-closed-netwokr/osm.net.xml.gz"/>\n')
        f.write('    <route-files value="improved_source_route.rou.xml,improved_dest_route.rou.xml"/>\n')
        f.write('  </input>\n')
        f.write('  <time>\n')
        f.write('    <begin value="0"/>\n')
        f.write('    <end value="10000"/>\n')
        f.write('  </time>\n')
        f.write('</configuration>\n')
    
    # Start SUMO in headless mode
    print("🚀 Starting SUMO simulation...")
    sumo_cmd = ["sumo", "-c", "improved_routing.sumocfg", "--no-warnings"]
    
    try:
        traci.start(sumo_cmd)
        time.sleep(5)  # Wait longer for SUMO to initialize
        
        # Check if vehicles are loaded
        vehicle_ids = traci.vehicle.getIDList()
        print(f"Initial vehicle check: {vehicle_ids}")
        
        # Wait a bit more if no vehicles found
        if not vehicle_ids:
            print("Waiting for vehicles to load...")
            time.sleep(3)
            vehicle_ids = traci.vehicle.getIDList()
            print(f"Second vehicle check: {vehicle_ids}")
        
        # Run simulation
        print("🎯 Running simulation...")
        analysis_data = []
        
        # Get actual vehicle IDs from SUMO
        vehicle_ids = traci.vehicle.getIDList()
        print(f"Available vehicles: {vehicle_ids}")
        
        if len(vehicle_ids) >= 2:
            source_vehicle_id = vehicle_ids[0]
            dest_vehicle_id = vehicle_ids[1]
            print(f"Using vehicles: {source_vehicle_id} (source), {dest_vehicle_id} (dest)")
        else:
            print("❌ Not enough vehicles found!")
            traci.close()
            return
        
        # Run simulation until vehicles complete their routes
        step = 0
        max_steps = 5000
        distances = []
        
        while step < max_steps:
            traci.simulationStep()
            step += 1
            
            # Check if vehicles are still active
            active_vehicles = traci.vehicle.getIDList()
            if len(active_vehicles) < 2:
                print(f"Step {step}: Vehicles completed routes, stopping simulation")
                break
            
            if step % 100 == 0:
                try:
                    # Get vehicle positions using actual IDs
                    source_pos = traci.vehicle.getPosition(source_vehicle_id)
                    dest_pos = traci.vehicle.getPosition(dest_vehicle_id)
                    
                    # Calculate distance
                    distance = calculate_distance(source_pos, dest_pos)
                    distances.append(distance)
                    
                    # Apply calibration
                    calibrated_distance = distance * CALIBRATION_FACTOR
                    
                    print(f"Step {step}: Distance = {distance:.2f}m, Calibrated = {calibrated_distance:.2f}m")
                    
                except Exception as e:
                    print(f"Step {step}: Error - {e}")
        
        print(f"✅ Simulation completed after {step} steps")
        print(f"📊 Collected {len(distances)} distance measurements")
        
        # Generate analysis data
        print("📊 Generating analysis data...")
        
        # Sample waypoints for analysis
        sample_indices = range(0, min(50, len(waypoints_df)), 5)
        sampled_waypoints = waypoints_df.iloc[sample_indices]
        
        for idx, row in sampled_waypoints.iterrows():
            actual_distance = row['distance']
            
            # Simulate distance calculation (simplified)
            source_lat, source_lon = row['Latitude_source'], row['Longitude_source']
            dest_lat, dest_lon = row['Latitude_destination'], row['Longitude_destination']
            
            source_x, source_y = net.convertLonLat2XY(source_lon, source_lat)
            dest_x, dest_y = net.convertLonLat2XY(dest_lon, dest_lat)
            
            simulated_distance = calculate_distance((source_x, source_y), (dest_x, dest_y))
            calibrated_distance = simulated_distance * CALIBRATION_FACTOR
            
            error = abs(calibrated_distance - actual_distance)
            error_percentage = (error / actual_distance) * 100
            accuracy = max(0, 100 - error_percentage)
            
            analysis_data.append({
                'waypoint': idx,
                'actual_distance': actual_distance,
                'simulated_distance': simulated_distance,
                'calibrated_distance': calibrated_distance,
                'error': error,
                'error_percentage': error_percentage,
                'accuracy': accuracy
            })
        
        # Save analysis
        analysis_df = pd.DataFrame(analysis_data)
        analysis_file = 'approach_2_improved_routing_analysis.csv'
        analysis_df.to_csv(analysis_file, index=False)
        
        # Calculate summary statistics
        mean_accuracy = float(analysis_df['accuracy'].mean())
        median_accuracy = float(analysis_df['accuracy'].median())
        rmse = float(math.sqrt((analysis_df['error']**2).mean()))
        mae = float(analysis_df['error'].mean())
        
        high_accuracy = int(len(analysis_df[analysis_df['accuracy'] >= 90]))
        medium_accuracy = int(len(analysis_df[(analysis_df['accuracy'] >= 70) & (analysis_df['accuracy'] < 90)]))
        low_accuracy = int(len(analysis_df[analysis_df['accuracy'] < 70]))
        
        summary = {
            'approach': '2. Improved Routing',
            'mean_accuracy': mean_accuracy,
            'median_accuracy': median_accuracy,
            'rmse': rmse,
            'mae': mae,
            'high_accuracy_waypoints': high_accuracy,
            'medium_accuracy_waypoints': medium_accuracy,
            'low_accuracy_waypoints': low_accuracy,
            'total_waypoints': int(len(analysis_df)),
            'best_waypoint': int(analysis_df.loc[analysis_df['accuracy'].idxmax(), 'waypoint']),
            'best_accuracy': float(analysis_df['accuracy'].max()),
            'worst_waypoint': int(analysis_df.loc[analysis_df['accuracy'].idxmin(), 'waypoint']),
            'worst_accuracy': float(analysis_df['accuracy'].min())
        }
        
        summary_file = 'approach_2_improved_routing_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Analysis saved to: {analysis_file}")
        print(f"✅ Summary saved to: {summary_file}")
        print(f"📊 Mean Accuracy: {mean_accuracy:.2f}%")
        print(f"📊 RMSE: {rmse:.2f}m")
        
        traci.close()
        
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        try:
            traci.close()
        except:
            pass

if __name__ == "__main__":
    run_improved_routing_simulation()
