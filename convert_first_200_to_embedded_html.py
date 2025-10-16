#!/usr/bin/env python3
"""
Convert first 200 points CSV data to embedded JavaScript for HTML visualization
This avoids browser security restrictions when loading local CSV files
"""

import pandas as pd
import json
import os

def convert_first_200_to_embedded_html():
    """Convert first 200 points CSV data to embedded JavaScript in HTML file"""
    
    print("🔄 Converting first 200 points CSV to embedded HTML...")
    
    # Read the first 200 points CSV
    csv_file = "vehicle_2_4_first_200.csv"
    if not os.path.exists(csv_file):
        print(f"❌ Error: {csv_file} not found!")
        print("Please run extract_first_200_points.py first.")
        return False
    
    print(f"📋 Reading {csv_file}...")
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df)} records")
    
    # Convert DataFrame to list of dictionaries
    data_list = df.to_dict('records')
    
    # Convert to JSON string
    json_data = json.dumps(data_list, indent=2)
    
    # Read the HTML template
    html_file = "first_200_v2v_visualization.html"
    if not os.path.exists(html_file):
        print(f"❌ Error: {html_file} not found!")
        return False
    
    print(f"📄 Reading {html_file}...")
    with open(html_file, 'r', encoding='utf-8') as f:
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

    new_csv_loading = f'''// Load embedded first 200 points data (no CSV file needed)
function loadCsvData() {{
  setInfoText('Loading embedded first 200 Vehicle 2-4 dataset...');
  
  try {{
    // Use embedded data instead of CSV file
    const data = embeddedFirst200Data;
    
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
    
    setInfoText(`Loaded ${{allData.length}} first 200 V2V communication records`);
    
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
// Embedded Vehicle 2-4 first 200 points data
const embeddedFirst200Data = {json_data};
'''
    
    # Find the script tag and insert embedded data right after it
    script_start = html_content.find('<script>')
    if script_start != -1:
        script_start = html_content.find('>', script_start) + 1
        html_content = html_content[:script_start] + embedded_data_script + html_content[script_start:]
    else:
        # Fallback: insert before the last script tag
        html_content = html_content.replace('</script>', f'{embedded_data_script}</script>')
    
    # Remove Papa.parse dependency since we don't need it anymore
    html_content = html_content.replace(
        '<script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js"></script>',
        '<!-- Papa.parse not needed for embedded data -->'
    )
    
    # Create new HTML file with embedded data
    output_file = "first_200_v2v_visualization_embedded.html"
    print(f"💾 Creating {output_file} with embedded data...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Created {output_file} with {len(data_list)} embedded records")
    print("🌐 This file can be opened directly in any browser without CSV file dependencies")
    
    return True

if __name__ == "__main__":
    convert_first_200_to_embedded_html()
