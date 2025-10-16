#!/usr/bin/env python3
"""
Simple GPS points extractor for SUMO simulation
"""

import pandas as pd
import numpy as np

def main():
    # Load sidelink data
    df = pd.read_csv('sidelink_parsed.csv')
    
    # Get unique GPS coordinates (both source and destination)
    source_coords = df[['Latitude_source', 'Longitude_source']].dropna()
    dest_coords = df[['Latitude_destination', 'Longitude_destination']].dropna()
    
    # Combine and deduplicate
    all_coords = pd.concat([
        source_coords.rename(columns={'Latitude_source': 'lat', 'Longitude_source': 'lon'}),
        dest_coords.rename(columns={'Latitude_destination': 'lat', 'Longitude_destination': 'lon'})
    ]).dropna().drop_duplicates()
    
    print(f'Total unique GPS points: {len(all_coords)}')
    print(f'Latitude range: {all_coords["lat"].min():.6f} to {all_coords["lat"].max():.6f}')
    print(f'Longitude range: {all_coords["lon"].min():.6f} to {all_coords["lon"].max():.6f}')
    
    # Sample 50 diverse points using spatial grid
    n_points = 50
    lat_min, lat_max = all_coords['lat'].min(), all_coords['lat'].max()
    lon_min, lon_max = all_coords['lon'].min(), all_coords['lon'].max()
    
    # Create grid and sample points
    selected_points = []
    grid_size = int(np.sqrt(n_points))
    lat_step = (lat_max - lat_min) / (grid_size - 1)
    lon_step = (lon_max - lon_min) / (grid_size - 1)
    
    for i in range(grid_size):
        for j in range(grid_size):
            if len(selected_points) >= n_points:
                break
            target_lat = lat_min + i * lat_step
            target_lon = lon_min + j * lon_step
            
            # Find closest point to grid center
            distances = np.sqrt((all_coords['lat'] - target_lat)**2 + (all_coords['lon'] - target_lon)**2)
            closest_idx = distances.idxmin()
            selected_points.append(all_coords.loc[closest_idx])
        
        if len(selected_points) >= n_points:
            break
    
    # Convert to DataFrame
    sampled_df = pd.DataFrame(selected_points[:n_points])
    sampled_df = sampled_df.reset_index(drop=True)
    
    print(f'\nSampled {len(sampled_df)} GPS points:')
    for idx, row in sampled_df.iterrows():
        print(f'{row["lat"]:.6f},{row["lon"]:.6f}')
    
    # Calculate bounds for SUMO
    center_lat = sampled_df['lat'].mean()
    center_lon = sampled_df['lon'].mean()
    
    # Calculate spread
    lat_spread = sampled_df['lat'].max() - sampled_df['lat'].min()
    lon_spread = sampled_df['lon'].max() - sampled_df['lon'].min()
    
    # Add buffer for SUMO road network (about 500m buffer)
    buffer_deg = 0.005  # ~500m in Berlin latitude
    bbox_min_lat = sampled_df['lat'].min() - buffer_deg
    bbox_max_lat = sampled_df['lat'].max() + buffer_deg
    bbox_min_lon = sampled_df['lon'].min() - buffer_deg
    bbox_max_lon = sampled_df['lon'].max() + buffer_deg
    
    print(f'\nSUMO Configuration Parameters:')
    print(f'Center Point: {center_lat:.6f}, {center_lon:.6f}')
    print(f'Data Points Area: {lat_spread*111000:.0f}m x {lon_spread*111000:.0f}m')
    print(f'SUMO Region bounds:')
    print(f'  SW: {bbox_min_lat:.6f}, {bbox_min_lon:.6f}')
    print(f'  NE: {bbox_max_lat:.6f}, {bbox_max_lon:.6f}')
    print(f'Region size: {(bbox_max_lat-bbox_min_lat)*111000:.0f}m x {(bbox_max_lon-bbox_min_lon)*111000:.0f}m')
    
    # Save to CSV
    sampled_df[['lat', 'lon']].to_csv('sumo_v2v_gps_points.csv', index=False)
    print(f'\nSaved to sumo_v2v_gps_points.csv')
    
    print(f'\nFor OSM Web Wizard:')
    print(f'Position: {center_lat:.6f}, {center_lon:.6f}')
    print(f'Use "Select Area" checkbox and manually draw region around the bounds')

if __name__ == "__main__":
    main()
