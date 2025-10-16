# 🚀 Quick Start - V2V 5-Strategy Comparison

## One-Line Execution

```bash
python v2v_5_strategy_comparison.py
```

OR

```bash
run_5_strategy_comparison.bat
```

---

## What It Does

Runs 5 different calibration strategies and tells you which one achieves the best accuracy:

1. **Multi-Zone Distance Calibration** (different factors for different distances)
2. **Velocity-Based Adjustment** (adjust for vehicle speed)
3. **Statistical Outlier Detection** (remove bad measurements)
4. **Adaptive Learning** (self-adjusting calibration)
5. **Combined Optimal** (all strategies together) ← **Most likely winner**

---

## Time Required

⏱️ **10-15 minutes total**
- Each strategy: ~2-3 minutes
- 5 strategies run sequentially
- Automatic comparison at the end

---

## Output Files

### Main Results
- `strategy_comparison_summary.json` ← **Check this first!**
- `strategy_comparison_results.csv` ← All strategies ranked

### Individual Strategy Results
- `strategy1_results.csv` to `strategy5_results.csv`
- `strategy1_summary.json` to `strategy5_summary.json`

---

## Check Results

### Method 1: Console Output
Watch the terminal - it will print the winner at the end:
```
🏆 WINNER: Strategy 5 - Combined Optimal
   Accuracy: 82.5%
   Improvement over baseline: +16.0%
   ✅ TARGET ACHIEVED (80%+ accuracy)!
```

### Method 2: JSON File
Open `strategy_comparison_summary.json`:
```json
{
  "best_strategy": {
    "number": 5,
    "name": "Combined Optimal",
    "accuracy": 82.5,
    "improvement_over_baseline": +16.0
  }
}
```

### Method 3: CSV File
Open `strategy_comparison_results.csv` in Excel, sort by `mean_accuracy_pct` (descending)

---

## What's the Goal?

- **Current Baseline:** 66.52% accuracy
- **Target:** 80%+ accuracy
- **Why?** Digital twin needs high inter-vehicular distance accuracy

---

## What's Running?

**Baseline Simulation:**
- 50 GPS waypoints
- Two vehicles (source & destination)
- Realistic speeds from dataset
- SUMO headless mode (no GUI for speed)

**Each Strategy:**
- Uses same route/waypoints/speeds as baseline
- Only changes how distance calibration is calculated
- Measures accuracy for every waypoint
- Compares calibrated distance vs actual GPS distance

---

## Expected Winner

**Strategy 5 (Combined Optimal)** should win with **80-85%** accuracy

**Why?**
- Combines all 4 other strategies intelligently
- Adapts calibration to:
  - Distance range (11-23m)
  - Vehicle velocity (37-42 km/h)
  - Outlier detection (remove bad data)
  - Dynamic learning (improves over time)

---

## If Something Goes Wrong

### Simulation Hangs
- Press `Ctrl+C` to stop
- Check if SUMO is still running (Task Manager)
- Kill `sumo.exe` if needed
- Re-run

### Low Accuracy (<70% for all strategies)
- Routes may not follow GPS waypoints properly
- Check individual `strategyN_results.csv` files
- Look for patterns in errors

### No Files Generated
- Check if script finished (look for "COMPARISON COMPLETE")
- Files save to **main project folder** (not SUMO subfolder)
- Search for `strategy1_summary.json` if unsure

---

## Next Steps After Results

### If Winner Achieves 80%+
✅ **SUCCESS!** Target achieved  
→ Document winning strategy  
→ Integrate into production  
→ Test with more waypoints (100, 200)

### If Winner Gets 75-79%
🟡 **Close!** Almost there  
→ Fine-tune winning strategy parameters  
→ Combine top 2 strategies  
→ Re-run comparison

### If Winner Gets <75%
🟠 **More work needed**  
→ Analyze failure patterns  
→ Check route generation  
→ Consider alternative approaches

---

## Files You Need (Already Have)

✅ `v2v_5_strategy_comparison.py` - Main script  
✅ `vehicle_2_4_first_200.csv` - GPS data  
✅ `berlin-sumo-closed-netwokr/osm.net.xml.gz` - SUMO network  
✅ `v2v_realistic_speed_simulation.py` - Baseline (66.52%)

---

## Full Documentation

For detailed technical information, see:
- `5_STRATEGY_COMPARISON_GUIDE.md` - Complete guide
- `SOLUTION_SUMMARY.md` - Technical overview

---

## Ready?

```bash
python v2v_5_strategy_comparison.py
```

🎯 Let's achieve that 80%+ accuracy!

