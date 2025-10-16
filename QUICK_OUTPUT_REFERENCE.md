# 📋 **Quick Reference: Where Are My Files?**

## 🎯 **TL;DR**

All simulation outputs are saved to: **`C:\Users\sahil\Sumo\berlin_v2x\`** (main project folder)

---

## 📂 **Output Files by Script**

### **`v2v_realistic_speed_simulation.py`** ✨ LATEST

**Generates:**
1. `realistic_speed_waypoint_analysis.csv` - Per-waypoint distance & speed analysis
2. `realistic_speed_simulation_summary.json` - Overall accuracy metrics

**Columns in CSV:**
- Distance: `actual_distance_m`, `simulated_distance_m`, `distance_error_m`, `distance_accuracy_pct`
- Speed (Source): `actual_speed_src_kmh`, `simulated_speed_src_kmh`, `speed_error_src_kmh`
- Speed (Dest): `actual_speed_dst_kmh`, `simulated_speed_dst_kmh`, `speed_error_dst_kmh`
- Settings: `calibration_enabled`, `realistic_speed_enabled`

**Location:** Main project folder

---

### **`v2v_enhanced_calibrated.py`**

**Generates:**
1. `calibrated_distance_accuracy_analysis.csv` - Distance accuracy per waypoint
2. `calibrated_simulation_summary.json` - Distance accuracy summary

**Columns in CSV:**
- `waypoint`, `actual_distance`, `simulated_distance`, `error`, `error_percentage`, `accuracy`

**Location:** Main project folder

---

### **`calculate_overall_accuracy.py`**

**Generates:**
1. `overall_accuracy_summary.json` - Overall accuracy metrics from existing CSV

**Location:** Main project folder

---

## 📊 **What Each File Contains**

| File | What's Inside | Use For |
|------|---------------|---------|
| `realistic_speed_waypoint_analysis.csv` | Distance + Speed per waypoint | Detailed per-waypoint analysis |
| `realistic_speed_simulation_summary.json` | Overall distance + speed metrics | Quick overview |
| `calibrated_distance_accuracy_analysis.csv` | Distance only per waypoint | Distance-focused analysis |
| `calibrated_simulation_summary.json` | Overall distance metrics | Distance accuracy summary |
| `overall_accuracy_summary.json` | Overall accuracy from CSV | Post-analysis metrics |

---

## 🔍 **How to Find Your Files**

### **Option 1: Check Console Output**

After running the simulation, look for:
```
💾 Detailed CSV saved to:
   C:\Users\sahil\Sumo\berlin_v2x\realistic_speed_waypoint_analysis.csv
   📂 Location: Main project folder
```

### **Option 2: Navigate Directly**

```bash
cd C:\Users\sahil\Sumo\berlin_v2x
dir *.csv
dir *.json
```

### **Option 3: Use Windows Explorer**

1. Open: `C:\Users\sahil\Sumo\berlin_v2x\`
2. Sort by "Date Modified" (newest first)
3. Look for files with today's date

---

## ⚡ **Quick Commands**

### **View Latest CSV:**
```bash
cd C:\Users\sahil\Sumo\berlin_v2x
python -c "import pandas as pd; df=pd.read_csv('realistic_speed_waypoint_analysis.csv'); print(df.head())"
```

### **View Latest JSON:**
```bash
cd C:\Users\sahil\Sumo\berlin_v2x
python -c "import json; print(json.dumps(json.load(open('realistic_speed_simulation_summary.json')), indent=2))"
```

### **List All Output Files:**
```bash
cd C:\Users\sahil\Sumo\berlin_v2x
dir *analysis*.csv
dir *summary*.json
```

---

## 🎯 **Common Questions**

### **Q: Where is the CSV saved?**
**A:** Main project folder: `C:\Users\sahil\Sumo\berlin_v2x\realistic_speed_waypoint_analysis.csv`

### **Q: Which CSV has speed data?**
**A:** `realistic_speed_waypoint_analysis.csv` (from `v2v_realistic_speed_simulation.py`)

### **Q: Which CSV is most detailed?**
**A:** `realistic_speed_waypoint_analysis.csv` - Has both distance AND speed for every waypoint!

### **Q: How do I check overall accuracy?**
**A:** Open `realistic_speed_simulation_summary.json` or run `calculate_overall_accuracy.py`

### **Q: Can I compare realistic vs constant speed?**
**A:** Yes! Run twice (with realistic speed ON/OFF), rename CSVs, then compare side-by-side.

---

## 📈 **Recommended Workflow**

1. **Run Simulation:**
   ```bash
   python v2v_realistic_speed_simulation.py
   ```

2. **Check Output Location:**
   - Look at console: "Files saved to: ..."
   - Navigate to main project folder

3. **Open CSV:**
   ```bash
   # With pandas (recommended)
   python -c "import pandas as pd; df=pd.read_csv('realistic_speed_waypoint_analysis.csv'); print(df.head(10))"
   
   # Or open in Excel/LibreOffice
   start realistic_speed_waypoint_analysis.csv
   ```

4. **Review JSON:**
   ```bash
   type realistic_speed_simulation_summary.json
   ```

5. **Analyze:**
   - Check mean accuracy (target: >60%)
   - Check speed errors (target: <2 km/h)
   - Identify problem waypoints

---

## 🎉 **That's It!**

**Remember:** All files go to **main project folder**, not SUMO subfolder!

**File naming pattern:**
- `realistic_speed_*` = From realistic speed simulation
- `calibrated_*` = From calibrated simulation
- `overall_*` = From overall accuracy calculator

