#!/bin/bash
# Build script for VWE_WorldScreenshot plugin

set -e

echo "============================================"
echo "Building VWE_WorldScreenshot Plugin"
echo "============================================"

# Check if dotnet is available
if ! command -v dotnet &> /dev/null; then
    echo "ERROR: dotnet CLI not found"
    echo "Install: https://dotnet.microsoft.com/download"
    exit 1
fi

# Build
echo "Building Release configuration..."
dotnet build -c Release

# Check output
if [ -f "bin/Release/net48/VWE_WorldScreenshot.dll" ]; then
    echo ""
    echo "✓ Build successful!"
    echo ""
    echo "Output: bin/Release/net48/VWE_WorldScreenshot.dll"

    # Copy to plugins directory
    PLUGIN_DIR="../../plugins"
    if [ -d "$PLUGIN_DIR" ]; then
        echo "Copying to $PLUGIN_DIR..."
        cp bin/Release/net48/VWE_WorldScreenshot.dll "$PLUGIN_DIR/"
        echo "✓ Plugin installed to $PLUGIN_DIR"
    fi

    echo ""
    echo "============================================"
    echo "Ready to deploy!"
    echo "============================================"
    echo ""
    echo "Next steps:"
    echo "1. Copy VWE_WorldScreenshot.dll to BepInEx/plugins/"
    echo "2. Start Valheim server"
    echo "3. Check logs for screenshot capture"
    echo ""
else
    echo "ERROR: Build failed - DLL not found"
    exit 1
fi
