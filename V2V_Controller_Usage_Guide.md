# V2V Simulation Controller - Usage Guide

## Overview
The V2V Simulation Controller provides complete control over SUMO simulations with advanced GUI controls for step-by-step monitoring and CSV data navigation.

## Features

### 🚗 Vehicle Control
- **Start/Stop SUMO**: Complete control over simulation lifecycle
- **Pause/Resume**: Freeze simulation at any point
- **Step Mode**: Advance simulation one step at a time for detailed observation
- **Vehicle Placement**: Automatic placement of source and destination vehicles at GPS coordinates

### 📊 Data Navigation
- **Row-by-Row Navigation**: Navigate through up to 50 CSV scenarios
- **Previous/Next Buttons**: Browse scenarios with GUI buttons
- **Direct Row Entry**: Jump to specific row numbers
- **Real-time Data Display**: See current CSV row data and coordinates

### 📱 Multi-Tab Interface
1. **CSV Data Tab**: Raw data from current row
2. **Vehicle Coordinates Tab**: GPS coordinates and actual distance
3. **V2V Communication Tab**: Signal parameters (SNR, RSRP, RSSI)

### 📝 Real-time Monitoring
- **Simulation Status**: Current state, step count, active vehicles
- **Live Log**: Real-time message log with timestamps
- **Distance Tracking**: Compare simulated vs actual GPS distances

## How to Use

### 1. Launch the Controller
```bash
python tkinter_simulation_controller.py
# OR
python run_v2v_controller.py
```

### 2. Start SUMO Simulation
- Click **"Start SUMO"** button
- SUMO GUI will open automatically
- Status shows "SUMO Running - Ready to Simulate"

### 3. Navigate CSV Data
- Use **Previous Row ◀** / **Next Row ▶** buttons
- Or enter row number directly and press Enter
- Data updates automatically in tabs

### 4. Step Through Simulation
- Click **"Step"** to advance one simulation step
- Vehicles will be automatically placed at GPS coordinates
- Watch live log for distance and position updates

### 5. Monitor V2V Communication
- Vehicles appear as red (source) and blue (destination)
- Check distance comparison between simulated and actual GPS
- Monitor signal parameters in V2V Communication tab

## Troubleshooting

### SUMO Doesn't Start
- Check that SUMO is installed and `sumo-config/osm.sumocfg` exists
- Ensure no other SUMO instance is running

### Vehicles Don't Appear
- Check that GPS coordinates are valid in CSV data
- Verify that SUMO network has corresponding edges
- Check simulation log for error messages

### No CSV Data Loaded
- Verify `sidelink_parsed.csv` exists in the same directory
- Check that CSV has required columns: `Source`, `Destination`, `lat`, `lon`, `Latitude_destination`, `Longitude_destination`

## Advanced Features

### Manual Step Control
- Use Step button for frame-by-frame analysis
- Perfect for capturing screenshots or detailed observations
- Log shows exact vehicle positions and distances

### Row-specific Analysis
- Each row represents a different V2V communication scenario
- Compare different Source-Destination pairs
- Analyze distance vs signal quality relationships

### Data Export
- Simulation results automatically saved to `focused_v2v_results/`
- Includes vehicle pairs, communication events, and statistics

## Tips for Best Results

1. **Start with Row 0**: Begin with first scenario to understand the interface
2. **Use Step Mode**: Take time to observe vehicle placement and movement
3. **Check GPS Accuracy**: Compare GPS-based distances with SUMO simulation distances
4. **Monitor Log**: Watch real-time messages for debugging and understanding
5. **Try Different Rows**: Each row may have different vehicle scenarios

## Requirements

- Python 3.6+
- tkinter (usually included with Python)
- pandas
- numpy
- SUMO simulation software
- TraCI Python bindings
- `sidelink_parsed.csv` data file
- `sumo-config/osm.sumocfg` SUMO configuration

## Keyboard Shortcuts

- **Enter**: Load specific row number
- **Space**: Step simulation (when Step button is enabled)

This controller provides complete control over V2V simulations with precise vehicle placement, step-by-step monitoring, and comprehensive data visualization.
