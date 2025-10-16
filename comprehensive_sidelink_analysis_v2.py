#!/usr/bin/env python3
"""
Comprehensive Sidelink Data Analysis Script v2
Analyzes all parquet files in the sidelink directory to understand their structure, 
similarities, differences, and potential for SUMO visualization without GPS data.
"""

import pandas as pd
import os
import glob
from pathlib import Path
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_parquet_file_comprehensive(file_path):
    """Comprehensive analysis of a single parquet file."""
    try:
        # Read the parquet file
        df = pd.read_parquet(file_path)
        
        # Basic file information
        file_name = os.path.basename(file_path)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # Extract date and UE info from filename
        parts = file_name.replace('.parquet', '').split('_')
        ue_id = parts[0] if len(parts) > 0 else 'unknown'
        session_id = parts[1] if len(parts) > 1 else 'unknown'
        date_str = parts[2] if len(parts) > 2 else 'unknown'
        
        analysis = {
            'file_name': file_name,
            'file_size_mb': file_size_mb,
            'ue_id': ue_id,
            'session_id': session_id,
            'date': date_str,
            'total_records': len(df),
            'columns': list(df.columns),
            'column_count': len(df.columns),
            'data_types': df.dtypes.to_dict(),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'null_counts': df.isnull().sum().to_dict(),
            'sample_data': df.head(5).to_dict('records') if len(df) > 0 else [],
        }
        
        # Time analysis
        if 'time_epoch' in df.columns:
            time_data = df['time_epoch'].dropna()
            if len(time_data) > 0:
                analysis['time_range'] = {
                    'start': datetime.fromtimestamp(time_data.min()),
                    'end': datetime.fromtimestamp(time_data.max()),
                    'duration_hours': (time_data.max() - time_data.min()) / 3600,
                    'start_epoch': time_data.min(),
                    'end_epoch': time_data.max()
                }
        
        # Signal quality analysis
        signal_cols = ['SNR', 'RSRP', 'RSSI', 'NOISE POWER', 'Rx_power']
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
        
        # Communication parameters
        comm_cols = ['MCS', 'SubFrame_NUMBER', 'SubFrame_LENGHT', 'RX_GAIN']
        analysis['communication_params'] = {}
        for col in comm_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    analysis['communication_params'][col] = {
                        'count': len(col_data),
                        'mean': col_data.mean(),
                        'std': col_data.std(),
                        'min': col_data.min(),
                        'max': col_data.max(),
                        'unique_values': col_data.nunique(),
                        'most_common': col_data.value_counts().head(5).to_dict()
                    }
        
        # Device analysis
        if 'Source' in df.columns:
            source_data = df['Source'].dropna()
            analysis['device_analysis'] = {
                'unique_sources': source_data.nunique(),
                'source_distribution': source_data.value_counts().to_dict(),
                'total_measurements': len(source_data)
            }
        
        if 'Destination' in df.columns:
            dest_data = df['Destination'].dropna()
            analysis['destination_analysis'] = {
                'unique_destinations': dest_data.nunique(),
                'destination_distribution': dest_data.value_counts().to_dict()
            }
        
        # Data completeness
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        analysis['data_completeness'] = {
            'total_cells': total_cells,
            'null_cells': null_cells,
            'completeness_percentage': ((total_cells - null_cells) / total_cells) * 100
        }
        
        # Communication pattern analysis
        if 'time_epoch' in df.columns and 'Source' in df.columns:
            time_source_data = df[['time_epoch', 'Source']].dropna()
            if len(time_source_data) > 0:
                # Group by source and analyze communication patterns
                source_patterns = {}
                for source in time_source_data['Source'].unique():
                    source_data = time_source_data[time_source_data['Source'] == source]
                    if len(source_data) > 1:
                        time_diffs = source_data['time_epoch'].diff().dropna()
                        source_patterns[source] = {
                            'message_count': len(source_data),
                            'avg_interval': time_diffs.mean(),
                            'min_interval': time_diffs.min(),
                            'max_interval': time_diffs.max(),
                            'std_interval': time_diffs.std()
                        }
                analysis['communication_patterns'] = source_patterns
        
        # SUMO visualization potential analysis
        analysis['sumo_potential'] = {
            'has_gps': False,
            'has_timing': 'time_epoch' in df.columns,
            'has_sources': 'Source' in df.columns,
            'has_signal_quality': any(col in df.columns for col in signal_cols),
            'potential_approaches': []
        }
        
        # Determine potential SUMO visualization approaches
        if analysis['sumo_potential']['has_timing'] and analysis['sumo_potential']['has_sources']:
            analysis['sumo_potential']['potential_approaches'].extend([
                'Communication-based vehicle positioning',
                'Signal strength-based distance estimation',
                'Timing-based vehicle movement simulation'
            ])
        
        if analysis['sumo_potential']['has_signal_quality']:
            analysis['sumo_potential']['potential_approaches'].extend([
                'Signal quality-based network visualization',
                'Communication range estimation',
                'Interference pattern visualization'
            ])
        
        return analysis
        
    except Exception as e:
        return {
            'file_name': os.path.basename(file_path),
            'error': str(e)
        }

def generate_sumo_visualization_strategies(analyses):
    """Generate strategies for SUMO visualization without GPS data."""
    valid_analyses = [a for a in analyses if 'error' not in a]
    
    strategies = {
        'communication_based_positioning': {
            'description': 'Use communication patterns to estimate vehicle positions',
            'approach': 'Map Source devices to virtual vehicles in SUMO',
            'requirements': ['Source', 'time_epoch', 'signal_quality'],
            'feasibility': 'High',
            'implementation': 'Create virtual vehicles for each Source device'
        },
        'signal_strength_distance_estimation': {
            'description': 'Estimate distances between vehicles using signal strength',
            'approach': 'Use RSRP/RSSI values to calculate approximate distances',
            'requirements': ['RSRP', 'RSSI', 'Source'],
            'feasibility': 'Medium',
            'implementation': 'Apply path loss models to estimate distances'
        },
        'timing_based_movement': {
            'description': 'Simulate vehicle movement based on communication timing',
            'approach': 'Use communication intervals to simulate vehicle behavior',
            'requirements': ['time_epoch', 'Source', 'communication_patterns'],
            'feasibility': 'Medium',
            'implementation': 'Map communication frequency to vehicle speed'
        },
        'network_topology_visualization': {
            'description': 'Visualize communication network topology',
            'approach': 'Show communication links between devices',
            'requirements': ['Source', 'Destination', 'signal_quality'],
            'feasibility': 'High',
            'implementation': 'Create network graph with communication links'
        },
        'signal_quality_heatmap': {
            'description': 'Create heatmap of signal quality over time',
            'approach': 'Visualize signal quality variations',
            'requirements': ['SNR', 'RSRP', 'RSSI', 'time_epoch'],
            'feasibility': 'High',
            'implementation': 'Create time-series visualization of signal metrics'
        }
    }
    
    return strategies

def main():
    """Main analysis function."""
    print("=" * 100)
    print("COMPREHENSIVE SIDELINK DATASET ANALYSIS v2")
    print("=" * 100)
    
    # Find all parquet files in sidelink directory
    sidelink_dir = Path("sidelink")
    if not sidelink_dir.exists():
        print("Error: sidelink directory not found!")
        return
    
    parquet_files = list(sidelink_dir.glob("*.parquet"))
    
    if not parquet_files:
        print("No parquet files found in sidelink directory!")
        return
    
    print(f"Found {len(parquet_files)} parquet files:")
    for file in sorted(parquet_files):
        print(f"  - {file.name}")
    print()
    
    # Analyze each file
    all_analyses = []
    for file_path in sorted(parquet_files):
        print(f"Analyzing {file_path.name}...")
        analysis = analyze_parquet_file_comprehensive(file_path)
        all_analyses.append(analysis)
    
    # Generate comprehensive report
    print("\n" + "=" * 100)
    print("DETAILED ANALYSIS RESULTS")
    print("=" * 100)
    
    for analysis in all_analyses:
        if 'error' in analysis:
            print(f"\nERROR analyzing {analysis['file_name']}: {analysis['error']}")
            continue
            
        print(f"\nFILE: {analysis['file_name']}")
        print("-" * 80)
        print(f"UE ID: {analysis['ue_id']}")
        print(f"Session ID: {analysis['session_id']}")
        print(f"Date: {analysis['date']}")
        print(f"File Size: {analysis['file_size_mb']:.2f} MB")
        print(f"Total Records: {analysis['total_records']:,}")
        print(f"Columns: {analysis['column_count']}")
        print(f"Memory Usage: {analysis['memory_usage_mb']:.2f} MB")
        print(f"Data Completeness: {analysis['data_completeness']['completeness_percentage']:.1f}%")
        
        if 'time_range' in analysis:
            print(f"\nTime Range:")
            print(f"  Start: {analysis['time_range']['start']}")
            print(f"  End: {analysis['time_range']['end']}")
            print(f"  Duration: {analysis['time_range']['duration_hours']:.2f} hours")
        
        if 'signal_quality' in analysis:
            print(f"\nSignal Quality Metrics:")
            for metric, stats in analysis['signal_quality'].items():
                print(f"  {metric}:")
                print(f"    Count: {stats['count']:,}")
                print(f"    Mean: {stats['mean']:.3f} ± {stats['std']:.3f}")
                print(f"    Range: {stats['min']:.3f} to {stats['max']:.3f}")
                print(f"    Median: {stats['median']:.3f}")
        
        if 'communication_params' in analysis:
            print(f"\nCommunication Parameters:")
            for param, stats in analysis['communication_params'].items():
                print(f"  {param}:")
                print(f"    Count: {stats['count']:,}")
                print(f"    Mean: {stats['mean']:.3f}")
                print(f"    Unique Values: {stats['unique_values']}")
                if 'most_common' in stats:
                    print(f"    Most Common: {stats['most_common']}")
        
        if 'device_analysis' in analysis:
            print(f"\nDevice Analysis:")
            print(f"  Unique Sources: {analysis['device_analysis']['unique_sources']}")
            print(f"  Source Distribution: {analysis['device_analysis']['source_distribution']}")
            print(f"  Total Measurements: {analysis['device_analysis']['total_measurements']:,}")
        
        if 'communication_patterns' in analysis:
            print(f"\nCommunication Patterns:")
            for source, pattern in analysis['communication_patterns'].items():
                print(f"  {source}:")
                print(f"    Messages: {pattern['message_count']:,}")
                print(f"    Avg Interval: {pattern['avg_interval']:.3f}s")
                print(f"    Interval Range: {pattern['min_interval']:.3f}s to {pattern['max_interval']:.3f}s")
        
        if 'sumo_potential' in analysis:
            print(f"\nSUMO Visualization Potential:")
            print(f"  Has GPS: {analysis['sumo_potential']['has_gps']}")
            print(f"  Has Timing: {analysis['sumo_potential']['has_timing']}")
            print(f"  Has Sources: {analysis['sumo_potential']['has_sources']}")
            print(f"  Has Signal Quality: {analysis['sumo_potential']['has_signal_quality']}")
            print(f"  Potential Approaches: {analysis['sumo_potential']['potential_approaches']}")
    
    # SUMO Visualization Strategies
    print("\n" + "=" * 100)
    print("SUMO VISUALIZATION STRATEGIES")
    print("=" * 100)
    
    strategies = generate_sumo_visualization_strategies(all_analyses)
    
    for strategy_name, strategy_info in strategies.items():
        print(f"\n{strategy_name.upper().replace('_', ' ')}:")
        print(f"  Description: {strategy_info['description']}")
        print(f"  Approach: {strategy_info['approach']}")
        print(f"  Requirements: {strategy_info['requirements']}")
        print(f"  Feasibility: {strategy_info['feasibility']}")
        print(f"  Implementation: {strategy_info['implementation']}")
    
    # Summary analysis
    print("\n" + "=" * 100)
    print("SUMMARY ANALYSIS")
    print("=" * 100)
    
    valid_analyses = [a for a in all_analyses if 'error' not in a]
    
    total_records = sum(a.get('total_records', 0) for a in valid_analyses)
    total_size = sum(a.get('file_size_mb', 0) for a in valid_analyses)
    
    print(f"Total Files Analyzed: {len(valid_analyses)}")
    print(f"Total Records: {total_records:,}")
    print(f"Total Size: {total_size:.2f} MB")
    
    # Find common columns across files
    all_columns = set()
    for analysis in valid_analyses:
        all_columns.update(analysis['columns'])
    
    print(f"Unique Columns Across All Files: {len(all_columns)}")
    print("All Columns:")
    for col in sorted(all_columns):
        print(f"  - {col}")
    
    # SUMO feasibility assessment
    print(f"\nSUMO Visualization Feasibility:")
    sumo_ready_files = 0
    for analysis in valid_analyses:
        if analysis.get('sumo_potential', {}).get('has_timing', False) and \
           analysis.get('sumo_potential', {}).get('has_sources', False):
            sumo_ready_files += 1
    
    print(f"  Files suitable for SUMO: {sumo_ready_files}/{len(valid_analyses)}")
    print(f"  Overall feasibility: {'High' if sumo_ready_files == len(valid_analyses) else 'Medium' if sumo_ready_files > 0 else 'Low'}")
    
    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    main()
