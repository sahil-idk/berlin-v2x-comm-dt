# Multi-Scenario Digital Twin Extension Plan

## 📊 Current Status

### ✅ Completed:
- **Vehicle 1-2**: Fully working digital twin with waypoint visualization
  - `visualize_vehicle_1_2_waypoints.py`
  - `v2v_communication_digital_twin_vehicle_1_2.py`
  - `veh_1_2_sumo_config/` directory
  - `scenarios/vehicle_1_2_first_2000.csv`

### ⏳ Remaining Scenarios:
- **Vehicle 1-3**: 58,907 records
- **Vehicle 1-4**: 48,534 records
- **Vehicle 2-3**: 56,916 records
- **Vehicle 2-4**: 61,925 records (original script exists, needs update)
- **Vehicle 3-4**: 42,165 records

---

## 🎯 Two Approaches: Individual vs Unified

### **Option A: Individual Scripts (Current Approach)**
**Pros:**
- ✅ Easy to customize per scenario
- ✅ Clear separation of concerns
- ✅ Can run scenarios independently
- ✅ Easy to debug specific scenarios

**Cons:**
- ❌ Code duplication (6 similar scripts)
- ❌ Maintenance overhead (changes need to be applied 6 times)
- ❌ More files to manage

**Best for:** Testing, debugging, scenario-specific tuning

### **Option B: Unified Multi-Scenario Script**
**Pros:**
- ✅ Single codebase to maintain
- ✅ Consistent behavior across scenarios
- ✅ Easy to add new scenarios
- ✅ Scenario selection via dropdown

**Cons:**
- ❌ More complex code
- ❌ Harder to customize per scenario
- ❌ Potential for bugs affecting all scenarios

**Best for:** Production, long-term maintenance

---

## 📋 Recommended Approach: **Hybrid**

### Phase 1: Create Individual Scripts (Quick)
- Create scripts for remaining 5 scenarios based on Vehicle 1-2 template
- Fast to implement, easy to test each scenario independently
- **Timeline**: ~2-3 hours per scenario

### Phase 2: Unified Script (Long-term)
- After all scenarios are working, refactor into unified script
- Extract common code, use scenario selection
- **Timeline**: ~4-6 hours refactoring

---

## 🗺️ Step-by-Step Plan for Each Scenario

### **For Each Remaining Scenario (1-3, 1-4, 2-3, 2-4, 3-4):**

#### **Step 1: OSM Web Wizard Setup** ⏱️ 10-15 min per scenario
1. Open OSM Web Wizard
2. Enter scenario center coordinates (from `OSM_WEB_WIZARD_COORDINATES.md`)
3. Enable "Select Area" checkbox
4. Draw coverage rectangle (same area for all - they overlap)
5. Set options:
   - Duration: 3600
   - ✅ Add Polygons
   - ⬜ Other options (default)
6. Generate scenario
7. Save to: `veh_X_Y_sumo_config/` directory

**Note**: Since all scenarios are in same Berlin area, you could:
- **Option A**: Generate separate networks (more accurate)
- **Option B**: Reuse `veh_1_2_sumo_config/` for all (faster, less accurate)

#### **Step 2: Extract First 2000 Points** ⏱️ 1 min per scenario
```python
# Create: extract_scenario_X_Y_points.py (or unified script)
# Load: scenarios/vehicle_X_Y.csv
# Extract: First 2000 points
# Save: scenarios/vehicle_X_Y_first_2000.csv
```

#### **Step 3: Create Waypoint Visualization** ⏱️ 15 min per scenario
**Template**: Copy `visualize_vehicle_1_2_waypoints.py`

**Changes needed**:
- Update `SCENARIO_CSV` path
- Update `SUMO_CONFIG_DIR` path
- Update vehicle IDs from metadata
- Update scenario name in output messages

**Output**: `visualize_vehicle_X_Y_waypoints.py`

#### **Step 4: Create Digital Twin Script** ⏱️ 30 min per scenario
**Template**: Copy `v2v_communication_digital_twin_vehicle_1_2.py`

**Changes needed**:
- Update `SCENARIO_NAME` constant
- Update `SCENARIO_CSV` path
- Update `SUMO_CONFIG_DIR` path
- Update GUI title
- Update output file names (CSV, JSON)

**Output**: `v2v_communication_digital_twin_vehicle_X_Y.py`

#### **Step 5: Test & Validate** ⏱️ 30-60 min per scenario
1. Run waypoint visualization → Verify waypoints visible
2. Run digital twin → Check:
   - Routes generated correctly (30-50+ edges)
   - Vehicles follow trajectories
   - Waypoints analyzed sequentially
   - Accuracy metrics reasonable
   - Analysis files saved correctly

---

## 📁 Expected File Structure After Completion

```
berlin_v2x/
├── scenarios/
│   ├── vehicle_1_2.csv / vehicle_1_2_first_2000.csv / vehicle_1_2_metadata.json ✅
│   ├── vehicle_1_3.csv / vehicle_1_3_first_2000.csv / vehicle_1_3_metadata.json ⏳
│   ├── vehicle_1_4.csv / vehicle_1_4_first_2000.csv / vehicle_1_4_metadata.json ⏳
│   ├── vehicle_2_3.csv / vehicle_2_3_first_2000.csv / vehicle_2_3_metadata.json ⏳
│   ├── vehicle_2_4.csv / vehicle_2_4_first_2000.csv / vehicle_2_4_metadata.json ✅ (update)
│   ├── vehicle_3_4.csv / vehicle_3_4_first_2000.csv / vehicle_3_4_metadata.json ⏳
│   └── scenarios_list.json ✅
│
├── veh_1_2_sumo_config/ ✅
├── veh_1_3_sumo_config/ ⏳
├── veh_1_4_sumo_config/ ⏳
├── veh_2_3_sumo_config/ ⏳
├── veh_2_4_sumo_config/ ⏳ (or reuse existing)
├── veh_3_4_sumo_config/ ⏳
│
├── visualize_vehicle_1_2_waypoints.py ✅
├── visualize_vehicle_1_3_waypoints.py ⏳
├── visualize_vehicle_1_4_waypoints.py ⏳
├── visualize_vehicle_2_3_waypoints.py ⏳
├── visualize_vehicle_2_4_waypoints.py ⏳
├── visualize_vehicle_3_4_waypoints.py ⏳
│
├── v2v_communication_digital_twin_vehicle_1_2.py ✅
├── v2v_communication_digital_twin_vehicle_1_3.py ⏳
├── v2v_communication_digital_twin_vehicle_1_4.py ⏳
├── v2v_communication_digital_twin_vehicle_2_3.py ⏳
├── v2v_communication_digital_twin_vehicle_2_4.py ⏳ (update existing)
├── v2v_communication_digital_twin_vehicle_3_4.py ⏳
│
└── Analysis outputs:
    ├── vehicle_1_2_communication_analysis.csv ✅
    ├── vehicle_1_2_communication_summary.json ✅
    └── ... (5 more scenarios)
```

---

## 🚀 Implementation Order (Recommended)

### **Priority 1: Vehicle 2-4** (Update Existing)
- **Why**: Already has working script, just needs updates
- **Effort**: Low (30 min)
- **Changes**: Apply improvements from Vehicle 1-2

### **Priority 2: Vehicle 1-3 & Vehicle 1-4**
- **Why**: Similar to Vehicle 1-2 (same source vehicle)
- **Effort**: Medium (1-2 hours each)
- **Benefit**: Compare Vehicle 1 behavior across different destinations

### **Priority 3: Vehicle 2-3 & Vehicle 3-4**
- **Why**: Different vehicle pairs
- **Effort**: Medium (1-2 hours each)
- **Benefit**: Complete coverage of all vehicle interactions

---

## 🔧 Key Decisions Needed

### **Decision 1: SUMO Network Strategy**
**Option A**: Separate networks per scenario
- ✅ More accurate per scenario
- ✅ Better coverage
- ❌ More setup time (6 networks to generate)
- ❌ More disk space

**Option B**: Reuse one network (e.g., `veh_1_2_sumo_config/`)
- ✅ Faster setup
- ✅ Less disk space
- ✅ Same Berlin area anyway
- ❌ May not cover all waypoints optimally

**Recommendation**: **Option B** (reuse network) - scenarios overlap significantly

### **Decision 2: Script Organization**
**Option A**: Individual scripts (like Vehicle 1-2)
- Easy to customize
- Fast to create
- More files

**Option B**: Unified script with scenario selector
- Single codebase
- Scenario dropdown
- More complex

**Recommendation**: **Option A** first (quick implementation), then **Option B** (refactor later)

### **Decision 3: Waypoint Count**
**Current**: First 2000 points per scenario
**Alternative**: 
- Use all points (large files)
- Use first 1000 (faster)
- Use first 500 (very fast, less coverage)

**Recommendation**: **Stick with 2000** - good balance

---

## 📊 What We'll Learn from Each Scenario

### **Comparison Metrics**:
1. **Distance accuracy** per vehicle pair
2. **Path loss accuracy** (FSPL vs 3GPP)
3. **SNR accuracy** comparison
4. **Communication range** differences
5. **Route complexity** (edge counts)
6. **Waypoint coverage** (% of GPS trajectory)

### **Hypotheses to Test**:
- Do different vehicle pairs have different accuracy?
- Does calibration factor vary by scenario?
- Are some scenarios harder to simulate (lower accuracy)?
- Which path loss model works better for which scenario?

---

## ⚠️ Potential Challenges

### **Challenge 1: Route Generation Failures**
- **Symptom**: Routes too short (<10 edges)
- **Solution**: 
  - Use denser sampling
  - Enable "Use All Waypoints"
  - Check waypoints are near roads

### **Challenge 2: Low Accuracy**
- **Symptom**: Distance accuracy < 50%
- **Solution**:
  - Try old calibration (0.607)
  - Check waypoint tracking
  - Verify routes follow GPS trajectory

### **Challenge 3: SUMO Network Coverage**
- **Symptom**: Waypoints outside network
- **Solution**:
  - Generate scenario-specific network
  - Adjust OSM Web Wizard area selection
  - Use larger coverage rectangle

### **Challenge 4: Waypoint Tracking Issues**
- **Symptom**: Waypoints jumping backwards
- **Solution**: Already fixed in Vehicle 1-2 (localized search)

---

## 📈 Success Criteria

### **For Each Scenario**:
- ✅ Waypoint visualization works
- ✅ Routes generated (30-50+ edges)
- ✅ Vehicles follow GPS trajectories
- ✅ Waypoints analyzed sequentially (no backward jumps)
- ✅ Analysis files saved correctly
- ✅ Accuracy metrics displayed in GUI

### **Overall Goals**:
- ✅ All 6 scenarios have working digital twins
- ✅ Consistent accuracy across scenarios (60-80%+)
- ✅ Comparison analysis possible
- ✅ Ready for unified script refactoring

---

## 🎯 Next Steps (Execution Order)

### **Immediate** (Today):
1. ✅ **Plan created** (this document)
2. ⏳ Generate SUMO networks for remaining scenarios (or decide to reuse)
3. ⏳ Extract first 2000 points for each scenario
4. ⏳ Create waypoint visualization scripts (5 scripts)

### **Short-term** (1-2 days):
5. ⏳ Create digital twin scripts (5 scripts)
6. ⏳ Test each scenario individually
7. ⏳ Compare accuracy across scenarios
8. ⏳ Document findings

### **Long-term** (Optional):
9. ⏳ Refactor into unified multi-scenario script
10. ⏳ Create batch processing script
11. ⏳ Generate combined analysis report

---

## 💡 Recommendations

### **Start with Vehicle 2-4**:
- Already has script, just needs updates
- Quick win to validate approach
- Can compare with Vehicle 1-2 results

### **Reuse SUMO Network**:
- All scenarios in same Berlin area
- Save time on network generation
- Focus on script creation instead

### **Template-Based Approach**:
- Use Vehicle 1-2 as template
- Create scripts via find/replace
- Faster than writing from scratch

### **Test Incrementally**:
- Create one scenario at a time
- Test before moving to next
- Catch issues early

---

## 📝 Notes

- **Time Estimate**: ~8-12 hours total for all 5 remaining scenarios
- **Complexity**: Medium (template-based, mostly copy-paste-modify)
- **Risk**: Low (similar to Vehicle 1-2 which is working)
- **Dependencies**: OSM Web Wizard, SUMO, Python scripts

---

**Ready to proceed?** Start with Vehicle 2-4 update, then create others in priority order.

