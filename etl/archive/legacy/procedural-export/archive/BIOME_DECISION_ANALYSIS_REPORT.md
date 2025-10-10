# Biome Classification Decision Logic Analysis

**World:** hkLycKKCMI (G0Ws7CmRyU)
**Samples:** 1,048,576 (1024×1024)
**Analysis Date:** 2025-10-09

---

## Executive Summary

This analysis examines the complete biome classification pipeline from Valheim's `WorldGenerator.GetBiome()` through post-processing filters, identifying decision-making logic, weights, and transformations.

### Key Findings

1. **Polar Biome Over-representation:** DeepNorth (31%) and Ashlands (16%) dominate the raw API data due to being checked BEFORE Mistlands
2. **Mistlands Starvation:** Only 5.5% in raw data vs expected 30%+ in outer ring - gets "starved" by polar biomes
3. **Post-Processing Impact:** Filters successfully recover Mistlands to 19% by reclassifying ~506k samples (48.3%)
4. **Directional Bias:** DeepNorth shows 66.5% in north vs 33.4% in south - indicating Y-offset logic works partially

---

## Part 1: Decision Tree Logic

### Biome Priority Order (WorldGenerator.GetBiome, lines 752-810)

The following shows the **exact order** biomes are checked - this order is critical because once a biome matches, the function returns immediately:

| Priority | Biome | Check Logic | Critical Notes |
|----------|-------|-------------|----------------|
| **1** | **Ashlands** | `IsAshlands(x, z)`: Distance from (x, z-4000) > ~9,626m + angle modulation | ⚠️ **Checked FIRST** - steals outer ring from Mistlands |
| 2 | Ocean (baseHeight) | `baseHeight <= 0.05` | Height-based, checked before DeepNorth |
| **3** | **DeepNorth** | `IsDeepnorth(x, z)`: Distance from (x, z+4000) > ~7,140m + angle modulation | ⚠️ **Checked BEFORE Mistlands** - also steals territory |
| 4 | Mountain | `baseHeight > 0.4` | Can appear anywhere if elevation high enough |
| 5 | Swamp | `PerlinNoise(offset0+x/z) > 0.6 && dist 2-6km && height 0.05-0.25` | Requires noise + distance + height band |
| **6** | **Mistlands** | `PerlinNoise(offset4+x/z) > 0.4 && dist 6-10km` | ⚠️ **Checked AFTER polar** - victims of priority bug |
| 7 | Plains | `PerlinNoise(offset1+x/z) > 0.4 && dist 3-8km` | Mid-range biome with noise requirement |
| 8 | BlackForest | `PerlinNoise(offset2+x/z) > 0.4 && dist 0.6-6km OR dist > 5km` | Has fallback: returns if distance > 5km |
| 9 | Meadows | Default fallback | Returns if nothing else matched |

### The Priority Bug

**Problem:** Polar biomes (Ashlands, DeepNorth) are checked at priorities 1 and 3, while Mistlands is checked at priority 6.

**Impact:**
- In the outer ring (6-10km), many points satisfy the polar distance checks
- Once polar biome returns, Mistlands check never executes
- Result: Polar biomes "steal" ~60% of outer ring where Mistlands should dominate

**Evidence from spatial distribution:**
```
Outer Ring (6-8km): 230,592 samples
├─ Ashlands:   101,206 (43.9%)  ← Should be Mistlands
├─ DeepNorth:   66,708 (28.9%)  ← Should be Mistlands
├─ Mistlands:       40 ( 0.0%)  ← STARVED!
└─ Mountain:    50,739 (22.0%)
```

---

## Part 2: Raw Distribution Analysis

### Overall World Distribution (API Data)

| Biome | Count | Percentage | Expected | Variance |
|-------|-------|------------|----------|----------|
| **DeepNorth** | 325,837 | **31.07%** | ~12-15% | ⚠️ **+16% over** |
| Ocean | 188,798 | 18.01% | ~18% | ✅ Correct |
| **Ashlands** | 163,766 | **15.62%** | ~5-8% | ⚠️ **+8% over** |
| Mountain | 151,298 | 14.43% | ~12-15% | ✅ Correct |
| Plains | 77,111 | 7.35% | ~8-10% | ✅ Acceptable |
| **Mistlands** | 57,684 | **5.50%** | ~25-30% | ⚠️ **-22% under** |
| Swamp | 31,133 | 2.97% | ~3-5% | ✅ Correct |
| Meadows | 28,086 | 2.68% | ~5-8% | ⚠️ Slightly under |
| BlackForest | 24,863 | 2.37% | ~5-8% | ⚠️ Slightly under |

### Spatial Distribution by Distance Rings

#### Center Ring (0-2km): Spawn Zone
```
Mountain:   14,146 (42.9%) ████████████████████
Meadows:    10,298 (31.3%) ███████████████
DeepNorth:   7,118 (21.6%) ██████████
Swamp:       1,375 ( 4.2%) ██
```
**Analysis:** Mountain dominance unexpected in center - likely due to high baseHeight noise

#### Inner Ring (2-4km): Starter Biomes
```
DeepNorth:  26,290 (26.6%) ████████████
Mountain:   26,042 (26.4%) ████████████
Plains:     21,658 (21.9%) ██████████
Meadows:    12,590 (12.7%) ██████
```
**Analysis:** Balanced distribution, DeepNorth still present (should be minimal)

#### Mid Ring (4-6km): Progression Biomes
```
Plains:     53,656 (32.6%) ████████████████
DeepNorth:  51,070 (31.0%) ███████████████
Mountain:   27,726 (16.8%) ████████
BlackForest:16,875 (10.2%) █████
```
**Analysis:** Plains and DeepNorth dominate as expected

#### Outer Ring (6-8km): **THE PROBLEM ZONE**
```
Ashlands:  101,206 (43.9%) █████████████████████ ← STEALING
DeepNorth:  66,708 (28.9%) ██████████████        ← STEALING
Mountain:   50,739 (22.0%) ██████████
Mistlands:      40 ( 0.0%) ·                     ← STARVED!
```
**Analysis:** **CRITICAL ISSUE** - Mistlands reduced to 0.0% due to polar priority

#### Far Ring (8-10km): Mistlands Territory
```
Ocean:      77,980 (26.3%) ████████████
DeepNorth:  69,528 (23.5%) ███████████  ← Still stealing
Ashlands:   61,446 (20.7%) ██████████   ← Still stealing
Mistlands:  51,228 (17.3%) ████████     ← Finally appears
```
**Analysis:** Mistlands finally breaks through at far distances, but still underrepresented

#### Edge Ring (10-12km): Ocean Boundary
```
Ocean:      84,685 (48.8%) ████████████████████████
DeepNorth:  79,549 (45.8%) ██████████████████████
Mistlands:   6,416 ( 3.7%) █
```
**Analysis:** Ocean forcing takes over, DeepNorth persists beyond boundary

---

## Part 3: Directional Distribution (Polar Biome Analysis)

### DeepNorth Y-Offset Analysis

| Direction | DeepNorth Count | % of Direction | % of All DeepNorth |
|-----------|-----------------|----------------|---------------------|
| **North (Z > 0)** | 216,582 | 41.4% | **66.5%** ✅ |
| **South (Z < 0)** | 108,902 | 20.8% | **33.4%** |
| East (X > 0) | 156,557 | 29.9% | 48.0% |
| West (X < 0) | 169,076 | 32.2% | 51.9% |

**Finding:** ✅ **Y-offset (+4000m north) IS working** - 66.5% of DeepNorth in northern hemisphere

### Ashlands Y-Offset Analysis

| Direction | Ashlands Count | % of Direction | % of All Ashlands |
|-----------|----------------|----------------|---------------------|
| North (Z > 0) | 84,212 | 16.1% | 51.4% |
| **South (Z < 0)** | 79,443 | 15.2% | **48.5%** ⚠️ |
| East (X > 0) | 85,313 | 16.3% | 52.1% |
| West (X < 0) | 78,365 | 14.9% | 47.9% |

**Finding:** ⚠️ **Y-offset (-4000m south) NOT working well** - Only 48.5% in southern hemisphere (expected >80%)

**Hypothesis:** Ashlands threshold (~9,626m) is too close to world boundary (10,000m), reducing effectiveness of directional offset.

---

## Part 4: Noise Thresholds and Weights

### Extracted Noise Parameters (from decompiled code)

| Biome | Noise Offset | Threshold | Scale | Distance Ring | Height Requirement |
|-------|--------------|-----------|-------|---------------|-------------------|
| Swamp | m_offset0 | **0.6** ⚠️ | 0.001 | 2-6km | 0.05-0.25 (narrow band) |
| Plains | m_offset1 | 0.4 | 0.001 | 3-8km | None |
| BlackForest | m_offset2 | 0.4 | 0.001 | 0.6-6km OR >5km | None |
| Mistlands | m_offset4 | 0.4 | 0.001 | 6-10km | None |

### Threshold Comparison

| Threshold | Biomes | Pass Rate | Impact |
|-----------|--------|-----------|--------|
| **0.6** | Swamp | ~25% | ⚠️ **Very restrictive** - Swamp is rare (2.97%) |
| **0.4** | Mistlands, Plains, BlackForest | ~40% | Standard threshold |

**Finding:** Swamp's 0.6 threshold makes it ~60% rarer than other noise-based biomes

### Seed-Specific Offsets (hkLycKKCMI)

From metadata extraction:
```json
{
  "Offset0": -4682.0,  // Base height X + Swamp noise
  "Offset1":  3703.0,  // Base height Y + Plains noise
  "Offset2":  9482.0,  // BlackForest noise
  "Offset3": -7075.0,  // Unused?
  "Offset4":  3697.0   // Mistlands noise
}
```

**Note:** These offsets are **seed-specific random values** - they shift the Perlin noise sampling coordinates, ensuring each world is unique while using the same noise function.

---

## Part 5: Post-Processing Filter Analysis

### Filter Pipeline (client/renderer.js)

#### Filter #1: Ocean Land Contamination Fix (lines 265-267)
```javascript
if (biomeId === 32 && height >= SEA_LEVEL) {
    biomeId = 64;  // Ocean → Mistlands
}
```
**Impact:** 20,249 samples (10.7% of Ocean) reclassified
**Reason:** Distant lands (>7,900m) misclassified as Ocean based on distance alone

#### Filter #2: Edge Biome Water Distinction (lines 271-273)
```javascript
if ((biomeId === 256 || biomeId === 512) && height < (SEA_LEVEL - 10)) {
    biomeId = 32;  // DeepNorth/Ashlands → Ocean
}
```
**Impact:** 325,837 DeepNorth + 39,124 Ashlands = 364,961 samples → Ocean
**Reason:** Deep water in polar regions should render as Ocean, not polar land biomes

**⚠️ CRITICAL FINDING:** This filter converts **100% of DeepNorth** to Ocean because nearly all DeepNorth samples are underwater! This is likely too aggressive.

#### Filter #3: Mistlands Recovery (lines 280-313)
```javascript
const OUTER_RING = (6000 <= dist <= 10000);
const POLAR_THRESHOLD = 7000;  // Latitude cutoff

// Ashlands: Keep only if Z < -7000 (far south)
if (biomeId === 512 && Z >= -POLAR_THRESHOLD) {
    biomeId = 64;  // → Mistlands
}

// DeepNorth: Keep only if Z > 7000 (far north)
if (biomeId === 256 && Z <= POLAR_THRESHOLD) {
    biomeId = 64;  // → Mistlands
}
```
**Impact:** 121,249 Ashlands (74.0%) → Mistlands
**Reason:** Recover Mistlands territory stolen by polar priority bug

### Combined Filter Impact

| Transformation | Count | % of Source | Purpose |
|----------------|-------|-------------|---------|
| DeepNorth → Ocean | 325,837 | 100.0% | ⚠️ All underwater |
| Ashlands → Ocean | 39,124 | 23.9% | Deep water distinction |
| Ashlands → Mistlands | 121,249 | 74.0% | Mistlands recovery |
| Ocean → Mistlands | 20,249 | 10.7% | Land contamination fix |
| **TOTAL** | **506,459** | **48.3%** | Nearly half of samples transformed! |

### Transformed Distribution

| Biome | Raw % | Transformed % | Change | Interpretation |
|-------|-------|---------------|--------|----------------|
| Ocean | 18.01% | **50.88%** | **+32.87%** | ⚠️ Includes all DeepNorth |
| Mistlands | 5.50% | **19.00%** | **+13.49%** | ✅ Recovered! |
| DeepNorth | 31.07% | **0.00%** | **-31.07%** | ⚠️ Completely eliminated |
| Ashlands | 15.62% | **0.32%** | **-15.29%** | ✅ Reduced to far south crescent |
| Mountain | 14.43% | 14.43% | 0.00% | ✅ Unchanged |
| Plains | 7.35% | 7.35% | 0.00% | ✅ Unchanged |

---

## Part 6: Problems and Recommendations

### Problem #1: Polar Biome Priority Bug 🔴 **CRITICAL**

**Issue:** Ashlands/DeepNorth checked before Mistlands → steals 60% of outer ring

**Current Solution:** Post-processing filter converts outer ring polar → Mistlands

**Better Solution:** Reorder C# checks in VWE_ProceduralMetadata plugin:
```csharp
// BEFORE (current Valheim code):
if (IsAshlands(x, z)) return Ashlands;   // Line 769
if (IsDeepNorth(x, z)) return DeepNorth; // Line 777
if (MistlandsCheck()) return Mistlands;  // Line 793

// AFTER (proposed fix):
if (MistlandsCheck()) return Mistlands;  // Check FIRST
if (IsAshlands(x, z)) return Ashlands;   // Then polar
if (IsDeepNorth(x, z)) return DeepNorth;
```

**Impact:** Would eliminate need for ~270k post-processing transformations

---

### Problem #2: DeepNorth 100% Elimination 🔴 **CRITICAL**

**Issue:** Filter #2 converts ALL DeepNorth to Ocean because they're mostly underwater

**Data:**
```
DeepNorth height distribution:
- Underwater (< 20m): 325,837 (100.0%)
- Above water (≥ 20m): 0 (0.0%)
```

**Current Logic:**
```javascript
if (biomeId === 256 && height < 20) {
    biomeId = 32;  // ALL DeepNorth → Ocean
}
```

**Recommendation:** Adjust Filter #2 to preserve DeepNorth in far north:
```javascript
// Only convert to Ocean if ALSO not in far north
if (biomeId === 256 && height < 20 && worldZ <= 8000) {
    biomeId = 32;  // DeepNorth → Ocean (except far north)
}
// Alternatively: Skip Filter #2 for polar biomes, rely only on Filter #3
```

**Impact:** Would preserve ~80k DeepNorth samples in far north region

---

### Problem #3: Swamp Noise Threshold Too High 🟡 **MODERATE**

**Issue:** Swamp uses 0.6 threshold vs 0.4 for other biomes → 60% rarer

**Evidence:**
- Swamp: 2.97% of world
- Plains: 7.35% (similar distance ring, 0.4 threshold)
- Expected: 4-5% based on distance ring size

**Recommendation:** Consider lowering Swamp threshold to 0.5:
```csharp
// Current:
if (PerlinNoise(...) > 0.6 && ...) return Swamp;

// Proposed:
if (PerlinNoise(...) > 0.5 && ...) return Swamp;
```

**Impact:** Would increase Swamp coverage by ~50% (2.97% → 4.5%)

---

### Problem #4: Ashlands Y-Offset Ineffective 🟡 **MODERATE**

**Issue:** Only 48.5% of Ashlands in southern hemisphere (expected >80%)

**Root Cause:** Threshold (~9,626m) too close to world boundary (10,000m)

**Recommendation:** Reduce Ashlands threshold OR increase Y-offset:
```csharp
// Option A: Lower threshold (easier)
ashlandsMinDistance = 8500;  // from 12000 (or ~9626 actual)

// Option B: Increase Y-offset (more directional)
ashlandsYOffset = -6000;  // from -4000
```

**Impact:** Would create clearer southern crescent concentration

---

### Problem #5: Mistlands Weight Balance 🟢 **MINOR**

**Issue:** Even after recovery filter, Mistlands at 19% vs expected 25-30%

**Root Cause:** Combination of:
1. Polar priority bug (partially fixed by filter)
2. Noise threshold 0.4 might be too high
3. Distance ring 6-10km overlaps heavily with polar rings

**Recommendation:** Adjust Mistlands parameters:
```csharp
// Option A: Lower noise threshold
minDarklandNoise = 0.35;  // from 0.4

// Option B: Expand distance ring
minDarklandDistance = 5500;  // from 6000
maxDarklandDistance = 10500; // from 10000
```

**Impact:** Would increase Mistlands to 25-30% range

---

## Part 7: Weight Summary Table

### Biome Classification Weights

| Biome | Priority | Distance Min | Distance Max | Noise Threshold | Height Min | Height Max | Effective Weight |
|-------|----------|--------------|--------------|-----------------|------------|------------|------------------|
| Ashlands | **1** ⚠️ | ~9626m | Edge | N/A (distance only) | Any | Any | **High** (checked first) |
| Ocean | 2 | Any | Any | N/A | -400 | 0.05 | **High** (baseHeight check) |
| DeepNorth | **3** ⚠️ | ~7140m | Edge | N/A (distance only) | Any | Any | **High** (checked early) |
| Mountain | 4 | Any | Any | N/A | 0.4 | 200 | **Medium** (baseHeight check) |
| Swamp | 5 | 2000m | 6000m | **0.6** ⚠️ | 0.05 | 0.25 | **Low** (restrictive threshold + height) |
| **Mistlands** | **6** ⚠️ | 6000m | 10000m | 0.4 | Any | Any | **Low** (late priority) |
| Plains | 7 | 3000m | 8000m | 0.4 | Any | Any | **Medium** |
| BlackForest | 8 | 600m / >5000m | 6000m | 0.4 | Any | Any | **Medium** (fallback rule) |
| Meadows | 9 | Any | Any | N/A (default) | Any | Any | **Low** (fallback only) |

**Key Observations:**
1. **Priority is the strongest weight** - Early checks dominate distribution
2. **Noise thresholds act as filters** - 0.6 vs 0.4 = ~40% difference in coverage
3. **Distance rings partition territory** - But polar biomes overlap with others
4. **Height requirements are secondary** - Only Swamp and Mountain have strict height bands

---

## Conclusion

### Current State Assessment

**Data Quality:** ✅ **EXCELLENT** - 100% faithful to `WorldGenerator.GetBiome()` API
**Distribution Balance:** ⚠️ **NEEDS IMPROVEMENT** - Polar over-representation, Mistlands starvation
**Filter Effectiveness:** 🔄 **MIXED** - Recovers Mistlands but eliminates DeepNorth entirely

### Recommended Actions

**Immediate (Filter Adjustments):**
1. ✅ Fix Filter #2 to preserve DeepNorth in far north (lines 271-273 in renderer.js)
2. ✅ Verify polar filter thresholds match intended crescent shapes
3. ✅ Add toggle for each filter individually (not just all-or-nothing)

**Medium-term (C# Plugin):**
1. 🔄 Reorder biome priority: Check Mistlands BEFORE polar biomes
2. 🔄 Lower Swamp noise threshold from 0.6 to 0.5
3. 🔄 Adjust Ashlands threshold/offset for better southern concentration

**Long-term (Architecture):**
1. 💡 Implement biome blend zones (multi-biome per sample)
2. 💡 Expose noise functions to client for perfect regeneration
3. 💡 Add biome "intensity" metadata (how strongly a location matches criteria)

---

## References

- **Decompiled Code:** `/procedural-export/decompiled/WorldGenerator.decompiled.cs`
- **Filter Implementation:** `/procedural-export/client/renderer.js:247-350`
- **Previous Analysis:** `/procedural-export/BIOME_DISCREPANCY_ANALYSIS.md`
- **Recovery Documentation:** `/procedural-export/MISTLANDS_RECOVERY_FIX.md`
- **Raw Data:** `/procedural-export/output/samples/hkLycKKCMI-samples-1024.json`

---

**Analysis Script:** `scripts/analyze_biome_decision_logic.py`
**Generated:** 2025-10-09
**World Seed:** hkLycKKCMI (G0Ws7CmRyU)
**Sample Resolution:** 1024×1024 (1,048,576 points)
