#!/usr/bin/env python3
"""
Launcher for GPS Waypoint Visualization
"""

import subprocess
import sys

def main():
    """Run the GPS waypoint visualization script"""
    print("Launching GPS Waypoint Visualization...")
    try:
        result = subprocess.run(['python', 'visualize_gps_waypoints.py'])
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error launching visualization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

