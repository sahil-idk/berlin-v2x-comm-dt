#!/usr/bin/env python3
"""
Extract focused dataset for Vehicle 2 and Vehicle 4 interactions
Creates a small, relevant subset for visualization
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime

def extract_vehicle_2_4_dataset():
    """Extract and analyze Vehicle 2-4 interactions"""
    
    print("🔍 Extracting Vehicle 2-4 Interaction Dataset")
    print("=" * 50)
    
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
    
    # Sample a small subset for visualization (around 10-15 entries)
    print("\n📊 Creating focused subset...")
    
    # Sort by timestamp to get chronological order
    vehicle_2_4_data = vehicle_2_4_data.sort_values('timestamp').reset_index(drop=True)
    
    # Take every nth record to get a good spread
    subset_size = min(15, len(vehicle_2_4_data))
    step = max(1, len(vehicle_2_4_data) // subset_size)
    
    focused_subset = vehicle_2_4_data.iloc[::step].head(subset_size).copy()
    
    print(f"✅ Created focused subset with {len(focused_subset)} records")
    
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
    
    # Save the focused dataset
    output_file = 'vehicle_2_4_focused.csv'
    focused_subset.to_csv(output_file, index=False)
    print(f"\n💾 Saved focused dataset: {output_file}")
    
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
            'min': float(focused_subset['distance'].min()),
            'max': float(focused_subset['distance'].max()),
            'mean': float(focused_subset['distance'].mean())
        }
    }
    
    with open('vehicle_2_4_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("💾 Saved metadata: vehicle_2_4_metadata.json")
    
    # Display sample of the focused data
    print("\n📋 Sample of focused dataset:")
    print(focused_subset[['timestamp', 'Source', 'Destination', 'Latitude_source', 'Longitude_source', 
                         'Latitude_destination', 'Longitude_destination', 'distance', 'SNR', 'RSRP']].head())
    
    return focused_subset, bounds

if __name__ == "__main__":
    extract_vehicle_2_4_dataset()
