#!/usr/bin/env python3
"""
Improved GPS to SUMO edge mapping with better accuracy
"""

import traci
import pandas as pd
import numpy as np
import math

class ImprovedGPSMapper:
    """Better GPS to SUMO edge mapping"""
    
    def __init__(self):
        self.edge_positions = {}
        
    def gps_to_sumo(self, lat, lon):
        """Convert GPS to SUMO coordinates using sumolib if available"""
        try:
            # Try sumolib first for better accuracy
            from sumolib import net
            net_file = net.readNet('sumo-config/osm.net.xml.gz')
            x, y = net_file.convertLonLat2XY(lon, lat)
            return x, y
        except ImportError:
            # Fallback to traci
            try:
                x, y = traci.simulation.convertGeo(lon, lat)
                return x, y
            except:
                return None, None
    
    def find_best_edges_for_gps(self, src_lat, src_lon, dst_lat, dst_lon):
        """Find the best edges for GPS coordinates using direct position matching"""
        
        # Convert GPS to SUMO coordinates
        src_x, src_y = self.gps_to_sumo(src_lat, src_lon)
        dst_x, dst_y = self.gps_to_sumo(dst_lat, dst_lon)
        
        if not all([src_x, src_y, dst_x, dst_y]):
            print("❌ GPS conversion failed")
            return None, None
            
        print(f"📍 GPS Conversion:")
        print(f"   Source GPS: ({src_lat:.6f}, {src_lon:.6f}) → SUMO: ({src_x:.2f}, {src_y:.2f})")
        print(f"   Dest GPS: ({dst_lat:.6f}, {dst_lon:.6f}) → SUMO: ({dst_x:.2f}, {dst_y:.2f})")
        
        # Calculate distance between vehicles
        vehicle_distance = math.sqrt((dst_x - src_x)**2 + (dst_y - src_y)**2)
        print(f"   Vehicle distance: {vehicle_distance:.2f}m")
        
        # Find edge closest to source
        src_edge = self.find_closest_edge_to_position(src_x, src_y)
        dst_edge = self.find_closest_edge_to_position(dst_x, dst_y)
        
        if src_edge and dst_edge:
            print(f"🎯 Selected edges:")
            print(f"   Source edge: {src_edge}")
            print(f"   Destination edge: {dst_edge}")
            
            # Verify edges are different and reachable
            if src_edge == dst_edge:
                print("⚠️  Warning: Same edge selected for both vehicles")
                # Try to find a nearby different edge for destination
                dst_edge = self.find_different_nearby_edge(src_edge, dst_x, dst_y)
                
            return src_edge, dst_edge, src_x, src_y, dst_x, dst_y
            
        return None, None, None, None, None, None
    
    def find_closest_edge_to_position(self, x, y, max_distance=2000):
        """Find edge closest to given SUMO position using multiple methods."""
        min_distance = float('inf')
        closest_edge = None
        
        # Method 1: Use edge junctions (more reliable)
        for edge_id in traci.edge.getIDList():
            # Skip internal edges
            if edge_id.startswith(':') or edge_id.startswith('-') or 'cluster' in edge_id:
                continue
                
            try:
                # Get edge from/to junctions
                from_junction = traci.edge.getFromJunction(edge_id)
                to_junction = traci.edge.getToJunction(edge_id)
                
                from_pos = traci.junction.getPosition(from_junction)
                to_pos = traci.junction.getPosition(to_junction)
                
                # Calculate distance to edge center
                edge_center_x = (from_pos[0] + to_pos[0]) / 2
                edge_center_y = (from_pos[1] + to_pos[1]) / 2
                
                distance = math.sqrt((x - edge_center_x)**2 + (y - edge_center_y)**2)
                
                if distance < min_distance and distance < max_distance:
                    min_distance = distance
                    closest_edge = edge_id
                    
            except:
                continue
                
        if closest_edge:
            print(f"   Found edge {closest_edge} at {min_distance:.2f}m (junction method)")
            return closest_edge
            
        # Method 2: Try any edge without constraints if method 1 fails
        print("   Junction method failed, trying broad search...")
        min_distance = float('inf')
        
        for edge_id in traci.edge.getIDList():
            try:
                from_junction = traci.edge.getFromJunction(edge_id)
                from_pos = traci.junction.getPosition(from_junction)
                
                distance = math.sqrt((x - from_pos[0])**2 + (y - from_pos[1])**2)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_edge = edge_id
                    
            except:
                continue
                
        if closest_edge:
            print(f"   Found edge {closest_edge} at {min_distance:.2f}m (fallback)")
            
        return closest_edge
    
    def find_different_nearby_edge(self, avoid_edge, target_x, target_y):
        """Find a different edge near the target position"""
        min_distance = float('inf')
        closest_edge = None
        
        # Find the 2nd closest edge (different from avoid_edge)
        for edge_id in traci.edge.getIDList():
            if edge_id == avoid_edge or edge_id.startswith(':') or edge_id.startswith('-') or 'cluster' in edge_id:
                continue
                
            try:
                from_junction = traci.edge.getFromJunction(edge_id)
                from_pos = traci.junction.getPosition(from_junction)
                
                distance = math.sqrt((target_x - from_pos[0])**2 + (target_y - from_pos[1])**2)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_edge = edge_id
                    
            except:
                continue
                
        if closest_edge:
            print(f"   Found nearby different edge: {closest_edge} at {min_distance:.2f}m")
        else:
            print(f"   No different edge found, keeping original")
            
        return closest_edge if closest_edge else avoid_edge

def test_gps_mapping():
    """Test GPS mapping with sample coordinates"""
    
    # Start SUMO with config
    sumo_cmd = [
        "sumo-gui",
        "-c", "sumo-config/osm.sumocfg",
        "--no-step-log",
        "--ignore-route-errors"
    ]
    
    traci.start(sumo_cmd, port=8813, label="test")
    
    mapper = ImprovedGPSMapper()
    
    # Test with CSV data
    df = pd.read_csv('sidelink_parsed.csv')
    valid_rows = df[
        (df['Source'] != df['Destination']) & 
        df['Latitude_destination'].notna() & 
        df['Longitude_destination'].notna()
    ].copy()
    
    print(f"📊 Testing with {len(valid_rows)} valid rows...")
    
    # Limit to first 10 rows
    for i in range(min(10, len(valid_rows))):
        row = valid_rows.iloc[i]
        
        print(f"\n🔄 Row {i}:")
        print(f"   Source: {row['Source']} → Dest: {row['Destination']}")
        
        result = mapper.find_best_edges_for_gps(
            row['Latitude_source'], row['Longitude_source'],
            row['Latitude_destination'], row['Longitude_destination']
        )
        
        if result and result[0] and result[1]:
            print(f"✅ Success: {result[0]} → {result[1]}")
        else:
            print(f"❌ Failed")
    
    traci.close()

if __name__ == "__main__":
    test_gps_mapping()
