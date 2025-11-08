# V2V Digital Twin - Dataset Scaling Feature

## Overview

The V2V Communication Digital Twin now supports scaling from **200 to 1000+ data points**, enabling comprehensive validation across larger datasets from the Berlin V2X project.

**Total Available Data**: 61,925 Vehicle 2-4 interaction records  
**Implemented Support**: 200, 500, 1000 points  
**Current Baseline**: 200 points at 78.25% distance accuracy, 89.23% overall quality

---

## Quick Start

### 1. Extract Datasets (Already Done ✅)

```bash
python extract_vehicle_2_4_dataset.py --preset 500   # Creates vehicle_2_4_500.csv
python extract_vehicle_2_4_dataset.py --preset 1000  # Creates vehicle_2_4_1000.csv
```

**Status**: ✅ Both datasets extracted successfully

### 2. Run Simulations

```bash
python v2v_communication_digital_twin.py
```

**In the GUI**:
- Select dataset: `vehicle_2_4_500.csv` or `vehicle_2_4_1000.csv`
- Set waypoints: 200-1000
- Enable realistic speed and calibration
- Click "Start Simulation"

### 3. Compare Results

After running with different datasets:

```bash
# Rename outputs after each run
move v2v_communication_analysis.csv v2v_communication_200pts_analysis.csv
move v2v_communication_analysis.csv v2v_communication_500pts_analysis.csv
move v2v_communication_analysis.csv v2v_communication_1000pts_analysis.csv

# Run comparison
python compare_dataset_sizes.py
```

---

## What's New?

### GUI Enhancements

| Feature | Before | After |
|---------|--------|-------|
| Max Waypoints | 200 | 1000 |
| Dataset Selection | Hardcoded | Dropdown menu |
| Simulation Steps | Fixed 6000 | Dynamic (50× waypoints) |
| Progress Display | Steps only | Steps + Percentage |

### Dataset Options

| Dataset | Records | Use Case |
|---------|---------|----------|
| `vehicle_2_4_first_200.csv` | 200 | Baseline validation |
| `vehicle_2_4_500.csv` | 500 | Extended validation |
| `vehicle_2_4_1000.csv` | 1000 | Comprehensive validation |

### Automatic Scaling

The simulation automatically adjusts:
- **Simulation steps**: Scales with waypoint count (minimum 50 steps per waypoint)
- **Route generation**: Maintains proven approach (sample every 5th point)
- **Memory allocation**: Scales appropriately with data size

---

## Expected Performance

| Waypoints | Runtime | Simulation Steps | Memory | Accuracy Target |
|-----------|---------|------------------|--------|-----------------|
| 50-200 | 2-3 min | 10,000 | ~200 MB | 78% ± 2% |
| 200-500 | 5-8 min | 25,000 | ~300 MB | 78% ± 3% |
| 500-1000 | 10-15 min | 50,000 | ~500 MB | 78% ± 3% |

**Accuracy should remain consistent (±3%) across all dataset sizes.**

---

## Testing Workflow

### Phase 1: Baseline (200 Points)

1. Launch GUI, select `vehicle_2_4_first_200.csv`
2. Set waypoints to 50
3. Run simulation (~2-3 min)
4. Expected: Distance 78.25%, Overall 89.23%
5. Save: `v2v_communication_200pts_analysis.csv`

### Phase 2: Medium Scale (500 Points)

1. Launch GUI, select `vehicle_2_4_500.csv`
2. Set waypoints to 200
3. Run simulation (~5-8 min)
4. Expected: Distance 75-81%, Overall 86-92%
5. Save: `v2v_communication_500pts_analysis.csv`

### Phase 3: Large Scale (1000 Points)

1. Launch GUI, select `vehicle_2_4_1000.csv`
2. Set waypoints to 400
3. Run simulation (~10-15 min)
4. Expected: Distance 75-81%, Overall 86-92%
5. Save: `v2v_communication_1000pts_analysis.csv`

### Phase 4: Comparison

1. Run `python compare_dataset_sizes.py`
2. Review generated plots and reports
3. Verify accuracy variance < 3%

---

## Files Overview

### Core Files (Modified)

- **`v2v_communication_digital_twin.py`**: Main simulation with scaling support
- **`extract_vehicle_2_4_dataset.py`**: Dataset extraction with size options

### New Tools

- **`compare_dataset_sizes.py`**: Accuracy comparison across dataset sizes
- **`extract_all_datasets.bat`**: Batch extract all dataset sizes

### Datasets (Generated)

- `vehicle_2_4_500.csv` (500 records, ~327 KB)
- `vehicle_2_4_1000.csv` (1000 records, ~654 KB)
- `vehicle_2_4_500_metadata.json`
- `vehicle_2_4_1000_metadata.json`

### Documentation

- **`SCALING_GUIDE.md`**: Comprehensive guide (all details)
- **`SCALING_QUICK_START.md`**: Quick reference (5-minute setup)
- **`SCALING_IMPLEMENTATION_SUMMARY.md`**: Technical details
- **`IMPLEMENTATION_COMPLETE.txt`**: Testing checklist
- **`README_SCALING.md`**: This file (overview)

---

## Key Features

### 1. Dynamic Configuration

```python
# Simulation steps auto-scale
SIMULATION_STEPS = max(6000, NUM_WAYPOINTS * 50)

# 200 waypoints → 10,000 steps
# 500 waypoints → 25,000 steps
# 1000 waypoints → 50,000 steps
```

### 2. Progress Reporting

```
📊 Step 400: Dist=14.29m, PL=83.2dB, SNR=29.8dB, PRR=100.0%, WP=48/200 (24.0%)
                                                                  ↑ New percentage
```

### 3. Dataset Flexibility

GUI dropdown allows selecting any extracted dataset without code changes.

### 4. Comparison Analysis

Automatically generates:
- 4 comparison plots (line, bar, grouped bar, box plot)
- JSON report with detailed metrics
- Text report with conclusions

---

## Validation Criteria

### Success ✅

- [x] GUI launches without errors
- [x] Dataset dropdown shows all options
- [x] Waypoints slider extends to 1000
- [x] Datasets extracted (500, 1000)
- [ ] 500-point simulation completes (user testing)
- [ ] 1000-point simulation completes (user testing)
- [ ] Accuracy stays within ±3% (user testing)
- [ ] Comparison script generates plots (user testing)

### Testing Required

**Next Steps** (User Action):
1. Run 500-point simulation
2. Run 1000-point simulation
3. Run comparison analysis
4. Verify accuracy consistency

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Vehicle disappears | Reduce waypoint count |
| Simulation too slow | Close other applications |
| Accuracy drops >5% | Check waypoint ranges in CSV |
| Memory error | Use smaller dataset |
| Wrong dataset loaded | Verify dropdown selection |

### Debug Commands

```bash
# Check available datasets
dir vehicle_2_4_*.csv

# Verify dataset content
python -c "import pandas as pd; df=pd.read_csv('vehicle_2_4_500.csv'); print(len(df))"

# Check metadata
type vehicle_2_4_500_metadata.json
```

---

## Architecture

### Data Flow

```
sidelink_parsed.csv (325,868 records)
        ↓
extract_vehicle_2_4_dataset.py (filters Vehicle 2-4)
        ↓
vehicle_2_4_*.csv (200/500/1000 records)
        ↓
v2v_communication_digital_twin.py (simulation)
        ↓
v2v_communication_analysis.csv (results)
        ↓
compare_dataset_sizes.py (comparison)
        ↓
dataset_size_comparison.png (visualizations)
```

### Key Components

1. **Extraction Layer**: Flexible dataset creation
2. **Simulation Layer**: Scalable SUMO simulation
3. **Analysis Layer**: Multi-dataset comparison
4. **Visualization Layer**: Plots and reports

---

## Limitations

- **Maximum practical size**: ~2000 waypoints (route generation constraints)
- **Network constraints**: Limited by Berlin SUMO network (104 edges)
- **Memory**: Scales linearly with waypoint count
- **GUI responsiveness**: May appear frozen during long runs (normal behavior)

---

## Future Enhancements (Not Yet Implemented)

- [ ] Visual progress bar in GUI
- [ ] Pause/resume capability
- [ ] Batch command-line mode
- [ ] Real-time plotting during simulation
- [ ] Automatic comparison after runs
- [ ] Support for other vehicle pairs

---

## Results Summary (To Be Updated After Testing)

### Baseline (200 Points)
- Distance Accuracy: 78.25%
- Path Loss Accuracy: 95.34%
- SNR Accuracy: 83.34%
- Overall Quality: 89.23%

### 500 Points
- Distance Accuracy: TBD (target: 75-81%)
- Path Loss Accuracy: TBD (target: 92-98%)
- SNR Accuracy: TBD (target: 80-86%)
- Overall Quality: TBD (target: 86-92%)

### 1000 Points
- Distance Accuracy: TBD (target: 75-81%)
- Path Loss Accuracy: TBD (target: 92-98%)
- SNR Accuracy: TBD (target: 80-86%)
- Overall Quality: TBD (target: 86-92%)

---

## Support & Documentation

- **Quick Start**: See `SCALING_QUICK_START.md`
- **Full Guide**: See `SCALING_GUIDE.md`
- **Technical Details**: See `SCALING_IMPLEMENTATION_SUMMARY.md`
- **Testing Checklist**: See `IMPLEMENTATION_COMPLETE.txt`

---

## Version History

**v1.0** (2025-10-17):
- Initial scaling implementation
- Support for 500 and 1000-point datasets
- Dynamic simulation configuration
- Comparison analysis tool
- Comprehensive documentation

---

## Contact

For issues or questions:
1. Check documentation files
2. Review CSV analysis files
3. Verify SUMO logs
4. Check dataset metadata JSON files

---

**Status**: ✅ Implementation Complete, Ready for User Testing  
**Next**: Run Phase 1-4 testing procedures  
**Estimated Testing Time**: 30-40 minutes

