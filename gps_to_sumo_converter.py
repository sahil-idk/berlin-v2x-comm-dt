#!/usr/bin/env python3
"""
GPS to SUMO Coordinate Conversion Helper
Converts GPS coordinates to SUMO network coordinates using proper projection
"""

import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
import gzip
import os
from typing import Tuple, Optional

class GPSToSUMOConverter:
    """Convert GPS coordinates to SUMO coordinates using network projection"""
    
    def __init__(self, net_file_path: str):
        self.net_file_path = net_file_path
        self.projection_params = None
        self.net_bounds = None
        self._load_network_info()
        
    def _load_network_info(self):
        """Load network file and extract projection information"""
        try:
            # Handle compressed files
            if self.net_file_path.endswith('.gz'):
                with gzip.open(self.net_file_path, 'rt') as f:
                    content = f.read()
            else:
                with open(self.net_file_path, 'r') as f:
                    content = f.read()
                    
            # Parse XML
            root = ET.fromstring(content)
            
            # Extract location element
            location = root.find('location')
            if location is not None:
                # Get projection parameters
                proj = location.get('projParameter', '')
                if proj:
                    self.projection_params = proj
                    
                # Get network bounds
                net_offset = location.get('netOffset', '0,0')
                conv_boundary = location.get('convBoundary', '')
                orig_boundary = location.get('origBoundary', '')
                
                if conv_boundary:
                    bounds = [float(x) for x in conv_boundary.split(',')]
                    self.net_bounds = {
                        'x_min': bounds[0],
                        'y_min': bounds[1], 
                        'x_max': bounds[2],
                        'y_max': bounds[3]
                    }
                    
                print(f"Network projection: {self.projection_params}")
                print(f"Network bounds: {self.net_bounds}")
                
        except Exception as e:
            print(f"Warning: Could not load network info: {e}")
            # Use default Berlin projection
            self.projection_params = "+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
            
    def gps_to_sumo(self, lat: float, lon: float) -> Tuple[float, float]:
        """Convert GPS coordinates to SUMO coordinates"""
        
        # For Berlin area, use UTM Zone 33N
        # This is a simplified conversion - for production use pyproj
        
        # Berlin approximate bounds
        berlin_lat_min, berlin_lat_max = 52.3, 52.7
        berlin_lon_min, berlin_lon_max = 13.0, 13.8
        
        # Check if coordinates are within Berlin bounds
        if not (berlin_lat_min <= lat <= berlin_lat_max and 
                berlin_lon_min <= lon <= berlin_lon_max):
            print(f"Warning: Coordinates ({lat}, {lon}) may be outside Berlin area")
            
        # Convert to UTM (simplified)
        # UTM Zone 33N for Berlin
        zone = 33
        false_easting = 500000
        false_northing = 0
        
        # Convert lat/lon to UTM
        x, y = self._latlon_to_utm(lat, lon, zone)
        
        # Apply network offset if available
        if self.net_bounds:
            # Adjust coordinates to network coordinate system
            x_offset = self.net_bounds['x_min']
            y_offset = self.net_bounds['y_min']
            x -= x_offset
            y -= y_offset
            
        return x, y
        
    def _latlon_to_utm(self, lat: float, lon: float, zone: int) -> Tuple[float, float]:
        """Convert lat/lon to UTM coordinates (simplified)"""
        
        # WGS84 ellipsoid parameters
        a = 6378137.0  # semi-major axis
        e2 = 0.00669438  # first eccentricity squared
        
        # Convert to radians
        lat_rad = np.radians(lat)
        lon_rad = np.radians(lon)
        
        # Central meridian
        lon0 = np.radians((zone - 1) * 6 - 180 + 3)
        
        # UTM parameters
        k0 = 0.9996  # scale factor
        false_easting = 500000
        false_northing = 0
        
        # Calculate intermediate values
        N = a / np.sqrt(1 - e2 * np.sin(lat_rad)**2)
        T = np.tan(lat_rad)**2
        C = e2 * np.cos(lat_rad)**2 / (1 - e2)
        A = np.cos(lat_rad) * (lon_rad - lon0)
        
        # Calculate M (meridional arc)
        M = a * ((1 - e2/4 - 3*e2**2/64 - 5*e2**3/256) * lat_rad
                - (3*e2/8 + 3*e2**2/32 + 45*e2**3/1024) * np.sin(2*lat_rad)
                + (15*e2**2/256 + 45*e2**3/1024) * np.sin(4*lat_rad)
                - (35*e2**3/3072) * np.sin(6*lat_rad))
        
        # Calculate UTM coordinates
        x = k0 * N * (A + (1-T+C)*A**3/6 + (5-18*T+T**2+72*C-58)*A**5/120) + false_easting
        y = k0 * (M + N*np.tan(lat_rad)*(A**2/2 + (5-T+9*C+4*C**2)*A**4/24 + (61-58*T+T**2+600*C-330)*A**6/720)) + false_northing
        
        return x, y
        
    def batch_convert(self, df: pd.DataFrame, lat_col: str, lon_col: str) -> pd.DataFrame:
        """Convert a dataframe of GPS coordinates to SUMO coordinates"""
        
        result_df = df.copy()
        
        # Convert coordinates
        sumo_coords = []
        for _, row in df.iterrows():
            lat, lon = row[lat_col], row[lon_col]
            if pd.notna(lat) and pd.notna(lon):
                x, y = self.gps_to_sumo(lat, lon)
                sumo_coords.append((x, y))
            else:
                sumo_coords.append((np.nan, np.nan))
                
        # Add SUMO coordinates to dataframe
        result_df[f'{lat_col}_sumo_x'] = [coord[0] for coord in sumo_coords]
        result_df[f'{lon_col}_sumo_y'] = [coord[1] for coord in sumo_coords]
        
        return result_df


def test_conversion():
    """Test the coordinate conversion with sample data"""
    
    # Test coordinates (Berlin area)
    test_coords = [
        (52.5200, 13.4050),  # Berlin center
        (52.4949, 13.3049),  # From sumo_points.csv
        (52.5099, 13.3600),  # From sumo_points.csv
    ]
    
    # Create converter
    net_file = "sumo-config/osm.net.xml.gz"
    if os.path.exists(net_file):
        converter = GPSToSUMOConverter(net_file)
    else:
        print("Network file not found, using default projection")
        converter = GPSToSUMOConverter("dummy")
        
    print("Testing GPS to SUMO coordinate conversion:")
    print("-" * 50)
    
    for lat, lon in test_coords:
        x, y = converter.gps_to_sumo(lat, lon)
        print(f"GPS: ({lat:.6f}, {lon:.6f}) -> SUMO: ({x:.2f}, {y:.2f})")


if __name__ == "__main__":
    test_conversion()
