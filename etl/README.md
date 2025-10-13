# VWE ETL Pipeline Strategies

ETL (Extract, Transform, Load) approaches for Valheim World Engine, organized by maturity level.

## Directory Structure

```
etl/
├── experimental/     # Research & development (active work)
├── stable/          # Production-ready (validated & deployed)
└── archive/         # Deprecated (historical reference)
```

## Maturity Levels

### 🧪 Experimental
**Purpose:** Research, development, proof-of-concept

**Status:** Active development, not production-ready

**Current Approaches:**
- `bepinex-gen1/` - Dense sampling baseline (512×512 @ ~3 min)
- `bepinex-adaptive-sampling/` - Edge-focused sampling optimization
- `warm-pooling/` - Pre-warmed Valheim server containers

**Guidelines:**
- Document hypothesis and expected performance
- Test with small datasets first
- Include performance benchmarks
- Document findings and lessons learned

### 🏭 Stable
**Purpose:** Validated, production-ready approaches

**Status:** Actively maintained and deployed

**Current State:** Empty, ready for promotion from experimental

**Requirements for Promotion:**
- Comprehensive testing complete
- Performance benchmarks documented
- Error handling and recovery implemented
- Production documentation created

### 📁 Archive
**Purpose:** Preserve deprecated approaches and lessons learned

**Status:** No longer developed, reference only

**Current Archive:**
- `legacy/` - All previous generation work (archived 2025-01-27)
  - Backend/worker system (FastAPI + RQ)
  - BepInEx plugins (production-ready but replaced)
  - Docker orchestration
  - Procedural export system
  - Validation data (preserved)

See `archive/legacy/README.md` for details.

## Maturity Progression

```
Experimental → Stable → Archive
     ↓            ↓        ↓
   Research → Production → Deprecated
```

### Promotion Criteria

**Experimental → Stable:**
1. ✅ Complete comprehensive testing
2. ✅ Document performance benchmarks vs baseline
3. ✅ Implement error handling and recovery
4. ✅ Create production documentation
5. ✅ Code review and approval
6. Move directory: `mv etl/experimental/approach etl/stable/`

**Stable → Archive:**
1. Identify replacement approach
2. Create migration guide
3. Update all code references
4. Move directory: `mv etl/stable/approach etl/archive/`
5. Add deprecation notice with reason

## Quick Reference

| Level | Use For | Modify | Deploy | Examples |
|-------|---------|--------|--------|----------|
| **Experimental** | Research, POCs | ✅ Yes | ❌ No | New algorithms, untested optimizations |
| **Stable** | Production | ✅ Yes | ✅ Yes | Validated approaches, core features |
| **Archive** | Reference | ❌ No | ❌ No | Deprecated, lessons learned |

## Current ETL Approaches

### Experimental Approaches

**1. bepinex-gen1** (Baseline)
- **Method:** Dense sampling via BepInEx plugins
- **Performance:** 512×512 @ ~3 min, 2048×2048 @ ~27 min
- **Coverage:** Full world (±10km)
- **Status:** ✅ Validated, baseline for comparisons
- **Path:** `etl/experimental/bepinex-gen1/`

**2. bepinex-adaptive-sampling** (Optimization)
- **Method:** Low-res base + edge refinement
- **Target:** 50-65% reduction vs baseline
- **Hypothesis:** Most detail needed at biome transitions
- **Status:** 🧪 Active research
- **Path:** `etl/experimental/bepinex-adaptive-sampling/`

**3. warm-pooling** (Infrastructure)
- **Method:** Pre-warmed Valheim server containers
- **Target:** 50-65% reduction in startup time
- **Hypothesis:** Eliminate 60-90s container initialization
- **Status:** 🧪 Active research
- **Path:** `etl/experimental/warm-pooling/`

### Integration

All ETL approaches integrate with:
- **Global Configuration:** YAML-based constants (`global/data/*.yml`)
- **Docker Orchestration:** Standardized container lifecycle
- **Code Generators:** Automated scaffolding (`global/generators/`)
- **Logging System:** Centralized monitoring (`global/logging/`)
- **Backend API:** Job queue and caching

## Development Workflow

### Creating a New Approach

```bash
# 1. Create directory
mkdir etl/experimental/my-approach

# 2. Add README documenting hypothesis
cat > etl/experimental/my-approach/README.md <<EOF
# My Approach - Experimental ETL Generator

## Hypothesis
[What you're trying to prove/optimize]

## Performance Target
[Expected improvement vs baseline]

## Implementation
[How it works]
EOF

# 3. Implement approach
# 4. Test with small datasets
# 5. Benchmark against baseline
# 6. Document findings
```

### Promoting to Stable

```bash
# After validation and testing
mv etl/experimental/my-approach etl/stable/
git add etl/stable/my-approach
git commit -m "Promote my-approach to stable"
```

### Archiving

```bash
# When deprecating
mv etl/stable/old-approach etl/archive/
echo "Deprecated YYYY-MM-DD: [reason]" >> etl/archive/old-approach/README.md
git add etl/archive/old-approach
git commit -m "Archive old-approach"
```

## Performance Tracking

Track all approaches against baseline:

| Approach | Resolution | Time | vs Baseline | Status |
|----------|-----------|------|-------------|--------|
| bepinex-gen1 | 512×512 | ~3 min | Baseline | ✅ Validated |
| bepinex-adaptive-sampling | 512×512 | TBD | Target: -50-65% | 🧪 Research |
| warm-pooling | 512×512 | TBD | Target: -50-65% | 🧪 Research |

Update this table as new data becomes available.

## Best Practices

### Documentation
- Clear README with hypothesis and approach
- Performance benchmarks vs baseline
- Known limitations and edge cases
- Migration notes when deprecating

### Testing
- Test with reference seed: `hkLycKKCMI`
- Validate against ground truth data
- Profile memory and CPU usage
- Test edge cases (short/long seeds, special chars)

### Code Quality
- Import constants from `global/data/*.yml`
- Use VWE logging system
- Handle errors gracefully
- Include integration tests

## References

- `README.md` - Main project documentation
- `global/README.md` - Global configuration system
- `etl/archive/legacy/README.md` - Legacy components archive
- `CLAUDE.md` - AI assistant guidance
