# How to Regenerate Data with Fixed Plugins

The backend pipeline needs to be updated to use the fixed BepInEx plugins. Here's how to regenerate data:

---

## ⚡ Quick Method: Manual Docker Run

This bypasses the backend and runs the Valheim server directly with your fixed plugins.

```bash
# 1. Prepare directory with fixed plugins
cd /home/steve/projects/valhem-world-engine
SEED_DIR="data/seeds/hkLycKKCMI_manual_test"
mkdir -p "$SEED_DIR/bepinex/plugins"
mkdir -p "$SEED_DIR/bepinex/config"

# 2. Copy FIXED plugins
cp bepinex/plugins/VWE_DataExporter.dll "$SEED_DIR/bepinex/plugins/"
cp bepinex/plugins/VWE_AutoSave.dll "$SEED_DIR/bepinex/plugins/"

# 3. Copy BepInEx config
cp bepinex/plugins/VWE_DataExporter.cfg "$SEED_DIR/bepinex/config/"

# 4. Run Docker container with BepInEx enabled
docker run --rm \
  -v "$(pwd)/$SEED_DIR:/config" \
  -e SERVER_NAME="hkLycKKCMI" \
  -e WORLD_NAME="hkLycKKCMI" \
  -e SERVER_PASS="test123" \
  -e BEPINEX=true \
  -e PRE_SERVER_SHUTDOWN_HOOK="echo 'VWE: Graceful shutdown initiated'; sleep 3; kill -TERM \$VALHEIM_SERVER_PID" \
  lloesche/valheim-server:latest

# 5. Monitor logs for:
#    - "★★★ BiomeExporter: Coverage range - X=[-10000 to 10000]"
#    - "★★★ BiomeExporter: Sample #1/... - pos=(-10000.00, -10000.00)"
#    - "★★★ BiomeExporter: Sample #262144/... - pos=(9980.47, 9980.47)"
#    - "VWE DataExporter: Biome JSON exported to ..."

# 6. Wait for completion (looks for "World generation complete")
# Then Ctrl+C when you see "VWE: Graceful shutdown initiated"

# 7. Check exported data
ls -lh "$SEED_DIR/world_data/"
# Should see: biomes.json, heightmap.json, structures.json (and .png versions)
```

### Expected Log Output (Verification)

```
★★★ BiomeExporter: START - resolution=2048, format=both
★★★ BiomeExporter: WorldGenerator.instance verified, starting sampling
★★★ BiomeExporter: Starting sampling loop - 4194304 total samples, stepSize=9.765625
★★★ BiomeExporter: Full world coverage - worldRadius=10000, worldDiameter=20000
★★★ BiomeExporter: Coverage range - X=[-10000 to 10000], Z=[-10000 to 10000]
★★★ BiomeExporter: Sample #1/4194304 - pos=(-10000.00, -10000.00), biome=Ashlands
...
★★★ BiomeExporter: Sample #4194304/4194304 - pos=(9990.23, 9990.23), biome=Ocean
★★★ BiomeExporter: COMPLETE - Total time: 45.2s
```

---

## 🔄 Proper Method: Update Backend Pipeline

To integrate fixed plugins into the backend service:

### Step 1: Update world_generator.py

The backend needs to mount the fixed plugins into containers. Modify:

`backend/app/services/world_generator.py`

```python
def _build_worldgen_plan(...):
    ...
    # Add fixed plugins to expected outputs
    plan = {
        ...
        "bepinex_plugins": [
            "VWE_DataExporter.dll",
            "VWE_AutoSave.dll"
        ],
        "expected_outputs": {
            "biomes": f"{extracted_dir}/biomes.json",
            "heightmap": f"{extracted_dir}/heightmap.json",
            ...
        }
    }

    # Copy fixed plugins to seed directory before container start
    plugin_src = Path(settings.REPO_ROOT) / "bepinex" / "plugins"
    plugin_dest = Path(seed_dir) / "bepinex" / "plugins"
    plugin_dest.mkdir(parents=True, exist_ok=True)

    for plugin in ["VWE_DataExporter.dll", "VWE_AutoSave.dll", "VWE_DataExporter.cfg"]:
        shutil.copy2(plugin_src / plugin, plugin_dest / plugin)
```

### Step 2: Update Docker Compose Volume Mounts

Ensure BepInEx plugins are mounted correctly in `docker/docker-compose.yml`:

```yaml
services:
  worker:
    volumes:
      - ${HOST_DATA_DIR}:/app/data
      - ${REPO_ROOT}/bepinex/plugins:/app/bepinex/plugins:ro
```

### Step 3: Rebuild and Restart Services

```bash
cd docker
docker-compose down
docker-compose build worker
docker-compose up -d
```

### Step 4: Regenerate via API

```bash
curl -X POST http://localhost:8000/api/v1/seeds/generate \
  -H "Content-Type: application/json" \
  -d '{"seed": "hkLycKKCMI"}'
```

---

## 🧪 Validate Fixed Data

After regeneration, run this validation script:

```bash
cd /home/steve/projects/valhem-world-engine

python3 << 'EOF'
import json
from pathlib import Path

# Find the exported biomes.json
data_file = Path("data/seeds/hkLycKKCMI_manual_test/world_data/biomes.json")

if not data_file.exists():
    print("❌ No biomes.json found!")
    print("   Check: data/seeds/*/world_data/biomes.json")
    exit(1)

with open(data_file) as f:
    data = json.load(f)

# Check metadata
print("Metadata Check:")
print(f"  Resolution: {data.get('resolution')}")
print(f"  World Radius: {data.get('world_radius')} (should be 10000)")
print(f"  World Diameter: {data.get('world_diameter')} (should be 20000)")

# Check biome names mapping
biome_names = data.get('biome_names', {})
print(f"\nBiome Names Check:")
if '1' in biome_names or 1 in biome_names:
    print("  ✅ Using correct bit flag indices (1, 2, 4, 8...)")
elif '0' in biome_names or 0 in biome_names:
    print("  ❌ Still using sequential indices (0, 1, 2, 3...) - OLD BUG!")

# Validate we have actual biome data
biome_map = data.get('biome_map', [])
if not biome_map:
    print("\n❌ No biome_map data!")
    exit(1)

print(f"\n✅ Biome map data found: {len(biome_map)} x {len(biome_map[0])} grid")

# Count unique biome IDs
from collections import Counter
flat_biomes = [cell for row in biome_map for cell in row]
biome_counts = Counter(flat_biomes)

print(f"\nBiome Distribution:")
BIOME_NAMES = {1: "Meadows", 2: "BlackForest", 4: "Swamp", 8: "Mountain",
               16: "Plains", 32: "Ocean", 64: "Mistlands", 256: "DeepNorth", 512: "Ashlands"}

for biome_id, count in sorted(biome_counts.items()):
    pct = count / len(flat_biomes) * 100
    name = BIOME_NAMES.get(biome_id, f"Unknown({biome_id})")
    print(f"  {name:<15} {count:>8,} ({pct:>5.1f}%)")

# Check for expected increases/decreases
mistlands_pct = biome_counts.get(64, 0) / len(flat_biomes) * 100
ocean_pct = biome_counts.get(32, 0) / len(flat_biomes) * 100

print(f"\n🔍 Validation:")
if mistlands_pct > 10:
    print(f"  ✅ Mistlands at {mistlands_pct:.1f}% (was ~5% with bug)")
else:
    print(f"  ⚠️  Mistlands still low at {mistlands_pct:.1f}% (expected 15-25%)")

if ocean_pct > 25:
    print(f"  ✅ Ocean at {ocean_pct:.1f}% (was ~20% with bug)")
else:
    print(f"  ⚠️  Ocean at {ocean_pct:.1f}% (expected 30-35%)")

print("\n" + "="*60)
print("If you see ✅ marks above, the fix is working!")
print("If you see ⚠️  marks, the old plugins may still be in use.")
EOF
```

---

## ⚠️ Current Issue

The backend pipeline (`docker-compose`) doesn't copy the fixed BepInEx plugins into containers before world generation. This is why the API-triggered generation didn't produce fixed data.

**Recommended**: Use the Quick Method first to validate the fixes work, then update the backend pipeline.

---

## Next Steps After Successful Generation

1. **Copy validated data to procedural-export**:
   ```bash
   # After validation succeeds
   cp data/seeds/hkLycKKCMI_manual_test/world_data/biomes.json \
      data/exports/bepinex-fixed/

   cp data/seeds/hkLycKKCMI_manual_test/world_data/heightmap.json \
      data/exports/bepinex-fixed/
   ```

2. **Convert to sample format**:
   ```bash
   # You'll need a conversion script (TBD) that reads biomes.json
   # and heightmap.json, then outputs the Samples array format
   ```

3. **Re-run Jupyter notebooks**:
   ```bash
   cd procedural-export/notebooks
   jupyter lab
   # Open 01_data_exploration.ipynb and verify new distributions
   ```

4. **Compare with reference**:
   - Load rendered output in browser
   - Compare against valheim-map.world for visual validation

---

## Files Needed for This

- ✅ `bepinex/plugins/VWE_DataExporter.dll` (rebuilt with fixes)
- ✅ `bepinex/plugins/VWE_AutoSave.dll` (rebuilt)
- ✅ `bepinex/plugins/VWE_DataExporter.cfg` (config)
- ⏳ Conversion script: biomes.json + heightmap.json → samples.json
- ⏳ Backend integration: Copy plugins before container start
