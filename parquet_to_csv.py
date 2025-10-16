#!/usr/bin/env python3
"""
parquet_to_csv.py

Usage:
    python3 parquet_to_csv.py input.parquet
    python3 parquet_to_csv.py input.parquet -o out.csv
    python3 parquet_to_csv.py input.parquet --lat LAT_COL --lon LON_COL --time TIME_COL

Requirements:
    pip install pandas pyarrow
    (or install fastparquet instead of pyarrow; pandas will choose an available engine)

What this script does:
- Reads the parquet into a pandas DataFrame
- Detects lat/lon/time columns (or you can explicitly pass them)
- Serializes nested dict/list columns into JSON strings so CSV keeps all columns
- Produces timestamp_iso column (ISO 8601) where possible
- Writes all columns to CSV, with timestamp/timestamp_iso/lat/lon first
"""

import argparse
import json
import pandas as pd
import os
import sys
from datetime import datetime

# -----------------------
# MODIFY THIS SECTION
# -----------------------
# Default CSV output name pattern (can be changed)
DEFAULT_OUTNAME = "parsed_parquet.csv"

# If your parquet files always use particular column names,
# set defaults here. If left None, the script tries to auto-detect.
# Example:
# DEFAULT_MAP = { 'lat':'latitude_column_name', 'lon':'longitude_column_name', 'time':'ts' }
DEFAULT_MAP = {
    "lat": None,
    "lon": None,
    "time": None
}
# -----------------------
# End modify section
# -----------------------

def parse_args():
    p = argparse.ArgumentParser(description="Convert parquet -> CSV (preserve all columns, normalize lat/lon/time).")
    p.add_argument("parquet", help="Path to input parquet file")
    p.add_argument("-o", "--out", default=None, help="Output CSV path (default: parsed_parquet.csv)")
    p.add_argument("--lat", default=None, help="Column name to use as latitude (overrides detection)")
    p.add_argument("--lon", default=None, help="Column name to use as longitude (overrides detection)")
    p.add_argument("--time", default=None, help="Column name to use as timestamp (overrides detection)")
    p.add_argument("--no-iso", dest="no_iso", action="store_true", help="Don't attempt to create timestamp_iso column")
    return p.parse_args()

def detect_columns(cols):
    lat = DEFAULT_MAP.get('lat')
    lon = DEFAULT_MAP.get('lon')
    timec = DEFAULT_MAP.get('time')

    # heuristics
    if lat is None:
        for c in cols:
            if 'lat' in c.lower():
                lat = c; break
    if lon is None:
        for c in cols:
            if any(k in c.lower() for k in ('lon','lng','longitude','long')):
                lon = c; break
    if timec is None:
        for c in cols:
            if any(k in c.lower() for k in ('time','timestamp','ts','date')):
                timec = c; break

    # fallback: try some generic names
    if lat is None and 'y' in [c.lower() for c in cols]: lat = [c for c in cols if c.lower()=='y'][0]
    if lon is None and 'x' in [c.lower() for c in cols]: lon = [c for c in cols if c.lower()=='x'][0]

    return lat, lon, timec

def serialize_nested(value):
    # Convert dicts/lists to JSON; leave scalar types as-is
    if pd.isna(value):
        return ''
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)
    # pandas may have numpy types; convert to python native
    try:
        # For bytes decode
        if isinstance(value, (bytes, bytearray)):
            try:
                return value.decode('utf-8', errors='ignore')
            except Exception:
                return str(value)
        # simple scalars -> convert to str safely for CSV
        if isinstance(value, (int, float, str, bool)):
            return value
        # fallback
        return str(value)
    except Exception:
        return str(value)

def make_timestamp_iso(series):
    # Try to coerce to datetime, handle epoch seconds/milliseconds heuristically
    if series.dtype.kind in 'iuf':  # numeric
        meanv = series.dropna().astype('float').mean()
        if pd.isna(meanv):
            return pd.Series([pd.NaT]*len(series))
        if meanv > 1e12:
            # milliseconds
            return pd.to_datetime(series, unit='ms', errors='coerce')
        elif meanv > 1e9:
            # seconds
            return pd.to_datetime(series, unit='s', errors='coerce')
        else:
            # assume seconds
            return pd.to_datetime(series, unit='s', errors='coerce')
    else:
        return pd.to_datetime(series, errors='coerce')

def main():
    args = parse_args()
    inp = args.parquet
    out = args.out or DEFAULT_OUTNAME

    if not os.path.exists(inp):
        print("Input file not found:", inp); sys.exit(1)

    print("Reading parquet:", inp)
    try:
        df = pd.read_parquet(inp)
    except Exception as e:
        print("Failed to read parquet. Ensure pyarrow or fastparquet is installed.")
        print("Error:", e)
        sys.exit(2)

    # Flatten columns that are nested: convert dict/list/bytes -> JSON/text
    # We'll create a sanitized copy where each cell is safe for CSV
    print("Sanitizing columns (serializing nested values)...")
    sanitized = {}
    for col in df.columns:
        # if column dtype is object, check sample of values for dict/list/bytes
        if df[col].dtype == 'object':
            # Map each value -> serialized string (but keep scalars unmodified where possible)
            sanitized[col] = df[col].apply(serialize_nested)
        else:
            # keep as-is (numeric/datetime types)
            sanitized[col] = df[col]

    sdf = pd.DataFrame(sanitized)

    # Determine lat/lon/time (CLI overrides > DEFAULT_MAP > detection)
    cli_lat = args.lat
    cli_lon = args.lon
    cli_time = args.time

    lat_col = cli_lat or DEFAULT_MAP.get('lat')
    lon_col = cli_lon or DEFAULT_MAP.get('lon')
    time_col = cli_time or DEFAULT_MAP.get('time')

    if not (lat_col and lon_col and time_col):
        detected_lat, detected_lon, detected_time = detect_columns(list(sdf.columns))
        lat_col = lat_col or detected_lat
        lon_col = lon_col or detected_lon
        time_col = time_col or detected_time

    print("Column mapping (may be None if not found):")
    print("  lat_col:", lat_col)
    print("  lon_col:", lon_col)
    print("  time_col:", time_col)

    # If lat/lon are missing -> we still proceed but warn user
    if lat_col is None or lon_col is None:
        print("WARNING: Could not detect lat/lon columns automatically. You can pass --lat and --lon to override.")
        # but continue writing all columns

    # Attempt to create timestamp_iso column if time_col found and user didn't disable
    if time_col and (not args.no_iso):
        print("Attempting to create timestamp_iso from", time_col)
        try:
            # operate on original dataframe series if it had numeric dtype,
            # else operate on sanitized (strings)
            raw_series = df[time_col] if time_col in df.columns else sdf[time_col]
            ts_iso = make_timestamp_iso(raw_series)
            sdf['timestamp_iso'] = ts_iso.dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ').replace('NaT','')
        except Exception as e:
            print("Could not create timestamp_iso:", e)
            sdf['timestamp_iso'] = ''
    else:
        sdf['timestamp_iso'] = ''

    # Create normalized timestamp column (string): preserve original if present
    if time_col and time_col in sdf.columns:
        sdf['timestamp'] = sdf[time_col]
    else:
        # fallback: use index as timestamp
        sdf['timestamp'] = sdf.index.astype(str)

    # Create normalized lat/lon columns (floats) if possible
    if lat_col and lat_col in sdf.columns:
        try:
            sdf['lat'] = pd.to_numeric(sdf[lat_col], errors='coerce')
        except Exception:
            sdf['lat'] = pd.NA
    else:
        sdf['lat'] = pd.NA

    if lon_col and lon_col in sdf.columns:
        try:
            sdf['lon'] = pd.to_numeric(sdf[lon_col], errors='coerce')
        except Exception:
            sdf['lon'] = pd.NA
    else:
        sdf['lon'] = pd.NA

    # Reorder columns: put timestamp, timestamp_iso, lat, lon up-front, then rest (avoid duplicates)
    front = ['timestamp', 'timestamp_iso', 'lat', 'lon']
    rest = [c for c in sdf.columns if c not in front]
    ordered = front + rest
    ordered = [c for c in ordered if c in sdf.columns]  # filter missing
    print("Writing CSV ->", out)
    sdf = sdf[ordered]
    # Write CSV (index=False to avoid index column)
    sdf.to_csv(out, index=False)
    print("Done. Columns written (first 20):", ordered[:20])
    print("Total rows:", len(sdf))

if __name__ == "__main__":
    main()
