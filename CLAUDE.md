# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Project Overview

**Valheim World Engine (VWE)** generates accurate world maps for Valheim from seed strings using a modular ETL architecture with YAML-based global configuration and automated code generation.

**Primary Test Seed:** `hkLycKKCMI`

## Architecture

### System Components

- **ETL Generators** (`etl/`): Self-contained world generation approaches organized by maturity
  - `experimental/`: R&D generators (bepinex-gen1, bepinex-adaptive-sampling, warm-pooling)
  - `stable/`: Production-ready generators (empty, ready for promotion)
  - `archive/legacy/`: Archived components (backend, bepinex, docker, procedural-export, scripts)

- **Global Configuration** (`global/`): YAML single source of truth
  - `data/*.yml`: Valheim constants, validation metrics, rendering config
  - `schemas/*.json`: JSON Schema validation
  - `generators/`: Code generators (C#, Python, TypeScript)
  - `docker/`: Container orchestration and warm pooling
  - `logging/`: Standardized logging

### Data Flow

```
YAML Config → Code Generation → ETL Generator → Docker (Valheim + BepInEx)
                                       ↓
                      Raw Data → Processed Data → Rendered Layers
```

## File Structure

```
valheim-world-engine/
├── etl/
│   ├── experimental/           # Active R&D generators
│   │   ├── bepinex-gen1/
│   │   ├── bepinex-adaptive-sampling/
│   │   └── warm-pooling/
│   ├── stable/                 # Production generators (empty)
│   └── archive/legacy/         # Archived (2025-01-27)
├── global/
│   ├── data/                   # YAML configuration (source of truth)
│   ├── schemas/                # JSON Schema validation
│   ├── generators/             # Code scaffolding
│   ├── docker/                 # Container management
│   └── logging/                # Logging system
├── backend/                    # Active FastAPI backend
├── docker/                     # Active Docker configs
├── procedural-export/          # Active procedural tools
├── scripts/                    # Active utility scripts
├── data/                       # Generated world data (git-ignored)
└── docs/                       # Documentation + reference images
```

**Per-Seed Data Structure:**
```
data/seeds/{seed_hash}/
├── raw/                        # Valheim world files (.db, .fwl)
├── extracted/                  # BepInEx exports (biomes.json, heightmap.npy)
├── processed/                  # Transformed data
└── renders/                    # Final map layers (webp)
```

## Development Commands

### Global Configuration
```bash
make global                     # Generate constants from YAML
cd global && make validate      # Validate YAML against schemas
cd global && make clean         # Clean generated files
```

### Code Generators
```bash
cd global/generators
python python_generator.py      # Generate FastAPI service
python csharp_generator.py      # Generate BepInEx plugin
python typescript_generator.py  # Generate Next.js app
```

### ETL Development
```bash
# Create experimental generator
mkdir etl/experimental/my-approach

# Promote to stable when validated
mv etl/experimental/my-approach etl/stable/

# Archive when deprecated
mv etl/stable/old-approach etl/archive/
```

## Key Implementation Rules

1. **Configuration**: All constants in `global/data/*.yml`, never hardcode
2. **Code Generation**: Run `make global` before building components
3. **Validation**: Run `cd global && make validate` before committing YAML
4. **ETL Maturity**: Experimental → Stable → Archive with documentation at each stage
5. **Path Awareness**: Legacy components in `etl/archive/legacy/`, active work at root or in `etl/experimental/`

## Common Pitfalls

### Configuration Drift
**Problem:** Hardcoded values scattered across codebase
**Solution:** Define in `global/data/*.yml`, generate with `make global`

### Outdated Constants
**Problem:** Stale generated code after YAML updates
**Solution:** `make global && git status global/generators/output/`

### Invalid YAML
**Problem:** Schema validation failures
**Solution:** `cd global && make validate`

### Path Confusion
**Problem:** Referencing old paths
**Solution:**
- Archived legacy: `etl/archive/legacy/`
- Active experimental: `etl/experimental/`
- Global config: `global/data/`

## Validation Data

**Status:** ✅ Complete validation (2025-10-09)

**Validated Metrics (Seed: hkLycKKCMI @ 512×512):**
- Full world coverage: ±10km
- Correct biome IDs: Bit flags (1, 2, 4, 8, 16, 32, 64, 256, 512)
- Export time: ~3 minutes
- Coordinate system validated

**Locations:**
- Validation metrics: `global/data/validation-data.yml`
- Raw data: `etl/archive/legacy/data/seeds/hkLycKKCMI/`
- Reference images: `docs/4096x4096_Map_hnLycKKCMI.png`, `docs/biomes_hnLycKKCMI.png`

## References

### Documentation
- `README.md` - Main project documentation
- `etl/README.md` - ETL maturity levels and guidelines
- `global/README.md` - Global configuration system
- `etl/archive/legacy/README.md` - Legacy components archive

### External Resources
- [lloesche/valheim-server-docker](https://github.com/lloesche/valheim-server-docker) - Valheim Docker image
- [MakeFwl Tool](https://github.com/CrystalFerrai/MakeFwl) - `.fwl` metadata extraction
- [BepInEx Documentation](https://docs.bepinex.dev/) - Plugin framework

### Key Configuration Files
- `global/data/valheim-world.yml` - Core Valheim constants
- `global/data/validation-data.yml` - Validated metrics
- `global/data/rendering-config.yml` - Rendering settings
