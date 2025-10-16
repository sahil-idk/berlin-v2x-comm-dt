#!/usr/bin/env python3
"""
Sidelink Data Analysis Script
Analyzes parquet files in the sidelink directory to understand their structure and content.
"""

import pandas as pd
import os
import glob
from pathlib import Path

def analyze_parquet_file(file_path):
    """Analyze a single parquet file and return its structure and statistics."""
    try:
        # Read the parquet file
        df = pd.read_parquet(file_path)
        
        analysis = {
            'file_name': os.path.basename(file_path),
            'file_size_mb': os.path.getsize(file_path) / (1024 * 1024),
            'total_records': len(df),
            'columns': list(df.columns),
            'column_count': len(df.columns),
            'data_types': df.dtypes.to_dict(),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'null_counts': df.isnull().sum().to_dict(),
            'sample_data': df.head(3).to_dict('records') if len(df) > 0 else [],
        }
        
        # Add basic statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            analysis['numeric_stats'] = df[numeric_cols].describe().to_dict()
        
        # Add unique value counts for categorical columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            analysis['categorical_stats'] = {}
            for col in categorical_cols:
                unique_count = df[col].nunique()
                analysis['categorical_stats'][col] = {
                    'unique_values': unique_count,
                    'most_common': df[col].value_counts().head(5).to_dict() if unique_count < 100 else f"{unique_count} unique values"
                }
        
        # Check for timestamp columns
        timestamp_cols = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['time', 'date', 'timestamp', 'ts']):
                timestamp_cols.append(col)
        analysis['timestamp_columns'] = timestamp_cols
        
        # Check for GPS/location columns
        location_cols = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['lat', 'lon', 'gps', 'location', 'coord', 'position']):
                location_cols.append(col)
        analysis['location_columns'] = location_cols
        
        return analysis
        
    except Exception as e:
        return {
            'file_name': os.path.basename(file_path),
            'error': str(e)
        }

def main():
    """Main analysis function."""
    print("=" * 80)
    print("SIDELINK DATA ANALYSIS REPORT")
    print("=" * 80)
    
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
    for file in parquet_files:
        print(f"  - {file.name}")
    print()
    
    # Analyze each file
    all_analyses = []
    for file_path in parquet_files:
        print(f"Analyzing {file_path.name}...")
        analysis = analyze_parquet_file(file_path)
        all_analyses.append(analysis)
    
    # Generate comprehensive report
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS RESULTS")
    print("=" * 80)
    
    for analysis in all_analyses:
        if 'error' in analysis:
            print(f"\nERROR analyzing {analysis['file_name']}: {analysis['error']}")
            continue
            
        print(f"\nFILE: {analysis['file_name']}")
        print("-" * 50)
        print(f"File Size: {analysis['file_size_mb']:.2f} MB")
        print(f"Total Records: {analysis['total_records']:,}")
        print(f"Columns: {analysis['column_count']}")
        print(f"Memory Usage: {analysis['memory_usage_mb']:.2f} MB")
        
        print(f"\nColumns ({analysis['column_count']}):")
        for i, col in enumerate(analysis['columns'], 1):
            dtype = analysis['data_types'][col]
            null_count = analysis['null_counts'][col]
            print(f"  {i:2d}. {col:<30} {str(dtype):<15} (nulls: {null_count})")
        
        if 'timestamp_columns' in analysis and analysis['timestamp_columns']:
            print(f"\nTimestamp Columns: {', '.join(analysis['timestamp_columns'])}")
        
        if 'location_columns' in analysis and analysis['location_columns']:
            print(f"Location Columns: {', '.join(analysis['location_columns'])}")
        
        if 'numeric_stats' in analysis:
            print(f"\nNumeric Column Statistics:")
            for col, stats in analysis['numeric_stats'].items():
                print(f"  {col}:")
                for stat, value in stats.items():
                    if isinstance(value, (int, float)):
                        print(f"    {stat}: {value:.4f}")
                    else:
                        print(f"    {stat}: {value}")
        
        if 'categorical_stats' in analysis:
            print(f"\nCategorical Column Statistics:")
            for col, stats in analysis['categorical_stats'].items():
                print(f"  {col}: {stats['unique_values']} unique values")
                if isinstance(stats['most_common'], dict):
                    print(f"    Most common: {stats['most_common']}")
        
        if analysis['sample_data']:
            print(f"\nSample Data (first 3 rows):")
            for i, row in enumerate(analysis['sample_data'], 1):
                print(f"  Row {i}: {row}")
    
    # Summary analysis
    print("\n" + "=" * 80)
    print("SUMMARY ANALYSIS")
    print("=" * 80)
    
    total_records = sum(a.get('total_records', 0) for a in all_analyses if 'error' not in a)
    total_size = sum(a.get('file_size_mb', 0) for a in all_analyses if 'error' not in a)
    
    print(f"Total Files Analyzed: {len([a for a in all_analyses if 'error' not in a])}")
    print(f"Total Records: {total_records:,}")
    print(f"Total Size: {total_size:.2f} MB")
    
    # Find common columns across files
    all_columns = set()
    for analysis in all_analyses:
        if 'error' not in analysis:
            all_columns.update(analysis['columns'])
    
    print(f"Unique Columns Across All Files: {len(all_columns)}")
    print("All Columns:")
    for col in sorted(all_columns):
        print(f"  - {col}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
