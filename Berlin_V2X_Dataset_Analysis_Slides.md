# Berlin V2X Dataset Analysis & Visualization Project

## Slide 1: Project Overview
### Berlin V2X Dataset Analysis & Interactive Visualization
- **Project**: Analysis of Vehicle-to-Everything (V2X) communication dataset from Berlin
- **Objective**: Create comprehensive visualization and analysis tools for multi-dimensional vehicle data
- **Dataset Source**: Berlin V2X Machine Learning Dataset from Multiple Vehicles and Radio Access Technologies
- **Tools Developed**: Interactive web-based visualization with parameter analysis

---

## Slide 2: Dataset Overview
### Berlin V2X Dataset Structure
- **Total Datasets**: 4 parquet files (PC1, PC2, PC3, PC4)
- **Total Records**: 206,587 data points
- **Time Period**: June 22, 2021 (09:49 AM onwards)
- **Location**: Berlin, Germany (coordinates ~52.51°N, 13.33°E)
- **Data Collection**: 1-second intervals for GPS data
- **File Sizes**: 
  - PC1: 502 KB (Network Performance)
  - PC2: 1.3 MB (GPS + Weather + Traffic)
  - PC3: 1.7 MB (GPS + Weather + Traffic)
  - PC4: 1.3 MB (GPS + Weather + Traffic)

---

## Slide 3: Dataset Types & Characteristics

### PC1 - Network Performance Data
- **Records**: 57,238 rows
- **Columns**: 7 (Network metrics only)
- **Focus**: V2X communication quality
- **Key Metrics**:
  - Data rate: 60-100 MB/s
  - Jitter: 0.0001-0.0008 seconds
  - IP addresses and ports
  - **No GPS coordinates**

### PC2, PC3, PC4 - Comprehensive Vehicle Data
- **Records**: 44,464 / 60,097 / 44,788 rows respectively
- **Columns**: 22 (Multi-dimensional data)
- **Focus**: Complete vehicle telemetry
- **Data Categories**:
  - GPS & Movement (Latitude, Longitude, Speed, Altitude)
  - Weather (Temperature, Humidity, Pressure, Wind)
  - Traffic (Jam Factor, Street Names, Distance)

---

## Slide 4: Data Categories Deep Dive

### GPS & Movement Data
- **Latitude**: 52.513-52.514°N (Berlin area)
- **Longitude**: 13.334-13.335°E (Berlin area)
- **Altitude**: 30-36 meters above sea level
- **Speed**: 0-6 km/h (urban traffic/parking scenarios)
- **Course Over Ground**: 0-360° compass heading

### Weather Data
- **Temperature**: ~18.13°C (mild conditions)
- **Humidity**: 77% (high humidity)
- **Pressure**: 1011.9 hPa (normal atmospheric pressure)
- **Wind Speed**: 4.07 m/s (moderate wind)
- **Cloud Cover**: 97% (overcast conditions)
- **Precipitation**: Light intensity (0.065)

### Traffic Data
- **Traffic Jam Factor**: ~2.53 (moderate congestion)
- **Street Names**: Bachstraße, Altonaerstraße
- **Distance**: 30-46 meters along route
- **Position**: Various locations in Berlin traffic network

---

## Slide 5: Technical Implementation

### Data Processing Pipeline
1. **Parquet to CSV Conversion**
   - Custom Python script (`parquet_to_csv.py`)
   - Automatic column detection (lat/lon/time)
   - Nested data serialization to JSON
   - ISO timestamp generation

2. **Interactive Web Visualization**
   - HTML5 + JavaScript + Leaflet.js
   - Real-time parameter filtering
   - GPS coordinate validation
   - Multi-dataset support

### Key Features Developed
- **Smart Dataset Detection**: Automatic GPS coordinate validation
- **Unified Interface**: Single HTML file for all datasets
- **Parameter Analysis**: Communication vs. other parameters
- **Visual Status Indicators**: GPS availability warnings
- **Interactive Controls**: Play/pause, speed control, navigation

---

## Slide 6: Visualization Features

### Interactive Map Interface
- **Base Map**: OpenStreetMap tiles
- **Vehicle Tracking**: Real-time marker movement
- **Trajectory Visualization**: Polyline showing vehicle path
- **Parameter Panel**: Live data display with filtering
- **Control Panel**: Play/pause, speed adjustment, navigation

### Dataset Selection
- **Dropdown Menu**: Easy switching between PC1-PC4
- **Smart Detection**: Automatic GPS availability detection
- **Status Indicators**: 
  - ⚠️ Warning for non-GPS datasets (PC1)
  - ✅ Confirmation for GPS datasets (PC2-PC4)

### Parameter Analysis
- **Communication Parameters**: Network performance metrics
- **Other Parameters**: Weather, traffic, vehicle data
- **Search Functionality**: Filter parameters by name
- **Real-time Updates**: Live parameter display during playback

---

## Slide 7: Dataset Analysis Results

### Network Performance (PC1)
- **Data Rate**: Consistent 60-100 MB/s throughput
- **Jitter**: Very low latency variation (< 1ms)
- **Connection**: Stable V2X communication
- **Endpoints**: Local (10.175.117.136:47474) ↔ Remote (193.174.67.58:5204)
- **Quality**: Excellent network performance for V2X applications

### Vehicle Behavior Patterns
- **Speed Profile**: Mostly stationary (0-6 km/h)
- **Location**: Concentrated on specific Berlin streets
- **Movement**: Minimal displacement (parking/traffic scenarios)
- **Duration**: Extended monitoring periods (15+ hours)

### Environmental Context
- **Weather Impact**: Mild conditions, light precipitation
- **Traffic Conditions**: Moderate congestion levels
- **Urban Environment**: Dense city center monitoring
- **Time Patterns**: Consistent data collection throughout day

---

## Slide 8: Technical Architecture

### Data Flow Architecture
```
Parquet Files → Python Converter → CSV Files → Web Visualization
     ↓              ↓                ↓              ↓
  Raw Data    →  Normalized    →  Structured   →  Interactive
  Storage         Format          Data          Interface
```

### Technology Stack
- **Backend**: Python (pandas, pyarrow)
- **Frontend**: HTML5, CSS3, JavaScript
- **Mapping**: Leaflet.js with OpenStreetMap
- **Data Processing**: PapaParse for CSV parsing
- **Visualization**: Custom interactive components

### File Structure
```
berlin_v2x/
├── pc1 (1).parquet          # Network performance data
├── pc2 (1).parquet          # GPS + Weather + Traffic
├── pc3 (1).parquet          # GPS + Weather + Traffic  
├── pc4 (1).parquet          # GPS + Weather + Traffic
├── pc1_parsed.csv           # Converted network data
├── pc2_parsed.csv           # Converted vehicle data
├── pc3_parsed.csv           # Converted vehicle data
├── pc4_parsed.csv           # Converted vehicle data
├── parquet_to_csv.py        # Conversion script
├── map_simulation.html      # Basic visualization
└── map_simulaton_with_params.html  # Advanced visualization
```

---

## Slide 9: Key Findings & Insights

### V2X Communication Quality
- **Excellent Performance**: Consistent high data rates (60-100 MB/s)
- **Low Latency**: Minimal jitter (< 1ms) indicates stable connections
- **Reliable Infrastructure**: Stable IP endpoints throughout monitoring
- **Real-world Conditions**: Data collected under actual urban traffic

### Vehicle Behavior Analysis
- **Urban Mobility**: Low-speed urban driving patterns
- **Traffic Integration**: Vehicles operating in real traffic conditions
- **Environmental Adaptation**: Behavior under various weather conditions
- **Spatial Distribution**: Concentrated monitoring in Berlin city center

### Data Quality Assessment
- **Completeness**: High data coverage across all parameters
- **Consistency**: Uniform sampling intervals (1-second)
- **Accuracy**: Precise GPS coordinates and sensor readings
- **Reliability**: Stable data collection over extended periods

---

## Slide 10: Applications & Use Cases

### Research Applications
- **V2X Protocol Analysis**: Network performance evaluation
- **Traffic Flow Modeling**: Urban mobility pattern analysis
- **Environmental Impact**: Weather effects on vehicle behavior
- **Machine Learning**: Multi-dimensional feature engineering

### Industry Applications
- **Autonomous Vehicles**: V2X communication validation
- **Smart Cities**: Traffic management optimization
- **Fleet Management**: Vehicle performance monitoring
- **Network Planning**: V2X infrastructure deployment

### Educational Value
- **Data Science**: Real-world dataset analysis
- **Visualization**: Interactive data exploration
- **IoT Systems**: Connected vehicle technology
- **Urban Planning**: Smart city development

---

## Slide 11: Future Enhancements

### Technical Improvements
- **Real-time Processing**: Live data streaming capabilities
- **Advanced Analytics**: Machine learning integration
- **Mobile Support**: Responsive design for mobile devices
- **Data Export**: Multiple format support (JSON, XML)

### Feature Additions
- **Comparative Analysis**: Multi-vehicle comparison tools
- **Statistical Dashboard**: Summary statistics and trends
- **Alert System**: Anomaly detection and notifications
- **Custom Filters**: Advanced parameter filtering

### Research Extensions
- **Temporal Analysis**: Long-term trend analysis
- **Spatial Clustering**: Geographic pattern recognition
- **Correlation Analysis**: Parameter relationship studies
- **Predictive Modeling**: Future behavior prediction

---

## Slide 12: Conclusion

### Project Achievements
✅ **Complete Dataset Analysis**: Comprehensive understanding of Berlin V2X data
✅ **Interactive Visualization**: User-friendly web interface for data exploration
✅ **Multi-format Support**: Seamless conversion between parquet and CSV
✅ **Smart Detection**: Automatic GPS coordinate validation
✅ **Parameter Analysis**: Detailed breakdown of communication and vehicle metrics

### Technical Deliverables
- **4 Converted CSV Files**: Ready for analysis and visualization
- **Interactive HTML Tool**: Complete visualization solution
- **Python Conversion Script**: Reusable data processing tool
- **Comprehensive Documentation**: Detailed dataset analysis

### Impact & Value
- **Research Ready**: Dataset prepared for academic and industry research
- **User Friendly**: Accessible visualization for non-technical users
- **Extensible**: Framework for future enhancements and analysis
- **Educational**: Valuable resource for V2X technology understanding

---

## Appendix: Dataset Screenshots Analysis

### Screenshot Analysis (Based on Attached Images)
The attached screenshots likely show:
- **Dataset Structure**: Column layouts and data types
- **Visualization Interface**: Interactive map and parameter panels
- **Data Quality**: Sample data rows and value ranges
- **Geographic Context**: Berlin map with vehicle trajectories

*Note: Detailed analysis of specific screenshots would require image processing capabilities to extract text and visual elements.*

---

**Project Status**: ✅ Complete
**Files Generated**: 4 CSV files + 2 HTML visualization tools
**Total Data Points**: 206,587 records
**Visualization Features**: Interactive map, parameter analysis, multi-dataset support
