#!/usr/bin/env python3
"""
Dataset Comparison Script
Compares vehicle_2_4_first_200.csv vs vehicle_2_4_continuous_500.csv
to understand why accuracy dropped from 89% to 66%
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

def load_dataset(filepath):
    """Load and validate dataset"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return None
    
    df = pd.read_csv(filepath)
    print(f"✅ Loaded {filepath}: {len(df)} rows")
    return df

def calculate_distance_stats(df):
    """Calculate distance statistics between vehicles"""
    # Use the actual column names from the CSV
    lat1_col = 'Latitude_source'
    lon1_col = 'Longitude_source'
    lat2_col = 'Latitude_destination'
    lon2_col = 'Longitude_destination'
    
    if not all(col in df.columns for col in [lat1_col, lon1_col, lat2_col, lon2_col]):
        return None
    
    lat1, lon1 = df[lat1_col], df[lon1_col]
    lat2, lon2 = df[lat2_col], df[lon2_col]
    
    # Calculate distances using Haversine formula
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371000  # Earth radius in meters
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c
    
    distances = haversine_distance(lat1, lon1, lat2, lon2)
    
    return {
        'mean': distances.mean(),
        'median': distances.median(),
        'std': distances.std(),
        'min': distances.min(),
        'max': distances.max(),
        'q25': distances.quantile(0.25),
        'q75': distances.quantile(0.75),
        'count': len(distances)
    }

def analyze_gps_patterns(df, dataset_name):
    """Analyze GPS patterns and characteristics"""
    print(f"\n📊 Analyzing {dataset_name}")
    print("=" * 50)
    
    # Basic info
    print(f"Total waypoints: {len(df)}")
    
    # Distance analysis
    dist_stats = calculate_distance_stats(df)
    if dist_stats:
        print(f"\n📏 Distance Statistics:")
        print(f"  Mean: {dist_stats['mean']:.2f}m")
        print(f"  Median: {dist_stats['median']:.2f}m")
        print(f"  Std Dev: {dist_stats['std']:.2f}m")
        print(f"  Range: {dist_stats['min']:.2f}m - {dist_stats['max']:.2f}m")
        print(f"  Q25-Q75: {dist_stats['q25']:.2f}m - {dist_stats['q75']:.2f}m")
    
    # GPS coordinate analysis
    lat1_col = 'Latitude_source'
    lon1_col = 'Longitude_source'
    lat2_col = 'Latitude_destination'
    lon2_col = 'Longitude_destination'
    
    if all(col in df.columns for col in [lat1_col, lon1_col, lat2_col, lon2_col]):
        lat1, lon1 = df[lat1_col], df[lon1_col]
        lat2, lon2 = df[lat2_col], df[lon2_col]
        
        print(f"\n🌍 GPS Coverage:")
        print(f"  Source Vehicle:")
        print(f"    Lat: {lat1.min():.6f} to {lat1.max():.6f} (span: {lat1.max()-lat1.min():.6f})")
        print(f"    Lon: {lon1.min():.6f} to {lon1.max():.6f} (span: {lon1.max()-lon1.min():.6f})")
        print(f"  Dest Vehicle:")
        print(f"    Lat: {lat2.min():.6f} to {lat2.max():.6f} (span: {lat2.max()-lat2.min():.6f})")
        print(f"    Lon: {lon2.min():.6f} to {lon2.max():.6f} (span: {lon2.max()-lon2.min():.6f})")
    
    # Communication parameters
    comm_params = ['snr', 'rsrp', 'rssi']
    print(f"\n📡 Communication Parameters:")
    for param in comm_params:
        if param in df.columns:
            values = df[param].dropna()
            if len(values) > 0:
                print(f"  {param.upper()}: mean={values.mean():.2f}, std={values.std():.2f}, range={values.min():.2f}-{values.max():.2f}")
    
    return {
        'waypoints': len(df),
        'distance_stats': dist_stats,
        'gps_coverage': {
            'lat_range': (lat1.min(), lat1.max()) if all(col in df.columns for col in [lat1_col, lon1_col, lat2_col, lon2_col]) else None,
            'lon_range': (lon1.min(), lon1.max()) if all(col in df.columns for col in [lat1_col, lon1_col, lat2_col, lon2_col]) else None
        } if all(col in df.columns for col in [lat1_col, lon1_col, lat2_col, lon2_col]) else None
    }

def compare_datasets():
    """Main comparison function"""
    print("🔍 V2V Dataset Comparison Analysis")
    print("=" * 60)
    
    # Load datasets
    baseline_df = load_dataset('vehicle_2_4_first_200.csv')
    continuous_df = load_dataset('vehicle_2_4_continuous_500.csv')
    
    if baseline_df is None or continuous_df is None:
        print("❌ Cannot proceed without both datasets")
        return
    
    # Analyze each dataset
    baseline_stats = analyze_gps_patterns(baseline_df, "Baseline (first_200)")
    continuous_stats = analyze_gps_patterns(continuous_df, "Continuous (continuous_500)")
    
    # Direct comparison
    print(f"\n🔄 Direct Comparison")
    print("=" * 50)
    
    if baseline_stats['distance_stats'] and continuous_stats['distance_stats']:
        print(f"📏 Distance Comparison:")
        print(f"  Baseline Mean: {baseline_stats['distance_stats']['mean']:.2f}m")
        print(f"  Continuous Mean: {continuous_stats['distance_stats']['mean']:.2f}m")
        print(f"  Difference: {continuous_stats['distance_stats']['mean'] - baseline_stats['distance_stats']['mean']:.2f}m")
        
        print(f"\n📊 Distance Distribution:")
        print(f"  Baseline Std: {baseline_stats['distance_stats']['std']:.2f}m")
        print(f"  Continuous Std: {continuous_stats['distance_stats']['std']:.2f}m")
        print(f"  Variance Ratio: {continuous_stats['distance_stats']['std'] / baseline_stats['distance_stats']['std']:.2f}x")
    
    # GPS coverage comparison
    if baseline_stats['gps_coverage'] and continuous_stats['gps_coverage']:
        print(f"\n🌍 GPS Coverage Comparison:")
        baseline_lat_range = baseline_stats['gps_coverage']['lat_range'][1] - baseline_stats['gps_coverage']['lat_range'][0]
        continuous_lat_range = continuous_stats['gps_coverage']['lat_range'][1] - continuous_stats['gps_coverage']['lat_range'][0]
        
        print(f"  Baseline Lat Span: {baseline_lat_range:.6f}")
        print(f"  Continuous Lat Span: {continuous_lat_range:.6f}")
        print(f"  Coverage Ratio: {continuous_lat_range / baseline_lat_range:.2f}x")
    
    # Test with same number of waypoints
    print(f"\n🧪 Testing with Same Waypoint Count")
    print("=" * 50)
    
    # Test first 133 points from baseline
    test_baseline = baseline_df.head(133)
    test_continuous = continuous_df.head(133)
    
    print(f"Testing with 133 waypoints:")
    print(f"  Baseline (first 133): {len(test_baseline)} points")
    print(f"  Continuous (first 133): {len(test_continuous)} points")
    
    # Analyze test samples
    baseline_test_stats = analyze_gps_patterns(test_baseline, "Baseline Test (133 pts)")
    continuous_test_stats = analyze_gps_patterns(test_continuous, "Continuous Test (133 pts)")
    
    # Key insights
    print(f"\n💡 Key Insights")
    print("=" * 50)
    
    if baseline_test_stats['distance_stats'] and continuous_test_stats['distance_stats']:
        baseline_mean = baseline_test_stats['distance_stats']['mean']
        continuous_mean = continuous_test_stats['distance_stats']['mean']
        
        print(f"1. Distance Pattern:")
        print(f"   Baseline 133pts: {baseline_mean:.2f}m")
        print(f"   Continuous 133pts: {continuous_mean:.2f}m")
        print(f"   Difference: {continuous_mean - baseline_mean:.2f}m")
        
        if abs(continuous_mean - baseline_mean) > 5:
            print(f"   ⚠️  SIGNIFICANT difference - different GPS patterns!")
        else:
            print(f"   ✅ Similar patterns - issue may be calibration")
    
    print(f"\n2. Recommendation:")
    if baseline_test_stats['distance_stats'] and continuous_test_stats['distance_stats']:
        if abs(continuous_test_stats['distance_stats']['mean'] - baseline_test_stats['distance_stats']['mean']) > 5:
            print(f"   📋 Continuous dataset has different characteristics")
            print(f"   📋 Need adaptive calibration for continuous data")
            print(f"   📋 Consider using baseline for production")
        else:
            print(f"   📋 Similar patterns - focus on calibration optimization")
    
    # Save comparison report
    report = {
        'baseline_stats': baseline_stats,
        'continuous_stats': continuous_stats,
        'test_comparison': {
            'baseline_133': baseline_test_stats,
            'continuous_133': continuous_test_stats
        },
        'recommendation': 'adaptive_calibration' if abs(continuous_test_stats['distance_stats']['mean'] - baseline_test_stats['distance_stats']['mean']) > 5 else 'calibration_optimization'
    }
    
    import json
    with open('dataset_comparison_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Report saved to: dataset_comparison_report.json")
    print(f"✅ Analysis complete!")

if __name__ == "__main__":
    compare_datasets()
