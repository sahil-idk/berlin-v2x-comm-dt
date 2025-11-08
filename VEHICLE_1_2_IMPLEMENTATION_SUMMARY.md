# Vehicle 1-2 Digital Twin Implementation Summary

## 📋 What We've Created

### 1. Waypoint Visualization Script (`visualize_vehicle_1_2_waypoints.py`)

**Purpose**: Display source and destination waypoints on SUMO map before simulation

**Features**:
- Loads first 2000 waypoints from `scenarios/vehicle_1_2_first_2000.csv`
- Converts GPS coordinates to SUMO coordinates
- Adds POIs (Points of Interest) for:
  - **Blue dots** = Vehicle 1 (Source) waypoints
  - **Red dots** = Vehicle 2 (Destination) waypoints
- Adds trajectory lines connecting waypoints
- Displays statistics (distance ranges, coverage area)

**Usage**:
```bash
python visualize_vehicle_1_2_waypoints.py
```

**Output**:
- Opens SUMO-GUI with waypoints marked
- Shows vehicle trajectories
- Keeps GUI open for inspection

### 2. Digital Twin Script (`v2v_communication_digital_twin_vehicle_1_2.py`)

**Purpose**: Run V2V communication simulation for Vehicle 1-2 scenario

**Features**:
- Same functionality as `v2v_communication_digital_twin.py` but customized for Vehicle 1-2
- Uses `veh_1_2_sumo_config/` directory for SUMO network
- Loads data from `scenarios/vehicle_1_2_first_2000.csv`
- Extracts vehicle IDs from metadata (Vehicle 1 ↔ Vehicle 2)
- Generates routes through GPS waypoints
- Simulates V2V communication (distance, SNR, PRR, path loss)
- Saves analysis to `vehicle_1_2_communication_analysis.csv`

**Key Differences from Vehicle 2-4 Version**:
- Scenario-specific configuration constants
- Uses `veh_1_2_sumo_config/` network directory
- Loads Vehicle 1-2 CSV and metadata
- Output files named with `vehicle_1_2` prefix

## 📁 File Structure

```
berlin_v2x/
├── scenarios/
│   ├── vehicle_1_2.csv (full dataset - 57,381 records)
│   ├── vehicle_1_2_first_2000.csv (extracted subset)
│   └── vehicle_1_2_metadata.json
├── veh_1_2_sumo_config/
│   ├── osm.net.xml.gz (SUMO network)
│   ├── osm.sumocfg (SUMO config)
│   └── ... (other SUMO files)
├── visualize_vehicle_1_2_waypoints.py ⭐ NEW
├── v2v_communication_digital_twin_vehicle_1_2.py ⭐ NEW
└── VEHICLE_1_2_IMPLEMENTATION_SUMMARY.md (this file)
```

## 🚀 Step-by-Step Usage

### Step 1: Visualize Waypoints

First, visualize the waypoints to understand the GPS trajectory:

```bash
python visualize_vehicle_1_2_waypoints.py
```

**What happens**:
1. Loads 2000 waypoints from CSV
2. Converts GPS to SUMO coordinates
3. Opens SUMO-GUI
4. Displays:
   - Blue POIs = Vehicle 1 waypoints
   - Red POIs = Vehicle 2 waypoints
   - Trajectory lines connecting waypoints

**What to check**:
- ✅ Waypoints are visible on the map
- ✅ Trajectories follow roads in SUMO network
- ✅ Coverage area matches Berlin area
- ✅ Both vehicles' paths are distinct

### Step 2: Run Digital Twin Simulation

After verifying waypoints, run the digital twin:

```bash
python v2v_communication_digital_twin_vehicle_1_2.py
```

**GUI Configuration**:
- **Waypoints**: Adjust slider (100-2000, default: 2000)
- **Use Realistic Speed**: ✅ Checked (uses GPS speed data)
- **Apply Calibration**: ✅ Checked (0.607 factor)
- **Path Loss Model**: Select FSPL or 3GPP Urban Macro
- **Use All Waypoints**: Optional (for dense sampling)

**Click**: "Start Digital Twin Simulation"

**What happens**:
1. Loads network from `veh_1_2_sumo_config/`
2. Loads waypoints from CSV
3. Generates routes through waypoints
4. Creates SUMO vehicles (blue = Vehicle 1, red = Vehicle 2)
5. Adds waypoint POIs to map
6. Runs simulation:
   - Vehicles follow GPS trajectories
   - Calculates inter-vehicular distances
   - Computes SNR, PRR, path loss
   - Validates against actual GPS distances
7. Saves analysis to CSV

**Output Files**:
- `vehicle_1_2_communication_analysis.csv` - Detailed analysis per waypoint
- Console logs with progress and statistics

## 📊 Expected Results

### Distance Statistics
- **Actual Distance Range**: ~0.8m - 408m (from metadata)
- **Mean Distance**: ~31.4m
- **Simulated Distance**: Should match actual with calibration

### Communication Parameters
- **SNR Range**: -1.8 dB to 28.4 dB (from dataset)
- **Path Loss**: Calculated using FSPL or 3GPP model
- **PRR**: Packet Reception Rate based on SNR

### Accuracy Metrics
- Distance accuracy: Should be ~78%+ (similar to Vehicle 2-4)
- Path loss accuracy: Validated against calculated values
- SNR accuracy: Compared to dataset SNR values

## 🔍 Verification Checklist

### Before Running Simulation:
- [ ] `scenarios/vehicle_1_2_first_2000.csv` exists
- [ ] `veh_1_2_sumo_config/osm.net.xml.gz` exists
- [ ] Waypoints visualization shows valid GPS points
- [ ] SUMO network covers the waypoint area

### During Simulation:
- [ ] Both vehicles appear in SUMO-GUI
- [ ] Vehicles follow GPS waypoint trajectories
- [ ] Waypoint POIs are visible on map
- [ ] Status log shows progress updates
- [ ] Distance calculations are reasonable

### After Simulation:
- [ ] `vehicle_1_2_communication_analysis.csv` is created
- [ ] Analysis file contains waypoint data
- [ ] Distance, SNR, PRR columns are populated
- [ ] Accuracy metrics are calculated

## 🐛 Troubleshooting

### Issue: Waypoints not visible
**Solution**: 
- Check GPS coordinates are in Berlin area
- Verify SUMO network covers the area
- Try reducing `MAX_POIS_TO_DISPLAY` in visualization script

### Issue: Routes not generated
**Solution**:
- Reduce number of waypoints (try 500-1000)
- Check waypoints are near roads in SUMO network
- Increase search radius in `find_optimal_path_through_waypoints`

### Issue: SUMO crashes
**Solution**:
- Reduce waypoints to 1000 or less
- Enable "Use All Waypoints" for better sampling
- Check route complexity (should be < 50 edges)

### Issue: Vehicles don't move
**Solution**:
- Check routes are valid (non-empty)
- Verify vehicles are added to simulation
- Check for route errors in SUMO log

## 📈 Next Steps

1. **Run waypoint visualization** to verify GPS data
2. **Run digital twin** with default settings
3. **Analyze results** in CSV file
4. **Compare** with Vehicle 2-4 results
5. **Adjust parameters** if needed (calibration, sampling, etc.)
6. **Extend** to other scenarios (Vehicle 1-3, 1-4, etc.)

## 🔄 Comparison with Vehicle 2-4

| Aspect | Vehicle 2-4 | Vehicle 1-2 |
|--------|-------------|-------------|
| **Dataset Size** | 61,925 records | 57,381 records |
| **First 2000 Points** | ✅ Available | ✅ Available |
| **SUMO Network** | `berlin-sumo-closed-netwokr/` | `veh_1_2_sumo_config/` |
| **Vehicle IDs** | 2 ↔ 4 | 1 ↔ 2 |
| **Distance Range** | 0.2m - 272m | 0.8m - 408m |
| **Mean Distance** | 19.7m | 31.4m |
| **Implementation** | Original script | Adapted script |

## ✅ Success Criteria

- [x] Waypoint visualization script created
- [x] Digital twin script created for Vehicle 1-2
- [x] First 2000 points extracted from CSV
- [x] Scripts use correct SUMO config directory
- [x] Vehicle IDs extracted from metadata
- [ ] Waypoints visualized successfully
- [ ] Simulation runs without errors
- [ ] Analysis file generated correctly

## 📝 Notes

- **Same Network**: Since all scenarios are in Berlin, you could potentially use one network file for all scenarios
- **Performance**: Large waypoint counts (>1000) may slow down SUMO - use sampling
- **Calibration**: Same calibration factor (0.607) used as Vehicle 2-4 baseline
- **Extension**: This pattern can be replicated for other vehicle pairs

