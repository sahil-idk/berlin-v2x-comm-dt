#!/usr/bin/env python3
"""
Create a minimal working network for SUMO
"""

def create_minimal_network():
    """Create a minimal but working network"""
    print("Creating minimal working network...")
    
    network_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<net version="1.9" junctionCornerDetail="5" limitTurnSpeed="5.5" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/net_file.xsd">
    <location netOffset="0.0,0.0" convBoundary="0.0,0.0,1000.0,1000.0" origBoundary="-10000000000.0,-10000000000.0,10000000000.0,10000000000.0" projParameter="+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"/>
    
    <!-- Simple junctions -->
    <junction id="junction_1" type="priority" x="0.0" y="0.0" incLanes="" intLanes="" shape="0.0,0.0 0.0,0.0"/>
    <junction id="junction_2" type="priority" x="500.0" y="0.0" incLanes="" intLanes="" shape="500.0,0.0 500.0,0.0"/>
    <junction id="junction_3" type="priority" x="1000.0" y="0.0" incLanes="" intLanes="" shape="1000.0,0.0 1000.0,0.0"/>
    
    <!-- Simple edges -->
    <edge id="edge_1" from="junction_1" to="junction_2" priority="1">
        <lane id="edge_1_0" index="0" speed="13.89" length="500.0" shape="0.0,0.0 500.0,0.0"/>
    </edge>
    <edge id="edge_2" from="junction_2" to="junction_3" priority="1">
        <lane id="edge_2_0" index="0" speed="13.89" length="500.0" shape="500.0,0.0 1000.0,0.0"/>
    </edge>
    
    <!-- Simple connections -->
    <connection from="edge_1" to="edge_2" fromLane="0" toLane="0" dir="s" state="M"/>
</net>'''
    
    # Write network file
    with open('berlin_network.net.xml', 'w') as f:
        f.write(network_xml)
    
    print("Minimal network created successfully!")
    return True

if __name__ == "__main__":
    create_minimal_network()
