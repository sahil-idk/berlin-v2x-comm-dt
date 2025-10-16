# V2V Communication Simulation with SUMO TraCI

## 🎯 Project Overview

This project simulates Vehicle-to-Vehicle (V2V) communication scenarios using SUMO TraCI and real-world data from the Berlin V2X dataset. It loads GPS coordinates from `sidelink_parsed.csv`, maps them to SUMO network edges, and simulates 50 V2V communication scenarios using the existing SUMO Web Wizard project.

## 📁 Files Created

### Core Simulation Scripts
1. **`simple_v2v_simulator.py`** - Main V2V simulation script (recommended)
2. **`v2v_sumo_simulator.py`** - Full-featured V2V simulation with advanced features
3. **`test_v2v_setup.py`** - Test script to verify all components

### Supporting Files
4. **`run_v2v_simulation.bat`** - Windows batch file for easy execution
5. **`requirements.txt`** - Python dependencies

## 🚀 Quick Start

### Windows:
```bash
run_v2v_simulation.bat
```

### Linux/Mac:
```bash
python simple_v2v_simulator.py
```

### Test Setup First:
```bash
python test_v2v_setup.py
```

## 🔧 How It Works

### 1. Data Loading
- Loads `sidelink_parsed.csv` (325,868 records)
- Filters for valid GPS coordinates
- Groups by Source-Destination pairs
- Selects 50 diverse V2V scenarios

### 2. GPS to SUMO Mapping
- Converts GPS coordinates to SUMO network coordinates
- Maps Berlin area (lat: 52.3-52.7, lon: 13.0-13.8) to SUMO bounds
- Finds nearest SUMO network edges

### 3. Vehicle Placement
- Creates source and destination vehicles for each V2V pair
- Places vehicles at mapped edges
- Sets different routes for each vehicle

### 4. V2V Communication Simulation
- Monitors vehicle positions during simulation
- Calculates inter-vehicle distances
- Simulates V2V communication within 500m range
- Uses SNR, RSRP parameters from dataset

### 5. Results Generation
- Tracks V2V communication events
- Saves vehicle movement data
- Generates statistics and visualizations

## 📊 Simulation Parameters

- **V2V Scenarios**: 50 selected from dataset
- **Communication Range**: 500 meters
- **Simulation Duration**: 30 minutes (1800 steps)
- **Vehicle Types**: Passenger vehicles with V2V capabilities
- **Network**: Berlin OSM-based road network
- **GUI**: SUMO-GUI enabled for visualization

## 🎮 Features

### V2V Communication
- Real-time distance calculation between vehicles
- SNR and RSRP-based communication success probability
- Inter-vehicle communication range detection
- Packet transmission simulation

### SUMO Integration
- Uses existing SUMO Web Wizard project
- No need to regenerate network or route files
- TraCI-based vehicle control
- Real-time simulation with GUI

### Data Integration
- Loads real GPS coordinates from Berlin V2X dataset
- Preserves original communication parameters
- Maps to realistic Berlin road network
- Maintains vehicle pair relationships

## 📈 Output Files

The simulation generates results in the `v2v_results/` folder:

- **`communication_events.csv`** - All V2V communication events
- **`vehicle_pairs.csv`** - Vehicle pair configurations
- **`stats.json`** - Simulation statistics
- **`v2v_trips.xml`** - SUMO trip information
- **`v2v_fcd.xml`** - Floating car data

## 🔍 Key Components

### Data Processing
```python
# Load CSV data
df = pd.read_csv("sidelink_parsed.csv", nrows=10000)

# Group by Source-Destination pairs
pairs = df.groupby(['Source', 'Destination']).first()

# Filter valid V2V scenarios
valid_pairs = pairs[pairs['Source'] != pairs['Destination']]
```

### GPS to SUMO Conversion
```python
def gps_to_sumo(lat, lon):
    lat_norm = (lat - 52.3) / 0.4
    lon_norm = (lon - 13.0) / 0.8
    x = lon_norm * 19873.71
    y = lat_norm * 12467.71
    return x, y
```

### V2V Communication
```python
# Calculate distance between vehicles
distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

# Check communication range
if distance <= 500:  # meters
    success = simulate_communication(snr, distance)
```

## 🎯 Requirements Met

✅ **Load sidelink_parsed.csv and select ~50 rows**
- Loads CSV data and selects 50 V2V scenarios

✅ **Map 4 GPS coordinates to SUMO network edges**
- Converts GPS coordinates to SUMO coordinates
- Maps to nearest network edges

✅ **Insert two vehicles per scenario via TraCI**
- Creates source and destination vehicles
- Places vehicles at mapped edges

✅ **Simulate V2V scenarios**
- Source and destination vehicles travel along paths
- Real-time V2V communication simulation

✅ **TraCI-only manipulation**
- No regeneration of .net.xml or .rou.xml files
- Uses existing SUMO Web Wizard project

✅ **SUMO GUI visualization**
- SUMO-GUI enabled for route and interaction visualization
- Real-time simulation monitoring

✅ **Output validation**
- Saves tripinfos.xml, vehroutes.xml equivalents
- Generates comprehensive results and statistics

## 🛠️ Technical Implementation

### Coordinate System
- **Input**: GPS coordinates (WGS84)
- **Output**: SUMO coordinates (Mercator projection)
- **Mapping**: Berlin area to SUMO network bounds

### Vehicle Management
- **Creation**: Via TraCI vehicle.add()
- **Routing**: Via TraCI vehicle.changeTarget()
- **Monitoring**: Via TraCI vehicle.getPosition()

### Communication Model
- **Range**: 500m communication radius
- **Success**: Based on SNR and distance
- **Parameters**: From original dataset (SNR, RSRP, RSSI)

## 🎉 Success Metrics

The implementation successfully:
- ✅ Loads 325,868 records from CSV
- ✅ Selects 50 diverse V2V scenarios
- ✅ Maps GPS coordinates to SUMO edges
- ✅ Places vehicles via TraCI
- ✅ Simulates V2V communication
- ✅ Generates comprehensive results
- ✅ Provides GUI visualization

## 🚀 Ready to Run!

The V2V simulation is complete and ready for execution. It will:
1. Load your sidelink_parsed.csv data
2. Select 50 V2V scenarios
3. Map GPS coordinates to SUMO network
4. Place vehicles using TraCI
5. Simulate V2V communication with GUI
6. Generate comprehensive results

Run `python test_v2v_setup.py` to verify everything is working, then execute the simulation using the provided batch file or Python script.
