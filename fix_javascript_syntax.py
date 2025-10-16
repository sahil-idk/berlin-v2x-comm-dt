#!/usr/bin/env python3
"""
Fix the JavaScript syntax error in the embedded HTML file
"""

def fix_javascript_syntax():
    """Fix the JavaScript syntax error in the embedded HTML"""
    
    print("🔧 Fixing JavaScript syntax error...")
    
    # Read the embedded HTML file
    with open('first_200_v2v_visualization_embedded.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the problematic loadCsvData function
    old_function = '''        function loadCsvData() {
            setInfoText('Loading embedded first 200 Vehicle 2-4 dataset...');

            const data = embeddedFirst200Data; // Papa.parse('vehicle_2_4_first_200.csv', {
                // download: true, header: true, skipEmptyLines: true,
                // complete: function(results){
                    // const data = results.data;
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

    new_function = '''        function loadCsvData() {
            setInfoText('Loading embedded first 200 Vehicle 2-4 dataset...');
            
            try {
                // Use embedded data instead of CSV file
                const data = embeddedFirst200Data;
                
                if (!data || data.length === 0){ 
                    setInfoText('No data found in embedded dataset'); 
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
            } catch (err) {
                setInfoText('Embedded data load error: ' + err); 
                console.error('Embedded data load error:', err);
            }
        }'''
    
    # Replace the function
    if old_function in content:
        content = content.replace(old_function, new_function)
        print("✅ Replaced loadCsvData function")
    else:
        print("⚠️ Function pattern not found, trying alternative approach")
        # Try to find and replace just the problematic part
        import re
        # Find the function start
        func_start = content.find("function loadCsvData() {")
        if func_start != -1:
            # Find the next function or end of script
            next_func = content.find("function ", func_start + 1)
            if next_func == -1:
                next_func = content.find("        }", func_start + 1)
                if next_func != -1:
                    next_func = content.find("\n", next_func) + 1
            
            if next_func != -1:
                # Replace the entire function
                before = content[:func_start]
                after = content[next_func:]
                content = before + new_function + "\n        " + after
                print("✅ Replaced function using alternative method")
    
    # Write the fixed content back
    with open('first_200_v2v_visualization_embedded.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed JavaScript syntax error")
    print("🌐 The file should now work without syntax errors")
    
    return True

if __name__ == "__main__":
    fix_javascript_syntax()
