# OSM Web Wizard Coordinates - Quick Reference

## 📍 Coordinates for Each Scenario

Copy-paste these coordinates into OSM Web Wizard's **Position** field:

| Scenario | Coordinates (lat lon) | Notes |
|----------|---------------------|-------|
| **Vehicle 1 ↔ 2** | `52.505376 13.325221` | 57,381 records |
| **Vehicle 1 ↔ 3** | `52.505698 13.326155` | 58,907 records |
| **Vehicle 1 ↔ 4** | `52.505468 13.325938` | 48,534 records |
| **Vehicle 2 ↔ 3** | `52.505082 13.324841` | 56,916 records |
| **Vehicle 2 ↔ 4** | `52.505589 13.326604` | 61,925 records |
| **Vehicle 3 ↔ 4** | `52.504503 13.324758` | 42,165 records |

## 🎯 Recommended Approach

### Option 1: Single Network (Simpler)
Since all scenarios are in the same Berlin area:
- Use coordinates: **`52.505589 13.326604`** (Vehicle 2-4 center - largest dataset)
- This covers all scenarios adequately
- Generate once, use for all 6 scenarios
- Save as: `berlin-sumo-all-scenarios/`

### Option 2: Separate Networks (More Accurate)
Generate individual networks for each scenario:
- Use scenario-specific coordinates from table above
- More precise coverage per vehicle pair
- Better for fine-tuned analysis
- Save as: `berlin-sumo-vehicle-X-Y/` for each

## 📋 OSM Web Wizard Settings

### Position Section
1. Enter coordinates (from table above)
2. Click **"Go to"** button

### Select Area Section
- ✅ **Check "Select Area" checkbox**
- Draw rectangle covering:
  - **Latitude**: 52.488 to 52.516
  - **Longitude**: 13.280 to 13.378

### Options Section
- **Duration**: `3600` (or higher for longer simulations)
- ✅ **Add Polygons** (checked)
- ⬜ Import Public Transport (optional)
- ⬜ Car-only Network (unchecked - use full network)
- ⬜ Satellite background (optional)
- ⬜ Left Hand Traffic (unchecked - Berlin is right-hand)

### Generate
- Click **"Generate Scenario"** button
- Wait for generation to complete
- Download/extract files

## 📂 Expected Output Structure

```
berlin-sumo-vehicle-X-Y/
├── osm.net.xml.gz          # Network file (required)
├── osm.poly.xml.gz         # Polygons/buildings
├── osm.sumocfg             # SUMO configuration
├── trips.trips.xml         # Trip definitions
└── ... (other files)
```

## 💡 Tips

1. **Coordinate Format**: Use space-separated: `lat lon` (e.g., `52.505589 13.326604`)
2. **Area Selection**: Draw rectangle that covers all waypoints for that scenario
3. **Network Reuse**: Since coordinates are very close, one network can serve all scenarios
4. **File Naming**: Use consistent naming: `berlin-sumo-vehicle-X-Y/`

## 🔄 Using Existing Network

If you already have `berlin-sumo-closed-netwokr/` network:
- ✅ You can reuse it for all scenarios
- ✅ All scenarios are in the same Berlin area
- ✅ Just update code to point to this directory
- ⚠️ For best accuracy, generate scenario-specific networks

