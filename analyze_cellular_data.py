#!/usr/bin/env python3
"""
Cellular Data Analysis Script
Analyzes the cellular dataframe parquet file to understand its structure and content.
"""

import pandas as pd
import os
import numpy as np
from datetime import datetime
import json

def analyze_cellular_dataframe(file_path):
    """Comprehensive analysis of the cellular dataframe."""
    try:
        # Read the parquet file
        df = pd.read_parquet(file_path)
        
        # Basic file information
        file_name = os.path.basename(file_path)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        analysis = {
            'file_name': file_name,
            'file_size_mb': file_size_mb,
            'total_records': len(df),
            'columns': list(df.columns),
            'column_count': len(df.columns),
            'data_types': df.dtypes.to_dict(),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
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
        
        # Signal quality analysis
        signal_cols = ['SNR', 'RSRP', 'RSSI', 'SINR', 'CQI', 'RSRQ', 'signal_strength', 'signal_quality']
        analysis['signal_quality'] = {}
        for col in signal_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    analysis['signal_quality'][col] = {
                        'count': len(col_data),
                        'mean': col_data.mean(),
                        'std': col_data.std(),
                        'min': col_data.min(),
                        'max': col_data.max(),
                        'median': col_data.median(),
                        'q25': col_data.quantile(0.25),
                        'q75': col_data.quantile(0.75)
                    }
        
        # Network parameters analysis
        network_cols = ['cell_id', 'tower_id', 'frequency', 'bandwidth', 'mcs', 'modulation', 'coding_rate']
        analysis['network_params'] = {}
        for col in network_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    analysis['network_params'][col] = {
                        'count': len(col_data),
                        'unique_values': col_data.nunique(),
                        'most_common': col_data.value_counts().head(5).to_dict(),
                        'mean': col_data.mean() if pd.api.types.is_numeric_dtype(col_data) else None,
                        'std': col_data.std() if pd.api.types.is_numeric_dtype(col_data) else None
                    }
        
        # Device analysis
        device_cols = ['device_id', 'imei', 'imsi', 'msisdn', 'ue_id', 'source', 'destination']
        analysis['device_info'] = {}
        for col in device_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    analysis['device_info'][col] = {
                        'count': len(col_data),
                        'unique_values': col_data.nunique(),
                        'most_common': col_data.value_counts().head(5).to_dict()
                    }
        
        # Data completeness
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        analysis['data_completeness'] = {
            'total_cells': total_cells,
            'null_cells': null_cells,
            'completeness_percentage': ((total_cells - null_cells) / total_cells) * 100
        }
        
        # Cellular-specific analysis
        analysis['cellular_analysis'] = {
            'has_gps': len(location_cols) > 0,
            'has_timing': len(time_cols) > 0,
            'has_signal_quality': len(analysis['signal_quality']) > 0,
            'has_network_params': len(analysis['network_params']) > 0,
            'has_device_info': len(analysis['device_info']) > 0,
            'potential_sumo_approaches': []
        }
        
        # Determine potential SUMO visualization approaches
        if analysis['cellular_analysis']['has_timing'] and analysis['cellular_analysis']['has_signal_quality']:
            analysis['cellular_analysis']['potential_sumo_approaches'].extend([
                'Cellular network coverage visualization',
                'Signal strength-based positioning',
                'Cell tower coverage mapping'
            ])
        
        if analysis['cellular_analysis']['has_gps']:
            analysis['cellular_analysis']['potential_sumo_approaches'].extend([
                'GPS-based vehicle tracking',
                'Location-based signal quality mapping',
                'Real-world cellular network simulation'
            ])
        
        if analysis['cellular_analysis']['has_network_params']:
            analysis['cellular_analysis']['potential_sumo_approaches'].extend([
                'Cell tower infrastructure visualization',
                'Network topology simulation',
                'Frequency and bandwidth analysis'
            ])
        
        return analysis
        
    except Exception as e:
        return {
            'file_name': os.path.basename(file_path),
            'error': str(e)
        }

def main():
    """Main analysis function."""
    print("=" * 80)
    print("CELLULAR DATAFRAME ANALYSIS")
    print("=" * 80)
    
    # Analyze cellular dataframe
    cellular_file = "cellular_dataframe (2).parquet"
    
    if not os.path.exists(cellular_file):
        print(f"Error: {cellular_file} not found!")
        return
    
    print(f"Analyzing {cellular_file}...")
    analysis = analyze_cellular_dataframe(cellular_file)
    
    if 'error' in analysis:
        print(f"ERROR analyzing {analysis['file_name']}: {analysis['error']}")
        return
    
    # Generate detailed report
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS RESULTS")
    print("=" * 80)
    
    print(f"\nFILE: {analysis['file_name']}")
    print("-" * 50)
    print(f"File Size: {analysis['file_size_mb']:.2f} MB")
    print(f"Total Records: {analysis['total_records']:,}")
    print(f"Columns: {analysis['column_count']}")
    print(f"Memory Usage: {analysis['memory_usage_mb']:.2f} MB")
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
    
    if analysis['signal_quality']:
        print(f"\nSignal Quality Metrics:")
        for metric, stats in analysis['signal_quality'].items():
            print(f"  {metric}:")
            print(f"    Count: {stats['count']:,}")
            print(f"    Mean: {stats['mean']:.3f} ± {stats['std']:.3f}")
            print(f"    Range: {stats['min']:.3f} to {stats['max']:.3f}")
            print(f"    Median: {stats['median']:.3f}")
    
    if analysis['network_params']:
        print(f"\nNetwork Parameters:")
        for param, stats in analysis['network_params'].items():
            print(f"  {param}:")
            print(f"    Count: {stats['count']:,}")
            print(f"    Unique Values: {stats['unique_values']}")
            if stats['mean'] is not None:
                print(f"    Mean: {stats['mean']:.3f} ± {stats['std']:.3f}")
            if 'most_common' in stats:
                print(f"    Most Common: {stats['most_common']}")
    
    if analysis['device_info']:
        print(f"\nDevice Information:")
        for info, stats in analysis['device_info'].items():
            print(f"  {info}:")
            print(f"    Count: {stats['count']:,}")
            print(f"    Unique Values: {stats['unique_values']}")
            if 'most_common' in stats:
                print(f"    Most Common: {stats['most_common']}")
    
    if analysis['cellular_analysis']:
        print(f"\nCellular Analysis:")
        print(f"  Has GPS: {analysis['cellular_analysis']['has_gps']}")
        print(f"  Has Timing: {analysis['cellular_analysis']['has_timing']}")
        print(f"  Has Signal Quality: {analysis['cellular_analysis']['has_signal_quality']}")
        print(f"  Has Network Params: {analysis['cellular_analysis']['has_network_params']}")
        print(f"  Has Device Info: {analysis['cellular_analysis']['has_device_info']}")
        print(f"  Potential SUMO Approaches: {analysis['cellular_analysis']['potential_sumo_approaches']}")
    
    if analysis['sample_data']:
        print(f"\nSample Data (first 5 rows):")
        for i, row in enumerate(analysis['sample_data'], 1):
            print(f"  Row {i}: {row}")
    
    # Save analysis to JSON
    analysis_file = "cellular_dataframe_analysis.json"
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"\nAnalysis saved to: {analysis_file}")
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
