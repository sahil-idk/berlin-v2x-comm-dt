# 🚗 **Realistic Speed Analysis - Complete Guide**

## ✅ **What's New in `v2v_realistic_speed_simulation.py`**

The simulation now generates **comprehensive CSV and JSON reports** with per-waypoint analysis of both **distance** and **speed** accuracy!

---

## 📂 **Output Files Location**

**All files are saved to the MAIN PROJECT FOLDER:**
```
C:\Users\sahil\Sumo\berlin_v2x\
├── realistic_speed_waypoint_analysis.csv  ✨ NEW!
└── realistic_speed_simulation_summary.json ✨ NEW!
```

---

## 📊 **CSV File: `realistic_speed_waypoint_analysis.csv`**

### **Columns:**

| Column | Description | Example |
|--------|-------------|---------|
| `waypoint` | Waypoint index | 0, 1, 2, ... |
| `step` | Simulation step | 50, 120, 190, ... |
| `actual_distance_m` | Distance from dataset (ground truth) | 23.07 |
| `simulated_distance_m` | Distance from SUMO simulation | 24.75 |
| `distance_error_m` | Error in meters | 1.68 |
| `distance_error_pct` | Error percentage | 7.28 |
| `distance_accuracy_pct` | Accuracy percentage (100 - abs(error%)) | 92.72 |
| `actual_speed_src_kmh` | Source vehicle speed from dataset | 37.78 |
| `simulated_speed_src_kmh` | Source vehicle speed from simulation | 37.80 |
| `speed_error_src_kmh` | Source speed error | 0.02 |
| `actual_speed_dst_kmh` | Destination vehicle speed from dataset | 39.82 |
| `simulated_speed_dst_kmh` | Destination vehicle speed from simulation | 39.80 |
| `speed_error_dst_kmh` | Destination speed error | -0.02 |
| `calibration_enabled` | Was calibration (0.607) applied? | True/False |
| `realistic_speed_enabled` | Were realistic speeds used? | True/False |

### **Use Cases:**

1. **Compare Distance Accuracy:**
   ```python
   import pandas as pd
   df = pd.read_csv('realistic_speed_waypoint_analysis.csv')
   print(df[['waypoint', 'actual_distance_m', 'simulated_distance_m', 'distance_accuracy_pct']])
   ```

2. **Compare Speed Accuracy:**
   ```python
   print(df[['waypoint', 'actual_speed_src_kmh', 'simulated_speed_src_kmh', 'speed_error_src_kmh']])
   ```

3. **Filter High-Accuracy Waypoints:**
   ```python
   high_acc = df[df['distance_accuracy_pct'] >= 90]
   print(f"High accuracy waypoints: {len(high_acc)}")
   ```

4. **Analyze Speed Errors:**
   ```python
   print(f"Mean speed error (source): {df['speed_error_src_kmh'].mean():.2f} km/h")
   print(f"Mean speed error (dest): {df['speed_error_dst_kmh'].mean():.2f} km/h")
   ```

---

## 📋 **JSON File: `realistic_speed_simulation_summary.json`**

### **Structure:**

```json
{
  "simulation_settings": {
    "num_waypoints": 30,
    "calibration_enabled": true,
    "calibration_factor": 0.607,
    "realistic_speed_enabled": true,
    "total_steps": 2500
  },
  "distance_accuracy": {
    "mean_accuracy_pct": 65.42,
    "median_accuracy_pct": 72.15,
    "min_accuracy_pct": 12.34,
    "max_accuracy_pct": 98.56,
    "mean_error_m": 5.67,
    "mean_absolute_error_m": 8.23,
    "rmse_m": 10.45,
    "std_dev_m": 7.89
  },
  "speed_accuracy": {
    "source_vehicle": {
      "mean_error_kmh": 0.15,
      "mean_absolute_error_kmh": 1.25,
      "rmse_kmh": 1.78,
      "std_dev_kmh": 1.45
    },
    "destination_vehicle": {
      "mean_error_kmh": -0.12,
      "mean_absolute_error_kmh": 1.32,
      "rmse_kmh": 1.85,
      "std_dev_kmh": 1.52
    }
  },
  "waypoint_distribution": {
    "high_accuracy_90_plus": 5,
    "medium_accuracy_70_89": 12,
    "low_accuracy_below_70": 13,
    "total_waypoints_analyzed": 30
  },
  "best_waypoint": {
    "waypoint": 2,
    "accuracy_pct": 98.56,
    "distance_error_m": 0.32
  },
  "worst_waypoint": {
    "waypoint": 15,
    "accuracy_pct": 12.34,
    "distance_error_m": 18.45
  }
}
```

### **Key Sections:**

1. **`simulation_settings`**: What settings were used
2. **`distance_accuracy`**: Overall distance accuracy metrics
3. **`speed_accuracy`**: Speed accuracy for both vehicles
4. **`waypoint_distribution`**: How many waypoints in each accuracy tier
5. **`best_waypoint`**: Most accurate waypoint
6. **`worst_waypoint`**: Least accurate waypoint

---

## 🎯 **How to Run the Simulation**

### **Step 1: Start the Simulation**

```bash
python v2v_realistic_speed_simulation.py
```

### **Step 2: Configure Settings**

In the GUI:
- ✅ **"Use Realistic Speed from Dataset"** - ON for realistic speeds
- ✅ **"Apply Calibration (0.607)"** - ON to apply calibration factor
- **Waypoints**: Adjust slider (5-100)

### **Step 3: Run and Wait**

Click **"Start Simulation"** and wait for completion.

### **Step 4: Check Output**

The GUI will show:
```
💾 Detailed CSV saved to:
   C:\Users\sahil\Sumo\berlin_v2x\realistic_speed_waypoint_analysis.csv
   📂 Location: Main project folder
   📊 Rows: 30

💾 Summary JSON saved to:
   C:\Users\sahil\Sumo\berlin_v2x\realistic_speed_simulation_summary.json
```

---

## 📊 **Understanding the Output**

### **Console Report Example:**

```
======================================================================
OVERALL ACCURACY REPORT
======================================================================

📊 Distance Accuracy:
   Mean Accuracy: 65.42%
   Median Accuracy: 72.15%
   Mean Absolute Error: 8.23 m
   RMSE: 10.45 m

📊 Speed Accuracy (Source Vehicle):
   Mean Absolute Error: 1.25 km/h
   RMSE: 1.78 km/h

📊 Speed Accuracy (Destination Vehicle):
   Mean Absolute Error: 1.32 km/h
   RMSE: 1.85 km/h

📊 Waypoint Distribution:
   High Accuracy (≥90%): 5 waypoints
   Medium Accuracy (70-89%): 12 waypoints
   Low Accuracy (<70%): 13 waypoints

📊 Best Waypoint: #2
   Accuracy: 98.56%

📊 Worst Waypoint: #15
   Accuracy: 12.34%

📊 Overall Assessment: 65.42% - GOOD ✓
```

---

## 🔍 **Interpreting Results**

### **Distance Accuracy:**

- **≥90%**: Excellent - Simulation matches dataset very closely
- **70-89%**: Good - Reasonable accuracy for V2V applications
- **<70%**: Needs improvement - Check calibration and routing

### **Speed Accuracy:**

- **<2 km/h error**: Excellent - Speeds are well-matched
- **2-5 km/h error**: Good - Acceptable for most use cases
- **>5 km/h error**: Poor - Check if realistic speeds are enabled

### **RMSE (Root Mean Square Error):**

- **Distance RMSE <10m**: Good accuracy
- **Distance RMSE 10-20m**: Fair accuracy
- **Distance RMSE >20m**: Poor accuracy

- **Speed RMSE <2 km/h**: Good accuracy
- **Speed RMSE 2-5 km/h**: Fair accuracy
- **Speed RMSE >5 km/h**: Poor accuracy

---

## 🆚 **Comparing Realistic vs Constant Speed**

### **Run 1: Realistic Speed ON**
```bash
# In GUI: ✅ Use Realistic Speed from Dataset
```

**Expected:**
- Speed errors: **<2 km/h** (vehicles use actual speeds)
- Distance accuracy: **Higher** (better temporal alignment)

### **Run 2: Realistic Speed OFF**
```bash
# In GUI: ❌ Use Realistic Speed from Dataset
```

**Expected:**
- Speed errors: **>5 km/h** (constant 15 m/s ≠ actual speeds)
- Distance accuracy: **Lower** (poor temporal alignment)

### **Comparison:**

Open both CSVs side-by-side:
```python
import pandas as pd

realistic = pd.read_csv('realistic_speed_waypoint_analysis_realistic.csv')
constant = pd.read_csv('realistic_speed_waypoint_analysis_constant.csv')

print(f"Realistic speed - Mean distance accuracy: {realistic['distance_accuracy_pct'].mean():.2f}%")
print(f"Constant speed - Mean distance accuracy: {constant['distance_accuracy_pct'].mean():.2f}%")

print(f"\nRealistic speed - Mean speed error: {realistic['speed_error_src_kmh'].abs().mean():.2f} km/h")
print(f"Constant speed - Mean speed error: {constant['speed_error_src_kmh'].abs().mean():.2f} km/h")
```

---

## 📈 **Analysis Tips**

### **1. Identify Problem Waypoints:**

```python
import pandas as pd
df = pd.read_csv('realistic_speed_waypoint_analysis.csv')

# Waypoints with low accuracy
low_acc = df[df['distance_accuracy_pct'] < 50]
print(f"Problem waypoints: {low_acc['waypoint'].tolist()}")
```

### **2. Visualize Distance Accuracy:**

```python
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(df['waypoint'], df['distance_accuracy_pct'], marker='o')
plt.axhline(y=90, color='g', linestyle='--', label='High Accuracy (90%)')
plt.axhline(y=70, color='orange', linestyle='--', label='Medium Accuracy (70%)')
plt.xlabel('Waypoint')
plt.ylabel('Distance Accuracy (%)')
plt.title('Distance Accuracy per Waypoint')
plt.legend()
plt.grid(True)
plt.savefig('distance_accuracy_plot.png')
plt.show()
```

### **3. Analyze Speed vs Distance Correlation:**

```python
import numpy as np

# Check if speed errors correlate with distance errors
correlation = np.corrcoef(
    df['speed_error_src_kmh'].abs(), 
    df['distance_error_m'].abs()
)[0, 1]

print(f"Speed-Distance error correlation: {correlation:.3f}")
# High correlation (>0.5) means speed errors affect distance accuracy
```

---

## 🎓 **Key Takeaways**

1. **CSV File** = Per-waypoint detailed analysis
2. **JSON File** = Overall summary metrics
3. **Both files** are saved to **main project folder**
4. **Realistic speeds** from dataset are now used (if enabled)
5. **Speed accuracy** is now measured alongside distance accuracy
6. **Calibration** can be toggled in GUI

---

## ✅ **Quick Checklist**

After running the simulation:

- [ ] CSV file exists in main project folder
- [ ] JSON file exists in main project folder
- [ ] CSV has all expected columns (15 columns)
- [ ] JSON has all expected sections
- [ ] Console shows overall accuracy report
- [ ] Mean speed error is reasonable (<5 km/h if realistic speed ON)
- [ ] Mean distance accuracy is documented

---

## 📞 **Troubleshooting**

### **Problem: No CSV/JSON files generated**

**Solution:**
- Check console for error messages
- Ensure vehicles reached at least one waypoint
- Increase number of simulation steps

### **Problem: Speed errors are very high (>10 km/h)**

**Solution:**
- Make sure "Use Realistic Speed from Dataset" is **checked**
- Verify dataset has `speed_kmh_source` and `speed_kmh_destination` columns
- Run `check_speed_data.py` to validate

### **Problem: Only 1-2 waypoints in CSV**

**Solution:**
- Increase simulation steps (3000 → 5000)
- Reduce number of waypoints (to ensure vehicles reach them)
- Check vehicle routes are long enough

---

## 🎉 **Summary**

You now have a **complete analysis system** that:

1. ✅ Uses **realistic speeds** from GPS dataset
2. ✅ Generates **per-waypoint CSV** with distance & speed data
3. ✅ Generates **overall JSON summary** with accuracy metrics
4. ✅ Saves **all files to main project folder**
5. ✅ Displays **comprehensive console report**
6. ✅ Enables **easy comparison** of realistic vs constant speed
7. ✅ Provides **detailed error analysis** for both distance and speed

**Run it now:**
```bash
python v2v_realistic_speed_simulation.py
```

🚗 **Happy simulating!**

