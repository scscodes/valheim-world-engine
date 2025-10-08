# Valheim Assembly Extraction Guide

## What We've Done

✅ **Completed:**
1. Created extraction script at `scripts/extract_valheim_assemblies.sh`
2. Downloaded BepInEx core DLLs (BepInEx.dll, BepInEx.Harmony.dll, 0Harmony20.dll, etc.)
3. Extracted UnityEngine modules (74 DLLs)
4. Updated `.csproj` files to use local DLL references instead of NuGet packages
5. Fixed script to detect `/opt/valheim/server/` path

⚠️ **Issue Discovered:**
The `Assembly-CSharp.dll` extracted from `lloesche/valheim-server` is only 24KB (a stub). The actual Valheim game assembly is much larger (200+ MB) and contains the game code (ZoneSystem, ZNet, etc.).

## Why This Happens

The `lloesche/valheim-server` image downloads Valheim via SteamCMD on first run. However, Valheim uses **obfuscated** assemblies that need additional processing for BepInEx development.

## Solution Options

### Option 1: Use Pre-Built Valheim Server (Recommended)

If you have access to a Valheim dedicated server installation or the game itself:

```bash
# Start a proper Valheim server with volume persistence
docker run -d \\
  --name valheim-bepinex \\
  -v ~/valheim-data:/config \\
  -e SERVER_NAME="DevServer" \\
  -e WORLD_NAME="DevWorld" \\
  -e SERVER_PASS="devpass123" \\
  -e SERVER_PUBLIC=0 \\
  lloesche/valheim-server:latest

# Wait 3-5 minutes for download to complete
# Check logs: docker logs -f valheim-bepinex

# Once "Game server connected" appears, extract assemblies
./scripts/extract_valheim_assemblies.sh --container valheim-bepinex --include-bepinex
```

The script now properly detects `/opt/valheim/server/` paths.

### Option 2: Use Assembly Publicizer

Valheim assemblies need to be "publicized" (make internal types public) for BepInEx development:

```bash
# Install BepInEx.AssemblyPublicizer.MSBuild
cd bepinex/src/VWE_AutoSave
dotnet add package BepInEx.AssemblyPublicizer.MSBuild --version 0.4.1

# It will auto-publicize Assembly-CSharp.dll during build
```

Update `.csproj` files to add publicizer configuration.

### Option 3: Use Community Resources

Many Valheim modding communities share publicized assemblies:
- **Valheim Modding Discord**: Has pinned resources
- **Thunderstore**: Some mod development kits include them
- **GitHub**: Search for "valheim publicized assemblies"

## Current Status

**Files in `bepinex/plugins/`:**
- ✅ BepInEx.dll, BepInEx.Harmony.dll (from BepInExPack_Valheim 5.4.2202)
- ✅ 0Harmony20.dll, MonoMod DLLs
- ✅ 74x UnityEngine modules  
- ⚠️ Assembly-CSharp.dll (stub, needs replacement)

**What's Needed:**
- Full Assembly-CSharp.dll (200+ MB) from actual Valheim server
- OR use AssemblyPublicizer during build

## Next Steps

### Immediate Action (Choose One):

**A. Extract from Running Server:**
```bash
# Start server and wait for download
docker run -d --name vw-extract \\
  -v /tmp/vw-data:/config \\
  -e SERVER_NAME="extract" -e WORLD_NAME="extract" \\
  -e SERVER_PASS="extract123" -e SERVER_PUBLIC=0 \\
  lloesche/valheim-server:latest

# Wait 5 minutes, then:
./scripts/extract_valheim_assemblies.sh --container vw-extract --include-bepinex

# Cleanup
docker stop vw-extract && docker rm vw-extract
```

**B. Use Assembly Publicizer:**
```bash
# Add to both .csproj files
cd bepinex
dotnet add src/VWE_AutoSave package BepInEx.AssemblyPublicizer.MSBuild
dotnet add src/VWE_DataExporter package BepInEx.AssemblyPublicizer.MSBuild
```

Then add to `.csproj`:
```xml
<ItemGroup>
  <Publicize Include="Assembly-CSharp" />
</ItemGroup>
```

**C. Manual Copy (if you have Valheim installed):**
```bash
# From game installation
cp ~/.steam/steam/steamapps/common/Valheim/valheim_Data/Managed/Assembly-CSharp.dll \\
   bepinex/plugins/

# From dedicated server
cp ~/valheim_server/valheim_server_Data/Managed/Assembly-CSharp.dll \\
   bepinex/plugins/
```

### After Getting Proper Assembly:

```bash
cd bepinex
make build  # Should compile successfully
make docker-build  # Create Docker image with plugins
```

## Troubleshooting

**"Unable to find package BepInEx.Core":**
- Fixed - we use local DLL references now

**"Assembly-CSharp not found":**
- Check file size: `ls -lh bepinex/plugins/Assembly-CSharp.dll`
- Should be 200+ MB, not 24 KB

**"Type 'ZoneSystem' not found":**
- Assembly-CSharp.dll is a stub or obfuscated
- Use Option 1 or 2 above

**Script says "Valheim root not found":**
- Updated script now checks `/opt/valheim/server/`
- Make sure container has fully started

## Files Modified

- `scripts/extract_valheim_assemblies.sh` - Updated path detection
- `bepinex/src/VWE_AutoSave/VWE_AutoSave.csproj` - Local DLL references
- `bepinex/src/VWE_DataExporter/VWE_DataExporter.csproj` - Local DLL references

## References

- BepInEx Valheim Pack: https://thunderstore.io/c/valheim/p/denikson/BepInExPack_Valheim/
- AssemblyPublicizer: https://github.com/BepInEx/BepInEx.AssemblyPublicizer
- Valheim Modding Wiki: https://github.com/Valheim-Modding/Wiki
