#!/usr/bin/env python3
"""
GPS and Sidelink Dataset Merger Implementation
Implements the merger plan to combine GPS datasets with sidelink datasets
for comprehensive V2X analysis and SUMO visualization.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import json
from scipy.spatial.distance import cdist
from scipy.interpolate import interp1d
import warnings
warnings.filterwarnings('ignore')

class GPSSidelinkMerger:
    """Class to handle GPS and sidelink dataset merging."""
    
    def __init__(self):
        self.gps_data = {}
        self.sidelink_data = {}
        self.merged_data = {}
        self.device_mapping = {
            'pc2': 'ue2',
            'pc3': 'ue3', 
            'pc4': 'ue4'
        }
        
    def load_gps_data(self):
        """Load GPS datasets from root directory."""
        print("Loading GPS datasets...")
        
        gps_files = ['pc2 (1).parquet', 'pc3 (1).parquet', 'pc4 (1).parquet']
        
        for gps_file in gps_files:
            if os.path.exists(gps_file):
                try:
                    df = pd.read_parquet(gps_file)
                    device_id = gps_file.split(' ')[0]  # Extract pc2, pc3, pc4
                    
                    # Clean and prepare GPS data
                    df_clean = self.clean_gps_data(df, device_id)
                    self.gps_data[device_id] = df_clean
                    
                    print(f"  Loaded {gps_file}: {len(df_clean)} records")
                    
                except Exception as e:
                    print(f"  Error loading {gps_file}: {e}")
            else:
                print(f"  File not found: {gps_file}")
    
    def clean_gps_data(self, df, device_id):
        """Clean and prepare GPS data."""
        # Select relevant columns
        gps_cols = ['ts_gps', 'Latitude', 'Longitude', 'Altitude', 'speed_kmh', 'COG']
        weather_cols = ['temperature', 'humidity', 'pressure', 'windSpeed', 'precipIntensity']
        traffic_cols = ['Traffic Jam Factor', 'Traffic Street Name', 'Traffic Distance']
        
        # Check which columns exist
        available_cols = [col for col in gps_cols + weather_cols + traffic_cols if col in df.columns]
        df_clean = df[available_cols + ['measurement']].copy()
        
        # Add device identifier
        df_clean['device_id'] = device_id
        
        # Convert timestamp to datetime if it exists
        if 'ts_gps' in df_clean.columns:
            df_clean['ts_gps'] = pd.to_datetime(df_clean['ts_gps'])
            # Convert to Unix timestamp for correlation
            df_clean['timestamp_unix'] = df_clean['ts_gps'].astype('int64') // 10**9
        
        # Remove rows with missing GPS coordinates
        if 'Latitude' in df_clean.columns and 'Longitude' in df_clean.columns:
            df_clean = df_clean.dropna(subset=['Latitude', 'Longitude'])
        
        return df_clean
    
    def load_sidelink_data(self):
        """Load sidelink datasets."""
        print("Loading sidelink datasets...")
        
        sidelink_dir = Path("sidelink")
        if not sidelink_dir.exists():
            print("  Sidelink directory not found!")
            return
        
        sidelink_files = list(sidelink_dir.glob("*.parquet"))
        
        for sidelink_file in sorted(sidelink_files):
            try:
                df = pd.read_parquet(sidelink_file)
                
                # Extract UE ID from filename
                filename = sidelink_file.name
                if 'ue' in filename.lower():
                    parts = filename.replace('.parquet', '').split('_')
                    if len(parts) >= 3:
                        ue_id = parts[0]  # ue1, ue2, etc.
                        
                        # Clean and prepare sidelink data
                        df_clean = self.clean_sidelink_data(df, ue_id)
                        
                        if ue_id not in self.sidelink_data:
                            self.sidelink_data[ue_id] = []
                        self.sidelink_data[ue_id].append(df_clean)
                        
                        print(f"  Loaded {filename}: {len(df_clean)} records")
                
            except Exception as e:
                print(f"  Error loading {sidelink_file}: {e}")
    
    def clean_sidelink_data(self, df, ue_id):
        """Clean and prepare sidelink data."""
        # Select relevant columns
        comm_cols = ['SNR', 'RSRP', 'RSSI', 'MCS', 'NOISE POWER', 'RX_GAIN']
        time_cols = ['time_epoch', 'TIME(S)', 'TIME(FrS)']
        network_cols = ['Source', 'Destination', 'SubFrame_NUMBER', 'SubFrame_LENGHT', 'Rx_power']
        
        # Check which columns exist
        available_cols = [col for col in comm_cols + time_cols + network_cols if col in df.columns]
        df_clean = df[available_cols].copy()
        
        # Add UE identifier
        df_clean['ue_id'] = ue_id
        
        # Convert timestamp to datetime
        if 'time_epoch' in df_clean.columns:
            df_clean['timestamp_unix'] = df_clean['time_epoch'].astype('int64')
            df_clean['timestamp_datetime'] = pd.to_datetime(df_clean['time_epoch'], unit='s')
        
        # Remove rows with missing communication data
        if 'RSRP' in df_clean.columns:
            df_clean = df_clean.dropna(subset=['RSRP'])
        
        return df_clean
    
    def calculate_inter_vehicle_distances(self):
        """Calculate distances between vehicles using GPS coordinates."""
        print("Calculating inter-vehicle distances...")
        
        # Get GPS coordinates for each device
        gps_coords = {}
        for device_id, df in self.gps_data.items():
            if 'Latitude' in df.columns and 'Longitude' in df.columns:
                # Use median coordinates for each device
                lat = df['Latitude'].median()
                lon = df['Longitude'].median()
                gps_coords[device_id] = (lat, lon)
        
        # Calculate distances between all pairs
        distances = {}
        devices = list(gps_coords.keys())
        
        for i, device1 in enumerate(devices):
            for j, device2 in enumerate(devices[i+1:], i+1):
                coord1 = gps_coords[device1]
                coord2 = gps_coords[device2]
                
                # Calculate distance using Haversine formula
                distance = self.haversine_distance(coord1, coord2)
                distances[f"{device1}_{device2}"] = distance
                distances[f"{device2}_{device1}"] = distance  # Symmetric
                
                print(f"  Distance {device1} <-> {device2}: {distance:.2f} meters")
        
        return distances
    
    def haversine_distance(self, coord1, coord2):
        """Calculate distance between two GPS coordinates using Haversine formula."""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        # Earth's radius in meters
        r = 6371000
        return c * r
    
    def merge_datasets(self):
        """Merge GPS and sidelink datasets."""
        print("Merging datasets...")
        
        # Calculate inter-vehicle distances
        distances = self.calculate_inter_vehicle_distances()
        
        for gps_device, ue_device in self.device_mapping.items():
            if gps_device in self.gps_data and ue_device in self.sidelink_data:
                print(f"  Merging {gps_device} with {ue_device}...")
                
                # Get GPS data
                gps_df = self.gps_data[gps_device].copy()
                
                # Combine all sidelink data for this UE
                sidelink_dfs = self.sidelink_data[ue_device]
                sidelink_combined = pd.concat(sidelink_dfs, ignore_index=True)
                
                # Merge based on temporal correlation
                merged_df = self.temporal_merge(gps_df, sidelink_combined, gps_device, ue_device)
                
                # Add distance information
                merged_df = self.add_distance_info(merged_df, distances, gps_device)
                
                # Add path loss calculations
                merged_df = self.add_path_loss_calculations(merged_df)
                
                self.merged_data[f"{gps_device}_{ue_device}"] = merged_df
                
                print(f"    Merged dataset: {len(merged_df)} records")
    
    def temporal_merge(self, gps_df, sidelink_df, gps_device, ue_device):
        """Merge datasets based on temporal correlation."""
        if 'timestamp_unix' not in gps_df.columns or 'timestamp_unix' not in sidelink_df.columns:
            print(f"    Warning: No timestamps available for {gps_device} and {ue_device}")
            return pd.DataFrame()
        
        # Sort by timestamp
        gps_df = gps_df.sort_values('timestamp_unix')
        sidelink_df = sidelink_df.sort_values('timestamp_unix')
        
        # Find overlapping time range
        gps_start = gps_df['timestamp_unix'].min()
        gps_end = gps_df['timestamp_unix'].max()
        sidelink_start = sidelink_df['timestamp_unix'].min()
        sidelink_end = sidelink_df['timestamp_unix'].max()
        
        overlap_start = max(gps_start, sidelink_start)
        overlap_end = min(gps_end, sidelink_end)
        
        if overlap_start >= overlap_end:
            print(f"    Warning: No temporal overlap between {gps_device} and {ue_device}")
            return pd.DataFrame()
        
        # Filter to overlapping time range
        gps_filtered = gps_df[
            (gps_df['timestamp_unix'] >= overlap_start) & 
            (gps_df['timestamp_unix'] <= overlap_end)
        ].copy()
        
        sidelink_filtered = sidelink_df[
            (sidelink_df['timestamp_unix'] >= overlap_start) & 
            (sidelink_df['timestamp_unix'] <= overlap_end)
        ].copy()
        
        # Merge using temporal interpolation
        merged_df = self.interpolate_merge(gps_filtered, sidelink_filtered)
        
        return merged_df
    
    def interpolate_merge(self, gps_df, sidelink_df):
        """Merge datasets using temporal interpolation."""
        if len(gps_df) == 0 or len(sidelink_df) == 0:
            return pd.DataFrame()
        
        # Create a common time grid
        time_start = max(gps_df['timestamp_unix'].min(), sidelink_df['timestamp_unix'].min())
        time_end = min(gps_df['timestamp_unix'].max(), sidelink_df['timestamp_unix'].max())
        
        # Use sidelink timestamps as primary (higher frequency)
        common_times = sidelink_df['timestamp_unix'].values
        
        # Interpolate GPS data to common times
        gps_interpolated = {}
        for col in gps_df.columns:
            if col != 'timestamp_unix' and gps_df[col].dtype in ['float64', 'int64']:
                try:
                    # Remove NaN values for interpolation
                    valid_mask = ~gps_df[col].isna()
                    if valid_mask.sum() > 1:
                        interp_func = interp1d(
                            gps_df.loc[valid_mask, 'timestamp_unix'],
                            gps_df.loc[valid_mask, col],
                            kind='linear',
                            bounds_error=False,
                            fill_value='extrapolate'
                        )
                        gps_interpolated[col] = interp_func(common_times)
                    else:
                        gps_interpolated[col] = np.full(len(common_times), np.nan)
                except:
                    gps_interpolated[col] = np.full(len(common_times), np.nan)
        
        # Create merged dataframe
        merged_df = sidelink_df.copy()
        for col, values in gps_interpolated.items():
            merged_df[f"gps_{col}"] = values
        
        return merged_df
    
    def add_distance_info(self, merged_df, distances, gps_device):
        """Add inter-vehicle distance information."""
        if len(merged_df) == 0:
            return merged_df
        
        # Add distances to other vehicles
        for other_device in ['pc2', 'pc3', 'pc4']:
            if other_device != gps_device:
                distance_key = f"{gps_device}_{other_device}"
                if distance_key in distances:
                    merged_df[f"distance_to_{other_device}"] = distances[distance_key]
        
        return merged_df
    
    def add_path_loss_calculations(self, merged_df):
        """Add path loss model calculations."""
        if len(merged_df) == 0 or 'RSRP' not in merged_df.columns:
            return merged_df
        
        # Free space path loss model
        # PL = 20*log10(d) + 20*log10(f) + 20*log10(4*pi/c)
        # Where d is distance in meters, f is frequency in Hz, c is speed of light
        
        # Assume 5.9 GHz frequency for V2V communication
        frequency = 5.9e9  # 5.9 GHz
        c = 3e8  # Speed of light
        
        # Calculate path loss for each distance column
        for col in merged_df.columns:
            if col.startswith('distance_to_'):
                distance = merged_df[col]
                # Free space path loss
                path_loss = 20 * np.log10(distance) + 20 * np.log10(frequency) + 20 * np.log10(4 * np.pi / c)
                merged_df[f"path_loss_{col}"] = path_loss
                
                # Calculate expected RSRP based on path loss
                # Assume transmit power of 23 dBm (typical for V2V)
                tx_power = 23  # dBm
                expected_rsrp = tx_power - path_loss
                merged_df[f"expected_rsrp_{col}"] = expected_rsrp
        
        return merged_df
    
    def save_merged_data(self):
        """Save merged datasets."""
        print("Saving merged datasets...")
        
        output_dir = Path("merged_data")
        output_dir.mkdir(exist_ok=True)
        
        for merge_key, merged_df in self.merged_data.items():
            if len(merged_df) > 0:
                output_file = output_dir / f"{merge_key}_merged.parquet"
                merged_df.to_parquet(output_file, index=False)
                print(f"  Saved {output_file}: {len(merged_df)} records")
        
        # Create combined dataset
        if self.merged_data:
            combined_df = pd.concat(list(self.merged_data.values()), ignore_index=True)
            combined_file = output_dir / "combined_gps_sidelink.parquet"
            combined_df.to_parquet(combined_file, index=False)
            print(f"  Saved combined dataset: {combined_file}: {len(combined_df)} records")
            
            # Save metadata
            metadata = {
                'merge_timestamp': datetime.now().isoformat(),
                'device_mapping': self.device_mapping,
                'total_records': len(combined_df),
                'columns': list(combined_df.columns),
                'data_summary': {
                    'gps_records': len([df for df in self.gps_data.values()]),
                    'sidelink_records': sum(len(df) for dfs in self.sidelink_data.values() for df in dfs),
                    'merged_records': len(combined_df)
                }
            }
            
            metadata_file = output_dir / "merge_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"  Saved metadata: {metadata_file}")
    
    def generate_sumo_ready_data(self):
        """Generate SUMO-ready dataset."""
        print("Generating SUMO-ready data...")
        
        if not self.merged_data:
            print("  No merged data available!")
            return
        
        # Combine all merged data
        combined_df = pd.concat(list(self.merged_data.values()), ignore_index=True)
        
        if len(combined_df) == 0:
            print("  No data to process!")
            return
        
        # Create SUMO-ready format
        sumo_df = combined_df.copy()
        
        # Add vehicle ID based on device mapping
        sumo_df['vehicle_id'] = sumo_df['device_id'].map({
            'pc2': 'vehicle_2',
            'pc3': 'vehicle_3', 
            'pc4': 'vehicle_4'
        })
        
        # Add communication quality indicators
        if 'RSRP' in sumo_df.columns:
            sumo_df['communication_quality'] = pd.cut(
                sumo_df['RSRP'],
                bins=[-np.inf, -90, -80, -70, -60, np.inf],
                labels=['Poor', 'Fair', 'Good', 'Very Good', 'Excellent']
            )
        
        # Add distance-based communication indicators
        distance_cols = [col for col in sumo_df.columns if col.startswith('distance_to_')]
        if distance_cols:
            sumo_df['min_distance'] = sumo_df[distance_cols].min(axis=1)
            sumo_df['max_distance'] = sumo_df[distance_cols].max(axis=1)
            sumo_df['avg_distance'] = sumo_df[distance_cols].mean(axis=1)
        
        # Save SUMO-ready data
        output_dir = Path("merged_data")
        sumo_file = output_dir / "sumo_ready_gps_sidelink.parquet"
        sumo_df.to_parquet(sumo_file, index=False)
        print(f"  Saved SUMO-ready data: {sumo_file}: {len(sumo_df)} records")
        
        return sumo_df
    
    def run_merge(self):
        """Run the complete merge process."""
        print("=" * 80)
        print("GPS AND SIDELINK DATASET MERGER")
        print("=" * 80)
        
        # Load data
        self.load_gps_data()
        self.load_sidelink_data()
        
        # Merge datasets
        self.merge_datasets()
        
        # Save results
        self.save_merged_data()
        
        # Generate SUMO-ready data
        sumo_df = self.generate_sumo_ready_data()
        
        print("\n" + "=" * 80)
        print("MERGE COMPLETE")
        print("=" * 80)
        
        if sumo_df is not None and len(sumo_df) > 0:
            print(f"Total merged records: {len(sumo_df)}")
            print(f"Columns: {len(sumo_df.columns)}")
            print(f"Vehicles: {sumo_df['vehicle_id'].nunique()}")
            print(f"Time range: {sumo_df['timestamp_unix'].min()} to {sumo_df['timestamp_unix'].max()}")
            print(f"GPS coordinates available: {sumo_df['gps_Latitude'].notna().sum()} records")
            print(f"V2V communication data available: {sumo_df['RSRP'].notna().sum()} records")
        
        return sumo_df

def main():
    """Main function to run the merger."""
    merger = GPSSidelinkMerger()
    result = merger.run_merge()
    return result

if __name__ == "__main__":
    main()
