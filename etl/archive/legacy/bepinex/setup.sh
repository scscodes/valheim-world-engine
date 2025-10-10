#!/bin/bash

# Setup script for BepInEx development environment
set -e

echo "Setting up BepInEx development environment..."

# Create plugins directory
mkdir -p plugins

# Install BepInEx templates
echo "Installing BepInEx templates..."
dotnet new -i BepInEx.Templates --nuget-source https://nuget.bepinex.dev/v3/index.json

# Download BepInEx runtime from Thunderstore
echo "Downloading BepInEx runtime..."
if [ ! -f "plugins/BepInEx.dll" ]; then
    # Try to download from Thunderstore (more reliable)
    wget -q "https://thunderstore.io/package/download/BepInEx/BepInExPack_Valheim/5.4.2202/" -O bepinex.zip || {
        echo "Failed to download from Thunderstore, trying alternative approach..."
        # Alternative: use the lloesche/valheim-server image which has BepInEx
        docker run --rm -v "$(pwd)/plugins:/output" lloesche/valheim-server:latest \
            sh -c "if [ -f /opt/valheim/BepInEx/core/BepInEx.dll ]; then cp /opt/valheim/BepInEx/core/*.dll /output/; else echo 'BepInEx not found in container'; exit 1; fi"
    }
    
    if [ -f "bepinex.zip" ]; then
        unzip -q bepinex.zip -d temp/
        # Find BepInEx files in the extracted structure
        find temp/ -name "BepInEx.dll" -exec cp {} plugins/ \;
        find temp/ -name "BepInEx.Harmony.dll" -exec cp {} plugins/ \;
        find temp/ -name "BepInEx.MonoMod.dll" -exec cp {} plugins/ \;
        rm -rf temp/ bepinex.zip
    fi
    
    echo "BepInEx runtime setup completed"
else
    echo "BepInEx runtime already exists"
fi

# Download Valheim assemblies from Docker container
echo "Downloading Valheim assemblies..."
if [ ! -f "plugins/Assembly-CSharp.dll" ]; then
    echo "Extracting Valheim assemblies from Docker container..."
    docker run --rm -v "$(pwd)/plugins:/output" lloesche/valheim-server:latest \
        sh -c "cp /opt/valheim/valheim_server_Data/Managed/Assembly-CSharp.dll /output/ && \
               cp /opt/valheim/valheim_server_Data/Managed/UnityEngine.dll /output/ && \
               cp /opt/valheim/valheim_server_Data/Managed/UnityEngine.CoreModule.dll /output/ && \
               cp /opt/valheim/valheim_server_Data/Managed/UnityEngine.PhysicsModule.dll /output/ && \
               cp /opt/valheim/valheim_server_Data/Managed/UnityEngine.IMGUIModule.dll /output/ && \
               cp /opt/valheim/valheim_server_Data/Managed/UnityEngine.TextRenderingModule.dll /output/ && \
               cp /opt/valheim/valheim_server_Data/Managed/UnityEngine.UI.dll /output/ && \
               cp /opt/valheim/valheim_server_Data/Managed/UnityEngine.UIModule.dll /output/"
    echo "Valheim assemblies extracted successfully"
else
    echo "Valheim assemblies already exist"
fi

# Verify setup
echo "Verifying setup..."
required_files=(
    "plugins/BepInEx.dll"
    "plugins/BepInEx.Harmony.dll"
    "plugins/MonoMod.RuntimeDetour.dll"
    "plugins/assembly_valheim.dll"
    "plugins/UnityEngine.dll"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo "✅ Setup completed successfully!"
    echo "Required files:"
    ls -la plugins/
    echo ""
    echo "You can now build the plugins with: make build"
else
    echo "❌ Setup failed. Missing files:"
    printf '%s\n' "${missing_files[@]}"
    echo ""
    echo "Please check the setup and try again."
    exit 1
fi
