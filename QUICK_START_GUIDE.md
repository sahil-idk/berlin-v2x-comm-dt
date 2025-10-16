# V2V Simulation - Quick Start Guide

## 🚀 Getting Started in 3 Steps

### 1. **Basic Simulation** (Route-based, stable)
```bash
python v2v_simple_robust.py
```
**Features**: Stable vehicles, no disappearance, basic distance analysis
**Best for**: Understanding the baseline system

### 2. **Calibrated Simulation** (All improvements)
```bash
python v2v_calibrated_simulation.py
# or
run_calibrated_simulation.bat
```
**Features**: All 4 improvements applied, precise positioning, waypoint tracking
**Best for**: Accurate distance validation

### 3. **Analyze Results**
```bash
python analyze_distance_accuracy.py
```
**Generates**: Plots, CSV reports, accuracy statistics
**Best for**: Understanding performance

## 📊 What You Get

### Output Files:
- `distance_accuracy_analysis.csv` - Per-waypoint detailed data
- `distance_accuracy_summary.json` - Summary statistics
- `distance_accuracy_analysis.png` - Visualization plots
- `calibrated_distance_analysis.csv` - Calibrated analysis
- `calibrated_simulation_summary.json` - Calibrated summary

### Key Metrics:
- **Mean Absolute Error**: Distance accuracy in meters
- **RMSE**: Root mean square error
- **Accuracy Percentage**: How close simulated matches actual
- **Waypoint Progress**: How many waypoints vehicles reached

## 🎯 Four Key Improvements Explained

### 1️⃣ **Calibration Factor (0.607)**
**What**: Corrects systematic distance overestimation
**How**: Multiplies all distances by 0.607
**Result**: 39% reduction in distance values

### 2️⃣ **Improved Route Planning**
**What**: Better follows GPS trajectories
**How**: Samples waypoints, uses Dijkstra routing
**Result**: Vehicles follow recorded paths more closely

### 3️⃣ **moveToXY with High Threshold**
**What**: Precise vehicle positioning
**How**: `matchThreshold=500`, `keepRoute=2`
**Result**: Vehicles don't disappear, move to exact GPS points

### 4️⃣ **Waypoint Proximity Detection**
**What**: Smart waypoint progression
**How**: 30m threshold, automatic advancement
**Result**: Intelligent trajectory following

## 📈 Performance Comparison

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Mean Accuracy | -336% | -192% | **44%** ✅ |
| Mean Abs Error | 81.6m | 67.4m | **17%** ✅ |
| RMSE | 104.9m | 72.9m | **31%** ✅ |
| Calibration | ❌ | ✅ | Applied |
| moveToXY | ❌ | ✅ | Active |
| Proximity Detect | ❌ | ✅ | 30m threshold |

## 🔧 Configuration Options

### In `v2v_calibrated_simulation.py`:

```python
# Adjust these parameters:
NUM_WAYPOINTS = 30           # Number of waypoints to simulate
CALIBRATION_FACTOR = 0.607   # Distance calibration
PROXIMITY_THRESHOLD = 30     # Waypoint detection (meters)
MATCH_THRESHOLD = 500        # moveToXY flexibility (meters)
sample_interval = 3          # Route planning density
```

## 🎮 Controls & Usage

### Basic Simulation:
- Launches SUMO-GUI automatically
- Blue vehicle = Source (Vehicle 2)
- Red vehicle = Destination (Vehicle 4)
- Semi-transparent dots = GPS waypoints
- Close GUI window to end

### Calibrated Simulation:
- Same as basic, plus:
- Vehicles move via moveToXY
- Real-time waypoint tracking
- Proximity-based progression
- Press Ctrl+C to stop

### Analysis Tool:
- Generates plots automatically
- Creates CSV reports
- Shows accuracy distribution
- Provides recommendations

## 📁 File Organization

```
berlin_v2x/
├── v2v_simple_robust.py           # Basic simulation
├── v2v_calibrated_simulation.py   # Calibrated (all improvements)
├── v2v_enhanced_robust.py         # GUI version with controls
├── analyze_distance_accuracy.py   # Analysis tool
├── run_calibrated_simulation.bat  # Easy launcher
├── run_analysis.bat               # Analysis launcher
├── README_Distance_Analysis.md    # Full documentation
├── IMPROVEMENTS_SUMMARY.md        # Technical details
└── QUICK_START_GUIDE.md          # This file

berlin-sumo-closed-netwokr/
├── osm.net.xml.gz                 # Road network
├── osm.sumocfg                    # SUMO config
├── v2v_calibrated_routes.rou.xml # Generated routes
├── calibrated_distance_analysis.csv # Results
└── calibrated_simulation_summary.json # Summary
```

## 🔍 Troubleshooting

### Issue: "Connection closed by SUMO"
**Solution**: Normal for moveToXY simulations, GUI will still work

### Issue: "Vehicles not visible"
**Check**: 
- Are blue/red dots visible? (waypoints)
- Zoom in to vehicle area
- Check simulation is running (bottom bar)

### Issue: "No analysis file found"
**Solution**: Run simulation first to generate data

### Issue: "Low accuracy results"
**Explanation**: Expected, current system achieves -192% (improvement over -336%)
**Next steps**: See recommendations in IMPROVEMENTS_SUMMARY.md

## 💡 Tips for Best Results

1. **Start with basic simulation** to understand the system
2. **Use calibrated version** for actual validation
3. **Run analysis tool** to see detailed metrics
4. **Check waypoint dots** to verify GPS coverage
5. **Watch console output** for real-time progress
6. **Compare CSV files** to track improvements

## 📚 Additional Resources

- **Full Documentation**: `README_Distance_Analysis.md`
- **Technical Details**: `IMPROVEMENTS_SUMMARY.md`
- **Original Plan**: `plan.md`
- **Dataset**: `vehicle_2_4_first_200.csv`

## 🎯 Quick Commands Reference

```bash
# Run basic simulation
python v2v_simple_robust.py

# Run calibrated simulation (recommended)
python v2v_calibrated_simulation.py

# Run GUI version with controls
python v2v_enhanced_robust.py

# Analyze results
python analyze_distance_accuracy.py

# Using batch files (Windows)
run_calibrated_simulation.bat
run_enhanced_v2v.bat
run_analysis.bat
```

## ✅ Expected Outcomes

### After Basic Simulation:
- CSV file with distance analysis
- JSON summary with statistics
- Console output showing progress
- Vehicles visible in SUMO-GUI

### After Calibrated Simulation:
- Improved accuracy metrics (17-31% better)
- Waypoint completion tracking
- Calibrated distance values
- Real-time position updates

### After Analysis:
- 6 visualization plots
- Detailed accuracy report
- Recommendations for improvement
- Statistical analysis

## 🚦 Success Indicators

✅ **Good Signs**:
- Vehicles appear in GUI
- Blue/red dots visible on roads
- Console shows waypoint progress
- CSV files generated
- Accuracy improving over time

⚠️ **Watch For**:
- Vehicles disappearing (use calibrated version)
- "Connection closed" errors (normal, ignore)
- Very low accuracy (<-300%) - needs tuning
- No waypoint progress - check proximity threshold

## 🎓 Learning Path

1. **Day 1**: Run basic simulation, understand output
2. **Day 2**: Run calibrated version, compare results
3. **Day 3**: Analyze data, review plots
4. **Day 4**: Adjust parameters, re-run
5. **Day 5**: Review improvements documentation

---

**Ready to start? Run:** `python v2v_calibrated_simulation.py`

**Need help? Check:** `IMPROVEMENTS_SUMMARY.md` for detailed explanations
