#!/bin/bash
# Build script for VWE_StandardPlugin

set -e

echo "Building VWE_StandardPlugin..."

# Check if dotnet is available
if ! command -v dotnet &> /dev/null; then
    echo "Error: dotnet is not installed or not in PATH"
    echo "Please install .NET SDK 6.0 or later"
    exit 1
fi

# Restore packages
echo "Restoring NuGet packages..."
dotnet restore

# Build the project
echo "Building project..."
dotnet build --configuration Release

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Build successful! Plugin should be in ../../plugins/VWE_StandardPlugin.dll"
else
    echo "Build failed!"
    exit 1
fi

echo "Build complete!"
