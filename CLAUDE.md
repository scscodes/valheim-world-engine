# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Valheim World Engine (VWE)** is a performant third-party mapping solution for Valheim that generates accurate world maps from seed strings. The system uses a **modular ETL architecture** with self-contained generators, a **global YAML-based configuration system**, and **automated code generation** for consistency across C#, Python, and TypeScript components.

**Primary Test Seed:** `hkLycKKCMI`

**Project Status:** ✅ **Modular architecture established** (2025-01-27)
- Global configuration system with YAML single source of truth
- Code generators for C#, Python, TypeScript components
- ETL maturity framework (experimental → stable → archive)
- Legacy components preserved in `etl/archive/legacy/`
- BepInEx plugins validated and production-ready (archived)

## Core Architecture

### System Components

- **Global Configuration System:** YAML-based single source of truth (`global/data/*.yml`)
  - Valheim world constants (dimensions, biomes, coordinates)
  - Validation data from seed `hkLycKKCMI`
  - Rendering configuration
  - JSON Schema validation for all YAML files

- **Code Generators:** Automated scaffolding for new components (`global/generators/`)
  - **C# Generator:** BepInEx plugin templates with proper dependencies
  - **Python Generator:** FastAPI service structures with testing
  - **TypeScript Generator:** Next.js applications with Tailwind CSS
  - **Constants Generator:** Auto-generates language-specific constants from YAML

- **ETL Generators:** Self-contained, maturity-tracked approaches (`etl/`)
  - **Stable:** Production-ready generators (empty, ready for new work)
  - **Experimental:** Early-stage R&D generators (empty, ready for new work)
  - **Archive:** Legacy components (backend, bepinex, docker, procedural-export, scripts)

- **Docker Management:** Intelligent container orchestration (`global/docker/`)
  - Warm container manager for instant world generation
  - Docker generator for consistent service configuration

- **Logging System:** Standardized logging across all components (`global/logging/`)

### Legacy Components (Archived but Validated)

The following components are **production-ready** but archived in `etl/archive/legacy/`:

- **BepInEx Plugins (C#):** ✅ **PRODUCTION READY** - Custom plugins for data export
  - VWE_AutoSave, VWE_DataExporter
  - Default resolution: 512×512 (~3 min export)
  - Full world coverage: ±10km (bug fixed from ±5km)
  - Correct biome ID bit flags (1, 2, 4, 8, 16, 32, 64, 256, 512)

- **Procedural Export System:** ✅ **VALIDATED** - Browser viewer + Jupyter notebooks

- **Backend/Worker System:** FastAPI + RQ with Docker orchestration
  - Replaced by self-contained ETL generators

See `etl/archive/legacy/README.md` for full details on archived components.

### Data Flow (New Modular Architecture)

**Global Configuration:**
1. Define constants in YAML (`global/data/*.yml`)
2. Validate against JSON Schema
3. Generate language-specific constants (`make global`)
4. Components import generated constants

**ETL Generator Workflow:**
1. Select appropriate ETL generator (stable or experimental)
2. Generator orchestrates Docker container with Valheim server
3. Container generates world → Exports data via BepInEx plugins or procedural methods
4. Generator processes data → Generates renders
5. Results stored in generator-specific output directory
6. Results served via generator's API (if applicable)

**Code Generation Workflow:**
1. Use generators to scaffold new components (`global/generators/`)
2. Generated code follows VWE standards automatically
3. Components integrate with global configuration system
4. Build process ensures constants are up-to-date

See `README.md` and individual generator documentation for detailed workflows.

### File Structure

```
valheim-world-engine/
├── etl/                          # ETL Pipeline Approaches (by maturity)
│   ├── stable/                   # Production-ready approaches (empty, ready for new work)
│   ├── experimental/             # Early-stage R&D approaches (empty, ready for new work)
│   └── archive/                  # Deprecated approaches
│       └── legacy/               # All previous generation work (2025-01-27 archive)
│           ├── backend/          # FastAPI backend (archived)
│           ├── bepinex/          # BepInEx plugins (production-ready, archived)
│           ├── data/             # Generated validation data (preserved)
│           ├── docker/           # Docker orchestration (archived)
│           ├── procedural-export/ # Procedural system (experimental, archived)
│           ├── scripts/          # Utility scripts (archived)
│           └── README.md         # Legacy archive documentation
│
├── global/                       # Global Configuration & Utilities
│   ├── data/                     # YAML configuration files (single source of truth)
│   │   ├── valheim-world.yml    # Core Valheim constants
│   │   ├── validation-data.yml  # Validation metrics (seed hkLycKKCMI)
│   │   └── rendering-config.yml # Rendering settings
│   ├── schemas/                  # JSON Schema validation
│   │   ├── valheim-world.schema.json
│   │   ├── validation-data.schema.json
│   │   └── rendering-config.schema.json
│   ├── generators/               # Code generators for VWE components
│   │   ├── python_generator.py  # FastAPI service generator
│   │   ├── csharp_generator.py  # BepInEx plugin generator
│   │   ├── typescript_generator.py # Next.js app generator
│   │   ├── python/              # Python constant generators
│   │   └── output/              # Generated code output
│   ├── logging/                  # VWE logging system
│   │   ├── vwe_logger.py
│   │   ├── log_monitoring.py
│   │   └── docker_logging.py
│   ├── docker/                   # Docker management
│   │   ├── docker_generator.py
│   │   ├── warm_container_manager.py
│   │   └── DOCKER_STRATEGY.md
│   ├── Makefile                  # Global build orchestration
│   └── README.md                 # Global system documentation
│
├── docs/                         # Documentation
│   ├── README.md                 # Documentation overview
│   ├── 4096x4096_Map_hnLycKKCMI.png  # Reference map image
│   └── biomes_hnLycKKCMI.png     # Reference biome visualization
│
├── Makefile                      # Root build orchestration
├── README.md                     # Main project documentation
└── CLAUDE.md                     # This file
```

**ETL Generator Data Structure** (per generator):
```
data/seeds/{seed_hash}/
├── raw/                        # Generated world files from Valheim
│   ├── {seed_hash}.db         # Valheim world save
│   ├── {seed_hash}.fwl        # Valheim world metadata
│   └── *.old                  # Optional backup files
├── extracted/                  # Exported data from BepInEx/procedural
│   ├── worldgen_plan.json     # Docker orchestration plan
│   ├── worldgen_logs.txt      # Container logs
│   ├── biomes.json            # Biome data
│   └── heightmap.npy          # Heightmap data
├── processed/                  # Transformed ETL outputs
│   ├── biomes.json
│   ├── heightmap.json
│   ├── shoreline.json
│   └── metadata.json
└── renders/                    # Final rendered map layers
    ├── biomes_layer.webp
    ├── land_sea_layer.webp
    ├── heightmap_layer.webp
    └── shoreline_overlay.webp
```

## Development Commands

### Global Configuration System

```bash
# Generate constants from YAML for all languages
make global

# Or from global directory
cd global && make generate

# Validate YAML configuration
cd global && make validate

# Clean generated files
cd global && make clean
```

### Code Generators

```bash
# Navigate to generators
cd global/generators

# Generate a new BepInEx plugin
python csharp_generator.py

# Generate a new FastAPI service
python python_generator.py

# Generate a new Next.js application
python typescript_generator.py

# See generator README for detailed usage
cat README.md
```

### ETL Generator Development

```bash
# Create a new experimental ETL generator
cd etl/experimental
mkdir my-new-approach
# Add README.md, implementation files, etc.

# When ready to promote to stable
mv etl/experimental/my-new-approach etl/stable/

# Archive deprecated approaches
mv etl/stable/old-approach etl/archive/
```

### Legacy Components (Archived)

**Note:** The following commands work with archived components in `etl/archive/legacy/`

#### Building BepInEx Plugins (Archived)
```bash
cd etl/archive/legacy/bepinex

# Setup environment and build plugins
make setup build

# Clean build artifacts
make clean
```

#### Starting Legacy Backend Stack (Archived)
```bash
cd etl/archive/legacy

# Start all services (backend, worker, redis)
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f backend

# Stop services
docker compose -f docker/docker-compose.yml down
```

#### Legacy World Generation Testing (Archived)
```bash
# Trigger world generation via legacy API
curl -X POST http://localhost:8000/api/v1/seeds/generate \
  -H "Content-Type: application/json" \
  -d '{"seed": "TestWorld"}'

# Monitor generation logs
tail -f etl/archive/legacy/data/seeds/*/extracted/worldgen_logs.txt
```

## Global Configuration System

### YAML Single Source of Truth

All mapping constants are defined in `global/data/*.yml` and auto-generated for each language:

**`valheim-world.yml`** - Core Valheim constants:
- World dimensions (radius: 10000m, diameter: 20000m)
- Coordinate system (x=east/west, y=height, z=north/south)
- Height system (sea level: 30.0m, multiplier: 200.0)
- Biome definitions with IDs, colors (RGB/hex), thresholds

**`validation-data.yml`** - Validated metrics from seed `hkLycKKCMI`:
- Coordinate ranges, height ranges
- Biome distribution percentages
- Performance metrics

**`rendering-config.yml`** - Rendering settings:
- Resolution presets
- Shoreline detection parameters
- Filter thresholds

### Configuration Workflow

```bash
# 1. Edit YAML files in global/data/
vim global/data/valheim-world.yml

# 2. Validate against JSON Schema
cd global && make validate

# 3. Generate language-specific constants
make generate

# 4. Generated files appear in:
#    - global/generators/output/python/<service>/generated_constants.py
#    - global/generators/output/csharp/<plugin>/ValheimConstants.cs
#    - global/generators/output/typescript/<app>/valheim-constants.ts
```

**Critical Rule:** Never hardcode mapping values. Always import from generated constants or YAML directly.

## Code Generators

VWE includes code generators to scaffold new components with consistent standards:

### C# Generator (`global/generators/csharp_generator.py`)
- Creates BepInEx plugin templates (.csproj, .cs, .cfg)
- Generates project files with proper dependencies
- Includes VWE-specific templates (DataExporter, AutoSave)

### Python Generator (`global/generators/python_generator.py`)
- Creates FastAPI service structures
- Generates Pydantic models, API routes, service layers
- Includes Docker configuration and test setup

### TypeScript Generator (`global/generators/typescript_generator.py`)
- Creates Next.js 14 applications with App Router
- Generates TypeScript types, React components, API clients
- Includes Tailwind CSS and testing setup

### Usage

```python
from global.generators.python_generator import PythonGenerator

generator = PythonGenerator()
files = generator.create_fastapi_service(
    service_name="VWE_DataProcessor",
    version="1.0.0"
)
```

See `global/generators/README.md` for detailed documentation.

## ETL Maturity Levels

ETL approaches are organized by maturity in `etl/`:

### Stable (`etl/stable/`)
- **Purpose**: Production-ready approaches
- **Status**: Actively maintained and deployed
- **Quality**: Comprehensive testing, error handling, documentation
- **Current**: Empty, ready for new production approaches

### Experimental (`etl/experimental/`)
- **Purpose**: Research, development, proof-of-concept
- **Status**: In active development, not production-ready
- **Quality**: Testing with small datasets, documenting findings
- **Current**: Empty, ready for new experiments

### Archive (`etl/archive/`)
- **Purpose**: Deprecated approaches, lessons learned
- **Status**: No longer developed, preserved for reference
- **Quality**: Historical context, migration notes
- **Current**: `legacy/` - All previous generation work (archived 2025-01-27)

### Maturity Progression

```
Experimental → Stable → Archive
     ↓            ↓        ↓
   Research → Production → Deprecated
```

See `etl/README.md` for promotion criteria and guidelines.

## Legacy Components (Archived)

Previous generation components are preserved in `etl/archive/legacy/`:

### BepInEx Plugins ✅ **Production Ready**
- **Location**: `etl/archive/legacy/bepinex/`
- **Plugins**: VWE_AutoSave, VWE_DataExporter
- **Performance**: 512×512 resolution in ~3 minutes
- **Validation**: Full world coverage (±10km), correct biome IDs
- **Status**: Validated and working, archived for reference
- **Docs**: See `etl/archive/legacy/bepinex/README.md`

### Backend/Worker System
- **Location**: `etl/archive/legacy/backend/`
- **Stack**: FastAPI + RQ + Redis + Docker orchestration
- **Status**: Replaced by self-contained ETL generators
- **Reason**: Simpler, direct integration preferred

### Procedural Export System
- **Location**: `etl/archive/legacy/procedural-export/`
- **Features**: Browser viewer, Jupyter notebooks, metadata extraction
- **Status**: Experimental approach, archived

### Validation Data
- **Location**: `etl/archive/legacy/data/`
- **Content**: Generated world data from seed `hkLycKKCMI`
- **Status**: Preserved for reference and validation

See `etl/archive/legacy/README.md` for complete details on archived components.

## Docker Management

VWE uses intelligent Docker orchestration via `global/docker/`:

### Warm Container Manager
- Pre-warmed Valheim server containers for instant world generation
- Automatic container lifecycle management
- Health checks and monitoring
- See `global/docker/warm_container_manager.py`

### Docker Generator
- Creates consistent Dockerfile templates for services
- Generates docker-compose configurations following VWE standards
- Includes health checks, resource limits, security settings
- See `global/docker/docker_generator.py`

### Docker Strategy
- Short-running containers: World generation (create → run → collect → destroy)
- Medium-running containers: API services with restart policies
- Long-running containers: Redis, databases with data persistence
- See `global/docker/DOCKER_STRATEGY.md` for complete patterns

## Common Pitfalls

### Configuration Drift

**Problem**: Hardcoded mapping values scattered across codebase

**Solution**: All constants must be defined in `global/data/*.yml` and generated. Never hardcode values. Run `make global` after YAML changes.

### Outdated Generated Constants

**Problem**: Components use stale constants after YAML updates

**Solution**:
```bash
# Regenerate constants after any YAML change
make global

# Verify generated files are updated
git status global/generators/output/
```

### Invalid YAML Configuration

**Problem**: YAML files fail schema validation

**Solution**:
```bash
# Validate before committing
cd global && make validate

# Check schema errors
jsonschema -i data/valheim-world.yml schemas/valheim-world.schema.json
```

### ETL Maturity Confusion

**Problem**: Using experimental approaches in production

**Solution**: Only use generators from `etl/stable/`. Experimental approaches are for R&D only. Check `etl/README.md` for maturity criteria.

### Legacy Path References

**Problem**: Code references old paths (backend/, bepinex/, docker/)

**Solution**: Legacy components are in `etl/archive/legacy/`. Update paths:
- OLD: `backend/app/core/mapping_config.py`
- NEW: `global/data/valheim-world.yml`
- OLD: `bepinex/plugins/`
- NEW: `etl/archive/legacy/bepinex/plugins/`

## Development Workflow

### Adding New Constants

```bash
# 1. Edit YAML configuration
vim global/data/valheim-world.yml

# 2. Update JSON Schema (if adding new fields)
vim global/schemas/valheim-world.schema.json

# 3. Validate
cd global && make validate

# 4. Regenerate constants
make generate

# 5. Verify generated files
ls -la global/generators/output/

# 6. Commit both YAML and generated files
git add global/data/ global/generators/output/
git commit -m "Add new constants"
```

### Creating a New ETL Generator

```bash
# 1. Create experimental directory
mkdir etl/experimental/my-approach
cd etl/experimental/my-approach

# 2. Add documentation
cat > README.md <<EOF
# My Approach - Experimental ETL Generator

## Hypothesis
...

## Performance Target
...
EOF

# 3. Implement generator
# Use code generators for scaffolding:
cd ../../../global/generators
python python_generator.py  # or csharp_generator.py

# 4. Test with small datasets
# 5. Document findings
# 6. Promote to stable when ready
```

### Using Code Generators

```bash
# Generate a new service
cd global/generators
python python_generator.py

# Follow prompts or use programmatically:
python -c "
from python_generator import PythonGenerator
gen = PythonGenerator()
files = gen.create_fastapi_service('VWE_MyService', version='1.0.0')
"
```

## Testing and Validation

### Validation Status - ✅ COMPLETE (2025-10-09)

Complete validation data preserved in `etl/archive/legacy/`:

**Validation Metrics (Seed: hkLycKKCMI @ 512×512):**
- ✅ Full world coverage: ±10km
- ✅ Correct biome IDs: Bit flags (1, 2, 4, 8, 16, 32, 64, 256, 512)
- ✅ Export time: ~3 minutes (512 resolution)
- ✅ Coordinate system validated against Valheim source
- ✅ Browser viewer + Jupyter notebooks working

**Validated Data Locations:**
- Raw data: `etl/archive/legacy/data/seeds/hkLycKKCMI/`
- Validation report: `etl/archive/legacy/procedural-export/VALIDATION_COMPLETE_512.md`
- Reference images: `docs/4096x4096_Map_hnLycKKCMI.png`, `docs/biomes_hnLycKKCMI.png`
- Validation metrics: `global/data/validation-data.yml` (YAML config)

**Using Validation Data:**

```bash
# Reference validation data in new ETL generators
cat global/data/validation-data.yml

# Compare new generator output against validated reference
diff new_output.json etl/archive/legacy/data/seeds/hkLycKKCMI/extracted/biomes.json

# View reference images
open docs/4096x4096_Map_hnLycKKCMI.png
```

See `global/data/validation-data.yml` for complete validated metrics.

## Important Implementation Rules

1. **Single Source of Truth**: All constants defined in `global/data/*.yml`, never hardcode
2. **Generate Before Build**: Run `make global` before building any component
3. **Validate YAML Changes**: Run `cd global && make validate` before committing YAML edits
4. **ETL Maturity Progression**: Experimental → Stable → Archive (document at each stage)
5. **Code Generation Standards**: Use generators (`global/generators/`) for new components
6. **Legacy Path Awareness**: Legacy components in `etl/archive/legacy/`, not at root
7. **Reference Validation Data**: Use `global/data/validation-data.yml` and archived seed data
8. **Docker Management**: Use warm container manager and docker generator for consistency


## References

### Documentation
- `README.md` - Main project documentation and architecture
- `etl/README.md` - ETL maturity levels and progression guidelines
- `global/README.md` - Global configuration system documentation
- `global/generators/README.md` - Code generator usage and templates
- `global/docker/DOCKER_STRATEGY.md` - Docker orchestration patterns
- `etl/archive/legacy/README.md` - Legacy components archive

### External Resources
- [lloesche/valheim-server-docker](https://github.com/lloesche/valheim-server-docker) - Valheim Docker image
- [MakeFwl Tool](https://github.com/CrystalFerrai/MakeFwl) - `.fwl` file metadata extraction
- [BepInEx Documentation](https://docs.bepinex.dev/) - Plugin framework (for legacy plugins)

### Key Configuration Files
- `global/data/valheim-world.yml` - Single source of truth for all constants
- `global/data/validation-data.yml` - Validated metrics from seed hkLycKKCMI
- `global/data/rendering-config.yml` - Rendering and visualization settings
