#!/usr/bin/env python3
"""
Comprehensive Sidelink Data Analysis Script
Analyzes all parquet files in the sidelink directory to understand their structure, 
similarities, differences, and significance based on the research paper context.
"""

import pandas as pd
import os
import glob
from pathlib import Path
import numpy as np
from datetime import datetime

def analyze_parquet_file_detailed(file_path):
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
            'sample_data': df.head(3).to_dict('records') if len(df) > 0 else [],
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
                        'median': col_data.median()
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
                        'most_common': col_data.value_counts().head(3).to_dict()
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
        
        return analysis
        
    except Exception as e:
        return {
            'file_name': os.path.basename(file_path),
            'error': str(e)
        }

def compare_datasets(analyses):
    """Compare multiple dataset analyses to identify similarities and differences."""
    valid_analyses = [a for a in analyses if 'error' not in a]
    
    if len(valid_analyses) < 2:
        return "Insufficient data for comparison"
    
    comparison = {
        'total_files': len(valid_analyses),
        'common_columns': set(valid_analyses[0]['columns']),
        'file_sizes': {},
        'record_counts': {},
        'ue_ids': set(),
        'session_ids': set(),
        'dates': set(),
        'mcs_values': set(),
        'signal_quality_comparison': {},
        'time_overlap': False
    }
    
    # Find common columns
    for analysis in valid_analyses[1:]:
        comparison['common_columns'] = comparison['common_columns'].intersection(set(analysis['columns']))
    
    # Collect basic statistics
    for analysis in valid_analyses:
        comparison['file_sizes'][analysis['file_name']] = analysis['file_size_mb']
        comparison['record_counts'][analysis['file_name']] = analysis['total_records']
        comparison['ue_ids'].add(analysis['ue_id'])
        comparison['session_ids'].add(analysis['session_id'])
        comparison['dates'].add(analysis['date'])
        
        # MCS values
        if 'communication_params' in analysis and 'MCS' in analysis['communication_params']:
            mcs_data = analysis['communication_params']['MCS']
            if 'most_common' in mcs_data:
                comparison['mcs_values'].update(mcs_data['most_common'].keys())
    
    # Signal quality comparison
    signal_cols = ['SNR', 'RSRP', 'RSSI', 'NOISE POWER', 'Rx_power']
    for col in signal_cols:
        comparison['signal_quality_comparison'][col] = {}
        for analysis in valid_analyses:
            if 'signal_quality' in analysis and col in analysis['signal_quality']:
                comparison['signal_quality_comparison'][col][analysis['file_name']] = {
                    'mean': analysis['signal_quality'][col]['mean'],
                    'std': analysis['signal_quality'][col]['std'],
                    'count': analysis['signal_quality'][col]['count']
                }
    
    # Time overlap analysis
    time_ranges = []
    for analysis in valid_analyses:
        if 'time_range' in analysis:
            time_ranges.append((analysis['time_range']['start_epoch'], analysis['time_range']['end_epoch']))
    
    if len(time_ranges) >= 2:
        # Check for any overlap
        for i in range(len(time_ranges)):
            for j in range(i+1, len(time_ranges)):
                start1, end1 = time_ranges[i]
                start2, end2 = time_ranges[j]
                if not (end1 < start2 or end2 < start1):
                    comparison['time_overlap'] = True
                    break
    
    return comparison

def main():
    """Main analysis function."""
    print("=" * 100)
    print("COMPREHENSIVE SIDELINK DATASET ANALYSIS")
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
        analysis = analyze_parquet_file_detailed(file_path)
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
                print(f"    Mean: {stats['mean']:.3f}")
                print(f"    Std: {stats['std']:.3f}")
                print(f"    Range: {stats['min']:.3f} to {stats['max']:.3f}")
        
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
    
    # Comparison analysis
    print("\n" + "=" * 100)
    print("COMPARISON ANALYSIS")
    print("=" * 100)
    
    comparison = compare_datasets(all_analyses)
    
    if isinstance(comparison, dict):
        print(f"Total Files Analyzed: {comparison['total_files']}")
        print(f"Common Columns: {len(comparison['common_columns'])}")
        print("Common Columns:", sorted(comparison['common_columns']))
        
        print(f"\nUE IDs: {sorted(comparison['ue_ids'])}")
        print(f"Session IDs: {sorted(comparison['session_ids'])}")
        print(f"Dates: {sorted(comparison['dates'])}")
        print(f"MCS Values: {sorted(comparison['mcs_values'])}")
        
        print(f"\nFile Sizes (MB):")
        for file, size in comparison['file_sizes'].items():
            print(f"  {file}: {size:.2f} MB")
        
        print(f"\nRecord Counts:")
        for file, count in comparison['record_counts'].items():
            print(f"  {file}: {count:,} records")
        
        print(f"\nTime Overlap: {comparison['time_overlap']}")
        
        print(f"\nSignal Quality Comparison:")
        for metric, file_data in comparison['signal_quality_comparison'].items():
            print(f"  {metric}:")
            for file, stats in file_data.items():
                print(f"    {file}: Mean={stats['mean']:.3f}, Std={stats['std']:.3f}, Count={stats['count']:,}")
    
    # Summary and significance
    print("\n" + "=" * 100)
    print("SIGNIFICANCE AND DIFFERENCES ANALYSIS")
    print("=" * 100)
    
    valid_analyses = [a for a in all_analyses if 'error' not in a]
    
    print("KEY DIFFERENCES IDENTIFIED:")
    print("1. UE ID Differences:")
    ue_ids = set(a['ue_id'] for a in valid_analyses)
    print(f"   - Different User Equipment: {sorted(ue_ids)}")
    print("   - Significance: Multiple vehicles/devices participating in V2V communication")
    
    print("\n2. Session ID Differences:")
    session_ids = set(a['session_id'] for a in valid_analyses)
    print(f"   - Different Sessions: {sorted(session_ids)}")
    print("   - Significance: Different communication sessions or test scenarios")
    
    print("\n3. Date Differences:")
    dates = set(a['date'] for a in valid_analyses)
    print(f"   - Different Dates: {sorted(dates)}")
    print("   - Significance: Data collected across multiple days")
    
    print("\n4. MCS Differences:")
    mcs_values = set()
    for analysis in valid_analyses:
        if 'communication_params' in analysis and 'MCS' in analysis['communication_params']:
            mcs_data = analysis['communication_params']['MCS']
            if 'most_common' in mcs_data:
                mcs_values.update(mcs_data['most_common'].keys())
    print(f"   - Different MCS Values: {sorted(mcs_values)}")
    print("   - Significance: Different modulation and coding schemes for various scenarios")
    
    print("\n5. Data Volume Differences:")
    for analysis in valid_analyses:
        print(f"   - {analysis['file_name']}: {analysis['total_records']:,} records, {analysis['file_size_mb']:.2f} MB")
    print("   - Significance: Different test durations or communication activity levels")
    
    print("\nRESEARCH PAPER CONTEXT:")
    print("Based on the Berlin V2X dataset paper, these sidelink files likely represent:")
    print("1. Vehicle-to-Vehicle (V2V) communication measurements")
    print("2. Different test scenarios (s1, s2 sessions)")
    print("3. Multiple User Equipment (UE1, UE2) for multi-vehicle testing")
    print("4. Sidelink communication performance under various conditions")
    print("5. Real-world V2X communication quality assessment")
    
    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    main()
