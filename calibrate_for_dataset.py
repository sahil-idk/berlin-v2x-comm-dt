#!/usr/bin/env python3
"""
Calibration Optimization Script
Calculates optimal calibration factor for continuous_500 dataset
based on the analysis showing 6.82m difference in distance patterns
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar
import json

def load_dataset(filepath):
    """Load dataset"""
    df = pd.read_csv(filepath)
    print(f"✅ Loaded {filepath}: {len(df)} rows")
    return df

def calculate_actual_distances(df):
    """Calculate actual distances from GPS coordinates"""
    lat1, lon1 = df['Latitude_source'], df['Longitude_source']
    lat2, lon2 = df['Latitude_destination'], df['Longitude_destination']
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371000  # Earth radius in meters
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c
    
    return haversine_distance(lat1, lon1, lat2, lon2)

def simulate_distances_with_calibration(actual_distances, calibration_factor):
    """Simulate distances using calibration factor"""
    # This simulates what SUMO would produce before calibration
    # We reverse-engineer the calibration process
    raw_simulated = actual_distances / calibration_factor
    return raw_simulated

def calculate_accuracy(simulated_distances, actual_distances):
    """Calculate distance accuracy percentage"""
    errors = np.abs(simulated_distances - actual_distances)
    accuracies = 100 * (1 - errors / actual_distances)
    return np.mean(accuracies)

def optimize_calibration_factor(actual_distances, calibration_range=(0.3, 1.0)):
    """Find optimal calibration factor"""
    print(f"🔍 Optimizing calibration factor for {len(actual_distances)} distances...")
    print(f"📏 Actual distance range: {actual_distances.min():.2f}m - {actual_distances.max():.2f}m")
    print(f"📊 Actual distance mean: {actual_distances.mean():.2f}m")
    
    def objective(calibration_factor):
        simulated_distances = simulate_distances_with_calibration(actual_distances, calibration_factor)
        accuracy = calculate_accuracy(simulated_distances, actual_distances)
        return -accuracy  # Minimize negative accuracy (maximize accuracy)
    
    # Test current calibration factor
    current_accuracy = calculate_accuracy(
        simulate_distances_with_calibration(actual_distances, 0.607), 
        actual_distances
    )
    print(f"📊 Current calibration (0.607): {current_accuracy:.2f}% accuracy")
    
    # Optimize
    result = minimize_scalar(objective, bounds=calibration_range, method='bounded')
    optimal_factor = result.x
    optimal_accuracy = -result.fun
    
    print(f"🎯 Optimal calibration factor: {optimal_factor:.4f}")
    print(f"📈 Optimal accuracy: {optimal_accuracy:.2f}%")
    print(f"📊 Improvement: +{optimal_accuracy - current_accuracy:.2f}%")
    
    return optimal_factor, optimal_accuracy, current_accuracy

def analyze_distance_ranges(actual_distances):
    """Analyze optimal calibration for different distance ranges"""
    print(f"\n📊 Distance Range Analysis")
    print("=" * 50)
    
    ranges = [
        (0, 15, "Short (<15m)"),
        (15, 25, "Medium (15-25m)"),
        (25, 40, "Long (25-40m)"),
        (40, float('inf'), "Very Long (>40m)")
    ]
    
    range_results = {}
    
    for min_dist, max_dist, label in ranges:
        if max_dist == float('inf'):
            mask = actual_distances >= min_dist
        else:
            mask = (actual_distances >= min_dist) & (actual_distances < max_dist)
        
        if mask.sum() < 5:  # Need at least 5 samples
            continue
            
        range_distances = actual_distances[mask]
        optimal_factor, optimal_accuracy, current_accuracy = optimize_calibration_factor(range_distances)
        
        range_results[label] = {
            'count': len(range_distances),
            'mean_distance': range_distances.mean(),
            'optimal_factor': optimal_factor,
            'optimal_accuracy': optimal_accuracy,
            'current_accuracy': current_accuracy,
            'improvement': optimal_accuracy - current_accuracy
        }
        
        print(f"\n{label}:")
        print(f"  Count: {len(range_distances)}")
        print(f"  Mean distance: {range_distances.mean():.2f}m")
        print(f"  Optimal factor: {optimal_factor:.4f}")
        print(f"  Optimal accuracy: {optimal_accuracy:.2f}%")
        print(f"  Improvement: +{optimal_accuracy - current_accuracy:.2f}%")
    
    return range_results

def create_adaptive_calibration_function(range_results):
    """Create adaptive calibration function based on distance ranges"""
    print(f"\n🔧 Creating Adaptive Calibration Function")
    print("=" * 50)
    
    # Sort ranges by mean distance
    sorted_ranges = sorted(range_results.items(), key=lambda x: x[1]['mean_distance'])
    
    print("Adaptive calibration thresholds:")
    for label, data in sorted_ranges:
        print(f"  {data['mean_distance']:.1f}m: factor={data['optimal_factor']:.4f}")
    
    # Create function code
    function_code = f"""
def get_adaptive_calibration(actual_distance_m):
    \"\"\"Adaptive calibration based on distance ranges\"\"\"
    if actual_distance_m < 15:
        return {sorted_ranges[0][1]['optimal_factor']:.4f}  # Short distances
    elif actual_distance_m < 25:
        return {sorted_ranges[1][1]['optimal_factor']:.4f}  # Medium distances
    elif actual_distance_m < 40:
        return {sorted_ranges[2][1]['optimal_factor']:.4f}  # Long distances
    else:
        return {sorted_ranges[3][1]['optimal_factor']:.4f}  # Very long distances
"""
    
    print(f"\nGenerated function:")
    print(function_code)
    
    return function_code, sorted_ranges

def main():
    """Main optimization function"""
    print("🎯 V2V Calibration Optimization")
    print("=" * 60)
    
    # Load continuous dataset
    df = load_dataset('vehicle_2_4_continuous_500.csv')
    
    # Calculate actual distances
    actual_distances = calculate_actual_distances(df)
    
    # Overall optimization
    print(f"\n🔍 Overall Calibration Optimization")
    print("=" * 50)
    optimal_factor, optimal_accuracy, current_accuracy = optimize_calibration_factor(actual_distances)
    
    # Range-based optimization
    range_results = analyze_distance_ranges(actual_distances)
    
    # Create adaptive calibration
    adaptive_code, sorted_ranges = create_adaptive_calibration_function(range_results)
    
    # Save results
    results = {
        'dataset': 'vehicle_2_4_continuous_500.csv',
        'total_waypoints': len(df),
        'overall_optimization': {
            'current_factor': 0.607,
            'current_accuracy': current_accuracy,
            'optimal_factor': optimal_factor,
            'optimal_accuracy': optimal_accuracy,
            'improvement': optimal_accuracy - current_accuracy
        },
        'range_optimization': range_results,
        'adaptive_calibration': {
            'function_code': adaptive_code,
            'thresholds': {label: data['mean_distance'] for label, data in sorted_ranges}
        }
    }
    
    with open('calibration_optimization_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: calibration_optimization_results.json")
    
    # Recommendations
    print(f"\n💡 Recommendations")
    print("=" * 50)
    print(f"1. Overall improvement: Use factor {optimal_factor:.4f} (+{optimal_accuracy - current_accuracy:.1f}%)")
    print(f"2. Adaptive calibration: Implement distance-based factors")
    print(f"3. Expected accuracy: {optimal_accuracy:.1f}% (vs current {current_accuracy:.1f}%)")
    
    if optimal_accuracy > 75:
        print(f"✅ Target achieved: >75% accuracy possible")
    else:
        print(f"⚠️  Target not met: Consider other improvements")
    
    print(f"\n✅ Calibration optimization complete!")

if __name__ == "__main__":
    main()
