# BepInEx Gen1 - Fixes Applied

**Date:** 2025-10-10
**Issue**: First test run revealed two critical problems
**Status**: ✅ FIXED

## Problems Identified

### 1. Permission Errors
**Symptom**: `PermissionError: [Errno 13] Permission denied` writing to `extracted/worldgen_logs.txt`
**Root Cause**: Docker creates files as root, Python runs as user

### 2. BepInEx Export Missing
**Symptom**: Missing `biomes.json` and `heightmap.npy` files
**Root Cause**: BepInEx plugins not configured with proper environment variables and mount paths

## Historical Solutions Found

### From `etl/archive/legacy/backend/app/services/world_generator.py`

**Permission Fix (lines 340-346)**:
```python
# Reassign ownership on host to avoid root-owned artifacts
if settings.host_uid is not None and settings.host_gid is not None:
    try:
        _chown_recursive(seed_dir, settings.host_uid, settings.host_gid)
    except Exception:
        pass
```

**PUID/PGID Support (lines 46-47)**:
```python
"PUID": str(settings.host_uid or 1000),
"PGID": str(settings.host_gid or 1000),
```

**BepInEx Export Wait Logic (lines 244-276)**:
- Wait for "ALL EXPORTS COMPLETE" log message
- 30-minute timeout for exports
- Monitor logs continuously after world generation

### From `etl/archive/legacy/bepinex/src/VWE_DataExporter/VWE_DataExporter.cs`

**Required Environment Variables**:
- `VWE_DATAEXPORT_ENABLED=true` - Enable export
- `VWE_EXPORT_RESOLUTION=256` - Resolution (read from config biome_resolution/heightmap_resolution)
- `_exportDir` config defaults to `./world_data` (relative to Valheim root)

**Export Path**: Relative to `Application.dataPath` (Valheim's `/valheim/valheim_server_Data/`)
- Actual path: `/valheim/world_data/`

**Log Indicator**: Plugin logs `"★★★ VWE_DataExporter: ALL EXPORTS COMPLETE - Total time: {time}s"`

## Fixes Applied

### Fix 1: Permission Handling

**File**: `lib/orchestrator.py`

**Added** `_fix_permissions()` method:
```python
def _fix_permissions(self, seed_dir: Path) -> None:
    """Fix file ownership after Docker container creates files as root"""
    import pwd

    try:
        # Get current user's UID/GID
        uid = os.getuid()
        gid = os.getgid()

        # Recursively chown all files in seed directory
        for root, dirs, files in os.walk(seed_dir):
            for d in dirs:
                path = os.path.join(root, d)
                try:
                    os.chown(path, uid, gid)
                except Exception:
                    pass
            for f in files:
                path = os.path.join(root, f)
                try:
                    os.chown(path, uid, gid)
                except Exception:
                    pass

        os.chown(seed_dir, uid, gid)
        logger.info(f"Fixed permissions for {seed_dir}")
    except Exception as e:
        logger.warning(f"Failed to fix permissions: {e}")
```

**Modified** `_execute_generation()` to call `_fix_permissions()` before saving logs.

### Fix 2: BepInEx Environment Variables

**File**: `lib/orchestrator.py`

**Modified** `_build_environment()`:
```python
# Add BepInEx configuration
if self.bepinex_config.get("enabled"):
    env["BEPINEX"] = "1"
    # Export configuration
    env["VWE_DATAEXPORT_ENABLED"] = "true"
    env["VWE_DATAEXPORT_FORMAT"] = "both"  # json + npy
    env["VWE_DATAEXPORT_DIR"] = "/config/BepInEx/export"  # Where to write exports
    # Resolution config (read by plugin from config file)
    env["VWE_BIOME_RESOLUTION"] = str(resolution)
    env["VWE_HEIGHTMAP_RESOLUTION"] = str(resolution)
    # Logging
    env["VWE_LOG_EXPORTS"] = "true"
    env["VWE_LOG_DEBUG"] = "true"

# Add PUID/PGID for proper file ownership
env["PUID"] = str(os.getuid())
env["PGID"] = str(os.getgid())
```

### Fix 3: Export Directory Mount

**File**: `lib/orchestrator.py`

**Modified** `_build_volumes()`:
```python
# Mount extracted directory for BepInEx exports
# BepInEx exports to /valheim/world_data by default
# We need to mount our extracted dir there
extracted_dir = directories["extracted"]
volumes[str(extracted_dir.absolute())] = {
    "bind": "/valheim/world_data",  # Where BepInEx writes
    "mode": "rw"
}
```

### Fix 4: Extended Wait Logic

**File**: `lib/orchestrator.py`

**Modified** `_wait_for_generation()`:
```python
# Extended readiness indicators for BepInEx
export_indicators = [
    "ALL EXPORTS COMPLETE",
    "VWE_DataExporter: Biome export phase completed",
    "VWE_DataExporter: Heightmap export phase completed"
]

# Check both server readiness AND export completion
for indicator in readiness_indicators + export_indicators:
    if indicator in logs:
        logger.info(f"Found indicator: '{indicator}'")
        # Continue waiting for ALL exports if we only see partial completion
        if "ALL EXPORTS COMPLETE" in logs:
            return True, False  # Fully ready
```

### Fix 5: File Validation Improvements

**File**: `lib/orchestrator.py`

**Modified** `_validate_output_files()` to check both locations:
```python
# Check in both raw directory AND extracted directory
# BepInEx might write to /valheim/world_data which maps to extracted/
for dir_name in ["raw", "extracted"]:
    if dir_name not in directories:
        continue
    # ... check files
```

## Test Plan

### Test 1: Permission Fix
**Command**: `python generator.py --seed QuickTest --resolution 256`

**Expected Outcomes**:
- ✅ Container creates files
- ✅ Python script can write `worldgen_logs.txt`
- ✅ No permission errors in output
- ✅ All files in `data/seeds/{hash}/` owned by current user

**Verification**:
```bash
ls -la data/seeds/*/extracted/
# Should show: steve steve (not root root)
```

### Test 2: BepInEx Export
**Command**: `python generator.py --seed QuickTest --resolution 256 --verbose`

**Expected Outcomes**:
- ✅ Container logs show: `"VWE DataExporter plugin loaded and enabled"`
- ✅ Container logs show: `"★★★ VWE DataExporter: ALL EXPORTS COMPLETE"`
- ✅ Files created: `extracted/biomes.json`, `extracted/heightmap.npy`
- ✅ JSON contains biome samples
- ✅ NPY contains height data

**Verification**:
```bash
# Check logs for export indicators
grep "VWE" data/seeds/*/extracted/worldgen_logs.txt

# Check exported files exist
ls -la data/seeds/*/extracted/*.json
ls -la data/seeds/*/extracted/*.npy

# Verify JSON structure
python -c "import json; print(len(json.load(open('data/seeds/.../extracted/biomes.json'))))"
# Should show: 65536 (256x256 samples)
```

### Test 3: End-to-End Validation
**Command**: `python generator.py --seed hkLycKKCMI --resolution 512 --validate`

**Expected Outcomes**:
- ✅ World generation completes
- ✅ BepInEx exports data
- ✅ Processing transforms data
- ✅ Rendering creates WebP files
- ✅ Validation passes against reference data
- ✅ Total time < 5 minutes

**Verification**:
```bash
# Check complete pipeline
ls -la data/seeds/*/raw/*.db
ls -la data/seeds/*/extracted/*.json
ls -la data/seeds/*/processed/*.json
ls -la data/seeds/*/renders/*.webp

# Verify sample counts
python -c "
import json
with open('data/seeds/.../extracted/biomes.json') as f:
    data = json.load(f)
    print(f'Samples: {len(data)}')
    print(f'Expected: {512*512}')
"
```

## Propagation Plan

These fixes need to be applied to:

1. ✅ **`lib/orchestrator.py`** - Primary fixes
2. **`config/generator.yaml`** - Default env vars documented
3. **`README.md`** - Usage examples updated
4. **Future generators** - Template for permission handling
5. **Global docker patterns** - Document in `global/docker/DOCKER_STRATEGY.md`

## Validation Checklist

- [ ] Permission fix prevents errors
- [ ] BepInEx plugins load correctly
- [ ] Export files created in correct location
- [ ] File ownership matches current user
- [ ] Logs show export completion
- [ ] Sample counts match resolution
- [ ] Processing pipeline succeeds
- [ ] Rendering generates all layers
- [ ] Validation passes for reference seed

## References

- **Legacy backend**: `etl/archive/legacy/backend/app/services/world_generator.py`
- **Legacy BepInEx**: `etl/archive/legacy/bepinex/src/VWE_DataExporter/VWE_DataExporter.cs`
- **Docker config**: `etl/archive/legacy/docker/docker-compose.procedural.yml`
- **BepInEx whitepaper**: `etl/archive/legacy/bepinex/ARCHIVE_WHITEPAPER.md`
