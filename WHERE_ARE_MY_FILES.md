# 📁 Where Are My Output Files?

## Quick Reference

### ✅ **Files Save Location: MAIN PROJECT FOLDER**

```
C:\Users\sahil\Sumo\berlin_v2x\
├── calibrated_distance_accuracy_analysis.csv  ✅ HERE!
├── calibrated_simulation_summary.json        ✅ HERE!
├── v2v_enhanced_calibrated.py
├── vehicle_2_4_first_200.csv
└── berlin-sumo-closed-netwokr/
    ├── osm.net.xml.gz
    └── (internal SUMO files only)
```

## How to Find Your Files

### **PowerShell Commands:**

```powershell
# List all CSV and JSON files in current directory
Get-ChildItem *.csv, *.json | Format-Table Name, Length, LastWriteTime

# View CSV content
Get-Content calibrated_distance_accuracy_analysis.csv -Head 10

# View JSON content (pretty formatted)
Get-Content calibrated_simulation_summary.json | ConvertFrom-Json | Format-List
```

### **Windows Explorer:**
1. Open folder: `C:\Users\sahil\Sumo\berlin_v2x\`
2. Look for files starting with `calibrated_`
3. Sort by "Date Modified" to find latest

## GUI Output Shows Full Path

When the simulation completes, the Tkinter GUI status window will show:

```
💾 Detailed analysis saved to: C:\Users\sahil\Sumo\berlin_v2x\calibrated_distance_accuracy_analysis.csv
   📂 File location: C:\Users\sahil\Sumo\berlin_v2x\calibrated_distance_accuracy_analysis.csv
💾 Summary saved to: C:\Users\sahil\Sumo\berlin_v2x\calibrated_simulation_summary.json
   📂 File location: C:\Users\sahil\Sumo\berlin_v2x\calibrated_simulation_summary.json
```

## Common Mistake ❌

**DON'T LOOK HERE:**
```
C:\Users\sahil\Sumo\berlin_v2x\berlin-sumo-closed-netwokr\
```
This folder only contains SUMO network files and temporary simulation files.

## What Each File Contains

### **`calibrated_distance_accuracy_analysis.csv`**
- **Format**: CSV with headers
- **Columns**:
  - `waypoint`: Waypoint index (0, 1, 2, ...)
  - `actual_distance`: Real GPS distance (meters)
  - `simulated_distance`: SUMO simulated distance (meters)
  - `error`: Difference (simulated - actual)
  - `error_percentage`: Error as percentage
  - `accuracy`: 100 - |error_percentage|

**Example:**
```csv
waypoint,actual_distance,simulated_distance,error,error_percentage,accuracy
0,23.07,4.52,-18.55,-80.41,19.59
1,23.07,49.65,26.58,115.25,-15.25
2,22.38,24.75,2.37,10.59,89.41
```

### **`calibrated_simulation_summary.json`**
- **Format**: JSON
- **Contains**:
  - Calibration settings
  - Summary statistics (mean error, RMSE, accuracy)
  - Accuracy distribution (high/medium/low)
  - Best/worst waypoints

**Example:**
```json
{
  "calibration_enabled": true,
  "calibration_factor": 0.607,
  "num_waypoints": 30,
  "mean_error_m": 12.48,
  "mean_absolute_error_m": 13.72,
  "rmse_m": 15.02,
  "mean_accuracy_percentage": 28.01
}
```

## Opening Files

### **CSV File:**
- **Excel**: Double-click the file
- **Python**: `pd.read_csv('calibrated_distance_accuracy_analysis.csv')`
- **Notepad**: Right-click → Open with → Notepad

### **JSON File:**
- **VS Code**: Double-click (auto-formats)
- **Python**: `json.load(open('calibrated_simulation_summary.json'))`
- **Online**: Copy content to [jsonformatter.org](https://jsonformatter.org)

## Still Can't Find Them?

### **Search Command:**
```powershell
# Search entire project
Get-ChildItem -Path . -Filter "calibrated_*.csv" -Recurse | Select-Object FullName

# Show last modified CSV files
Get-ChildItem *.csv | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

### **Verify Script Ran:**
Check Tkinter GUI status window for the save confirmation messages. If you don't see them, the simulation may have stopped before completing.

---

## Quick Checklist

✅ Run `python v2v_enhanced_calibrated.py`  
✅ Click "Start Simulation" in Tkinter GUI  
✅ Wait for simulation to complete  
✅ Check status window for "💾 Detailed analysis saved to..."  
✅ Look in **main project folder** (not SUMO subfolder)  
✅ Files should be there with today's timestamp  

---

**Remember: Output files are ALWAYS saved to the main project directory where you run the script from!** 📂✅

