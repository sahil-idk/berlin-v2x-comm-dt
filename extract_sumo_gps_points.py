#!/usr/bin/env python3
"""
Extract diverse GPS points from sidelink dataset for SUMO simulation
"""

import pandas as pd
import numpy as np
import random

def sample_diverse_points(df, n_points=50):
    """Sample diverse GPS points for SUMO simulation"""
    
    # Get all unique GPS points
    source_coords = df[['Latitude_source', 'Longitude_source']].dropna()
    dest_coords = df[['Latitude_destination', 'Longitude_destination']].dropna()
    
    # Combine coordinates
    all_coords = pd.concat([
        source_coords.rename(columns={'Latitude_source': 'lat', 'Longitude_source': 'lon'}),
        dest_coords.rename(columns={'Latitude_destination': 'lat', 'Longitude_destination': 'lon'})
    ]).dropna().drop_duplicates()
    
    print(f"Total unique GPS points available: {len(all_coords)}")
    
    # Sample diverse points using hexagonal distribution
    lat_range = all_coords['lat'].max() - all_coords['lat'].min()
    lon_range = all_coords['lon'].max() - all_coords['lon'].min()
    
    # Create a hexagonal grid for better spatial distribution
    n_cols = int(np.sqrt(n_points * 1.5))
    n_rows = int(n_points / n_cols) + 1
    
    lat_step = lat_range / (n_rows - 1)
    lon_step = lon_range / (n_cols - 1)
    
    selected_points = []
    
    for i in range(n_rows):
        for j in range(n_cols):
            # Calculate grid center
            target_lat = all_coords['lat'].min() + i * lat_step
            target_lon = all_coords['lon'].min() + j * lon_step
            
            # Find closest point to grid center
            distances = ((all_coords['lat'] - target_lat)**2 + (all_coords['lon'] - target_lon)**2)**0.5
            closest_idx = distances.idxmin()
            
            if closest_idx not in [p.index[0] for p in selected_points]:
                selected_points.append(all_coords.loc[closest_idx])
            
            if len(selected_points) >= n_points:
                break
        
        if len(selected_points) >= n_points:
            break
    
    # If we need more points, add random ones
    while len(selected_points) < n_points:
        selected_indices = set([p.index[0] for p in selected_points])
        remaining_indices = set(all_coords.index) - selected_indices
        if len(remaining_indices) > 0:
            random_idx = random.sample(list(remaining_indices), 1)
            selected_points.append(all_coords.loc[random_idx])
        else:
            break
    
    return pd.DataFrame(selected_points).head(n_points)

def main():
    """Main function"""
    
    # Load sidelink data
    df = pd.read_csv('sidelink_parsed.csv')
    
    # Sample 50 diverse points
    sampled_points = sample_diverse_points(df, 50)
    
    print(f"\nSelected {len(sampled_points)} diverse GPS points for SUMO simulation:")
    print("Index,Latitude,Longitude")
    for idx, row in sampled_points.iterrows():
        print(f"{idx},{row['lat']:.6f},{row['lon']:.6f}")
    
    # Calculate simulation area bounds
    sim_lat_min = sampled_points['lat'].min()
    sim_lat_max = sampled_points['lat'].max()
    sim_lon_min = sampled_points['lon'].min()
    sim_lon_max = sampled_points['lon'].max()
    
    sim_center_lat = (sim_lat_min + sim_lat_max) / 2
    sim_center_lon = (sim_lon_min + sim_lon_max) / 2
    
    # Add buffer for SUMO road network
    lat_buffer = (sim_lat_max - sim_lat_min) * 0.2  # 20% buffer
    lon_buffer = (sim_lon_max - sim_lon_min) * 0.2  # 20% buffer
    
    buffer_min_lat = sim_lat_min - lat_buffer
    buffer_max_lat = sim_lat_max + lat_buffer
    buffer_min_lon = sim_lon_min - lon_buffer
    buffer_max_lon = sim_lon_max + lon_buffer
    
    print(f"\nSUMO Simulation Area:")
    print(f"Center Point: {sim_center_lat:.6f}, {sim_center_lon:.6f}")
    print(f"\nData Points Bounds:")
    print(f"  SW Corner: {sim_lat_min:.6f}, {sim_lon_min:.6f}")
    print(f"  NE Corner: {sim_lat_max:.6f}, {sim_lon_max:.6f}")
    print(f"\nSUMO Region Bounds (with buffer):")
    print(f"  SW Corner: {buffer_min_lat:.6f}, {buffer_min_lon:.6f}")
    print(f"  NE Corner: {buffer_max_lat:.6f}, {buffer_max_lon:.6f}")
    
    # Calculate geographic spread
    lat_spread = sim_lat_max - sim_lat_min
    lon_spread = sim_lon_max - sim_lon_min
    
    print(f"\nGeographic Spread:")
    print(f"  Latitude: {lat_spread:.6f} degrees ({lat_spread * 111000:.1f} meters)")
    print(f"  Longitude: {lon_spread:.6f} degrees ({lon_spread * 111000:.1f} meters)")
    
    # Save points to file for SUMO simulation
    sampled_points[['lat', 'lon']].to_csv('sumo_gps_points.csv', index=False, header=True)
    print(f"\nSaved {len(sampled_points)} GPS points to 'sumo_gps_points.csv'")

if __name__ == "__main__":
    main()
