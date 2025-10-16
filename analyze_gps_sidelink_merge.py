#!/usr/bin/env python3
"""
GPS and Sidelink Dataset Merger Analysis
Analyzes the GPS datasets (pc1-pc4) and sidelink datasets to plan a proper merger
that combines GPS coordinates with V2V communication parameters.
"""

import pandas as pd
import os
import glob
from pathlib import Path
import numpy as np
from datetime import datetime
import json

def analyze_gps_file(file_path):
    """Analyze a GPS parquet file to understand its structure."""
    try:
        df = pd.read_parquet(file_path)
        
        analysis = {
            'file_name': os.path.basename(file_path),
            'total_records': len(df),
            'columns': list(df.columns),
            'column_count': len(df.columns),
            'data_types': df.dtypes.to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'sample_data': df.head(3).to_dict('records') if len(df) > 0 else [],
        }
        
        # GPS-specific analysis
        gps_cols = []
        time_cols = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['lat', 'lon', 'gps', 'location', 'coord', 'position']):
                gps_cols.append(col)
            if any(keyword in col.lower() for keyword in ['time', 'date', 'timestamp', 'ts']):
                time_cols.append(col)
        
        analysis['gps_columns'] = gps_cols
        analysis['timestamp_columns'] = time_cols
        
        # Check for communication-related columns
        comm_cols = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['datarate', 'jitter', 'ping', 'signal', 'rsrp', 'rssi', 'snr']):
                comm_cols.append(col)
        analysis['communication_columns'] = comm_cols
        
        return analysis
        
    except Exception as e:
        return {
            'file_name': os.path.basename(file_path),
            'error': str(e)
        }

def analyze_sidelink_file(file_path):
    """Analyze a sidelink parquet file to understand its structure."""
    try:
        df = pd.read_parquet(file_path)
        
        analysis = {
            'file_name': os.path.basename(file_path),
            'total_records': len(df),
            'columns': list(df.columns),
            'column_count': len(df.columns),
            'data_types': df.dtypes.to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'sample_data': df.head(3).to_dict('records') if len(df) > 0 else [],
        }
        
        # Sidelink-specific analysis
        comm_cols = []
        time_cols = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['rsrp', 'rssi', 'snr', 'mcs', 'signal', 'datarate', 'jitter']):
                comm_cols.append(col)
            if any(keyword in col.lower() for keyword in ['time', 'date', 'timestamp', 'ts']):
                time_cols.append(col)
        
        analysis['communication_columns'] = comm_cols
        analysis['timestamp_columns'] = time_cols
        
        # Extract UE and session info from filename
        filename = os.path.basename(file_path)
        if 'ue' in filename.lower():
            parts = filename.replace('.parquet', '').split('_')
            if len(parts) >= 3:
                analysis['ue_id'] = parts[0]  # ue1, ue2, etc.
                analysis['session_id'] = parts[1]  # s1, s2, etc.
                analysis['date'] = parts[2]  # 0622, 0623, etc.
        
        return analysis
        
    except Exception as e:
        return {
            'file_name': os.path.basename(file_path),
            'error': str(e)
        }

def plan_merge_strategy(gps_analyses, sidelink_analyses):
    """Plan the merge strategy based on analysis results."""
    
    merge_plan = {
        'strategy': 'temporal_and_spatial_correlation',
        'challenges': [],
        'opportunities': [],
        'recommendations': [],
        'merge_approaches': []
    }
    
    # Analyze challenges
    gps_has_timing = any('timestamp_columns' in a and a['timestamp_columns'] for a in gps_analyses if 'error' not in a)
    sidelink_has_timing = any('timestamp_columns' in a and a['timestamp_columns'] for a in sidelink_analyses if 'error' not in a)
    
    if not gps_has_timing:
        merge_plan['challenges'].append("GPS datasets lack timestamp columns for temporal correlation")
    if not sidelink_has_timing:
        merge_plan['challenges'].append("Sidelink datasets lack timestamp columns for temporal correlation")
    
    gps_has_gps = any('gps_columns' in a and a['gps_columns'] for a in gps_analyses if 'error' not in a)
    if not gps_has_gps:
        merge_plan['challenges'].append("GPS datasets may not contain actual GPS coordinates")
    
    # Analyze opportunities
    if gps_has_gps:
        merge_plan['opportunities'].append("GPS datasets provide spatial context for V2V communication")
    
    comm_overlap = False
    for gps_a in gps_analyses:
        if 'error' not in gps_a and 'communication_columns' in gps_a:
            for sidelink_a in sidelink_analyses:
                if 'error' not in sidelink_a and 'communication_columns' in sidelink_a:
                    if gps_a['communication_columns'] and sidelink_a['communication_columns']:
                        comm_overlap = True
                        break
    
    if comm_overlap:
        merge_plan['opportunities'].append("Both datasets contain communication parameters for validation")
    
    # Plan merge approaches
    merge_plan['merge_approaches'] = [
        {
            'name': 'Device-based Correlation',
            'description': 'Correlate based on device identifiers (pc1-pc4 with ue1-ue4)',
            'feasibility': 'High',
            'method': 'Map pc1->ue1, pc2->ue2, etc. and merge on device basis'
        },
        {
            'name': 'Temporal Correlation',
            'description': 'Use timestamps to correlate measurements if available',
            'feasibility': 'Medium',
            'method': 'Align measurements by time and interpolate missing values'
        },
        {
            'name': 'Spatial Interpolation',
            'description': 'Use GPS coordinates to estimate V2V communication distances',
            'feasibility': 'High',
            'method': 'Calculate distances between vehicles and correlate with signal strength'
        },
        {
            'name': 'Communication Parameter Validation',
            'description': 'Use overlapping communication parameters to validate correlation',
            'feasibility': 'Medium',
            'method': 'Compare similar metrics (datarate, jitter) between datasets'
        },
        {
            'name': 'Hybrid Approach',
            'description': 'Combine multiple correlation methods for robust merging',
            'feasibility': 'High',
            'method': 'Use device mapping + spatial correlation + parameter validation'
        }
    ]
    
    # Generate recommendations
    merge_plan['recommendations'] = [
        "Start with device-based correlation (pc1->ue1, pc2->ue2, etc.)",
        "Use GPS coordinates to calculate inter-vehicle distances",
        "Correlate signal strength with calculated distances using path loss models",
        "Validate correlation using overlapping communication parameters",
        "Create a unified dataset with both GPS and V2V communication data",
        "Implement interpolation for missing temporal data points",
        "Generate a comprehensive V2X dataset suitable for SUMO visualization"
    ]
    
    return merge_plan

def main():
    """Main analysis function."""
    print("=" * 100)
    print("GPS AND SIDELINK DATASET MERGER ANALYSIS")
    print("=" * 100)
    
    # Find GPS files in root directory
    gps_files = []
    for i in range(1, 5):
        gps_file = f"pc{i} (1).parquet"
        if os.path.exists(gps_file):
            gps_files.append(gps_file)
    
    print(f"Found {len(gps_files)} GPS files:")
    for file in gps_files:
        print(f"  - {file}")
    
    # Find sidelink files
    sidelink_dir = Path("sidelink")
    sidelink_files = list(sidelink_dir.glob("*.parquet")) if sidelink_dir.exists() else []
    
    print(f"\nFound {len(sidelink_files)} sidelink files:")
    for file in sorted(sidelink_files):
        print(f"  - {file.name}")
    
    # Analyze GPS files
    print("\n" + "=" * 100)
    print("GPS DATASET ANALYSIS")
    print("=" * 100)
    
    gps_analyses = []
    for gps_file in gps_files:
        print(f"\nAnalyzing {gps_file}...")
        analysis = analyze_gps_file(gps_file)
        gps_analyses.append(analysis)
        
        if 'error' in analysis:
            print(f"ERROR: {analysis['error']}")
            continue
        
        print(f"  Records: {analysis['total_records']:,}")
        print(f"  Columns: {analysis['column_count']}")
        print(f"  GPS Columns: {analysis.get('gps_columns', [])}")
        print(f"  Timestamp Columns: {analysis.get('timestamp_columns', [])}")
        print(f"  Communication Columns: {analysis.get('communication_columns', [])}")
        
        if analysis['sample_data']:
            print(f"  Sample data: {analysis['sample_data'][0]}")
    
    # Analyze sidelink files
    print("\n" + "=" * 100)
    print("SIDELINK DATASET ANALYSIS")
    print("=" * 100)
    
    sidelink_analyses = []
    for sidelink_file in sorted(sidelink_files):
        print(f"\nAnalyzing {sidelink_file.name}...")
        analysis = analyze_sidelink_file(sidelink_file)
        sidelink_analyses.append(analysis)
        
        if 'error' in analysis:
            print(f"ERROR: {analysis['error']}")
            continue
        
        print(f"  Records: {analysis['total_records']:,}")
        print(f"  Columns: {analysis['column_count']}")
        print(f"  UE ID: {analysis.get('ue_id', 'Unknown')}")
        print(f"  Session ID: {analysis.get('session_id', 'Unknown')}")
        print(f"  Date: {analysis.get('date', 'Unknown')}")
        print(f"  Timestamp Columns: {analysis.get('timestamp_columns', [])}")
        print(f"  Communication Columns: {analysis.get('communication_columns', [])}")
        
        if analysis['sample_data']:
            print(f"  Sample data: {analysis['sample_data'][0]}")
    
    # Plan merge strategy
    print("\n" + "=" * 100)
    print("MERGE STRATEGY PLANNING")
    print("=" * 100)
    
    merge_plan = plan_merge_strategy(gps_analyses, sidelink_analyses)
    
    print(f"\nStrategy: {merge_plan['strategy']}")
    
    print(f"\nChallenges:")
    for challenge in merge_plan['challenges']:
        print(f"  - {challenge}")
    
    print(f"\nOpportunities:")
    for opportunity in merge_plan['opportunities']:
        print(f"  - {opportunity}")
    
    print(f"\nMerge Approaches:")
    for approach in merge_plan['merge_approaches']:
        print(f"  {approach['name']} ({approach['feasibility']} feasibility)")
        print(f"    Description: {approach['description']}")
        print(f"    Method: {approach['method']}")
        print()
    
    print(f"Recommendations:")
    for i, rec in enumerate(merge_plan['recommendations'], 1):
        print(f"  {i}. {rec}")
    
    # Save analysis
    analysis_data = {
        'gps_analyses': gps_analyses,
        'sidelink_analyses': sidelink_analyses,
        'merge_plan': merge_plan
    }
    
    with open('gps_sidelink_merge_analysis.json', 'w') as f:
        json.dump(analysis_data, f, indent=2, default=str)
    
    print(f"\nAnalysis saved to: gps_sidelink_merge_analysis.json")
    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    main()
