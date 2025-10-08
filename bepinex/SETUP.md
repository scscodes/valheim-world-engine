# BepInEx Setup Guide

This guide covers the prerequisites and setup required for BepInEx development and deployment.

## Prerequisites

### 1. .NET Framework 4.8 SDK
BepInEx plugins require .NET Framework 4.8, not .NET Core/5+.

**Installation:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install dotnet-sdk-4.8

# Or download from Microsoft:
# https://dotnet.microsoft.com/download/dotnet-framework/net48
```

### 2. BepInEx Templates (Already Installed)
BepInEx templates are already installed and ready to use:

```bash
# Templates are already installed via:
dotnet new -i BepInEx.Templates --nuget-source https://nuget.bepinex.dev/v3/index.json
```

### 3. BepInEx Runtime (Manual Setup Required)
**⚠️ Manual Step Required**: Download and extract BepInEx for Valheim:

```bash
# Option 1: Download from Thunderstore (Recommended)
wget "https://thunderstore.io/package/download/BepInEx/BepInExPack_Valheim/5.4.2202/" -O bepinex.zip
unzip bepinex.zip
# Extract BepInEx files to bepinex/plugins/

# Option 2: Download from GitHub (if available)
# wget https://github.com/BepInEx/BepInEx/releases/download/v5.4.22/BepInEx_Valheim_5.4.22.0.zip
# unzip and extract files
```

### 4. Valheim Server Files
We need Valheim server assemblies for compilation:

```bash
# Download Valheim server (if not already available)
# This requires a Valheim server installation
# Copy these files to bepinex/plugins/:
# - Assembly-CSharp.dll
# - UnityEngine.dll
# - UnityEngine.CoreModule.dll
# - UnityEngine.PhysicsModule.dll
# - UnityEngine.IMGUIModule.dll
# - UnityEngine.TextRenderingModule.dll
# - UnityEngine.UI.dll
# - UnityEngine.UIModule.dll
```

## Setup Steps

### 1. Download BepInEx Runtime
```bash
cd bepinex
mkdir -p plugins
wget https://github.com/BepInEx/BepInEx/releases/download/v5.4.22/BepInEx_Valheim_5.4.22.0.zip
unzip BepInEx_Valheim_5.4.22.0.zip -d plugins/
```

### 2. Get Valheim Assemblies
You need to extract Valheim server assemblies. This can be done by:

**Option A: From existing Valheim installation**
```bash
# If you have Valheim installed locally
cp /path/to/valheim/valheim_server_Data/Managed/Assembly-CSharp.dll plugins/
cp /path/to/valheim/valheim_server_Data/Managed/UnityEngine*.dll plugins/
```

**Option B: From Docker container**
```bash
# Extract from lloesche/valheim-server container
docker run --rm -v $(pwd)/plugins:/output lloesche/valheim-server:latest \
  sh -c "cp /opt/valheim/valheim_server_Data/Managed/*.dll /output/"
```

**Option C: Download Valheim Dedicated Server**
```bash
# Download Valheim dedicated server from Steam
# Extract the assemblies from valheim_server_Data/Managed/
```

### 3. Verify Setup
```bash
# Check that required files exist
ls -la plugins/
# Should show:
# - BepInEx.dll
# - BepInEx.Harmony.dll
# - BepInEx.MonoMod.dll
# - Assembly-CSharp.dll
# - UnityEngine.dll
# - (other UnityEngine modules)
```

### 4. Build Plugins
```bash
# Build the plugins
make build
```

### 5. Build Docker Image
```bash
# Build the Docker image
make docker-build
```

## Alternative: Manual Assembly Setup

If you can't get the Valheim assemblies, you can modify the project files to use NuGet packages instead:

### Update VWE_AutoSave.csproj
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net48</TargetFramework>
    <AssemblyName>VWE_AutoSave</AssemblyName>
    <RootNamespace>VWE_AutoSave</RootNamespace>
    <OutputType>Library</OutputType>
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="BepInEx.Core" Version="5.4.22" />
    <PackageReference Include="BepInEx.Harmony" Version="2.2.2" />
    <PackageReference Include="UnityEngine" Version="2019.4.40" />
    <PackageReference Include="Assembly-CSharp" Version="0.0.0" />
  </ItemGroup>
</Project>
```

### Update VWE_DataExporter.csproj
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net48</TargetFramework>
    <AssemblyName>VWE_DataExporter</AssemblyName>
    <RootNamespace>VWE_DataExporter</RootNamespace>
    <OutputType>Library</OutputType>
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="BepInEx.Core" Version="5.4.22" />
    <PackageReference Include="BepInEx.Harmony" Version="2.2.2" />
    <PackageReference Include="UnityEngine" Version="2019.4.40" />
    <PackageReference Include="Assembly-CSharp" Version="0.0.0" />
    <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
  </ItemGroup>
</Project>
```

## Docker Setup

### 1. Update Dockerfile
The Dockerfile needs to include BepInEx runtime:

```dockerfile
FROM lloesche/valheim-server:latest

# Install BepInEx
RUN wget https://github.com/BepInEx/BepInEx/releases/download/v5.4.22/BepInEx_Valheim_5.4.22.0.zip \
    && unzip BepInEx_Valheim_5.4.22.0.zip -d /valheim/ \
    && rm BepInEx_Valheim_5.4.22.0.zip

# Copy VWE plugins
COPY plugins/VWE_AutoSave.dll /valheim/BepInEx/plugins/
COPY plugins/VWE_DataExporter.dll /valheim/BepInEx/plugins/

# Set permissions
RUN chown -R 1000:1000 /valheim/BepInEx
```

### 2. Environment Variables
Add these to your .env:

```bash
# BepInEx Configuration
BEPINEX_ENABLED=true
BEPINEX_LOG_LEVEL=Info
VWE_AUTOSAVE_ENABLED=true
VWE_DATAEXPORT_ENABLED=true
```

## Troubleshooting

### Common Issues

1. **"Unable to find package BepInEx.Core"**
   - Solution: Use local assembly references instead of NuGet packages
   - Download BepInEx runtime and reference local DLLs

2. **"Assembly-CSharp not found"**
   - Solution: Extract Valheim server assemblies
   - Use Docker container to get the files

3. **"UnityEngine not found"**
   - Solution: Extract UnityEngine assemblies from Valheim
   - Or use NuGet packages for UnityEngine

4. **"Plugin not loading"**
   - Check BepInEx version compatibility
   - Verify DLL files are in correct location
   - Check file permissions

### Verification Commands

```bash
# Check .NET version
dotnet --version

# Check BepInEx files
ls -la bepinex/plugins/

# Check plugin compilation
cd bepinex/src/VWE_AutoSave
dotnet build -v detailed

# Check Docker image
docker images | grep valheim-server-bepinex
```

## Next Steps

1. Complete the setup steps above
2. Build the plugins: `make build`
3. Build Docker image: `make docker-build`
4. Test the integration: `make docker-run`
5. Integrate with main project following `INTEGRATION_EXAMPLE.md`

This setup provides a complete BepInEx development environment for Valheim World Engine.
