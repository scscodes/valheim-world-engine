#!/bin/bash
# Build script for BepInEx Adaptive Sampling experiment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "==================================="
echo "BepInEx Adaptive Sampling - Build"
echo "==================================="
echo ""

# Build plugins
echo "[1/3] Building BepInEx plugins..."
cd "$PROJECT_ROOT/src/VWE_DataExporter"
dotnet build -c Release
cd "$PROJECT_ROOT/src/VWE_AutoSave"
dotnet build -c Release

echo ""
echo "[2/3] Copying compiled plugins..."
mkdir -p "$PROJECT_ROOT/plugins"
cp "$PROJECT_ROOT/src/VWE_DataExporter/bin/Release/net48/VWE_DataExporter.dll" "$PROJECT_ROOT/plugins/"
cp "$PROJECT_ROOT/src/VWE_AutoSave/bin/Release/net48/VWE_AutoSave.dll" "$PROJECT_ROOT/plugins/"
cp "$PROJECT_ROOT/src/VWE_DataExporter/bin/Release/net48/Newtonsoft.Json.dll" "$PROJECT_ROOT/plugins/"

echo ""
echo "[3/3] Building Docker image..."
cd "$PROJECT_ROOT/docker"
docker compose build

echo ""
echo "✓ Build complete!"
echo ""
echo "Next steps:"
echo "  1. Run validation test: cd $PROJECT_ROOT && python tests/validate_performance.py"
echo "  2. View results: cat $PROJECT_ROOT/output/performance_results.md"
