# Berlin V2X Dataset Parameter Verification

## 🚨 CRITICAL FINDINGS - PARAMETERS NEED UPDATE!

### ❌ Our Assumptions vs. Actual Dataset Parameters

| Parameter | Our Assumption | Actual (from Paper) | Status |
|-----------|---------------|---------------------|--------|
| **Sidelink Frequency** | 5.9 GHz ✅ | 5.9 GHz | ✅ CORRECT |
| **Cellular Frequency** | 5.9 GHz ❌ | 700 MHz - 2.7 GHz | ❌ WRONG! |
| **Sidelink Scenarios** | Not defined | S1: CAM, S2: CPM | ❌ MISSING |
| **Packet Rates** | Not defined | S1: 20 Hz, S2: 50 Hz | ❌ MISSING |
| **MCS** | Not defined | S1: MCS 8, S2: MCS 12 | ❌ MISSING |

---

## 📊 Actual Dataset Parameters (from Berlin V2X Paper)

### Cellular (LTE) Communication

**Network Configuration:**
- **Operators:** 2 different MNOs (Vodafone, Deutsche Telekom)
  - Operator 1: Vodafone
  - Operator 2: Deutsche Telekom
- **Frequency Bands:** **700 MHz to 2.7 GHz** (NOT 5.9 GHz!)
- **Technology:** LTE (4G)

**Traffic Profiles:**
1. **Low Datarate:** 400 kbit/s (both UL and DL) - for delay measurements
2. **High Datarate:** 75 Mbit/s UL, 350 Mbit/s DL - for max throughput

**Measured Parameters:**
- PHY: SNR, RSRP, RSRQ, RSSI (10-20 ms intervals)
- Throughput: UL/DL datarate (1 s intervals)
- Latency: Ping delay (1 s intervals)

---

### Sidelink (V2V) Communication

**Network Configuration:**
- **Frequency:** **5.9 GHz** ✅ (This is correct!)
- **Technology:** 3GPP Release 14 Sidelink
- **HARQ:** Blind HARQ

**Operation Scenarios:**

**S1: Cooperative Awareness Messages (CAM)**
- Packet Size: 69 bytes
- Transmission Rate: **20 Hz**
- MCS: **8**
- Sub-channels: **2**
- Use Case: Basic awareness (position, speed)

**S2: Collective Perception Messages (CPM)**
- Packet Size: **1000 bytes** (including IP header)
- Transmission Rate: **50 Hz**
- MCS: **12**
- Sub-channels: **10**
- Use Case: Environmental perception (sensors, objects)

**Measured Parameters:**
- PHY: SNR, RSRP, RSRQ, RSSI, noise power, RX power, RX gain (event-based)
- Link Quality: Packet Error Rate (PER)
- Distance: From GPS (1 s intervals)

---

## 🔍 Key Insights from the Paper

### Link Range Analysis (Figure 5, Figure 6)

**S1 (CAM):**
- Practical Link Range: **~80 meters**
- Good SNR range: 5-25 dB
- PER behavior: Increases with distance

**S2 (CPM):**
- Practical Link Range: **~30 meters** (much shorter due to higher data rate)
- Good SNR range: Similar to S1
- PER behavior: More sensitive to distance

**Distance vs PER Relationship:**
- Strong correlation between distance and PER
- Mediated by SNR
- Different behavior for different scenarios (S1 vs S2)

---

## ⚠️ What We Got WRONG in Our Code

### 1. Cellular Frequency ❌
**Our Code:**
```python
CARRIER_FREQUENCY_GHZ = 5.9  # WRONG!
```

**Should Be:**
```python
# Cellular uses 700 MHz - 2.7 GHz (LTE bands)
# Common LTE bands in Germany:
LTE_BAND_20 = 0.8    # 800 MHz (most common)
LTE_BAND_3 = 1.8     # 1800 MHz
LTE_BAND_7 = 2.6     # 2600 MHz
```

### 2. Missing Sidelink Parameters ❌
**Our Code:**
- No differentiation between CAM and CPM scenarios
- No packet rate consideration
- No MCS parameters

**Should Have:**
```python
# Sidelink Scenario S1 (CAM)
SIDELINK_S1_FREQ_GHZ = 5.9
SIDELINK_S1_PACKET_SIZE = 69  # bytes
SIDELINK_S1_RATE_HZ = 20
SIDELINK_S1_MCS = 8
SIDELINK_S1_SUBCHANNELS = 2

# Sidelink Scenario S2 (CPM)
SIDELINK_S2_FREQ_GHZ = 5.9
SIDELINK_S2_PACKET_SIZE = 1000  # bytes
SIDELINK_S2_RATE_HZ = 50
SIDELINK_S2_MCS = 12
SIDELINK_S2_SUBCHANNELS = 10
```

### 3. Path Loss Model Application ❌
**Our Code:**
- Applied FSPL and 3GPP models to cellular at 5.9 GHz

**Reality:**
- **Cellular:** Should use LTE frequencies (0.7-2.7 GHz)
- **Sidelink:** Can use 5.9 GHz models ✅

---

## 📊 Dataset Column Mapping

### What's Available in `sidelink_parsed.csv`

Based on the paper, the sidelink data should contain:

| Column (Likely) | Description | Unit | Sampling |
|-----------------|-------------|------|----------|
| `timestamp` | Time | ms | Event-based |
| `Latitude_source` | Source GPS lat | degrees | 1 s |
| `Longitude_source` | Source GPS lon | degrees | 1 s |
| `Latitude_destination` | Dest GPS lat | degrees | 1 s |
| `Longitude_destination` | Dest GPS lon | degrees | 1 s |
| `distance` | Inter-vehicle distance | meters | Calculated |
| `SNR` | Signal-to-Noise Ratio | dB | Event-based |
| `RSRP` | Reference Signal Received Power | dBm | Event-based |
| `RSRQ` | Reference Signal Received Quality | dB | Event-based |
| `RSSI` | Received Signal Strength Indicator | dBm | Event-based |
| `noise_power` | Noise power | dBm | Event-based |
| `rx_power` | Received power | dBm | Event-based |
| `rx_gain` | Receiver gain | dB | Event-based |

### What We're Using

✅ **Correctly Used:**
- `distance` - Inter-vehicle distance
- `Latitude/Longitude` - GPS positions
- `speed_kmh` - Vehicle speed
- `SNR` - Signal quality (if available)
- `RSRP` - Signal strength (if available)

---

## 🔧 Required Code Updates

### 1. Update Frequency Parameters

**File:** `v2v_communication_digital_twin.py`

**Current (Line 23-25):**
```python
CARRIER_FREQUENCY_GHZ = 5.9  # ❌ WRONG for cellular!
CARRIER_FREQUENCY_MHZ = 5900
```

**Should Be:**
```python
# Cellular (LTE) - Use typical German LTE band
CELLULAR_FREQUENCY_GHZ = 0.8  # 800 MHz (Band 20)
CELLULAR_FREQUENCY_MHZ = 800

# Sidelink (V2V) - This is correct!
SIDELINK_FREQUENCY_GHZ = 5.9
SIDELINK_FREQUENCY_MHZ = 5900
```

### 2. Add Sidelink Scenario Parameters

```python
# Sidelink Scenarios (from paper)
SIDELINK_SCENARIOS = {
    'S1_CAM': {
        'name': 'Cooperative Awareness Messages',
        'packet_size_bytes': 69,
        'rate_hz': 20,
        'mcs': 8,
        'subchannels': 2,
        'typical_range_m': 80
    },
    'S2_CPM': {
        'name': 'Collective Perception Messages',
        'packet_size_bytes': 1000,
        'rate_hz': 50,
        'mcs': 12,
        'subchannels': 10,
        'typical_range_m': 30
    }
}
```

### 3. Update Path Loss Models

**For Cellular (LTE):**
```python
def calculate_lte_path_loss(distance_m, frequency_ghz=0.8):
    """
    Urban Macro path loss for LTE (800 MHz)
    3GPP 38.901 model adapted for sub-1GHz
    """
    if distance_m <= 0:
        return 0
    
    # Urban macro model for 0.7-2.7 GHz
    pl = 28.0 + 22 * math.log10(distance_m) + 20 * math.log10(frequency_ghz)
    return pl
```

**For Sidelink (5.9 GHz):**
```python
def calculate_sidelink_path_loss(distance_m, frequency_ghz=5.9):
    """
    FSPL for sidelink V2V at 5.9 GHz
    Suitable for line-of-sight V2V communication
    """
    if distance_m <= 0:
        return 0
    
    frequency_mhz = frequency_ghz * 1000
    fspl_db = 20 * math.log10(distance_m) + 20 * math.log10(frequency_mhz) + 32.45
    return fspl_db
```

### 4. Update GUI to Reflect Dataset

**Add selection for communication type:**
```python
# Communication Type Selection
comm_type_frame = ttk.LabelFrame(self.root, text="Communication Type", padding=10)
comm_type_frame.pack(fill="x", padx=10, pady=5)

self.comm_type = tk.StringVar(value='SIDELINK')
ttk.Radiobutton(comm_type_frame, text="Sidelink V2V (5.9 GHz)", 
               variable=self.comm_type, value='SIDELINK').pack(anchor='w')
ttk.Radiobutton(comm_type_frame, text="Cellular LTE (800 MHz)", 
               variable=self.comm_type, value='CELLULAR').pack(anchor='w')
```

---

## 📈 Impact on Results

### Current Results (with 5.9 GHz for both):
- Path Loss: Calculated for 5.9 GHz
- SNR: Based on 5.9 GHz path loss
- **Problem:** Cellular data uses 0.7-2.7 GHz, not 5.9 GHz!

### Corrected Results (with proper frequencies):

**For Cellular (800 MHz):**
- Path Loss will be **LOWER** (lower frequency = less attenuation)
- SNR will be **HIGHER**
- Range will be **LONGER**

**Example at 100m:**
```
Current (wrong):
  PL @ 5.9 GHz = 20*log10(100) + 20*log10(5900) + 32.45 = 115.87 dB

Correct:
  PL @ 0.8 GHz = 28.0 + 22*log10(100) + 20*log10(0.8) = 89.94 dB
  
Difference: ~26 dB! (HUGE!)
```

**For Sidelink (5.9 GHz):**
- ✅ Already correct
- Path loss calculations are valid
- SNR and range estimates are accurate

---

## ✅ Action Items

### Immediate (Critical):

1. **Update `v2v_communication_digital_twin.py`:**
   - [ ] Change cellular frequency from 5.9 GHz to 0.8 GHz (or make selectable)
   - [ ] Add separate path loss model for LTE
   - [ ] Add sidelink scenario parameters (S1, S2)
   - [ ] Update GUI to show correct frequencies

2. **Update Documentation:**
   - [ ] Correct `V2V_COMMUNICATION_GUIDE.md` frequency specs
   - [ ] Add Berlin V2X dataset reference
   - [ ] Document sidelink scenarios (S1: CAM, S2: CPM)

3. **Verify Dataset:**
   - [ ] Check if `sidelink_parsed.csv` contains SNR/RSRP
   - [ ] Confirm which scenario (S1 or S2) the data uses
   - [ ] Validate distance range (should be <80m for S1, <30m for S2)

### Future Enhancements:

4. **Add Multi-RAT Support:**
   - [ ] Toggle between cellular and sidelink analysis
   - [ ] Different path loss models for each RAT
   - [ ] Comparative analysis between RATs

5. **Scenario-Specific Analysis:**
   - [ ] CAM scenario (S1) - 20 Hz, 69 bytes, ~80m range
   - [ ] CPM scenario (S2) - 50 Hz, 1000 bytes, ~30m range
   - [ ] Packet rate impact on accuracy

---

## 📚 Key References from Paper

### Measurement Setup (Section II):
- **Route:** 17.2 km in West Berlin
- **Duration:** ~45 min per round
- **Vehicles:** Up to 4 vehicles
- **Modes:** Platoon (11 rounds), 2x2 (6 rounds)

### Cellular Configuration:
- **DME:** Dedicated Measurement Equipment
- **Datarates:** 400 kbit/s (low), 75 Mbit/s UL / 350 Mbit/s DL (high)
- **Frequency:** **700 MHz - 2.7 GHz** (LTE bands)

### Sidelink Configuration:
- **Platform:** SDR-based (3GPP Release 14)
- **Frequency:** **5.9 GHz** (ITS-G5 band)
- **HARQ:** Blind hybrid ARQ
- **Scenarios:** S1 (CAM), S2 (CPM) as detailed above

### Key Findings (Section III):
- SNR strongly correlates with DL datarate
- RSRP/RSSI correlate with UL datarate
- Cross-operator correlation is modest
- Sidelink range: 80m (S1), 30m (S2)

---

## 🎯 Conclusion

**MAJOR FINDING:** Our cellular communication model is using **5.9 GHz** when the actual dataset uses **0.7-2.7 GHz (LTE)**!

**Impact:**
- ❌ Path loss calculations for cellular are WRONG (off by ~26 dB!)
- ✅ Sidelink calculations at 5.9 GHz are CORRECT
- ❌ SNR estimates for cellular are WRONG
- ❌ Range predictions for cellular are WRONG

**Required Action:**
1. Update frequency parameters immediately
2. Separate cellular and sidelink models
3. Re-run simulations with correct parameters
4. Update all documentation

**The sidelink (V2V) part of our simulation is correct, but the cellular part needs major corrections!**

