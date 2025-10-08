#!/bin/bash

# Simple setup script for BepInEx development using templates
set -e

echo "Setting up BepInEx development environment using templates..."

# Install BepInEx templates
echo "Installing BepInEx templates..."
dotnet new -i BepInEx.Templates --nuget-source https://nuget.bepinex.dev/v3/index.json

# Create a temporary project to get the references
echo "Creating temporary BepInEx project to extract references..."
mkdir -p temp-project
cd temp-project

# Create a new BepInEx plugin project
dotnet new bepinex5plugin -n TempPlugin

# Copy the project file to see what references are needed
cp TempPlugin/TempPlugin.csproj ../reference.csproj

# Clean up
cd ..
rm -rf temp-project

echo "Setup completed!"
echo ""
echo "Next steps:"
echo "1. Update the project files to use the correct references"
echo "2. Build the plugins with: make build"
echo ""
echo "Note: You'll need to provide Valheim assemblies manually or use the Docker approach"
