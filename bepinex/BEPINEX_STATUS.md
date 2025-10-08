# BepInEx Plugin Development Status

## ✅ Completed & Functional

### Programmatic World Save (VWE_AutoSave)
- **Status**: ✅ Fully working
- **Performance**: ~17 seconds total (world gen + save)
- **Speed improvement**: 10x faster than backend approach (2-3 minutes)
- **Save time**: ~67ms programmatic save

**Key fixes applied**:
- Removed Windows-only process filter `[BepInProcess("valheim_server.exe")]`
- Deleted broken `ZoneSystemGeneratePatch` (targeted non-existent method)
- Kept working `ZoneSystemStartPatch` hook
- Added debug logging: `★★★ VWE AutoSave: HOOK EXECUTED ★★★`

**Test results**:
```
✅ BepInEx loads successfully (5.4.23.2)
✅ VWE AutoSave plugin loads
✅ Harmony patches apply without errors
✅ Hook executes on ZoneSystem.Start
✅ World files created: hkLycKKCMI.db (315KB), hkLycKKCMI.fwl (51B)
✅ Programmatic save triggers (67ms)
```

### Docker Integration
- **Custom image**: `vwe/valheim-bepinex:latest` based on Debian 12
- **GLIBC**: 2.36 (required for BepInEx doorstop loader)
- **Build time**: ~3-5 minutes (first build)
- **Runtime**: Stable, plugins load correctly

---

## ⏳ In Progress

### Data Export (VWE_DataExporter)
- **Status**: ⏳ Partial - hooks execute but export not completing
- **Issue**: Unity coroutines start but don't yield results
- **Logs show**: `Starting biome export (resolution: 2048)` but no completion

**Working**:
- Plugin loads successfully
- Harmony patches apply
- Hook executes on ZoneSystem.Start
- Export directory created (`/opt/valheim/world_data/`)

**Not working**:
- Coroutines don't complete (BiomeExporter, HeightmapExporter)
- No files written to world_data directory
- No error messages or exceptions logged

**Next steps**:
1. Add more logging to coroutine methods
2. Investigate Unity coroutine behavior in headless server
3. Consider switching from coroutines to synchronous export
4. Debug WorldGenerator API access in dedicated server context

---

## 📋 Architecture

### Custom Docker Image Required
- **Why**: BepInEx doorstop loader requires GLIBC 2.33+
- **lloesche/valheim-server**: Debian 11 (GLIBC 2.31) ❌
- **vwe/valheim-bepinex**: Debian 12 (GLIBC 2.36) ✅

### Plugin Architecture
```
VWE_AutoSave.dll (11KB)
├── ZoneSystemStartPatch → Hooks world generation complete
├── MonitorWorldGeneration → Coroutine waits for flag
└── TriggerWorldSave → Calls ZNet.instance.Save(true)

VWE_DataExporter.dll (30KB)
├── ZoneSystemStartPatch → Hooks world generation complete
├── MonitorWorldGeneration → Coroutine waits for flag
├── TriggerDataExport → Starts export coroutines
└── DataExporters/
    ├── BiomeExporter.cs → Samples WorldGenerator.GetBiome()
    ├── HeightmapExporter.cs → Samples WorldGenerator.GetHeight()
    └── StructureExporter.cs → Queries ZoneSystem locations
```

---

## 🎯 Current State Summary

**Production ready**:
- ✅ World generation with programmatic save (17 seconds)
- ✅ 10x performance improvement over backend approach
- ✅ Harmony patches stable and reliable

**Needs work**:
- ⏳ Data export coroutines debugging
- ⏳ Alternative: Use MakeFwl for data extraction (already working in backend)

**Recommendation**: Deploy VWE_AutoSave now for fast world generation. Data export can be handled by existing MakeFwl pipeline until coroutine issue resolved.

---

## 🔧 Development Workflow

### Building Plugins
```bash
cd bepinex
make build  # Builds both plugins
```

### Testing
```bash
cd docker/bepinex
docker compose -f docker-compose.bepinex.yml --profile bepinex up --build

# Monitor logs
docker logs -f vwe-valheim-bepinex | grep -E "(VWE|★★★|saved)"

# Check files
ls -lh ../../data/seeds/hkLycKKCMI/worlds_local/
ls -lh ../../data/seeds/hkLycKKCMI/world_data/
```

### Key Log Messages
```
[Info   :   BepInEx] Loading [VWE AutoSave 1.0.0]
[Info   :VWE AutoSave] VWE AutoSave plugin loaded and enabled
[Info   :VWE AutoSave] VWE AutoSave patches applied
[Info   :VWE AutoSave] ★★★ VWE AutoSave: HOOK EXECUTED - ZoneSystem.Start detected ★★★
[Info   :VWE AutoSave] VWE AutoSave: Triggering world save...
World saved ( 67.534ms )
[Info   :VWE AutoSave] VWE AutoSave: World save triggered successfully
```

---

## 📚 Files Modified (Session)

### Plugin Source Code
- `src/VWE_AutoSave/VWE_AutoSave.cs` - Removed Windows filter, deleted broken patch
- `src/VWE_DataExporter/VWE_DataExporter.cs` - Same fixes applied

### Docker Configuration
- `docker/bepinex/Dockerfile` - Custom Debian 12 image with BepInEx
- `docker/bepinex/entrypoint.sh` - PUID/PGID handling, BepInEx wrapper
- `docker/bepinex/docker-compose.bepinex.yml` - Isolated test environment

### Documentation
- `bepinex/README.md` - Updated status, performance metrics
- `bepinex/BEPINEX_STATUS.md` - This file (current state)
- `bepinex/BEPINEX_FIXES_SUMMARY.md` - Historical journey

### Removed
- `docker/bepinex/Dockerfile.deprecated` - No longer needed

---

## 🔗 References

- [BepInEx 5.4.23.2 Release](https://github.com/BepInEx/BepInEx/releases/tag/v5.4.23.2)
- [Harmony Patching Guide](https://harmony.pardeike.net/)
- [Valheim Dedicated Server](https://steamdb.info/app/896660/)
- Project README: Phase 1-2 world generation pipeline
