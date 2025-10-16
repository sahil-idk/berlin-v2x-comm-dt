#!/usr/bin/env python3
"""
Sidelink Dataframe Analysis Script
Analyzes the converted sidelink dataframe CSV to understand its structure and content.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

def main():
    """Main analysis function."""
    print("=" * 100)
    print("SIDELINK DATAFRAME CSV ANALYSIS")
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
        
        # V2V communication columns
        v2v_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['rsrp', 'rsrq', 'rssi', 'snr', 'mcs', 'signal', 'source', 'destination'])]
        print(f"  V2V Communication: {len(v2v_cols)} columns")
        
        # Network performance columns
        network_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['datarate', 'jitter', 'ping', 'throughput', 'latency', 'packet'])]
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
        if 'Source' in df.columns:
            source_counts = df['Source'].value_counts()
            print(f"\nSource Device Distribution:")
            for source, count in source_counts.head(10).items():
                print(f"  {source}: {count:,} records")
        
        if 'Destination' in df.columns:
            dest_counts = df['Destination'].value_counts()
            print(f"\nDestination Device Distribution:")
            for dest, count in dest_counts.head(10).items():
                print(f"  {dest}: {count:,} records")
        
        # Scenario information
        if 'Scenario' in df.columns:
            scenario_counts = df['Scenario'].value_counts()
            print(f"\nScenario Distribution:")
            for scenario, count in scenario_counts.items():
                print(f"  {scenario}: {count:,} records")
        
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
        sample_cols = ['Source', 'Destination', 'lat', 'lon', 'timestamp', 'SNR', 'RSRP', 'RSSI', 'MCS'] if all(col in df.columns for col in ['Source', 'Destination', 'lat', 'lon', 'timestamp', 'SNR', 'RSRP', 'RSSI', 'MCS']) else df.columns[:9]
        print(df[sample_cols].head(3).to_string())
        
        # V2V communication metrics summary
        v2v_metrics = ['SNR', 'RSRP', 'RSSI', 'MCS', 'NOISE POWER', 'RX_GAIN', 'Rx_power']
        print(f"\nV2V Communication Metrics Summary:")
        for col in v2v_metrics:
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
        
        # SubFrame analysis
        if 'SubFrame_NUMBER' in df.columns:
            subframe_data = df['SubFrame_NUMBER'].dropna()
            if len(subframe_data) > 0:
                print(f"\nSubFrame Analysis:")
                print(f"  SubFrame_NUMBER: {subframe_data.mean():.3f} ± {subframe_data.std():.3f} (n={len(subframe_data):,})")
                print(f"  Range: {subframe_data.min():.0f} to {subframe_data.max():.0f}")
        
        if 'SubFrame_LENGHT' in df.columns:
            subframe_len_data = df['SubFrame_LENGHT'].dropna()
            if len(subframe_len_data) > 0:
                print(f"  SubFrame_LENGHT: {subframe_len_data.mean():.3f} ± {subframe_len_data.std():.3f} (n={len(subframe_len_data):,})")
                print(f"  Range: {subframe_len_data.min():.0f} to {subframe_len_data.max():.0f}")
        
        # Packet analysis
        if 'Received Packets' in df.columns:
            packet_data = df['Received Packets'].dropna()
            if len(packet_data) > 0:
                print(f"\nPacket Analysis:")
                print(f"  Received Packets: {packet_data.mean():.3f} ± {packet_data.std():.3f} (n={len(packet_data):,})")
                print(f"  Range: {packet_data.min():.0f} to {packet_data.max():.0f}")
        
        # SUMO visualization potential
        print(f"\nSUMO Visualization Potential:")
        has_gps = len(gps_cols) > 0
        has_timing = len(time_cols) > 0
        has_v2v = len(v2v_cols) > 0
        has_network = len(network_cols) > 0
        has_vehicle = len(vehicle_cols) > 0
        has_weather = len(weather_cols) > 0
        has_traffic = len(traffic_cols) > 0
        
        print(f"  Has GPS: {has_gps}")
        print(f"  Has Timing: {has_timing}")
        print(f"  Has V2V Communication: {has_v2v}")
        print(f"  Has Network Performance: {has_network}")
        print(f"  Has Vehicle Telemetry: {has_vehicle}")
        print(f"  Has Weather Data: {has_weather}")
        print(f"  Has Traffic Data: {has_traffic}")
        
        if has_gps and has_timing and has_v2v:
            print(f"  SUMO Feasibility: HIGH - GPS + timing + V2V communication available")
        elif has_gps and has_v2v:
            print(f"  SUMO Feasibility: MEDIUM - GPS + V2V communication available")
        elif has_v2v:
            print(f"  SUMO Feasibility: MEDIUM - V2V communication available, no GPS")
        else:
            print(f"  SUMO Feasibility: LOW - Limited data for simulation")
        
        print("\n" + "=" * 100)
        print("ANALYSIS COMPLETE")
        print("=" * 100)
        
    except Exception as e:
        print(f"Error analyzing {csv_file}: {e}")

if __name__ == "__main__":
    main()
