#!/usr/bin/env python3
"""
Open the optimized first 200 points V2V visualization in browser
"""

import webbrowser
import os

def open_optimized_visualization():
    """Open the optimized first 200 points V2V visualization"""
    
    print("🌐 Opening optimized first 200 points V2V visualization...")
    
    # Check if optimized HTML file exists
    html_file = "first_200_optimized_visualization.html"
    if not os.path.exists(html_file):
        print(f"❌ Error: {html_file} not found!")
        print("Please run create_optimized_visualization.py first.")
        return False
    
    # Get absolute path
    abs_path = os.path.abspath(html_file)
    
    # Open in default browser
    webbrowser.open(f"file://{abs_path}")
    
    print(f"✅ Optimized visualization opened in your default browser!")
    print(f"   File: {html_file}")
    
    # Check file size
    file_size = os.path.getsize(html_file)
    print(f"   Size: {file_size / 1024:.1f} KB (optimized from 529.4 KB)")
    
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
    print("   - 200 GPS points (optimized embedded data)")
    print("   - Distance range: 11.4m - 23.1m")
    print("   - Mean distance: 16.4m")
    print("   - Scenario S2 only")
    print("   - Focused simulation patch")
    print("   - 85% smaller file size for faster loading")
    
    print("\n✅ No CSV file dependencies - all data is embedded!")
    
    return True

if __name__ == "__main__":
    open_optimized_visualization()
