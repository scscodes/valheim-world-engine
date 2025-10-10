# BepInEx Prerequisites Quick Reference

## Required Software

### 1. .NET Framework 4.8 SDK
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install dotnet-sdk-4.8

# Or download from Microsoft:
# https://dotnet.microsoft.com/download/dotnet-framework/net48
```

### 2. Docker (Optional)
```bash
# Ubuntu/Debian
sudo apt install docker.io docker-compose
```

### 3. Git
```bash
# Ubuntu/Debian
sudo apt install git
```

## Required Assembly Files

**⚠️ Manual Setup Required**: These files must be obtained manually and placed in `bepinex/plugins/`:

### BepInEx Runtime
- `BepInEx.dll`
- `BepInEx.Harmony.dll` 
- `BepInEx.MonoMod.dll`

### Valheim Game Assemblies
- `Assembly-CSharp.dll` (Valheim's main game assembly)
- `UnityEngine.dll` and related modules

## Quick Setup

```bash
# 1. Install prerequisites
sudo apt update
sudo apt install dotnet-sdk-4.8 docker.io docker-compose git

# 2. Install BepInEx templates (already done)
dotnet new -i BepInEx.Templates --nuget-source https://nuget.bepinex.dev/v3/index.json

# 3. Get assembly files (choose one method):
# Method 1: Download from Thunderstore
wget "https://thunderstore.io/package/download/BepInEx/BepInExPack_Valheim/5.4.2202/"
unzip BepInExPack_Valheim_5.4.2202.zip
# Extract BepInEx files to bepinex/plugins/

# Method 2: Extract from Valheim installation
cp /path/to/valheim/valheim_server_Data/Managed/Assembly-CSharp.dll bepinex/plugins/
cp /path/to/valheim/valheim_server_Data/Managed/UnityEngine*.dll bepinex/plugins/

# 4. Build plugins
cd bepinex
make build

# 5. Build Docker image
make docker-build
```

## Verification

```bash
# Check .NET version
dotnet --version
# Should show 4.8.x

# Check required files
ls -la bepinex/plugins/
# Should show: BepInEx.dll, BepInEx.Harmony.dll, BepInEx.MonoMod.dll, Assembly-CSharp.dll, UnityEngine.dll

# Test build
cd bepinex
make build
# Should complete without errors
```

## Troubleshooting

### "Unable to find package BepInEx.Core"
- **Cause**: Missing BepInEx assembly files
- **Fix**: Download BepInEx runtime and place in `bepinex/plugins/`

### "Assembly-CSharp not found"
- **Cause**: Missing Valheim game assemblies
- **Fix**: Extract from Valheim installation or download from Thunderstore

### "dotnet command not found"
- **Cause**: .NET Framework 4.8 SDK not installed
- **Fix**: Install .NET Framework 4.8 SDK

### "Permission denied" errors
- **Cause**: File permissions issues
- **Fix**: Check file ownership and permissions

## Current Status

✅ **Completed:**
- BepInEx templates installed
- Project structure created
- Source code written
- Docker configuration ready
- Documentation updated

❌ **Pending:**
- Assembly files setup (manual step required)
- Plugin compilation
- Docker image building
- Integration testing
