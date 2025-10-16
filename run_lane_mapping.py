#!/usr/bin/env python3
"""
Launcher script for GPS to Lane Mapping (2 Point Test)
"""

import subprocess
import sys

if __name__ == "__main__":
    print("=" * 60)
    print("GPS to Lane Mapping (2 Point Test)")
    print("=" * 60)
    print()
    
    # Run the lane mapping script
    result = subprocess.run([sys.executable, "map_gps_to_lanes.py"])
    
    sys.exit(result.returncode)

