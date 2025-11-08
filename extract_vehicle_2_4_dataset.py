#!/usr/bin/env python3
"""
Extract focused dataset for Vehicle 2 and Vehicle 4 interactions
Creates datasets of various sizes for digital twin validation
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import argparse

def extract_vehicle_2_4_dataset(num_points=200, sampling_method='sequential'):
    """Extract and analyze Vehicle 2-4 interactions"""
    
    print("🔍 Extracting Vehicle 2-4 Interaction Dataset")
    print("=" * 50)
    print(f"📊 Target size: {num_points} points")
    print(f"📊 Sampling method: {sampling_method}")
    
    # Load the full dataset
    print("\n📋 Loading sidelink dataset...")
    df = pd.read_csv('sidelink_parsed.csv')
    print(f"✅ Loaded {len(df)} total records")
    
    # Filter for Vehicle 2 and Vehicle 4 interactions
    print("\n🎯 Filtering for Vehicle 2-4 interactions...")
    vehicle_2_4_data = df[
        ((df['Source'] == 2) & (df['Destination'] == 4)) |
        ((df['Source'] == 4) & (df['Destination'] == 2))
    ].copy()
    
    print(f"✅ Found {len(vehicle_2_4_data)} Vehicle 2-4 interaction records")
    
    if len(vehicle_2_4_data) == 0:
        print("❌ No Vehicle 2-4 interactions found!")
        return None
    
    # Analyze GPS coordinate distribution
    print("\n📍 Analyzing GPS coordinate distribution...")
    
    # Get all unique GPS coordinates
    source_coords = vehicle_2_4_data[['Latitude_source', 'Longitude_source']].drop_duplicates()
    dest_coords = vehicle_2_4_data[['Latitude_destination', 'Longitude_destination']].drop_duplicates()
    
    print(f"   Unique source coordinates: {len(source_coords)}")
    print(f"   Unique destination coordinates: {len(dest_coords)}")
    
    # Calculate coordinate bounds
    all_lats = pd.concat([
        vehicle_2_4_data['Latitude_source'],
        vehicle_2_4_data['Latitude_destination']
    ])
    all_lons = pd.concat([
        vehicle_2_4_data['Longitude_source'],
        vehicle_2_4_data['Longitude_destination']
    ])
    
    bounds = {
        'min_lat': all_lats.min(),
        'max_lat': all_lats.max(),
        'min_lon': all_lons.min(),
        'max_lon': all_lons.max(),
        'center_lat': all_lats.mean(),
        'center_lon': all_lons.mean()
    }
    
    print(f"   Latitude range: {bounds['min_lat']:.6f} to {bounds['max_lat']:.6f}")
    print(f"   Longitude range: {bounds['min_lon']:.6f} to {bounds['max_lon']:.6f}")
    print(f"   Center: ({bounds['center_lat']:.6f}, {bounds['center_lon']:.6f})")
    
    # Calculate approximate area coverage
    lat_range = bounds['max_lat'] - bounds['min_lat']
    lon_range = bounds['max_lon'] - bounds['min_lon']
    print(f"   Coverage: {lat_range:.6f}° × {lon_range:.6f}°")
    
    # Sample subset based on specified size and method
    print(f"\n📊 Creating {num_points}-point dataset using {sampling_method} sampling...")
    
    # Sort by timestamp to get chronological order
    vehicle_2_4_data = vehicle_2_4_data.sort_values('timestamp').reset_index(drop=True)
    
    # Apply sampling method
    if sampling_method == 'sequential':
        # Take first N points (simple, preserves temporal order)
        focused_subset = vehicle_2_4_data.head(num_points).copy()
        print(f"✅ Extracted first {len(focused_subset)} sequential records")
    elif sampling_method == 'uniform':
        # Uniform sampling across entire dataset
        if num_points >= len(vehicle_2_4_data):
            focused_subset = vehicle_2_4_data.copy()
            print(f"⚠️ Requested {num_points} points, but only {len(focused_subset)} available")
        else:
            step = len(vehicle_2_4_data) // num_points
            focused_subset = vehicle_2_4_data.iloc[::step].head(num_points).copy()
            print(f"✅ Sampled {len(focused_subset)} records uniformly (every {step}th record)")
    elif sampling_method == 'all':
        # Take all available records
        focused_subset = vehicle_2_4_data.copy()
        print(f"✅ Extracted all {len(focused_subset)} available records")
    else:
        print(f"⚠️ Unknown sampling method '{sampling_method}', using sequential")
        focused_subset = vehicle_2_4_data.head(num_points).copy()
    
    print(f"✅ Final dataset size: {len(focused_subset)} records")
    
    # Analyze the subset
    print("\n📈 Subset Analysis:")
    print(f"   Time range: {focused_subset['timestamp'].min()} to {focused_subset['timestamp'].max()}")
    print(f"   Scenarios: {focused_subset['Scenario'].unique()}")
    print(f"   Distance range: {focused_subset['distance'].min():.1f}m to {focused_subset['distance'].max():.1f}m")
    
    # Communication quality analysis
    if 'SNR' in focused_subset.columns:
        print(f"   SNR range: {focused_subset['SNR'].min():.1f} to {focused_subset['SNR'].max():.1f} dB")
    if 'RSRP' in focused_subset.columns:
        print(f"   RSRP range: {focused_subset['RSRP'].min():.1f} to {focused_subset['RSRP'].max():.1f} dBm")
    
    # Save the focused dataset with descriptive name
    if num_points == len(vehicle_2_4_data) or sampling_method == 'all':
        output_file = 'vehicle_2_4_full.csv'
    else:
        output_file = f'vehicle_2_4_{len(focused_subset)}.csv'
    
    focused_subset.to_csv(output_file, index=False)
    print(f"\n💾 Saved dataset: {output_file}")
    
    # Save metadata
    metadata = {
        'extraction_date': datetime.now().isoformat(),
        'total_records': len(df),
        'vehicle_2_4_records': len(vehicle_2_4_data),
        'extracted_subset_size': len(focused_subset),
        'target_points': num_points,
        'sampling_method': sampling_method,
        'coordinate_bounds': bounds,
        'coverage_degrees': {
            'latitude': lat_range,
            'longitude': lon_range
        },
        'scenarios': focused_subset['Scenario'].unique().tolist(),
        'distance_range': {
            'min': float(focused_subset['distance'].min()),
            'max': float(focused_subset['distance'].max()),
            'mean': float(focused_subset['distance'].mean())
        }
    }
    
    metadata_file = output_file.replace('.csv', '_metadata.json')
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"💾 Saved metadata: {metadata_file}")
    
    # Display sample of the focused data
    print("\n📋 Sample of focused dataset:")
    print(focused_subset[['timestamp', 'Source', 'Destination', 'Latitude_source', 'Longitude_source', 
                         'Latitude_destination', 'Longitude_destination', 'distance', 'SNR', 'RSRP']].head())
    
    return focused_subset, bounds

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract Vehicle 2-4 interaction dataset')
    parser.add_argument('--points', type=int, default=200, 
                       help='Number of points to extract (default: 200)')
    parser.add_argument('--method', type=str, default='sequential',
                       choices=['sequential', 'uniform', 'all'],
                       help='Sampling method: sequential (first N), uniform (spread), or all (default: sequential)')
    parser.add_argument('--preset', type=str, choices=['200', '500', '1000', 'full'],
                       help='Use preset: 200, 500, 1000, or full dataset')
    
    args = parser.parse_args()
    
    # Handle presets
    if args.preset:
        if args.preset == '200':
            num_points, method = 200, 'sequential'
        elif args.preset == '500':
            num_points, method = 500, 'sequential'
        elif args.preset == '1000':
            num_points, method = 1000, 'sequential'
        elif args.preset == 'full':
            num_points, method = 999999, 'all'  # Large number to ensure all records
    else:
        num_points = args.points
        method = args.method
    
    print(f"\n🚀 Starting extraction with:")
    print(f"   Points: {num_points if method != 'all' else 'ALL'}")
    print(f"   Method: {method}\n")
    
    extract_vehicle_2_4_dataset(num_points, method)
