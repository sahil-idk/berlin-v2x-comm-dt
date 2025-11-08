#!/usr/bin/env python3
"""
Extract center coordinates for all scenarios for OSM Web Wizard
"""

import json
import os

scenarios = ['vehicle_1_2', 'vehicle_1_3', 'vehicle_1_4', 'vehicle_2_3', 'vehicle_2_4', 'vehicle_3_4']

print('='*70)
print('OSM WEB WIZARD COORDINATES FOR EACH SCENARIO')
print('='*70)
print('\nUse these coordinates in OSM Web Wizard Position field:')
print('Format: lat lon (e.g., 52.505376 13.325221)\n')

for s in scenarios:
    metadata_file = f'scenarios/{s}_metadata.json'
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        center_lat = metadata['coordinate_bounds']['center_lat']
        center_lon = metadata['coordinate_bounds']['center_lon']
        min_lat = metadata['coordinate_bounds']['min_lat']
        max_lat = metadata['coordinate_bounds']['max_lat']
        min_lon = metadata['coordinate_bounds']['min_lon']
        max_lon = metadata['coordinate_bounds']['max_lon']
        
        print(f"Scenario: {s.replace('_', ' ').title()}")
        print(f"  Center (use this): {center_lat:.6f} {center_lon:.6f}")
        print(f"  Bounds: Lat [{min_lat:.6f}, {max_lat:.6f}], Lon [{min_lon:.6f}, {max_lon:.6f}]")
        print(f"  Coverage: {metadata['coverage_degrees']['latitude']:.6f}° × {metadata['coverage_degrees']['longitude']:.6f}°")
        print(f"  Records: {metadata['total_records']:,}")
        print()

print('='*70)
print('NOTE:')
print('  - Use the Center coordinates in OSM Web Wizard Position field')
print('  - Enable "Select Area" checkbox if you want to manually select bounds')
print('  - The bounds show the actual GPS coverage area for each scenario')
print('='*70)

