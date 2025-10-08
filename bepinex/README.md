# BepInEx Integration for Valheim World Engine

This directory contains BepInEx plugins and Docker configuration for optimized Valheim world generation and data export.

## Prerequisites

### Required Software
- **.NET Framework 4.8 SDK** (not .NET Core/5+)
- **Docker** (for extracting Valheim assemblies)
- **Git** (for cloning repositories)

### Required Assembly Files
**⚠️ Manual Setup Required**: The following files need to be obtained manually and placed in `bepinex/plugins/`:

**BepInEx Runtime:**
- `BepInEx.dll`
- `BepInEx.Harmony.dll` 
- `BepInEx.MonoMod.dll`

**Valheim Game Assemblies:**
- `Assembly-CSharp.dll` (Valheim's main game assembly)
- `UnityEngine.dll` and related modules

**Quick Setup:**
```bash
# Install .NET Framework 4.8 SDK
sudo apt update && sudo apt install dotnet-sdk-4.8

# Install BepInEx templates (already done)
dotnet new -i BepInEx.Templates --nuget-source https://nuget.bepinex.dev/v3/index.json

# Get assembly files (choose one method):
# Method 1: Download from Thunderstore
wget "https://thunderstore.io/package/download/BepInEx/BepInExPack_Valheim/5.4.2202/"

# Method 2: Extract from Valheim installation
cp /path/to/valheim/valheim_server_Data/Managed/Assembly-CSharp.dll bepinex/plugins/
cp /path/to/valheim/valheim_server_Data/Managed/UnityEngine*.dll bepinex/plugins/

# Method 3: Use existing Valheim server installation
# Copy files from your Valheim server directory
```

## Overview

BepInEx provides direct access to Valheim's internal systems, enabling:
- **Programmatic world saves** (eliminates 20-30 minute autosave wait)
- **Real-time data export** (biomes, heightmaps, structures)
- **Event-driven world generation** (hooks into world completion events)
- **Performance optimization** (30-60 second generation vs 2-3 minutes)

## Directory Structure

```
bepinex/
├── README.md                    # This file
├── docker/                      # Docker configuration
│   ├── Dockerfile              # Custom Valheim server with BepInEx
│   └── docker-compose.override.yml
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
├── plugins/                    # Compiled plugin binaries
│   ├── VWE_AutoSave.dll
│   └── VWE_DataExporter.dll
└── config/                     # BepInEx configuration
    ├── BepInEx.cfg
    └── VWE_DataExporter.cfg
```

## Plugins

### VWE_AutoSave
**Purpose**: Triggers immediate world saves when world generation completes.

**Key Features**:
- Hooks into `ZoneSystem.Start` event (world generation complete)
- Calls `ZNet.instance.ConsoleSave()` programmatically
- Configurable save triggers and timing
- Logs save events for debugging

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

### Prerequisites Check
Before building, ensure you have the required assembly files in `bepinex/plugins/`:

```bash
# Check for required files
ls -la bepinex/plugins/
# Should show: BepInEx.dll, BepInEx.Harmony.dll, BepInEx.MonoMod.dll, Assembly-CSharp.dll, UnityEngine.dll
```

### Development Workflow

1. **Setup assembly files** (if not already done):
   ```bash
   # Download BepInEx from Thunderstore or extract from Valheim installation
   # Place files in bepinex/plugins/ directory
   ```

2. **Build plugins**:
   ```bash
   cd bepinex
   make build
   # Or manually:
   # cd src/VWE_AutoSave && dotnet build -c Release
   # cd ../VWE_DataExporter && dotnet build -c Release
   ```

3. **Build Docker image**:
   ```bash
   cd bepinex
   make docker-build
   # Or manually:
   # cd docker && docker build -t vwe/valheim-server-bepinex:latest .
   ```

4. **Update world_generator.py**:
   - Change `VALHEIM_IMAGE` to `vwe/valheim-server-bepinex:latest`
   - Add BepInEx-specific environment variables
   - Update expected output paths for exported data

### Production Deployment

1. **Build and push image**:
   ```bash
   docker build -t vwe/valheim-server-bepinex:latest bepinex/docker/
   docker push vwe/valheim-server-bepinex:latest
   ```

2. **Update configuration**:
   - Set `VALHEIM_IMAGE=vwe/valheim-server-bepinex:latest` in `.env`
   - Configure BepInEx settings in `bepinex/config/`

3. **Deploy**:
   ```bash
   docker-compose up -d
   ```

## Configuration

### Environment Variables

```bash
# BepInEx Configuration
BEPINEX_ENABLED=true
BEPINEX_LOG_LEVEL=Info
BEPINEX_LOG_CONSOLE=true
BEPINEX_LOG_FILE=true

# Plugin Configuration
VWE_AUTOSAVE_ENABLED=true
VWE_AUTOSAVE_DELAY=2
VWE_DATAEXPORT_ENABLED=true
VWE_DATAEXPORT_FORMAT=both
VWE_DATAEXPORT_DIR=./world_data
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
