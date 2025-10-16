#!/usr/bin/env python3
"""
Simple Cellular CSV Analysis
Analyzes the converted cellular dataframe CSV to understand its structure and content.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

def main():
    """Main analysis function."""
    print("=" * 100)
    print("CELLULAR DATAFRAME CSV ANALYSIS")
    print("=" * 100)
    
    # Read the CSV file
    csv_file = "parsed_parquet.csv"
    
    try:
        df = pd.read_csv(csv_file)
        print(f"Successfully loaded {csv_file}")
        print(f"Total Records: {len(df):,}")
        print(f"Total Columns: {len(df.columns)}")
        
        # Basic information
        print(f"\nData Completeness: {((len(df) * len(df.columns) - df.isnull().sum().sum()) / (len(df) * len(df.columns))) * 100:.1f}%")
        
        # Column analysis
        print(f"\nColumn Categories:")
        
        # GPS and location columns
        gps_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['lat', 'lon', 'gps', 'location', 'coord', 'position'])]
        print(f"  GPS/Location: {gps_cols}")
        
        # Time columns
        time_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['time', 'date', 'timestamp', 'ts'])]
        print(f"  Time: {time_cols}")
        
        # Cellular network columns
        cellular_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['rsrp', 'rsrq', 'rssi', 'snr', 'mcs', 'cell', 'frequency', 'bandwidth'])]
        print(f"  Cellular Network: {len(cellular_cols)} columns")
        
        # Network performance columns
        network_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['datarate', 'jitter', 'ping', 'throughput', 'latency'])]
        print(f"  Network Performance: {network_cols}")
        
        # Vehicle telemetry columns
        vehicle_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['speed', 'cog', 'altitude', 'direction'])]
        print(f"  Vehicle Telemetry: {vehicle_cols}")
        
        # Weather columns
        weather_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['temperature', 'humidity', 'pressure', 'wind', 'precipitation', 'visibility'])]
        print(f"  Weather: {len(weather_cols)} columns")
        
        # Traffic columns
        traffic_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['jam', 'traffic', 'street', 'distance'])]
        print(f"  Traffic: {traffic_cols}")
        
        # Device information
        if 'device' in df.columns:
            device_counts = df['device'].value_counts()
            print(f"\nDevice Distribution:")
            for device, count in device_counts.items():
                print(f"  {device}: {count:,} records")
        
        # GPS coordinate analysis
        if 'lat' in df.columns and 'lon' in df.columns:
            lat_data = df['lat'].dropna()
            lon_data = df['lon'].dropna()
            if len(lat_data) > 0 and len(lon_data) > 0:
                print(f"\nGPS Coordinates:")
                print(f"  Latitude Range: {lat_data.min():.6f} to {lat_data.max():.6f}")
                print(f"  Longitude Range: {lon_data.min():.6f} to {lon_data.max():.6f}")
                print(f"  Valid GPS Points: {len(lat_data):,}")
                print(f"  GPS Completeness: {(len(lat_data) / len(df)) * 100:.1f}%")
        
        # Time range analysis
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                print(f"\nTime Range:")
                print(f"  Start: {df['timestamp'].min()}")
                print(f"  End: {df['timestamp'].max()}")
                print(f"  Duration: {df['timestamp'].max() - df['timestamp'].min()}")
            except:
                print(f"\nTime Range: Could not parse timestamps")
        
        # Sample data
        print(f"\nSample Data (first 3 rows):")
        sample_cols = ['device', 'lat', 'lon', 'timestamp', 'datarate', 'jitter'] if all(col in df.columns for col in ['device', 'lat', 'lon', 'timestamp', 'datarate', 'jitter']) else df.columns[:6]
        print(df[sample_cols].head(3).to_string())
        
        # Cellular metrics summary
        if cellular_cols:
            print(f"\nCellular Metrics Summary:")
            for col in cellular_cols[:5]:  # Show first 5 cellular columns
                if col in df.columns:
                    col_data = df[col].dropna()
                    if len(col_data) > 0 and pd.api.types.is_numeric_dtype(col_data):
                        print(f"  {col}: {col_data.mean():.3f} ± {col_data.std():.3f} (n={len(col_data):,})")
        
        # Network performance summary
        if network_cols:
            print(f"\nNetwork Performance Summary:")
            for col in network_cols:
                if col in df.columns:
                    col_data = df[col].dropna()
                    if len(col_data) > 0 and pd.api.types.is_numeric_dtype(col_data):
                        print(f"  {col}: {col_data.mean():.3f} ± {col_data.std():.3f} (n={len(col_data):,})")
        
        # SUMO visualization potential
        print(f"\nSUMO Visualization Potential:")
        has_gps = len(gps_cols) > 0
        has_timing = len(time_cols) > 0
        has_cellular = len(cellular_cols) > 0
        has_network = len(network_cols) > 0
        has_vehicle = len(vehicle_cols) > 0
        has_weather = len(weather_cols) > 0
        has_traffic = len(traffic_cols) > 0
        
        print(f"  Has GPS: {has_gps}")
        print(f"  Has Timing: {has_timing}")
        print(f"  Has Cellular Metrics: {has_cellular}")
        print(f"  Has Network Performance: {has_network}")
        print(f"  Has Vehicle Telemetry: {has_vehicle}")
        print(f"  Has Weather Data: {has_weather}")
        print(f"  Has Traffic Data: {has_traffic}")
        
        if has_gps and has_timing:
            print(f"  SUMO Feasibility: HIGH - GPS + timing available")
        elif has_gps:
            print(f"  SUMO Feasibility: MEDIUM - GPS available, no timing")
        else:
            print(f"  SUMO Feasibility: LOW - No GPS data")
        
        print("\n" + "=" * 100)
        print("ANALYSIS COMPLETE")
        print("=" * 100)
        
    except Exception as e:
        print(f"Error analyzing {csv_file}: {e}")

if __name__ == "__main__":
    main()
