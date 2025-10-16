#!/usr/bin/env python3
"""
Open the embedded closer V2V visualization in the default browser
"""

import webbrowser
import os
import sys

def open_embedded_closer_visualization():
    """Open the embedded closer V2V visualization HTML file"""
    
    html_file = "closer_v2v_visualization_embedded.html"
    
    if not os.path.exists(html_file):
        print(f"❌ Error: {html_file} not found!")
        print("Please run convert_csv_to_embedded_html.py first to create the embedded version.")
        return False
    
    print("🌐 Opening embedded closer V2V visualization...")
    print(f"   File: {html_file}")
    
    # Get absolute path
    abs_path = os.path.abspath(html_file)
    
    # Open in default browser
    webbrowser.open(f"file://{abs_path}")
    
    print("✅ Embedded closer visualization opened in your default browser!")
    print("\n📋 Instructions:")
    print("   - Use Play/Pause controls to animate the V2V communication")
    print("   - Adjust speed slider to control animation speed (1-1000 steps/sec)")
    print("   - Use Step button to move one point at a time")
    print("   - Blue line: Vehicle 2 trajectory")
    print("   - Orange line: Vehicle 4 trajectory")
    print("   - Red dashed line: V2V communication link")
    print("   - Orange dots: GPS waypoints (every 10th point)")
    print("   - Progress bar shows current position in dataset")
    print("\n🎯 Dataset Features:")
    print("   - 1,465 closer GPS points (embedded in HTML)")
    print("   - Distance range: 2.6m - 25.0m")
    print("   - Mean distance: 13.4m")
    print("   - Scenario S2 only")
    print("   - Enhanced zoom level for better visibility")
    print("\n✅ No CSV file dependencies - all data is embedded!")
    
    return True

if __name__ == "__main__":
    open_embedded_closer_visualization()
