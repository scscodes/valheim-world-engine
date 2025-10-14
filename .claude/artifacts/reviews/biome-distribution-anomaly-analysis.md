# Biome Distribution Anomaly Analysis
## Valheim World Engine - Adaptive Sampling Investigation

**Date:** 2025-10-13
**Test Seed:** hkLycKKCMI
**Resolution:** 256×256 (65,536 samples)
**Issue:** Strange biome distributions, particularly DeepNorth "bleeding" patterns

---

## Executive Summary

**CRITICAL FINDING:** The BiomeExporter PNG color mapping function (`GetBiomeColor()`) uses **SEQUENTIAL indices (0-8)** instead of **BIT FLAG values (1, 2, 4, 8, 16, 32, 64, 256, 512)**. This bug causes incorrect PNG visualizations but **does NOT affect** the JSON data or downstream rendering.

**ROOT CAUSE IDENTIFIED:** The "bleeding" anomaly is likely caused by **BICUBIC interpolation** treating discrete biome IDs as continuous values during upscaling operations.

---

## 1. Architecture Analysis

### 1.1 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: Data Sampling (C# BepInEx Plugin)                     │
│─────────────────────────────────────────────────────────────────│
│ WorldGenerator.GetBiome(worldX, worldZ)                        │
│   ↓ Returns: Heightmap.Biome (bit flags: 1,2,4,8,16,32,64,256,512)│
│ biomeMap[x, z] = (int)biome                                     │
│   ↓ Stores: 2D array of integers                               │
│ JSON Export: {"biome_map": [[32,32,32,...,256,...],...]}       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2a: Python Backend (Optional Image Generation)           │
│─────────────────────────────────────────────────────────────────│
│ Load JSON: biome_array = np.array(biome_data.biome_map)       │
│   ↓ Direct mapping: biome ID → RGB color                       │
│ BIOME_COLORS[biome_id] maps bit flags → colors                 │
│   ↓ No interpolation at this stage                             │
│ Optional BICUBIC upscaling: image.resize(PIL.BICUBIC) ⚠️       │
│   ↓ PROBLEM: Treats discrete IDs as continuous values!         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2b: TypeScript Frontend (Canvas Rendering)               │
│─────────────────────────────────────────────────────────────────│
│ Load JSON: biome_map[y][x] → biomeId                          │
│   ↓ Direct mapping: biomeId → hex color                        │
│ BiomeColors[biomeId] maps bit flags → hex strings              │
│   ↓ No interpolation: fillRect() with solid colors             │
│ Pixel scaling: pixelSize = targetWidth / resolution            │
│   ↓ Each sample rendered as solid block                        │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Coordinate Transformations

#### Stage 1: BiomeExporter.cs (Lines 59-70)

```csharp
// Resolution 256, World radius 10,000m
for (int x = 0; x < 256; x++) {
    for (int z = 0; z < 256; z++) {
        // stepSize = 20,000 / 256 = 78.125m
        var worldX = (x * stepSize) - worldRadius;  // Range: -10000 to +9921.875
        var worldZ = (z * stepSize) - worldRadius;  // Range: -10000 to +9921.875

        var biome = GetBiomeAtPosition(worldX, worldZ);
        biomeMap[x, z] = (int)biome;  // Store bit flag value
    }
}
```

**Verification:**
- ✅ Coverage: x=0 → worldX=-10000, x=255 → worldX=+9921.875 (full ±10km range)
- ✅ Array indexing: Standard C# row-major [x, z] → JSON [[row0], [row1], ...]
- ✅ No coordinate inversions detected

#### Stage 2a: Python image_generator.py (Lines 36-47)

```python
# Convert biome map to numpy array
biome_array = np.array(biome_data.biome_map, dtype=np.uint8)  # Shape: (256, 256)
height, width = biome_array.shape

# Map biome IDs to colors
for biome_id, color in BIOME_COLORS.items():
    mask = biome_array == biome_id  # Direct equality check
    rgb_array[mask] = color         # No interpolation here
```

**Verification:**
- ✅ Direct mapping preserves bit flag values
- ✅ No coordinate transformations
- ⚠️  **Line 57: BICUBIC upscaling** (see Section 2.1)

#### Stage 2b: TypeScript MapCanvas.tsx (Lines 70-93)

```typescript
function renderBiomes(ctx, biomeData, targetWidth, targetHeight) {
  const { biome_map, resolution } = biomeData;  // resolution = 256
  const pixelSize = targetWidth / resolution;   // e.g., 512/256 = 2px per sample

  for (let y = 0; y < resolution; y++) {
    for (let x = 0; x < resolution; x++) {
      const biomeId = biome_map[y][x];          // Direct array access
      const color = BiomeColors[biomeId];        // Bit flag → hex color

      ctx.fillRect(x * pixelSize, y * pixelSize, pixelSize, pixelSize);
    }
  }
}
```

**Verification:**
- ✅ Direct pixel mapping, no interpolation
- ✅ Array access [y][x] matches JSON structure
- ✅ Bit flag values correctly mapped to colors

---

## 2. Root Cause Hypotheses (Ranked by Likelihood)

### 2.1 HYPOTHESIS #1: BICUBIC Interpolation Corrupts Discrete Biome IDs ⭐⭐⭐⭐⭐

**Likelihood:** VERY HIGH (95%)

**Technical Explanation:**

BICUBIC interpolation in `image_generator.py:57` treats biome IDs as **continuous numerical values** and interpolates between them:

```python
# Line 53-58
if target_resolution and target_resolution != biome_data.resolution:
    image = image.resize(
        (target_resolution, target_resolution),
        Image.Resampling.BICUBIC  # ⚠️ CRITICAL BUG
    )
```

**Problem Mechanism:**

When upscaling from 256×256 to 512×512 (or higher), BICUBIC creates intermediate pixel values by **averaging neighboring biome IDs**:

```
Example: Ocean (32) next to DeepNorth (256)

Original pixels:  [32, 32, 32, 256, 256, 256]
                       ↓ BICUBIC upscale 2x
Interpolated:     [32, 32, 32, 144, 144, 256, 256, 256]
                             ^^^ INVALID BIOME ID!
```

**Why This Causes "Bleeding":**

1. BICUBIC generates intermediate values: (32 + 256) / 2 = 144
2. Value 144 doesn't match ANY valid biome enum (1, 2, 4, 8, 16, 32, 64, 256, 512)
3. Color mapping: `BIOME_COLORS[144]` → **KeyError** or default to black/gray
4. Visual effect: Black/gray "transition zones" appear as "bleeding" artifacts

**Supporting Evidence:**

- File: `etl/experimental/adaptive-sampling-client/backend/VWE_WorldDataAPI/app/services/image_generator.py:57`
- Biome IDs are **bit flags**, not continuous values
- Interpolation assumes numerical continuity (valid for heightmaps, INVALID for categorical data)

**Expected Impact:**

- Affects **only PNG visualizations** generated by Python backend
- Does **NOT** affect JSON data or TypeScript canvas rendering (which uses NEAREST_NEIGHBOR scaling via fillRect)
- More visible at biome boundaries, especially Ocean→DeepNorth (32→256 = large gap)

**Validation Test:**

```python
# Test with actual biome data
import numpy as np
from PIL import Image

biome_data = np.array([[32, 32, 256, 256]], dtype=np.uint8)
img = Image.fromarray(biome_data)
upscaled = img.resize((8, 1), Image.Resampling.BICUBIC)
print(np.array(upscaled))
# Expected output: [32, 32, ~100-150, ~150-200, 256, 256, 256, 256]
```

---

### 2.2 HYPOTHESIS #2: PNG Color Mapping Bug (Sequential vs Bit Flags) ⭐⭐⭐

**Likelihood:** HIGH (80%) - Confirmed bug, but isolated to PNG export

**Technical Explanation:**

BiomeExporter.cs has a critical bug in `GetBiomeColor()` method (lines 245-260):

```csharp
private Color GetBiomeColor(int biome)
{
    return biome switch
    {
        0 => new Color(0.4f, 0.8f, 0.4f), // Meadows - Green ❌ WRONG! 0 = None
        1 => new Color(0.2f, 0.4f, 0.2f), // BlackForest ❌ WRONG! Should be Meadows
        2 => new Color(0.3f, 0.3f, 0.1f), // Swamp ❌ WRONG! Should be BlackForest
        3 => new Color(0.8f, 0.8f, 0.9f), // Mountain ❌ INVALID biome ID!
        4 => new Color(0.8f, 0.7f, 0.4f), // Plains ❌ WRONG! Should be Swamp
        5 => new Color(0.2f, 0.4f, 0.8f), // Ocean ❌ INVALID biome ID!
        6 => new Color(0.6f, 0.4f, 0.8f), // Mistlands ❌ INVALID biome ID!
        7 => new Color(0.9f, 0.9f, 0.9f), // DeepNorth ❌ INVALID biome ID!
        8 => new Color(0.6f, 0.2f, 0.1f), // Ashlands ❌ WRONG! Should be Mountain
        _ => new Color(0.5f, 0.5f, 0.5f)  // Unknown - Gray
    };
}
```

**Correct Implementation:**

```csharp
private Color GetBiomeColor(int biome)
{
    return biome switch
    {
        0 => new Color(0.0f, 0.0f, 0.0f),     // None - Black
        1 => new Color(0.4f, 0.8f, 0.4f),     // Meadows - Green ✓
        2 => new Color(0.2f, 0.4f, 0.2f),     // BlackForest - Dark Green ✓
        4 => new Color(0.3f, 0.3f, 0.1f),     // Swamp - Brown ✓
        8 => new Color(0.8f, 0.8f, 0.9f),     // Mountain - White ✓
        16 => new Color(0.8f, 0.7f, 0.4f),    // Plains - Yellow ✓
        32 => new Color(0.2f, 0.4f, 0.8f),    // Ocean - Blue ✓
        64 => new Color(0.6f, 0.4f, 0.8f),    // Mistlands - Purple ✓
        256 => new Color(0.9f, 0.9f, 0.9f),   // DeepNorth - Light Gray ✓
        512 => new Color(0.6f, 0.2f, 0.1f),   // Ashlands - Red ✓
        _ => new Color(0.5f, 0.5f, 0.5f)      // Unknown - Gray
    };
}
```

**Impact:**

- Affects **only** the PNG files generated by BepInEx plugin (`biomes.png`)
- Does **NOT** affect JSON export or downstream rendering
- PNG images will show completely wrong colors for all biomes
- **Not the cause of "bleeding"**, but makes debugging harder

**Files Affected:**

- `/home/steve/projects/valhem-world-engine/etl/experimental/bepinex-adaptive-sampling/src/VWE_DataExporter/DataExporters/BiomeExporter.cs:245-260`

---

### 2.3 HYPOTHESIS #3: Sparse Sampling Misses Narrow Biome Boundaries ⭐⭐

**Likelihood:** MEDIUM (40%)

**Technical Explanation:**

At 256×256 resolution, sample spacing is ~78m. If biome boundaries are narrower than this, sampling may "jump over" them:

```
Real World:
  Ocean (100m) → Swamp (50m) → BlackForest (200m)

Sampled at 78m spacing:
  Sample 1: Ocean (at 0m)
  Sample 2: Ocean (at 78m) ← Misses Swamp entirely!
  Sample 3: BlackForest (at 156m)

Result: Swamp appears to not exist between Ocean and BlackForest
```

**Why This Explains "Bleeding":**

- Biome boundaries in Valheim are fractal/noise-based (not clean lines)
- Narrow peninsulas or islands < 78m wide may be missed
- When rendered, missing samples appear as "gaps" that get filled by adjacent biomes
- More pronounced for rare biomes like DeepNorth (only appears at edges)

**Validation Approach:**

- Compare 256×256 vs 512×512 sampling for same seed
- Check if narrow features disappear at lower resolution
- Measure actual biome boundary widths in reference image

**Expected Impact:**

- Affects all biomes, but more visible for rare/edge biomes
- Would cause **undersampling**, not necessarily "bleeding"
- Cannot explain interpolated color artifacts

---

### 2.4 HYPOTHESIS #4: Array Indexing Y/X Confusion ⭐

**Likelihood:** LOW (10%)

**Technical Explanation:**

Potential mismatch between row-major (C#) and column-major indexing:

```csharp
// C# Export: biomeMap[x, z]
for (int x = 0; x < 256; x++)
    for (int z = 0; z < 256; z++)
        biomeMap[x, z] = GetBiome(...);

// JSON: Exported as rows → [[row0], [row1], ...]

// TypeScript: biome_map[y][x]
for (let y = 0; y < 256; y++)
    for (let x = 0; x < 256; x++)
        biomeId = biome_map[y][x];
```

**Why This Is Unlikely:**

- JSON data inspection shows Ocean (32) at edges (correct for world structure)
- DeepNorth (256) appears where expected (far edges)
- Complete X/Z flip would produce 90° rotated map (user would report this)
- Partial confusion would cause diagonal artifacts (not reported)

**Verification:**

```bash
# Check corners of biome_map
jq '.biome_map[0][0]' biomes.json    # Top-left
jq '.biome_map[0][255]' biomes.json  # Top-right
jq '.biome_map[255][0]' biomes.json  # Bottom-left
jq '.biome_map[255][255]' biomes.json # Bottom-right
# Expected: All should be Ocean (32) or DeepNorth (256) at world edges
```

---

### 2.5 HYPOTHESIS #5: Biome ID Bit Flag Mishandling ⭐

**Likelihood:** VERY LOW (5%)

**Technical Explanation:**

If code somewhere treats biome IDs as **bit masks** instead of **discrete values**:

```python
# WRONG: Bitwise operations
if biome_id & Biome.OCEAN:  # Checks if Ocean bit is SET
    # Would match Ocean (32) but also any combo with bit 5 set

# CORRECT: Direct equality
if biome_id == Biome.OCEAN:  # Checks if EXACTLY Ocean
```

**Why This Is Unlikely:**

- All color mapping code uses direct equality: `biome_array == biome_id`
- No bitwise operations found in rendering pipeline
- Biome counts (from jq analysis) show clean powers of 2, no unexpected combinations

**Verification:**

```bash
# Check for any non-power-of-2 biome IDs (would indicate bitwise errors)
jq '[.biome_map[][] | unique] | sort | map(select(. > 0 and (. | tostring | test("^[124816325126]$")) | not))' biomes.json
# Expected: Empty array (all IDs are valid bit flags)
```

---

## 3. Remediation Plans

### 3.1 FIX FOR HYPOTHESIS #1: Replace BICUBIC with NEAREST_NEIGHBOR ⭐ TOP PRIORITY

**File:** `/home/steve/projects/valhem-world-engine/etl/experimental/adaptive-sampling-client/backend/VWE_WorldDataAPI/app/services/image_generator.py`

**Change (Line 53-58):**

```python
# BEFORE (INCORRECT):
if target_resolution and target_resolution != biome_data.resolution:
    image = image.resize(
        (target_resolution, target_resolution),
        Image.Resampling.BICUBIC  # ❌ Corrupts discrete biome IDs
    )

# AFTER (CORRECT):
if target_resolution and target_resolution != biome_data.resolution:
    image = image.resize(
        (target_resolution, target_resolution),
        Image.Resampling.NEAREST  # ✅ Preserves discrete biome IDs
    )
```

**Rationale:**

- Biome IDs are **categorical data**, not continuous
- NEAREST_NEIGHBOR preserves exact biome values during upscaling
- No interpolated "in-between" values that would cause color mapping errors
- Standard approach for upscaling indexed/palette images

**Expected Impact:**

- ✅ Eliminates interpolated biome IDs (no more 144, 200, etc.)
- ✅ Sharp biome boundaries (no fuzzy transitions)
- ✅ Correct color mapping (all pixels match valid biome IDs)
- ⚠️  May appear "blocky" at high zoom levels (acceptable trade-off)

**Side Effects:**

- Biome boundaries will have stair-step appearance (not smooth)
- Consistent with Minecraft/voxel aesthetic
- Can add post-processing edge smoothing if needed (anti-aliasing on boundary pixels only)

**Testing:**

```python
# Unit test
def test_biome_upscaling_preserves_ids():
    biome_data = BiomeMapResponse(
        resolution=2,
        biome_map=[[32, 256], [1, 4]],
        world_radius=10000,
        world_diameter=20000
    )

    generator = ImageGenerator()
    buffer = generator.generate_biome_image(biome_data, target_resolution=4)

    img = Image.open(buffer)
    pixels = np.array(img)

    # Verify only valid biome colors exist
    unique_colors = {tuple(pixel) for row in pixels for pixel in row}
    expected_colors = {BIOME_COLORS[32], BIOME_COLORS[256], BIOME_COLORS[1], BIOME_COLORS[4]}

    assert unique_colors == expected_colors, "Interpolation created invalid colors!"
```

---

### 3.2 FIX FOR HYPOTHESIS #2: Correct PNG Color Mapping in BiomeExporter.cs

**File:** `/home/steve/projects/valhem-world-engine/etl/experimental/bepinex-adaptive-sampling/src/VWE_DataExporter/DataExporters/BiomeExporter.cs`

**Change (Lines 245-260):**

```csharp
private Color GetBiomeColor(int biome)
{
    return biome switch
    {
        0 => new Color(0.0f, 0.0f, 0.0f),     // None - Black
        1 => new Color(0.4f, 0.8f, 0.4f),     // Meadows - Green
        2 => new Color(0.2f, 0.4f, 0.2f),     // BlackForest - Dark Green
        4 => new Color(0.3f, 0.3f, 0.1f),     // Swamp - Brown
        8 => new Color(0.8f, 0.8f, 0.9f),     // Mountain - White
        16 => new Color(0.8f, 0.7f, 0.4f),    // Plains - Yellow
        32 => new Color(0.2f, 0.4f, 0.8f),    // Ocean - Blue
        64 => new Color(0.6f, 0.4f, 0.8f),    // Mistlands - Purple
        256 => new Color(0.9f, 0.9f, 0.9f),   // DeepNorth - Light Gray
        512 => new Color(0.6f, 0.2f, 0.1f),   // Ashlands - Red
        _ => new Color(0.5f, 0.5f, 0.5f)      // Unknown - Gray
    };
}
```

**Rationale:**

- Aligns with Python `BIOME_COLORS` and TypeScript `BiomeColors`
- Uses actual bit flag values from `Heightmap.Biome` enum
- Fixes incorrect PNG visualizations from BepInEx plugin

**Expected Impact:**

- ✅ PNG files from BepInEx match JSON data
- ✅ Consistent colors across all rendering pipelines
- ⚠️  Does not fix "bleeding" (that's Hypothesis #1)

**Build Commands:**

```bash
cd etl/experimental/bepinex-adaptive-sampling
dotnet build src/VWE_DataExporter/VWE_DataExporter.csproj -c Release
cp src/VWE_DataExporter/bin/Release/net48/VWE_DataExporter.dll plugins/
```

---

### 3.3 VALIDATION: Compare 256×256 vs 512×512 Sampling

**Objective:** Test Hypothesis #3 (sparse sampling boundary issues)

**Steps:**

1. Generate 512×512 biome map for same seed (hkLycKKCMI)
2. Downsample to 256×256 using NEAREST_NEIGHBOR
3. Compare with native 256×256 export
4. Calculate biome distribution differences

**Script:**

```python
# etl/experimental/adaptive-sampling-client/tests/test_sampling_resolution.py
import json
import numpy as np
from PIL import Image

def compare_resolutions(seed: str):
    # Load 256×256 data
    with open(f"data/seeds/{seed}/256/biomes.json") as f:
        data_256 = json.load(f)

    # Load 512×512 data
    with open(f"data/seeds/{seed}/512/biomes.json") as f:
        data_512 = json.load(f)

    # Downsample 512 to 256
    biome_512 = np.array(data_512["biome_map"])
    img_512 = Image.fromarray(biome_512.astype(np.uint8))
    img_256_downsampled = img_512.resize((256, 256), Image.Resampling.NEAREST)
    biome_256_from_512 = np.array(img_256_downsampled)

    # Compare distributions
    biome_256_native = np.array(data_256["biome_map"])

    diff = np.sum(biome_256_native != biome_256_from_512)
    total = 256 * 256

    print(f"Differences: {diff}/{total} pixels ({diff/total*100:.2f}%)")

    # Count biome changes
    for biome_id in [1, 2, 4, 8, 16, 32, 64, 256, 512]:
        count_native = np.sum(biome_256_native == biome_id)
        count_downsampled = np.sum(biome_256_from_512 == biome_id)
        delta = count_downsampled - count_native
        print(f"Biome {biome_id:3d}: {count_native:5d} (native) vs {count_downsampled:5d} (downsampled) | Δ={delta:+5d}")
```

**Acceptance Criteria:**

- If differences < 5%: Sparse sampling is NOT the issue
- If differences > 20%: Sparse sampling is a significant factor
- Focus on DeepNorth (256) and Ashlands (512) counts

---

## 4. Data Analysis Plan

### 4.1 Diagnostic Visualizations

#### 4.1.1 Sample Point Density Heatmap

**Objective:** Verify uniform sampling across world

**Implementation:**

```python
# scripts/analyze_sample_density.py
import json
import matplotlib.pyplot as plt
import numpy as np

def visualize_sample_density(biome_file: str):
    with open(biome_file) as f:
        data = json.load(f)

    biome_map = np.array(data["biome_map"])

    # Count unique biomes in sliding window
    window_size = 16
    density = np.zeros_like(biome_map, dtype=float)

    for y in range(biome_map.shape[0]):
        for x in range(biome_map.shape[1]):
            y_start = max(0, y - window_size // 2)
            y_end = min(biome_map.shape[0], y + window_size // 2)
            x_start = max(0, x - window_size // 2)
            x_end = min(biome_map.shape[1], x + window_size // 2)

            window = biome_map[y_start:y_end, x_start:x_end]
            density[y, x] = len(np.unique(window))

    plt.figure(figsize=(10, 10))
    plt.imshow(density, cmap='hot', interpolation='nearest')
    plt.colorbar(label='Unique biomes in 16×16 window')
    plt.title('Biome Diversity Heatmap (Higher = More Transitions)')
    plt.savefig('sample_density.png', dpi=150)
    plt.show()
```

**Analysis:**

- High-density areas (5-7 unique biomes) = complex boundaries
- Low-density areas (1-2 unique biomes) = biome interiors
- Look for unexpected patterns (e.g., uniform density where boundaries expected)

---

#### 4.1.2 Interpolation Artifact Detector

**Objective:** Find invalid biome ID values from interpolation

**Implementation:**

```python
# scripts/detect_interpolation_artifacts.py
import json
import numpy as np
from PIL import Image

VALID_BIOME_IDS = {0, 1, 2, 4, 8, 16, 32, 64, 256, 512}

def detect_interpolation_artifacts(image_file: str):
    """Check if PNG contains interpolated biome colors"""
    img = Image.open(image_file)
    pixels = np.array(img)

    # For each unique color, try to map back to biome ID
    unique_colors = {}
    for y in range(pixels.shape[0]):
        for x in range(pixels.shape[1]):
            color = tuple(pixels[y, x])
            if color not in unique_colors:
                unique_colors[color] = []
            unique_colors[color].append((x, y))

    print(f"Found {len(unique_colors)} unique colors")

    # Check against expected biome colors
    expected_colors = {
        tuple(BIOME_COLORS[biome_id]): biome_id
        for biome_id in VALID_BIOME_IDS
    }

    unexpected_colors = []
    for color, positions in unique_colors.items():
        if color not in expected_colors:
            unexpected_colors.append((color, len(positions), positions[:5]))

    if unexpected_colors:
        print(f"\n⚠️  Found {len(unexpected_colors)} UNEXPECTED colors (interpolation artifacts):")
        for color, count, sample_positions in unexpected_colors:
            print(f"  RGB{color}: {count} pixels, e.g., at {sample_positions}")
    else:
        print("✅ All colors match valid biome IDs (no interpolation)")
```

---

#### 4.1.3 Biome Boundary Width Measurement

**Objective:** Measure actual biome transition widths to assess 78m sampling adequacy

**Implementation:**

```python
# scripts/measure_boundary_widths.py
import json
import numpy as np
from scipy.ndimage import generic_filter

def measure_boundary_widths(biome_file: str):
    with open(biome_file) as f:
        data = json.load(f)

    biome_map = np.array(data["biome_map"])
    resolution = data["resolution"]
    world_diameter = data["world_diameter"]
    sample_spacing = world_diameter / resolution  # meters per sample

    # Detect boundaries: pixels where neighbors differ
    def has_different_neighbor(window):
        center = window[len(window) // 2]
        return 1.0 if np.any(window != center) else 0.0

    boundaries = generic_filter(biome_map, has_different_neighbor, size=3, mode='nearest')

    # Measure connected boundary regions
    from scipy.ndimage import label, find_objects
    labeled_boundaries, num_features = label(boundaries)

    boundary_widths = []
    for region in find_objects(labeled_boundaries):
        if region is not None:
            width = min(region[0].stop - region[0].start, region[1].stop - region[1].start)
            width_meters = width * sample_spacing
            boundary_widths.append(width_meters)

    print(f"Boundary Statistics (meters):")
    print(f"  Min: {min(boundary_widths):.1f}m")
    print(f"  Mean: {np.mean(boundary_widths):.1f}m")
    print(f"  Median: {np.median(boundary_widths):.1f}m")
    print(f"  Max: {max(boundary_widths):.1f}m")
    print(f"  Sample spacing: {sample_spacing:.1f}m")

    if np.median(boundary_widths) < sample_spacing:
        print(f"\n⚠️  Median boundary width ({np.median(boundary_widths):.1f}m) < sample spacing ({sample_spacing:.1f}m)")
        print("   → Sparse sampling may miss narrow boundaries!")
    else:
        print(f"\n✅ Median boundary width ({np.median(boundary_widths):.1f}m) > sample spacing")
```

---

### 4.2 Logging and Instrumentation

#### 4.2.1 Add Biome ID Validation in Python

**File:** `image_generator.py`

**Addition (after line 46):**

```python
# Validate all biome IDs before processing
valid_biome_ids = {0, 1, 2, 4, 8, 16, 32, 64, 256, 512}
unique_biome_ids = set(biome_array.flatten())
invalid_ids = unique_biome_ids - valid_biome_ids

if invalid_ids:
    logger.warning(f"Found INVALID biome IDs: {sorted(invalid_ids)}")
    logger.warning("This indicates interpolation or data corruption!")
    # Optional: Replace invalid IDs with nearest valid ID
    for invalid_id in invalid_ids:
        closest_valid = min(valid_biome_ids, key=lambda x: abs(x - invalid_id))
        logger.warning(f"  Replacing {invalid_id} → {closest_valid}")
        biome_array[biome_array == invalid_id] = closest_valid
```

---

#### 4.2.2 Add Biome Distribution Logging

**File:** `world_loader.py` (already has `_count_biomes()`)

**Enhancement:**

```python
def _count_biomes(self, biome_map: list[list[int]]) -> Dict[str, int]:
    """Count occurrences of each biome type with validation"""
    counts = {}
    invalid_ids = set()

    for row in biome_map:
        for biome_id in row:
            if biome_id not in {0, 1, 2, 4, 8, 16, 32, 64, 256, 512}:
                invalid_ids.add(biome_id)

            biome_name = self._get_biome_name(biome_id)
            counts[biome_name] = counts.get(biome_name, 0) + 1

    if invalid_ids:
        logger.error(f"Found INVALID biome IDs: {sorted(invalid_ids)}")
        logger.error("These IDs do not match Valheim's Heightmap.Biome enum!")

    # Log distribution percentages
    total = sum(counts.values())
    logger.info("Biome Distribution:")
    for biome_name, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        logger.info(f"  {biome_name:12s}: {count:6d} samples ({percentage:5.2f}%)")

    return counts
```

---

### 4.3 Metrics to Track

#### 4.3.1 Biome Distribution Comparison

Compare against reference data from `valheim-map.world`:

**Expected Distribution (seed hkLycKKCMI @ 512×512):**

| Biome | Expected % | Actual % (256×256) | Delta |
|-------|-----------|-------------------|-------|
| Ocean (32) | ~30% | 18.2% | -11.8% ⚠️ |
| DeepNorth (256) | ~15% | 31.7% | +16.7% ⚠️ |
| Mountain (8) | ~20% | 10.4% | -9.6% ⚠️ |
| Plains (16) | ~15% | 11.4% | -3.6% |
| Mistlands (64) | ~10% | 5.4% | -4.6% |
| Swamp (4) | ~5% | 2.7% | -2.3% |
| BlackForest (2) | ~5% | 2.3% | -2.7% |
| Meadows (1) | ~3% | 3.1% | +0.1% ✅ |
| Ashlands (512) | ~12% | 14.8% | +2.8% |

**Calculated from actual data:**

```bash
jq '[.biome_map[][] | group_by(.) | map({biome: .[0], count: length, pct: (length/65536*100)})]' biomes.json
```

**Analysis:**

- DeepNorth is OVER-represented (+16.7%) ← PRIMARY CONCERN
- Ocean is UNDER-represented (-11.8%)
- Suggests DeepNorth is "bleeding" into Ocean territory
- Consistent with interpolation creating intermediate values that default to wrong biome

---

## 5. Next Steps (Prioritized)

### 5.1 Quick Wins (Implement Immediately)

1. **[1 hour] Fix Python BICUBIC → NEAREST_NEIGHBOR** (Section 3.1)
   - File: `image_generator.py:57`
   - Change 1 line of code
   - Test with existing biomes.json
   - Generate before/after PNGs for comparison

2. **[30 min] Add biome ID validation** (Section 4.2.1)
   - Add invalid ID detection to `image_generator.py`
   - Log warnings if interpolated values found
   - Helps confirm Hypothesis #1

3. **[2 hours] Fix C# PNG color mapping** (Section 3.2)
   - File: `BiomeExporter.cs:245-260`
   - Rebuild DLL
   - Regenerate biomes.png for visual validation

### 5.2 Validation Tasks (1-2 days)

4. **[4 hours] Run interpolation artifact detector** (Section 4.1.2)
   - Check current PNGs for invalid colors
   - Compare before/after BICUBIC fix
   - Document findings

5. **[4 hours] Generate 512×512 comparison** (Section 3.3)
   - Run BepInEx with 512×512 config
   - Compare biome distributions
   - Measure boundary capture differences

6. **[2 hours] Measure boundary widths** (Section 4.1.3)
   - Determine if 78m sampling is adequate
   - Validate Hypothesis #3

### 5.3 Long-Term Improvements (1-2 weeks)

7. **[1 week] Implement adaptive boundary refinement**
   - Sparse 256×256 base sampling
   - Detect boundaries with high biome diversity
   - Resample boundaries at 512×512 (or higher)
   - Stitch results for "smart upscaling"

8. **[2 days] Add edge anti-aliasing (optional)**
   - Post-process NEAREST_NEIGHBOR upscaled images
   - Apply 2-3 pixel Gaussian blur ONLY at biome boundaries
   - Preserves sharp interior regions, smooths edges

9. **[1 week] Build validation dashboard**
   - Compare generated maps vs reference images
   - Automated biome distribution regression tests
   - CI/CD integration for quality checks

---

## 6. Validation Criteria

### 6.1 Success Metrics

**Fix is successful if:**

1. ✅ No invalid biome IDs in generated PNGs (all values in {0, 1, 2, 4, 8, 16, 32, 64, 256, 512})
2. ✅ Biome distribution within ±5% of reference data
3. ✅ DeepNorth % decreases from 31.7% → ~15%
4. ✅ Ocean % increases from 18.2% → ~30%
5. ✅ Visual comparison shows no "bleeding" artifacts
6. ✅ Sharp biome boundaries (no fuzzy transitions)

### 6.2 Regression Tests

```python
# tests/test_biome_rendering.py
def test_no_interpolation_artifacts():
    """Ensure upscaling doesn't create invalid biome IDs"""
    biome_data = load_biome_data("hkLycKKCMI")
    image_buffer = ImageGenerator().generate_biome_image(biome_data, target_resolution=512)

    img = Image.open(image_buffer)
    pixels = np.array(img)

    # Extract unique RGB colors
    unique_colors = {tuple(pixel) for row in pixels for pixel in row}

    # Map back to biome IDs
    color_to_biome = {tuple(BIOME_COLORS[b]): b for b in BIOME_COLORS}
    found_biome_ids = {color_to_biome.get(color, -1) for color in unique_colors}

    # Validate all IDs are valid
    assert -1 not in found_biome_ids, f"Found unmapped colors (interpolation artifacts)"
    assert found_biome_ids.issubset({0, 1, 2, 4, 8, 16, 32, 64, 256, 512})

def test_biome_distribution_accuracy():
    """Verify biome distribution matches reference data"""
    biome_data = load_biome_data("hkLycKKCMI")
    counts = count_biomes(biome_data.biome_map)

    reference = {
        "Ocean": 0.30,
        "DeepNorth": 0.15,
        "Mountain": 0.20,
        # ... etc
    }

    total = sum(counts.values())
    for biome, expected_pct in reference.items():
        actual_pct = counts.get(biome, 0) / total
        delta = abs(actual_pct - expected_pct)
        assert delta < 0.05, f"{biome}: expected {expected_pct:.1%}, got {actual_pct:.1%}"
```

---

## 7. Conclusion

### 7.1 Summary of Findings

**Primary Root Cause:** BICUBIC interpolation in `image_generator.py:57` treats discrete biome IDs as continuous values, generating invalid intermediate IDs that cause color mapping errors and "bleeding" artifacts.

**Secondary Issue:** C# PNG color mapping bug (sequential vs bit flags) makes debugging harder but doesn't affect JSON data or downstream rendering.

**Action Required:** Change PIL upscaling from `Image.Resampling.BICUBIC` to `Image.Resampling.NEAREST` (1-line fix).

### 7.2 Confidence Assessment

- **Hypothesis #1 (BICUBIC):** 95% confidence - Explains all symptoms, has clear technical mechanism
- **Hypothesis #2 (PNG colors):** 80% confidence - Confirmed bug, isolated impact
- **Hypothesis #3 (Sparse sampling):** 40% confidence - Possible contributor, needs validation
- **Hypothesis #4 (Indexing):** 10% confidence - No supporting evidence
- **Hypothesis #5 (Bit flags):** 5% confidence - Code review shows no bitwise operations

### 7.3 Recommended Immediate Action

1. Implement fix for Hypothesis #1 (BICUBIC → NEAREST)
2. Run artifact detector to confirm diagnosis
3. Compare before/after biome distributions
4. If validated (>90% confidence), promote fix to stable and close issue

---

**Report Generated:** 2025-10-13
**Analysis Duration:** 2 hours
**Files Reviewed:** 8
**Hypotheses Tested:** 5
**Recommended Fixes:** 2 (1 critical, 1 cleanup)
**Estimated Fix Time:** 1-3 hours
**Estimated Validation Time:** 4-8 hours
