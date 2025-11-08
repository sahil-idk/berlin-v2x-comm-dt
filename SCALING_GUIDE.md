# V2V Digital Twin - Dataset Scaling Guide

## Overview

This guide explains how to scale the V2V Communication Digital Twin to handle larger datasets, from the current 200-point baseline to 500, 1000, or even the full 61,925 Vehicle 2-4 interaction records.

## Table of Contents

1. [Dataset Extraction](#dataset-extraction)
2. [Running Simulations with Different Sizes](#running-simulations)
3. [Expected Performance](#expected-performance)
4. [Analyzing Results](#analyzing-results)
5. [Troubleshooting](#troubleshooting)

---

## Dataset Extraction

### Available Dataset Sizes

The full Berlin V2X dataset contains **61,925 Vehicle 2-4 interaction records**. You can extract subsets of any size.

### Extracting Datasets

Use the `extract_vehicle_2_4_dataset.py` script with presets or custom sizes:

#### Quick Presets

```bash
# Extract 200 points (baseline)
python extract_vehicle_2_4_dataset.py --preset 200

# Extract 500 points
python extract_vehicle_2_4_dataset.py --preset 500

# Extract 1000 points
python extract_vehicle_2_4_dataset.py --preset 1000

# Extract full dataset (all 61,925 records)
python extract_vehicle_2_4_dataset.py --preset full
```

#### Custom Extraction

```bash
# Extract custom number with sequential sampling
python extract_vehicle_2_4_dataset.py --points 750

# Extract with uniform sampling (spread across entire dataset)
python extract_vehicle_2_4_dataset.py --points 1000 --method uniform
```

### Output Files

Each extraction creates two files:

- **CSV File**: `vehicle_2_4_<N>.csv` - The actual data points
- **Metadata File**: `vehicle_2_4_<N>_metadata.json` - Statistics and info

Example for 500 points:
- `vehicle_2_4_500.csv`
- `vehicle_2_4_500_metadata.json`

### Sampling Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| `sequential` | First N records in temporal order | Best for continuous trajectory validation |
| `uniform` | Evenly spaced across entire dataset | Best for overall coverage |
| `all` | All available records | Comprehensive validation |

---

## Running Simulations

### GUI Method (Recommended)

1. **Launch the Digital Twin**:
   ```bash
   python v2v_communication_digital_twin.py
   ```

2. **Configure in GUI**:
   - **Waypoints slider**: Set to desired number (5-1000)
   - **Dataset dropdown**: Select dataset file:
     - `vehicle_2_4_first_200.csv` (baseline)
     - `vehicle_2_4_500.csv`
     - `vehicle_2_4_1000.csv`
   - **Checkboxes**: Enable/disable realistic speed and calibration
   - **Path Loss Model**: Select FSPL or 3GPP

3. **Start Simulation**: Click "Start Simulation"

### Dynamic Configuration

The digital twin automatically adjusts based on the selected waypoint count:

- **Simulation Steps**: `max(6000, NUM_WAYPOINTS * 50)`
  - 200 waypoints → 10,000 steps
  - 500 waypoints → 25,000 steps
  - 1000 waypoints → 50,000 steps

- **Route Sampling**: Every 5th waypoint for route generation
  - 200 points → 40 route waypoints
  - 500 points → 100 route waypoints
  - 1000 points → 200 route waypoints

### Progress Monitoring

During simulation, you'll see progress updates every 200 steps:

```
📊 Step 200: Dist=13.14m, PL=81.8dB, SNR=31.2dB, PRR=100.0%, WP=16/50 (32.0%)
📊 Step 400: Dist=14.29m, PL=83.2dB, SNR=29.8dB, PRR=100.0%, WP=48/50 (96.0%)
```

The percentage shows how many waypoints have been processed.

---

## Expected Performance

### Runtime Estimates

| Dataset Size | Waypoints | Sim Steps | Est. Runtime | Memory |
|--------------|-----------|-----------|--------------|--------|
| 200 points | 50-200 | 10,000 | 2-3 min | ~200 MB |
| 500 points | 100-500 | 25,000 | 5-8 min | ~300 MB |
| 1000 points | 200-1000 | 50,000 | 10-15 min | ~500 MB |
| Full (61,925) | All | ~3M steps | 30+ min | ~2 GB |

*Note: Times measured on typical consumer hardware (Intel i5/i7, 8GB RAM)*

### Accuracy Goals

Based on baseline validation:

| Metric | Target | Baseline (200) | Expected (500+) |
|--------|--------|----------------|-----------------|
| Distance Accuracy | 75-80% | 78.25% | Should hold ±3% |
| Path Loss Accuracy | 90%+ | 95.34% | Should improve |
| SNR Accuracy | 80%+ | 83.34% | Should hold |
| Overall Quality | 85%+ | 89.23% | Should hold |

### What to Expect

**Consistent Accuracy**: If the digital twin is working correctly, accuracy should remain consistent (±3%) across dataset sizes.

**Possible Improvements**:
- Path loss accuracy may improve with more data (averaging effect)
- Communication parameter validation becomes more robust

**Possible Challenges**:
- Specific waypoint regions may be less accurate
- Edge cases (very close/far distances) may be exposed

---

## Analyzing Results

### Output Files

Each simulation generates:

1. **Analysis CSV**: `v2v_communication_analysis.csv`
   - One row per waypoint
   - Columns: distance, path_loss, SNR, RSRP, RSSI, PRR, accuracy metrics
   - Rows: 90-1000+ depending on waypoint count

2. **Summary JSON**: `v2v_communication_summary.json`
   - Overall statistics
   - Mean accuracies
   - Error metrics (MAE, RMSE)

### Comparing Dataset Sizes

After running simulations with different dataset sizes:

1. **Rename output files** to preserve them:
   ```bash
   # After running with 200 points
   mv v2v_communication_analysis.csv v2v_communication_200pts_analysis.csv
   mv v2v_communication_summary.json v2v_communication_200pts_summary.json
   
   # After running with 500 points
   mv v2v_communication_analysis.csv v2v_communication_500pts_analysis.csv
   mv v2v_communication_summary.json v2v_communication_500pts_summary.json
   
   # After running with 1000 points
   mv v2v_communication_analysis.csv v2v_communication_1000pts_analysis.csv
   mv v2v_communication_summary.json v2v_communication_1000pts_summary.json
   ```

2. **Run comparison analysis**:
   ```bash
   python compare_dataset_sizes.py
   ```

3. **Review outputs**:
   - `dataset_size_comparison.png` - Visual comparison plots
   - `dataset_size_comparison_report.json` - Detailed metrics
   - `dataset_size_comparison_report.txt` - Human-readable report

### Interpretation

**Accuracy Consistency**:
- ✅ **Change < 3%**: Digital twin is robust and reliable
- ⚠️ **Change > 5%**: Investigate specific waypoint regions

**Trends**:
- **Improving**: Larger datasets average out noise → more reliable
- **Degrading**: May indicate edge cases or route generation issues

---

## Troubleshooting

### Issue: Vehicle Disappears Early

**Symptom**: "Vehicle not known" errors, simulation stops early

**Causes**:
1. Route too short for the number of waypoints
2. GPS waypoints span larger area than available routes

**Solutions**:
- Use smaller waypoint count relative to dataset size
- Check route generation: "Source route: X edges" in logs
- If route < 10 edges, waypoints may be too far apart

### Issue: Simulation Too Slow

**Symptom**: Taking much longer than expected runtime

**Causes**:
1. Too many waypoints for available route length
2. System resources constrained

**Solutions**:
- Reduce waypoint count
- Close other applications
- Use sequential sampling instead of uniform

### Issue: Accuracy Drops with More Data

**Symptom**: Accuracy decreases when using 500+ points

**Possible Causes**:
1. Early waypoints (0-200) are easier/better positioned
2. Later waypoints span more challenging areas
3. Route generation less optimal for distant waypoints

**Investigation**:
```python
# Load and analyze CSV
import pandas as pd
df = pd.read_csv('v2v_communication_analysis.csv')

# Check accuracy by waypoint range
print("0-200:", df.iloc[:200]['distance_accuracy_pct'].mean())
print("200-500:", df.iloc[200:500]['distance_accuracy_pct'].mean())
print("500+:", df.iloc[500:]['distance_accuracy_pct'].mean())
```

### Issue: Out of Memory

**Symptom**: Python crashes or system freezes

**Causes**:
- Very large datasets (10,000+ points)
- Insufficient RAM

**Solutions**:
- Use smaller dataset sizes
- Close other applications
- Increase system virtual memory

### Issue: Wrong Dataset Loaded

**Symptom**: Fewer waypoints than expected, or old data

**Causes**:
- Old CSV file cached
- Wrong file selected in GUI

**Solutions**:
1. Check dataset dropdown selection
2. Verify CSV file exists: `dir vehicle_2_4_*.csv`
3. Check file date/size
4. Re-extract if needed

---

## Advanced Usage

### Batch Processing

To run all dataset sizes automatically:

```bash
# Extract all datasets
python extract_vehicle_2_4_dataset.py --preset 200
python extract_vehicle_2_4_dataset.py --preset 500
python extract_vehicle_2_4_dataset.py --preset 1000

# Run simulations (manual via GUI)
# 1. Load GUI, select 200-point dataset, run, rename outputs
# 2. Load GUI, select 500-point dataset, run, rename outputs
# 3. Load GUI, select 1000-point dataset, run, rename outputs

# Compare all
python compare_dataset_sizes.py
```

### Custom Waypoint Ranges

To test specific waypoint ranges within a dataset:

```python
# In v2v_communication_digital_twin.py, modify line 367:
# Instead of: waypoints_df = df.head(NUM_WAYPOINTS)
# Use: waypoints_df = df.iloc[200:700]  # Test waypoints 200-700
```

### Memory Optimization

For very large datasets, process in chunks:

1. Extract multiple smaller datasets (500 points each)
2. Run simulations separately
3. Combine results manually

---

## Best Practices

1. **Start Small**: Always test with 200 points first
2. **Incremental Scaling**: Go 200 → 500 → 1000, not directly to 1000
3. **Preserve Baselines**: Always rename output files before new runs
4. **Monitor Progress**: Watch the percentage indicator in logs
5. **Validate Consistency**: Use `compare_dataset_sizes.py` to check
6. **Document Changes**: Note any anomalies or accuracy changes

---

## Support

For issues or questions:
1. Check this guide first
2. Review `v2v_communication_analysis.csv` for per-waypoint details
3. Check SUMO logs for vehicle/route errors
4. Verify GPS data in extracted CSV files

---

## Quick Reference

| Task | Command |
|------|---------|
| Extract 500 points | `python extract_vehicle_2_4_dataset.py --preset 500` |
| Extract 1000 points | `python extract_vehicle_2_4_dataset.py --preset 1000` |
| Run simulation | `python v2v_communication_digital_twin.py` |
| Compare results | `python compare_dataset_sizes.py` |
| Check dataset | `head vehicle_2_4_500.csv` |
| List datasets | `dir vehicle_2_4_*.csv` |

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-17  
**Compatible with**: v2v_communication_digital_twin.py v3.0+

