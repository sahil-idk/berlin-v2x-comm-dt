#!/usr/bin/env python3
"""
Cellular CSV Analysis Script
Analyzes the converted cellular dataframe CSV to understand its structure and content.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

def analyze_cellular_csv(file_path):
    """Comprehensive analysis of the cellular CSV file."""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Basic file information
        file_name = file_path
        total_records = len(df)
        
        analysis = {
            'file_name': file_name,
            'total_records': total_records,
            'columns': list(df.columns),
            'column_count': len(df.columns),
            'data_types': df.dtypes.to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'sample_data': df.head(5).to_dict('records') if len(df) > 0 else [],
        }
        
        # Time analysis
        time_cols = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['time', 'date', 'timestamp', 'ts']):
                time_cols.append(col)
        analysis['timestamp_columns'] = time_cols
        
        # Location analysis
        location_cols = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['lat', 'lon', 'gps', 'location', 'coord', 'position']):
                location_cols.append(col)
        analysis['location_columns'] = location_cols
        
        # Cellular network analysis
        cellular_cols = ['rsrp', 'rsrq', 'rssi', 'snr', 'mcs', 'cell', 'frequency', 'bandwidth']
        analysis['cellular_metrics'] = {}
        for col in cellular_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    analysis['cellular_metrics'][col] = {
                        'count': len(col_data),
                        'mean': col_data.mean(),
                        'std': col_data.std(),
                        'min': col_data.min(),
                        'max': col_data.max(),
                        'median': col_data.median(),
                        'q25': col_data.quantile(0.25),
                        'q75': col_data.quantile(0.75)
                    }
        
        # Network performance analysis
        network_cols = ['datarate', 'jitter', 'ping', 'throughput', 'latency']
        analysis['network_performance'] = {}
        for col in network_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    analysis['network_performance'][col] = {
                        'count': len(col_data),
                        'mean': col_data.mean(),
                        'std': col_data.std(),
                        'min': col_data.min(),
                        'max': col_data.max(),
                        'median': col_data.median()
                    }
        
        # Vehicle telemetry analysis
        vehicle_cols = ['speed', 'cog', 'altitude', 'direction']
        analysis['vehicle_telemetry'] = {}
        for col in vehicle_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    analysis['vehicle_telemetry'][col] = {
                        'count': len(col_data),
                        'mean': col_data.mean(),
                        'std': col_data.std(),
                        'min': col_data.min(),
                        'max': col_data.max(),
                        'median': col_data.median()
                    }
        
        # Weather analysis
        weather_cols = ['temperature', 'humidity', 'pressure', 'wind', 'precipitation', 'visibility']
        analysis['weather_data'] = {}
        for col in weather_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    analysis['weather_data'][col] = {
                        'count': len(col_data),
                        'mean': col_data.mean(),
                        'std': col_data.std(),
                        'min': col_data.min(),
                        'max': col_data.max(),
                        'median': col_data.median()
                    }
        
        # Traffic analysis
        traffic_cols = ['jam', 'traffic', 'street', 'distance']
        analysis['traffic_data'] = {}
        for col in traffic_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    if pd.api.types.is_numeric_dtype(col_data):
                        analysis['traffic_data'][col] = {
                            'count': len(col_data),
                            'mean': col_data.mean(),
                            'std': col_data.std(),
                            'min': col_data.min(),
                            'max': col_data.max(),
                            'median': col_data.median()
                        }
                    else:
                        analysis['traffic_data'][col] = {
                            'count': len(col_data),
                            'unique_values': col_data.nunique(),
                            'most_common': col_data.value_counts().head(5).to_dict()
                        }
        
        # Device analysis
        if 'device' in df.columns:
            device_data = df['device'].dropna()
            analysis['device_info'] = {
                'count': len(device_data),
                'unique_devices': device_data.nunique(),
                'device_distribution': device_data.value_counts().to_dict()
            }
        
        # Data completeness
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        analysis['data_completeness'] = {
            'total_cells': total_cells,
            'null_cells': null_cells,
            'completeness_percentage': ((total_cells - null_cells) / total_cells) * 100
        }
        
        # Time range analysis
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                analysis['time_range'] = {
                    'start_time': df['timestamp'].min(),
                    'end_time': df['timestamp'].max(),
                    'duration': df['timestamp'].max() - df['timestamp'].min(),
                    'total_measurements': len(df)
                }
            except:
                analysis['time_range'] = "Could not parse timestamps"
        
        # GPS coordinate analysis
        if 'lat' in df.columns and 'lon' in df.columns:
            lat_data = df['lat'].dropna()
            lon_data = df['lon'].dropna()
            if len(lat_data) > 0 and len(lon_data) > 0:
                analysis['gps_coordinates'] = {
                    'latitude_range': {'min': lat_data.min(), 'max': lat_data.max()},
                    'longitude_range': {'min': lon_data.min(), 'max': lon_data.max()},
                    'valid_gps_points': len(lat_data),
                    'gps_completeness': (len(lat_data) / len(df)) * 100
                }
        
        # Cellular-specific analysis
        analysis['cellular_analysis'] = {
            'has_gps': len(location_cols) > 0,
            'has_timing': len(time_cols) > 0,
            'has_cellular_metrics': len(analysis['cellular_metrics']) > 0,
            'has_network_performance': len(analysis['network_performance']) > 0,
            'has_vehicle_telemetry': len(analysis['vehicle_telemetry']) > 0,
            'has_weather_data': len(analysis['weather_data']) > 0,
            'has_traffic_data': len(analysis['traffic_data']) > 0,
            'potential_sumo_approaches': []
        }
        
        # Determine potential SUMO visualization approaches
        if analysis['cellular_analysis']['has_gps'] and analysis['cellular_analysis']['has_timing']:
            analysis['cellular_analysis']['potential_sumo_approaches'].extend([
                'Real-world vehicle tracking with GPS coordinates',
                'Cellular network coverage visualization',
                'Signal strength-based positioning',
                'Weather impact on communication simulation'
            ])
        
        if analysis['cellular_analysis']['has_vehicle_telemetry']:
            analysis['cellular_analysis']['potential_sumo_approaches'].extend([
                'Vehicle speed and direction simulation',
                'Traffic condition impact analysis',
                'Environmental factor correlation'
            ])
        
        if analysis['cellular_analysis']['has_cellular_metrics']:
            analysis['cellular_analysis']['potential_sumo_approaches'].extend([
                'Cellular signal quality visualization',
                'Network performance mapping',
                'Communication quality analysis'
            ])
        
        return analysis
        
    except Exception as e:
        return {
            'file_name': file_path,
            'error': str(e)
        }

def main():
    """Main analysis function."""
    print("=" * 100)
    print("CELLULAR DATAFRAME CSV ANALYSIS")
    print("=" * 100)
    
    # Analyze cellular CSV
    csv_file = "parsed_parquet.csv"
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        return
    
    print(f"Analyzing {csv_file}...")
    analysis = analyze_cellular_csv(csv_file)
    
    if 'error' in analysis:
        print(f"ERROR analyzing {analysis['file_name']}: {analysis['error']}")
        return
    
    # Generate detailed report
    print("\n" + "=" * 100)
    print("DETAILED ANALYSIS RESULTS")
    print("=" * 100)
    
    print(f"\nFILE: {analysis['file_name']}")
    print("-" * 80)
    print(f"Total Records: {analysis['total_records']:,}")
    print(f"Columns: {analysis['column_count']}")
    print(f"Data Completeness: {analysis['data_completeness']['completeness_percentage']:.1f}%")
    
    if analysis['timestamp_columns']:
        print(f"\nTimestamp Columns: {', '.join(analysis['timestamp_columns'])}")
    
    if analysis['location_columns']:
        print(f"Location Columns: {', '.join(analysis['location_columns'])}")
    
    print(f"\nColumns ({analysis['column_count']}):")
    for i, col in enumerate(analysis['columns'], 1):
        dtype = analysis['data_types'][col]
        null_count = analysis['null_counts'][col]
        print(f"  {i:2d}. {col:<30} {str(dtype):<15} (nulls: {null_count})")
    
    if analysis['cellular_metrics']:
        print(f"\nCellular Network Metrics:")
        for metric, stats in analysis['cellular_metrics'].items():
            print(f"  {metric}:")
            print(f"    Count: {stats['count']:,}")
            print(f"    Mean: {stats['mean']:.3f} ± {stats['std']:.3f}")
            print(f"    Range: {stats['min']:.3f} to {stats['max']:.3f}")
            print(f"    Median: {stats['median']:.3f}")
    
    if analysis['network_performance']:
        print(f"\nNetwork Performance:")
        for metric, stats in analysis['network_performance'].items():
            print(f"  {metric}:")
            print(f"    Count: {stats['count']:,}")
            print(f"    Mean: {stats['mean']:.3f} ± {stats['std']:.3f}")
            print(f"    Range: {stats['min']:.3f} to {stats['max']:.3f}")
            print(f"    Median: {stats['median']:.3f}")
    
    if analysis['vehicle_telemetry']:
        print(f"\nVehicle Telemetry:")
        for metric, stats in analysis['vehicle_telemetry'].items():
            print(f"  {metric}:")
            print(f"    Count: {stats['count']:,}")
            print(f"    Mean: {stats['mean']:.3f} ± {stats['std']:.3f}")
            print(f"    Range: {stats['min']:.3f} to {stats['max']:.3f}")
            print(f"    Median: {stats['median']:.3f}")
    
    if analysis['weather_data']:
        print(f"\nWeather Data:")
        for metric, stats in analysis['weather_data'].items():
            print(f"  {metric}:")
            print(f"    Count: {stats['count']:,}")
            print(f"    Mean: {stats['mean']:.3f} ± {stats['std']:.3f}")
            print(f"    Range: {stats['min']:.3f} to {stats['max']:.3f}")
            print(f"    Median: {stats['median']:.3f}")
    
    if analysis['traffic_data']:
        print(f"\nTraffic Data:")
        for metric, stats in analysis['traffic_data'].items():
            print(f"  {metric}:")
            print(f"    Count: {stats['count']:,}")
            if 'mean' in stats:
                print(f"    Mean: {stats['mean']:.3f} ± {stats['std']:.3f}")
                print(f"    Range: {stats['min']:.3f} to {stats['max']:.3f}")
            else:
                print(f"    Unique Values: {stats['unique_values']}")
                if 'most_common' in stats:
                    print(f"    Most Common: {stats['most_common']}")
    
    if 'device_info' in analysis:
        print(f"\nDevice Information:")
        print(f"  Total Devices: {analysis['device_info']['unique_devices']}")
        print(f"  Device Distribution: {analysis['device_info']['device_distribution']}")
    
    if 'time_range' in analysis and isinstance(analysis['time_range'], dict):
        print(f"\nTime Range:")
        print(f"  Start: {analysis['time_range']['start_time']}")
        print(f"  End: {analysis['time_range']['end_time']}")
        print(f"  Duration: {analysis['time_range']['duration']}")
        print(f"  Total Measurements: {analysis['time_range']['total_measurements']:,}")
    
    if 'gps_coordinates' in analysis:
        print(f"\nGPS Coordinates:")
        print(f"  Latitude Range: {analysis['gps_coordinates']['latitude_range']['min']:.6f} to {analysis['gps_coordinates']['latitude_range']['max']:.6f}")
        print(f"  Longitude Range: {analysis['gps_coordinates']['longitude_range']['min']:.6f} to {analysis['gps_coordinates']['longitude_range']['max']:.6f}")
        print(f"  Valid GPS Points: {analysis['gps_coordinates']['valid_gps_points']:,}")
        print(f"  GPS Completeness: {analysis['gps_coordinates']['gps_completeness']:.1f}%")
    
    if analysis['cellular_analysis']:
        print(f"\nCellular Analysis:")
        print(f"  Has GPS: {analysis['cellular_analysis']['has_gps']}")
        print(f"  Has Timing: {analysis['cellular_analysis']['has_timing']}")
        print(f"  Has Cellular Metrics: {analysis['cellular_analysis']['has_cellular_metrics']}")
        print(f"  Has Network Performance: {analysis['cellular_analysis']['has_network_performance']}")
        print(f"  Has Vehicle Telemetry: {analysis['cellular_analysis']['has_vehicle_telemetry']}")
        print(f"  Has Weather Data: {analysis['cellular_analysis']['has_weather_data']}")
        print(f"  Has Traffic Data: {analysis['cellular_analysis']['has_traffic_data']}")
        print(f"  Potential SUMO Approaches: {analysis['cellular_analysis']['potential_sumo_approaches']}")
    
    if analysis['sample_data']:
        print(f"\nSample Data (first 5 rows):")
        for i, row in enumerate(analysis['sample_data'], 1):
            print(f"  Row {i}: {row}")
    
    # Save analysis to JSON
    analysis_file = "cellular_csv_analysis.json"
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"\nAnalysis saved to: {analysis_file}")
    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    import os
    main()
