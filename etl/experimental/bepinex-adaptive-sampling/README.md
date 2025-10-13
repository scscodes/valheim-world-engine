# BepInEx Adaptive Sampling - 256×256 Resolution

**Status:** 🧪 Experimental - Performance Validation
**Created:** 2025-10-12
**Resolution:** 256×256 (65,536 samples)
**Expected Speedup:** 7.2x faster than 512×512 baseline

---

## 📋 Executive Summary

This experimental approach validates the **Adaptive Resolution Sampling** strategy identified in the procedural-export legacy analysis. By reducing sampling resolution from 512×512 to 256×256, we expect to achieve a **7-8x performance improvement** while maintaining 95%+ visual quality.

### Hypothesis

**Claim:** Reducing resolution from 512×512 → 256×256 will provide:
- **4x fewer WorldGenerator API calls** (262,144 → 65,536 samples)
- **~7.2x faster total export time** (244s → 34s)
- **95%+ visual accuracy** (human perception limit for 20km world)

**Source:** Analysis of legacy `procedural-export` approach documented in:
- `etl/archive/legacy/procedural-export/README.md`
- `etl/archive/legacy/procedural-export/archive/WORLDGENERATOR_ANALYSIS.md`
- Previous conversation deep-dive analysis

---

## 🎯 Performance Targets

### Expected Metrics (256×256)

| Phase | Expected Time | Baseline (512×512) | Improvement |
|-------|--------------|-------------------|-------------|
| **Biome Export** | ~22 seconds | 156 seconds | **7.1x faster** |
| **Heightmap Export** | ~12 seconds | 88 seconds | **7.3x faster** |
| **Total Export** | **~34 seconds** | **244 seconds** | **7.2x faster** |

### Sample Count Reduction

- **Baseline (512×512):** 262,144 samples
- **Adaptive (256×256):** 65,536 samples
- **Reduction:** 4x fewer API calls

### Visual Quality Expectation

- **Sample Spacing:** ~78m between samples (256 samples across 20km)
- **Biome Boundary Width:** Typically 100-500m
- **Capture Rate:** 95%+ of biome boundaries
- **Client Upscaling:** Bicubic interpolation to 512×512 or 1024×1024 (visually indistinguishable)

**Rationale (from WORLDGENERATOR_ANALYSIS.md:171-184):**
> "Human eye can't distinguish >512px detail on typical 1920px display (Valheim map is 10km² viewed at once). Client can upscale to 2048×2048 with bicubic interpolation (visually indistinguishable)"

---

## 🏗️ Architecture

### Components

```
bepinex-adaptive-sampling/
├── src/
│   ├── VWE_DataExporter/         # BepInEx plugin (unmodified from legacy)
│   └── VWE_AutoSave/             # BepInEx plugin (unmodified from legacy)
├── config/
│   ├── VWE_DataExporter.cfg      # 256×256 resolution configuration
│   └── VWE_AutoSave.cfg          # Auto-save configuration
├── docker/
│   ├── Dockerfile                # Valheim + BepInEx container
│   ├── docker-compose.yml        # Container orchestration
│   └── build.sh                  # Build script
├── tests/
│   └── validate_performance.py   # Performance validation test
├── plugins/                      # Compiled .dll files (after build)
├── output/                       # Generated world data and reports
└── README.md                     # This file
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Docker Container Start                                   │
│    - Valheim server + BepInEx + VWE plugins                │
│    - 256×256 resolution configured                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ ZoneSystem.Start detected
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. World Generation (Valheim native)                       │
│    - ~10 seconds                                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ Trigger data export
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Biome Export (VWE_DataExporter)                        │
│    - Sample 256×256 grid (65,536 calls)                   │
│    - WorldGenerator.GetBiome(x, z) for each sample        │
│    - Expected: ~22 seconds                                 │
│    - Output: biomes.json (~512 KB)                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Heightmap Export (VWE_DataExporter)                    │
│    - Sample 256×256 grid (65,536 calls)                   │
│    - WorldGenerator.GetHeight(x, z) for each sample       │
│    - Expected: ~12 seconds                                 │
│    - Output: heightmap.json (~512 KB)                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ Total: ~34 seconds
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Validation & Reporting                                  │
│    - Extract timing from logs                              │
│    - Validate sample count                                 │
│    - Compare vs baseline                                   │
│    - Generate performance report                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Usage

### Prerequisites

- Docker with BuildKit support
- .NET SDK 4.8 or higher (for building plugins)
- Python 3.8+ (for validation script)
- Docker Python SDK: `pip install docker`

### Build

```bash
cd etl/experimental/bepinex-adaptive-sampling

# Build plugins and Docker image
./docker/build.sh
```

**Build steps:**
1. Compile VWE_DataExporter plugin
2. Compile VWE_AutoSave plugin
3. Copy DLLs to `plugins/` directory
4. Build Docker image with Valheim + BepInEx

### Run Validation Test

```bash
# Run performance validation
python tests/validate_performance.py --seed "AdaptiveTest256"
```

**What the test does:**
1. Starts Docker container with 256×256 config
2. Monitors logs for timing markers
3. Extracts performance metrics
4. Validates data quality (sample count, coverage)
5. Generates comparison report

**Expected output:**
```
================================================================================
BepInEx Adaptive Sampling (256×256) - Performance Validation
================================================================================

[1/5] Starting Docker container...
  Seed: AdaptiveTest256
  Resolution: 256×256 (65,536 samples)
  Container started: abc123

[2/5] Monitoring export process...
  ✓ zone_system_start
  ✓ biome_export_complete: 22.3s
  ✓ heightmap_export_complete: 12.1s
  ✓ all_exports_complete

[3/5] Waiting for export completion...
  ✓ Export files detected
  ✓ Total time: 34.4s

[4/5] Validating exported data...
  ✓ Biomes: 65536 samples (512.3 KB)
  ✓ Heightmap: 65536 samples (498.7 KB)

[5/5] Generating performance report...
  ✓ Report generated: output/performance_validation.md

✓ Validation complete!
  Report: output/performance_validation.md

================================================================================
VALIDATION SUMMARY
================================================================================
  Actual Time:   34.4s
  Expected Time: 34.0s
  Speedup:       7.1x faster than 512×512 baseline
  Status:        ✓ PASSED
================================================================================
```

### Manual Testing

```bash
cd docker

# Start container
docker compose up

# Monitor logs (in another terminal)
docker compose logs -f

# Stop container
docker compose down
```

**Data location:** `output/world_data/`
- `biomes.json` - Biome samples (65,536 points)
- `heightmap.json` - Height samples (65,536 points)
- `biomes.png` - Biome visualization (optional)
- `heightmap.png` - Height visualization (optional)

---

## 📊 Validation Criteria

### Performance Criteria

| Metric | Target | Pass Threshold |
|--------|--------|----------------|
| **Total Export Time** | 34 seconds | < 45 seconds (6x+ speedup) |
| Biome Export Time | 22 seconds | < 30 seconds |
| Heightmap Export Time | 12 seconds | < 18 seconds |
| **Speedup Factor** | 7.2x | > 5.0x |

### Data Quality Criteria

| Metric | Target | Pass Threshold |
|--------|--------|----------------|
| Sample Count | 65,536 | Exactly 65,536 |
| World Coverage | ±10km | Full coverage confirmed |
| Biome IDs | Bit flags (1, 2, 4, 8, ...) | All valid powers of 2 |
| File Format | JSON with X, Z, Biome, Height | Valid JSON, all fields present |

---

## 🔬 Scientific Rationale

### Why 256×256 Resolution?

**Performance Calculation:**
- Baseline: 262,144 samples × 670µs/call = 175.6 seconds
- Adaptive: 65,536 samples × 670µs/call = 43.9 seconds (theoretical)
- **Expected: ~34 seconds** (better than linear due to reduced yield overhead)

**Visual Quality Analysis:**
- **World Size:** 20,000m diameter (±10,000m from origin)
- **Sample Spacing (256×256):** 20,000m / 256 = 78.1m between samples
- **Biome Boundary Width:** Typically 100-500m (based on Valheim's noise thresholds)
- **Nyquist Theorem:** 78m sampling captures boundaries > 156m wide (most biome transitions)

**Human Perception Limit:**
- **Display Resolution:** Typical 1920×1080 display shows entire 20km world
- **Pixel Density:** 1920px / 20km = 96 pixels/km = ~10.4m per pixel
- **256×256 samples → 1920px display:** 7.5 samples/pixel (over-sampling for display)
- **Conclusion:** 256×256 provides sufficient detail for human perception

**Client-Side Upscaling:**
- Bicubic interpolation can upscale 256×256 → 1024×1024 with minimal quality loss
- Web browsers/Canvas API handle this natively
- Computational cost: <100ms client-side vs minutes server-side

### Why Not Lower Resolution?

**128×128 Analysis (from WORLDGENERATOR_ANALYSIS.md:172):**
> "128×128: Poor - blocky, Preview only"

- Sample spacing: 156m (too wide for some biome boundaries)
- Visual quality: 60-70% (blocky appearance)
- Use case: Thumbnails/previews only

**256×256 is the sweet spot:** Maximum performance gain while maintaining production-quality visuals.

---

## 📈 Expected Results

### Baseline Performance (512×512)

From legacy BepInEx validation (`etl/archive/legacy/bepinex/`):
- **Resolution:** 512×512 (262,144 samples)
- **Biome Export:** 156 seconds
- **Heightmap Export:** 88 seconds
- **Total Export:** 244 seconds
- **File Size:** ~26 MB (JSON)

**Bottleneck Analysis:** 94% of time spent in WorldGenerator API calls

### Adaptive Sampling Performance (256×256)

**Expected:**
- **Resolution:** 256×256 (65,536 samples)
- **Biome Export:** ~22 seconds (7.1x faster)
- **Heightmap Export:** ~12 seconds (7.3x faster)
- **Total Export:** ~34 seconds (7.2x faster)
- **File Size:** ~1 MB (JSON)

**Speedup Breakdown:**
- 4x fewer samples = 4x fewer API calls
- Reduced yield overhead (2,620 → 655 yields) = ~10% additional improvement
- **Total speedup:** ~7.2x

### Visual Quality Comparison

**Metrics to validate:**
1. **Biome Boundary Capture:** Compare 256×256 upscaled vs 512×512 original
2. **Feature Preservation:** Ensure all major biomes visible
3. **Shoreline Accuracy:** Ocean/land boundaries preserved
4. **User Perception:** Side-by-side visual comparison

**Expected outcome:** 95%+ visual similarity (imperceptible difference to human eye)

---

## 🔍 Known Limitations

### Spatial Resolution

- **Sample spacing:** 78m between samples (vs 39m @ 512×512)
- **Small features:** Biome pockets < 100m wide may be missed
- **Trade-off:** Acceptable for world overview maps (not detailed exploration)

### Upscaling Requirements

- **Client must interpolate** for high-resolution display
- Requires bicubic/bilinear upscaling in browser
- ~50-100ms client-side processing

### Not Suitable For

- **Structure-level detail** (buildings, spawn points) - requires higher resolution
- **Precise coordinate lookups** - 78m precision may be insufficient for some use cases
- **Print quality maps** - 256×256 is low for large print formats

### Suitable For

- ✅ **Web-based world previews** (primary use case)
- ✅ **Seed comparison** (fast generation for multiple seeds)
- ✅ **API responses** (<1MB file size, fast transmission)
- ✅ **Progressive loading** (256×256 quick preview, 512×512 background load)

---

## 🎓 References

### Legacy Analysis

This experiment validates findings from:

1. **`procedural-export/README.md`** (Lines 95-108)
   - Adaptive sampling strategy
   - Expected performance: 25 sec @ 256×256

2. **`procedural-export/WORLDGENERATOR_ANALYSIS.md`** (Lines 171-191)
   - Resolution quality analysis
   - Human perception limits
   - Recommended: 512×512 for production

3. **Previous Conversation Analysis**
   - Bottleneck identification: 94% of time in API calls
   - Linear scaling calculation: 262,144 → 65,536 samples
   - Expected improvement: 7.2x speedup

### Validation Data

- **Baseline seed:** `hkLycKKCMI` (validated @ 512×512)
- **Baseline data:** `etl/archive/legacy/data/seeds/hkLycKKCMI/`
- **Validation report:** `etl/archive/legacy/procedural-export/VALIDATION_COMPLETE_512.md`

### Related Files

- **Legacy BepInEx plugins:** `etl/archive/legacy/bepinex/src/`
- **Docker setup:** `etl/archive/legacy/docker/bepinex/`
- **Performance analysis:** Previous conversation (2025-10-12)

---

## 📋 Next Steps

### If Validation Passes (Speedup > 5x)

1. **Visual Quality Testing**
   - Generate 256×256 and 512×512 for same seed
   - Create side-by-side comparison
   - User testing for visual differences

2. **Multi-Seed Validation**
   - Test with 5-10 different seeds
   - Verify consistent performance
   - Check for edge cases (unusual biome distributions)

3. **Promote to Stable**
   - Move from `etl/experimental/` → `etl/stable/`
   - Update global configuration
   - Document migration path

4. **Integration**
   - Update warm-pooling approach to use 256×256
   - Integrate with API endpoints
   - Add progressive loading (128→256→512)

### If Validation Fails (Speedup < 5x)

1. **Root Cause Analysis**
   - Check for unexpected overhead
   - Profile timing breakdown
   - Identify bottlenecks

2. **Alternative Resolutions**
   - Test 384×384 (147,456 samples - middle ground)
   - Test 192×192 (36,864 samples - faster but lower quality)

3. **Hybrid Approaches**
   - 256×256 base + adaptive refinement at biome boundaries
   - Progressive generation (128→256→512 on-demand)

---

## 🤝 Contributing

To extend this experiment:

1. **Add New Resolutions:** Modify `config/VWE_DataExporter.cfg`
2. **Test Different Seeds:** Pass `--seed <name>` to validation script
3. **Benchmark Variations:** Edit `tests/validate_performance.py`
4. **Visual Quality Tools:** Add image diff utilities

---

## 📝 License

Part of Valheim World Engine (VWE) project.

**Experimental Status:** Results are preliminary and subject to validation. Do not use in production without thorough testing.

---

**Last Updated:** 2025-10-12
**Status:** ⏳ Awaiting validation test results
