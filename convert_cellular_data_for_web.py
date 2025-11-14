#!/usr/bin/env python3
"""
Convert cellular parquet data to JSON format for web-based RSU placement simulation
"""

import pandas as pd
import json
import numpy as np

def convert_cellular_data_to_json(parquet_file, output_json, sample_size=None):
    """
    Convert cellular parquet data to JSON format for web visualization

    Args:
        parquet_file: Path to cellular parquet file
        output_json: Path to output JSON file
        sample_size: Optional sample size (None = use all data)
    """
    print(f"📂 Loading cellular data from {parquet_file}...")
    df = pd.read_parquet(parquet_file)

    print(f"✅ Loaded {len(df):,} records")
    print(f"📊 Columns: {len(df.columns)}")

    # Required columns for tower placement
    required_cols = ['Latitude', 'Longitude', 'PCell_Cell_ID']

    # Check if required columns exist
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ Missing required columns: {missing_cols}")
        print(f"Available columns: {list(df.columns)[:20]}")
        return

    # Filter to rows with valid GPS and Cell ID data
    df_valid = df[
        df['Latitude'].notna() &
        df['Longitude'].notna() &
        df['PCell_Cell_ID'].notna()
    ].copy()

    print(f"✅ Valid GPS + Cell ID records: {len(df_valid):,}")

    # Optional: Sample data if requested (for faster web loading)
    if sample_size and len(df_valid) > sample_size:
        print(f"📊 Sampling {sample_size:,} records...")
        df_valid = df_valid.sample(n=sample_size, random_state=42)

    # Select relevant columns for web visualization
    web_columns = ['Latitude', 'Longitude', 'PCell_Cell_ID']

    # Add optional columns if they exist
    optional_cols = [
        'PCell_RSRP_max', 'PCell_RSRQ_max', 'PCell_RSSI_max', 'PCell_SNR_max',
        'SCell_Cell_ID', 'SCell_RSRP_max',
        'operator', 'device_id',
        'Time'
    ]

    for col in optional_cols:
        if col in df_valid.columns:
            web_columns.append(col)

    df_web = df_valid[web_columns].copy()

    # Replace NaN with None for JSON compatibility
    df_web = df_web.replace({np.nan: None})

    # Convert to list of dictionaries
    records = df_web.to_dict('records')

    # Create metadata
    metadata = {
        'total_records': len(records),
        'original_records': len(df),
        'valid_gps_records': len(df_valid),
        'unique_cells': int(df_web['PCell_Cell_ID'].nunique()),
        'columns': web_columns,
        'has_rsrp': 'PCell_RSRP_max' in web_columns,
        'has_operator': 'operator' in web_columns,
        'has_device_id': 'device_id' in web_columns,
    }

    # Calculate bounds for map centering
    metadata['bounds'] = {
        'lat_min': float(df_web['Latitude'].min()),
        'lat_max': float(df_web['Latitude'].max()),
        'lon_min': float(df_web['Longitude'].min()),
        'lon_max': float(df_web['Longitude'].max()),
        'center_lat': float(df_web['Latitude'].mean()),
        'center_lon': float(df_web['Longitude'].mean()),
    }

    # Create output structure
    output_data = {
        'metadata': metadata,
        'records': records
    }

    # Write to JSON file
    print(f"💾 Writing to {output_json}...")
    with open(output_json, 'w') as f:
        json.dump(output_data, f, indent=2)

    # Calculate file size
    import os
    file_size = os.path.getsize(output_json) / (1024 * 1024)

    print(f"✅ Conversion complete!")
    print(f"📊 Output file size: {file_size:.2f} MB")
    print(f"📍 Map center: ({metadata['bounds']['center_lat']:.4f}, {metadata['bounds']['center_lon']:.4f})")
    print(f"📡 Unique cells: {metadata['unique_cells']}")

    return output_data


def create_sample_for_web(parquet_file, output_json, sample_size=10000):
    """
    Create a sampled version for faster web loading
    """
    print(f"\n🔬 Creating web-optimized sample ({sample_size:,} records)...")
    return convert_cellular_data_to_json(parquet_file, output_json, sample_size)


if __name__ == '__main__':
    # Convert full dataset
    parquet_file = 'cellular_dataframe (2).parquet'

    print("="*70)
    print("CELLULAR DATA CONVERSION FOR WEB VISUALIZATION")
    print("="*70)

    # Option 1: Create a sampled version (10K records) for fast web loading
    sample_output = 'cellular_data_sample.json'
    create_sample_for_web(parquet_file, sample_output, sample_size=10000)

    # Option 2: Full dataset (may be large - comment out if not needed)
    # full_output = 'cellular_data_full.json'
    # print("\n" + "="*70)
    # print("Converting full dataset (this may take a while)...")
    # print("="*70)
    # convert_cellular_data_to_json(parquet_file, full_output)

    print("\n✅ All done! Use cellular_data_sample.json in your HTML simulation.")
    print("💡 Tip: Uncomment the full dataset section if you need all records.")
