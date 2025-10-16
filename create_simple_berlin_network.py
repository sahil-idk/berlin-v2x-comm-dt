#!/usr/bin/env python3
"""
Create a simple Berlin network for SUMO using basic road network
"""

import subprocess
import sys

def create_simple_network():
    """Create a simple network for Berlin area"""
    print("=== CREATING SIMPLE BERLIN NETWORK ===\n")
    
    # Create a simple network file manually
    network_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<net version="1.9" junctionCornerDetail="5" limitTurnSpeed="5.5" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/net_file.xsd">
    <location netOffset="13.236472,52.469215" convBoundary="0.0,0.0,1410.0,1410.0" origBoundary="-10000000000.0,-10000000000.0,10000000000.0,10000000000.0" projParameter="+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"/>
    
    <!-- Junctions -->
    <junction id="junction_1" type="priority" x="0.0" y="0.0" incLanes="" intLanes="" shape="0.0,0.0 0.0,0.0"/>
    <junction id="junction_2" type="priority" x="100.0" y="0.0" incLanes="" intLanes="" shape="100.0,0.0 100.0,0.0"/>
    <junction id="junction_3" type="priority" x="200.0" y="0.0" incLanes="" intLanes="" shape="200.0,0.0 200.0,0.0"/>
    <junction id="junction_4" type="priority" x="0.0" y="100.0" incLanes="" intLanes="" shape="0.0,100.0 0.0,100.0"/>
    <junction id="junction_5" type="priority" x="100.0" y="100.0" incLanes="" intLanes="" shape="100.0,100.0 100.0,100.0"/>
    <junction id="junction_6" type="priority" x="200.0" y="100.0" incLanes="" intLanes="" shape="200.0,100.0 200.0,100.0"/>
    
    <!-- Edges -->
    <edge id="edge_1" from="junction_1" to="junction_2" priority="1">
        <lane id="edge_1_0" index="0" speed="13.89" length="100.0" shape="0.0,0.0 100.0,0.0"/>
    </edge>
    <edge id="edge_2" from="junction_2" to="junction_3" priority="1">
        <lane id="edge_2_0" index="0" speed="13.89" length="100.0" shape="100.0,0.0 200.0,0.0"/>
    </edge>
    <edge id="edge_3" from="junction_4" to="junction_5" priority="1">
        <lane id="edge_3_0" index="0" speed="13.89" length="100.0" shape="0.0,100.0 100.0,100.0"/>
    </edge>
    <edge id="edge_4" from="junction_5" to="junction_6" priority="1">
        <lane id="edge_4_0" index="0" speed="13.89" length="100.0" shape="100.0,100.0 200.0,100.0"/>
    </edge>
    <edge id="edge_5" from="junction_1" to="junction_4" priority="1">
        <lane id="edge_5_0" index="0" speed="13.89" length="100.0" shape="0.0,0.0 0.0,100.0"/>
    </edge>
    <edge id="edge_6" from="junction_2" to="junction_5" priority="1">
        <lane id="edge_6_0" index="0" speed="13.89" length="100.0" shape="100.0,0.0 100.0,100.0"/>
    </edge>
    <edge id="edge_7" from="junction_3" to="junction_6" priority="1">
        <lane id="edge_7_0" index="0" speed="13.89" length="100.0" shape="200.0,0.0 200.0,100.0"/>
    </edge>
    
    <!-- Connections -->
    <connection from="edge_1" to="edge_2" fromLane="0" toLane="0" dir="s" state="M"/>
    <connection from="edge_3" to="edge_4" fromLane="0" toLane="0" dir="s" state="M"/>
    <connection from="edge_5" to="edge_6" fromLane="0" toLane="0" dir="s" state="M"/>
    <connection from="edge_6" to="edge_7" fromLane="0" toLane="0" dir="s" state="M"/>
    <connection from="edge_1" to="edge_6" fromLane="0" toLane="0" dir="r" state="M"/>
    <connection from="edge_3" to="edge_6" fromLane="0" toLane="0" dir="l" state="M"/>
    <connection from="edge_2" to="edge_7" fromLane="0" toLane="0" dir="r" state="M"/>
    <connection from="edge_4" to="edge_7" fromLane="0" toLane="0" dir="l" state="M"/>
</net>'''
    
    # Write network file
    with open('berlin_network.net.xml', 'w') as f:
        f.write(network_xml)
    
    print("Simple Berlin network created successfully!")
    print("Network file: berlin_network.net.xml")
    return True

if __name__ == "__main__":
    create_simple_network()
