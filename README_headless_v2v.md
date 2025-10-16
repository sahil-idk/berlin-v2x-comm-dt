# Headless V2V Distance Validation

This approach validates inter-vehicle distance calculations in SUMO simulations without requiring GUI visualization.

## Overview

The headless V2V simulation compares actual GPS distances from the dataset with simulated distances computed by SUMO, providing accuracy validation for vehicle-to-vehicle communication parameters.

## Files Included

### Core Scripts

1. **headless_v2v_distance_validation.py**
   - Main validation script that runs SUMO simulations
   - Converts GPS coordinates to SUMO positions
   - Compares real vs simulated inter-vehicle distances
   - Reports accuracy metrics

2. **create_headless_config.py**
   - Creates optimized SUMO configuration for headless operation
   - Removes GUI dependencies
   - Optimizes performance for background simulation

3. **run_headless_v2v.bat**
   - Windows batch script to automate the validation process
   - Creates headless config and runs validation

## Dataset Integration

### sidelink_parsed.csv Structure

The validation uses the following columns from `sidelink_parsed.csv`:
- `timestamp`: Time of the measurement
- `Latitude_source`, `Longitude_source`: GPS coordinates of source vehicle
- `Latitude_destination`, `Longitude_destination`: GPS coordinates of destination vehicle
- `Source`, `Destination`: Vehicle identifiers

## How It Works

### Step 1: Data Selection
1. Reads the sidelink_parsed.csv dataset
2. Filters for valid GPS coordinates and different source/destination pairs
3. Randomly selects 10 timestamps for validation (configurable)

### Step 2: GPS to SUMO Mapping
1. Converts GPS coordinates to SUMO simulation coordinates
2. Finds closest SUMO edges to each GPS position
3. Calculates actual geographic distance using Haversine formula

### Step 3: SUMO Simulation
1. Runs SUMO in headless mode using the osm.sumocfg configuration
2. Computes inter-vehicle distances within the SUMO simulation environment
3. Uses vehicle positions on mapped edges

### Step 4: Accuracy Validation
1. Compares real GPS distances with SUMO simulated distances
2. Calculates error metrics for each sample
3. Generates comprehensive accuracy report

## Running the Validation

### Prerequisites

Make sure SUMO is installed and configured:
```bash
# SUMO should be in PATH
sumo --version
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Execute Validation

#### Option 1: Run manually
```bash
python create_headless_config.py
python headless_v2v_distance_validation.py
```

#### Option 2: Run using batch script (Windows)
```cmd
run_headless_v2v.bat
```

## Output

The script generates several output files:

### 1. distance_validation_results_[timestamp].json
Detailed results in JSON format including:
- Statistical summaries
- Individual sample results
- GPS coordinates
- Error metrics

### 2. distance_validation_summary_[timestamp].txt
Human-readable summary report:
- Overall accuracy statistics
- Sample-by-sample breakdown
- Error analysis

### 3. sumo-config/osm_headless.sumocfg
Headless-optimized SUMO configuration

## Configuration Options

Customize the validation by modifying these parameters in `headless_v2v_distance_validation.py`:

```python
class HeadlessV2VDistanceValidator:
    def __init__(self, sumo_config_path="sumo-config/osm_headless.sumocfg", debug=False):
        # ...
    
    def run_distance_validation(self, csv_path="sidelink_parsed.csv", num_samples=10):
        # num_samples: Number of random timestamps to validate
```

## Understanding the Results

### Accuracy Metrics

1. **Mean/M median Error**: Average distance error across samples
2. **Accuracy Percentage**: How close simulated distances are to real distances
3. **Standard Deviation**: Consistency of accuracy across samples

### Good vs Poor Accuracy Examples

- High Accuracy (90%+): Simulated distances closely match GPS distances
- Poor Accuracy (<80%): Significant mismatch indicates mapping issues

### Troubleshooting

Common issues and solutions:

#### GPS Conversion Failures
- Issue: "GPS conversion failed"
- Solution: Check SUMO network file exists and is readable

#### Edge Finding Failures  
- Issue: No edges found for GPS positions
- Solution: Verify GPS coordinates are within network bounds

#### SUMO Connection Issues
- Issue: "Failed to start SUMO"
- Solution: Verify SUMO installation and config files

## API Usage

```python
from headless_v2v_distance_validation import HeadlessV2VDistanceValidator

validator = HeadlessV2VDistanceValidator(debug=True)
stats = validator.run_distance_validation("sidelink_parsed.csv", num_samples=10)
```

## Future Extensions

This validation forms the basis for communication parameter analysis:

1. **Propagation Models**: Use validated distances in fading/loss calculations
2. **Throughput Estimation**: Couple distance with RSRP/SNR data
3. **Real-time Adaptation**: Move to dynamic positioning updates

## Notes

- The simulation runs completely in the background (no GUI required)
- All accuracy values are logged and saved for analysis
- The approach validates mapping accuracy before communication modeling
- Designed to be repeatable and statistically robust

Dive confidently into extending this validated foundation for V2V communication research!
