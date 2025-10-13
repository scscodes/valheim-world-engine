# Quick Start Guide - BepInEx Adaptive Sampling

**Fast validation in 3 steps:**

## Step 1: Build

```bash
cd etl/experimental/bepinex-adaptive-sampling
./docker/build.sh
```

**Time:** ~10-15 minutes (first build, downloads Valheim)

## Step 2: Run Validation

```bash
python tests/validate_performance.py --seed "QuickTest"
```

**Time:** ~2-3 minutes total

## Step 3: Review Results

```bash
cat output/performance_validation.md
```

**Expected outcome:**
- ✓ Biome export: ~22 seconds
- ✓ Heightmap export: ~12 seconds
- ✓ Total time: ~34 seconds
- ✓ Speedup: 7.2x faster than 512×512

---

## Troubleshooting

### "Docker image not found"

```bash
cd docker
docker compose build
```

### "Plugins not found"

```bash
# Compile plugins manually
cd src/VWE_DataExporter
dotnet build -c Release

cd ../VWE_AutoSave
dotnet build -c Release

# Copy to plugins/
cp src/VWE_DataExporter/bin/Release/net48/*.dll plugins/
cp src/VWE_AutoSave/bin/Release/net48/*.dll plugins/
```

### "Container fails to start"

```bash
# Check logs
docker logs vwe-adaptive-sampling-test

# Common issues:
# - Port 2456 already in use: Change SERVER_PORT in docker-compose.yml
# - Permission denied: Run with sudo or add user to docker group
```

### "Validation timeout"

```bash
# Check if export is still running
docker logs -f vwe-adaptive-sampling-test | grep -i export

# If stuck, restart:
docker stop vwe-adaptive-sampling-test
docker rm vwe-adaptive-sampling-test
python tests/validate_performance.py
```

---

## Manual Testing (Without validation script)

```bash
# Start container
cd docker
docker compose up -d

# Watch logs for timing
docker logs -f vwe-adaptive-sampling-test

# Look for:
# - "BiomeExporter: COMPLETE" - biome export time
# - "HeightmapExporter: COMPLETE" - heightmap export time
# - "ALL EXPORTS COMPLETE" - total time

# Check output files
ls -lh output/world_data/
# Should see: biomes.json, heightmap.json (~500 KB each)

# Stop container
docker compose down
```

---

## Questions?

See full documentation in [README.md](README.md)
