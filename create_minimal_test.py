#!/usr/bin/env python3
"""
Create a minimal test version of the first 200 points visualization
with only 5 records to test if the issue is with data size
"""

import pandas as pd
import json

def create_minimal_test():
    """Create a minimal test version with only 5 records"""
    
    print("🔄 Creating minimal test version...")
    
    # Read the first 200 points CSV
    df = pd.read_csv("vehicle_2_4_first_200.csv")
    print(f"✅ Loaded {len(df)} records")
    
    # Take only first 5 records
    minimal_df = df.head(5).copy()
    print(f"📊 Selected {len(minimal_df)} records for testing")
    
    # Convert to list of dictionaries
    data_list = minimal_df.to_dict('records')
    
    # Convert to JSON string
    json_data = json.dumps(data_list, indent=2)
    
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

    new_csv_loading = f'''// Load embedded minimal test data (no CSV file needed)
function loadCsvData() {{
  setInfoText('Loading embedded minimal test dataset...');
  
  try {{
    // Use embedded data instead of CSV file
    const data = embeddedMinimalData;
    
    if (!data || data.length === 0){{ 
      setInfoText('No data found in embedded dataset'); 
      return; 
    }}
    
    // Filter out rows without valid GPS coordinates
    allData = data.filter(row => {{
      const sourceLat = parseFloat(row['Latitude_source']);
      const sourceLon = parseFloat(row['Longitude_source']);
      const destLat = parseFloat(row['Latitude_destination']);
      const destLon = parseFloat(row['Longitude_destination']);
      
      return !isNaN(sourceLat) && !isNaN(sourceLon) && !isNaN(destLat) && !isNaN(destLon);
    }});
    
    filteredData = allData; // Use all data since it's already filtered
    
    setInfoText(`Loaded ${{allData.length}} minimal test V2V communication records`);
    
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
// Embedded minimal test data (5 records)
const embeddedMinimalData = {json_data};
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
    output_file = "minimal_test_visualization.html"
    print(f"💾 Creating {output_file} with {len(data_list)} embedded records...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Created {output_file}")
    print("🌐 This file should load much faster for testing")
    
    return True

if __name__ == "__main__":
    create_minimal_test()
