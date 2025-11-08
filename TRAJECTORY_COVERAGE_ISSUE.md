# V2V Digital Twin - Trajectory Coverage Issue

## Problem Identified

**Real GPS Trajectory**: 845 meters (200 data points)  
**SUMO Simulation**: Only covers ~150-200 meters before vehicles complete route  
**Visual Issue**: Vehicles don't reach the traffic junction like in real data

## Root Cause Analysis

### 1. GPS Trajectory Distance
```
First 200 GPS points:
- Start: (52.509930, 13.357697)
- End: (52.506753, 13.346327)
- Straight-line distance: 845 meters
- Actual driving distance: ~900-1000 meters (following roads)
```

### 2. SUMO Network Coverage
```
Network size: 1370m x 564m  ✅ Large enough
Total edges: 104 edges
Coverage: Adequate for the trajectory
```

### 3. Actual Problem: Short Routes
```
Current route generation:
- Source route: 7 edges  ← Too short!
- Destination route: 7 edges  ← Too short!
- Typical edge length: 20-30 meters
- Total route coverage: ~140-210 meters  ← Only 15-25% of real trajectory!
```

## Why Routes Are So Short

### Current Algorithm Limitations

1. **Sparse Waypoint Sampling**:
   ```python
   # For 200 waypoints, samples every 5th = 40 route points
   # But only 7-10 of those create connected paths
   ```

2. **Dijkstra Path Failures**:
   - When waypoints are far apart, `getShortestPath()` may fail
   - Algorithm skips failed connections
   - Result: Only keeps successfully connected edges

3. **One-Way Streets**:
   - Some connections impossible due to traffic direction
   - Further reduces usable route edges

4. **Network Gaps**:
   - Not all GPS points map to connected road segments
   - Creates disconnected route fragments

## Solutions

### Option 1: Use More Waypoints for Route Generation (Quick Fix)

Modify the sampling to use MORE waypoints:

```python
# Current in v2v_communication_digital_twin.py lines 158-168
if num_waypoints <= 50:
    sample_step = 1  # Use all
elif num_waypoints <= 100:
    sample_step = 2  # Every 2nd
elif num_waypoints <= 200:
    sample_step = 4  # Every 4th ← Currently gives ~50 sampled points
else:
    sample_step = 5  # Every 5th

# CHANGE TO: Use more points
if num_waypoints <= 50:
    sample_step = 1
elif num_waypoints <= 100:
    sample_step = 1  # Use ALL points for better coverage
elif num_waypoints <= 200:
    sample_step = 2  # Every 2nd = 100 route points instead of 50
else:
    sample_step = 3  # Every 3rd instead of 5th
```

**Pros**: Simple one-line change  
**Cons**: May slow route generation, might still have gaps

### Option 2: Extend Routes to Cover Full Trajectory (Better Fix)

After initial route generation, extend the route to match the GPS trajectory distance:

```python
def extend_route_to_distance(net, initial_route, target_distance_m):
    """Extend route until it covers target distance"""
    
    current_distance = 0
    extended_route = initial_route.copy()
    
    # Calculate current route distance
    for edge_id in initial_route:
        edge = net.getEdge(edge_id)
        current_distance += edge.getLength()
    
    if current_distance >= target_distance_m:
        return extended_route  # Already long enough
    
    # Extend by following outgoing edges
    last_edge = net.getEdge(extended_route[-1])
    visited = set(extended_route)
    
    while current_distance < target_distance_m:
        outgoing = last_edge.getOutgoing()
        if not outgoing:
            break  # Dead end
        
        # Choose longest unvisited outgoing edge
        next_edges = [(e, e.getLength()) for e in outgoing.keys() 
                     if e.getID() not in visited]
        
        if not next_edges:
            break  # No new edges available
        
        next_edge = max(next_edges, key=lambda x: x[1])[0]
        extended_route.append(next_edge.getID())
        visited.add(next_edge.getID())
        current_distance += next_edge.getLength()
        last_edge = next_edge
    
    return extended_route
```

**Usage**:
```python
# After line 412 in v2v_communication_digital_twin.py
source_route, _ = find_optimal_path_through_waypoints(net, waypoints_df, 'source')

# Extend to cover full GPS trajectory
target_distance = 900  # meters (approximate real trajectory)
source_route = extend_route_to_distance(net, source_route, target_distance)
```

**Pros**: Guarantees full trajectory coverage  
**Cons**: May deviate from actual GPS path

### Option 3: Use Larger/Better SUMO Network (Best but Most Work)

Download a more complete Berlin road network:

```bash
# Option A: Larger area from OpenStreetMap
# 1. Go to openstreetmap.org
# 2. Export larger area around coordinates (52.506-52.510, 13.346-13.358)
# 3. Convert to SUMO network with netconvert

# Option B: Use Berlin's official SUMO network
# Download from: https://sumo.dlr.de/docs/Data/Scenarios/Berlin.html
```

**Pros**: Most realistic simulation  
**Cons**: Requires network setup, may be very large

### Option 4: Loop Routes (Simple Workaround)

Make vehicles loop through the route multiple times:

```xml
<!-- In route file -->
<vehicle id="v2v_source" type="v2v_source_type" depart="0.0" departSpeed="max">
    <route edges="edge1 edge2 ... edgeN edge1 edge2 ... edgeN edge1 edge2 ... edgeN"/>
    ↑ Repeat route 3-4 times
</vehicle>
```

**Pros**: Simple, extends simulation time  
**Cons**: Unrealistic (vehicles loop), doesn't match GPS trajectory

## Recommended Solution

**Combination of Option 1 + Option 2**:

1. **Increase waypoint sampling** (Option 1) - Get more connected edges
2. **Extend routes** (Option 2) - Ensure minimum 800m coverage
3. **Validate** - Check that routes actually cover the junction area

###  Implementation

I'll create an updated version with both fixes applied.

## Current vs Desired Behavior

### Current (Wrong)
```
GPS Trajectory: 845m across junction
SUMO Route: 140-210m, stops before junction
Vehicles: Complete route, simulation ends early
Coverage: Only 15-25% of real path
```

### Desired (Correct)
```
GPS Trajectory: 845m across junction
SUMO Route: 800-1000m, crosses junction
Vehicles: Cover full trajectory
Coverage: 95%+ of real path
```

## Why This Matters for Digital Twin

**Impact on Accuracy**:
- Current: Only validates first 15-25% of GPS data
- With fix: Validates 95%+ of GPS data
- Result: More comprehensive validation, better confidence in accuracy metrics

**Impact on Visualization**:
- Current: Vehicles stop early, don't match screenshot
- With fix: Vehicles cover full path through junction, matches real data

## Files to Modify

1. `v2v_communication_digital_twin.py`:
   - Line 158-168: Adjust sampling (Option 1)
   - After line 412: Add route extension (Option 2)

2. Create: `extend_routes.py` - Helper function for route extension

3. Update: `SCALING_GUIDE.md` - Document route coverage expectations

## Quick Test

After implementing fix, verify:
```bash
python v2v_communication_digital_twin.py
# In logs, should see:
✅ Source route: 25-40 edges (not 7)
✅ Estimated coverage: 800-1000m
```

## Next Steps

1. Implement Option 1 + 2 combination
2. Test with 200-point baseline
3. Verify vehicles reach junction in SUMO-GUI
4. Validate accuracy still ~78%
5. Apply to all continuous datasets (300, 400, 500)

---

**Priority**: HIGH  
**Impact**: Simulation only covers 15-25% of real trajectory  
**Solution Complexity**: MEDIUM (code changes to route generation)  
**Estimated Time**: 30-45 minutes to implement and test

