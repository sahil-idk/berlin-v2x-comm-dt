#!/usr/bin/env python3
"""
Extract closer GPS points for Vehicle 2-4 interactions
Focus on same segment/area for better visualization
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime

def extract_closer_vehicle_2_4_dataset():
    """Extract Vehicle 2-4 interactions with closer GPS points"""
    
    print("🔍 Extracting Closer Vehicle 2-4 Interaction Dataset")
    print("=" * 55)
    
    # Load the full dataset
    print("📋 Loading sidelink dataset...")
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
    
    # Sort by timestamp to get chronological order
    vehicle_2_4_data = vehicle_2_4_data.sort_values('timestamp').reset_index(drop=True)
    
    # Find a cluster of closer points
    print("\n📍 Finding closer GPS point clusters...")
    
    # Calculate distances between consecutive points
    distances = []
    for i in range(len(vehicle_2_4_data) - 1):
        row1 = vehicle_2_4_data.iloc[i]
        row2 = vehicle_2_4_data.iloc[i + 1]
        
        # Calculate distance between consecutive GPS points
        lat1, lon1 = row1['Latitude_source'], row1['Longitude_source']
        lat2, lon2 = row2['Latitude_source'], row2['Longitude_source']
        
        # Simple distance calculation (approximate)
        dist = np.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111000  # Rough conversion to meters
        distances.append(dist)
    
    # Find clusters of points that are close together
    close_clusters = []
    current_cluster = [0]  # Start with first point
    
    for i, dist in enumerate(distances):
        if dist < 50:  # Points within 50 meters
            current_cluster.append(i + 1)
        else:
            if len(current_cluster) >= 5:  # At least 5 points in cluster
                close_clusters.append(current_cluster)
            current_cluster = [i + 1]
    
    # Add the last cluster if it's large enough
    if len(current_cluster) >= 5:
        close_clusters.append(current_cluster)
    
    print(f"✅ Found {len(close_clusters)} clusters of close points")
    
    if not close_clusters:
        print("⚠️  No close clusters found, using alternative method...")
        
        # Alternative: Find points with small inter-vehicle distances
        small_distance_data = vehicle_2_4_data[vehicle_2_4_data['distance'] < 20].copy()
        
        if len(small_distance_data) >= 10:
            # Take first 10-15 points with small distances
            focused_subset = small_distance_data.head(15)
            print(f"✅ Using {len(focused_subset)} points with small inter-vehicle distances")
        else:
            # Fallback: take first 10 points
            focused_subset = vehicle_2_4_data.head(10)
            print(f"✅ Using first {len(focused_subset)} points as fallback")
    else:
        # Use the largest cluster
        largest_cluster = max(close_clusters, key=len)
        focused_subset = vehicle_2_4_data.iloc[largest_cluster].copy()
        print(f"✅ Using largest cluster with {len(focused_subset)} points")
    
    # Analyze the focused subset
    print("\n📊 Focused Subset Analysis:")
    print(f"   Records: {len(focused_subset)}")
    print(f"   Time range: {focused_subset['timestamp'].min()} to {focused_subset['timestamp'].max()}")
    print(f"   Scenarios: {focused_subset['Scenario'].unique()}")
    
    # Calculate coordinate bounds for the focused subset
    all_lats = pd.concat([
        focused_subset['Latitude_source'],
        focused_subset['Latitude_destination']
    ])
    all_lons = pd.concat([
        focused_subset['Longitude_source'],
        focused_subset['Longitude_destination']
    ])
    
    bounds = {
        'min_lat': all_lats.min(),
        'max_lat': all_lats.max(),
        'min_lon': all_lons.min(),
        'max_lon': all_lons.max(),
        'center_lat': all_lats.mean(),
        'center_lon': all_lons.mean()
    }
    
    lat_range = bounds['max_lat'] - bounds['min_lat']
    lon_range = bounds['max_lon'] - bounds['min_lon']
    
    print(f"   Latitude range: {bounds['min_lat']:.6f} to {bounds['max_lat']:.6f}")
    print(f"   Longitude range: {bounds['min_lon']:.6f} to {bounds['max_lon']:.6f}")
    print(f"   Center: ({bounds['center_lat']:.6f}, {bounds['center_lon']:.6f})")
    print(f"   Coverage: {lat_range:.6f}° × {lon_range:.6f}°")
    
    # Distance analysis
    distances = focused_subset['distance'].values
    print(f"   Distance range: {distances.min():.1f}m to {distances.max():.1f}m")
    print(f"   Mean distance: {distances.mean():.1f}m")
    
    # Communication quality analysis
    if 'SNR' in focused_subset.columns:
        print(f"   SNR range: {focused_subset['SNR'].min():.1f} to {focused_subset['SNR'].max():.1f} dB")
    if 'RSRP' in focused_subset.columns:
        print(f"   RSRP range: {focused_subset['RSRP'].min():.1f} to {focused_subset['RSRP'].max():.1f} dBm")
    
    # Save the focused dataset
    output_file = 'vehicle_2_4_closer_points.csv'
    focused_subset.to_csv(output_file, index=False)
    print(f"\n💾 Saved closer points dataset: {output_file}")
    
    # Save metadata
    metadata = {
        'extraction_date': datetime.now().isoformat(),
        'total_records': len(df),
        'vehicle_2_4_records': len(vehicle_2_4_data),
        'focused_subset_size': len(focused_subset),
        'coordinate_bounds': bounds,
        'coverage_degrees': {
            'latitude': lat_range,
            'longitude': lon_range
        },
        'scenarios': focused_subset['Scenario'].unique().tolist(),
        'distance_range': {
            'min': float(distances.min()),
            'max': float(distances.max()),
            'mean': float(distances.mean())
        },
        'extraction_method': 'closer_points_clustering'
    }
    
    with open('vehicle_2_4_closer_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("💾 Saved metadata: vehicle_2_4_closer_metadata.json")
    
    # Display sample of the focused data
    print("\n📋 Sample of closer points dataset:")
    sample_cols = ['timestamp', 'Source', 'Destination', 'Latitude_source', 'Longitude_source', 
                   'Latitude_destination', 'Longitude_destination', 'distance', 'SNR', 'RSRP']
    print(focused_subset[sample_cols].head())
    
    return focused_subset, bounds

if __name__ == "__main__":
    extract_closer_vehicle_2_4_dataset()
