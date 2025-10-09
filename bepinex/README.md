# BepInEx Integration for Valheim World Engine

This directory contains custom BepInEx plugins for programmatic Valheim world generation and data export.

## Current Status (2025-10-09)

✅ **PRODUCTION READY:**
- World generation and data export fully functional
- Full world coverage (±10km, bug fixed from ±5km)
- Correct biome ID bit flags (1, 2, 4, 8, 16, 32, 64, 256, 512)
- Optimized default resolution: 512×512 (~3 min export)
- Docker integration complete with BepInExPack_Valheim 5.4.2333
- Comprehensive validation completed

✅ **Bug Fixes Applied:**
- World sampling bug fixed (50% → 100% coverage)
- Biome ID mapping fixed (sequential → bit flags)
- Docker compatibility fixed (generic BepInEx → BepInExPack_Valheim)
- Newtonsoft.Json dependency added

**See:** `procedural-export/VALIDATION_COMPLETE_512.md` for detailed validation results

## How It Works

**Instead of** waiting for server lifecycle and graceful shutdown hooks, this approach:
1. Hooks into `ZoneSystem.Start` event (world generation complete)
2. Immediately triggers `ZNet.instance.Save()` programmatically
3. Exports biomes/heightmap data **during** generation (in progress)
4. **Achieved: ~17 seconds** (10x faster than backend approach)

## Prerequisites

### Required Software
- **.NET Framework 4.8 SDK** (for building plugins)
- **Docker** (for running isolated test environment)
- **Valheim assemblies** (for compiling plugins)

### Required Assembly Files for Plugin Development

**⚠️ Only needed if modifying plugin source code**

To compile the C# plugins, you need Valheim game assemblies in `bepinex/plugins/`:
- `Assembly-CSharp.dll` (Valheim's main game assembly)
- `UnityEngine.dll` and related modules
- `BepInEx.dll`, `BepInEx.Harmony.dll`

**Extraction methods:** See `ASSEMBLY_EXTRACTION_GUIDE.md`

**Note:** Pre-compiled plugins (`VWE_AutoSave.dll`, `VWE_DataExporter.dll`) are already in `bepinex/plugins/` and ready to use.

## Architecture

**Key Differences from Backend Approach:**

1. **Custom Docker Image:**
   - Backend uses `lloesche/valheim-server` (Debian 11, GLIBC 2.31)
   - BepInEx uses custom `vwe/valheim-bepinex` (Debian 12, GLIBC 2.36)
   - **Why:** BepInEx doorstop loader requires GLIBC 2.33+

2. **Programmatic Control:**
   - Backend relies on graceful shutdown hooks (timing-based)
   - BepInEx uses **custom VWE plugins** that hook world generation events
   - VWE plugins trigger saves immediately when generation completes

3. **Data Export:**
   - Backend extracts data post-generation
   - BepInEx exports biomes/heightmaps **during** generation

**Performance Achieved:**
- Eliminates wait for autosave timer (20-30 min)
- World generation + save: ~17 seconds
- **10x faster than backend approach** (2-3 minutes)
- Data export in progress (coroutines need debugging)

## Directory Structure

```
bepinex/
├── README.md                    # This file
├── src/                        # BepInEx plugin source code
│   ├── VWE_AutoSave/          # Auto-save plugin
│   │   ├── VWE_AutoSave.cs
│   │   └── VWE_AutoSave.csproj
│   └── VWE_DataExporter/      # Data export plugin
│       ├── VWE_DataExporter.cs
│       ├── VWE_DataExporter.csproj
│       └── DataExporters/
│           ├── BiomeExporter.cs
│           ├── HeightmapExporter.cs
│           └── StructureExporter.cs
├── plugins/                    # Compiled plugin DLLs (ready to use)
│   ├── VWE_AutoSave.dll       # Triggers immediate save on world gen complete
│   ├── VWE_DataExporter.dll   # Exports biome/heightmap data
│   └── [assembly files...]    # Required for compilation only
├── config/                     # BepInEx configuration
│   ├── BepInEx.cfg            # BepInEx runtime config
│   └── VWE_DataExporter.cfg   # Plugin-specific settings
└── Makefile                    # Build automation

../docker/bepinex/              # Isolated Docker setup
└── docker-compose.bepinex.yml # Standalone compose file
```

## Plugins

### VWE_AutoSave
**Purpose**: Triggers immediate world saves when world generation completes.

**Key Features**:
- Hooks into `ZoneSystem.Start` event (world generation complete)
- Calls `ZNet.instance.Save(true)` programmatically (synchronous save)
- Configurable save triggers and timing
- Logs save events for debugging
- **Status**: ✅ Working (saves in ~67ms)

**Configuration**:
```ini
[AutoSave]
# Enable/disable auto-save functionality
enabled = true
# Delay before triggering save (seconds)
save_delay = 2
# Log save events
log_saves = true
```

### VWE_DataExporter
**Purpose**: Exports world data (biomes, heightmaps, structures) in real-time.

**Key Features**:
- Real-time biome data extraction
- Heightmap generation and export
- Structure detection and mapping
- JSON/PNG export formats
- Configurable export intervals
- **Status**: ⏳ Coroutines start but not completing (under investigation)

**Configuration**:
```ini
[DataExporter]
# Enable/disable data export
enabled = true
# Export format: json, png, both
export_format = both
# Export interval (seconds, 0 = on-demand)
export_interval = 0
# Export directory (relative to Valheim root)
export_dir = ./world_data
# Log export events
log_exports = true

[BiomeExport]
# Export biome data
enabled = true
# Resolution for biome maps
resolution = 2048

[HeightmapExport]
# Export heightmap data
enabled = true
# Resolution for heightmaps
resolution = 2048
```

## Docker Integration

### Custom Valheim Server Image
The `docker/Dockerfile` creates a custom Valheim server image with:
- BepInEx pre-installed and configured
- VWE plugins pre-loaded
- Optimized for world generation (no player management)
- Health checks for plugin status

### Docker Compose Override
The `docker-compose.override.yml` extends the main compose file with:
- BepInEx-enabled Valheim server
- Plugin volume mounts
- Environment variables for BepInEx
- Health checks and monitoring

## Usage

### Quick Start (Using Pre-Compiled Plugins)

**No build required** - plugins are already compiled in `bepinex/plugins/`:

```bash
# From repo root
cd docker/bepinex

# Run BepInEx approach (isolated from backend)
docker compose -f docker-compose.bepinex.yml --profile bepinex up

# Monitor logs for plugin activity
docker logs -f vwe-valheim-bepinex | grep -E "(VWE|BepInEx)"

# Check for world files
ls -la ../../data/seeds/hkLycKKCMI/worlds_local/

# Check for exported data
ls -la ../../data/seeds/hkLycKKCMI/world_data/
```

### Development Workflow (Modifying Plugins)

**Only needed if changing plugin source code:**

1. **Setup assembly files** (one-time):
   ```bash
   # See ASSEMBLY_EXTRACTION_GUIDE.md for extraction methods
   # Required files in bepinex/plugins/:
   # - Assembly-CSharp.dll
   # - UnityEngine.dll (and modules)
   # - BepInEx.dll, BepInEx.Harmony.dll
   ```

2. **Modify plugin source**:
   ```bash
   # Edit files in src/VWE_AutoSave/ or src/VWE_DataExporter/
   ```

3. **Build plugins**:
   ```bash
   cd bepinex
   make build
   # Outputs updated DLLs to plugins/ directory
   ```

4. **Test changes**:
   ```bash
   # Restart container to load new plugins
   cd ../docker/bepinex
   docker compose -f docker-compose.bepinex.yml down
   docker compose -f docker-compose.bepinex.yml --profile bepinex up
   ```

### Integration with Backend (Future)

**Current state:** Fully isolated for testing

**Future integration:** Once validated, the backend's `world_generator.py` can optionally use this approach by:
- Checking for `BEPINEX_APPROACH=true` env var
- Using different container orchestration
- Expecting exported data in `/config/world_data/`

**No changes to backend until BepInEx approach is proven reliable.**

## Configuration

### Environment Variables

**Configured in `docker/bepinex/docker-compose.bepinex.yml`:**

```bash
# Enable BepInEx (lloesche native support)
BEPINEX=true

# VWE Plugin Configuration (read by custom plugins)
VWE_AUTOSAVE_ENABLED=true
VWE_AUTOSAVE_DELAY=2
VWE_DATAEXPORT_ENABLED=true
VWE_DATAEXPORT_FORMAT=both
VWE_DATAEXPORT_DIR=/config/world_data

# Inherits from .env:
# - HOST_DATA_DIR
# - WORLD_NAME
# - HOST_UID/HOST_GID (mapped to PUID/PGID)
```

### Plugin Settings

Each plugin can be configured via:
- **Environment variables** (runtime configuration)
- **Config files** (persistent settings)
- **Command line arguments** (override settings)

## Maintenance

### Plugin Updates

1. **Modify source code** in `src/` directories
2. **Rebuild plugins** using `dotnet build`
3. **Copy DLLs** to `plugins/` directory
4. **Rebuild Docker image** with new plugins
5. **Deploy updated image** to production

### Configuration Updates

1. **Modify config files** in `config/` directory
2. **Update environment variables** in `.env`
3. **Restart containers** to apply changes

### Debugging

1. **Check plugin logs**:
   ```bash
   docker logs valheim-server 2>&1 | grep -E "(VWE|BepInEx)"
   ```

2. **Verify plugin loading**:
   ```bash
   docker exec valheim-server ls -la /valheim/BepInEx/plugins/
   ```

3. **Test plugin functionality**:
   ```bash
   # Check if auto-save is working
   docker logs valheim-server 2>&1 | grep "Auto-save triggered"
   
   # Check if data export is working
   docker exec valheim-server ls -la /valheim/world_data/
   ```

### Troubleshooting

**Common Issues**:

1. **"Unable to find package BepInEx.Core"**:
   - **Cause**: Missing BepInEx assembly files
   - **Fix**: Download BepInEx runtime and place in `bepinex/plugins/`
   - **Check**: `ls -la bepinex/plugins/` should show BepInEx.dll

2. **"Assembly-CSharp not found"**:
   - **Cause**: Missing Valheim game assemblies
   - **Fix**: Extract from Valheim installation or download from Thunderstore
   - **Check**: `ls -la bepinex/plugins/` should show Assembly-CSharp.dll

3. **"dotnet command not found"**:
   - **Cause**: .NET Framework 4.8 SDK not installed
   - **Fix**: Install .NET Framework 4.8 SDK
   - **Check**: `dotnet --version` should show 4.8.x

4. **Plugins not loading**:
   - Check BepInEx version compatibility
   - Verify DLL files are in correct location
   - Check file permissions

5. **Auto-save not working**:
   - Verify `VWE_AutoSave.dll` is loaded
   - Check configuration settings
   - Monitor logs for errors

6. **Data export failing**:
   - Check export directory permissions
   - Verify plugin configuration
   - Monitor memory usage (large exports)

## Performance Benefits

- **Generation time**: 30-60 seconds (vs 2-3 minutes)
- **Data availability**: Real-time (vs post-generation)
- **Resource usage**: Lower (no 20-30 minute waits)
- **Reliability**: Higher (programmatic vs timing-based)

## Security Considerations

- **Plugin isolation**: BepInEx runs in separate process
- **File access**: Limited to Valheim data directory
- **Network access**: None (plugins are local-only)
- **Code signing**: Plugins should be signed for production

## Future Enhancements

- **Additional data exporters** (vegetation, ore deposits)
- **Real-time map generation** (eliminate MakeFwl dependency)
- **Performance monitoring** (generation metrics)
- **Plugin hot-reloading** (development mode)
- **Configuration UI** (web-based settings management)
