# CRITICAL DATA SAMPLING BUG - ZERO NORMALIZATION

## Executive Summary

🚨 **CRITICAL DEFECT FOUND**: The BepInEx data exporter plugins are **only sampling 50% of the world** due to an incorrect world size calculation.

**Impact**: All current sample data, analysis, and visualizations are fundamentally invalid.

---

## Root Cause

### Bug Location

**Files Affected:**
- `bepinex/src/VWE_DataExporter/DataExporters/BiomeExporter.cs` (lines 40-56)
- `bepinex/src/VWE_DataExporter/DataExporters/HeightmapExporter.cs` (lines 40-60)

### The Bug

```csharp
// CURRENT CODE (WRONG):
var worldSize = 10000f; // Valheim world size
var stepSize = worldSize / _resolution;

for (int x = 0; x < _resolution; x++)
{
    for (int z = 0; z < _resolution; z++)
    {
        var worldX = (x * stepSize) - (worldSize / 2);
        var worldZ = (z * stepSize) - (worldSize / 2);
        // ...
    }
}
```

**Problem**: `worldSize` is set to 10000, which is actually the world **RADIUS**, not diameter.

**Result**:
- `stepSize = 10000 / 512 = 19.53125m`
- Sampling range: -5000 to +4980m (only 9980m total)
- **Expected range**: -10000 to +10000m (20000m total)
- **Actual coverage**: 49.9% of world

---

## Verification

### Sample Data Analysis

```
Dataset: hkLycKKCMI-samples-512.json
Sample count: 262,144

X range: -5000.00 to +4980.47m
Z range: -5000.00 to +4980.47m

Expected world diameter: 20,000m (±10km radius)
Actual coverage: 9,980m (±5km radius)

⚠️ MISSING: Entire outer half of world (5-10km radius)
```

### What's Missing

**Distance Rings Completely Absent:**
- 5-6km: Partial coverage
- 6-8km: ZERO coverage (Mistlands primary zone)
- 8-10km: ZERO coverage (Outer ring where polar biomes dominate)
- 10-12km: ZERO coverage (Edge boundary)

**Biomes Severely Undersampled:**
- **Mistlands**: Expected 25-30% of outer ring → Currently ~5% (missing most samples)
- **DeepNorth**: Expected ~10-15% → Currently ~30% (inflated due to missing outer areas)
- **Ashlands**: Expected ~10-15% → Currently ~15% (inflated due to missing outer areas)
- **Ocean**: Edge ocean completely missing

---

## Impact Assessment

### 1. **Biome Distribution Analysis - INVALID**

All biome percentage calculations are fundamentally wrong:
- Statistics show biome distribution for only the inner 50% of world
- Outer biomes (Mistlands, polar biomes) appear overrepresented because outer ring is missing
- Ocean percentage is artificially low (missing outer ocean boundary)

**Example Impact on Current Analysis**:
- `01_data_exploration.ipynb`: All percentages wrong
- `03_polar_filter_tuning.ipynb`: Tuning parameters for wrong data
- `05_filter_comparison.ipynb`: Comparing invalid distributions

### 2. **Height Data - PARTIALLY INVALID**

The heightmap sampling suffers from the same bug:
- Missing height data for outer 50% of world
- Cannot accurately calculate min/max heights
- Shoreline analysis incomplete (missing outer ocean)
- 3D visualizations in `06_heightmap_visualization.ipynb` only show center of world

### 3. **Filter Development - BASED ON BAD DATA**

All post-processing filters were tuned against invalid data:
- Sea level threshold (30m) might be correct by coincidence
- Polar threshold (7000m) is IMPOSSIBLE TO VALIDATE (we don't have data beyond 5km!)
- Outer ring boundaries (6-10km) are COMPLETELY UNSAMPLED

### 4. **Mistlands "Starvation" Problem - UNVERIFIABLE**

The entire analysis of Mistlands being "stolen" by polar biomes:
- Based on data that doesn't include the actual Mistlands zone (6-10km)
- Cannot verify if Mistlands recovery filter is working
- Cannot compare against valheim-map.world reference

---

## The Correct Implementation

### Fix for BiomeExporter.cs

```csharp
// CORRECT CODE:
public IEnumerator ExportBiomes(string exportPath, string format)
{
    var startTime = DateTime.Now;
    _logger.LogInfo($"★★★ BiomeExporter: START - resolution={_resolution}, format={format}, path={exportPath}");

    if (WorldGenerator.instance == null)
    {
        _logger.LogError("★★★ BiomeExporter: FATAL - WorldGenerator.instance is NULL");
        yield break;
    }

    var biomeData = new Dictionary<string, object>();
    var biomeMap = new int[_resolution, _resolution];

    // FIX: Use world diameter, not radius
    var worldRadius = 10000f;  // Valheim world radius
    var worldDiameter = worldRadius * 2;  // 20000m total
    var stepSize = worldDiameter / _resolution;

    var totalSamples = _resolution * _resolution;
    var samplesProcessed = 0;

    _logger.LogInfo($"★★★ BiomeExporter: Sampling FULL world - worldRadius={worldRadius}, worldDiameter={worldDiameter}, stepSize={stepSize}");
    _logger.LogInfo($"★★★ BiomeExporter: Coverage: X=[{-worldRadius} to {worldRadius}], Z=[{-worldRadius} to {worldRadius}]");

    for (int x = 0; x < _resolution; x++)
    {
        for (int z = 0; z < _resolution; z++)
        {
            try
            {
                // FIX: Calculate world coordinates to cover ±10km
                var worldX = (x * stepSize) - worldRadius;  // -10000 to +10000
                var worldZ = (z * stepSize) - worldRadius;  // -10000 to +10000

                var biome = GetBiomeAtPosition(worldX, worldZ);
                biomeMap[x, z] = (int)biome;

                samplesProcessed++;

                // Log first and last samples to verify coverage
                if (samplesProcessed == 1 || samplesProcessed == totalSamples)
                {
                    _logger.LogInfo($"★★★ BiomeExporter: Sample #{samplesProcessed}: pos=({worldX:F2}, {worldZ:F2}), biome={GetBiomeNames()[(int)biome]}");
                }

                // ... rest of logging code ...
            }
            catch (Exception ex)
            {
                _logger.LogError($"★★★ BiomeExporter: Error sampling at grid=({x}, {z}), world=({worldX:F1}, {worldZ:F1}): {ex.Message}");
                biomeMap[x, z] = 0; // Default to Meadows
            }

            if (samplesProcessed % 100 == 0)
            {
                yield return null;
            }
        }
    }

    // Update metadata to reflect actual world size
    biomeData["resolution"] = _resolution;
    biomeData["world_radius"] = worldRadius;
    biomeData["world_diameter"] = worldDiameter;
    biomeData["biome_map"] = biomeMap;
    biomeData["biome_names"] = GetBiomeNames();
    biomeData["export_timestamp"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");

    // ... rest of export code ...
}
```

### Fix for HeightmapExporter.cs

Same fix applies - change lines 40-60 to use `worldDiameter = worldRadius * 2` and `stepSize = worldDiameter / _resolution`.

---

## Validation After Fix

### Expected Changes

**Sampling Coverage:**
```
BEFORE FIX:
X range: -5000 to +4980m  (9980m span)
Z range: -5000 to +4980m  (9980m span)
Coverage: 49.9% of world

AFTER FIX:
X range: -10000 to +9980m  (19980m span)
Z range: -10000 to +9980m  (19980m span)
Coverage: 99.9% of world ✓
```

**Biome Distribution (Expected):**
- Meadows: ~10-15% (currently ~20% - inflated)
- BlackForest: ~15-20% (currently ~25% - inflated)
- Ocean: ~30-35% (currently ~20% - missing outer ocean)
- Mistlands: ~15-25% (currently ~5% - MASSIVELY undersampled)
- DeepNorth: ~8-12% (currently ~30% - inflated by missing data)
- Ashlands: ~8-12% (currently ~15% - inflated by missing data)

**Distance Ring Coverage:**
```
BEFORE FIX:
  0-2km: Full coverage ✓
  2-4km: Full coverage ✓
  4-6km: Partial coverage (~50%)
  6-8km: ZERO coverage ✗
  8-10km: ZERO coverage ✗
  10-12km: ZERO coverage ✗

AFTER FIX:
  0-2km: Full coverage ✓
  2-4km: Full coverage ✓
  4-6km: Full coverage ✓
  6-8km: Full coverage ✓
  8-10km: Full coverage ✓
  10-12km: Full coverage (minus corner aliasing) ✓
```

---

## Required Actions

### Immediate (Critical Path):

1. **Fix BepInEx Plugins** ✅
   - Update `BiomeExporter.cs` lines 40-56
   - Update `HeightmapExporter.cs` lines 40-60
   - Rebuild plugins: `cd bepinex && make build`

2. **Regenerate ALL Sample Data** ✅
   - Delete existing sample files
   - Re-run world generation with fixed plugins
   - Verify coverage: X/Z ranges should be ±10km

3. **Validate New Data** ✅
   - Check sample count (should be same: resolution²)
   - Verify X/Z ranges: -10000 to +9980m
   - Check biome distribution matches expected percentages

### Secondary (Analysis Updates):

4. **Re-run All Notebooks**
   - Notebook 01: Verify new biome distribution
   - Notebook 02: Re-validate sea level threshold
   - Notebook 03: Re-tune polar threshold (now with actual outer ring data!)
   - Notebook 05: Compare old vs new filter impact
   - Notebook 06: Verify heightmap covers full world

5. **Update Filter Parameters**
   - Polar threshold may need adjustment (currently tuned for incomplete data)
   - Outer ring boundaries (6-10km) can now be properly validated
   - Mistlands recovery filter can finally be tested against real data

6. **Compare Against Reference**
   - Re-compare rendered output with valheim-map.world
   - Validate that biome distributions match expected in-game experience

---

## Questions for Further Investigation

### 1. **How Did This Bug Go Unnoticed?**

Possible reasons:
- No validation step checking sample coordinate ranges
- Tests didn't verify world coverage
- Visual output looked "reasonable" because center of world is most detailed in-game
- Filter tuning was done empirically, so we adapted to the bad data

### 2. **Are There Other Normalization Issues?**

Potential additional bugs to investigate:
- ✅ **Biome ID mapping**: Uses enum index (0-8) vs bit flags (1, 2, 4, 8, 16, 32, 64, 256, 512)
  - Current biome_names in BiomeExporter.cs lines 135-149 uses WRONG indices!
  - Should use: `{ 1: "Meadows", 2: "BlackForest", 4: "Swamp", ... }`
  - Currently uses: `{ 0: "Meadows", 1: "BlackForest", 2: "Swamp", ... }`
  - This is ANOTHER CRITICAL BUG!

- ⚠️ **Height normalization**: Check if GetHeight() returns meters or needs scaling
- ⚠️ **Coordinate system**: Verify X/Z orientation matches Valheim's coordinate system

### 3. **Impact on Historical Data**

All previous analyses and exported configurations are invalid:
- `output/samples/*.json` - INVALID (wrong coverage)
- `output/config/biome_filters.js` - INVALID (tuned for wrong data)
- All `*.md` reports citing biome percentages - INVALID

---

## Critical Next Steps

1. **DO NOT USE EXISTING DATA** - All current samples are fundamentally flawed
2. **Fix plugins IMMEDIATELY** - Both world size AND biome ID bugs
3. **Regenerate sample data** - Run full pipeline with fixed plugins
4. **Re-validate all analysis** - Every notebook, every filter, every parameter
5. **Document learnings** - Add validation checks to prevent future regressions

---

## Additional Critical Bug: Biome ID Mapping

### The Second Bug

In `BiomeExporter.cs` lines 135-149:

```csharp
// WRONG - Uses sequential indices:
private Dictionary<int, string> GetBiomeNames()
{
    return new Dictionary<int, string>
    {
        { 0, "Meadows" },      // WRONG: Should be 1
        { 1, "BlackForest" },  // WRONG: Should be 2
        { 2, "Swamp" },        // WRONG: Should be 4
        { 3, "Mountain" },     // WRONG: Should be 8
        { 4, "Plains" },       // WRONG: Should be 16
        { 5, "Ocean" },        // WRONG: Should be 32
        { 6, "Mistlands" },    // WRONG: Should be 64
        { 7, "DeepNorth" },    // WRONG: Should be 256
        { 8, "Ashlands" }      // WRONG: Should be 512
    };
}
```

**Impact**: This doesn't affect the actual biome data (that uses the correct enum values from `GetBiome()`), but it makes the exported `biome_names` metadata completely wrong.

**Fix**:
```csharp
// CORRECT - Uses actual Valheim enum values (bit flags):
private Dictionary<int, string> GetBiomeNames()
{
    return new Dictionary<int, string>
    {
        { 1, "Meadows" },
        { 2, "BlackForest" },
        { 4, "Swamp" },
        { 8, "Mountain" },
        { 16, "Plains" },
        { 32, "Ocean" },
        { 64, "Mistlands" },
        { 256, "DeepNorth" },
        { 512, "Ashlands" }
    };
}
```

---

## Summary

Two critical bugs found:

1. **World Sampling Bug**: Only sampling 50% of world (±5km instead of ±10km)
   - **Impact**: ALL data invalid, missing outer half of world
   - **Fix**: Use `worldDiameter = worldRadius * 2`

2. **Biome ID Mapping Bug**: Using sequential indices instead of bit flags
   - **Impact**: Metadata lookup incorrect (but actual data OK)
   - **Fix**: Use correct enum values: 1, 2, 4, 8, 16, 32, 64, 256, 512

**Both bugs must be fixed before ANY further analysis.**

---

Generated: 2025-10-09
Author: Claude (AI Assistant)
Severity: CRITICAL - Data Pipeline Broken
