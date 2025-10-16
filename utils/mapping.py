#!/usr/bin/env python3
"""
GPS to SUMO coordinate mapping utilities
"""

import math
import traci
from typing import Tuple, Optional, List
import numpy as np

class GPSSumoMapper:
    """Handle GPS to SUMO coordinate conversion and edge matching"""
    
    def __init__(self, net_file: str = "osm.net.xml.gz"):
        self.net_file = net_file
        self.net = None
        self._load_network()
    
    def _load_network(self):
        """Load SUMO network"""
        try:
            from sumolib import net
            self.net = net.readNet(self.net_file)
            print(f"✅ Loaded SUMO network from {self.net_file}")
        except ImportError:
            print("⚠️  sumolib not available, using TraCI fallback")
            self.net = None
    
    def gps_to_sumo_xy(self, lat: float, lon: float) -> Optional[Tuple[float, float]]:
        """Convert GPS coordinates to SUMO XY coordinates"""
        
        try:
            if self.net:
                # Use sumolib for conversion
                x, y = self.net.convertLonLat2XY(lon, lat)
            else:
                # Fallback to TraCI
                x, y = traci.simulation.convertGeo(lon, lat)
            
            return x, y
            
        except Exception as e:
            print(f"❌ GPS conversion failed: {e}")
            return None
    
    def find_closest_edge(self, x: float, y: float, max_radius: float = 5000) -> Optional[str]:
        """Find the closest drivable edge to given SUMO coordinates"""
        
        min_distance = float('inf')
        closest_edge = None
        
        try:
            # Get all edges
            edge_ids = traci.edge.getIDList()
            drivable_edges = [e for e in edge_ids if not e.startswith(':') and not e.startswith('-')]
            
            print(f"     Debug: Looking for edge near ({x:.1f}, {y:.1f})")
            print(f"     Debug: Checking {len(drivable_edges)} drivable edges")
            
            for edge_id in drivable_edges[:50]:  # Check first 50 edges for debugging
                try:
                    # Get edge geometry
                    edge_shape = traci.edge.getShape(edge_id)
                    
                    # Calculate distance to edge
                    edge_distance = self._distance_to_edge(x, y, edge_shape)
                    
                    if edge_distance < min_distance and edge_distance < max_radius:
                        min_distance = edge_distance
                        closest_edge = edge_id
                        
                except Exception:
                    continue
            
            print(f"     Debug: Closest edge: {closest_edge}, distance: {min_distance:.1f}")
            return closest_edge
            
        except Exception as e:
            print(f"❌ Edge finding failed: {e}")
            return None
    
    def _distance_to_edge(self, x: float, y: float, edge_shape: List[Tuple[float, float]]) -> float:
        """Calculate minimum distance from point to edge shape"""
        
        min_distance = float('inf')
        
        for i in range(len(edge_shape) - 1):
            # Distance to line segment
            p1 = edge_shape[i]
            p2 = edge_shape[i + 1]
            
            distance = self._point_to_line_distance(x, y, p1[0], p1[1], p2[0], p2[1])
            min_distance = min(min_distance, distance)
        
        return min_distance
    
    def _point_to_line_distance(self, px: float, py: float, 
                               x1: float, y1: float, x2: float, y2: float) -> float:
        """Calculate distance from point to line segment"""
        
        # Vector from line start to point
        dx = px - x1
        dy = py - y1
        
        # Vector along line
        lx = x2 - x1
        ly = y2 - y1
        
        # Line length squared
        line_length_sq = lx * lx + ly * ly
        
        if line_length_sq == 0:
            # Line is a point
            return math.sqrt(dx * dx + dy * dy)
        
        # Project point onto line
        t = max(0, min(1, (dx * lx + dy * ly) / line_length_sq))
        
        # Closest point on line
        closest_x = x1 + t * lx
        closest_y = y1 + t * ly
        
        # Distance to closest point
        return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)
    
    def get_edge_position(self, edge_id: str, lane_index: int = 0) -> Optional[Tuple[float, float]]:
        """Get position on edge for vehicle placement"""
        
        try:
            # Get lane ID
            lane_ids = traci.edge.getLaneIDs(edge_id)
            if not lane_ids or lane_index >= len(lane_ids):
                lane_index = 0
            
            lane_id = lane_ids[lane_index]
            
            # Get lane position
            lane_pos = traci.lane.getPosition(lane_id)
            
            return lane_pos
            
        except Exception as e:
            print(f"❌ Failed to get edge position: {e}")
            return None
    
    def get_neighboring_edges(self, x: float, y: float, radius: float = 100) -> List[str]:
        """Get edges within radius of given position"""
        
        neighboring_edges = []
        
        try:
            edge_ids = traci.edge.getIDList()
            
            for edge_id in edge_ids:
                if edge_id.startswith(':') or edge_id.startswith('-'):
                    continue
                
                try:
                    edge_shape = traci.edge.getShape(edge_id)
                    distance = self._distance_to_edge(x, y, edge_shape)
                    
                    if distance <= radius:
                        neighboring_edges.append(edge_id)
                        
                except Exception:
                    continue
            
            return neighboring_edges
            
        except Exception as e:
            print(f"❌ Failed to get neighboring edges: {e}")
            return []
    
    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """Validate GPS coordinates"""
        
        return (-90 <= lat <= 90) and (-180 <= lon <= 180)
    
    def calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two SUMO positions"""
        
        return math.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)
