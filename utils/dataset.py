#!/usr/bin/env python3
"""
Dataset utilities for digital twin V2V replay
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
from datetime import datetime

class DatasetProcessor:
    """Process dataset for digital twin replay"""
    
    def __init__(self, csv_path: str = "sidelink_parsed.csv"):
        self.csv_path = csv_path
        self.df = None
        
    def load_and_filter(self, source_id: int, destination_id: int) -> pd.DataFrame:
        """Load dataset and filter for specific vehicle IDs"""
        
        print(f"📋 Loading dataset from {self.csv_path}")
        
        # Load dataset in chunks to handle large files
        chunk_size = 10000
        chunks = []
        
        for chunk in pd.read_csv(self.csv_path, chunksize=chunk_size):
            # Filter for specific source and destination
            filtered_chunk = chunk[
                (chunk['Source'] == source_id) & 
                (chunk['Destination'] == destination_id)
            ]
            if not filtered_chunk.empty:
                chunks.append(filtered_chunk)
        
        if not chunks:
            raise ValueError(f"No data found for source_id={source_id}, destination_id={destination_id}")
        
        self.df = pd.concat(chunks, ignore_index=True)
        
        print(f"✅ Loaded {len(self.df)} records for source_id={source_id}, destination_id={destination_id}")
        
        # Clean data
        self._clean_data()
        
        return self.df
    
    def _clean_data(self):
        """Clean and validate dataset"""
        
        print("🧹 Cleaning dataset...")
        
        # Remove rows with missing GPS coordinates
        initial_count = len(self.df)
        self.df = self.df.dropna(subset=[
            'Latitude_source', 'Longitude_source',
            'Latitude_destination', 'Longitude_destination',
            'distance', 'timestamp'
        ])
        
        # Remove rows with invalid coordinates
        self.df = self.df[
            (self.df['Latitude_source'].between(-90, 90)) &
            (self.df['Longitude_source'].between(-180, 180)) &
            (self.df['Latitude_destination'].between(-90, 90)) &
            (self.df['Longitude_destination'].between(-180, 180))
        ]
        
        # Sort by timestamp
        self.df = self.df.sort_values('timestamp').reset_index(drop=True)
        
        # Remove duplicate timestamps
        self.df = self.df.drop_duplicates(subset=['timestamp']).reset_index(drop=True)
        
        cleaned_count = len(self.df)
        print(f"✅ Cleaned dataset: {initial_count} → {cleaned_count} records")
        
        if cleaned_count == 0:
            raise ValueError("No valid records remaining after cleaning")
    
    def select_evaluation_timestamps(self, n_timestamps: int, min_gap_seconds: float) -> List[int]:
        """Select N timestamps with minimum gap for evaluation"""
        
        if len(self.df) < n_timestamps:
            print(f"⚠️  Dataset has only {len(self.df)} records, using all")
            return list(range(len(self.df)))
        
        # Convert timestamps to seconds for gap calculation
        timestamps_sec = self.df['timestamp'].values
        
        selected_indices = []
        last_timestamp = -min_gap_seconds - 1  # Ensure first timestamp is selected
        
        for i, timestamp in enumerate(timestamps_sec):
            if timestamp - last_timestamp >= min_gap_seconds:
                selected_indices.append(i)
                last_timestamp = timestamp
                
                if len(selected_indices) >= n_timestamps:
                    break
        
        print(f"✅ Selected {len(selected_indices)} evaluation timestamps")
        print(f"   Time range: {timestamps_sec[selected_indices[0]]:.1f}s - {timestamps_sec[selected_indices[-1]]:.1f}s")
        
        return selected_indices
    
    def get_trajectory_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Get trajectory data for continuous replay"""
        
        return (
            self.df['timestamp'].values,
            self.df['Latitude_source'].values,
            self.df['Longitude_source'].values,
            self.df['Latitude_destination'].values,
            self.df['Longitude_destination'].values,
            self.df['distance'].values
        )
    
    def get_evaluation_data(self, indices: List[int]) -> pd.DataFrame:
        """Get data for evaluation timestamps"""
        
        return self.df.iloc[indices].copy()
    
    def interpolate_position(self, timestamp: float, 
                           lat_source: np.ndarray, lon_source: np.ndarray,
                           lat_dest: np.ndarray, lon_dest: np.ndarray,
                           timestamps: np.ndarray) -> Tuple[float, float, float, float]:
        """Interpolate vehicle positions for given timestamp"""
        
        # Find surrounding timestamps
        if timestamp <= timestamps[0]:
            return lat_source[0], lon_source[0], lat_dest[0], lon_dest[0]
        elif timestamp >= timestamps[-1]:
            return lat_source[-1], lon_source[-1], lat_dest[-1], lon_dest[-1]
        
        # Find indices for interpolation
        idx = np.searchsorted(timestamps, timestamp)
        t1, t2 = timestamps[idx-1], timestamps[idx]
        
        # Interpolate source position
        lat_src = lat_source[idx-1] + (lat_source[idx] - lat_source[idx-1]) * (timestamp - t1) / (t2 - t1)
        lon_src = lon_source[idx-1] + (lon_source[idx] - lon_source[idx-1]) * (timestamp - t1) / (t2 - t1)
        
        # Interpolate destination position
        lat_dst = lat_dest[idx-1] + (lat_dest[idx] - lat_dest[idx-1]) * (timestamp - t1) / (t2 - t1)
        lon_dst = lon_dest[idx-1] + (lon_dest[idx] - lon_dest[idx-1]) * (timestamp - t1) / (t2 - t1)
        
        return lat_src, lon_src, lat_dst, lon_dst
