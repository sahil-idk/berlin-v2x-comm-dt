#!/usr/bin/env python3
"""
Create continuous datasets from the same GPS area as the working 200-point baseline
This ensures all datasets work with the same SUMO network region
"""

import pandas as pd
import json
from datetime import datetime

def create_continuous_datasets():
    """Create 300, 400, 500 point datasets from the same GPS region"""
    
    print("=" * 70)
    print("CREATING CONTINUOUS DATASETS FROM WORKING GPS REGION")
    print("=" * 70)
    
    # Load the full Vehicle 2-4 dataset
    print("\n📋 Loading full Vehicle 2-4 dataset...")
    df = pd.read_csv('sidelink_parsed.csv')
    
    # Filter for Vehicle 2-4
    vehicle_2_4_data = df[
        ((df['Source'] == 2) & (df['Destination'] == 4)) |
        ((df['Source'] == 4) & (df['Destination'] == 2))
    ].copy()
    
    vehicle_2_4_data = vehicle_2_4_data.sort_values('timestamp').reset_index(drop=True)
    
    print(f"✅ Total Vehicle 2-4 records: {len(vehicle_2_4_data)}")
    
    # Load the working 200-point baseline to understand the GPS region
    print("\n📍 Analyzing working 200-point baseline region...")
    df_200 = pd.read_csv('vehicle_2_4_first_200.csv')
    
    lat_min = df_200['Latitude_source'].min()
    lat_max = df_200['Latitude_source'].max()
    lon_min = df_200['Longitude_source'].min()
    lon_max = df_200['Longitude_source'].max()
    
    print(f"   Working region:")
    print(f"   Lat: {lat_min:.6f} to {lat_max:.6f}")
    print(f"   Lon: {lon_min:.6f} to {lon_max:.6f}")
    
    # Filter full dataset to same GPS region with some buffer
    lat_buffer = (lat_max - lat_min) * 0.1  # 10% buffer
    lon_buffer = (lon_max - lon_min) * 0.1
    
    print(f"\n📊 Filtering full dataset to working GPS region (with 10% buffer)...")
    region_data = vehicle_2_4_data[
        (vehicle_2_4_data['Latitude_source'] >= lat_min - lat_buffer) &
        (vehicle_2_4_data['Latitude_source'] <= lat_max + lat_buffer) &
        (vehicle_2_4_data['Longitude_source'] >= lon_min - lon_buffer) &
        (vehicle_2_4_data['Longitude_source'] <= lon_max + lon_buffer)
    ].copy()
    
    print(f"✅ Found {len(region_data)} records in working GPS region")
    
    if len(region_data) < 500:
        print(f"⚠️ Warning: Only {len(region_data)} records available in this region")
        max_points = len(region_data)
    else:
        max_points = 500
    
    # Create datasets of different sizes
    datasets_to_create = [
        (200, 'vehicle_2_4_continuous_200.csv'),
        (300, 'vehicle_2_4_continuous_300.csv'),
        (400, 'vehicle_2_4_continuous_400.csv'),
        (min(500, max_points), 'vehicle_2_4_continuous_500.csv'),
    ]
    
    print("\n" + "=" * 70)
    print("CREATING DATASETS")
    print("=" * 70)
    
    for num_points, filename in datasets_to_create:
        if num_points > len(region_data):
            print(f"\n⚠️ Skipping {filename}: Only {len(region_data)} records available")
            continue
        
        print(f"\n📦 Creating {filename} ({num_points} points)...")
        
        # Take first N points from the filtered region
        subset = region_data.head(num_points).copy()
        
        # Save dataset
        subset.to_csv(filename, index=False)
        
        # Create metadata
        metadata = {
            'extraction_date': datetime.now().isoformat(),
            'source': 'Continuous extraction from working GPS region',
            'num_records': len(subset),
            'gps_region': {
                'lat_min': float(subset['Latitude_source'].min()),
                'lat_max': float(subset['Latitude_source'].max()),
                'lon_min': float(subset['Longitude_source'].min()),
                'lon_max': float(subset['Longitude_source'].max())
            },
            'time_range': {
                'start': float(subset['timestamp'].min()),
                'end': float(subset['timestamp'].max())
            },
            'distance_stats': {
                'min': float(subset['distance'].min()),
                'max': float(subset['distance'].max()),
                'mean': float(subset['distance'].mean())
            },
            'snr_stats': {
                'min': float(subset['SNR'].min()),
                'max': float(subset['SNR'].max()),
                'mean': float(subset['SNR'].mean())
            }
        }
        
        metadata_file = filename.replace('.csv', '_metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Created {filename}")
        print(f"   Records: {len(subset)}")
        print(f"   Lat range: {metadata['gps_region']['lat_min']:.6f} to {metadata['gps_region']['lat_max']:.6f}")
        print(f"   Lon range: {metadata['gps_region']['lon_min']:.6f} to {metadata['gps_region']['lon_max']:.6f}")
        print(f"   Distance: {metadata['distance_stats']['min']:.1f}m to {metadata['distance_stats']['max']:.1f}m")
        print(f"   SNR: {metadata['snr_stats']['min']:.1f}dB to {metadata['snr_stats']['max']:.1f}dB")
        print(f"💾 Metadata: {metadata_file}")
    
    print("\n" + "=" * 70)
    print("DATASET CREATION COMPLETE")
    print("=" * 70)
    
    print("\n📊 Summary of Available Datasets:")
    print("\nContinuous (Same GPS Region - RECOMMENDED):")
    for num_points, filename in datasets_to_create:
        if num_points <= len(region_data):
            print(f"  ✅ {filename} - {num_points} points from working region")
    
    print("\nOriginal Extraction (Different GPS Regions - May Not Work):")
    print(f"  ⚠️ vehicle_2_4_500.csv - Different GPS area (52.513-52.515)")
    print(f"  ⚠️ vehicle_2_4_1000.csv - Different GPS area")
    
    print("\n💡 Recommendation:")
    print("   Use the 'continuous' datasets for scaling validation")
    print("   They're guaranteed to work with the same SUMO network region")
    
    print("\n🎯 Next Steps:")
    print("   1. Update GUI dropdown to include continuous datasets")
    print("   2. Test with vehicle_2_4_continuous_300.csv")
    print("   3. Test with vehicle_2_4_continuous_400.csv")
    print("   4. Test with vehicle_2_4_continuous_500.csv")
    
    return region_data

if __name__ == "__main__":
    create_continuous_datasets()

