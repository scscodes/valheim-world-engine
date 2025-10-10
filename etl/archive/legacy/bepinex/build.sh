#!/bin/bash

# Build script for VWE BepInEx plugins
set -e

echo "Building VWE BepInEx plugins..."

# Check if dotnet is available
if ! command -v dotnet &> /dev/null; then
    echo "Error: dotnet is not installed or not in PATH"
    echo "Please install .NET Framework 4.8 SDK"
    exit 1
fi

# Create plugins directory if it doesn't exist
mkdir -p plugins

# Build VWE_AutoSave plugin
echo "Building VWE_AutoSave plugin..."
cd src/VWE_AutoSave
dotnet build -c Release -o ../../plugins/
cd ../..

# Build VWE_DataExporter plugin
echo "Building VWE_DataExporter plugin..."
cd src/VWE_DataExporter
dotnet build -c Release -o ../../plugins/
cd ../..

# Copy configuration files
echo "Copying configuration files..."
cp config/*.cfg plugins/

echo "Build completed successfully!"
echo "Plugins built:"
ls -la plugins/

echo ""
echo "To build Docker image:"
echo "cd docker && docker build -t vwe/valheim-server-bepinex:latest ."
