#!/usr/bin/env python3
"""
Extract all vehicle pair scenarios from sidelink_parsed.csv
Creates individual CSV files for each unique vehicle pair scenario
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from collections import defaultdict

def normalize_pair(source, destination):
    """Normalize vehicle pair so (1,2) and (2,1) are treated as same scenario"""
    return tuple(sorted([int(source), int(destination)]))

def extract_all_scenarios():
    """Extract all vehicle pair scenarios and create individual CSV files"""
    
    print("🔍 Extracting All Vehicle Pair Scenarios")
    print("=" * 60)
    
    # Load the full dataset
    print("\n📋 Loading sidelink dataset...")
    df = pd.read_csv('sidelink_parsed.csv')
    print(f"✅ Loaded {len(df):,} total records")
    
    # Filter out rows without valid GPS coordinates
    print("\n🎯 Filtering valid GPS coordinates...")
    df = df.dropna(subset=['Latitude_source', 'Longitude_source', 
                           'Latitude_destination', 'Longitude_destination'])
    df = df[
        (df['Latitude_source'] != 0) & (df['Longitude_source'] != 0) &
        (df['Latitude_destination'] != 0) & (df['Longitude_destination'] != 0)
    ]
    print(f"✅ {len(df):,} records with valid GPS coordinates")
    
    # Filter out self-communication
    df = df[df['Source'] != df['Destination']]
    print(f"✅ {len(df):,} records after filtering self-communication")
    
    # Group by normalized vehicle pairs
    print("\n📊 Identifying unique vehicle pair scenarios...")
    scenarios = defaultdict(list)
    
    for idx, row in df.iterrows():
        source = row['Source']
        dest = row['Destination']
        pair = normalize_pair(source, dest)
        scenarios[pair].append(idx)
    
    print(f"✅ Found {len(scenarios)} unique vehicle pair scenarios")
    
    # Create scenarios directory
    scenarios_dir = 'scenarios'
    os.makedirs(scenarios_dir, exist_ok=True)
    
    # Create scenario metadata
    scenario_metadata = {}
    scenario_list = []
    
    # Extract and save each scenario
    print("\n💾 Extracting individual scenario CSV files...")
    for pair, indices in sorted(scenarios.items()):
        source_veh, dest_veh = pair
        scenario_name = f"vehicle_{source_veh}_{dest_veh}"
        
        # Get all records for this pair (including both directions)
        scenario_data = df.loc[indices].copy()
        
        # Sort by timestamp to maintain chronological order
        scenario_data = scenario_data.sort_values('timestamp').reset_index(drop=True)
        
        # Calculate metadata
        all_lats = pd.concat([
            scenario_data['Latitude_source'],
            scenario_data['Latitude_destination']
        ])
        all_lons = pd.concat([
            scenario_data['Longitude_source'],
            scenario_data['Longitude_destination']
        ])
        
        lat_range = all_lats.max() - all_lats.min()
        lon_range = all_lons.max() - all_lons.min()
        
        # Calculate distance statistics
        distances = scenario_data['distance'].dropna()
        
        metadata = {
            'scenario_name': scenario_name,
            'vehicle_pair': f"{source_veh}-{dest_veh}",
            'source_vehicle': int(source_veh),
            'destination_vehicle': int(dest_veh),
            'total_records': len(scenario_data),
            'coordinate_bounds': {
                'min_lat': float(all_lats.min()),
                'max_lat': float(all_lats.max()),
                'min_lon': float(all_lons.min()),
                'max_lon': float(all_lons.max()),
                'center_lat': float(all_lats.mean()),
                'center_lon': float(all_lons.mean())
            },
            'coverage_degrees': {
                'latitude': float(lat_range),
                'longitude': float(lon_range)
            },
            'distance_stats': {
                'min': float(distances.min()) if len(distances) > 0 else 0,
                'max': float(distances.max()) if len(distances) > 0 else 0,
                'mean': float(distances.mean()) if len(distances) > 0 else 0
            },
            'scenarios': scenario_data['Scenario'].unique().tolist() if 'Scenario' in scenario_data.columns else [],
            'snr_range': {
                'min': float(scenario_data['SNR'].min()) if 'SNR' in scenario_data.columns else 0,
                'max': float(scenario_data['SNR'].max()) if 'SNR' in scenario_data.columns else 0
            } if 'SNR' in scenario_data.columns else None
        }
        
        # Save CSV file
        csv_filename = os.path.join(scenarios_dir, f"{scenario_name}.csv")
        scenario_data.to_csv(csv_filename, index=False)
        
        # Save metadata
        metadata_filename = os.path.join(scenarios_dir, f"{scenario_name}_metadata.json")
        with open(metadata_filename, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        scenario_metadata[scenario_name] = metadata
        # Use forward slashes for web compatibility
        csv_file_web = csv_filename.replace('\\', '/')
        metadata_file_web = metadata_filename.replace('\\', '/')
        scenario_list.append({
            'name': scenario_name,
            'display_name': f"Vehicle {source_veh} ↔ Vehicle {dest_veh}",
            'csv_file': csv_file_web,
            'metadata_file': metadata_file_web,
            'record_count': len(scenario_data)
        })
        
        print(f"  ✅ {scenario_name}: {len(scenario_data):,} records")
    
    # Save master scenario list
    master_list_file = os.path.join(scenarios_dir, 'scenarios_list.json')
    with open(master_list_file, 'w') as f:
        json.dump({
            'extraction_date': datetime.now().isoformat(),
            'total_scenarios': len(scenario_list),
            'scenarios': scenario_list,
            'metadata': scenario_metadata
        }, f, indent=2)
    
    print(f"\n💾 Saved master scenario list: {master_list_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Total scenarios extracted: {len(scenario_list)}")
    print(f"Total records processed: {len(df):,}")
    print(f"\nScenarios:")
    for scenario in sorted(scenario_list, key=lambda x: x['record_count'], reverse=True):
        print(f"  • {scenario['display_name']}: {scenario['record_count']:,} records")
    
    return scenario_list, scenario_metadata

if __name__ == "__main__":
    extract_all_scenarios()

