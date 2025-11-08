# SNR Accuracy Fix Guide for Berlin V2X Digital Twin

## Problem Summary
Current SNR accuracy: **34.93%** (POOR)
Path loss accuracy: **85.14%** (GOOD)
Mean SNR error: **14.4 dB** (too low)

## Root Causes

### 1. ❌ INCORRECT NOISE FLOOR (-14 dB error)
**File:** `v2v_communication_digital_twin_vehicle_1_2.py:42`

**Current (WRONG):**
```python
NOISE_FLOOR_DBM = -90
```

**Should be:**
```python
# Thermal noise calculation: -174 dBm/Hz + 10*log10(Bandwidth)
BANDWIDTH_HZ = BANDWIDTH_MHZ * 1e6  # 10 MHz = 10e6 Hz
THERMAL_NOISE_DENSITY_DBM = -174  # dBm/Hz
NOISE_FLOOR_DBM = THERMAL_NOISE_DENSITY_DBM + 10 * math.log10(BANDWIDTH_HZ)
# Result: -174 + 70 = -104 dBm
```

**Impact:** Using -90 instead of -104 causes **14 dB SNR underestimation**

### 2. ❌ INCORRECT TX POWER (-3 dB error)
**File:** `v2v_communication_digital_twin_vehicle_1_2.py:41`

**Current (WRONG):**
```python
TX_POWER_DBM = 20
```

**Should be:**
```python
TX_POWER_DBM = 23  # Standard V2V/PC5 Sidelink TX power
```

**Impact:** 3 dB less transmitted power = 3 dB lower SNR

### 3. ❌ MISSING RX ANTENNA GAIN (-3 dB error)
**File:** `v2v_communication_digital_twin_vehicle_1_2.py:90`

**Current (WRONG):**
```python
snr_db = tx_power_dbm + antenna_gain_db - path_loss - noise_floor_dbm
#                       ^^^^^^^^^^^^^^^ Only TX antenna (3 dB)
```

**Should be:**
```python
# Both vehicles have antennas
TX_ANTENNA_GAIN_DB = 3  # Transmitter antenna
RX_ANTENNA_GAIN_DB = 3  # Receiver antenna
TOTAL_ANTENNA_GAIN_DB = TX_ANTENNA_GAIN_DB + RX_ANTENNA_GAIN_DB  # = 6 dB

# Correct SNR calculation
received_power_dbm = tx_power_dbm + TOTAL_ANTENNA_GAIN_DB - path_loss
snr_db = received_power_dbm - noise_floor_dbm
```

**Impact:** Missing 3 dB from RX antenna

### 4. ⚠️ MISSING ENVIRONMENTAL EFFECTS (optional but recommended)
- No log-normal shadowing (standard deviation ~4-8 dB for urban)
- No small-scale fading (Rayleigh/Rician)
- No LOS/NLOS differentiation
- Dataset shows real-world variations that models don't capture

## Quick Fix Implementation

### Step 1: Update Communication Parameters

```python
# ============================================================================
# V2V Communication Parameters (CORRECTED)
# ============================================================================
CARRIER_FREQUENCY_GHZ = 5.9
TX_POWER_DBM = 23  # ✅ FIXED: Standard V2V TX power
BANDWIDTH_MHZ = 10
BANDWIDTH_HZ = BANDWIDTH_MHZ * 1e6

# Antenna gains
TX_ANTENNA_GAIN_DB = 3
RX_ANTENNA_GAIN_DB = 3
TOTAL_ANTENNA_GAIN_DB = TX_ANTENNA_GAIN_DB + RX_ANTENNA_GAIN_DB  # = 6 dB

# Noise floor calculation (CORRECTED)
THERMAL_NOISE_DENSITY_DBM_HZ = -174
NOISE_FLOOR_DBM = THERMAL_NOISE_DENSITY_DBM_HZ + 10 * math.log10(BANDWIDTH_HZ)
# Result: -174 + 70 = -104 dBm ✅
```

### Step 2: Update SNR Calculation Function

**OLD (WRONG):**
```python
def calculate_snr(distance_m, tx_power_dbm, noise_floor_dbm, model='FSPL',
                  frequency_ghz=5.9, antenna_gain_db=3):
    """Calculate Signal-to-Noise Ratio"""
    if model == 'FSPL':
        path_loss = calculate_fspl(distance_m, frequency_ghz)
    elif model == '3GPP':
        path_loss = calculate_3gpp_urban_macro_path_loss(distance_m, frequency_ghz)
    else:
        path_loss = calculate_fspl(distance_m, frequency_ghz)

    snr_db = tx_power_dbm + antenna_gain_db - path_loss - noise_floor_dbm  # ❌ WRONG
    return snr_db, path_loss
```

**NEW (CORRECT):**
```python
def calculate_snr(distance_m, tx_power_dbm, noise_floor_dbm, model='FSPL',
                  frequency_ghz=5.9, tx_antenna_gain_db=3, rx_antenna_gain_db=3):
    """Calculate Signal-to-Noise Ratio"""
    if model == 'FSPL':
        path_loss = calculate_fspl(distance_m, frequency_ghz)
    elif model == '3GPP':
        path_loss = calculate_3gpp_urban_macro_path_loss(distance_m, frequency_ghz)
    else:
        path_loss = calculate_fspl(distance_m, frequency_ghz)

    # Correct calculation: Received Power - Noise Power
    total_antenna_gain = tx_antenna_gain_db + rx_antenna_gain_db
    received_power_dbm = tx_power_dbm + total_antenna_gain - path_loss
    snr_db = received_power_dbm - noise_floor_dbm  # ✅ CORRECT

    return snr_db, path_loss
```

### Step 3: Update all calls to calculate_snr()

**OLD:**
```python
sim_snr, sim_path_loss = calculate_snr(simulated_distance, TX_POWER_DBM,
                                      NOISE_FLOOR_DBM, model,
                                      CARRIER_FREQUENCY_GHZ, ANTENNA_GAIN_DB)
```

**NEW:**
```python
sim_snr, sim_path_loss = calculate_snr(simulated_distance, TX_POWER_DBM,
                                      NOISE_FLOOR_DBM, model,
                                      CARRIER_FREQUENCY_GHZ,
                                      TX_ANTENNA_GAIN_DB, RX_ANTENNA_GAIN_DB)
```

## Expected Improvement

### Before Fixes:
- SNR Accuracy: **34.93%**
- Mean SNR Error: **-4.9 dB**
- Mean Absolute Error: **14.4 dB**

### After Fixes (Estimated):
With all 3 fixes combined:
- **Noise floor fix**: +14 dB to SNR
- **TX power fix**: +3 dB to SNR
- **RX antenna fix**: +3 dB to SNR
- **Total improvement**: +20 dB to SNR values

**Expected SNR Accuracy: >80%** (similar to path loss accuracy)

## Advanced Improvements (Optional)

### 1. Add Log-Normal Shadowing
```python
# Add to 3GPP model
SHADOWING_STD_DB = 4.0  # Urban environment

def add_shadowing(path_loss):
    """Add log-normal shadowing"""
    shadowing = np.random.normal(0, SHADOWING_STD_DB)
    return path_loss + shadowing
```

### 2. Use Dataset SNR/RSRP for Calibration
Your dataset contains real SNR and RSRP values. You could:
- Compare simulated vs. measured SNR
- Calculate calibration factor for your specific environment
- Apply environment-specific corrections

### 3. LOS/NLOS Modeling
```python
def is_los(distance_m):
    """Simplified LOS probability"""
    # Shorter distances more likely to be LOS
    los_probability = max(0.3, 1.0 - distance_m / 500.0)
    return random.random() < los_probability

# Different path loss for LOS vs NLOS
if is_los(distance):
    path_loss = calculate_3gpp_los(distance)
else:
    path_loss = calculate_3gpp_nlos(distance)
```

## Testing the Fixes

After implementing the fixes:

1. Run the simulation:
   ```bash
   python v2v_communication_digital_twin_vehicle_1_2.py
   ```

2. Check the new results in:
   - `vehicle_1_2_communication_summary.json`
   - Look for improved SNR accuracy (should be >80%)

3. Compare SNR values:
   ```python
   import pandas as pd

   # Load results
   df = pd.read_csv('vehicle_1_2_communication_analysis.csv')

   # Check SNR accuracy
   print(f"SNR Accuracy: {df['snr_accuracy_pct'].mean():.2f}%")
   print(f"SNR MAE: {df['snr_error_db'].abs().mean():.2f} dB")
   ```

## Summary of Changes

| Parameter | Old Value | New Value | Impact |
|-----------|-----------|-----------|--------|
| TX Power | 20 dBm | 23 dBm | +3 dB SNR |
| Noise Floor | -90 dBm | -104 dBm | +14 dB SNR |
| Antenna Gain | 3 dB (TX only) | 6 dB (TX+RX) | +3 dB SNR |
| **Total** | - | - | **+20 dB SNR** |

## Files to Modify

1. `v2v_communication_digital_twin_vehicle_1_2.py` - Main digital twin file
2. `v2v_communication_digital_twin.py` - If you have another scenario
3. `comm/models.py` - If you want to update the base models

## Questions?

If SNR accuracy is still low after these fixes:
1. Check if dataset SNR values are in dB (not linear)
2. Verify path loss model matches your urban environment
3. Consider adding shadowing/fading effects
4. Calibrate against real measurements from dataset
