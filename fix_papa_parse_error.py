#!/usr/bin/env python3
"""
Fix the Papa.parse reference error in the optimized visualization
"""

def fix_papa_parse_error():
    """Fix the Papa.parse reference error in optimized visualization"""
    
    print("🔧 Fixing Papa.parse reference error...")
    
    # Read the optimized HTML file
    with open('first_200_optimized_visualization.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the entire loadCsvData function
    old_function_start = content.find('function loadCsvData() {')
    if old_function_start == -1:
        print("❌ loadCsvData function not found")
        return False
    
    # Find the end of the function (next function or end of script)
    next_function = content.find('function ', old_function_start + 1)
    if next_function == -1:
        # Look for the end of the script section
        next_function = content.find('</script>', old_function_start)
    
    if next_function == -1:
        print("❌ Could not find function end")
        return False
    
    # Extract the old function
    old_function = content[old_function_start:next_function]
    
    # Create the new function
    new_function = '''function loadCsvData() {
            setInfoText('Loading embedded optimized dataset...');
            
            try {
                // Use embedded data instead of CSV file
                const data = embeddedOptimizedData;
                
                if (!data || data.length === 0){ 
                    setInfoText('No data found in embedded dataset'); 
                    return; 
                }
                
                // Convert compact data to full format for compatibility
                allData = data.map(row => ({
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
                }));
                
                filteredData = allData; // Use all data since it's already filtered
                
                setInfoText(`Loaded ${allData.length} optimized V2V communication records`);
                
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
            } catch (err) {
                setInfoText('Embedded data load error: ' + err); 
                console.error('Embedded data load error:', err);
            }
        }'''
    
    # Replace the function
    content = content.replace(old_function, new_function)
    
    # Also remove any Papa.parse script references
    content = content.replace(
        '<script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js"></script>',
        '<!-- Papa.parse not needed for embedded data -->'
    )
    
    # Write the fixed content back
    with open('first_200_optimized_visualization.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed Papa.parse reference error")
    print("🌐 The file should now work without Papa.parse dependencies")
    
    return True

if __name__ == "__main__":
    fix_papa_parse_error()
