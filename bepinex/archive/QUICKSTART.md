# BepInEx Quick Start Guide

Get the BepInEx approach running in under 2 minutes.

## What This Is

An **isolated experimental approach** to Valheim world generation that uses custom BepInEx plugins to programmatically trigger saves and exports, targeting 30-60 second generation time (vs 2-3 minutes for the working backend approach).

## Prerequisites

- Docker installed and running
- `.env` file in repo root (should already exist)
- Pre-compiled plugins in `bepinex/plugins/` (already present)

## Run It

```bash
# From repo root
cd bepinex

# Start the BepInEx container
make run

# Watch the logs
make logs
```

## What to Look For

**Success indicators in logs:**

1. **BepInEx loads:**
   ```
   [Message:   BepInEx] BepInEx 5.x.x - valheim_server
   ```

2. **Plugins load:**
   ```
   [Info   :   BepInEx] Loading [VWE_AutoSave 1.0.0]
   [Info   :   BepInEx] Loading [VWE_DataExporter 1.0.0]
   ```

3. **Hooks execute:**
   ```
   [VWE_AutoSave] World generation detected
   [VWE_AutoSave] Triggering save in 2 seconds...
   ```

4. **Save completes:**
   ```
   World saved ( xxxx ms )
   ```

5. **Data exported:**
   ```
   [VWE_DataExporter] Biomes exported to /config/world_data/biomes.json
   ```

## Verify Results

```bash
# Check world files
ls -la ../data/seeds/hkLycKKCMI/worlds_local/
# Should show: hkLycKKCMI.db and hkLycKKCMI.fwl

# Check exported data
ls -la ../data/seeds/hkLycKKCMI/world_data/
# Should show: biomes.json, heightmap files, etc.
```

## Stop It

```bash
make stop
```

## Troubleshooting

**No BepInEx logs?**
- Check `BEPINEX=true` in `docker-compose.bepinex.yml`
- Verify container is running: `docker ps | grep vwe-valheim-bepinex`

**No plugin logs?**
- Check plugins exist: `ls -la plugins/VWE_*.dll`
- Verify volume mounts: `docker inspect vwe-valheim-bepinex | grep bepinex`

**No world files?**
- Wait longer (first run downloads Valheim, takes ~5 min)
- Check logs for errors: `make logs | grep -i error`

**Still stuck?**
- See `VALIDATION_GUIDE.md` for detailed troubleshooting
- Compare to working backend approach (should work as reference)

## Next Steps

**After successful run:**
1. Follow `VALIDATION_GUIDE.md` for comprehensive testing
2. Measure performance vs backend approach
3. Test with multiple seeds for consistency

**If it works better than backend:**
- Document performance gains
- See `INTEGRATION_EXAMPLE.md` for integration plan

**If it doesn't work:**
- Stick with working backend approach
- Document findings in issues
