#!/usr/bin/env python3
"""
Simple TraCI Test - Verify SUMO connection works
"""

import traci
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_traci_connection():
    """Test basic TraCI connection"""
    logger.info("Testing TraCI connection...")
    
    try:
        # Start SUMO with minimal config
        sumo_cmd = [
            "sumo-gui",
            "-c", "sumo-config/osm.sumocfg",
            "--no-step-log",
            "--start"
        ]
        
        traci.start(sumo_cmd)
        logger.info("SUMO started successfully")
        
        # Get network info
        edges = traci.edge.getIDList()
        logger.info(f"Found {len(edges)} edges in network")
        
        # Get simple edges
        simple_edges = [e for e in edges if not e.startswith('-') and not e.startswith(':') and len(e) < 20]
        logger.info(f"Found {len(simple_edges)} simple edges")
        
        if len(simple_edges) >= 2:
            src_edge = simple_edges[0]
            dst_edge = simple_edges[1]
            
            logger.info(f"Testing with edges: {src_edge} -> {dst_edge}")
            
            # Test route finding
            try:
                route = traci.simulation.findRoute(src_edge, dst_edge)
                logger.info(f"Route found with {len(route.edges)} edges")
            except Exception as e:
                logger.warning(f"Route finding failed: {e}")
                
            # Test vehicle addition
            try:
                traci.vehicle.add(
                    vehID="test_vehicle",
                    typeID="DEFAULT_VEHTYPE",
                    routeID="",
                    depart=0.0,
                    departLane="best"
                )
                traci.vehicle.changeTarget("test_vehicle", dst_edge)
                logger.info("Test vehicle added successfully")
                
                # Run a few simulation steps
                for step in range(10):
                    traci.simulationStep()
                    if "test_vehicle" in traci.vehicle.getIDList():
                        pos = traci.vehicle.getPosition("test_vehicle")
                        logger.info(f"Step {step}: Vehicle at ({pos[0]:.1f}, {pos[1]:.1f})")
                    else:
                        logger.info(f"Step {step}: Vehicle completed journey")
                        break
                        
            except Exception as e:
                logger.error(f"Vehicle test failed: {e}")
                
        traci.close()
        logger.info("TraCI test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"TraCI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_traci_connection()
    if success:
        print("✅ TraCI connection test passed!")
    else:
        print("❌ TraCI connection test failed!")
