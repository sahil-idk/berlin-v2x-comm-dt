# V2V Digital Twin - Scaling Quick Start

## Quick Setup (5 Minutes)

### 1. Extract Datasets

Run these commands to create 500 and 1000-point datasets:

```bash
python extract_vehicle_2_4_dataset.py --preset 500
python extract_vehicle_2_4_dataset.py --preset 1000
```

**Output**: `vehicle_2_4_500.csv` and `vehicle_2_4_1000.csv`

### 2. Run Simulation

```bash
python v2v_communication_digital_twin.py
```

**In the GUI**:
1. Select dataset from dropdown (500 or 1000 points)
2. Set waypoints slider (50-1000)
3. Click "Start Simulation"
4. Watch progress percentage: `WP=16/50 (32.0%)`

### 3. Compare Results

After running with different dataset sizes, rename files and compare:

```bash
# After 200-point run
move v2v_communication_analysis.csv v2v_communication_200pts_analysis.csv

# After 500-point run  
move v2v_communication_analysis.csv v2v_communication_500pts_analysis.csv

# After 1000-point run
move v2v_communication_analysis.csv v2v_communication_1000pts_analysis.csv

# Compare all
python compare_dataset_sizes.py
```

**Output**: Comparison plots and report

---

## What Changed?

### GUI Updates

- **Waypoints slider**: Now supports 5-1000 (was 5-200)
- **Dataset dropdown**: Select CSV file (200/500/1000 points)
- **Progress percentage**: Shows waypoint completion %

### Automatic Adjustments

- **Simulation steps**: Auto-scales with waypoints (50 steps/waypoint)
- **Route generation**: Maintains proven approach (every 5th waypoint)

### Expected Runtimes

| Waypoints | Runtime | Simulation Steps |
|-----------|---------|------------------|
| 50-200 | 2-3 min | 10,000 |
| 200-500 | 5-8 min | 25,000 |
| 500-1000 | 10-15 min | 50,000 |

---

## Validation Goals

**Accuracy should stay consistent (±3%):**

- Distance: ~78%
- Path Loss: ~95%
- SNR: ~83%
- Overall: ~89%

If accuracy drops >5% with more data, check waypoint ranges in analysis CSV.

---

## Files Created

### Extraction
- `extract_vehicle_2_4_dataset.py` - Enhanced with size options
- `vehicle_2_4_500.csv` - 500-point dataset
- `vehicle_2_4_1000.csv` - 1000-point dataset

### Simulation
- `v2v_communication_digital_twin.py` - Updated to support larger datasets

### Analysis
- `compare_dataset_sizes.py` - Compare accuracy across sizes
- `dataset_size_comparison.png` - Visualization
- `dataset_size_comparison_report.json` - Detailed metrics

### Documentation
- `SCALING_GUIDE.md` - Complete guide
- `SCALING_QUICK_START.md` - This file

---

## Troubleshooting

**Vehicle disappears**: Route too short, reduce waypoint count

**Too slow**: Close other apps, or use fewer waypoints

**Accuracy drops**: Check `v2v_communication_analysis.csv`, filter by waypoint range

---

## Next Steps

1. Run baseline (200 points) and save results
2. Run 500-point simulation and save results
3. Run 1000-point simulation and save results
4. Compare all three with `compare_dataset_sizes.py`
5. Validate consistency: Distance accuracy should be within ±3%

See `SCALING_GUIDE.md` for complete details.

