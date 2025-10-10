# BepInEx Approach - End-to-End Validation Guide

This guide validates the BepInEx programmatic approach for Valheim world generation.

## Goal

Verify that custom VWE plugins successfully:
1. Hook into world generation completion events
2. Programmatically trigger saves
3. Export biome/heightmap data during generation
4. Complete in 30-60 seconds (vs 2-3 minutes for backend approach)

## Pre-Validation Checklist

### Required Files

```bash
# Verify plugins exist
ls -la bepinex/plugins/VWE_*.dll
# Should show:
# - VWE_AutoSave.dll
# - VWE_DataExporter.dll

# Verify config files exist
ls -la bepinex/config/
# Should show:
# - BepInEx.cfg
# - VWE_DataExporter.cfg

# Verify .env is configured
grep -E "^(HOST_DATA_DIR|WORLD_NAME|HOST_UID|HOST_GID|PLUGINS_HOST_DIR)" .env
```

### Expected .env Values

```bash
HOST_DATA_DIR=/home/steve/projects/valhem-world-engine/data
WORLD_NAME=hkLycKKCMI
HOST_UID=1000
HOST_GID=1000
PLUGINS_HOST_DIR=/home/steve/projects/valhem-world-engine/bepinex/plugins
```

## Validation Steps

### Step 1: Clean Slate

```bash
# Remove any existing world data for clean test
rm -rf data/seeds/hkLycKKCMI/

# Verify no BepInEx container running
docker ps | grep vwe-valheim-bepinex
# Should return nothing

# If container exists, stop it
docker stop vwe-valheim-bepinex
docker rm vwe-valheim-bepinex
```

### Step 2: Start BepInEx Container

```bash
# From repo root
cd docker/bepinex

# Start container
docker compose -f docker-compose.bepinex.yml --profile bepinex up -d

# Verify container started
docker ps | grep vwe-valheim-bepinex
# Should show running container
```

### Step 3: Monitor Logs

**Open multiple terminals for comprehensive monitoring:**

**Terminal 1 - Full logs:**
```bash
docker logs -f vwe-valheim-bepinex
```

**Terminal 2 - BepInEx/Plugin activity:**
```bash
docker logs -f vwe-valheim-bepinex 2>&1 | grep -E "(BepInEx|VWE|plugin)"
```

**Terminal 3 - World generation progress:**
```bash
docker logs -f vwe-valheim-bepinex 2>&1 | grep -E "(World|Zone|Save|Export)"
```

### Step 4: Watch for Key Events

Monitor logs for these critical events **in order**:

#### 1. BepInEx Initialization
```
[Message:   BepInEx] BepInEx 5.x.x - valheim_server
[Info   :   BepInEx] Running under Unity vX.X.X
[Info   :   BepInEx] Preloader started
```

#### 2. Plugin Loading
```
[Info   :   BepInEx] Loading [VWE_AutoSave 1.0.0]
[Info   :   BepInEx] Loading [VWE_DataExporter 1.0.0]
```

#### 3. World Generation Start
```
Zonesystem Awake
Generating locations
```

#### 4. Plugin Hook Execution (CRITICAL)
```
[VWE_AutoSave] World generation detected
[VWE_AutoSave] Triggering save in 2 seconds...
[VWE_DataExporter] Exporting world data...
```

#### 5. Save Triggered
```
Saving world...
World saved ( xxxx ms )
```

#### 6. Data Export Completed
```
[VWE_DataExporter] Biomes exported to /config/world_data/biomes.json
[VWE_DataExporter] Heightmap exported to /config/world_data/heightmap.npy
```

### Step 5: Verify Output Files

**Check world files:**
```bash
# From repo root
ls -la data/seeds/hkLycKKCMI/worlds_local/
# Should show:
# - hkLycKKCMI.db
# - hkLycKKCMI.fwl
```

**Check exported data:**
```bash
ls -la data/seeds/hkLycKKCMI/world_data/
# Should show:
# - biomes.json
# - heightmap.npy (or .json depending on plugin config)
# - structures.json (if enabled)
```

**Verify file timestamps:**
```bash
stat data/seeds/hkLycKKCMI/worlds_local/hkLycKKCMI.db
stat data/seeds/hkLycKKCMI/world_data/biomes.json
# Timestamps should be within seconds of each other
```

### Step 6: Performance Validation

**Record timing:**
```bash
# Start time
docker logs vwe-valheim-bepinex 2>&1 | grep "BepInEx.*Preloader started"

# End time (save completed)
docker logs vwe-valheim-bepinex 2>&1 | grep "World saved"

# Calculate duration (should be 30-60 seconds)
```

**Compare to backend approach:**
- Backend: 2-3 minutes
- BepInEx target: 30-60 seconds
- Success criteria: <90 seconds total

### Step 7: Data Integrity Check

**Validate world file:**
```bash
# Check file size (should be >100KB)
du -h data/seeds/hkLycKKCMI/worlds_local/hkLycKKCMI.db

# Verify not corrupted (shouldn't be all zeros)
hexdump -C data/seeds/hkLycKKCMI/worlds_local/hkLycKKCMI.db | head
```

**Validate exported data:**
```bash
# Check JSON validity
cat data/seeds/hkLycKKCMI/world_data/biomes.json | jq . > /dev/null
echo $?  # Should be 0 (success)

# Check data structure
cat data/seeds/hkLycKKCMI/world_data/biomes.json | jq 'keys'
# Should show expected structure
```

### Step 8: Cleanup

```bash
# Stop container
cd docker/bepinex
docker compose -f docker-compose.bepinex.yml down

# Optionally preserve test data for comparison
mv data/seeds/hkLycKKCMI data/seeds/hkLycKKCMI_bepinex_test_$(date +%Y%m%d_%H%M%S)
```

## Success Criteria

✅ **PASS if all true:**
- [ ] BepInEx loaded successfully
- [ ] VWE plugins loaded (both AutoSave and DataExporter)
- [ ] World generation completed
- [ ] Plugin hooks executed (logs show VWE messages)
- [ ] Save triggered programmatically
- [ ] Both .db and .fwl files created
- [ ] Exported data files created (biomes.json, heightmap)
- [ ] Total time < 90 seconds
- [ ] Files not corrupted (valid JSON, non-zero .db)

❌ **FAIL if any:**
- [ ] BepInEx failed to load
- [ ] Plugins not loaded
- [ ] No VWE log messages (hooks didn't execute)
- [ ] Missing .db or .fwl files
- [ ] Missing exported data
- [ ] Took > 90 seconds
- [ ] Files corrupted or invalid

## Troubleshooting

### Issue: BepInEx not loading

**Symptoms:**
```
No BepInEx messages in logs
Container starts but no plugin activity
```

**Check:**
```bash
# Verify BEPINEX env var is set
docker exec vwe-valheim-bepinex env | grep BEPINEX
# Should show: BEPINEX=true

# Check if BepInEx is installed in container
docker exec vwe-valheim-bepinex ls -la /opt/valheim/bepinex/
```

**Fix:**
- Verify `BEPINEX=true` in docker-compose.bepinex.yml
- Check lloesche image version supports BepInEx

### Issue: Plugins not loading

**Symptoms:**
```
BepInEx loads but no [VWE_AutoSave] or [VWE_DataExporter] messages
```

**Check:**
```bash
# Verify plugins mounted correctly
docker exec vwe-valheim-bepinex ls -la /config/bepinex/plugins/
# Should show VWE_AutoSave.dll and VWE_DataExporter.dll

# Check plugin permissions
docker exec vwe-valheim-bepinex ls -la /config/bepinex/plugins/VWE_*.dll
# Should be readable
```

**Fix:**
- Verify volume mounts in docker-compose.bepinex.yml
- Check PLUGINS_HOST_DIR in .env points to correct directory
- Rebuild plugins: `cd bepinex && make build`

### Issue: Hooks not executing

**Symptoms:**
```
Plugins loaded but no "World generation detected" or "Triggering save" messages
```

**Possible causes:**
1. Plugin code not hooking correct events
2. Environment variables not read by plugins
3. Timing issue (hooks registered too late)

**Debug:**
```bash
# Check plugin config
docker exec vwe-valheim-bepinex cat /config/bepinex/VWE_DataExporter.cfg

# Check environment vars visible to plugins
docker exec vwe-valheim-bepinex env | grep VWE_
```

### Issue: No exported data

**Symptoms:**
```
Save triggered but no files in world_data/
```

**Check:**
```bash
# Verify export directory exists
docker exec vwe-valheim-bepinex ls -la /config/world_data/

# Check for permission issues
docker exec vwe-valheim-bepinex ls -la /config/
```

**Fix:**
- Verify VWE_DATAEXPORT_DIR=/config/world_data in compose
- Check plugin logs for export errors
- Verify PUID/PGID match HOST_UID/HOST_GID

### Issue: Performance no better than backend

**Symptoms:**
```
Takes 2-3 minutes (same as backend approach)
```

**Root cause:** Plugins not triggering immediate save, falling back to default autosave timer

**Check:**
```bash
# Look for VWE_AutoSave triggering
docker logs vwe-valheim-bepinex 2>&1 | grep "VWE_AutoSave"
# Should show "Triggering save" message within seconds of world gen
```

**Fix:**
- Verify VWE_AUTOSAVE_ENABLED=true
- Check VWE_AUTOSAVE_DELAY value (should be 2 seconds)
- Review plugin source: does it properly hook ZoneSystem.Start?

## Comparison Test

Run both approaches back-to-back:

```bash
# Backend approach
cd docker
docker compose -f docker-compose.yml up -d
# Monitor: time to .db/.fwl creation
docker compose -f docker-compose.yml down

# BepInEx approach
cd docker/bepinex
docker compose -f docker-compose.bepinex.yml --profile bepinex up -d
# Monitor: time to .db/.fwl + exported data creation
docker compose -f docker-compose.bepinex.yml down
```

**Compare:**
- Time to world files
- Presence of exported data
- File integrity
- Reliability/consistency

## Next Steps

### If BepInEx approach PASSES all criteria:
1. Document performance gains
2. Run multiple test seeds for consistency
3. Prepare integration plan for backend/
4. Create migration guide

### If BepInEx approach FAILS:
1. Document failure mode
2. Isolate root cause (BepInEx, plugins, config)
3. Fix and re-test
4. If unfixable, document limitations
5. Stick with backend approach as primary
