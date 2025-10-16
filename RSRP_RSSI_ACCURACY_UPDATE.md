# RSRP & RSSI Accuracy Implementation

## Overview
The V2V Communication Digital Twin now includes comprehensive RSRP and RSSI calculations and accuracy metrics based on simulated distances.

## What's New

### 1. **RSRP (Reference Signal Received Power) Calculation**
- **Formula**: `RSRP = Tx_Power - Path_Loss`
- **Based on**: Simulated and actual inter-vehicle distances
- **Accuracy Metric**: Comparison with dataset RSRP values

### 2. **RSSI (Received Signal Strength Indicator) Calculation**
- **Formula**: `RSSI = 10 * log10(10^(RSRP/10) + 10^(Noise/10))`
- **Based on**: Calculated RSRP + noise floor contribution
- **Accuracy Metric**: Comparison with dataset RSSI values

### 3. **Dataset Integration**
The script now correctly reads communication parameters from your dataset:
- **Column Names Used**:
  - `SNR` - Signal-to-Noise Ratio
  - `RSRP` - Reference Signal Received Power
  - `RSSI` - Received Signal Strength Indicator
  - `NOISE POWER` - Noise power measurements
  - `Rx_power` - Received power

## GUI Output Format

### Communication Parameters Display
```
📊 Dataset vs Calculated Communication Parameters:
   SNR:
      Dataset (mean): XX.XX dB
      Calculated (mean): XX.XX dB
      Difference: XX.XX dB
   
   RSRP:
      Dataset (mean): XX.XX dBm
      Simulated (mean): XX.XX dBm
      Accuracy: XX.XX%
      Error: XX.XX dBm
   
   RSSI:
      Dataset (mean): XX.XX dBm
      Simulated (mean): XX.XX dBm
      Accuracy: XX.XX%
      Error: XX.XX dBm
```

## CSV Output Columns

### New Columns Added:
1. **RSRP Metrics**:
   - `actual_rsrp_dbm` - RSRP calculated from actual distance
   - `simulated_rsrp_dbm` - RSRP calculated from simulated distance
   - `dataset_rsrp_dbm` - RSRP from original dataset
   - `rsrp_error_dbm` - Error between simulated and dataset RSRP
   - `rsrp_accuracy_pct` - RSRP accuracy percentage

2. **RSSI Metrics**:
   - `actual_rssi_dbm` - RSSI calculated from actual distance
   - `simulated_rssi_dbm` - RSSI calculated from simulated distance
   - `dataset_rssi_dbm` - RSSI from original dataset
   - `rssi_error_dbm` - Error between simulated and dataset RSSI
   - `rssi_accuracy_pct` - RSSI accuracy percentage

3. **Supporting Data**:
   - `dataset_noise_power` - Noise power from dataset
   - `dataset_rx_power_dbm` - Received power from dataset

## How It Works

### Step 1: Path Loss Calculation
Both actual and simulated distances are used to calculate path loss using the selected model (FSPL or 3GPP Urban Macro).

### Step 2: RSRP Calculation
```python
RSRP = Tx_Power - Path_Loss
```
- Tx_Power = 23 dBm (standard for V2V)
- Path_Loss = calculated from distance

### Step 3: RSSI Calculation
```python
RSSI = 10 * log10(10^(RSRP/10) + 10^(Noise/10))
```
- Combines signal power (RSRP) with noise floor
- Noise floor = -110 dBm (typical)

### Step 4: Accuracy Calculation
```python
RSRP_Accuracy = 100 - |((Simulated_RSRP - Dataset_RSRP) / Dataset_RSRP) * 100|
RSSI_Accuracy = 100 - |((Simulated_RSSI - Dataset_RSSI) / Dataset_RSSI) * 100|
```

## Expected Accuracy Levels

Based on your digital twin performance:
- **Distance Accuracy**: ~78% ✓
- **Path Loss Accuracy**: ~95% (mean) ✓
- **SNR Accuracy**: ~83% ✓
- **RSRP Accuracy**: Expected ~80-90% (new)
- **RSSI Accuracy**: Expected ~75-85% (new)

## Interpretation Guide

### RSRP Accuracy
- **>90%**: Excellent signal power estimation
- **80-90%**: Good estimation, suitable for digital twin
- **<80%**: May need calibration adjustments

### RSSI Accuracy
- **>85%**: Excellent total signal strength estimation
- **75-85%**: Good estimation for practical V2V simulation
- **<75%**: Consider noise floor calibration

### Error Metrics
- **RSRP Error**: Should be within ±5 dBm for good accuracy
- **RSSI Error**: Should be within ±3 dBm for reliable simulation

## Files Generated

1. **v2v_communication_analysis.csv** - Full detailed analysis with all RSRP/RSSI metrics
2. **v2v_communication_summary.json** - Summary statistics including RSRP/RSSI accuracy

## Usage

Simply run the communication digital twin as before:
```bash
python v2v_communication_digital_twin.py
```

The GUI will automatically:
1. Detect RSRP and RSSI columns in your dataset
2. Calculate simulated RSRP and RSSI from distances
3. Compare with dataset values
4. Display accuracy metrics in the console
5. Save detailed analysis to CSV

## Technical Notes

### Why RSRP Matters
- Key metric for handover decisions in LTE/5G V2V
- Determines link quality independent of bandwidth
- Critical for sidelink communication modeling

### Why RSSI Matters
- Represents total received signal strength
- Includes both signal and interference
- Used for channel assessment and power control

### Relationship Between Metrics
```
Path Loss → RSRP → RSSI → SNR → PRR
```
All metrics are interconnected through the propagation model, making distance accuracy the foundation of communication accuracy.

## Validation

The implementation has been validated to ensure:
1. ✓ Correct column names from dataset (`RSRP`, `RSSI`, not `actual_rsrp`/`actual_rssi`)
2. ✓ Proper RSRP calculation (Tx_Power - Path_Loss)
3. ✓ Proper RSSI calculation (signal + noise combination)
4. ✓ Accurate error and accuracy percentage calculations
5. ✓ Complete CSV output with all metrics

## Next Steps

After reviewing the RSRP and RSSI accuracy:
1. If accuracy >80%, your digital twin is excellent for communication modeling
2. If accuracy 70-80%, consider fine-tuning path loss model parameters
3. If accuracy <70%, may need to revisit noise floor assumptions or antenna gain settings

---

**Last Updated**: Based on correct dataset column names from `vehicle_2_4_first_200.csv`

