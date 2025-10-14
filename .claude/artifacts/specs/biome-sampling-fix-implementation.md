# Biome Sampling Bias Fix - Implementation Guide

**Date:** 2025-10-13
**Issue:** Boundary sampling bias causing DeepNorth +16.73%, Ashlands +11.83% over-representation
**Root Cause:** Grid samples align to pixel corners, not centers - causing edge over-sampling

---

## Quick Fix (15 minutes)

### 1. Apply Pixel-Center Sampling

**File:** `/home/steve/projects/valhem-world-engine/etl/experimental/bepinex-adaptive-sampling/src/VWE_DataExporter/DataExporters/BiomeExporter.cs`

**Change Lines 65-67:**

```csharp
// BEFORE (corner-aligned):
var worldX = (x * stepSize) - worldRadius;
var worldZ = (z * stepSize) - worldRadius;

// AFTER (center-aligned):
var worldX = ((x + 0.5f) * stepSize) - worldRadius;
var worldZ = ((z + 0.5f) * stepSize) - worldRadius;
```

**Explanation:**
- Current: Grid [0,0] samples (-10000, -10000) - exact world edge
- Fixed: Grid [0,0] samples (-9961, -9961) - 39m inside boundary
- Effect: Reduces edge bias by shifting all samples to pixel centers

### 2. Rebuild and Test

```bash
cd /home/steve/projects/valhem-world-engine/etl/experimental/bepinex-adaptive-sampling

# Rebuild BepInEx plugin
make build

# Run test export (seed: hkLycKKCMI)
make run-export

# Analyze results
python /home/steve/projects/valhem-world-engine/scripts/analyze_biome_distribution.py \
    output/world_data/biomes.json
```

### 3. Validation

**Expected Improvement:**
- Total absolute error: 61.35% → < 45% (25% reduction minimum)
- DeepNorth error: +16.73% → < +10%
- Ocean error: -11.84% → < -8%
- All biomes within ±8% of expected

**Success Criteria:**
- ✅ Total error reduction > 15%
- ✅ Max single-biome error < 10%
- ✅ 7/9 biomes within ±8%

---

## Validation Commands

### Before/After Comparison

```bash
# Copy current (broken) output for comparison
cp etl/experimental/bepinex-adaptive-sampling/output/world_data/biomes.json \
   /tmp/biomes_before.json

# After applying fix and re-exporting:
python scripts/compare_biome_distributions.py \
    /tmp/biomes_before.json \
    etl/experimental/bepinex-adaptive-sampling/output/world_data/biomes.json
```

### Sample Density Visualization

```bash
# Generates heatmap showing spatial sample distribution
python scripts/visualize_sample_density.py \
    etl/experimental/bepinex-adaptive-sampling/output/world_data/biomes.json \
    sample_density_analysis.png
```

---

## If Quick Fix Insufficient (<40% improvement)

### Option A: Multi-Scale Sampling (4-6 hours)

Sample at multiple resolutions and composite:
1. Coarse pass: 128x128 for general layout
2. Fine pass: 512x512 at biome boundaries only
3. Composite into 256x256 output

**Trade-off:** 2x computation time, better accuracy

### Option B: True Adaptive Sampling (1-2 days)

Implement gradient-based boundary detection:
1. Initial coarse sampling (64x64)
2. Detect high-variance regions (biome boundaries)
3. Adaptively increase sampling density at boundaries (4x)
4. Reduce sampling in uniform regions (0.5x)
5. Maintain same total sample count

**Trade-off:** Complex implementation, best accuracy

---

## Files Modified

**Source Code:**
- `/home/steve/projects/valhem-world-engine/etl/experimental/bepinex-adaptive-sampling/src/VWE_DataExporter/DataExporters/BiomeExporter.cs` (lines 65-67)

**Validation Scripts (Created):**
- `/home/steve/projects/valhem-world-engine/scripts/visualize_sample_density.py`
- `/home/steve/projects/valhem-world-engine/scripts/compare_biome_distributions.py`

**Documentation:**
- `/home/steve/projects/valhem-world-engine/.claude/artifacts/reviews/biome-sampling-bias-analysis.md`
- `/home/steve/projects/valhem-world-engine/.claude/artifacts/specs/biome-sampling-fix-implementation.md` (this file)

---

## Technical Details

### Root Cause Analysis

**Current Sampling:**
```
Grid [0, 0]     → World (-10000.0, -10000.0)  [EXACT EDGE]
Grid [255, 255] → World (+9921.9, +9921.9)    [near edge]
Step size: 78.12m
```

**Edge Distribution (outer 10% of map = 25 pixels/side):**
- Edge pixels: 35.2% of total samples
- Ocean in edge region: 39.41% (vs 6.60% interior)
- DeepNorth in edge region: 35.83% (vs 29.49% interior)

**Why This Causes Bias:**
1. Valheim world generation places Ocean/DeepNorth at poles/edges
2. Uniform grid samples edges disproportionately (corner alignment)
3. Large uniform interior regions (Meadows, Plains) get proportionally fewer samples
4. Boundary biomes (Ashlands) get sampled more due to edge proximity

### Fix Mechanism

**Pixel-Center Sampling:**
```
Grid [0, 0]     → World (-9960.9, -9960.9)  [39m inside]
Grid [255, 255] → World (+9960.9, +9960.9)  [39m inside]
Step size: 78.12m (unchanged)
```

**Effect:**
- All samples shift 0.5 * stepSize = 39m inward
- Reduces edge over-sampling by ~10%
- Standard GIS practice: pixels represent areas, sample centers
- No performance impact: same sample count, same API calls

### Performance

- Current: ~3 minutes for 256x256 @ 65,536 samples (~130x speedup)
- After fix: Same (no sampling count change)
- Memory: Same (identical grid dimensions)

---

## References

**Validation Data:**
- Test seed: `hkLycKKCMI`
- Expected distributions: `global/data/validation-data.yml` (if exists)
- Reference image: `/home/steve/projects/valhem-world-engine/docs/biomes_hnLycKKCMI.png`

**Analysis Scripts:**
- Current: `/home/steve/projects/valhem-world-engine/scripts/analyze_biome_distribution.py`
- New: `/home/steve/projects/valhem-world-engine/scripts/visualize_sample_density.py`
- New: `/home/steve/projects/valhem-world-engine/scripts/compare_biome_distributions.py`

**Build System:**
- Makefile: `/home/steve/projects/valhem-world-engine/etl/experimental/bepinex-adaptive-sampling/Makefile`
- Docker compose: `/home/steve/projects/valhem-world-engine/etl/experimental/bepinex-adaptive-sampling/docker/docker-compose.yml`
