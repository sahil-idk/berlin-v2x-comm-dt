# SUMO TraCI Simulation Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: GUI Opens but Stuck in Loading
**Symptoms**: SUMO GUI opens but shows constant loading or doesn't advance

**Causes & Solutions**:

1. **Network File Issues**
   - Problem: Invalid network structure
   - Solution: Use the minimal network created by `create_minimal_network.py`

2. **Configuration Issues**
   - Problem: Invalid SUMO configuration
   - Solution: Check `berlin_simulation.sumocfg` syntax

3. **Route File Issues**
   - Problem: Routes don't match network edges
   - Solution: Ensure routes reference existing edges

4. **TraCI Connection Issues**
   - Problem: TraCI can't connect to SUMO
   - Solution: Use `working_sumo_traci.py` instead of `simple_sumo_traci.py`

### Issue 2: Vehicle Not Moving
**Symptoms**: Vehicle appears but doesn't move

**Solutions**:
1. Check if PC2 data is loaded correctly
2. Verify vehicle speed is being set properly
3. Ensure vehicle is on a valid route

### Issue 3: SUMO Not Found
**Symptoms**: "SUMO not found" error

**Solutions**:
1. Install SUMO from https://sumo.dlr.de/docs/Downloads.php
2. Add SUMO to PATH environment variable
3. Verify installation: `sumo --version`

### Issue 4: TraCI Import Error
**Symptoms**: "No module named 'traci'"

**Solutions**:
1. TraCI comes with SUMO installation
2. Ensure SUMO is properly installed
3. Check Python can find SUMO libraries

## Step-by-Step Fix Process

### Step 1: Verify Installation
```bash
python simple_test.py
```

### Step 2: Create Minimal Network
```bash
python create_minimal_network.py
```

### Step 3: Run Working Simulation
```bash
python working_sumo_traci.py
```

## File Structure Check

Ensure these files exist:
- ✅ `berlin_network.net.xml` - SUMO network
- ✅ `berlin_simulation.sumocfg` - Simulation configuration
- ✅ `berlin_routes.rou.xml` - Vehicle routes
- ✅ `berlin_additional.add.xml` - Additional elements
- ✅ `pc2_parsed.csv` - GPS trajectory data

## Working Configuration

The minimal network uses:
- Simple linear road (2 edges, 3 junctions)
- Basic vehicle routes
- Compatible with PC2 data

## Performance Tips

1. **Reduce Data Sampling**: Use every 50th data point
2. **Limit Simulation Steps**: Run for 500 steps max
3. **Add Delays**: Use `time.sleep(0.1)` for visualization
4. **Close Properly**: Always call `traci.close()`

## Debug Mode

To debug issues:
1. Run `python simple_test.py` first
2. Check console output for errors
3. Use `--verbose` flag in SUMO
4. Check TraCI connection status

## Alternative Approaches

If TraCI doesn't work:
1. Use SUMO without TraCI (static simulation)
2. Use different network (download real Berlin OSM)
3. Use different vehicle control method

## Success Indicators

✅ SUMO GUI opens
✅ Vehicle appears on road
✅ Vehicle moves with changing speed
✅ Console shows progress updates
✅ Simulation completes without errors

## Common Error Messages

- **"No option with the name 'check' exists"**: Use newer SUMO version
- **"Could not parse commandline options"**: Check configuration syntax
- **"Error connecting to SUMO"**: SUMO not running or configuration invalid
- **"Failed to add vehicle"**: Route or network issues

## Final Checklist

Before running simulation:
- [ ] SUMO installed and in PATH
- [ ] All required files present
- [ ] Network file is valid
- [ ] PC2 data file exists
- [ ] Python packages installed
- [ ] No other SUMO instances running

## Quick Fix Commands

```bash
# Test everything
python simple_test.py

# Create minimal network
python create_minimal_network.py

# Run working simulation
python working_sumo_traci.py
```

If issues persist, check SUMO documentation or try a different approach.
