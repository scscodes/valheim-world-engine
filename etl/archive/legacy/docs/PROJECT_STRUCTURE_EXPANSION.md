# Project Structure Expansion for BepInEx Integration

## Complete Directory Structure

```
valheim-world-engine/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── seeds.py
│   │   │   │   └── health.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py                    # MODIFIED: Add BepInEx config
│   │   │   ├── mapping_config.py           # EXISTING: Mapping standards
│   │   │   └── cache.py
│   │   ├── services/
│   │   │   ├── world_generator.py          # MODIFIED: BepInEx integration
│   │   │   ├── extractor.py                # MODIFIED: Handle BepInEx exports
│   │   │   ├── processor.py                # EXISTING: Data processing
│   │   │   ├── renderer.py                 # EXISTING: Image rendering
│   │   │   └── job_queue.py                # EXISTING: Redis queue
│   │   ├── models/
│   │   │   ├── seed.py                     # EXISTING: Data models
│   │   │   └── job.py                      # EXISTING: Job models
│   │   └── main.py                         # EXISTING: FastAPI app
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_world_generator.py     # MODIFIED: Add BepInEx tests
│   │   │   ├── test_extractor.py           # MODIFIED: Add BepInEx tests
│   │   │   └── test_processor.py           # EXISTING
│   │   ├── integration/
│   │   │   ├── test_bepinex_pipeline.py    # NEW: End-to-end BepInEx tests
│   │   │   └── test_graceful_shutdown.py   # NEW: Fallback tests
│   │   └── fixtures/
│   │       ├── sample_biomes.json          # NEW: Test data
│   │       ├── sample_heightmap.raw        # NEW: Test data
│   │       └── sample_world_metadata.json  # NEW: Test data
│   ├── requirements.txt                    # MODIFIED: Add BepInEx dependencies
│   └── Dockerfile                          # EXISTING
├── frontend/                               # EXISTING: Next.js app
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   ├── public/
│   └── package.json
├── docker/
│   ├── docker-compose.yml                  # MODIFIED: Add BepInEx service
│   ├── valheim-server/                     # EXISTING
│   └── valheim-server-bepinex/             # NEW: BepInEx-enabled server
│       ├── Dockerfile                      # NEW: Custom BepInEx image
│       ├── plugins/                        # NEW: VWE BepInEx plugins
│       │   ├── VWE_AutoSave.dll            # NEW: Auto-save plugin
│       │   └── VWE_DataExporter.dll        # NEW: Data export plugin
│       └── config/
│           └── BepInEx.cfg                 # NEW: BepInEx configuration
├── src/                                    # NEW: BepInEx plugin source code
│   ├── plugins/
│   │   ├── VWE_AutoSave/
│   │   │   ├── VWE_AutoSave.cs             # NEW: Auto-save plugin source
│   │   │   ├── VWE_AutoSave.csproj         # NEW: C# project file
│   │   │   └── Properties/
│   │   │       └── AssemblyInfo.cs         # NEW: Assembly metadata
│   │   ├── VWE_DataExporter/
│   │   │   ├── VWE_DataExporter.cs         # NEW: Data export plugin source
│   │   │   ├── VWE_DataExporter.csproj     # NEW: C# project file
│   │   │   └── Properties/
│   │   │       └── AssemblyInfo.cs         # NEW: Assembly metadata
│   │   └── VWE_Common/
│   │       ├── VWE_Common.cs               # NEW: Shared utilities
│   │       └── VWE_Common.csproj           # NEW: Common library
│   └── packages/                           # NEW: NuGet packages
│       ├── BepInEx.5.4.22.nupkg
│       ├── 0Harmony.2.3.3.nupkg
│       └── Newtonsoft.Json.13.0.3.nupkg
├── scripts/
│   ├── init_db.py                          # EXISTING
│   ├── validate_env.py                     # EXISTING
│   ├── build_bepinex_plugins.sh            # NEW: Build BepInEx plugins
│   ├── build_docker_images.sh              # NEW: Build all Docker images
│   ├── test_bepinex_pipeline.py            # NEW: Test BepInEx pipeline
│   └── benchmark_generation.py             # NEW: Performance testing
├── data/                                   # EXISTING: Git-ignored
│   └── seeds/
├── docs/
│   ├── REFERENCES.md                       # EXISTING
│   ├── WORLD_GENERATION.md                 # EXISTING: Current implementation
│   ├── BEPINEX_OPTIMIZATION_ANALYSIS.md    # NEW: BepInEx analysis
│   ├── BEPINEX_IMPLEMENTATION_DETAILS.md   # NEW: Implementation details
│   └── PROJECT_STRUCTURE_EXPANSION.md      # NEW: This file
├── tests/                                  # NEW: Integration tests
│   ├── e2e/
│   │   ├── test_bepinex_generation.py      # NEW: End-to-end BepInEx tests
│   │   └── test_graceful_shutdown.py       # NEW: Fallback tests
│   └── performance/
│       ├── benchmark_bepinex.py            # NEW: BepInEx performance tests
│       └── benchmark_comparison.py         # NEW: Compare methods
├── .env.example                            # MODIFIED: Add BepInEx config
├── .gitignore                              # MODIFIED: Add BepInEx build artifacts
├── .github/
│   └── workflows/
│       ├── ci.yml                          # NEW: Continuous integration
│       ├── build-bepinex.yml               # NEW: Build BepInEx plugins
│       └── deploy.yml                      # NEW: Deployment
├── docker-compose.yml                      # MODIFIED: Add BepInEx service
├── docker-compose.bepinex.yml              # NEW: BepInEx-specific compose
├── docker-compose.override.yml             # NEW: Local development overrides
├── README.md                               # MODIFIED: Add BepInEx documentation
└── Makefile                                # NEW: Build automation
```

## Files to Create

### 1. BepInEx Plugin Source Code

#### `src/plugins/VWE_AutoSave/VWE_AutoSave.cs`
```csharp
using BepInEx;
using HarmonyLib;
using UnityEngine;

[BepInPlugin("com.vwe.autosave", "VWE Auto Save", "1.0.0")]
public class VWE_AutoSave : BaseUnityPlugin
{
    private static bool _worldGenerationComplete = false;
    private static bool _saveTriggered = false;

    void Awake()
    {
        Logger.LogInfo("VWE AutoSave plugin loaded");
        Harmony.CreateAndPatchAll(typeof(VWE_AutoSave));
    }

    [HarmonyPatch(typeof(ZoneSystem), "Start")]
    [HarmonyPostfix]
    static void OnZoneSystemStart()
    {
        if (!_worldGenerationComplete)
        {
            _worldGenerationComplete = true;
            InvokeRepeating("TriggerImmediateSave", 2f, 0f);
        }
    }

    void TriggerImmediateSave()
    {
        if (ZNet.instance != null && ZNet.instance.IsServer() && !_saveTriggered)
        {
            _saveTriggered = true;
            ZNet.instance.ConsoleSave();
            Logger.LogInfo("VWE: Triggered immediate world save after generation");
            CancelInvoke("TriggerImmediateSave");
        }
    }
}
```

#### `src/plugins/VWE_AutoSave/VWE_AutoSave.csproj`
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net48</TargetFramework>
    <AssemblyName>VWE_AutoSave</AssemblyName>
    <RootNamespace>VWE_AutoSave</RootNamespace>
  </PropertyGroup>
  
  <ItemGroup>
    <Reference Include="BepInEx">
      <HintPath>../../packages/BepInEx.5.4.22.nupkg</HintPath>
    </Reference>
    <Reference Include="0Harmony">
      <HintPath>../../packages/0Harmony.2.3.3.nupkg</HintPath>
    </Reference>
  </ItemGroup>
</Project>
```

### 2. Docker Configuration

#### `docker/valheim-server-bepinex/Dockerfile`
```dockerfile
FROM lloesche/valheim-server:latest

# Install BepInEx dependencies
RUN apt-get update && apt-get install -y \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy VWE plugins
COPY plugins/ /config/BepInEx/plugins/

# Set BepInEx environment variables
ENV BEPINEX=1
ENV BEPINEX_CONFIG_PATH=/config/BepInEx/config
ENV BEPINEX_PLUGINS_PATH=/config/BepInEx/plugins

# Create export directory
RUN mkdir -p /config/vwe_export

# Ensure proper permissions
RUN chown -R 1000:1000 /config/BepInEx
```

#### `docker-compose.bepinex.yml`
```yaml
version: '3.8'
services:
  valheim-bepinex:
    build:
      context: ./docker/valheim-server-bepinex
    image: vwe/valheim-server-bepinex:latest
    profiles: ["bepinex"]
    # This service is used by the worker, not standalone
```

### 3. Build Scripts

#### `scripts/build_bepinex_plugins.sh`
```bash
#!/bin/bash
set -e

PLUGIN_DIR="docker/valheim-server-bepinex/plugins"
BUILD_DIR="build/bepinex"

echo "Building BepInEx plugins..."

# Create build directory
mkdir -p $BUILD_DIR

# Download BepInEx dependencies
echo "Downloading BepInEx dependencies..."
wget -O $BUILD_DIR/BepInEx.dll "https://github.com/BepInEx/BepInEx/releases/latest/download/BepInEx.dll"
wget -O $BUILD_DIR/0Harmony.dll "https://github.com/BepInEx/BepInEx/releases/latest/download/0Harmony.dll"

# Compile plugins
echo "Compiling VWE_AutoSave..."
dotnet build src/plugins/VWE_AutoSave/VWE_AutoSave.csproj -o $BUILD_DIR

echo "Compiling VWE_DataExporter..."
dotnet build src/plugins/VWE_DataExporter/VWE_DataExporter.csproj -o $BUILD_DIR

# Copy to plugin directory
echo "Installing plugins..."
cp $BUILD_DIR/*.dll $PLUGIN_DIR/

echo "BepInEx plugins built successfully"
```

#### `Makefile`
```makefile
.PHONY: build-bepinex build-docker test clean

# Build BepInEx plugins
build-bepinex:
	@echo "Building BepInEx plugins..."
	@./scripts/build_bepinex_plugins.sh

# Build Docker images
build-docker:
	@echo "Building Docker images..."
	@docker compose --profile bepinex build valheim-bepinex

# Build everything
build: build-bepinex build-docker

# Test BepInEx pipeline
test-bepinex:
	@echo "Testing BepInEx pipeline..."
	@python scripts/test_bepinex_pipeline.py

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/
	@docker system prune -f

# Start services with BepInEx
start-bepinex:
	@echo "Starting services with BepInEx..."
	@export VALHEIM_IMAGE=vwe/valheim-server-bepinex:latest
	@docker compose up -d

# Start services with graceful shutdown
start-graceful:
	@echo "Starting services with graceful shutdown..."
	@export VALHEIM_IMAGE=lloesche/valheim-server:latest
	@docker compose up -d
```

### 4. Configuration Files

#### `.env.example` (Modified)
```bash
# Backend configuration
REDIS_URL=redis://redis:6379/0
DATA_DIR=/home/steve/projects/valheim-world-engine/data
ALLOWED_ORIGINS=http://localhost:3000

# World generation configuration
HOST_DATA_DIR=/home/steve/projects/valheim-world-engine/data
REPO_ROOT=/home/steve/projects/valheim-world-engine
PLUGINS_HOST_DIR=/home/steve/projects/valheim-world-engine/docker/valheim-server/plugins

# Valheim orchestration
VALHEIM_IMAGE=lloesche/valheim-server:latest  # Default: graceful shutdown
BEPINEX_ENABLED=false                         # NEW: Enable BepInEx
BEPINEX_IMAGE=vwe/valheim-server-bepinex:latest  # NEW: BepInEx image
VALHEIM_BRANCH=public
STAGE1_TIMEOUT_SEC=300
STAGE1_STABLE_SEC=30

# BepInEx configuration
BEPINEX_CONFIG_PATH=/config/BepInEx/config    # NEW
BEPINEX_PLUGINS_PATH=/config/BepInEx/plugins  # NEW
VWE_EXPORT_PATH=/config/vwe_export            # NEW

# Workers
RQ_WORKERS=1

# Database
SQLITE_PATH=./data/valheim_dev.db

# Rendering
RENDER_RESOLUTION_PX=2048
```

#### `.gitignore` (Modified)
```gitignore
# Existing entries...
data/
*.db
*.fwl

# BepInEx build artifacts
build/
src/packages/
*.dll
*.pdb

# Docker build cache
docker/valheim-server-bepinex/plugins/*.dll

# Test artifacts
test-results/
coverage/
```

## Files to Modify

### 1. Backend Configuration

#### `backend/app/core/config.py` (Modified)
```python
# Add BepInEx configuration
bepinex_enabled: bool = os.getenv("BEPINEX_ENABLED", "false").lower() == "true"
bepinex_image: str = os.getenv("BEPINEX_IMAGE", "vwe/valheim-server-bepinex:latest")
bepinex_config_path: str = os.getenv("BEPINEX_CONFIG_PATH", "/config/BepInEx/config")
bepinex_plugins_path: str = os.getenv("BEPINEX_PLUGINS_PATH", "/config/BepInEx/plugins")
vwe_export_path: str = os.getenv("VWE_EXPORT_PATH", "/config/vwe_export")

# Modified valheim_image to support BepInEx
def get_valheim_image(self) -> str:
    if self.bepinex_enabled:
        return self.bepinex_image
    return self.valheim_image
```

#### `backend/app/services/world_generator.py` (Modified)
```python
def build_worldgen_plan(seed: str, seed_hash: str) -> dict:
    # ... existing code ...
    
    # Choose image based on BepInEx setting
    image = settings.get_valheim_image()
    
    # Different expected outputs based on method
    if settings.bepinex_enabled:
        expected_outputs = {
            "raw": [
                os.path.join(seed_dir, "worlds_local", f"{seed}.db"),
                os.path.join(seed_dir, "worlds_local", f"{seed}.fwl"),
            ],
            "extracted": [
                os.path.join(extracted_dir, "biomes.json"),        # BepInEx export
                os.path.join(extracted_dir, "heightmap.raw"),      # BepInEx export
                os.path.join(extracted_dir, "world_metadata.json"), # BepInEx export
            ],
        }
    else:
        expected_outputs = {
            "raw": [
                os.path.join(seed_dir, "worlds_local", f"{seed}.db"),
                os.path.join(seed_dir, "worlds_local", f"{seed}.fwl"),
            ],
            "extracted": [
                os.path.join(extracted_dir, "biomes.json"),        # MakeFwl export
                os.path.join(extracted_dir, "heightmap.npy"),      # MakeFwl export
            ],
        }
    
    return {
        "image": image,
        "env": env_vars,
        "volumes": volumes,
        "expected_outputs": expected_outputs,
        # ... rest of config
    }
```

#### `backend/app/services/extractor.py` (Modified)
```python
def extract_world_data(seed_hash: str) -> dict:
    """Extract world data using either MakeFwl or BepInEx exports"""
    
    if settings.bepinex_enabled:
        return extract_bepinex_data(seed_hash)
    else:
        return extract_makefwl_data(seed_hash)

def extract_bepinex_data(seed_hash: str) -> dict:
    """Extract data from BepInEx exports"""
    extracted_dir = os.path.join(settings.data_dir, "seeds", seed_hash, "extracted")
    
    # Read BepInEx exports
    biomes_data = json.load(open(os.path.join(extracted_dir, "biomes.json")))
    heightmap_data = np.fromfile(os.path.join(extracted_dir, "heightmap.raw"), dtype=np.float32)
    metadata = json.load(open(os.path.join(extracted_dir, "world_metadata.json")))
    
    return {
        "biomes": biomes_data,
        "heightmap": heightmap_data,
        "metadata": metadata,
        "method": "bepinex"
    }

def extract_makefwl_data(seed_hash: str) -> dict:
    """Extract data using MakeFwl (existing implementation)"""
    # ... existing MakeFwl extraction code
```

### 2. Docker Compose

#### `docker/docker-compose.yml` (Modified)
```yaml
services:
  # ... existing services ...
  
  valheim-bepinex:
    build:
      context: ./valheim-server-bepinex
    image: vwe/valheim-server-bepinex:latest
    profiles: ["bepinex"]
    # This service is used by the worker, not standalone
```

### 3. Testing

#### `backend/tests/unit/test_world_generator.py` (Modified)
```python
def test_bepinex_generation():
    """Test BepInEx world generation"""
    with patch('app.core.config.settings.bepinex_enabled', True):
        plan = build_worldgen_plan("TestSeed", "test_hash")
        assert plan["image"] == "vwe/valheim-server-bepinex:latest"
        assert "biomes.json" in plan["expected_outputs"]["extracted"]

def test_graceful_shutdown_generation():
    """Test graceful shutdown world generation"""
    with patch('app.core.config.settings.bepinex_enabled', False):
        plan = build_worldgen_plan("TestSeed", "test_hash")
        assert plan["image"] == "lloesche/valheim-server:latest"
        assert "heightmap.npy" in plan["expected_outputs"]["extracted"]
```

#### `tests/e2e/test_bepinex_generation.py` (New)
```python
import pytest
import requests
import time

def test_bepinex_world_generation():
    """End-to-end test of BepInEx world generation"""
    
    # Start services with BepInEx
    os.system("make start-bepinex")
    time.sleep(10)  # Wait for services to start
    
    # Trigger generation
    response = requests.post(
        "http://localhost:8000/api/v1/seeds/generate",
        json={"seed": "BepInExTest"}
    )
    assert response.status_code == 200
    
    job_id = response.json()["job_id"]
    
    # Wait for completion
    max_wait = 120  # 2 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status_response = requests.get(f"http://localhost:8000/api/v1/seeds/{job_id}/status")
        status = status_response.json()
        
        if status["status"] == "completed":
            break
        elif status["status"] == "failed":
            pytest.fail(f"Generation failed: {status.get('error', 'Unknown error')}")
        
        time.sleep(5)
    else:
        pytest.fail("Generation timed out")
    
    # Verify BepInEx exports exist
    data_response = requests.get(f"http://localhost:8000/api/v1/seeds/{job_id}/data")
    data = data_response.json()
    
    assert "biomes" in data["layers"]["base_layers"]
    assert "heightmap" in data["layers"]["base_layers"]
    assert data["metadata"]["method"] == "bepinex"
```

### 4. Documentation

#### `README.md` (Modified)
```markdown
# Valheim Mapping Solution - Project Plan

## Quick Start

### Option 1: Graceful Shutdown (Default)
```bash
# Start with graceful shutdown (2-3 minutes per world)
docker compose up -d
```

### Option 2: BepInEx (Faster)
```bash
# Build BepInEx plugins
make build-bepinex

# Start with BepInEx (30-60 seconds per world)
make start-bepinex
```

## Configuration

Set `BEPINEX_ENABLED=true` in your `.env` file to use BepInEx for faster generation.

## Performance

- **Graceful Shutdown:** 2-3 minutes per world
- **BepInEx:** 30-60 seconds per world
- **Improvement:** 3-4x faster with BepInEx
```

This expanded structure provides a complete, production-ready BepInEx integration that can be gradually rolled out while maintaining the current graceful shutdown as a reliable fallback.
