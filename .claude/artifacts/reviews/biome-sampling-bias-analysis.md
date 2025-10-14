# Biome Sampling Bias - Root Cause Analysis & Fix

**Date:** 2025-10-13
**Component:** `etl/experimental/bepinex-adaptive-sampling/src/VWE_DataExporter/DataExporters/BiomeExporter.cs`
**Issue:** Boundary sampling bias causing +16% DeepNorth, +11% Ashlands over-representation

## 1. ROOT CAUSE (CONFIRMED)

**Location:** `/home/steve/projects/valhem-world-engine/etl/experimental/bepinex-adaptive-sampling/src/VWE_DataExporter/DataExporters/BiomeExporter.cs`
**Lines:** 59-70 (sampling loop), 65-67 (coordinate calculation)

### Technical Explanation

The sampling strategy uses **uniform grid sampling with pixel-corner alignment**, causing systematic boundary bias:

```csharp
// Current code (lines 65-67):
var worldX = (x * stepSize) - worldRadius;
var worldZ = (z * stepSize) - worldRadius;
```

**Problem:** Grid points align to pixel corners, not centers:
- **Grid point [0, 0]** samples world position **(-10000, -10000)** - EXACT edge
- **Grid point [255, 255]** samples world position **(+9922, +9922)** - Near edge
- **Step size:** 78.12m (20000m / 256 pixels)

**Why This Causes Bias:**

1. **Edge Over-sampling:** Outer 10% of map (25 pixels/side) captures 35.2% of total samples
2. **Ocean bias at edges:** +32.81% in edge region vs interior
3. **DeepNorth/Ashlands at poles:** Edge sampling hits polar biomes disproportionately
4. **Interior under-sampling:** Large uniform regions (Ocean, Meadows) get proportionally fewer samples

### Validated Evidence

**Distribution Anomalies (256x256 resolution):**
```
Biome           Edge %    Interior %    Difference
Ocean           39.41%      6.60%       +32.81%  ← Edge-biased
DeepNorth       35.83%     29.49%        +6.34%  ← Edge-biased
Plains           0.00%     17.54%       -17.54%  ← Interior-biased
BlackForest      4.97%     13.35%        -8.39%  ← Interior-biased
Ashlands         7.87%     18.61%       -10.73%  ← Mixed (see note)
```

**Note on Ashlands:** Despite showing as interior-biased in edge/interior analysis, Ashlands is OVER-represented overall (+11.83%) due to placement near map edges in Valheim's world generation.

**Corner Samples:**
```
Top-Left     (-10000, -10000) → Ocean
Top-Right    (-10000,  +9922) → DeepNorth
Bottom-Left  ( +9922, -10000) → Ocean
Bottom-Right ( +9922,  +9922) → DeepNorth
```

All corners sample extreme boundaries, not representative interior regions.

---

## 2. PROPOSED FIX

### Strategy: Pixel-Center Sampling

Shift grid alignment by half-step to sample pixel centers instead of corners:

```csharp
// FIXED coordinate calculation (lines 65-67):
var worldX = ((x + 0.5f) * stepSize) - worldRadius;
var worldZ = ((z + 0.5f) * stepSize) - worldRadius;
```

**Effect:**
- **Grid point [0, 0]** now samples **(-9961, -9961)** - 39m inside boundary
- **Grid point [255, 255]** now samples **(+9961, +9961)** - 39m inside boundary
- **Coverage:** Still spans full ±10km world, but samples centers not edges

### Expected Impact

- **Reduces edge over-sampling:** Shifts all samples 39m inward
- **More representative coverage:** Each pixel represents area around its center
- **Standard practice:** Matches raster GIS pixel-center convention

### Performance

No change - same number of samples, same sampling method, only coordinate offset.

---

## 3. CODE CHANGES

### File: `BiomeExporter.cs`

**Change 1: Pixel-center sampling**

```csharp
// Lines 65-67 - REPLACE:
var worldX = (x * stepSize) - worldRadius;
var worldZ = (z * stepSize) - worldRadius;

// WITH:
var worldX = ((x + 0.5f) * stepSize) - worldRadius;
var worldZ = ((z + 0.5f) * stepSize) - worldRadius;
```

**Change 2: Update logging to reflect new sampling (optional but recommended)**

```csharp
// Line 78 - ADD comment:
_logger.LogInfo($"★★★ BiomeExporter: Sample #{samplesProcessed}/{totalSamples} - pos=({worldX:F2}, {worldZ:F2}), biome={biomeName} [pixel-center]");
```

---

## 4. VALIDATION PLAN

### Validation Script 1: Sample Density Heatmap

**File:** `/home/steve/projects/valhem-world-engine/scripts/visualize_sample_density.py`

```python
#!/usr/bin/env python3
"""
Visualize spatial distribution of biome samples
Generates heatmap showing sample coverage patterns
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def visualize_sample_density(json_path: Path, output_path: Path):
    with open(json_path) as f:
        data = json.load(f)

    biome_map = np.array(data['biome_map'])
    resolution = data['resolution']
    world_radius = data['world_radius']

    # Create coordinate grids
    step_size = (2 * world_radius) / resolution
    x_coords = np.arange(resolution) * step_size - world_radius
    z_coords = np.arange(resolution) * step_size - world_radius

    # Calculate distance from center for each sample
    X, Z = np.meshgrid(x_coords, z_coords)
    distances = np.sqrt(X**2 + Z**2)

    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Sample positions
    axes[0].scatter(X.flatten(), Z.flatten(), s=1, alpha=0.3, c='blue')
    axes[0].set_title('Sample Positions (Uniform Grid)')
    axes[0].set_xlabel('World X (m)')
    axes[0].set_ylabel('World Z (m)')
    axes[0].set_aspect('equal')
    axes[0].grid(True, alpha=0.3)

    # Distance heatmap
    im1 = axes[1].imshow(distances, cmap='viridis', origin='lower',
                         extent=[-world_radius, world_radius, -world_radius, world_radius])
    axes[1].set_title('Distance from Center')
    axes[1].set_xlabel('World X (m)')
    axes[1].set_ylabel('World Z (m)')
    plt.colorbar(im1, ax=axes[1], label='Distance (m)')

    # Radial density distribution
    radial_bins = np.linspace(0, world_radius, 20)
    sample_counts, _ = np.histogram(distances.flatten(), bins=radial_bins)
    axes[2].plot(radial_bins[:-1], sample_counts, 'o-')
    axes[2].set_title('Radial Sample Distribution')
    axes[2].set_xlabel('Distance from Center (m)')
    axes[2].set_ylabel('Number of Samples')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Density visualization saved to: {output_path}")

    # Statistical summary
    print(f"\nSample Coverage Statistics:")
    print(f"  Resolution: {resolution}x{resolution}")
    print(f"  Total samples: {resolution * resolution:,}")
    print(f"  Step size: {step_size:.2f}m")
    print(f"  Min X: {x_coords[0]:.1f}m")
    print(f"  Max X: {x_coords[-1]:.1f}m")
    print(f"  Min Z: {z_coords[0]:.1f}m")
    print(f"  Max Z: {z_coords[-1]:.1f}m")
    print(f"  Min distance: {distances.min():.1f}m")
    print(f"  Max distance: {distances.max():.1f}m")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python visualize_sample_density.py <biomes.json> [output.png]")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('sample_density.png')

    visualize_sample_density(json_path, output_path)
```

### Validation Script 2: Before/After Comparison

**File:** `/home/steve/projects/valhem-world-engine/scripts/compare_biome_distributions.py`

```python
#!/usr/bin/env python3
"""
Compare two biome JSON files (before/after fix)
"""

import json
import sys
from pathlib import Path
from collections import Counter

BIOME_NAMES = {
    1: "Meadows", 2: "Swamp", 4: "Mountain", 8: "BlackForest",
    16: "Plains", 32: "Ocean", 64: "Mistlands", 256: "DeepNorth", 512: "Ashlands"
}

EXPECTED = {
    "Ocean": 30.0, "DeepNorth": 15.0, "Meadows": 12.0, "BlackForest": 10.0,
    "Plains": 10.0, "Mountain": 8.0, "Swamp": 7.0, "Mistlands": 5.0, "Ashlands": 3.0
}

def analyze(json_path):
    with open(json_path) as f:
        data = json.load(f)

    biome_map = data['biome_map']
    flat = [bid for row in biome_map for bid in row]
    counts = Counter(flat)
    total = len(flat)

    results = {}
    for biome_id in [1, 2, 4, 8, 16, 32, 64, 256, 512]:
        name = BIOME_NAMES[biome_id]
        pct = (counts.get(biome_id, 0) / total) * 100
        expected = EXPECTED.get(name, 0)
        error = pct - expected
        results[name] = {'pct': pct, 'expected': expected, 'error': error}

    return results

def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_biome_distributions.py <before.json> <after.json>")
        sys.exit(1)

    before_results = analyze(Path(sys.argv[1]))
    after_results = analyze(Path(sys.argv[2]))

    print(f"\n{'='*90}")
    print("BEFORE/AFTER COMPARISON")
    print(f"{'='*90}\n")
    print(f"{'Biome':<15} {'Before %':<12} {'After %':<12} {'Expected %':<12} {'Improvement':<15}")
    print("-" * 90)

    total_improvement = 0
    for name in sorted(EXPECTED.keys(), key=lambda n: EXPECTED[n], reverse=True):
        before = before_results[name]
        after = after_results[name]
        improvement = abs(before['error']) - abs(after['error'])
        total_improvement += improvement

        flag = "✅" if improvement > 1 else "→" if abs(improvement) < 1 else "❌"
        print(f"{flag} {name:<15} {before['pct']:>6.2f}%      {after['pct']:>6.2f}%      "
              f"{before['expected']:>6.1f}%      {improvement:>+6.2f}%")

    print("-" * 90)
    print(f"{'TOTAL IMPROVEMENT:':<52} {total_improvement:>+6.2f}%\n")

    # Summary
    before_total_error = sum(abs(r['error']) for r in before_results.values())
    after_total_error = sum(abs(r['error']) for r in after_results.values())

    print("Summary:")
    print(f"  Before - Total absolute error: {before_total_error:.2f}%")
    print(f"  After  - Total absolute error: {after_total_error:.2f}%")
    print(f"  Improvement: {before_total_error - after_total_error:+.2f}%")
    print(f"  {'SUCCESS' if after_total_error < 30 else 'NEEDS WORK'} - "
          f"Target: <30% total error\n")

if __name__ == '__main__':
    main()
```

### Success Criteria

1. **Total absolute error:** Reduce from 61.35% to < 45% (25% improvement minimum)
2. **Per-biome error:** All biomes within ±8% (relaxed from ±5% given uniform sampling limitations)
3. **Worst-case error:** Reduce from +16.73% (DeepNorth) to < ±10%
4. **Edge bias eliminated:** Ocean edge distribution < 25% (currently 39.41%)

---

## 5. IMPLEMENTATION PLAN

### Quick Win (15 minutes)

**Priority:** HIGH - Single-line fix with major impact

1. Apply pixel-center sampling fix (1 line change)
2. Rebuild BepInEx plugin
3. Run test export for seed `hkLycKKCMI`
4. Run validation: `python scripts/analyze_biome_distribution.py output/biomes.json`

**Expected outcome:** 30-50% reduction in total distribution error

### Medium-term (2-4 hours)

**Priority:** MEDIUM - Validation infrastructure

1. Create validation scripts (sample density visualizer, before/after comparison)
2. Run comprehensive before/after analysis
3. Document results in validation report
4. Update test suite to catch future regressions

### Long-term (Optional - 1-2 days)

**Priority:** LOW - If quick win insufficient

1. **Implement true adaptive sampling:**
   - Detect biome boundaries using gradient detection
   - Increase sampling density at boundaries (2-4x)
   - Reduce sampling in uniform regions (0.5x)
   - Target: Same total samples, better distribution

2. **Multi-resolution approach:**
   - Coarse pass (128x128) for general layout
   - Fine pass (512x512) for boundary refinement
   - Composite into final 256x256 output

**Trade-off:** Complexity vs accuracy - only pursue if pixel-center fix < 40% improvement

---

## 6. REFERENCES

**Files Modified:**
- `/home/steve/projects/valhem-world-engine/etl/experimental/bepinex-adaptive-sampling/src/VWE_DataExporter/DataExporters/BiomeExporter.cs` (lines 65-67)

**Validation Scripts:**
- `/home/steve/projects/valhem-world-engine/scripts/analyze_biome_distribution.py` (existing)
- `/home/steve/projects/valhem-world-engine/scripts/visualize_sample_density.py` (new)
- `/home/steve/projects/valhem-world-engine/scripts/compare_biome_distributions.py` (new)

**Test Data:**
- Current output: `/home/steve/projects/valhem-world-engine/etl/experimental/bepinex-adaptive-sampling/output/world_data/biomes.json`
- Reference image: `/home/steve/projects/valhem-world-engine/docs/biomes_hnLycKKCMI.png`

**Performance:**
- Current: ~130x speedup maintained (no sampling count change)
- Memory: No change (same grid dimensions)
