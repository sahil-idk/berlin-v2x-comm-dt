# CSV File Save Location - Fixed ✅

## Issue Identified
The CSV files were being saved in the **SUMO subfolder** (`berlin-sumo-closed-netwokr/`) instead of the **main project folder**.

## Root Cause
The simulation script changes directory to `berlin-sumo-closed-netwokr` to run SUMO, and file paths were resolving relative to that directory instead of the original project directory.

## Solution Applied

### **Changes to `v2v_enhanced_calibrated.py`:**

1. **Enhanced Error Handling for CSV Saving** (Line 584-599):
```python
# Build absolute path to main project directory
analysis_file = os.path.join(original_dir, 'calibrated_distance_accuracy_analysis.csv')

# Create directory if needed and save
try:
    os.makedirs(os.path.dirname(analysis_file), exist_ok=True)
    analysis_df.to_csv(analysis_file, index=False)
    self.log_message(f"\n💾 Detailed analysis saved to: {analysis_file}")
    self.log_message(f"   📂 File location: {os.path.abspath(analysis_file)}")
except Exception as e:
    self.log_message(f"\n❌ Error saving CSV: {e}")
    self.log_message(f"   Current directory: {os.getcwd()}")
    self.log_message(f"   Attempted path: {analysis_file}")
```

2. **Enhanced Error Handling for JSON Saving** (Line 617-626):
```python
# Save JSON summary to main project directory
summary_file = os.path.join(original_dir, 'calibrated_simulation_summary.json')

try:
    with open(summary_file, 'w') as f:
        json.dump(summary_stats, f, indent=2)
    self.log_message(f"💾 Summary saved to: {summary_file}")
    self.log_message(f"   📂 File location: {os.path.abspath(summary_file)}")
except Exception as e:
    self.log_message(f"❌ Error saving JSON: {e}")
```

## File Locations NOW ✅

### **Main Project Directory** (`C:\Users\sahil\Sumo\berlin_v2x\`)
✅ **`calibrated_distance_accuracy_analysis.csv`** - Per-waypoint analysis  
✅ **`calibrated_simulation_summary.json`** - Summary statistics  

### **SUMO Subfolder** (`berlin-sumo-closed-netwokr/`)
- `v2v_enhanced_calibrated_routes.rou.xml` - Generated routes (internal)  
- `v2v_enhanced_calibrated.sumocfg` - SUMO config (internal)  

## How to Verify

### **After Running Simulation:**

1. **Check Main Folder:**
```powershell
# PowerShell
Get-ChildItem *.csv, *.json | Select-Object Name, Length, LastWriteTime

# Expected output:
# calibrated_distance_accuracy_analysis.csv
# calibrated_simulation_summary.json
```

2. **Read CSV:**
```powershell
Get-Content calibrated_distance_accuracy_analysis.csv -Head 5
```

3. **Read JSON:**
```powershell
Get-Content calibrated_simulation_summary.json | ConvertFrom-Json
```

## GUI Output Changes

### **Before Fix:**
```
💾 Detailed analysis saved to: calibrated_distance_accuracy_analysis.csv
💾 Summary saved to: calibrated_simulation_summary.json
```
*(Unclear where files were saved)*

### **After Fix:**
```
💾 Detailed analysis saved to: C:\Users\sahil\Sumo\berlin_v2x\calibrated_distance_accuracy_analysis.csv
   📂 File location: C:\Users\sahil\Sumo\berlin_v2x\calibrated_distance_accuracy_analysis.csv
💾 Summary saved to: C:\Users\sahil\Sumo\berlin_v2x\calibrated_simulation_summary.json
   📂 File location: C:\Users\sahil\Sumo\berlin_v2x\calibrated_simulation_summary.json
```
*(Clear absolute paths shown)*

## Example CSV Output

### **`calibrated_distance_accuracy_analysis.csv`:**
```csv
waypoint,actual_distance,simulated_distance,error,error_percentage,accuracy
0,23.07,4.52,-18.55,-80.41,19.59
1,23.07,49.65,26.58,115.25,-15.25
2,22.38,24.75,2.37,10.59,89.41
3,22.38,24.75,2.37,10.59,89.41
...
```

### **`calibrated_simulation_summary.json`:**
```json
{
  "calibration_enabled": true,
  "calibration_factor": 0.607,
  "num_waypoints": 30,
  "total_waypoints_analyzed": 30,
  "mean_error_m": 12.48,
  "mean_absolute_error_m": 13.72,
  "rmse_m": 15.02,
  "mean_accuracy_percentage": 28.01,
  "high_accuracy_count": 0,
  "medium_accuracy_count": 3,
  "low_accuracy_count": 27,
  "best_waypoint": 2,
  "worst_waypoint": 21
}
```

## Benefits of This Fix

1. ✅ **Clear File Locations**: Absolute paths shown in GUI
2. ✅ **Error Handling**: Detailed error messages if save fails
3. ✅ **Consistent Behavior**: All output files in same main directory
4. ✅ **Easy Access**: No need to search subdirectories
5. ✅ **Better UX**: User knows exactly where to find results

## Testing the Fix

### **Run the Simulation:**
```bash
python v2v_enhanced_calibrated.py
```

### **Expected Behavior:**
1. Tkinter GUI opens
2. Click "Start Simulation"
3. SUMO-GUI opens and runs
4. Status window shows file save messages with **full paths**
5. Check main project folder for CSV and JSON files

### **Verify Files:**
```bash
# Should see both files in main directory
ls calibrated_*.csv
ls calibrated_*.json
```

## Backward Compatibility

Old files in `berlin-sumo-closed-netwokr/` subfolder are **not automatically deleted**. You can manually remove them:

```powershell
# Optional cleanup of old files
Remove-Item berlin-sumo-closed-netwokr\calibrated_distance_*.csv -ErrorAction SilentlyContinue
Remove-Item berlin-sumo-closed-netwokr\calibrated_simulation_*.json -ErrorAction SilentlyContinue
```

---

## Summary

✅ **Problem**: CSV files saved in SUMO subfolder  
✅ **Solution**: Enhanced path handling with `os.path.join(original_dir, filename)`  
✅ **Result**: Files now save to main project directory with clear confirmation  
✅ **Bonus**: Better error handling and absolute path display  

**The enhanced calibrated simulation now correctly saves all output files to the main project directory where you can easily find them!** 🎉

