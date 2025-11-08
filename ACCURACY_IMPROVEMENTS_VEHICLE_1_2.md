# Vehicle 1-2 Accuracy Improvements

## 🔍 Problem Analysis

### Current Issues:
1. **Low Distance Accuracy: 24.58%** ❌
2. **Low SNR Accuracy: 18.77%** ❌
3. **Low Overall Quality: 38.95%** ❌
4. **Only 44 waypoints analyzed** (out of 386 loaded)
5. **Routes too short**: 12 edges (source), 8 edges (dest)
6. **Vehicles finish early**: Routes complete before covering all waypoints

### Root Causes:

#### 1. Sparse Route Sampling
- **Current**: Every 7th waypoint used for route generation
- **Result**: Only ~55 route points from 386 waypoints
- **Impact**: Routes are too short, vehicles finish quickly

#### 2. Waypoint Tracking Issues
- **Current**: Finds "closest" waypoint globally
- **Problem**: Can jump backwards (waypoint 126 → 9 → 6)
- **Impact**: Inaccurate waypoint progress tracking

#### 3. Calibration Disabled
- **Current**: No calibration (factor = 1.0)
- **Analysis shows**: Optimal calibration = 1.135 (simulated distances are smaller)
- **But**: Even with optimal calibration, accuracy only 22.27%
- **Conclusion**: Calibration alone won't fix the issue

## ✅ Improvements Made

### 1. Denser Route Sampling
**Before**: Every 7th waypoint (for 386 waypoints)  
**After**: 
- ≤200 waypoints: Every 2nd waypoint
- ≤500 waypoints: Every 3rd waypoint  
- >500 waypoints: Every 4th waypoint

**Expected Result**: Longer routes (more edges), vehicles cover more waypoints

### 2. Improved Waypoint Tracking
**Before**: Global search for closest waypoint (can jump backwards)  
**After**: 
- Localized search around current waypoint (±5 to +20)
- Only advances if moving forward or very close (<50m)
- Prevents backward jumps

**Expected Result**: Sequential waypoint progression, more waypoints analyzed

### 3. Better Waypoint Progress Calculation
**Before**: `min(source_progress, dest_progress)`  
**After**: Average of both vehicles' progress with forward-only advancement

**Expected Result**: More stable waypoint tracking

### 4. Calibration Options
- **Adaptive**: No calibration (1.0) - for when waypoints are accurate
- **Old Calibration**: 0.607 - checkbox option if accuracy is low
- Can be toggled in GUI

## 📊 Expected Improvements

### Route Length
- **Before**: 12-8 edges (~2.5km total)
- **After**: 30-50+ edges (expect 3-5km+ routes)
- **Impact**: Vehicles stay active longer, cover more waypoints

### Waypoints Analyzed
- **Before**: 44 waypoints
- **After**: 100-200+ waypoints (expect 3-5x more)
- **Impact**: More data points for analysis

### Accuracy
- **Before**: 24.58% distance accuracy
- **Expected**: 60-80%+ distance accuracy
- **Reason**: More waypoints, better tracking, longer routes

## 🎯 Recommendations

### For Best Accuracy:

1. **Use Denser Sampling**:
   - Enable "Use All Waypoints" checkbox
   - Or reduce waypoint slider to 200-300 for denser sampling

2. **Try Old Calibration**:
   - If accuracy is still low, check "Use Old Calibration (0.607)"
   - This applies the calibration factor from Vehicle 2-4 baseline

3. **Monitor Waypoint Progress**:
   - Check that waypoints advance sequentially (not jumping)
   - If stuck at same waypoint, routes may be too short

4. **Compare with Vehicle 2-4**:
   - Vehicle 2-4 uses calibration 0.607
   - If Vehicle 1-2 accuracy is much lower, may need different approach

## 🔧 If Accuracy Still Low

### Option 1: Apply Calibration Factor
```python
# In get_adaptive_calibration(), try:
return 0.85  # If simulated distances are too large
# or
return 1.15  # If simulated distances are too small
```

### Option 2: Reduce Waypoints
- Use 200-300 waypoints instead of 2000
- Ensures denser route sampling
- Routes will be longer relative to waypoint count

### Option 3: Check Route Generation
- Verify routes follow GPS trajectory
- Routes should be 30-50+ edges for good coverage
- If routes are still short, waypoints may be too far apart

## 📈 Success Metrics

After improvements, expect:
- ✅ **Distance Accuracy**: 60-80%+ (vs 24.58%)
- ✅ **SNR Accuracy**: 60-80%+ (vs 18.77%)
- ✅ **Waypoints Analyzed**: 100-200+ (vs 44)
- ✅ **Overall Quality**: 70%+ (vs 38.95%)

If these aren't met, the issue may be:
- Routes still too short
- Waypoint GPS coordinates don't match SUMO network well
- Need different calibration factor

