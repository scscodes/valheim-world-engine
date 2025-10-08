# BepInEx Save Trigger Plugin - Complete Guide

## Overview

This guide covers creating a custom BepInEx plugin for Valheim that triggers world saves programmatically. This is specifically for your ETL pipeline use case with the `lloesche/valheim-server` Docker container.

---

## Prerequisites & Downloads

### Required Software

1. **.NET SDK 6.0 or newer**
   - Download: https://dotnet.microsoft.com/download
   - Verify installation: `dotnet --version`

2. **Visual Studio Community 2022** (or VS Code)
   - VS Community: https://visualstudio.microsoft.com/vs/community/
   - VS Code: https://code.visualstudio.com/

3. **BepInEx Pack for Valheim**
   - Download: https://thunderstore.io/c/valheim/p/denikson/BepInExPack_Valheim/
   - Latest version: 5.4.23.3 (as of writing)
   - Manual download the `.zip` file

4. **BepInEx Plugin Templates**
   - Install via command line (after .NET SDK installed):
   ```bash
   dotnet new install BepInEx.Templates::2.0.0-be.4 --nuget-source https://nuget.bepinex.dev/v3/index.json
   ```

### Required Game Files

From your Valheim dedicated server installation, you need:
- `valheim_server_Data/Managed/assembly_valheim.dll` (contains game code)
- `valheim_server_Data/Managed/UnityEngine.CoreModule.dll`
- `BepInEx/core/BepInEx.dll` (after installing BepInEx pack)
- `BepInEx/core/0Harmony.dll` (for patching, if needed)

---

## Project Setup

### Step 1: Create Plugin Project

```bash
# Create project directory
mkdir ValheimSaveTrigger
cd ValheimSaveTrigger

# Create BepInEx plugin from template
dotnet new bepinex5plugin -n ValheimSaveTrigger -T netstandard2.0
```

### Step 2: Project Structure

Your project should look like:
```
ValheimSaveTrigger/
├── ValheimSaveTrigger.csproj
├── Plugin.cs
├── libs/                        # Create this folder
│   ├── assembly_valheim.dll     # Copy from server
│   ├── UnityEngine.CoreModule.dll
│   ├── BepInEx.dll
│   └── 0Harmony.dll
└── bin/
    └── Debug/
        └── netstandard2.0/
```

### Step 3: Configure Project File

Edit `ValheimSaveTrigger.csproj`:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>netstandard2.0</TargetFramework>
    <AssemblyName>ValheimSaveTrigger</AssemblyName>
    <LangVersion>latest</LangVersion>
    <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
  </PropertyGroup>

  <ItemGroup>
    <!-- BepInEx dependencies -->
    <PackageReference Include="BepInEx.Core" Version="5.*" />
    <PackageReference Include="BepInEx.PluginInfoProps" Version="1.*" />
    <PackageReference Include="UnityEngine.Modules" Version="2022.3.17" />
  </ItemGroup>

  <ItemGroup>
    <!-- Game-specific assemblies -->
    <Reference Include="assembly_valheim">
      <HintPath>libs/assembly_valheim.dll</HintPath>
      <Private>false</Private>
    </Reference>
    <Reference Include="UnityEngine.CoreModule">
      <HintPath>libs/UnityEngine.CoreModule.dll</HintPath>
      <Private>false</Private>
    </Reference>dotnet new -i BepInEx.Templates --nuget-source https://nuget.bepinex.dev/v3/index.json
  </ItemGroup>

  <!-- Copy output to BepInEx plugins folder for testing -->
  <Target Name="CopyToPlugins" AfterTargets="Build">
    <Copy SourceFiles="$(TargetPath)" DestinationFolder="$(VALHEIM_INSTALL)\BepInEx\plugins\" Condition="Exists('$(VALHEIM_INSTALL)')" />
  </Target>
</Project>
```

---

## Plugin Implementation

### Approach 1: File System Watcher (Recommended for Docker)

This approach watches for a trigger file and saves when detected.

**Plugin.cs:**

```csharp
using System;
using System.IO;
using BepInEx;
using BepInEx.Logging;
using UnityEngine;

namespace ValheimSaveTrigger
{
    [BepInPlugin(PluginGUID, PluginName, PluginVersion)]
    public class SaveTriggerPlugin : BaseUnityPlugin
    {
        public const string PluginGUID = "com.yourname.valheim.savetrigger";
        public const string PluginName = "Valheim Save Trigger";
        public const string PluginVersion = "1.0.0";

        private static ManualLogSource _logger;
        private FileSystemWatcher _watcher;
        private string _triggerPath;
        private bool _saveRequested = false;

        void Awake()
        {
            _logger = Logger;
            _logger.LogInfo($"{PluginName} v{PluginVersion} loaded!");

            // Set up trigger file path (mounted volume in Docker)
            _triggerPath = Path.Combine(
                Environment.GetEnvironmentVariable("TRIGGER_PATH") ?? "/config/trigger",
                "save.trigger"
            );

            string triggerDir = Path.GetDirectoryName(_triggerPath);
            
            // Ensure directory exists
            if (!Directory.Exists(triggerDir))
            {
                Directory.CreateDirectory(triggerDir);
                _logger.LogInfo($"Created trigger directory: {triggerDir}");
            }

            // Setup file watcher
            SetupFileWatcher(triggerDir);
            
            _logger.LogInfo($"Monitoring for save trigger at: {_triggerPath}");
        }

        void SetupFileWatcher(string path)
        {
            _watcher = new FileSystemWatcher(path)
            {
                Filter = "save.trigger",
                NotifyFilter = NotifyFilters.FileName | NotifyFilters.CreationTime
            };

            _watcher.Created += OnTriggerFileCreated;
            _watcher.EnableRaisingEvents = true;
        }

        void OnTriggerFileCreated(object sender, FileSystemEventArgs e)
        {
            _logger.LogInfo("Save trigger detected!");
            _saveRequested = true;
        }

        void Update()
        {
            // Process save request on main thread
            if (_saveRequested && ZNet.instance != null && ZNet.instance.IsServer())
            {
                _saveRequested = false;
                TriggerWorldSave();
            }
        }

        void TriggerWorldSave()
        {
            try
            {
                _logger.LogInfo("Triggering world save...");

                // Save the world using Valheim's save system
                if (ZoneSystem.instance != null)
                {
                    ZoneSystem.instance.Save();
                    _logger.LogInfo("ZoneSystem saved");
                }

                if (RandEventSystem.instance != null)
                {
                    RandEventSystem.instance.Save();
                    _logger.LogInfo("RandEventSystem saved");
                }

                // Write completion file
                string completePath = Path.Combine(
                    Path.GetDirectoryName(_triggerPath),
                    "save.complete"
                );
                
                File.WriteAllText(completePath, DateTime.UtcNow.ToString("o"));
                _logger.LogInfo($"Save complete! Wrote confirmation to {completePath}");

                // Cleanup trigger file
                if (File.Exists(_triggerPath))
                {
                    File.Delete(_triggerPath);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error during save: {ex}");
            }
        }

        void OnDestroy()
        {
            _watcher?.Dispose();
        }
    }
}
```

### Approach 2: HTTP Endpoint (More Advanced)

Requires additional NuGet package for HTTP server.

**Add to .csproj:**
```xml
<PackageReference Include="EmbedIO" Version="3.5.2" />
```

**Plugin.cs with HTTP endpoint:**

```csharp
using System;
using System.Threading.Tasks;
using BepInEx;
using BepInEx.Logging;
using EmbedIO;
using EmbedIO.Actions;
using UnityEngine;

namespace ValheimSaveTrigger
{
    [BepInPlugin(PluginGUID, PluginName, PluginVersion)]
    public class SaveTriggerPlugin : BaseUnityPlugin
    {
        public const string PluginGUID = "com.yourname.valheim.savetrigger";
        public const string PluginName = "Valheim Save Trigger HTTP";
        public const string PluginVersion = "1.0.0";

        private static ManualLogSource _logger;
        private WebServer _server;
        private bool _saveRequested = false;

        void Awake()
        {
            _logger = Logger;
            _logger.LogInfo($"{PluginName} v{PluginVersion} loaded!");

            // Start HTTP server
            int port = int.Parse(Environment.GetEnvironmentVariable("TRIGGER_PORT") ?? "8080");
            StartHttpServer(port);
        }

        void StartHttpServer(int port)
        {
            _server = new WebServer(o => o
                .WithUrlPrefix($"http://+:{port}/")
                .WithMode(HttpListenerMode.EmbedIO))
                .WithAction("/save", HttpVerbs.Post, ctx =>
                {
                    _logger.LogInfo("HTTP save trigger received");
                    _saveRequested = true;
                    return ctx.SendStringAsync("Save requested", "text/plain", System.Text.Encoding.UTF8);
                })
                .WithAction("/health", HttpVerbs.Get, ctx =>
                {
                    return ctx.SendStringAsync("OK", "text/plain", System.Text.Encoding.UTF8);
                });

            _ = _server.RunAsync();
            _logger.LogInfo($"HTTP trigger server listening on port {port}");
        }

        void Update()
        {
            if (_saveRequested && ZNet.instance != null && ZNet.instance.IsServer())
            {
                _saveRequested = false;
                TriggerWorldSave();
            }
        }

        void TriggerWorldSave()
        {
            try
            {
                _logger.LogInfo("Triggering world save via HTTP...");

                if (ZoneSystem.instance != null)
                {
                    ZoneSystem.instance.Save();
                    _logger.LogInfo("World saved successfully");
                }

                if (RandEventSystem.instance != null)
                {
                    RandEventSystem.instance.Save();
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error during save: {ex}");
            }
        }

        void OnDestroy()
        {
            _server?.Dispose();
        }
    }
}
```

---

## Building the Plugin

```bash
# Build the project
dotnet build

# Output will be in:
# bin/Debug/netstandard2.0/ValheimSaveTrigger.dll
```

---

## Docker Integration

### Modified Dockerfile for lloesche/valheim-server

```dockerfile
FROM ghcr.io/lloesche/valheim-server:latest

# Install BepInEx
COPY BepInExPack_Valheim/ /opt/valheim/

# Copy custom save trigger plugin
COPY ValheimSaveTrigger.dll /opt/valheim/BepInEx/plugins/

# Create trigger directory
RUN mkdir -p /config/trigger

# Set environment variables for plugin
ENV TRIGGER_PATH=/config/trigger
ENV DOORSTOP_ENABLE=TRUE
ENV DOORSTOP_INVOKE_DLL_PATH=./BepInEx/core/BepInEx.Preloader.dll
ENV DOORSTOP_CORLIB_OVERRIDE_PATH=./unstripped_corlib
ENV LD_LIBRARY_PATH=./doorstop_libs:$LD_LIBRARY_PATH
ENV LD_PRELOAD=libdoorstop_x64.so:$LD_PRELOAD

# Modify startup to use BepInEx
COPY start_server_bepinex.sh /opt/valheim/
RUN chmod +x /opt/valheim/start_server_bepinex.sh

CMD ["/opt/valheim/start_server_bepinex.sh"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  valheim-generator:
    build: .
    container_name: valheim-worldgen-${WORLD_SEED:-default}
    restart: "no"
    
    volumes:
      - ./generated_worlds/${WORLD_SEED:-default}:/config
      - ./trigger:/config/trigger  # Mounted trigger directory
      - ./server_data:/opt/valheim
      
    environment:
      - WORLD_NAME=${WORLD_NAME:-WorldGen}
      - SERVER_NAME=Generator-${WORLD_SEED:-default}
      - SERVER_PASS=generate123
      - SERVER_PUBLIC=false
      - TRIGGER_PATH=/config/trigger
      
    ports:
      - "2456-2457:2456-2457/udp"
      
    healthcheck:
      test: ["CMD-SHELL", "test -f /config/worlds_local/${WORLD_NAME:-WorldGen}.fwl"]
      interval: 10s
      timeout: 5s
      retries: 30
      start_period: 120s
```

---

## Usage in ETL Pipeline

### Python Script to Trigger Save

```python
import time
import os
from pathlib import Path

def trigger_world_save(trigger_path="/path/to/trigger"):
    """Trigger a world save via file system"""
    trigger_file = Path(trigger_path) / "save.trigger"
    complete_file = Path(trigger_path) / "save.complete"
    
    # Remove old completion file
    if complete_file.exists():
        complete_file.unlink()
    
    # Create trigger file
    trigger_file.touch()
    print(f"Save triggered at {trigger_file}")
    
    # Wait for completion
    timeout = 60  # 60 seconds timeout
    start_time = time.time()
    
    while not complete_file.exists():
        if time.time() - start_time > timeout:
            raise TimeoutError("Save did not complete within timeout")
        time.sleep(1)
    
    print("Save completed successfully!")
    return True

# Usage in your ETL pipeline
def generate_world(seed, world_name):
    # Start container
    # ... docker start logic ...
    
    # Wait for healthcheck to pass (world generated)
    wait_for_healthcheck()
    
    # Trigger explicit save
    trigger_world_save("/path/to/mounted/trigger")
    
    # Now safe to stop container and extract files
    docker_stop_container()
    extract_world_files()
```

### Alternative: HTTP Trigger

```python
import requests

def trigger_save_http(container_ip, port=8080):
    """Trigger save via HTTP endpoint"""
    response = requests.post(f"http://{container_ip}:{port}/save")
    if response.status_code == 200:
        print("Save triggered successfully")
        return True
    return False
```

---

## Testing the Plugin

### Local Testing (Windows)

1. Install BepInEx in your local Valheim installation
2. Copy `ValheimSaveTrigger.dll` to `Valheim/BepInEx/plugins/`
3. Start Valheim with BepInEx (console should appear)
4. Create trigger file: `touch "C:\path\to\trigger\save.trigger"`
5. Check BepInEx console for log messages

### Docker Testing

```bash
# Build container
docker-compose build

# Start container
docker-compose up -d

# Wait for world generation
docker-compose logs -f | grep "World generator"

# Trigger save
touch ./trigger/save.trigger

# Check if save completed
cat ./trigger/save.complete

# Verify world files
ls -la ./generated_worlds/*/worlds_local/
```

---

## Debugging

### Enable BepInEx Console Logging

Edit `BepInEx/config/BepInEx.cfg`:
```ini
[Logging.Console]
Enabled = true

[Logging.Disk]
Enabled = true
```

### Common Issues

**Issue:** Plugin not loading
- Check BepInEx console for errors
- Verify .dll is in `BepInEx/plugins/`
- Ensure BepInEx is properly installed

**Issue:** Save trigger not detected
- Verify trigger path is accessible
- Check file permissions in Docker volume
- Review logs: `docker logs <container_id>`

**Issue:** ZoneSystem is null
- Wait for server to fully initialize
- Check that world generation has completed
- Ensure running on server instance

---

## Resources

### Documentation
- BepInEx Docs: https://docs.bepinex.dev/
- Valheim Modding: https://valheim.thunderstore.io/
- BepInEx GitHub: https://github.com/BepInEx/BepInEx

### Community
- Valheim Modding Discord: https://discord.gg/RBq2mzeu4z
- BepInEx Discord: https://discord.gg/MpFEDAg (note: for general BepInEx, not Valheim-specific)

### Tools
- dnSpy (decompiler): https://github.com/dnSpy/dnSpy
- ILSpy (decompiler): https://github.com/icsharpcode/ILSpy
- Thunderstore Mod Manager: https://www.overwolf.com/app/Thunderstore-Thunderstore_Mod_Manager

---

## Recommendation for Your Use Case

**Use Approach 1 (File System Watcher)** because:

1. ✅ Simple and reliable
2. ✅ No network dependencies
3. ✅ Works well with Docker volumes
4. ✅ Easy to debug
5. ✅ Minimal external dependencies

**However, you may not need this plugin at all** if:
- Your current graceful shutdown approach is working
- World generation is one-time per container
- The healthcheck + shutdown cycle is reliable

The plugin adds value only if you need:
- Mid-generation snapshots
- Explicit save confirmation before extraction
- Fine-grained control over save timing
