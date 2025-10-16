# Sidelink V2V Simulation with SUMO TraCI

This project simulates Vehicle-to-Vehicle (V2V) communication using SUMO TraCI based on real sidelink data from the Berlin V2X dataset.

## Overview

The simulation takes 50 datapoints from the sidelink dataframe and simulates V2V communication between vehicles in a realistic Berlin road network using SUMO.

## Files

- `simple_sidelink_simulation.py` - Main simulation script (simplified version)
- `sidelink_traci_simulation.py` - Full-featured simulation script
- `gps_to_sumo_converter.py` - GPS to SUMO coordinate conversion helper
- `run_sidelink_simulation.bat` - Windows batch file to run simulation
- `requirements.txt` - Python dependencies

## Prerequisites

1. **Python 3.7+** with required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. **SUMO** (Simulation of Urban Mobility):
   - Download from: https://sumo.dlr.de/docs/Downloads.php
   - Add SUMO to your system PATH
   - Verify installation: `sumo --version`

3. **Required Data Files**:
   - `sidelink_dataframe.parquet` - Sidelink V2V communication data
   - `sumo-config/osm.sumocfg` - SUMO configuration file
   - `sumo-config/osm.net.xml.gz` - Berlin road network

## Quick Start

### Windows:
```bash
run_sidelink_simulation.bat
```

### Linux/Mac:
```bash
python simple_sidelink_simulation.py
```

## How It Works

1. **Data Selection**: Selects 50 diverse datapoints from the sidelink dataframe
2. **Coordinate Conversion**: Converts GPS coordinates to SUMO network coordinates
3. **Vehicle Placement**: Places vehicles at source coordinates with destinations
4. **V2V Simulation**: Simulates communication between vehicles within range
5. **Results**: Generates communication events and statistics

## Simulation Parameters

- **Communication Range**: 500 meters
- **Simulation Duration**: 30 minutes (1800 steps)
- **Vehicle Types**: Passenger vehicles with V2V capabilities
- **Communication Model**: Based on SNR, RSRP, and distance

## Output Files

The simulation generates results in the `simulation_results/` folder:

- `communication_events.csv` - All V2V communication events
- `vehicle_data.csv` - Vehicle parameters and positions
- `stats.json` - Simulation statistics

## Customization

You can modify simulation parameters in the script:

```python
# Communication range
communication_range = 500  # meters

# Simulation duration
max_steps = 1800  # 30 minutes

# Number of datapoints
n_points = 50
```

## Troubleshooting

1. **SUMO not found**: Ensure SUMO is installed and in PATH
2. **Missing files**: Check that all required data files exist
3. **Python errors**: Install required packages with pip
4. **Memory issues**: Reduce number of vehicles or simulation duration

## Advanced Usage

For more advanced features, use the full simulation script:

```bash
python sidelink_traci_simulation.py
```

This includes:
- Advanced coordinate conversion
- Detailed V2V communication modeling
- Visualization generation
- Comprehensive statistics

## Data Format

The sidelink dataframe should contain:
- GPS coordinates (Latitude_source, Longitude_source, etc.)
- Communication parameters (SNR, RSRP, RSSI, MCS)
- Vehicle parameters (speed, etc.)
- Timestamps

## License

This project is part of the Berlin V2X dataset analysis.
