# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Valheim World Engine (VWE)** is a performant third-party mapping solution for Valheim that generates accurate world maps from seed strings. The system uses an ETL pipeline with Docker-orchestrated Valheim servers to generate world data, then processes and renders it for web visualization.

**Primary Test Seed:** `hkLycKKCMI`

**Project Status:** ✅ **BepInEx plugins validated and production-ready** (2025-10-09)

## Core Architecture

### System Components

- **Backend (FastAPI):** Python-based API server handling seed requests and orchestrating world generation
- **Worker (RQ):** Background job processor that manages Docker containers for world generation
- **Redis:** Job queue and caching layer
- **Valheim Server (Docker):** Custom `vwe/valheim-bepinex:latest` image with BepInExPack_Valheim 5.4.2333
- **BepInEx Plugins (C#):** ✅ **PRODUCTION READY** - Custom plugins for data export (VWE_AutoSave, VWE_DataExporter)
  - Default resolution: 512×512 (~3 min export, optimized for validation)
  - Full world coverage: ±10km (bug fixed from ±5km)
  - Correct biome ID bit flags (1, 2, 4, 8, 16, 32, 64, 256, 512)
- **Procedural Export System:** ✅ **VALIDATED** - Browser-based viewer + Jupyter notebooks for analysis
- **Frontend:** Next.js application for map visualization (planned/future)

### Data Flow

1. User submits seed → FastAPI creates job in Redis queue
2. RQ worker picks up job → Orchestrates Docker container with Valheim server
3. Container generates world (~60-90s) → BepInEx plugins export data
4. Graceful shutdown triggers world save → Creates `.db` and `.fwl` files
5. ETL pipeline processes data → Generates renders
6. Results cached in Redis → Served to frontend

### File Structure

```
data/seeds/{seed_hash}/
├── raw/                        # Generated world files from Valheim
├── worlds_local/               # Server creates .db and .fwl here
├── extracted/                  # Exported data from BepInEx plugins
│   ├── worldgen_plan.json     # Docker orchestration plan
│   ├── worldgen_logs.txt      # Container logs
│   ├── biomes.json            # Biome data from plugin
│   └── heightmap.npy          # Heightmap data from plugin
├── processed/                  # Transformed ETL outputs
└── renders/                    # Final rendered map layers
```

## Development Commands

### Starting the Stack

```bash
# Start all services (backend, worker, redis)
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f backend
docker compose -f docker/docker-compose.yml logs -f worker

# Stop services
docker compose -f docker/docker-compose.yml down
```

### Building BepInEx Plugins

```bash
cd bepinex

# Setup environment and build plugins
make setup build

# Clean build artifacts
make clean

# Build Docker image with plugins
make docker-build
```

### Testing World Generation

```bash
# Trigger world generation via API
curl -X POST http://localhost:8000/api/v1/seeds/generate \
  -H "Content-Type: application/json" \
  -d '{"seed": "TestWorld"}'

# Check job status (replace {seed_hash} with actual hash from response)
curl http://localhost:8000/api/v1/seeds/{seed_hash}/status

# Monitor generation logs
tail -f data/seeds/*/extracted/worldgen_logs.txt
```

### Docker Operations

```bash
# Build worldgen-runner base image (first time setup)
docker compose --profile build-only build worldgen-runner

# Check for stuck containers
docker ps | grep vwe-worldgen

# Clean up old worldgen containers
docker ps -a | grep vwe-worldgen | awk '{print $1}' | xargs docker rm -f
```

## Key Implementation Details

### World Generation Flow

The world generation process uses Docker containers with specific lifecycle management:

1. **Container Orchestration** (`world_generator.py`):
   - Creates unique container name per job to avoid conflicts
   - Mounts host data directory to `/config` in container
   - Sets environment variables including `PRE_SERVER_SHUTDOWN_HOOK` for graceful save
   - Streams logs in real-time for progress monitoring

2. **Log Pattern Matching**:
   - Monitors for patterns: "Game server connected", "Zonesystem Start", "Export complete", "Saving world", "World saved"
   - Detects world generation completion via "Failed to place all" or "Generated" messages
   - Triggers graceful shutdown immediately after generation completes

3. **Graceful Shutdown**:
   - Uses `PRE_SERVER_SHUTDOWN_HOOK` to trigger save command before container stops
   - Waits for both `.db` and `.fwl` files to appear and stabilize
   - Falls back to `.old` backup files if primary files not found

4. **File Ownership**:
   - Sets `PUID`/`PGID` for container to match host user
   - Recursively fixes ownership after generation to avoid root-owned files

### BepInEx Plugin Integration

The project includes custom C# plugins for data extraction:

- **VWE_AutoSave**: Triggers world save after a configurable delay post-generation
- **VWE_DataExporter**: Exports biome data, heightmaps, and structures in JSON/PNG formats

**Critical Bug Fixes Applied (2025-10-09):**
1. ✅ **World Coverage Bug** - Fixed sampling from 50% to 100% of world
   - **Before**: Only sampled ±5km (used world radius as diameter)
   - **After**: Full ±10km coverage (correctly uses `worldDiameter = worldRadius * 2`)
   - **Files**: BiomeExporter.cs, HeightmapExporter.cs, StructureExporter.cs

2. ✅ **Biome ID Mapping Bug** - Fixed from sequential to bit flags
   - **Before**: Used indices 0, 1, 2, 3, 4, 5, 6, 7, 8
   - **After**: Correct bit flags 1, 2, 4, 8, 16, 32, 64, 256, 512
   - **Files**: BiomeExporter.cs (GetBiomeNames method)

3. ✅ **Resolution Optimization** - Changed default from 2048 to 512
   - **Reason**: 512 resolution sufficient for validation (~3 min vs ~27 min)
   - **Quality**: Equivalent for analysis purposes, 4x faster export
   - **Production**: Can scale to 1024 or 2048 when needed

4. ✅ **Docker Integration** - Switched from generic BepInEx to BepInExPack_Valheim
   - **Reason**: Generic BepInEx had GLIBC compatibility issues with Valheim
   - **Solution**: Use Valheim-specific build (BepInExPack_Valheim 5.4.2333)
   - **Added**: Newtonsoft.Json.dll dependency for JSON serialization

**Plugin Development Workflow:**
1. Modify C# source in `bepinex/src/`
2. Run `make build` to compile plugins → outputs to `bepinex/plugins/`
3. Plugins are mounted into container at `/config/BepInEx/plugins/`
4. Server loads plugins on startup (requires `BEPINEX=1` env var)

**Validation Status**: See `procedural-export/VALIDATION_COMPLETE_512.md` for comprehensive validation results.

### Mapping Configuration Standards

All coordinate systems, colors, and rendering parameters are centralized in `backend/app/core/mapping_config.py`:

- **Coordinate System**: Origin at world center (0,0), units in meters, bounds ±10500m
- **Biome Colors**: Defined in `BIOME_COLORS` dict (e.g., Meadows=#4CAF50)
- **Shoreline Detection**: Water level at 30.0m, configurable depth threshold
- **Render Resolution**: Default 2048×2048 pixels (configurable via `RENDER_RESOLUTION_PX`)

**Critical Rule**: Never hardcode mapping values elsewhere. Always import from `mapping_config.py`.

### Job Queue Architecture

RQ (Redis Queue) manages background processing:

- **Queue Name**: `default` (RQ default)
- **Worker Command**: `python -m app.worker`
- **Job Timeout**: Configured via `PIPELINE_TIMEOUT_SEC` (default 1800s)
- **Job Metadata**: Tracks `current_stage` (generation/extraction/processing/rendering/caching) and `progress` (0-100)

**Job Meta Structure**:
```python
job.meta = {
    "current_stage": "generation",
    "progress": 45,
    "generation_status": {
        "log_match": True,
        "raw_present": True,
        "extracted_present": False,
        "log_path": "/path/to/logs.txt",
        "timed_out": False,
        "lines_written": 1234,
        "has_db": True,
        "has_fwl": True
    }
}
```

### Configuration Management

Environment variables are loaded from `.env` and managed through `backend/app/core/config.py`:

**Critical Variables:**
- `DATA_DIR`: Container-internal data path (default: `/app/data`)
- `HOST_DATA_DIR`: Host filesystem path for Docker volume mounts
- `REPO_ROOT`: Repository root for resolving relative paths
- `VALHEIM_IMAGE`: Docker image to use (default: `lloesche/valheim-server:latest`)
- `STAGE1_TIMEOUT_SEC`: World generation timeout (default: 300s)
- `HOST_UID`/`HOST_GID`: User/group IDs for file ownership

**Development vs Production:**
- Development uses relative paths and local Docker
- Production requires absolute paths for `HOST_DATA_DIR` and proper Docker socket access

## Common Pitfalls

### Docker Permission Issues

**Problem**: Container can't access `/var/run/docker.sock`

**Solution**: Worker service runs as `user: "0:0"` (root) in docker-compose to access Docker socket. Alternatively, add host user to `docker` group.

### File Ownership Conflicts

**Problem**: Generated files owned by root, not accessible by host user

**Solution**: Set `HOST_UID` and `HOST_GID` in `.env` to match host user. The `_chown_recursive()` function in `world_generator.py` fixes ownership post-generation.

### Container Name Conflicts

**Problem**: Docker error "Conflict. The container name ... is already in use"

**Solution**: Generator uses unique names (`vwe-worldgen-{hash}-{uuid}`) and removes stale containers before creation.

### Missing .db Files

**Problem**: Container generates `.fwl` but no `.db` file

**Solution**:
1. Check that `PRE_SERVER_SHUTDOWN_HOOK` is set correctly
2. Verify graceful shutdown logs show "VWE: Graceful shutdown initiated"
3. Look for `.db.old` backup files (handled automatically by `_choose_present_files()`)

### BepInEx Plugins Not Loading

**Problem**: Data exports not appearing in `extracted/` directory

**Solution**:
1. Verify `BEPINEX=1` is set in container environment
2. Check that plugins are mounted correctly: `docker exec <container> ls /config/BepInEx/plugins/`
3. Monitor container logs for BepInEx initialization messages

## Code Architecture Notes

### Backend Service Layer

- **`world_generator.py`**: Orchestrates Docker containers for world generation
- **`tasks.py`**: RQ job entry point, calls world generation and simulates pipeline stages
- **`job_queue.py`**: Enqueues jobs and manages Redis interaction (presumed location)
- **`config.py`**: Centralized settings loaded from environment variables
- **`mapping_config.py`**: Single source of truth for all mapping standards

### API Routes

- `POST /api/v1/seeds/generate`: Submit seed for generation
- `GET /api/v1/seeds/{seed_hash}/status`: Check job progress
- `GET /api/v1/seeds/{seed_hash}/data`: Retrieve processed world data (future)

### Worker Process

The worker (`app/worker.py`) runs as a separate process:
- Connects to Redis queue
- Pulls jobs from `default` queue
- Executes `simulate_pipeline()` function from `tasks.py`
- Updates job metadata for progress tracking

### BepInEx Plugin Architecture

Plugins are .NET 4.8 assemblies targeting BepInEx 5.x:
- **Entry Point**: Classes decorated with `[BepInPlugin]` attribute
- **Game Hooks**: Use Harmony patches or Unity lifecycle methods (Awake, Start, Update)
- **Data Export**: Write to `/config/world_data/` (mapped to container mount)
- **Logging**: Use BepInEx logger (`Logger.LogInfo/Warning/Error`)

## Testing and Validation

### Validation Process - ✅ COMPLETE (2025-10-09)

The project completed a comprehensive validation workflow:

1. ✅ Generated primary seed (`hkLycKKCMI`) at 512×512 resolution
2. ✅ Verified full world coverage (±10km, not ±5km)
3. ✅ Validated biome ID bit flags (1, 2, 4, 8, 16, 32, 64, 256, 512)
4. ✅ Confirmed export time: ~3 minutes (175 seconds) at 512 resolution
5. ✅ Browser visualization working with interactive biome map
6. ✅ Jupyter notebooks compatible with exported data format
7. ✅ Analyzed Valheim's WorldGenerator.GetBiome() source code

### Validation Results (Seed: hkLycKKCMI @ 512×512)

**Data Export:**
- Resolution: 512×512 = 262,144 samples
- World Size: 20,000m diameter (±10,000m)
- Export Time: ~175 seconds (2.9 minutes)
- File Size: 15.1 MB (samples JSON)

**Coordinate Coverage:**
- X range: [-10000.0, 9960.94] ✓ Full world coverage
- Z range: [-10000.0, 9960.94] ✓ Full world coverage
- Height: [-400.0, 448.27] ✓ Realistic terrain range

**Biome Distribution:**
| Biome        | ID  | Percentage | Status |
|--------------|-----|------------|--------|
| DeepNorth    | 256 | 30.89%     | ✓ Correct per Valheim logic |
| Ocean        | 32  | 18.06%     | ✓ Validated |
| Ashlands     | 512 | 15.08%     | ✓ Validated |
| Plains       | 16  | 11.85%     | ✓ Validated |
| Mountain     | 8   | 10.11%     | ✓ Validated |
| Mistlands    | 64  | 5.62%      | ✓ Correct (polar biomes have precedence) |
| Swamp        | 4   | 3.30%      | ✓ Validated |
| Meadows      | 1   | 2.88%      | ✓ Validated |
| BlackForest  | 2   | 2.23%      | ✓ Validated |

**Biome Distribution Notes:**
- High DeepNorth/Ashlands, low Mistlands is **CORRECT** per Valheim's WorldGenerator.GetBiome()
- Polar biomes checked BEFORE Mistlands in order-of-precedence
- Browser viewer includes "polar filter" toggle to recover Mistlands if desired

### Success Criteria - ✅ ALL MET

- ✅ Both `.db` and `.fwl` files created for every generation
- ✅ Total generation time < 5 minutes (~3 minutes at 512 resolution)
- ✅ Clean container shutdown with no data corruption
- ✅ Coordinate system validated against Valheim source code
- ✅ All biome IDs use correct bit flags
- ✅ Full world coverage (100%, not 50%)
- ✅ Browser viewer functional with interactive controls
- ✅ Jupyter notebooks compatible and working

**Detailed Validation Report:** `procedural-export/VALIDATION_COMPLETE_512.md`

## Important Implementation Rules

1. **No Configuration Drift**: All mapping constants must be imported from `mapping_config.py`
2. **Docker Socket Access**: Worker must run with appropriate permissions (root or docker group)
3. **Graceful Shutdown**: Always use `PRE_SERVER_SHUTDOWN_HOOK` to trigger save before container stops
4. **File Stability**: Wait for files to be stable (no size changes) for `STAGE1_STABLE_SEC` before considering generation complete
5. **Error Logging**: Always write to `worldgen_logs.txt` even on exceptions
6. **Unique Containers**: Generate unique container names per job to avoid conflicts
7. **Ownership Management**: Always fix file ownership after generation using `_chown_recursive()`

## Development Workflow

### Adding a New Map Layer

1. Update `SHORELINE_CONFIG` or add new config in `mapping_config.py`
2. Implement processing logic in a new service (e.g., `processor.py`)
3. Add rendering logic (e.g., `renderer.py`)
4. Update `expected_outputs` in `build_worldgen_plan()` if new files are needed
5. Add API endpoint in `seeds.py` to serve the new layer
6. Document the layer in README.md

### Modifying BepInEx Plugins

1. Edit C# source in `bepinex/src/VWE_*/`
2. Run `cd bepinex && make build` to compile
3. Plugins automatically copied to `bepinex/plugins/`
4. Rebuild Docker image if using containerized plugins: `make docker-build`
5. Test with a generation job to verify export files appear

### Debugging World Generation

1. Check container logs in `data/seeds/{seed_hash}/extracted/worldgen_logs.txt`
2. Look for Docker errors, SteamCMD download progress, and game server readiness patterns
3. Verify files exist in `data/seeds/{seed_hash}/worlds_local/`
4. Check job metadata via API: `GET /api/v1/seeds/{seed_hash}/status`
5. Use `docker ps` to see if containers are stuck running
6. Monitor RQ worker logs: `docker compose logs -f worker`

## References

- [lloesche/valheim-server-docker](https://github.com/lloesche/valheim-server-docker) - Docker image used for world generation
- [MakeFwl Tool](https://github.com/CrystalFerrai/MakeFwl) - Extracts metadata from `.fwl` files (planned integration)
- [BepInEx Documentation](https://docs.bepinex.dev/) - Plugin framework documentation
- `docs/REFERENCES.md` - Additional technical references
- `README.md` - Complete project plan and architecture
