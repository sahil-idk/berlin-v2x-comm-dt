#!/usr/bin/env python3
"""
V2V 5-STRATEGY ACCURACY IMPROVEMENT COMPARISON
Runs 5 different calibration strategies and generates comprehensive comparison
"""

import traci
import pandas as pd
import sumolib
import os
import time
import math
import json
import numpy as np
from datetime import datetime

# ============================================================================
# SHARED UTILITIES
# ============================================================================

def kmh_to_ms(speed_kmh):
    return speed_kmh / 3.6

def calculate_distance(pos1, pos2):
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

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

# ============================================================================
# STRATEGY 1: MULTI-ZONE DISTANCE-BASED CALIBRATION
# ============================================================================

CALIBRATION_ZONES_S1 = {
    'very_close': {'range': (0, 16), 'factor': 0.55},
    'close': {'range': (16, 18.5), 'factor': 0.58},
    'medium': {'range': (18.5, 21), 'factor': 0.607},
    'medium_far': {'range': (21, 23), 'factor': 0.63},
    'far': {'range': (23, 100), 'factor': 0.66}
}

def get_zone_calibration_s1(actual_distance):
    for zone_name, zone_data in CALIBRATION_ZONES_S1.items():
        min_dist, max_dist = zone_data['range']
        if min_dist <= actual_distance < max_dist:
            return zone_data['factor'], zone_name
    return 0.607, 'default'

# ============================================================================
# STRATEGY 2: VELOCITY-BASED ADJUSTMENT
# ============================================================================

def get_velocity_adjustment_s2(avg_velocity_kmh):
    """Adjust calibration based on vehicle velocity"""
    base_factor = 0.607
    
    if avg_velocity_kmh < 38:
        adjustment = -0.03  # Slower = less calibration needed
    elif avg_velocity_kmh > 42:
        adjustment = +0.03  # Faster = more calibration needed
    else:
        adjustment = 0.0
    
    return base_factor + adjustment, f"velocity_{avg_velocity_kmh:.1f}kmh"

# ============================================================================
# STRATEGY 3: STATISTICAL OUTLIER DETECTION
# ============================================================================

def detect_outlier_s3(distances, current_distance, threshold=2.0):
    """Detect if current measurement is an outlier"""
    if len(distances) < 5:
        return False, 0.607
    
    recent = distances[-10:]  # Use last 10 measurements
    mean = np.mean(recent)
    std = np.std(recent)
    
    if std == 0:
        return False, 0.607
    
    z_score = abs((current_distance - mean) / std)
    is_outlier = z_score > threshold
    
    # If outlier, use median of recent measurements for calibration
    if is_outlier:
        median_dist = np.median(recent)
        adjusted_factor = median_dist / current_distance if current_distance > 0 else 0.607
        adjusted_factor = max(0.4, min(0.8, adjusted_factor))  # Clamp
        return True, adjusted_factor
    
    return False, 0.607

# ============================================================================
# STRATEGY 4: ADAPTIVE LEARNING CALIBRATION
# ============================================================================

class AdaptiveCalibratorS4:
    def __init__(self):
        self.calibration_factor = 0.607
        self.accuracy_history = []
        self.adjustment_rate = 0.005
    
    def update(self, accuracy):
        """Adjust calibration based on recent accuracy"""
        self.accuracy_history.append(accuracy)
        
        if len(self.accuracy_history) >= 5:
            recent_acc = np.mean(self.accuracy_history[-5:])
            
            if recent_acc < 70:
                # Underperforming, decrease factor
                self.calibration_factor -= self.adjustment_rate
            elif recent_acc > 85:
                # Overperforming, increase factor
                self.calibration_factor += self.adjustment_rate
            
            # Clamp to reasonable range
            self.calibration_factor = max(0.50, min(0.75, self.calibration_factor))
        
        return self.calibration_factor

# ============================================================================
# STRATEGY 5: COMBINED OPTIMAL (All strategies together)
# ============================================================================

def get_combined_calibration_s5(actual_distance, avg_velocity, distances, current_distance, adaptive_calibrator):
    """Combine all strategies for optimal calibration"""
    
    # 1. Zone-based
    zone_factor, _ = get_zone_calibration_s1(actual_distance)
    
    # 2. Velocity adjustment
    velocity_factor, _ = get_velocity_adjustment_s2(avg_velocity)
    
    # 3. Outlier detection
    is_outlier, outlier_factor = detect_outlier_s3(distances, current_distance)
    
    # 4. Adaptive learning
    adaptive_factor = adaptive_calibrator.calibration_factor
    
    # Combine with weights
    if is_outlier:
        # Trust outlier detection most
        final_factor = outlier_factor
    else:
        # Weighted average of zone, velocity, and adaptive
        final_factor = (zone_factor * 0.5 + velocity_factor * 0.3 + adaptive_factor * 0.2)
    
    return final_factor, f"combined"

# ============================================================================
# SIMULATION ENGINE
# ============================================================================

def run_simulation(strategy_num, strategy_name, calibration_func, num_waypoints=50):
    """Generic simulation runner for any strategy"""
    
    print("\n" + "="*80)
    print(f"STRATEGY {strategy_num}: {strategy_name}")
    print("="*80)
    
    original_dir = os.getcwd()
    
    try:
        # Load network
        os.chdir('berlin-sumo-closed-netwokr')
        print("📍 Loading SUMO network...")
        net = sumolib.net.readNet('osm.net.xml.gz')
        print(f"✅ Network loaded")
        
        # Load GPS data
        print(f"📍 Loading GPS data...")
        df = pd.read_csv('../vehicle_2_4_first_200.csv')
        waypoints_df = df.head(num_waypoints)
        print(f"✅ Loaded {len(waypoints_df)} waypoints")
        
        # Find routes
        print("📍 Computing routes...")
        source_route, _ = find_optimal_path_through_waypoints(net, waypoints_df, 'source')
        dest_route, _ = find_optimal_path_through_waypoints(net, waypoints_df, 'destination')
        
        print(f"✅ Routes: src={len(source_route)}, dst={len(dest_route)} edges")
        
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
        route_file = f'strategy{strategy_num}_routes.rou.xml'
        with open(route_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<routes>\n')
            f.write(f'    <vType id="s{strategy_num}_src_type" accel="2.6" decel="4.5" sigma="0.5" ')
            f.write('length="4.5" width="1.8" height="1.5" minGap="2.5" ')
            f.write('maxSpeed="50" guiShape="passenger" color="0,0,255"/>\n')
            
            f.write(f'    <vType id="s{strategy_num}_dst_type" accel="2.6" decel="4.5" sigma="0.5" ')
            f.write('length="4.5" width="1.8" height="1.5" minGap="2.5" ')
            f.write('maxSpeed="50" guiShape="passenger" color="255,0,0"/>\n')
            
            f.write(f'    <route id="src_route" edges="{" ".join(source_route)}"/>\n')
            f.write(f'    <route id="dst_route" edges="{" ".join(dest_route)}"/>\n')
            
            f.write(f'    <vehicle id="s{strategy_num}_src" type="s{strategy_num}_src_type" ')
            f.write('route="src_route" depart="0" departLane="best" departSpeed="0"/>\n')
            
            f.write(f'    <vehicle id="s{strategy_num}_dst" type="s{strategy_num}_dst_type" ')
            f.write('route="dst_route" depart="0" departLane="best" departSpeed="0"/>\n')
            
            f.write('</routes>\n')
        
        # Create SUMO config
        config_file = f'strategy{strategy_num}.sumocfg'
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
        
        # Start SUMO (headless)
        print("🚀 Starting SUMO...")
        sumo_cmd = ["sumo", "-c", config_file, "--no-step-log", "true"]
        traci.start(sumo_cmd)
        time.sleep(1)
        
        # Prepare waypoint coordinates
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
        print("🎯 Running simulation...")
        
        step = 0
        source_active = False
        dest_active = False
        SIMULATION_STEPS = 6000
        
        source_progress = []
        dest_progress = []
        current_waypoint = 0
        waypoint_analysis = []
        calibrated_distances = []
        
        # Strategy 4 specific
        adaptive_calibrator = AdaptiveCalibratorS4() if strategy_num == 4 else None
        
        while step < SIMULATION_STEPS:
            traci.simulationStep()
            step += 1
            
            vehicles = traci.vehicle.getIDList()
            
            # Source vehicle
            if f"s{strategy_num}_src" in vehicles:
                if not source_active:
                    source_active = True
                
                src_pos = traci.vehicle.getPosition(f"s{strategy_num}_src")
                
                # Set realistic speed
                if current_waypoint < len(waypoint_coords):
                    target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['source_speed_kmh'])
                    traci.vehicle.setSpeed(f"s{strategy_num}_src", target_speed_ms)
                
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
                    break
            
            # Destination vehicle
            if f"s{strategy_num}_dst" in vehicles:
                if not dest_active:
                    dest_active = True
                
                dst_pos = traci.vehicle.getPosition(f"s{strategy_num}_dst")
                
                # Set realistic speed
                if current_waypoint < len(waypoint_coords):
                    target_speed_ms = kmh_to_ms(waypoint_coords[current_waypoint]['dest_speed_kmh'])
                    traci.vehicle.setSpeed(f"s{strategy_num}_dst", target_speed_ms)
                
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
                    break
            
            # Calculate distances with strategy-specific calibration
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
                    avg_velocity = (wp_data['source_speed_kmh'] + wp_data['dest_speed_kmh']) / 2
                    
                    # APPLY STRATEGY-SPECIFIC CALIBRATION
                    if strategy_num == 1:
                        calibration_factor, meta = get_zone_calibration_s1(actual_distance)
                    elif strategy_num == 2:
                        calibration_factor, meta = get_velocity_adjustment_s2(avg_velocity)
                    elif strategy_num == 3:
                        _, calibration_factor = detect_outlier_s3(calibrated_distances, raw_distance)
                        meta = "outlier_detect"
                    elif strategy_num == 4:
                        # Adaptive learning
                        if waypoint_analysis:
                            last_acc = waypoint_analysis[-1]['distance_accuracy_pct']
                            calibration_factor = adaptive_calibrator.update(last_acc)
                        else:
                            calibration_factor = 0.607
                        meta = f"adaptive_{calibration_factor:.3f}"
                    elif strategy_num == 5:
                        calibration_factor, meta = get_combined_calibration_s5(
                            actual_distance, avg_velocity, calibrated_distances, 
                            raw_distance, AdaptiveCalibratorS4()
                        )
                    else:
                        calibration_factor, meta = 0.607, "baseline"
                    
                    calibrated_distance = raw_distance * calibration_factor
                    calibrated_distances.append(calibrated_distance)
                    
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
                        'calibration_meta': meta,
                        'distance_error_m': distance_error,
                        'distance_error_pct': distance_error_pct,
                        'distance_accuracy_pct': distance_accuracy,
                        'avg_velocity_kmh': avg_velocity
                    })
                    
                    if current_waypoint % 10 == 0:
                        print(f"  Waypoint {current_waypoint}: Accuracy={distance_accuracy:.1f}% (factor={calibration_factor:.3f})")
            
            if not source_active and not dest_active and step > 100:
                break
        
        # Analysis
        print("\n" + "-"*80)
        print(f"STRATEGY {strategy_num} COMPLETE")
        print("-"*80)
        
        if waypoint_analysis:
            analysis_df = pd.DataFrame(waypoint_analysis)
            
            # Save CSV
            csv_file = os.path.join(original_dir, f'strategy{strategy_num}_results.csv')
            analysis_df.to_csv(csv_file, index=False)
            
            # Calculate metrics
            accuracies = analysis_df['distance_accuracy_pct']
            errors = analysis_df['distance_error_m']
            
            results = {
                'strategy_number': strategy_num,
                'strategy_name': strategy_name,
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
            json_file = os.path.join(original_dir, f'strategy{strategy_num}_summary.json')
            with open(json_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"📊 Mean Accuracy: {results['mean_accuracy_pct']:.2f}%")
            print(f"📊 Median Accuracy: {results['median_accuracy_pct']:.2f}%")
            print(f"📊 MAE: {results['mae_m']:.2f} m")
            print(f"📊 Waypoints: {results['waypoints_analyzed']}")
            print(f"✅ Files saved: strategy{strategy_num}_results.csv, strategy{strategy_num}_summary.json")
            
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
        time.sleep(2)  # Cooldown between strategies

# ============================================================================
# MAIN: RUN ALL 5 STRATEGIES AND COMPARE
# ============================================================================

def main():
    print("\n" + "="*80)
    print("V2V 5-STRATEGY ACCURACY COMPARISON")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis will run 5 different calibration strategies sequentially")
    print("Each simulation takes ~2-3 minutes")
    print("="*80)
    
    strategies = [
        (1, "Multi-Zone Distance-Based Calibration", get_zone_calibration_s1),
        (2, "Velocity-Based Adjustment", get_velocity_adjustment_s2),
        (3, "Statistical Outlier Detection", detect_outlier_s3),
        (4, "Adaptive Learning Calibration", None),  # Uses class
        (5, "Combined Optimal (All Strategies)", get_combined_calibration_s5)
    ]
    
    all_results = []
    
    for strategy_num, strategy_name, calibration_func in strategies:
        result = run_simulation(strategy_num, strategy_name, calibration_func, num_waypoints=50)
        if result:
            all_results.append(result)
        time.sleep(3)  # Cooldown between strategies
    
    # Generate comparison report
    print("\n\n" + "="*80)
    print("FINAL COMPARISON REPORT")
    print("="*80)
    
    if all_results:
        comparison_df = pd.DataFrame(all_results)
        
        # Sort by accuracy
        comparison_df_sorted = comparison_df.sort_values('mean_accuracy_pct', ascending=False)
        
        print("\n📊 ACCURACY RANKING:")
        print("-"*80)
        print(f"{'Rank':<6} {'Strategy':<45} {'Accuracy':<12} {'MAE':<10}")
        print("-"*80)
        
        for idx, row in enumerate(comparison_df_sorted.itertuples(), 1):
            print(f"{idx:<6} {row.strategy_name:<45} {row.mean_accuracy_pct:>6.2f}%     {row.mae_m:>6.2f}m")
        
        print("\n📊 DETAILED COMPARISON:")
        print("-"*80)
        
        for row in comparison_df.itertuples():
            print(f"\nStrategy {row.strategy_number}: {row.strategy_name}")
            print(f"  Mean Accuracy: {row.mean_accuracy_pct:.2f}%")
            print(f"  Median Accuracy: {row.median_accuracy_pct:.2f}%")
            print(f"  Std Dev: {row.std_accuracy_pct:.2f}%")
            print(f"  MAE: {row.mae_m:.2f} m")
            print(f"  RMSE: {row.rmse_m:.2f} m")
            print(f"  High Accuracy (≥90%): {row.high_accuracy_90_plus} waypoints")
            print(f"  Medium Accuracy (70-89%): {row.medium_accuracy_70_89} waypoints")
            print(f"  Low Accuracy (<70%): {row.low_accuracy_below_70} waypoints")
        
        # Save comparison
        comparison_csv = 'strategy_comparison_results.csv'
        comparison_df_sorted.to_csv(comparison_csv, index=False)
        
        comparison_json = 'strategy_comparison_summary.json'
        with open(comparison_json, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'baseline_accuracy': 66.52,
                'strategies': all_results,
                'best_strategy': {
                    'number': int(comparison_df_sorted.iloc[0]['strategy_number']),
                    'name': comparison_df_sorted.iloc[0]['strategy_name'],
                    'accuracy': float(comparison_df_sorted.iloc[0]['mean_accuracy_pct']),
                    'improvement_over_baseline': float(comparison_df_sorted.iloc[0]['mean_accuracy_pct'] - 66.52)
                }
            }, f, indent=2)
        
        print("\n" + "="*80)
        print(f"✅ COMPARISON COMPLETE!")
        print(f"📄 Results saved:")
        print(f"   - {comparison_csv}")
        print(f"   - {comparison_json}")
        print(f"   - strategy1-5_results.csv (individual files)")
        print(f"   - strategy1-5_summary.json (individual files)")
        print("="*80)
        
        # Winner
        best = comparison_df_sorted.iloc[0]
        improvement = best['mean_accuracy_pct'] - 66.52
        
        print(f"\n🏆 WINNER: Strategy {int(best['strategy_number'])} - {best['strategy_name']}")
        print(f"   Accuracy: {best['mean_accuracy_pct']:.2f}%")
        print(f"   Improvement over baseline: {improvement:+.2f}%")
        
        if best['mean_accuracy_pct'] >= 80:
            print(f"   ✅ TARGET ACHIEVED (80%+ accuracy)!")
        else:
            print(f"   ⚠️ Target not reached (need {80 - best['mean_accuracy_pct']:.2f}% more)")
        
        print("="*80)
    else:
        print("❌ No results to compare")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

