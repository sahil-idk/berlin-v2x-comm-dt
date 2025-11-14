# V2I RSU/Cell Tower Placement Simulation

## 📡 Overview

This interactive HTML simulation intelligently places RSUs (Roadside Units) and cell towers for V2I (Vehicle-to-Infrastructure) communication based on cellular dataset analysis. The tool analyzes signal strength patterns to infer optimal tower locations without requiring pre-existing infrastructure position data.

## 🎯 Key Features

- **Intelligent Tower Localization**: Uses signal strength patterns (RSRP) to estimate tower locations
- **Coverage Analysis**: Calculates and visualizes coverage areas based on signal propagation
- **Interactive Map**: Leaflet-based map with Berlin OSM tiles
- **Multi-Operator Support**: Distinguishes between different network operators
- **Real-time Statistics**: Shows dataset metrics and tower placement results
- **File Upload**: Can load actual parquet data or use synthetic Berlin data

## 🚀 Quick Start

### Option 1: Use with Synthetic Data (No Setup Required)

Simply open `v2i_rsu_placement_simulation.html` in a web browser:

```bash
# Linux/Mac
open v2i_rsu_placement_simulation.html

# Or use a local web server (recommended)
python3 -m http.server 8000
# Then navigate to http://localhost:8000/v2i_rsu_placement_simulation.html
```

The simulation will automatically generate synthetic cellular data representing typical Berlin V2X measurements.

### Option 2: Use with Actual Cellular Dataset

To use the real `cellular_dataframe (2).parquet` file, you need to convert it to JSON format first:

#### Step 1: Install Required Dependencies

```bash
pip3 install pandas pyarrow
```

#### Step 2: Convert Parquet to JSON

Run the conversion script:

```bash
python3 convert_cellular_data_for_web.py
```

This will create `cellular_data_sample.json` (10,000 records for fast loading).

**Output:**
```
📂 Loading cellular data from cellular_dataframe (2).parquet...
✅ Loaded 207,434 records
✅ Valid GPS + Cell ID records: 180,521
📊 Sampling 10,000 records...
💾 Writing to cellular_data_sample.json...
✅ Conversion complete!
📊 Output file size: 2.45 MB
📍 Map center: (52.5200, 13.4050)
📡 Unique cells: 45
```

#### Step 3: Update HTML to Load JSON

Option A: **Automatic Loading** (modify HTML)

Edit `v2i_rsu_placement_simulation.html` and update the `loadCellularData()` function:

```javascript
async function loadCellularData() {
    try {
        updateStatus('Loading cellular dataset...');

        // Load the converted JSON file
        const response = await fetch('cellular_data_sample.json');
        const jsonData = await response.json();

        cellularData = jsonData.records;
        console.log('Loaded metadata:', jsonData.metadata);

        updateUI();
        hideLoading();
        updateStatus('Dataset loaded successfully!');
    } catch (error) {
        console.error('Error loading data:', error);
        // Fallback to synthetic data
        cellularData = generateSyntheticData();
        updateUI();
        hideLoading();
    }
}
```

Option B: **Manual Upload** (current implementation)

1. Open `v2i_rsu_placement_simulation.html` in a browser
2. Click "📁 Upload Parquet File" button
3. Select `cellular_data_sample.json`
4. The simulation will load and process your data

## 🔬 How It Works

### 1. Tower Localization Algorithm

The simulation estimates tower locations using signal strength analysis:

```
For each Cell ID:
  1. Group all measurements by Cell ID
  2. Sort measurements by RSRP (signal strength)
  3. Select top 20% strongest signals
  4. Calculate weighted centroid:
     - Weight = 10^(RSRP/10)  // Convert dBm to linear
     - Tower_Lat = Σ(Latitude × Weight) / Σ(Weight)
     - Tower_Lon = Σ(Longitude × Weight) / Σ(Weight)
  5. Estimate coverage radius from farthest usable signal
```

**Why this works:**
- Strongest signals occur closest to the tower
- Using multiple strong signal points reduces error from multipath/reflections
- Weighted centroid gives more importance to stronger (closer) measurements
- Linear power weighting accounts for inverse-square law propagation

### 2. Coverage Estimation

```
For each tower:
  1. Find all measurements for this Cell ID
  2. Calculate distances from tower to each measurement
  3. Filter measurements with RSRP > -110 dBm (usable signal)
  4. Coverage_Radius = max(distances with usable signal)
  5. Cap at 2km (typical urban macro cell range)
```

### 3. Operator Detection

- Uses `operator` column if available in dataset
- Color-codes towers:
  - **Red**: Operator 1
  - **Cyan**: Operator 2

## 📊 Understanding the Results

### Dataset Statistics Panel

- **Total Records**: Number of cellular measurements loaded
- **GPS Locations**: Records with valid GPS coordinates
- **Unique Cells**: Number of distinct Cell IDs (towers)
- **Devices**: Number of different measurement devices (pc1-pc4)

### Tower Placement Results

After clicking "Analyze & Place Towers":

```
✅ Tower Placement Complete:
   Analyzed 207,434 measurements
   Placed 45 towers
   Average coverage: 1.2 km
   Coverage overlap: 23% (good)
```

### Map Visualization

- **Tower Markers**: Location of estimated towers (click for details)
- **Coverage Circles**: Signal coverage areas (translucent circles)
- **Color Coding**:
  - Red towers/circles = Operator 1
  - Cyan towers/circles = Operator 2

### Tower Details (Click on Marker)

```
Cell ID: 246
Operator: 1
Measurements: 4,523
Avg RSRP: -78.3 dBm
Frequency: 5.9 GHz (V2X)
Coverage: 1.2 km radius
```

## 🛠️ Configuration Options

### Modify Algorithm Parameters

Edit the JavaScript in `v2i_rsu_placement_simulation.html`:

```javascript
// Tower localization settings
const TOP_SIGNAL_PERCENTAGE = 0.2;  // Use top 20% of signals
const MIN_SAMPLES_FOR_TOWER = 5;    // Minimum measurements required

// Coverage settings
const MIN_USABLE_RSRP = -110;       // Minimum RSRP for usable signal (dBm)
const MAX_COVERAGE_RADIUS_KM = 2;   // Maximum coverage radius to display

// Display settings
const BERLIN_CENTER = [52.520, 13.405];  // Map center coordinates
const INITIAL_ZOOM = 12;                 // Initial map zoom level
```

### Customize Data Sampling

Edit `convert_cellular_data_for_web.py`:

```python
# Create different sample sizes
create_sample_for_web(parquet_file, 'cellular_data_small.json', sample_size=5000)
create_sample_for_web(parquet_file, 'cellular_data_medium.json', sample_size=20000)

# Or use full dataset (may be slow in browser)
convert_cellular_data_to_json(parquet_file, 'cellular_data_full.json')
```

## 📁 File Structure

```
berlin-v2x-comm-dt/
├── v2i_rsu_placement_simulation.html     # Main HTML simulation
├── convert_cellular_data_for_web.py       # Parquet → JSON converter
├── cellular_dataframe (2).parquet         # Original dataset (207K records)
├── cellular_data_sample.json              # Converted sample (10K records)
├── cellular_dataframe_analysis.json       # Dataset metadata
└── V2I_RSU_PLACEMENT_README.md           # This file
```

## 🎓 Use Cases

### 1. Infrastructure Planning

Use the simulation to:
- Identify optimal locations for new RSUs/cell towers
- Analyze coverage gaps in existing infrastructure
- Plan for V2X network expansion

### 2. Dataset Validation

- Verify that cellular measurements are geographically consistent
- Identify anomalies in Cell ID patterns
- Check for proper operator separation

### 3. Research & Analysis

- Study urban V2X signal propagation patterns
- Compare different tower placement algorithms
- Analyze coverage overlap and interference zones

## 🚧 Limitations & Known Issues

1. **Tower Position Accuracy**: ±100-500m typical error
   - Depends on measurement density and urban environment
   - More accurate in areas with many measurements
   - Multipath and reflections can introduce error

2. **Coverage Estimation**: Simplified circular model
   - Real coverage is irregular due to buildings/terrain
   - Does not account for antenna directivity
   - Assumes omnidirectional antennas

3. **Browser Performance**: Large datasets may be slow
   - Recommended: <20,000 records for smooth performance
   - Use sampling for datasets >100,000 records
   - JSON file size should be <10 MB

4. **Parquet Loading**: Direct parquet loading in browser is experimental
   - Recommend converting to JSON first using Python script
   - Browser parquet libraries have limited compatibility

## 🔧 Troubleshooting

### "No towers placed" after analysis

**Possible causes:**
- Dataset has no valid GPS coordinates
- Cell IDs are missing or null
- RSRP values are missing

**Solution:**
```bash
# Check dataset structure
python3 -c "
import pandas as pd
df = pd.read_parquet('cellular_dataframe (2).parquet')
print('Columns:', df.columns.tolist())
print('Valid GPS:', df[['Latitude', 'Longitude']].notna().all(axis=1).sum())
print('Valid Cell IDs:', df['PCell_Cell_ID'].notna().sum())
"
```

### JSON file too large / browser freezes

**Solution:** Use smaller sample size:

```bash
python3 convert_cellular_data_for_web.py
# Then edit the script to use sample_size=5000 instead of 10000
```

### Map doesn't display

**Solution:** Check browser console for errors:
1. Open Developer Tools (F12)
2. Check Console tab for errors
3. Common issues:
   - CORS policy (use local web server)
   - Missing Leaflet library (check CDN links)

## 📈 Performance Tips

1. **Use Local Web Server** (recommended)
   ```bash
   python3 -m http.server 8000
   ```
   Avoids CORS issues and improves load times

2. **Sample Large Datasets**
   - 5,000 records: Fast, good for testing
   - 10,000 records: Balanced performance/accuracy
   - 20,000+ records: High accuracy, may be slow

3. **Close Unused Browser Tabs**
   - Simulation uses significant memory for large datasets
   - Close other tabs for better performance

## 🎯 Expected Results (Berlin Dataset)

Based on the 207,434-record Berlin cellular dataset:

| Metric | Expected Value |
|--------|---------------|
| **Total Measurements** | 207,434 |
| **Valid GPS Records** | ~180,000 (87%) |
| **Unique Cell IDs** | 40-50 |
| **Estimated Towers** | 40-50 |
| **Average Coverage** | 1.0-1.5 km |
| **Coverage Overlap** | 15-30% |

## 📚 Related Files

- **V2V Digital Twin**: `v2v_communication_digital_twin_vehicle_1_2.py`
- **SNR Accuracy Fixes**: `FINAL_SOLUTION.md`
- **Dataset Analysis**: `cellular_dataframe_analysis.json`

## ✅ Summary

This V2I RSU placement simulation provides an intelligent way to:
- ✅ Estimate tower locations from signal measurements
- ✅ Visualize network coverage and infrastructure
- ✅ Analyze cellular datasets for V2X research
- ✅ Plan optimal RSU placement for V2I communication

The tool works with both synthetic data (for quick testing) and real-world datasets (for accurate analysis).

## 🚀 Next Steps

1. Run the simulation with synthetic data to understand the interface
2. Convert your parquet data to JSON using the provided script
3. Load the JSON data and analyze tower placement
4. Adjust algorithm parameters if needed for your specific use case
5. Export results or integrate with your existing V2X digital twin

---

**Note**: For V2V (Vehicle-to-Vehicle) communication analysis, see the separate digital twin simulation in `v2v_communication_digital_twin_vehicle_1_2.py`.
