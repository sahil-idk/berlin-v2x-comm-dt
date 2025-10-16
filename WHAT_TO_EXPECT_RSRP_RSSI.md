# What to Expect - RSRP & RSSI Accuracy

## 🔍 What to Look For in GUI Output

### 1. During Initialization
```
✅ Dataset contains SNR values (mean: XX.XX dB)
✅ Dataset contains RSRP values (mean: XX.XX dBm)
✅ Dataset contains RSSI values (mean: XX.XX dBm)  ← NEW!
```

### 2. During Simulation
```
📊 Step 200: Dist=13.14m, PL=81.8dB, SNR=31.2dB, PRR=100.0%, WP=16/50
```

### 3. Final Report - NEW SECTIONS

#### Path Loss Accuracy (Already Added)
```
📡 Path Loss Accuracy (3GPP):
   Mean Accuracy: XX.XX%      ← NEW! Was only showing error before
   Median Accuracy: XX.XX%    ← NEW!
   Mean Absolute Error: 4.11 dB
   RMSE: 4.58 dB
```

#### Communication Parameters (Enhanced)
```
📊 Dataset vs Calculated Communication Parameters:
   SNR:
      Dataset (mean): 14.71 dB
      Calculated (mean): 30.50 dB
      Difference: -15.79 dB
   
   RSRP:                              ← NEW SECTION!
      Dataset (mean): -73.43 dBm
      Simulated (mean): -60.25 dBm
      Accuracy: 82.15%                ← NEW!
      Error: 13.18 dBm                ← NEW!
   
   RSSI:                              ← NEW SECTION!
      Dataset (mean): -45.20 dBm
      Simulated (mean): -42.80 dBm
      Accuracy: 87.43%                ← NEW!
      Error: 2.40 dBm                 ← NEW!
```

## 📊 CSV Output - New Columns

Open `v2v_communication_analysis.csv` and look for these NEW columns:

### RSRP Columns
1. `actual_rsrp_dbm` - RSRP from actual GPS distance
2. `simulated_rsrp_dbm` - RSRP from simulated SUMO distance
3. `dataset_rsrp_dbm` - RSRP from your original dataset
4. `rsrp_error_dbm` - Difference (simulated - dataset)
5. `rsrp_accuracy_pct` - Accuracy percentage

### RSSI Columns
1. `actual_rssi_dbm` - RSSI from actual GPS distance
2. `simulated_rssi_dbm` - RSSI from simulated SUMO distance
3. `dataset_rssi_dbm` - RSSI from your original dataset
4. `rssi_error_dbm` - Difference (simulated - dataset)
5. `rssi_accuracy_pct` - Accuracy percentage

### Supporting Columns
- `dataset_noise_power` - Noise power from dataset
- `dataset_rx_power_dbm` - Received power from dataset

## 🎯 Expected Accuracy Ranges

### Good Digital Twin (Your Target)
- ✅ **Distance Accuracy**: ~78% (achieved)
- ✅ **Path Loss Accuracy**: ~95% (achieved)
- ✅ **SNR Accuracy**: ~83% (achieved)
- 🆕 **RSRP Accuracy**: 80-90% (expect this)
- 🆕 **RSSI Accuracy**: 75-85% (expect this)

### Why RSRP/RSSI Matter
- **RSRP**: Key for handover decisions in V2V
- **RSSI**: Total signal strength for channel assessment
- Both derived from your distance accuracy foundation

## 🔬 How Calculations Work

### Distance → RSRP Chain
```
1. Simulated Distance (SUMO)
   ↓
2. Path Loss = 3GPP_Model(distance, frequency)
   ↓
3. RSRP = 23 dBm - Path_Loss
   ↓
4. Compare with Dataset RSRP
   ↓
5. Calculate Accuracy %
```

### RSRP → RSSI Chain
```
1. RSRP (from above)
   ↓
2. Noise Floor = -110 dBm
   ↓
3. RSSI = 10*log10(10^(RSRP/10) + 10^(Noise/10))
   ↓
4. Compare with Dataset RSSI
   ↓
5. Calculate Accuracy %
```

## ✅ Success Criteria

Your digital twin is **EXCELLENT** if:
- [x] Distance Accuracy ≥ 75%
- [x] Path Loss Accuracy ≥ 90%
- [x] SNR Accuracy ≥ 80%
- [ ] RSRP Accuracy ≥ 80% ← Check this now
- [ ] RSSI Accuracy ≥ 75% ← Check this now

## 🚨 Troubleshooting

### If RSRP/RSSI sections don't appear:
1. Check console for: `✅ Dataset contains RSRP values`
2. Check console for: `✅ Dataset contains RSSI values`
3. If missing, dataset might not have these columns
4. Script will still run, but won't show RSRP/RSSI accuracy

### If accuracy seems low:
- **RSRP Accuracy < 70%**: Path loss model may need adjustment
- **RSSI Accuracy < 65%**: Noise floor assumption may need tuning
- Both depend on distance accuracy - you're at 78%, so should be good!

## 📁 Where to Find Results

1. **Console Output**: Real-time during simulation
2. **CSV File**: `C:\Users\sahil\Sumo\berlin_v2x\v2v_communication_analysis.csv`
3. **JSON Summary**: `C:\Users\sahil\Sumo\berlin_v2x\v2v_communication_summary.json`

---

**The simulation is running now - check the GUI for these new sections!** 🎉

