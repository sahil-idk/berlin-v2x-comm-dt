#!/usr/bin/env python3
"""
Open the focused V2V visualization in the default browser
"""

import webbrowser
import os
import sys

def open_focused_visualization():
    """Open the focused V2V visualization HTML file"""
    
    html_file = "focused_v2v_visualization.html"
    
    if not os.path.exists(html_file):
        print(f"❌ Error: {html_file} not found!")
        print("Please run extract_vehicle_2_4_dataset.py first to create the dataset.")
        return False
    
    print("🌐 Opening focused V2V visualization...")
    print(f"   File: {html_file}")
    
    # Get absolute path
    abs_path = os.path.abspath(html_file)
    
    # Open in default browser
    webbrowser.open(f"file://{abs_path}")
    
    print("✅ Visualization opened in your default browser!")
    print("\n📋 Instructions:")
    print("   - Use Play/Pause controls to animate the V2V communication")
    print("   - Adjust speed slider to control animation speed")
    print("   - Switch between scenarios (S1/S2) using the dropdown")
    print("   - Blue line: Vehicle 2 trajectory")
    print("   - Orange line: Vehicle 4 trajectory")
    print("   - Red dashed line: V2V communication link")
    print("   - Orange dots: GPS waypoints")
    
    return True

if __name__ == "__main__":
    open_focused_visualization()
