# BepInEx Gen1 - Experimental ETL Generator

**Status:** 🧪 Experimental
**Created:** 2025-10-09
**Maturity:** Early development

## Hypothesis

The BepInEx plugin approach from legacy can be modernized into a self-contained, modular ETL generator that:
- Uses global YAML configuration (no hardcoded values)
- Integrates with warm Docker container manager
- Follows new data structure standard (raw/extracted/processed/renders)
- Proves the modular architecture pattern works end-to-end

## Approach

### Data Flow
```
Input (Seed) → Docker Orchestration (Valheim + BepInEx)
                        ↓
              World Generation (.db, .fwl)
                        ↓
              BepInEx Export (biomes.json, heightmap.npy)
                        ↓
              ETL Processing (transform to standard format)
                        ↓
              Rendering (generate WebP layers)
                        ↓
              Output (complete seed data package)
```

### Architecture

```
bepinex-gen1/
├── generator.py          # Main orchestrator
├── lib/
│   ├── orchestrator.py   # Docker + BepInEx coordination
│   ├── processor.py      # Transform extracted → processed
│   ├── renderer.py       # Generate WebP renders
│   └── utils.py          # Helper functions
├── config/
│   └── generator.yaml    # Generator-specific settings
├── data/                 # Output directory (gitignored)
│   └── seeds/{hash}/     # Generated data per seed
└── README.md             # This file
```

## Performance Targets

Based on legacy BepInEx validation:
- **Generation time:** ~3 minutes (512×512 resolution)
- **Full world coverage:** ±10km
- **Accuracy:** Validated against seed `hkLycKKCMI`
- **Output format:** JSON + NumPy + WebP

## Integration Points

### Global Configuration
- Imports constants from `global/data/valheim-world.yml`
- Uses rendering settings from `global/data/rendering-config.yml`
- Validates against `global/data/validation-data.yml`

### Docker Orchestration
- Uses `global/docker/warm_container_manager.py`
- Container: `vwe/valheim-bepinex:latest` or `lloesche/valheim-server`
- BepInEx plugins from `etl/experimental/bepinex-gen1/plugins/`

### Output Structure
```
data/seeds/{seed_hash}/
├── raw/                  # Valheim world files
│   ├── {seed}.db
│   └── {seed}.fwl
├── extracted/            # BepInEx exports
│   ├── worldgen_plan.json
│   ├── worldgen_logs.txt
│   ├── biomes.json
│   └── heightmap.npy
├── processed/            # Transformed data
│   ├── biomes.json
│   ├── heightmap.json
│   ├── metadata.json
│   └── statistics.json
└── renders/              # Final renders
    ├── biomes_layer.webp
    ├── land_sea_layer.webp
    ├── heightmap_layer.webp
    └── shoreline_overlay.webp
```

## Validation Plan

1. **Generate validation seed:** `hkLycKKCMI`
2. **Compare outputs:**
   - Biome data structure matches legacy
   - Heightmap values align (±tolerance)
   - Visual renders match reference images
3. **Performance check:**
   - Generation time within expected range
   - Memory usage acceptable
4. **Config drift check:**
   - Zero hardcoded values
   - All constants from YAML

## Success Criteria

- [ ] Successfully generates seed `hkLycKKCMI`
- [ ] Output structure matches new standard
- [ ] All constants imported from global YAML
- [ ] Docker orchestration works reliably
- [ ] Visual output matches reference images in `docs/`
- [ ] Performance within 10% of legacy (~3 min)
- [ ] Zero configuration drift

## Migration from Legacy

### Reused Components
- BepInEx plugins (VWE_DataExporter, VWE_AutoSave) from archive
- Docker orchestration patterns
- Validation data for testing

### New Components
- Global YAML config integration
- Warm container manager usage
- Modular processor/renderer separation
- Standard output structure

### Deprecated
- Custom backend API orchestration
- Hardcoded mapping values
- Complex job queue system

## Dependencies

```bash
# Python packages
pip install -r requirements.txt

# Docker images
docker pull lloesche/valheim-server:latest
# Or build custom: docker build -t vwe/valheim-bepinex:latest .

# BepInEx plugins
# Use compiled .dll files from etl/experimental/bepinex-gen1/plugins/
```

## Usage

```bash
# Generate a single seed
python generator.py --seed "hkLycKKCMI" --resolution 512

# Generate with validation
python generator.py --seed "hkLycKKCMI" --validate

# Batch generation
python generator.py --seeds-file seeds.txt --resolution 1024
```

## Known Limitations

- Docker required (no native execution)
- BepInEx plugins must be pre-compiled
- Valheim server startup overhead (~30-60s)
- Single-threaded generation (one seed at a time)

## Future Enhancements

If promoted to stable:
- Parallel seed generation
- Custom resolution per layer
- Incremental updates (detect changes)
- Caching of common patterns
- API endpoint integration

## References

- Experimental BepInEx: `etl/experimental/bepinex-gen1/`
- Validation data: `global/data/validation-data.yml`
- Global config: `global/data/`
- Docker manager: `global/docker/warm_container_manager.py`
