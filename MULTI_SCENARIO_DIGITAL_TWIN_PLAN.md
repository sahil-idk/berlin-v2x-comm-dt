# Multi-Scenario V2V Digital Twin - Implementation Plan

## 📋 Current Code Analysis (`v2v_communication_digital_twin.py`)

### What the Current Code Does:

1. **Data Loading**: 
   - Loads GPS waypoint data from CSV files (currently hardcoded to `vehicle_2_4_*` datasets)
   - Filters waypoints based on user-selected count
   - Checks for communication parameters (SNR, RSRP, RSSI)

2. **Route Generation**:
   - Uses SUMO network (`berlin-sumo-closed-netwokr/osm.net.xml.gz`)
   - Finds optimal paths through GPS waypoints for source and destination vehicles
   - Uses intelligent sampling to prevent SUMO crashes with large datasets
   - Creates routes that follow GPS trajectories

3. **SUMO Simulation**:
   - Creates route files (`v2v_communication_routes.rou.xml`)
   - Creates SUMO config (`v2v_communication.sumocfg`)
   - Starts SUMO-GUI with TraCI
   - Adds POIs (Points of Interest) for waypoints

4. **V2V Communication Simulation**:
   - Calculates inter-vehicular distances
   - Applies path loss models (FSPL or 3GPP Urban Macro)
   - Calculates SNR, PRR, RSRP, RSSI
   - Validates against actual GPS distances and dataset communication parameters
   - Applies calibration factors for distance accuracy

5. **Analysis & Reporting**:
   - Saves communication analysis CSV
   - Generates JSON summary with accuracy metrics
   - Displays comprehensive reports

### Key Limitations:
- **Hardcoded dataset**: Only works with `vehicle_2_4_*` CSV files
- **Single scenario**: Processes one vehicle pair at a time
- **Single network**: Uses one SUMO network for all scenarios
- **Manual selection**: User must manually select dataset from dropdown

---

## 🎯 Plan: Extend to All 6 Scenarios

### Phase 1: OSM Web Wizard Setup (Generate SUMO Networks)

For each scenario, generate SUMO network files using OSM Web Wizard:

#### OSM Web Wizard Coordinates:

| Scenario | Center Coordinates (lat lon) | Coverage Area |
|----------|------------------------------|---------------|
| **Vehicle 1 ↔ 2** | `52.505376 13.325221` | 0.028° × 0.097° |
| **Vehicle 1 ↔ 3** | `52.505698 13.326155` | 0.028° × 0.097° |
| **Vehicle 1 ↔ 4** | `52.505468 13.325938` | 0.028° × 0.097° |
| **Vehicle 2 ↔ 3** | `52.505082 13.324841` | 0.028° × 0.097° |
| **Vehicle 2 ↔ 4** | `52.505589 13.326604` | 0.028° × 0.097° |
| **Vehicle 3 ↔ 4** | `52.504503 13.324758` | 0.028° × 0.097° |

#### OSM Web Wizard Settings for Each Scenario:

1. **Position Section**:
   - Enter center coordinates (e.g., `52.505376 13.325221` for Vehicle 1-2)
   - Click "Go to" button

2. **Select Area Section**:
   - ✅ **Enable "Select Area" checkbox**
   - Draw a rectangle covering the bounds:
     - All scenarios cover approximately: Lat [52.488, 52.516], Lon [13.280, 13.378]
     - You can use the same area for all scenarios since they overlap

3. **Options Section**:
   - Duration: `3600` (1 hour) or higher
   - ✅ Add Polygons (checked)
   - ⬜ Import Public Transport (optional)
   - ⬜ Car-only Network (leave unchecked for full network)
   - ⬜ Satellite background (optional)
   - ⬜ Left Hand Traffic (unchecked for Berlin)

4. **Generate Scenario**:
   - Click "Generate Scenario" button
   - Download/extract the generated files
   - Rename the folder to match scenario (e.g., `berlin-sumo-vehicle-1-2`)

#### Expected Output Files for Each Scenario:
```
berlin-sumo-vehicle-1-2/
├── osm.net.xml.gz          # Network file
├── osm.poly.xml.gz         # Polygons/buildings
├── osm.sumocfg             # SUMO config
├── trips.trips.xml         # Trip definitions
└── ... (other generated files)
```

**Note**: Since all scenarios are in the same Berlin area, you could potentially use ONE network file for all scenarios, but separate networks ensure optimal coverage for each vehicle pair.

---

### Phase 2: Code Modifications

#### 2.1 Update Dataset Selector

**Current**:
```python
dataset_combo = ttk.Combobox(config_frame, textvariable=self.dataset_file, 
                            values=['vehicle_2_4_first_200.csv',
                                    'vehicle_2_4_continuous_200.csv',
                                    ...],
                            state='readonly', width=28)
```

**New**:
```python
# Load scenarios from scenarios_list.json
scenarios_list = []
try:
    with open('scenarios/scenarios_list.json', 'r') as f:
        scenarios_data = json.load(f)
        scenarios_list = scenarios_data['scenarios']
except:
    pass

# Build dataset options
dataset_options = []
for scenario in scenarios_list:
    dataset_options.append(f"scenarios/{scenario['name']}.csv")

dataset_combo = ttk.Combobox(config_frame, textvariable=self.dataset_file, 
                            values=dataset_options,
                            state='readonly', width=40)
```

#### 2.2 Dynamic Network Selection

**Current**:
```python
os.chdir('berlin-sumo-closed-netwokr')
net = sumolib.net.readNet('osm.net.xml.gz')
```

**New**:
```python
# Determine scenario from dataset filename
dataset_name = self.dataset_file.get()
scenario_name = os.path.basename(dataset_name).replace('.csv', '')

# Map scenario to network directory
scenario_to_network = {
    'vehicle_1_2': 'berlin-sumo-vehicle-1-2',
    'vehicle_1_3': 'berlin-sumo-vehicle-1-3',
    'vehicle_1_4': 'berlin-sumo-vehicle-1-4',
    'vehicle_2_3': 'berlin-sumo-vehicle-2-3',
    'vehicle_2_4': 'berlin-sumo-vehicle-2-4',
    'vehicle_3_4': 'berlin-sumo-vehicle-3-4',
}

network_dir = scenario_to_network.get(scenario_name, 'berlin-sumo-closed-netwokr')
os.chdir(network_dir)
net = sumolib.net.readNet('osm.net.xml.gz')
```

#### 2.3 Dynamic Vehicle ID Extraction

**Current**: Hardcoded assumption of vehicle 2 and 4

**New**: Extract from CSV or metadata
```python
# Load metadata to get vehicle IDs
metadata_file = dataset_name.replace('.csv', '_metadata.json')
with open(metadata_file, 'r') as f:
    metadata = json.load(f)
    
vehicle1_id = metadata['source_vehicle']
vehicle2_id = metadata['destination_vehicle']
```

#### 2.4 Update Analysis File Names

**Current**:
```python
csv_file = os.path.join(original_dir, 'v2v_communication_analysis.csv')
json_file = os.path.join(original_dir, 'v2v_communication_summary.json')
```

**New**:
```python
scenario_name = os.path.basename(dataset_name).replace('.csv', '')
csv_file = os.path.join(original_dir, f'{scenario_name}_communication_analysis.csv')
json_file = os.path.join(original_dir, f'{scenario_name}_communication_summary.json')
```

---

### Phase 3: Multi-Scenario Batch Processing (Optional)

Create a batch processor to run all 6 scenarios automatically:

```python
def run_all_scenarios():
    """Run digital twin for all scenarios"""
    scenarios = [
        'vehicle_1_2', 'vehicle_1_3', 'vehicle_1_4',
        'vehicle_2_3', 'vehicle_2_4', 'vehicle_3_4'
    ]
    
    for scenario in scenarios:
        print(f"\n{'='*70}")
        print(f"Processing Scenario: {scenario}")
        print(f"{'='*70}")
        
        # Run simulation for this scenario
        # (Modify existing code to accept scenario parameter)
        run_scenario(scenario)
```

---

## 📝 Implementation Steps

### Step 1: Generate SUMO Networks (OSM Web Wizard)
1. Open OSM Web Wizard
2. For each scenario:
   - Enter center coordinates from table above
   - Enable "Select Area" and draw coverage rectangle
   - Set options (Duration: 3600, Add Polygons: checked)
   - Generate scenario
   - Save to `berlin-sumo-vehicle-X-Y/` directory

### Step 2: Update Code
1. Modify `v2v_communication_digital_twin.py`:
   - Update dataset selector to load from `scenarios/` directory
   - Add dynamic network selection based on scenario
   - Extract vehicle IDs from metadata
   - Update file naming to include scenario name

### Step 3: Test Each Scenario
1. Run digital twin for each scenario individually
2. Verify:
   - Routes are generated correctly
   - Vehicles follow GPS trajectories
   - Communication parameters are calculated
   - Analysis files are saved with correct names

### Step 4: Batch Processing (Optional)
1. Create batch runner script
2. Process all scenarios sequentially
3. Generate combined analysis report

---

## 🔍 Key Considerations

### Network Coverage
- All scenarios are in the same Berlin area
- Coordinates are very close (within ~0.1°)
- **Option A**: Use one network for all scenarios (simpler)
- **Option B**: Generate separate networks for each (more accurate)

### Coordinate Precision
- OSM Web Wizard coordinates should use center points
- Coverage area is similar for all scenarios (~0.028° × 0.097°)
- Selecting area manually ensures proper coverage

### File Organization
```
berlin_v2x/
├── scenarios/
│   ├── vehicle_1_2.csv
│   ├── vehicle_1_2_metadata.json
│   ├── vehicle_1_3.csv
│   └── ...
├── berlin-sumo-vehicle-1-2/
│   ├── osm.net.xml.gz
│   └── ...
├── berlin-sumo-vehicle-1-3/
│   └── ...
└── v2v_communication_digital_twin.py (updated)
```

---

## ✅ Success Criteria

1. ✅ All 6 scenarios can be selected from dropdown
2. ✅ Each scenario loads correct CSV and network
3. ✅ Vehicles follow GPS trajectories accurately
4. ✅ Communication analysis files saved per scenario
5. ✅ Analysis includes distance, SNR, PRR accuracy metrics

---

## 🚀 Quick Start Guide

### For OSM Web Wizard:
1. Use coordinates: `52.505589 13.326604` (Vehicle 2-4 center)
2. Enable "Select Area"
3. Draw rectangle covering Berlin area
4. Generate scenario → Save as `berlin-sumo-vehicle-2-4/`
5. Repeat for other scenarios OR use same network for all

### For Code Updates:
1. Dataset selector → Load from `scenarios/` directory
2. Network selection → Map scenario name to network directory
3. Vehicle IDs → Extract from metadata JSON
4. File naming → Include scenario name in output files

---

**Next Steps**: 
1. Generate SUMO networks using OSM Web Wizard with provided coordinates
2. Update code with modifications listed above
3. Test with one scenario first (Vehicle 2-4)
4. Extend to all 6 scenarios

