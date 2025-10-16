#!/usr/bin/env python3
"""
Comprehensive analysis of sidelink datasets to:
1. Extract column information from all parquet files
2. Check for column variations across datasets
3. Validate data quality (null values, empty entries)
4. Generate detailed report
"""

import pandas as pd
import os
import json
from pathlib import Path
from collections import defaultdict
import numpy as np

def analyze_sidelink_datasets():
    """Analyze all sidelink parquet files in the sidelink folder"""
    
    sidelink_folder = "sidelink"
    results = {}
    all_columns = set()
    column_variations = defaultdict(list)
    
    # Get all parquet files in sidelink folder
    parquet_files = [f for f in os.listdir(sidelink_folder) if f.endswith('.parquet')]
    parquet_files.sort()
    
    print(f"Found {len(parquet_files)} parquet files in {sidelink_folder} folder")
    print("=" * 80)
    
    for file in parquet_files:
        file_path = os.path.join(sidelink_folder, file)
        print(f"\nAnalyzing: {file}")
        print("-" * 50)
        
        try:
            # Read parquet file
            df = pd.read_parquet(file_path)
            
            # Basic info
            num_rows = len(df)
            num_cols = len(df.columns)
            
            print(f"Shape: {num_rows} rows × {num_cols} columns")
            print(f"Columns: {list(df.columns)}")
            
            # Store column info
            all_columns.update(df.columns)
            for col in df.columns:
                column_variations[col].append(file)
            
            # Data quality analysis
            data_quality = {}
            
            for col in df.columns:
                col_info = {
                    'dtype': str(df[col].dtype),
                    'total_values': len(df[col]),
                    'null_count': df[col].isnull().sum(),
                    'null_percentage': (df[col].isnull().sum() / len(df[col])) * 100,
                    'unique_values': df[col].nunique(),
                    'empty_strings': 0,
                    'whitespace_only': 0
                }
                
                # Check for empty strings and whitespace-only values (for string columns)
                if df[col].dtype == 'object':
                    empty_strings = (df[col] == '').sum()
                    whitespace_only = df[col].astype(str).str.strip().eq('').sum() - empty_strings
                    
                    col_info['empty_strings'] = int(empty_strings)
                    col_info['whitespace_only'] = int(whitespace_only)
                    col_info['empty_percentage'] = ((empty_strings + whitespace_only) / len(df[col])) * 100
                
                # Sample values (first 5 non-null values)
                non_null_values = df[col].dropna().head(5).tolist()
                col_info['sample_values'] = [str(val) for val in non_null_values]
                
                data_quality[col] = col_info
                
                # Print column summary
                print(f"  {col}:")
                print(f"    Type: {col_info['dtype']}")
                print(f"    Nulls: {col_info['null_count']} ({col_info['null_percentage']:.2f}%)")
                if df[col].dtype == 'object':
                    print(f"    Empty strings: {col_info['empty_strings']}")
                    print(f"    Whitespace-only: {col_info['whitespace_only']}")
                print(f"    Unique values: {col_info['unique_values']}")
                print(f"    Sample: {col_info['sample_values']}")
            
            # Store results
            results[file] = {
                'shape': (num_rows, num_cols),
                'columns': list(df.columns),
                'data_quality': data_quality,
                'file_size_mb': os.path.getsize(file_path) / (1024 * 1024)
            }
            
        except Exception as e:
            print(f"Error reading {file}: {str(e)}")
            results[file] = {'error': str(e)}
    
    # Column variation analysis
    print("\n" + "=" * 80)
    print("COLUMN VARIATION ANALYSIS")
    print("=" * 80)
    
    print(f"\nTotal unique columns across all datasets: {len(all_columns)}")
    print(f"All columns: {sorted(all_columns)}")
    
    # Find columns that appear in all files
    common_columns = set(column_variations.keys())
    for col, files in column_variations.items():
        if len(files) < len(parquet_files):
            common_columns.discard(col)
    
    print(f"\nColumns present in ALL datasets ({len(common_columns)}):")
    for col in sorted(common_columns):
        print(f"  - {col}")
    
    # Find columns that vary across datasets
    varying_columns = {}
    for col, files in column_variations.items():
        if len(files) < len(parquet_files):
            varying_columns[col] = files
    
    if varying_columns:
        print(f"\nColumns that vary across datasets ({len(varying_columns)}):")
        for col, files in sorted(varying_columns.items()):
            missing_files = [f for f in parquet_files if f not in files]
            print(f"  - {col}:")
            print(f"    Present in: {files}")
            print(f"    Missing in: {missing_files}")
    else:
        print("\nNo column variations found - all datasets have identical column structure")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    successful_files = [f for f in results.keys() if 'error' not in results[f]]
    print(f"Successfully analyzed: {len(successful_files)}/{len(parquet_files)} files")
    
    if successful_files:
        total_rows = sum(results[f]['shape'][0] for f in successful_files)
        total_size = sum(results[f]['file_size_mb'] for f in successful_files)
        
        print(f"Total rows across all datasets: {total_rows:,}")
        print(f"Total file size: {total_size:.2f} MB")
        
        # Row count by file
        print(f"\nRow counts by file:")
        for file in successful_files:
            rows = results[file]['shape'][0]
            size = results[file]['file_size_mb']
            print(f"  {file}: {rows:,} rows ({size:.1f} MB)")
    
    # Save detailed results to JSON
    output_data = {
        'analysis_summary': {
            'total_files': len(parquet_files),
            'successful_files': len(successful_files),
            'total_unique_columns': len(all_columns),
            'common_columns': sorted(common_columns),
            'varying_columns': varying_columns,
            'all_columns': sorted(all_columns)
        },
        'file_results': results,
        'column_variations': dict(column_variations)
    }
    
    with open('sidelink_column_analysis.json', 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: sidelink_column_analysis.json")
    
    return output_data

if __name__ == "__main__":
    results = analyze_sidelink_datasets()

