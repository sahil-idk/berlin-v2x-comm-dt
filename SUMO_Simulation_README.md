# SUMO TraCI Simulation with Berlin V2X Data

This project creates a SUMO (Simulation of Urban Mobility) simulation using real GPS trajectory data from the Berlin V2X dataset (PC2). The simulation uses TraCI (Traffic Control Interface) to control vehicle movement based on actual GPS data.

## Overview

The simulation reads GPS trajectory data from `pc2_parsed.csv` and controls a vehicle in SUMO GUI to follow the real-world movement patterns captured in Berlin.

## Features

- **Real GPS Data**: Uses actual vehicle trajectory from Berlin V2X dataset
- **SUMO GUI**: Visual simulation with interactive interface
- **TraCI Control**: Dynamic vehicle control based on real data
- **Speed Adaptation**: Vehicle speed matches real-world measurements
- **Background Traffic**: Additional vehicles for realistic simulation

## Files Created

### Core Simulation Files
- `simple_sumo_traci.py` - Main TraCI simulation script
- `setup_sumo_simulation.py` - Setup and installation checker
- `create_simple_berlin_network.py` - Network creation script

### SUMO Configuration Files
- `berlin_simulation.sumocfg` - SUMO simulation configuration
- `berlin_network.net.xml` - SUMO road network
- `berlin_routes.rou.xml` - Vehicle routes and types
- `berlin_additional.add.xml` - Additional simulation elements

### Data Analysis
- `analyze_pc2_for_sumo.py` - PC2 data analysis for SUMO integration

## Prerequisites

### 1. SUMO Installation
Download and install SUMO from: https://sumo.dlr.de/docs/Downloads.php

**Windows:**
- Download the Windows installer
- Add SUMO to your PATH environment variable
- Verify installation: `sumo --version`

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install sumo sumo-tools

# macOS with Homebrew
brew install sumo
```

### 2. Python Packages
```bash
pip install pandas numpy
```

Note: `traci` comes with SUMO installation.

### 3. Required Data
- `pc2_parsed.csv` - GPS trajectory data (generated from parquet files)

## Quick Start

### 1. Setup
```bash
python setup_sumo_simulation.py
```

This script will:
- Check SUMO installation
- Verify Python packages
- Create required network files
- Set up simulation configuration

### 2. Run Simulation
```bash
python simple_sumo_traci.py
```

This will:
- Load PC2 GPS data
- Start SUMO GUI
- Add vehicle to simulation
- Control vehicle movement based on real GPS data

## Detailed Usage

### Data Analysis
```bash
python analyze_pc2_for_sumo.py
```

This analyzes the PC2 data and shows:
- GPS coordinate ranges
- Time duration
- Speed statistics
- Trajectory characteristics

### Network Creation
```bash
python create_simple_berlin_network.py
```

Creates a simple road network for Berlin area.

### Manual SUMO Launch
```bash
sumo-gui -c berlin_simulation.sumocfg
```

Launches SUMO GUI with the simulation configuration.

## Simulation Details

### PC2 Data Characteristics
- **Records**: 44,464 GPS points
- **Duration**: 12.35 hours (June 22-24, 2021)
- **Location**: Berlin city center
- **Speed Range**: 0-97.6 km/h
- **Average Speed**: 18.14 km/h

### Simulation Features
- **Real-time Control**: Vehicle movement controlled by TraCI
- **Speed Matching**: Vehicle speed matches real GPS data
- **Visual Feedback**: Real-time display in SUMO GUI
- **Data Sampling**: Uses every 10th data point for performance

### Vehicle Control
The simulation:
1. Loads PC2 GPS trajectory data
2. Adds a vehicle to the SUMO network
3. Updates vehicle speed based on real data
4. Advances simulation step by step
5. Displays movement in SUMO GUI

## Configuration

### Simulation Parameters
- **Step Length**: 1 second
- **Duration**: Up to 1000 steps (or data length)
- **Vehicle Type**: DEFAULT_VEHTYPE
- **Network**: Simple Berlin road network

### Customization
You can modify:
- `berlin_simulation.sumocfg` - Simulation settings
- `berlin_routes.rou.xml` - Vehicle types and routes
- `simple_sumo_traci.py` - TraCI control logic

## Troubleshooting

### Common Issues

1. **SUMO not found**
   ```
   Error: SUMO not found!
   ```
   - Install SUMO and add to PATH
   - Verify with `sumo --version`

2. **Missing data file**
   ```
   ERROR: Required file pc2_parsed.csv not found!
   ```
   - Run parquet to CSV conversion first
   - Ensure PC2 data is available

3. **TraCI connection failed**
   ```
   Error connecting to SUMO
   ```
   - Check network file exists
   - Verify SUMO configuration
   - Ensure no other SUMO instance running

4. **Python package missing**
   ```
   ImportError: No module named 'pandas'
   ```
   - Install required packages: `pip install pandas numpy`

### Performance Optimization
- Reduce data sampling frequency
- Limit simulation duration
- Use smaller network
- Adjust step length

## Advanced Usage

### Custom Network
To use a real Berlin network:
1. Download Berlin OSM data
2. Convert using `netconvert`
3. Update configuration files

### Multiple Vehicles
Extend the simulation to control multiple vehicles:
1. Modify TraCI script
2. Add more vehicles
3. Use different data sources

### Real-time Data
For real-time simulation:
1. Modify data loading
2. Implement streaming
3. Adjust timing

## Output

The simulation provides:
- **Visual Display**: SUMO GUI showing vehicle movement
- **Console Output**: Progress and statistics
- **Data Logging**: Vehicle positions and speeds

## Example Output

```
=== Simple SUMO TraCI Simulation with PC2 Data ===

Loading PC2 data...
Loaded 44464 data points
Time range: 2021-06-22 09:49:54 to 2021-06-24 10:14:14
Using 4446 sampled data points for simulation
Connected to SUMO successfully!
Vehicle PC2_Vehicle added successfully
Step 0: Speed 0.00 km/h (0.00 m/s)
Step 50: Speed 0.00 km/h (0.00 m/s)
...
Simulation completed after 1000 steps
Processed 1000 data points

✅ Simulation completed successfully!
```

## Contributing

To extend this simulation:
1. Fork the repository
2. Add new features
3. Test thoroughly
4. Submit pull request

## License

This project uses the Berlin V2X dataset and SUMO simulation framework. Please respect their respective licenses.

## References

- [SUMO Documentation](https://sumo.dlr.de/docs/)
- [TraCI Documentation](https://sumo.dlr.de/docs/TraCI.html)
- [Berlin V2X Dataset](https://ieee-dataport.org/open-access/berlin-v2x-machine-learning-dataset-multiple-vehicles-and-radio-access-technologies)

---

**Note**: This simulation is designed for educational and research purposes. The network is simplified and may not represent the complete Berlin road infrastructure.
