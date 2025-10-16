#!/usr/bin/env python3
"""
Extract first 200 points from Vehicle 2-4 closer points dataset
This creates a smaller, more manageable dataset for focused simulation
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

def extract_first_200_points():
    """Extract first 200 points from the closer Vehicle 2-4 dataset"""
    
    print("🔄 Extracting first 200 points from Vehicle 2-4 closer dataset...")
    
    # Read the closer points CSV
    input_file = "vehicle_2_4_closer_points.csv"
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found!")
        print("Please run extract_closer_vehicle_2_4_dataset.py first.")
        return False
    
    print(f"📋 Reading {input_file}...")
    df = pd.read_csv(input_file)
    print(f"✅ Loaded {len(df)} records")
    
    # Take first 200 points
    first_200_df = df.head(200).copy()
    
    print(f"📊 Selected first 200 points:")
    print(f"   - Records: {len(first_200_df)}")
    print(f"   - Date range: {first_200_df['timestamp'].min()} to {first_200_df['timestamp'].max()}")
    
    # Calculate distance statistics
    distances = first_200_df['distance'].values
    print(f"   - Distance range: {distances.min():.1f}m - {distances.max():.1f}m")
    print(f"   - Mean distance: {distances.mean():.1f}m")
    print(f"   - Median distance: {np.median(distances):.1f}m")
    
    # Save the filtered dataset
    output_file = "vehicle_2_4_first_200.csv"
    first_200_df.to_csv(output_file, index=False)
    print(f"💾 Saved first 200 points to {output_file}")
    
    # Create metadata
    metadata = {
        "dataset_name": "Vehicle 2-4 First 200 Points",
        "source_file": input_file,
        "extraction_date": datetime.now().isoformat(),
        "total_records": len(first_200_df),
        "date_range": {
            "start": float(first_200_df['timestamp'].min()),
            "end": float(first_200_df['timestamp'].max())
        },
        "coordinate_bounds": {
            "source_lat_min": float(first_200_df['Latitude_source'].min()),
            "source_lat_max": float(first_200_df['Latitude_source'].max()),
            "source_lon_min": float(first_200_df['Longitude_source'].min()),
            "source_lon_max": float(first_200_df['Longitude_source'].max()),
            "dest_lat_min": float(first_200_df['Latitude_destination'].min()),
            "dest_lat_max": float(first_200_df['Latitude_destination'].max()),
            "dest_lon_min": float(first_200_df['Longitude_destination'].min()),
            "dest_lon_max": float(first_200_df['Longitude_destination'].max())
        },
        "distance_statistics": {
            "min_distance": float(distances.min()),
            "max_distance": float(distances.max()),
            "mean_distance": float(distances.mean()),
            "median_distance": float(np.median(distances)),
            "std_distance": float(distances.std())
        },
        "scenarios": list(first_200_df['Scenario'].unique()),
        "description": "First 200 points from Vehicle 2-4 closer dataset for focused simulation"
    }
    
    # Save metadata
    metadata_file = "vehicle_2_4_first_200_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"📄 Saved metadata to {metadata_file}")
    
    # Display summary
    print("\n📊 Dataset Summary:")
    print(f"   📁 Output file: {output_file}")
    print(f"   📄 Metadata: {metadata_file}")
    print(f"   📍 Records: {len(first_200_df)}")
    print(f"   📏 Distance: {distances.min():.1f}m - {distances.max():.1f}m")
    print(f"   🎯 Mean distance: {distances.mean():.1f}m")
    print(f"   📅 Scenarios: {', '.join(metadata['scenarios'])}")
    
    return True

if __name__ == "__main__":
    extract_first_200_points()
