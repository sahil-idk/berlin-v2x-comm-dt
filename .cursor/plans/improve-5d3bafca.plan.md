<!-- 5d3bafca-9dc4-49f0-ad3c-18e740fb43ca 200f633b-453c-42d7-8383-3b4d68d28f9e -->
# Plan: Improve V2V Distance Accuracy and Verify Mapping

## Why accuracy is low (current state)

- **Constant ~35.5% accuracy implies a fixed scale mismatch**: SUMO XY distances (via `convertLonLat2XY`) are ~1.64× larger than Haversine GPS distances. This points to a projection/unit scaling difference rather than random noise.
- **We are not truly mapping to the network**: current script converts lat/lon to XY and computes Euclidean distance; it does not snap to lanes nor use vehicle positions from SUMO.

## Approach

1. **Use SIM-bound conversion**

- Switch to `traci.simulation.convertGeo(lon, lat)` after SUMO starts to guarantee alignment with the loaded network’s offset/projection.
- Add a one-time sanity check: compare Haversine vs converted-XY distance ratios over 100 pairs; if a constant factor exists, log it.

2. **Snap GPS to network lanes**

- For each GPS point, find nearest lane using `sumolib` (`net.getNeighboringEdges`) or `traci.simulation.convertRoad(x, y)`.
- Use the snapped lane centerline positions (x,y) for distance instead of raw converted XY.

3. **Optional: Spawn two vehicles per sample**

- Place two vehicles on the snapped lanes at the closest lane positions (`traci.vehicle.add`, `moveToXY`).
- Query `traci.vehicle.getPosition3D` to obtain ground-truth simulation positions and compute distance.

4. **Consistency checks**

- Verify lon/lat argument order across all conversions.
- Ensure headless config uses the same network as the web-wizard project (`sumo-config/osm.net.xml.gz`).

5. **Reporting improvements**

- Log: raw GPS Haversine, raw XY distance, snapped-lane XY distance, and (if vehicles spawned) vehicle-position distance.
- Emit per-sample and aggregate stats for each method to show improvement.

## Expected outcome

- Switching to `traci` conversion and lane snapping should bring average error down substantially (often <5–10 m for close pairs) and remove the constant scaling bias.

## Files to update

- `headless_v2v_distance_validation.py`: switch conversion, add snapping, optional vehicle placement, enhanced reporting.
- (No changes to SUMO config beyond existing `osm_headless.sumocfg`).

### To-dos

- [ ] Use traci.simulation.convertGeo for XY conversion and add scale sanity check
- [ ] Snap lat/lon to nearest lane and use snapped positions for distance
- [ ] Spawn two vehicles at snapped positions; compare traci-reported distance
- [ ] Report GPS vs raw-XY vs snapped-XY vs vehicle distances with stats