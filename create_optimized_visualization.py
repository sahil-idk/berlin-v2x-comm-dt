#!/usr/bin/env python3
"""
Create an optimized version of the first 200 points visualization
using a more efficient data structure and smaller embedded dataset
"""

import pandas as pd
import json

def create_optimized_visualization():
    """Create an optimized version with smaller embedded data"""
    
    print("🔄 Creating optimized first 200 points visualization...")
    
    # Read the first 200 points CSV
    df = pd.read_csv("vehicle_2_4_first_200.csv")
    print(f"✅ Loaded {len(df)} records")
    
    # Create a more compact data structure with only essential fields
    compact_data = []
    for _, row in df.iterrows():
        compact_record = {
            'timestamp': row['timestamp'],
            'source_lat': row['Latitude_source'],
            'source_lon': row['Longitude_source'],
            'dest_lat': row['Latitude_destination'],
            'dest_lon': row['Longitude_destination'],
            'distance': row['distance'],
            'snr': row['SNR'],
            'source': row['Source'],
            'destination': row['Destination']
        }
        compact_data.append(compact_record)
    
    print(f"📊 Created compact data with {len(compact_data)} records")
    
    # Convert to JSON string
    json_data = json.dumps(compact_data, indent=2)
    
    # Read the original HTML template
    with open('first_200_v2v_visualization.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Replace the Papa.parse CSV loading with embedded data
    old_csv_loading = '''// Load first 200 points CSV data
function loadCsvData() {
  setInfoText('Loading first 200 Vehicle 2-4 dataset...');
  
  Papa.parse('vehicle_2_4_first_200.csv', {
    download: true, header: true, skipEmptyLines: true,
    complete: function(results){
      const data = results.data;
      if (!data || data.length === 0){ 
        setInfoText('No data found in CSV'); 
        return; 
      }
      
      // Filter out rows without valid GPS coordinates
      allData = data.filter(row => {
        const sourceLat = parseFloat(row['Latitude_source']);
        const sourceLon = parseFloat(row['Longitude_source']);
        const destLat = parseFloat(row['Latitude_destination']);
        const destLon = parseFloat(row['Longitude_destination']);
        
        return !isNaN(sourceLat) && !isNaN(sourceLon) && !isNaN(destLat) && !isNaN(destLon);
      });
      
      filteredData = allData; // Use all data since it's already filtered
      
      setInfoText(`Loaded ${allData.length} first 200 V2V communication records`);
      
      // Update dataset info
      document.getElementById('totalRecords').textContent = `${allData.length} records`;
      document.getElementById('coverage').textContent = '0.010° × 0.030°';
      document.getElementById('distanceRange').textContent = '11.4m - 23.1m';
      document.getElementById('scenario').textContent = 'S2';
      
      // Build vehicle trajectories
      buildVehicleTrajectories();
      
      // Initial display
      currentIndex = 0;
      updateForIndex(0);
    },
    error: function(err){ 
      setInfoText('CSV load error: ' + err); 
      console.error('CSV load error:', err);
    }
  });
}'''

    new_csv_loading = f'''// Load embedded optimized data (no CSV file needed)
function loadCsvData() {{
  setInfoText('Loading embedded optimized dataset...');
  
  try {{
    // Use embedded data instead of CSV file
    const data = embeddedOptimizedData;
    
    if (!data || data.length === 0){{ 
      setInfoText('No data found in embedded dataset'); 
      return; 
    }}
    
    // Convert compact data to full format for compatibility
    allData = data.map(row => ({{
      'timestamp': row.timestamp,
      'Latitude_source': row.source_lat,
      'Longitude_source': row.source_lon,
      'Latitude_destination': row.dest_lat,
      'Longitude_destination': row.dest_lon,
      'distance': row.distance,
      'SNR': row.snr,
      'Source': row.source,
      'Destination': row.destination,
      'Scenario': 'S2'
    }}));
    
    filteredData = allData; // Use all data since it's already filtered
    
    setInfoText(`Loaded ${{allData.length}} optimized V2V communication records`);
    
    // Update dataset info
    document.getElementById('totalRecords').textContent = `${{allData.length}} records`;
    document.getElementById('coverage').textContent = '0.010° × 0.030°';
    document.getElementById('distanceRange').textContent = '11.4m - 23.1m';
    document.getElementById('scenario').textContent = 'S2';
    
    // Build vehicle trajectories
    buildVehicleTrajectories();
    
    // Initial display
    currentIndex = 0;
    updateForIndex(0);
  }} catch (err) {{
    setInfoText('Embedded data load error: ' + err); 
    console.error('Embedded data load error:', err);
  }}
}}'''
    
    # Replace the CSV loading function
    html_content = html_content.replace(old_csv_loading, new_csv_loading)
    
    # Add embedded data at the very beginning of the script section
    embedded_data_script = f'''
// Embedded optimized data (compact format)
const embeddedOptimizedData = {json_data};
'''
    
    # Find the script tag and insert embedded data right after it
    script_start = html_content.find('<script>')
    if script_start != -1:
        script_start = html_content.find('>', script_start) + 1
        html_content = html_content[:script_start] + embedded_data_script + html_content[script_start:]
    
    # Remove Papa.parse dependency
    html_content = html_content.replace(
        '<script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js"></script>',
        '<!-- Papa.parse not needed for embedded data -->'
    )
    
    # Create new HTML file with embedded data
    output_file = "first_200_optimized_visualization.html"
    print(f"💾 Creating {output_file} with {len(compact_data)} optimized records...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Created {output_file}")
    
    # Check file size
    import os
    file_size = os.path.getsize(output_file)
    print(f"📊 File size: {file_size / 1024:.1f} KB")
    
    return True

if __name__ == "__main__":
    create_optimized_visualization()
