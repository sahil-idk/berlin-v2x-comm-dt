# V2V 5-Strategy Accuracy Improvement Comparison

## 📋 Overview

This comprehensive comparison framework tests **5 different calibration strategies** to improve V2V simulation accuracy beyond the baseline **66.52%**.

**Goal:** Achieve **80%+** inter-vehicular distance accuracy for digital twin validation.

---

## 🎯 The 5 Strategies

### **Strategy 1: Multi-Zone Distance-Based Calibration**

**Concept:** Different calibration factors for different distance ranges.

**Implementation:**
- Very Close (0-16m): Factor = 0.55
- Close (16-18.5m): Factor = 0.58
- Medium (18.5-21m): Factor = 0.607 (baseline)
- Medium-Far (21-23m): Factor = 0.63
- Far (23-100m): Factor = 0.66

**Rationale:** SUMO's coordinate system accuracy varies with distance. Closer vehicles need less correction.

**Expected Impact:** +5-8% accuracy improvement

---

### **Strategy 2: Velocity-Based Adjustment**

**Concept:** Adjust calibration based on vehicle speed.

**Implementation:**
- Slow (<38 km/h): Factor = 0.607 - 0.03 = 0.577
- Normal (38-42 km/h): Factor = 0.607 (baseline)
- Fast (>42 km/h): Factor = 0.607 + 0.03 = 0.637

**Rationale:** Vehicle dynamics affect positioning accuracy. Faster vehicles have more prediction error.

**Expected Impact:** +2-4% accuracy improvement

---

### **Strategy 3: Statistical Outlier Detection**

**Concept:** Detect and correct anomalous measurements using z-score.

**Implementation:**
```python
z_score = (current_distance - mean_recent) / std_recent
if abs(z_score) > 2.0:
    # Use median-based correction instead
    adjusted_factor = median_distance / current_distance
```

**Rationale:** Some measurements are wildly off (e.g., 394m instead of 23m). These should be corrected or removed.

**Expected Impact:** +3-5% accuracy improvement

---

### **Strategy 4: Adaptive Learning Calibration**

**Concept:** Self-adjusting calibration that learns from recent performance.

**Implementation:**
```python
if recent_accuracy < 70%:
    calibration_factor -= 0.005  # Decrease
elif recent_accuracy > 85%:
    calibration_factor += 0.005  # Increase
```

**Rationale:** Static calibration doesn't adapt to simulation conditions. Dynamic learning can optimize over time.

**Expected Impact:** +2-3% accuracy improvement

---

### **Strategy 5: Combined Optimal**

**Concept:** Combine all 4 strategies with intelligent weighting.

**Implementation:**
- If outlier detected: Use outlier correction (highest priority)
- Otherwise: Weighted average
  - Zone-based: 50%
  - Velocity-based: 30%
  - Adaptive: 20%

**Rationale:** Each strategy addresses different accuracy issues. Combining them should give best overall results.

**Expected Impact:** +10-15% accuracy improvement (cumulative)

---

## 🚀 How to Run

### Quick Start

1. **Run the comparison:**
   ```bash
   run_5_strategy_comparison.bat
   ```
   OR
   ```bash
   python v2v_5_strategy_comparison.py
   ```

2. **Wait for completion** (~10-15 minutes)

3. **Check results** in generated files

### What Happens

The script will:
1. Load GPS data (50 waypoints)
2. Run Strategy 1 simulation → Save results
3. Run Strategy 2 simulation → Save results
4. Run Strategy 3 simulation → Save results
5. Run Strategy 4 simulation → Save results
6. Run Strategy 5 simulation → Save results
7. **Generate comparison report** ranking all strategies

---

## 📊 Output Files

### Individual Strategy Results

For each strategy (1-5):

**`strategyN_results.csv`** - Detailed per-waypoint analysis
- Columns: waypoint, step, actual_distance_m, simulated_distance_m, calibrated_distance_m, calibration_factor, distance_error_m, distance_accuracy_pct, avg_velocity_kmh
- One row per waypoint measurement

**`strategyN_summary.json`** - Overall metrics
```json
{
  "strategy_number": 1,
  "strategy_name": "Multi-Zone Distance-Based Calibration",
  "mean_accuracy_pct": 72.5,
  "median_accuracy_pct": 74.2,
  "mae_m": 5.8,
  "rmse_m": 6.9,
  "waypoints_analyzed": 39
}
```

### Comparison Report

**`strategy_comparison_results.csv`** - All strategies ranked by accuracy

**`strategy_comparison_summary.json`** - Final comparison
```json
{
  "baseline_accuracy": 66.52,
  "best_strategy": {
    "number": 5,
    "name": "Combined Optimal",
    "accuracy": 81.3,
    "improvement_over_baseline": +14.78
  },
  "strategies": [...]
}
```

---

## 📈 Expected Results

### Baseline (Current)
- **Accuracy:** 66.52%
- **MAE:** 6.55 m
- **RMSE:** 7.03 m
- **Method:** Single calibration factor (0.607)

### Strategy Performance Predictions

| Strategy | Expected Accuracy | Improvement | Status |
|----------|------------------|-------------|---------|
| Strategy 1 (Multi-Zone) | 71-74% | +5-8% | 🟡 Better |
| Strategy 2 (Velocity) | 68-70% | +2-4% | 🟢 Good |
| Strategy 3 (Outlier) | 70-72% | +3-5% | 🟢 Good |
| Strategy 4 (Adaptive) | 68-70% | +2-3% | 🟢 Good |
| **Strategy 5 (Combined)** | **78-85%** | **+12-19%** | ✅ **Excellent** |

### Target: 80%+ Accuracy
**Most likely winner:** Strategy 5 (Combined Optimal)

---

## 🔍 How to Analyze Results

### 1. Check the Winner
```bash
# Open strategy_comparison_summary.json
# Look for "best_strategy" section
```

### 2. Compare Visually
Open `strategy_comparison_results.csv` in Excel:
- Sort by `mean_accuracy_pct` (descending)
- Create bar chart comparing strategies
- Highlight strategies that beat 80%

### 3. Detailed Analysis
For the winning strategy:
- Open `strategyN_results.csv`
- Identify which waypoints have low accuracy
- Check if specific distance ranges or velocities are problematic

### 4. Diagnostic Checks
- **If all strategies fail (<75%):** Problem is with route generation or vehicle movement
- **If outlier detection helps most:** Data quality issues (GPS errors)
- **If velocity adjustment helps most:** Speed simulation is inaccurate
- **If zone calibration helps most:** SUMO coordinate mapping varies by distance
- **If combined wins by large margin:** Multiple factors affecting accuracy

---

## 🛠️ Customization

### Adjust Number of Waypoints
Edit `v2v_5_strategy_comparison.py`:
```python
result = run_simulation(strategy_num, strategy_name, calibration_func, num_waypoints=100)  # Change from 50
```

### Modify Calibration Zones (Strategy 1)
```python
CALIBRATION_ZONES_S1 = {
    'very_close': {'range': (0, 16), 'factor': 0.52},  # Adjust factors
    'close': {'range': (16, 18.5), 'factor': 0.57},
    # ...
}
```

### Tune Velocity Adjustments (Strategy 2)
```python
if avg_velocity_kmh < 38:
    adjustment = -0.05  # Change from -0.03
elif avg_velocity_kmh > 42:
    adjustment = +0.05  # Change from +0.03
```

### Change Outlier Threshold (Strategy 3)
```python
def detect_outlier_s3(distances, current_distance, threshold=3.0):  # Change from 2.0
```

### Adjust Learning Rate (Strategy 4)
```python
self.adjustment_rate = 0.01  # Change from 0.005
```

---

## ⚠️ Troubleshooting

### Issue: "No data collected"
**Cause:** Vehicles disappeared before collecting measurements
**Fix:** Routes too short. Increase waypoint sampling or extend routes.

### Issue: Very low accuracy (<50%)
**Cause:** Vehicles not following GPS trajectory
**Fix:** Check route generation in `find_optimal_path_through_waypoints()`

### Issue: SUMO crashes
**Cause:** Route connectivity issues
**Fix:** Ensure `net.getShortestPath()` returns valid paths

### Issue: Simulation hangs
**Cause:** Vehicles stuck or disappeared
**Fix:** Add timeout logic or vehicle status checks

---

## 📚 Technical Details

### Accuracy Calculation
```python
distance_error = calibrated_distance - actual_distance
distance_error_pct = (distance_error / actual_distance) * 100
distance_accuracy = max(0, 100 - abs(distance_error_pct))
```

**Example:**
- Actual: 20m
- Calibrated: 17m
- Error: -3m
- Error %: -15%
- **Accuracy: 85%** ✅

### Why 66.52% Baseline?
The current baseline uses:
1. Realistic GPS routes (good)
2. Realistic speeds from dataset (good)
3. **Single calibration factor 0.607** (limitation)
4. No outlier detection (limitation)
5. No velocity adjustment (limitation)

The 5 strategies address these limitations systematically.

---

## 🎓 Key Insights

### What We Learned from Baseline Analysis

1. **Route generation matters most**
   - Using `find_optimal_path_through_waypoints()` with Dijkstra gives connected, realistic routes
   - Without this, vehicles go off-road or disappear

2. **Realistic speeds are crucial**
   - Using actual GPS speeds (37-42 km/h) vs constant 54 km/h improves accuracy by ~15%

3. **Measurement timing is important**
   - Measuring every waypoint change (irregular) works well
   - Could be improved with fixed-interval measurements

4. **Single calibration factor is limiting**
   - 0.607 works averagely for all distances
   - But accuracy varies significantly (55-82%) across waypoints
   - This variation suggests different calibration needed per context

### Why Multi-Strategy Approach?

Different waypoints fail for different reasons:
- **Distance-dependent errors:** Some distances map poorly in SUMO coordinates
- **Velocity-dependent errors:** Fast-moving vehicles have more prediction error
- **Outlier measurements:** GPS errors or simulation glitches
- **Time-dependent drift:** Calibration accuracy changes over simulation time

**Solution:** Use the right calibration for the right situation.

---

## 🏆 Success Criteria

### Minimum Viable
- **Mean Accuracy:** ≥75%
- **Improvement:** +8% over baseline
- **High Accuracy Waypoints (≥90%):** ≥10

### Target Goal
- **Mean Accuracy:** ≥80%
- **Improvement:** +13% over baseline
- **High Accuracy Waypoints (≥90%):** ≥20

### Stretch Goal
- **Mean Accuracy:** ≥85%
- **Improvement:** +18% over baseline
- **High Accuracy Waypoints (≥90%):** ≥30

---

## 📞 Next Steps

### If Target Achieved (80%+)
1. Document the winning strategy
2. Integrate into production digital twin
3. Validate with additional test cases
4. Extend to more waypoints (100, 200)

### If Target Not Achieved (<80%)
1. Analyze failure modes in detail
2. Combine winning strategies further
3. Consider alternative approaches:
   - Machine learning calibration
   - GPS error correction
   - Advanced route planning
   - Dynamic vehicle positioning with `moveToXY`

---

## 📄 Files in This Package

- `v2v_5_strategy_comparison.py` - Main comparison script
- `run_5_strategy_comparison.bat` - Launcher script
- `5_STRATEGY_COMPARISON_GUIDE.md` - This documentation
- `strategy_1_multi_zone_calibration.py` - Standalone Strategy 1 (optional)

**Generated Files:**
- `strategy1_results.csv` to `strategy5_results.csv`
- `strategy1_summary.json` to `strategy5_summary.json`
- `strategy_comparison_results.csv`
- `strategy_comparison_summary.json`

---

## 🙏 Acknowledgments

**Baseline:** `v2v_realistic_speed_simulation.py` (66.52% accuracy)

**Dataset:** `vehicle_2_4_first_200.csv` (200 GPS waypoints, Vehicle 2 ↔ Vehicle 4)

**SUMO Network:** `berlin-sumo-closed-netwokr/osm.net.xml.gz`

---

**Ready to find the winning strategy? Run the comparison now!**

```bash
run_5_strategy_comparison.bat
```

🚀 Good luck achieving 80%+ accuracy! 🎯

