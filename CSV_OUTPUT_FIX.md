# CSV Output File Location - FIXED ✅

## Problem
The CSV and JSON output files were being saved **inside** the `berlin-sumo-closed-netwokr` folder instead of the main project directory, making them hard to find.

## Solution Applied
Updated `v2v_enhanced_calibrated.py` to save all analysis files to the **main project directory**.

---

## File Locations

### ✅ **After Fix (Correct)**
All output files save to:
```
C:\Users\sahil\Sumo\berlin_v2x\
├── calibrated_distance_accuracy_analysis.csv  ← HERE
├── calibrated_simulation_summary.json         ← HERE
└── berlin-sumo-closed-netwokr\
    ├── v2v_enhanced_calibrated_routes.rou.xml   (SUMO files stay here)
    └── v2v_enhanced_calibrated.sumocfg          (SUMO files stay here)
```

### ❌ **Before Fix (Wrong)**
Files were hidden in:
```
berlin-sumo-closed-netwokr\
├── calibrated_distance_accuracy_analysis.csv  ← WRONG!
└── calibrated_simulation_summary.json         ← WRONG!
```

---

## Changes Made

### 1. **Updated CSV Save Path** (Line ~585)
```python
# BEFORE:
analysis_file = 'calibrated_distance_accuracy_analysis.csv'
analysis_df.to_csv(analysis_file, index=False)

# AFTER:
analysis_file = os.path.join(original_dir, 'calibrated_distance_accuracy_analysis.csv')
analysis_df.to_csv(analysis_file, index=False)
```

### 2. **Updated JSON Save Path** (Line ~605)
```python
# BEFORE:
with open('calibrated_simulation_summary.json', 'w') as f:
    json.dump(summary_stats, f, indent=2)

# AFTER:
summary_file = os.path.join(original_dir, 'calibrated_simulation_summary.json')
with open(summary_file, 'w') as f:
    json.dump(summary_stats, f, indent=2)
```

### 3. **Added Output Directory Message** (Line ~249)
```python
original_dir = os.getcwd()
self.log_message(f"📁 Output files will be saved to: {original_dir}")
```

---

## How to Verify

### **Option 1: Run Check Script**
```bash
python check_csv_output.py
```

This will:
- Show current directory
- List all found/missing output files
- Show file sizes and row counts
- Check for old files in wrong location
- Give clear instructions

### **Option 2: Run Simulation**
```bash
python v2v_enhanced_calibrated.py
```

Then check the GUI status window for messages like:
```
📁 Output files will be saved to: C:\Users\sahil\Sumo\berlin_v2x
...
💾 Detailed analysis saved to: C:\Users\sahil\Sumo\berlin_v2x\calibrated_distance_accuracy_analysis.csv
💾 Summary saved to: C:\Users\sahil\Sumo\berlin_v2x\calibrated_simulation_summary.json
```

### **Option 3: Manual Check**
Look in the main directory:
```bash
dir *.csv
dir *.json
```

---

## Expected Output Files

After running `v2v_enhanced_calibrated.py` successfully:

### **📊 calibrated_distance_accuracy_analysis.csv**
```csv
waypoint,actual_distance,simulated_distance,error,error_percentage,accuracy
0,23.07,30.37,7.30,31.66,68.34
1,23.07,7.18,-15.89,-68.89,31.11
2,22.38,30.36,7.99,35.70,64.30
...
```

**Columns:**
- `waypoint`: Index (0-29 for 30 waypoints)
- `actual_distance`: GPS-measured distance (meters)
- `simulated_distance`: SUMO simulated distance with calibration (meters)
- `error`: Difference (meters)
- `error_percentage`: Error as percentage of actual
- `accuracy`: 100 - abs(error_percentage)

**Typical Size:** 2-3 KB for 30 waypoints

### **📊 calibrated_simulation_summary.json**
```json
{
  "calibration_enabled": true,
  "calibration_factor": 0.607,
  "num_waypoints": 30,
  "total_waypoints_analyzed": 29,
  "mean_error_m": 67.39,
  "mean_absolute_error_m": 67.39,
  "rmse_m": 72.89,
  "mean_accuracy_percentage": -192.17,
  "high_accuracy_count": 0,
  "medium_accuracy_count": 0,
  "low_accuracy_count": 29,
  "best_waypoint": 1,
  "worst_waypoint": 0
}
```

**Typical Size:** 0.4-0.5 KB

---

## Troubleshooting

### **Issue: Files still not appearing**

**Check 1:** Are you running the latest version?
```bash
# Look for this line in the code (around line 585):
analysis_file = os.path.join(original_dir, 'calibrated_distance_accuracy_analysis.csv')
```

**Check 2:** Did simulation complete successfully?
- Look for "SIMULATION COMPLETE - STATISTICS" in GUI
- Look for "💾 Detailed analysis saved to:" message

**Check 3:** Check write permissions
```bash
# Try creating a test file
echo test > test.csv
# If this fails, you have permission issues
```

### **Issue: Old files in SUMO folder**

**Clean up old files:**
```bash
cd berlin-sumo-closed-netwokr
del calibrated_distance_accuracy_analysis.csv
del calibrated_simulation_summary.json
cd ..
```

Or just leave them - they won't interfere with new files.

---

## Additional Tools

### **check_csv_output.py**
- **Purpose**: Verify CSV/JSON output files exist and show details
- **Usage**: `python check_csv_output.py`
- **Output**: File locations, sizes, row counts, old file warnings

### **analyze_distance_accuracy.py**
- **Purpose**: Create detailed visualizations from CSV files
- **Usage**: `python analyze_distance_accuracy.py`
- **Requires**: CSV files must exist first

---

## Quick Reference

| File | Location | Created By | Purpose |
|------|----------|------------|---------|
| `calibrated_distance_accuracy_analysis.csv` | **Main Dir** ✅ | Enhanced Calibrated | Per-waypoint analysis |
| `calibrated_simulation_summary.json` | **Main Dir** ✅ | Enhanced Calibrated | Summary statistics |
| `distance_accuracy_analysis.csv` | **Main Dir** ✅ | Enhanced Robust | Per-waypoint (no calib) |
| `distance_accuracy_summary.json` | **Main Dir** ✅ | Enhanced Robust | Summary (no calib) |
| `v2v_enhanced_calibrated_routes.rou.xml` | SUMO Dir | Enhanced Calibrated | SUMO routes |
| `v2v_enhanced_calibrated.sumocfg` | SUMO Dir | Enhanced Calibrated | SUMO config |

---

## Next Steps

1. **Run new simulation:**
   ```bash
   python v2v_enhanced_calibrated.py
   ```

2. **Verify files created:**
   ```bash
   python check_csv_output.py
   ```

3. **Analyze results:**
   - Open CSV in Excel/LibreOffice
   - Or use: `python analyze_distance_accuracy.py`

4. **Compare calibrated vs uncalibrated:**
   - Run `v2v_enhanced_robust.py` (no calibration)
   - Run `v2v_enhanced_calibrated.py` (with calibration)
   - Compare the two CSV files

---

**The CSV output location is now FIXED! All analysis files save to the main project directory where they're easy to find.** ✅

