# Valheim World Engine

A performant, accurate third-party mapping solution for Valheim that generates world maps from seed strings using a modular ETL architecture.

**Primary Test Seed:** `hkLycKKCMI`

## Architecture

```
┌─────────────────┐
│   Next.js UI    │
│   (Frontend)    │
└────────┬────────┘
         │ REST
         ▼
┌─────────────────┐      ┌──────────────┐
│  ETL Generators │◄────►│   Global     │
│  (Self-contained)│     │  Config YAML │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Docker + BepInEx│      │  Generated   │
│  (Valheim Server)│      │     Data     │
└─────────────────┘      └──────────────┘
```

### Data Flow

```
Seed Input → ETL Generator → Docker (Valheim + BepInEx)
                 ↓
    Raw Data (.db, .fwl, biomes.json, heightmap.npy)
                 ↓
    Processing (biomes, heightmap, shoreline detection)
                 ↓
    Renders (webp layers: biomes, heightmap, land/sea, shoreline overlay)
                 ↓
    API Response → Client Visualization
```

## Project Structure

```
valheim-world-engine/
├── etl/
│   ├── experimental/             # Active R&D generators
│   │   ├── bepinex-gen1/        # Dense sampling via BepInEx
│   │   ├── bepinex-adaptive-sampling/  # Edge-focused sampling
│   │   └── warm-pooling/        # Pre-warmed container pool
│   ├── stable/                   # Production generators (ready for promotion)
│   └── archive/legacy/           # Archived components (2025-01-27)
├── global/
│   ├── data/                     # YAML config (single source of truth)
│   ├── schemas/                  # JSON Schema validation
│   ├── generators/               # Code scaffolding (C#, Python, TS)
│   ├── docker/                   # Container orchestration
│   └── logging/                  # Standardized logging
├── backend/                      # FastAPI backend
├── docker/                       # Docker configurations
├── procedural-export/            # Procedural extraction tools
├── scripts/                      # Utility scripts
├── data/                         # Generated world data (git-ignored)
└── docs/                         # Documentation + reference images
```

**Per-Seed Data Structure:**
```
data/seeds/{seed_hash}/
├── raw/                          # Valheim world files
│   ├── {seed_hash}.db            # World save
│   └── {seed_hash}.fwl           # World metadata
├── extracted/                    # BepInEx exports
│   ├── biomes.json               # Biome grid data
│   ├── heightmap.npy             # Height values
│   ├── worldgen_plan.json        # Orchestration plan
│   └── worldgen_logs.txt         # Container logs
├── processed/                    # Transformed data
│   ├── biomes.json
│   ├── heightmap.json
│   ├── shoreline.json
│   └── metadata.json
└── renders/                      # Final layers
    ├── biomes_layer.webp
    ├── heightmap_layer.webp
    ├── land_sea_layer.webp
    └── shoreline_overlay.webp
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+

### Setup
```bash
# Clone and setup
git clone <repo_url>
cd valheim-world-engine

# Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Generate constants from YAML
make global

# Start services
docker compose up -d

# Initialize database
python scripts/init_db.py
```

### Common Commands
```bash
# Global configuration
make global                       # Generate constants from YAML
cd global && make validate        # Validate YAML schemas

# Code generation
cd global/generators
python python_generator.py        # FastAPI service
python csharp_generator.py        # BepInEx plugin
python typescript_generator.py    # Next.js app

# ETL development
cd etl/experimental/bepinex-gen1
python main.py --seed hkLycKKCMI  # Generate world map
```

## Configuration Standards

### Global Configuration (YAML)

All constants defined in `global/data/*.yml`:

- **`valheim-world.yml`** - Core constants (world bounds, biomes, coordinates)
- **`validation-data.yml`** - Validated metrics from seed hkLycKKCMI
- **`rendering-config.yml`** - Rendering settings (resolution, colors, patterns)

**Critical Rule:** Never hardcode values. Always import from generated constants.

```bash
# After editing YAML
cd global && make validate        # Validate against schema
make generate                     # Regenerate constants
```

### Key Constants

**World Dimensions:**
- Radius: 10500m (10000m playable + 500m edge)
- Diameter: 21000m
- Units: Meters (Valheim native)

**Coordinate System:**
- Origin: World center (0, 0)
- X-axis: East (+) / West (-)
- Y-axis: Height/Elevation
- Z-axis: North (+) / South (-)

**Height System:**
- Sea level: 30.0m
- Zone size: 64m × 64m

**Rendering:**
- Default resolution: 2048×2048
- Meters per pixel: 21000 / resolution
- Format: WebP with alpha channel

## ETL Generators

ETL approaches organized by maturity:

**Experimental** (`etl/experimental/`):
- `bepinex-gen1/` - Dense sampling baseline (512×512 @ ~3 min)
- `bepinex-adaptive-sampling/` - Edge-focused sampling (research)
- `warm-pooling/` - Pre-warmed container pool (research)

**Stable** (`etl/stable/`):
- Empty, ready for promotion from experimental

**Archive** (`etl/archive/legacy/`):
- Legacy components from 2025-01-27 archive
- See `etl/archive/legacy/README.md`

**Maturity Progression:**
```
Experimental → Stable → Archive
     ↓            ↓        ↓
   Research → Production → Deprecated
```

See `etl/README.md` for guidelines.

## Performance

**Current Baseline (BepInEx Dense Sampling):**
- 512×512: ~3 minutes
- 2048×2048: ~27 minutes

**Optimization Strategies (In Research):**

1. **Adaptive Sampling** (Target: 50-65% reduction)
   - Low-res base + edge refinement
   - Implementation: `etl/experimental/bepinex-adaptive-sampling/`

2. **Warm Pooling** (Target: 50-65% reduction)
   - Pre-warmed Valheim servers
   - Implementation: `etl/experimental/warm-pooling/`

3. **Parallel Chunks** (Target: 70-80% reduction)
   - Spatial parallelization (future work)

## API Endpoints

**Generate World:**
```bash
POST /api/v1/seeds/generate
{
  "seed": "hkLycKKCMI",
  "force_regenerate": false
}
```

**Check Status:**
```bash
GET /api/v1/seeds/{seed_hash}/status
```

**Get Data:**
```bash
GET /api/v1/seeds/{seed_hash}/data
```

See detailed API docs in `docs/API.md` (future).

## Validation Status

✅ **Complete** (2025-10-09)

**Validated Metrics (Seed: hkLycKKCMI @ 512×512):**
- Full world coverage: ±10km
- Correct biome IDs: Bit flags (1, 2, 4, 8, 16, 32, 64, 256, 512)
- Export time: ~3 minutes
- Coordinate system validated against in-game `/pos` command

**Validation Data:**
- Metrics: `global/data/validation-data.yml`
- Raw data: `etl/archive/legacy/data/seeds/hkLycKKCMI/`
- Reference images: `docs/4096x4096_Map_hnLycKKCMI.png`

## Development Guidelines

### Configuration Management
1. Define all constants in `global/data/*.yml`
2. Validate: `cd global && make validate`
3. Generate: `make global`
4. Never hardcode values in source code

### ETL Development
1. Start in `etl/experimental/`
2. Document hypothesis and approach
3. Test with small datasets
4. Promote to `etl/stable/` when validated
5. Archive deprecated approaches

### Code Generation
Use generators for new components:
```bash
cd global/generators
python python_generator.py      # Creates FastAPI service
python csharp_generator.py      # Creates BepInEx plugin
python typescript_generator.py  # Creates Next.js app
```

## Common Issues

**Outdated constants after YAML changes:**
```bash
make global && git status global/generators/output/
```

**YAML validation failures:**
```bash
cd global && make validate
```

**Path confusion:**
- Archived legacy: `etl/archive/legacy/`
- Active experimental: `etl/experimental/`
- Global config: `global/data/`

## References

### Documentation
- `CLAUDE.md` - AI assistant guidance
- `etl/README.md` - ETL maturity framework
- `global/README.md` - Global configuration system
- `etl/archive/legacy/README.md` - Legacy components

### External Resources
- [lloesche/valheim-server-docker](https://github.com/lloesche/valheim-server-docker)
- [MakeFwl Tool](https://github.com/CrystalFerrai/MakeFwl)
- [BepInEx Documentation](https://docs.bepinex.dev/)
- [valheim-map.world](https://valheim-map.world/) (reference implementation)

## License

TBD
