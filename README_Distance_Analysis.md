# V2V Simulation with Distance Accuracy Analysis

## Overview

This enhanced V2V simulation system provides comprehensive distance accuracy analysis comparing simulated inter-vehicle distances with actual GPS-derived distances for each waypoint in the dataset.

## Key Features

### ✅ **Vehicle Simulation**
- **Route-based navigation** (no more vehicle disappearance!)
- **3D car visualization** (blue source, red destination vehicles)
- **GPS waypoint POIs** (blue/red dots for visualization)
- **Dynamic speed control** based on waypoint proximity

### ✅ **Distance Accuracy Analysis**
- **Per-waypoint comparison** of simulated vs actual distances
- **Comprehensive metrics**: MAE, RMSE, correlation coefficient
- **Accuracy distribution** analysis (high/medium/low accuracy categories)
- **Best/worst waypoint** identification
- **Statistical analysis** with detailed reporting

### ✅ **GUI Controls** (Enhanced Version)
- **Adjustable waypoints** (5-100 range)
- **Speed control** (5-30 m/s)
- **Simulation speed** control (0.1-5.0x)
- **Real-time status** and progress tracking

## Files Overview

### Core Simulation Scripts
- `v2v_simple_robust.py` - **Main simulation script** with distance analysis
- `v2v_enhanced_robust.py` - **GUI version** with Tkinter controls
- `run_enhanced_v2v.bat` - Launcher for GUI version

### Analysis Scripts
- `analyze_distance_accuracy.py` - **Distance accuracy analysis** and visualization
- `run_analysis.bat` - Launcher for analysis

### Output Files
- `distance_accuracy_analysis.csv` - **Detailed per-waypoint analysis**
- `distance_accuracy_summary.json` - **Summary statistics**
- `distance_accuracy_analysis.png` - **Visualization plots**
- `detailed_accuracy_analysis.png` - **Additional analysis plots**
- `distance_accuracy_report.txt` - **Comprehensive report**

## Usage

### 1. Run Basic Simulation
```bash
python v2v_simple_robust.py
```

### 2. Run GUI Simulation
```bash
python v2v_enhanced_robust.py
# or
run_enhanced_v2v.bat
```

### 3. Analyze Results
```bash
python analyze_distance_accuracy.py
# or
run_analysis.bat
```

## Distance Analysis Features

### 📊 **Comprehensive Metrics**
- **Mean Error**: Average difference between simulated and actual distances
- **Mean Absolute Error (MAE)**: Average absolute difference
- **Root Mean Square Error (RMSE)**: Square root of mean squared errors
- **Correlation Coefficient**: How well simulated distances correlate with actual
- **Accuracy Percentage**: 100% - |error_percentage|

### 📈 **Visualizations**
1. **Actual vs Simulated Distance Scatter Plot**
   - Shows correlation between actual and simulated distances
   - Includes perfect correlation line for reference
   - Displays correlation coefficient

2. **Error Distribution Histogram**
   - Shows distribution of errors across waypoints
   - Highlights mean error

3. **Accuracy by Waypoint Bar Chart**
   - Color-coded accuracy (green ≥70%, orange 0-70%, red <0%)
   - Shows accuracy threshold lines

4. **Error Percentage Distribution**
   - Shows distribution of error percentages
   - Helps identify systematic biases

5. **Distance Comparison Over Waypoints**
   - Line plot comparing actual vs simulated distances
   - Shows trends over waypoint sequence

6. **Cumulative Accuracy Analysis**
   - Shows how accuracy improves with best-performing waypoints

### 📋 **Detailed Analysis**
- **Accuracy Categories**: High (≥90%), Medium (70-89%), Low (<70%)
- **Best/Worst Waypoints**: Identifies most and least accurate waypoints
- **Distance Range Analysis**: Accuracy by distance ranges
- **Statistical Measures**: Standard deviation, median, etc.
- **Recommendations**: Based on overall accuracy performance

## Sample Output

```
======================================================================
DISTANCE ACCURACY ANALYSIS
======================================================================
📊 Distance Analysis Results:
   Total waypoints analyzed: 50
   Mean Error: 80.57 m
   Mean Absolute Error: 81.61 m
   Root Mean Square Error: 104.86 m
   Mean Error Percentage: 431.00%
   Mean Absolute Error Percentage: 436.27%
   Mean Accuracy: -336.27%

📊 Best Waypoint (Most Accurate):
   Waypoint 0: Actual=23.07m, Simulated=30.37m, Error=7.30m (31.66%)

📊 Worst Waypoint (Least Accurate):
   Waypoint 33: Actual=19.78m, Simulated=255.19m, Error=235.41m (1190.13%)

📊 Accuracy Distribution:
   High Accuracy (≥90%): 0 waypoints (0.0%)
   Medium Accuracy (70-89%): 0 waypoints (0.0%)
   Low Accuracy (<70%): 50 waypoints (100.0%)
```

## Technical Implementation

### Distance Analysis Algorithm
1. **Waypoint Matching**: For each GPS waypoint, find the simulation step where vehicles were closest
2. **Distance Extraction**: Get simulated inter-vehicle distance at that step
3. **Error Calculation**: Compare with actual GPS-derived distance
4. **Accuracy Metrics**: Calculate error percentage and accuracy
5. **Statistical Analysis**: Compute comprehensive statistics

### Key Functions
- `calculate_distance()`: Euclidean distance between two positions
- `find_optimal_path_through_waypoints()`: Route planning through GPS waypoints
- `analyze_distance_accuracy()`: Comprehensive analysis and visualization

## Calibration and Improvement

### Current Issues Identified
- **High error rates** in current implementation
- **Systematic overestimation** of distances
- **Route planning** may not follow GPS trajectories closely enough

### Potential Improvements
1. **Apply calibration factor** (0.607) to simulated distances
2. **Improve route planning** to better follow GPS trajectories
3. **Use moveToXY with higher matchThreshold** for more precise positioning
4. **Implement waypoint proximity detection** for better matching

## Data Files

### Input
- `vehicle_2_4_first_200.csv` - GPS trajectory data with actual distances

### Output
- `distance_accuracy_analysis.csv` - Per-waypoint analysis results
- `distance_accuracy_summary.json` - Summary statistics
- `distance_accuracy_analysis.png` - Main visualization
- `detailed_accuracy_analysis.png` - Additional analysis plots
- `distance_accuracy_report.txt` - Comprehensive text report

## Requirements

- Python 3.x
- SUMO 1.23.1+
- Required packages: pandas, matplotlib, numpy, traci, sumolib, tkinter

## Next Steps

1. **Apply calibration factor** to improve accuracy
2. **Implement better route planning** algorithms
3. **Add communication parameter analysis** (SNR, RSRP)
4. **Create batch processing** for multiple datasets
5. **Add real-time accuracy monitoring** in GUI

---

**The system now provides comprehensive distance accuracy analysis, helping you validate and improve your V2V simulation accuracy!** 🎯
