#!/usr/bin/env python3
"""
PCAP Data Analysis Script
Analyzes all parquet files in the pcap directory to understand their structure, 
similarities, differences, and potential for SUMO visualization.
"""

import pandas as pd
import os
import glob
from pathlib import Path
import numpy as np
from datetime import datetime
import json

def analyze_pcap_file(file_path):
    """Comprehensive analysis of a single pcap parquet file."""
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
        
        # PCAP-specific analysis
        pcap_cols = ['packet', 'frame', 'length', 'size', 'bytes', 'protocol', 'src', 'dst', 'port', 'ip']
        analysis['pcap_metrics'] = {}
        for col in pcap_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    if pd.api.types.is_numeric_dtype(col_data):
                        analysis['pcap_metrics'][col] = {
                            'count': len(col_data),
                            'mean': col_data.mean(),
                            'std': col_data.std(),
                            'min': col_data.min(),
                            'max': col_data.max(),
                            'median': col_data.median(),
                            'q25': col_data.quantile(0.25),
                            'q75': col_data.quantile(0.75)
                        }
                    else:
                        analysis['pcap_metrics'][col] = {
                            'count': len(col_data),
                            'unique_values': col_data.nunique(),
                            'most_common': col_data.value_counts().head(5).to_dict()
                        }
        
        # Network traffic analysis
        traffic_cols = ['traffic', 'flow', 'connection', 'session', 'stream', 'conversation']
        analysis['network_traffic'] = {}
        for col in traffic_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    if pd.api.types.is_numeric_dtype(col_data):
                        analysis['network_traffic'][col] = {
                            'count': len(col_data),
                            'mean': col_data.mean(),
                            'std': col_data.std(),
                            'min': col_data.min(),
                            'max': col_data.max(),
                            'median': col_data.median(),
                            'unique_values': col_data.nunique()
                        }
                    else:
                        analysis['network_traffic'][col] = {
                            'count': len(col_data),
                            'unique_values': col_data.nunique(),
                            'most_common': col_data.value_counts().head(5).to_dict()
                        }
        
        # Protocol analysis
        protocol_cols = ['tcp', 'udp', 'ip', 'ethernet', 'arp', 'icmp', 'http', 'https', 'dns']
        analysis['protocol_info'] = {}
        for col in protocol_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    analysis['protocol_info'][col] = {
                        'count': len(col_data),
                        'unique_values': col_data.nunique(),
                        'most_common': col_data.value_counts().head(5).to_dict()
                    }
        
        # Device/Client analysis
        device_cols = ['client', 'server', 'host', 'device', 'source', 'destination', 'id', 'mac']
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
        
        # PCAP-specific analysis
        analysis['pcap_analysis'] = {
            'has_gps': len(location_cols) > 0,
            'has_timing': len(time_cols) > 0,
            'has_packet_data': any(col in df.columns for col in pcap_cols),
            'has_network_traffic': any(col in df.columns for col in traffic_cols),
            'has_protocol_info': any(col in df.columns for col in protocol_cols),
            'has_device_info': any(col in df.columns for col in device_cols),
            'potential_sumo_approaches': []
        }
        
        # Determine potential SUMO visualization approaches
        if analysis['pcap_analysis']['has_timing'] and analysis['pcap_analysis']['has_packet_data']:
            analysis['pcap_analysis']['potential_sumo_approaches'].extend([
                'Network traffic visualization',
                'Packet flow simulation',
                'Communication pattern analysis'
            ])
        
        if analysis['pcap_analysis']['has_gps']:
            analysis['pcap_analysis']['potential_sumo_approaches'].extend([
                'GPS-based vehicle tracking',
                'Location-based traffic mapping',
                'Real-world network simulation'
            ])
        
        if analysis['pcap_analysis']['has_network_traffic']:
            analysis['pcap_analysis']['potential_sumo_approaches'].extend([
                'Network topology visualization',
                'Traffic flow simulation',
                'Communication network analysis'
            ])
        
        if analysis['pcap_analysis']['has_protocol_info']:
            analysis['pcap_analysis']['potential_sumo_approaches'].extend([
                'Protocol-based communication simulation',
                'Network protocol analysis',
                'Communication layer visualization'
            ])
        
        # Extract file type from filename
        if 'server' in file_name.lower():
            analysis['file_type'] = 'server'
        elif 'pc' in file_name.lower():
            analysis['file_type'] = 'client'
        else:
            analysis['file_type'] = 'unknown'
        
        return analysis
        
    except Exception as e:
        return {
            'file_name': os.path.basename(file_path),
            'error': str(e)
        }

def compare_pcap_datasets(analyses):
    """Compare multiple pcap dataset analyses to identify similarities and differences."""
    valid_analyses = [a for a in analyses if 'error' not in a]
    
    if len(valid_analyses) < 2:
        return "Insufficient data for comparison"
    
    comparison = {
        'total_files': len(valid_analyses),
        'common_columns': set(valid_analyses[0]['columns']),
        'file_sizes': {},
        'record_counts': {},
        'file_types': set(),
        'pcap_metrics_comparison': {},
        'network_traffic_comparison': {},
        'protocol_info_comparison': {},
        'data_completeness_comparison': {}
    }
    
    # Find common columns
    for analysis in valid_analyses[1:]:
        comparison['common_columns'] = comparison['common_columns'].intersection(set(analysis['columns']))
    
    # Collect basic statistics
    for analysis in valid_analyses:
        comparison['file_sizes'][analysis['file_name']] = analysis['file_size_mb']
        comparison['record_counts'][analysis['file_name']] = analysis['total_records']
        comparison['file_types'].add(analysis.get('file_type', 'unknown'))
        comparison['data_completeness_comparison'][analysis['file_name']] = analysis['data_completeness']['completeness_percentage']
    
    # PCAP metrics comparison
    pcap_metrics = ['packet', 'frame', 'length', 'size', 'bytes', 'protocol', 'src', 'dst', 'port', 'ip']
    for metric in pcap_metrics:
        comparison['pcap_metrics_comparison'][metric] = {}
        for analysis in valid_analyses:
            if 'pcap_metrics' in analysis and metric in analysis['pcap_metrics']:
                if 'mean' in analysis['pcap_metrics'][metric]:
                    comparison['pcap_metrics_comparison'][metric][analysis['file_name']] = {
                        'mean': analysis['pcap_metrics'][metric]['mean'],
                        'std': analysis['pcap_metrics'][metric]['std'],
                        'count': analysis['pcap_metrics'][metric]['count']
                    }
                else:
                    comparison['pcap_metrics_comparison'][metric][analysis['file_name']] = {
                        'unique_values': analysis['pcap_metrics'][metric]['unique_values'],
                        'count': analysis['pcap_metrics'][metric]['count']
                    }
    
    # Network traffic comparison
    traffic_metrics = ['traffic', 'flow', 'connection', 'session', 'stream', 'conversation']
    for metric in traffic_metrics:
        comparison['network_traffic_comparison'][metric] = {}
        for analysis in valid_analyses:
            if 'network_traffic' in analysis and metric in analysis['network_traffic']:
                if 'mean' in analysis['network_traffic'][metric]:
                    comparison['network_traffic_comparison'][metric][analysis['file_name']] = {
                        'mean': analysis['network_traffic'][metric]['mean'],
                        'std': analysis['network_traffic'][metric]['std'],
                        'count': analysis['network_traffic'][metric]['count']
                    }
                else:
                    comparison['network_traffic_comparison'][metric][analysis['file_name']] = {
                        'unique_values': analysis['network_traffic'][metric]['unique_values'],
                        'count': analysis['network_traffic'][metric]['count']
                    }
    
    # Protocol info comparison
    protocol_metrics = ['tcp', 'udp', 'ip', 'ethernet', 'arp', 'icmp', 'http', 'https', 'dns']
    for metric in protocol_metrics:
        comparison['protocol_info_comparison'][metric] = {}
        for analysis in valid_analyses:
            if 'protocol_info' in analysis and metric in analysis['protocol_info']:
                comparison['protocol_info_comparison'][metric][analysis['file_name']] = {
                    'unique_values': analysis['protocol_info'][metric]['unique_values'],
                    'count': analysis['protocol_info'][metric]['count']
                }
    
    return comparison

def main():
    """Main analysis function."""
    print("=" * 100)
    print("PCAP DATASET ANALYSIS")
    print("=" * 100)
    
    # Find all parquet files in pcap directory
    pcap_dir = Path("pcap")
    if not pcap_dir.exists():
        print("Error: pcap directory not found!")
        return
    
    parquet_files = list(pcap_dir.glob("*.parquet"))
    
    if not parquet_files:
        print("No parquet files found in pcap directory!")
        return
    
    print(f"Found {len(parquet_files)} parquet files:")
    for file in sorted(parquet_files):
        print(f"  - {file.name}")
    print()
    
    # Analyze each file
    all_analyses = []
    for file_path in sorted(parquet_files):
        print(f"Analyzing {file_path.name}...")
        analysis = analyze_pcap_file(file_path)
        all_analyses.append(analysis)
    
    # Generate detailed report
    print("\n" + "=" * 100)
    print("DETAILED ANALYSIS RESULTS")
    print("=" * 100)
    
    for analysis in all_analyses:
        if 'error' in analysis:
            print(f"\nERROR analyzing {analysis['file_name']}: {analysis['error']}")
            continue
            
        print(f"\nFILE: {analysis['file_name']}")
        print("-" * 80)
        print(f"File Type: {analysis.get('file_type', 'unknown')}")
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
        
        if analysis['pcap_metrics']:
            print(f"\nPCAP Metrics:")
            for metric, stats in analysis['pcap_metrics'].items():
                print(f"  {metric}:")
                print(f"    Count: {stats['count']:,}")
                if 'mean' in stats:
                    print(f"    Mean: {stats['mean']:.3f} ± {stats['std']:.3f}")
                    print(f"    Range: {stats['min']:.3f} to {stats['max']:.3f}")
                    print(f"    Median: {stats['median']:.3f}")
                else:
                    print(f"    Unique Values: {stats['unique_values']}")
                    if 'most_common' in stats:
                        print(f"    Most Common: {stats['most_common']}")
        
        if analysis['network_traffic']:
            print(f"\nNetwork Traffic:")
            for metric, stats in analysis['network_traffic'].items():
                print(f"  {metric}:")
                print(f"    Count: {stats['count']:,}")
                if 'mean' in stats:
                    print(f"    Mean: {stats['mean']:.3f} ± {stats['std']:.3f}")
                    print(f"    Range: {stats['min']:.3f} to {stats['max']:.3f}")
                    print(f"    Unique Values: {stats['unique_values']}")
                else:
                    print(f"    Unique Values: {stats['unique_values']}")
                    if 'most_common' in stats:
                        print(f"    Most Common: {stats['most_common']}")
        
        if analysis['protocol_info']:
            print(f"\nProtocol Information:")
            for info, stats in analysis['protocol_info'].items():
                print(f"  {info}:")
                print(f"    Count: {stats['count']:,}")
                print(f"    Unique Values: {stats['unique_values']}")
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
        
        if analysis['pcap_analysis']:
            print(f"\nPCAP Analysis:")
            print(f"  Has GPS: {analysis['pcap_analysis']['has_gps']}")
            print(f"  Has Timing: {analysis['pcap_analysis']['has_timing']}")
            print(f"  Has Packet Data: {analysis['pcap_analysis']['has_packet_data']}")
            print(f"  Has Network Traffic: {analysis['pcap_analysis']['has_network_traffic']}")
            print(f"  Has Protocol Info: {analysis['pcap_analysis']['has_protocol_info']}")
            print(f"  Has Device Info: {analysis['pcap_analysis']['has_device_info']}")
            print(f"  Potential SUMO Approaches: {analysis['pcap_analysis']['potential_sumo_approaches']}")
        
        if analysis['sample_data']:
            print(f"\nSample Data (first 5 rows):")
            for i, row in enumerate(analysis['sample_data'], 1):
                print(f"  Row {i}: {row}")
    
    # Comparison analysis
    print("\n" + "=" * 100)
    print("COMPARISON ANALYSIS")
    print("=" * 100)
    
    comparison = compare_pcap_datasets(all_analyses)
    
    if isinstance(comparison, dict):
        print(f"Total Files Analyzed: {comparison['total_files']}")
        print(f"Common Columns: {len(comparison['common_columns'])}")
        print("Common Columns:", sorted(comparison['common_columns']))
        
        print(f"\nFile Types: {sorted(comparison['file_types'])}")
        
        print(f"\nFile Sizes (MB):")
        for file, size in comparison['file_sizes'].items():
            print(f"  {file}: {size:.2f} MB")
        
        print(f"\nRecord Counts:")
        for file, count in comparison['record_counts'].items():
            print(f"  {file}: {count:,} records")
        
        print(f"\nData Completeness:")
        for file, completeness in comparison['data_completeness_comparison'].items():
            print(f"  {file}: {completeness:.1f}%")
        
        print(f"\nPCAP Metrics Comparison:")
        for metric, file_data in comparison['pcap_metrics_comparison'].items():
            if file_data:  # Only show metrics that exist in at least one file
                print(f"  {metric}:")
                for file, stats in file_data.items():
                    if 'mean' in stats:
                        print(f"    {file}: Mean={stats['mean']:.3f}, Std={stats['std']:.3f}, Count={stats['count']:,}")
                    else:
                        print(f"    {file}: Unique={stats['unique_values']}, Count={stats['count']:,}")
        
        print(f"\nNetwork Traffic Comparison:")
        for metric, file_data in comparison['network_traffic_comparison'].items():
            if file_data:  # Only show metrics that exist in at least one file
                print(f"  {metric}:")
                for file, stats in file_data.items():
                    if 'mean' in stats:
                        print(f"    {file}: Mean={stats['mean']:.3f}, Std={stats['std']:.3f}, Count={stats['count']:,}")
                    else:
                        print(f"    {file}: Unique={stats['unique_values']}, Count={stats['count']:,}")
        
        print(f"\nProtocol Information Comparison:")
        for metric, file_data in comparison['protocol_info_comparison'].items():
            if file_data:  # Only show metrics that exist in at least one file
                print(f"  {metric}:")
                for file, stats in file_data.items():
                    print(f"    {file}: Unique={stats['unique_values']}, Count={stats['count']:,}")
    
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
        if analysis.get('pcap_analysis', {}).get('has_timing', False) and \
           analysis.get('pcap_analysis', {}).get('has_packet_data', False):
            sumo_ready_files += 1
    
    print(f"  Files suitable for SUMO: {sumo_ready_files}/{len(valid_analyses)}")
    print(f"  Overall feasibility: {'High' if sumo_ready_files == len(valid_analyses) else 'Medium' if sumo_ready_files > 0 else 'Low'}")
    
    # Save analysis to JSON
    analysis_file = "pcap_dataframe_analysis.json"
    with open(analysis_file, 'w') as f:
        json.dump({
            'analyses': all_analyses,
            'comparison': comparison,
            'summary': {
                'total_files': len(valid_analyses),
                'total_records': total_records,
                'total_size_mb': total_size,
                'all_columns': sorted(all_columns),
                'sumo_feasibility': sumo_ready_files
            }
        }, f, indent=2, default=str)
    
    print(f"\nAnalysis saved to: {analysis_file}")
    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    main()
