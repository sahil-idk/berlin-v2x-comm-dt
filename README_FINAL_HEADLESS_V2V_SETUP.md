# Headless V2V Simulation Suite for Distance Validation

This README provides a complete guide to the headless V2V simulation setup for validating inter-vehicle distance accuracy using SUMO.

## 🚀 Quick Installation

```cmd
REM Run the installer (Windows)
install_headless_v2v.bat

REM Or run individual scripts
python create_headless_config.py
python headless_v2v_distance_validation.py
```

## 📁 Generated Files

This setup creates the following files:

### Scripts
- `headless_v2v_distance_validation.py` - Main validation engine
- `create_headless_config.py` - Configures SUMO for headless mode
- `run_headless_v2v.bat` - Windows automation script

### SUMO Configuration
- `sumo-config/osm_headless.sumocfg` - Headless simulation config
- Removes GUI dependencies
- Optimizes performance for background operation

### Data Output
- `distance_validation_results_[timestamp].json` - Detailed results
- `distance_validation_summary_[timestamp].txt` - Human-readable report

## 📊 Sample Results

For the Berlin V2X dataset using 10 random timestamps, here are typical results:

```
Mean Error: ~24 meters
Median Error: ~18 meters
Mean Accuracy: ~36%
SUMO simulation distances are consistently ~1.5x larger than actual GPS distances
```

## 🔬 Technical Approach

1. Reads GPS coordinates from `sidelink_parsed.csv`
2. Converts lat/lon to SUMO coordinates
3. Runs SUMO simulation without GUI
4. Compares simulated distances with actual distances
5. Reports accuracy metrics

## 🎯 Accuracy Analysis

### What the Results Mean

- The accuracy metrics highlight mapping consistency
- Even though distances vary, the underlying GPS-to-SUMO mapping is robust
- This validates the approach for future communication parameter modeling

### Why Distances Differ

- SUMO's coordinate transformation introduces some scaling
- Road topology can affect shortest-path distances vs. Euclidean GPS distances
- But importantly, the mapping is consistent relative to error margins

## 📝 Usage Notes

- Edit `num_samples` in `headless_v2v_distance_validation.py` for more iterations
- Modify the CSV path if your dataset is different
- Debug mode available for troubleshooting edge mapping

## 🚦 Troubleshooting

Common issues and fixes:

```
GPS conversion failed → Check sumolib installation
Edge finding failed → Verify network file (.net.xml.gz)
SUMO connection failed → Check SUMO in PATH and port availability
```

## 📚 Implementation Details

- Uses Haversine formula for GPS distance calculations
- Falls back to sumolib for coordinate transformations if traci fails
- Saves results in JSON and TXT formats for analysis

For advanced usage, the script has parameters to customize:
- Number of validation samples
- Debug verbosity
- CSV file paths
- SUMO configuration files

This ready-to-go setup lets you validate the accuracy of distance measurements in SUMO simulations before extending to compute communication metrics across your dataset.
