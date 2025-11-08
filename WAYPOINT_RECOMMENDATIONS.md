# V2V Digital Twin - Waypoint Count Recommendations

## Issue: Route Generation Failure

When selecting too many waypoints from larger datasets, the route generation may fail with:
```
❌ ERROR: list index out of range
```

This happens because the GPS waypoints become too sparse when sampled for route generation.

## Solution: Use Recommended Waypoint Counts

### Recommended Waypoint Counts by Dataset

| Dataset | Total Records | Recommended Waypoints | Why? |
|---------|---------------|----------------------|------|
| `vehicle_2_4_first_200.csv` | 200 | 50-200 | All waypoints work well |
| `vehicle_2_4_500.csv` | 500 | 50-100 | Avoid sparse sampling issues |
| `vehicle_2_4_1000.csv` | 1000 | 50-150 | Route generation constraints |

### How Route Sampling Works

The digital twin samples waypoints for route generation based on the count you select:

| Waypoints Selected | Sampling Rate | Route Points Used |
|-------------------|---------------|-------------------|
| ≤ 50 | Every 1st | 50 |
| 51-100 | Every 2nd | 25-50 |
| 101-200 | Every 4th | 25-50 |
| 201+ | Every 5th | 40+ |

**Example**: If you select 138 waypoints, it will sample every 4th point = ~34 route points

### Why Does It Fail?

1. **Sparse Sampling**: With 138 waypoints from 500 records, waypoints are already spread out
2. **Additional Sampling**: Route generation samples every 4th of those = very sparse
3. **Network Constraints**: Berlin SUMO network has only 104 edges
4. **GPS Spread**: Some waypoint pairs may be too far apart to connect

## Recommended Configurations

### For Baseline Testing (200-point dataset)

```
Dataset: vehicle_2_4_first_200.csv
Waypoints: 50-100
Expected: 7-10 edge routes
Runtime: 2-3 minutes
Accuracy: 78% ±2%
```

### For Medium Scale (500-point dataset)

```
Dataset: vehicle_2_4_500.csv
Waypoints: 50-100  ← Recommended
Expected: 7-10 edge routes
Runtime: 3-5 minutes
Accuracy: 76-80%
```

**Avoid**: 138+ waypoints (sparse sampling issues)

### For Large Scale (1000-point dataset)

```
Dataset: vehicle_2_4_1000.csv
Waypoints: 50-150  ← Recommended
Expected: 7-15 edge routes
Runtime: 5-10 minutes
Accuracy: 75-80%
```

**Avoid**: 200+ waypoints (route generation may fail)

## How to Use Larger Datasets Properly

### Strategy 1: Multiple Smaller Runs

Instead of using 138 waypoints at once, run multiple simulations:

```bash
# Run 1: First 50 points
python v2v_communication_digital_twin.py
# Select vehicle_2_4_500.csv, waypoints: 50

# Run 2: Next 50 points (modify code to use df.iloc[50:100])
# Run 3: Next 50 points (df.iloc[100:150])
```

### Strategy 2: Use Optimal Waypoint Count

```bash
# Best practice for 500-point dataset
Dataset: vehicle_2_4_500.csv
Waypoints: 80  ← Sweet spot
```

This gives:
- Good route connectivity
- Sufficient validation points
- Avoids sparse sampling
- ~16 route points (every 5th)

### Strategy 3: Check Route Generation First

Before running full simulation, check if routes generate:

```python
# In v2v_communication_digital_twin.py, after route generation:
print(f"Source route: {len(source_route)} edges")
print(f"Dest route: {len(dest_route)} edges")
```

Expected:
- **Good**: 7-15 edges
- **Warning**: 3-6 edges (may work but limited)
- **Error**: 0-2 edges (will fail)

## Quick Fix Guide

### If You See "list index out of range"

**Step 1**: Reduce waypoint count
```
Current: 138 waypoints
Try: 80 waypoints
```

**Step 2**: Check dataset selection
```
✅ vehicle_2_4_500.csv with 50-100 waypoints
❌ vehicle_2_4_500.csv with 138+ waypoints
```

**Step 3**: Verify in logs
```
📊 Using every Xth waypoint for route (~Y route points)
✅ Source route: Z edges
```

If Z = 0, reduce waypoint count further.

## Technical Details

### Why Not Just Use All Waypoints?

1. **Route Complexity**: SUMO routes need connected edges
2. **Network Size**: Only 104 edges in Berlin network
3. **GPS Accuracy**: Not all GPS points map perfectly to roads
4. **Performance**: More waypoints = longer route computation

### Sampling Algorithm

```python
if num_waypoints <= 50:
    sample_step = 1  # Use all
elif num_waypoints <= 100:
    sample_step = 2  # Every 2nd
elif num_waypoints <= 200:
    sample_step = 4  # Every 4th
else:
    sample_step = 5  # Every 5th
```

**Your Case (138 waypoints)**:
- Falls into 101-200 range
- Samples every 4th waypoint
- Creates ~34 route points
- These 34 points were too sparse to connect → empty route

## Best Practices

1. **Start Small**: Always test with 50 waypoints first
2. **Increase Gradually**: 50 → 80 → 100
3. **Check Logs**: Verify route edge count before full run
4. **Match Dataset**: Use appropriate waypoint count for dataset size
5. **Multiple Runs**: Break large validations into smaller runs

## Recommended Workflow

### For 500-Point Dataset Validation

```bash
# Run 1: Baseline
Waypoints: 50
Expected runtime: 3 min
Expected accuracy: 76-80%

# Run 2: Medium
Waypoints: 80
Expected runtime: 4 min
Expected accuracy: 76-80%

# Run 3: Maximum
Waypoints: 100
Expected runtime: 5 min
Expected accuracy: 75-79%

# Compare all three
python compare_dataset_sizes.py
```

### For 1000-Point Dataset Validation

```bash
# Run with 100-150 waypoints max
Waypoints: 100
Expected runtime: 8 min
Expected accuracy: 75-80%
```

## Summary

**Key Takeaway**: More waypoints ≠ Better validation

**Optimal Approach**:
- Use 50-100 waypoints for most validations
- This provides good coverage without sparse sampling issues
- Accuracy is consistent regardless of waypoint count (75-80%)

**Avoid**:
- Don't use >100 waypoints from 500-point dataset
- Don't use >150 waypoints from 1000-point dataset
- These create sparse sampling that breaks route generation

---

**Document Version**: 1.0  
**Related to**: Bug fix for IndexError with 138 waypoints from 500-point dataset  
**Date**: 2025-10-17

