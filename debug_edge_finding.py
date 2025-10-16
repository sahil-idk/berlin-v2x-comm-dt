#!/usr/bin/env python3
"""
Debug script to test edge finding with improved coordinate conversion
"""

import traci
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_edge_finding():
    """Test edge finding with sample coordinates"""
    
    # Start SUMO
    sumo_cmd = [
        "sumo", "-c", "sumo-config/osm.sumocfg",
        "--no-step-log"
    ]
    
    try:
        traci.start(sumo_cmd)
        logger.info("SUMO started successfully")
        
        # Get network info
        bounds = traci.simulation.getNetBoundary()
        edges = traci.edge.getIDList()
        
        logger.info(f"Network bounds: {bounds}")
        logger.info(f"Total edges: {len(edges)}")
        
        # Test coordinate conversion
        def gps_to_sumo(lat: float, lon: float):
            lat_norm = (lat - 52.3) / 0.4
            lon_norm = (lon - 13.0) / 0.8
            x = lon_norm * 19873.71
            y = lat_norm * 12467.71
            return x, y
        
        def find_closest_edge(x: float, y: float):
            min_dist = float('inf')
            closest_edge = None
            
            for edge_id in edges[:100]:  # Test first 100 edges
                try:
                    # Use the correct TraCI API
                    shape = traci.edge.getShape(edge_id)
                    if shape:
                        edge_center_x = sum(point[0] for point in shape) / len(shape)
                        edge_center_y = sum(point[1] for point in shape) / len(shape)
                        
                        dist = np.sqrt((x - edge_center_x)**2 + (y - edge_center_y)**2)
                        if dist < min_dist:
                            min_dist = dist
                            closest_edge = edge_id
                except Exception as e:
                    logger.warning(f"Error processing edge {edge_id}: {e}")
                    continue
                    
            return closest_edge, min_dist
        
        # Test with sample coordinates from sumo_points.csv
        test_coords = [
            (52.494875, 13.304918333333331),
            (52.50987666666666, 13.360006666666669),
            (52.51278666666666, 13.286895)
        ]
        
        logger.info("Testing coordinate conversion and edge finding:")
        for lat, lon in test_coords:
            x, y = gps_to_sumo(lat, lon)
            edge, dist = find_closest_edge(x, y)
            
            logger.info(f"GPS ({lat:.6f}, {lon:.6f}) -> SUMO ({x:.2f}, {y:.2f})")
            logger.info(f"  Closest edge: {edge}, distance: {dist:.2f}m")
            
        # Test with some actual edge coordinates
        logger.info("\nTesting with actual edge coordinates:")
        for edge_id in edges[:5]:
            try:
                shape = traci.edge.getShape(edge_id)
                if shape:
                    edge_x = sum(point[0] for point in shape) / len(shape)
                    edge_y = sum(point[1] for point in shape) / len(shape)
                    
                    logger.info(f"Edge {edge_id} at ({edge_x:.2f}, {edge_y:.2f})")
                    
                    # Test finding this edge
                    found_edge, dist = find_closest_edge(edge_x, edge_y)
                    logger.info(f"  Found edge: {found_edge}, distance: {dist:.2f}m")
                    
                    # Show edge shape
                    logger.info(f"  Shape points: {len(shape)} points")
                    if len(shape) > 0:
                        logger.info(f"  First point: {shape[0]}")
                        
            except Exception as e:
                logger.warning(f"Error processing edge {edge_id}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        traci.close()

if __name__ == "__main__":
    test_edge_finding()
