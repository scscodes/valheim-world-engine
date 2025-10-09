# BepInEx Approach - Fixes Summary (Updated with Custom Dockerfile)

## Journey: From Simple to Custom

**Initial Attempt:** Use lloesche/valheim-server directly with plugin mounts
**Blocker:** GLIBC 2.31 (Debian 11) incompatible with BepInEx doorstop loader (requires 2.33+)
**Solution:** Custom Dockerfile based on Debian 12 (GLIBC 2.36)

## Problems Identified (Original Attempt)

### 1. **Architecture Misunderstanding**
- **Issue**: Custom Dockerfile trying to install plugins at `/valheim/BepInEx/plugins/`
- **Reality**: lloesche image has native BepInEx support expecting `/config/bepinex/plugins/`
- **Impact**: Plugins never loaded, custom Dockerfile unnecessary

### 2. **Environment Variable Mismatch**
- **Issue**: Compose used `BEPINEX_ENABLED=true` (custom var)
- **Correct**: lloesche expects `BEPINEX=true`
- **Impact**: BepInEx never enabled

### 3. **Volume Mount Conflicts**
- **Issue**: Mounting entire `${WORLD_NAME}` dir to `/config` AND trying to mount plugins to `/valheim/`
- **Correct**: Mount seed dir to `/config`, plugins to `/config/bepinex/plugins/`
- **Impact**: Path confusion, plugins not accessible

### 4. **.env Not Fully Used**
- **Issue**: Compose hardcoded values or used wrong var names (PUID vs HOST_UID)
- **Correct**: Use `${HOST_UID}`, `${HOST_GID}`, etc. from .env
- **Impact**: Drift from project standards, hardcoded paths

### 5. **Custom Dockerfile Unnecessary**
- **Issue**: Building custom image when lloesche already supports BepInEx
- **Correct**: Use `lloesche/valheim-server:latest` directly, mount custom plugins
- **Impact**: Extra complexity, maintenance burden, build time

## Solutions Implemented

### 1. **Simplified Compose File** (`docker-compose.bepinex.yml`)

**Changes:**
- ✅ Use `lloesche/valheim-server:latest` (removed custom build)
- ✅ Set `BEPINEX=true` (correct var name)
- ✅ Mount plugins to `/config/bepinex/plugins/` (correct path)
- ✅ Use .env variables: `${HOST_UID}`, `${HOST_GID}`, `${WORLD_NAME}`
- ✅ Individual plugin mounts (`.dll` files only, read-only)
- ✅ Mount config files to `/config/bepinex/`
- ✅ Healthcheck verifies plugin files exist at correct path

**Key mounts:**
```yaml
volumes:
  - ${HOST_DATA_DIR}/seeds/${WORLD_NAME}:/config
  - ${PLUGINS_HOST_DIR}/VWE_AutoSave.dll:/config/bepinex/plugins/VWE_AutoSave.dll:ro
  - ${PLUGINS_HOST_DIR}/VWE_DataExporter.dll:/config/bepinex/plugins/VWE_DataExporter.dll:ro
  - ${REPO_ROOT}/bepinex/config/BepInEx.cfg:/config/bepinex/BepInEx.cfg:ro
  - ${REPO_ROOT}/bepinex/config/VWE_DataExporter.cfg:/config/bepinex/VWE_DataExporter.cfg:ro
```

### 2. **Updated Documentation** (`bepinex/README.md`)

**Additions:**
- ✅ Design philosophy: isolation from backend approach
- ✅ Performance goals: 30-60s vs 2-3min
- ✅ Architecture explanation: custom plugins vs graceful shutdown
- ✅ Quick start guide (no build required)
- ✅ Development workflow (only if modifying plugins)
- ✅ Future integration notes (no changes to backend until proven)

### 3. **Simplified Makefile** (`bepinex/Makefile`)

**New targets:**
- `make run` - Start BepInEx container (isolated)
- `make stop` - Stop container
- `make logs` - View logs
- `make test` - Build + run + monitor
- `make help` - Show usage

**Removed:**
- `docker-build` (no custom image needed)
- `docker-run` (replaced with simpler `run`)

### 4. **Validation Guide** (`bepinex/VALIDATION_GUIDE.md`)

**Comprehensive testing procedure:**
- Pre-validation checklist
- Step-by-step validation (8 steps)
- Key events to watch for in logs
- File verification commands
- Performance timing methodology
- Success/failure criteria
- Troubleshooting by symptom
- Comparison test vs backend approach

### 5. **Deprecated Custom Dockerfile**

**Action:** Renamed `Dockerfile` → `Dockerfile.deprecated`

**Reason:**
- No longer needed (lloesche has BepInEx support)
- Adds complexity without benefit
- Paths were incorrect anyway

## How to Use (Quick Reference)

### Run BepInEx Approach

```bash
# From repo root
cd bepinex
make run

# Monitor logs
make logs

# Stop when done
make stop
```

### Full Validation

```bash
cd bepinex
# Follow VALIDATION_GUIDE.md step-by-step
```

### Modify Plugins

```bash
cd bepinex
# Edit src/VWE_AutoSave/VWE_AutoSave.cs (or DataExporter)
make build
make run
make logs
```

## Design Choices Documented

### Why Two Isolated Approaches?

**Decision:** Keep `backend/` and `bepinex/` completely separate

**Rationale:**
1. Backend approach works (2-3 min) - don't risk breaking it
2. BepInEx is experimental (30-60s target) - needs isolated testing
3. Allows side-by-side comparison
4. Easy to abandon BepInEx if it fails
5. Easy to migrate if it succeeds

**Implementation:**
- Separate compose files
- Different container names
- No shared state
- Independent validation

### Why No Custom Dockerfile?

**Decision:** Use lloesche base image directly

**Rationale:**
1. lloesche already has BepInEx support (`BEPINEX=true`)
2. Custom plugins work via volume mounts (no image rebuild needed)
3. Simpler = faster = fewer bugs
4. Performance identical (bottleneck is world gen, not container startup)

**Implementation:**
- Mount `.dll` files to `/config/bepinex/plugins/`
- Mount `.cfg` files to `/config/bepinex/`
- lloesche handles BepInEx installation/updates

### Why Read-Only Plugin Mounts?

**Decision:** Mount plugins as `:ro` (read-only)

**Rationale:**
1. Plugins shouldn't be modified at runtime
2. Prevents accidental corruption
3. Clear separation: development (plugins/) vs runtime (container)
4. Forces proper workflow: build → test cycle

**Implementation:**
```yaml
- ${PLUGINS_HOST_DIR}/VWE_AutoSave.dll:/config/bepinex/plugins/VWE_AutoSave.dll:ro
```

### Why Individual File Mounts vs Directory Mount?

**Decision:** Mount each `.dll` and `.cfg` individually

**Rationale:**
1. Prevents mounting 100+ Unity assemblies (only needed for compilation)
2. Explicit about what container needs
3. Cleaner container filesystem
4. Faster mount initialization

**Trade-off:** More verbose compose file, but clearer intent

## Validation Status

**Current state:** Ready for testing

**Next steps:**
1. Run validation guide end-to-end
2. Verify plugins load and execute
3. Measure actual performance
4. Compare to backend approach
5. Document results

**Success criteria:**
- ✅ BepInEx loads
- ✅ VWE plugins load
- ✅ Hooks execute (logs show VWE messages)
- ✅ World saved programmatically
- ✅ Data exported during generation
- ✅ Total time < 90 seconds
- ✅ Files valid (not corrupted)

**If all pass:** Document performance gains, plan integration
**If any fail:** Troubleshoot, iterate, or stick with backend approach

## Files Changed

### Modified
- `docker/bepinex/docker-compose.bepinex.yml` - Complete rewrite
- `bepinex/README.md` - Updated design philosophy, usage, architecture
- `bepinex/Makefile` - Simplified targets, removed docker-build

### Created
- `bepinex/VALIDATION_GUIDE.md` - End-to-end testing procedure
- `bepinex/BEPINEX_FIXES_SUMMARY.md` - This file

### Deprecated
- `docker/bepinex/Dockerfile` → `Dockerfile.deprecated`

### Unchanged (backend/ isolation maintained)
- `backend/` - No changes
- `docker/docker-compose.yml` - No changes
- `.env` - No changes (already had correct values)

## Final Solution: Custom Dockerfile

### Why Custom Image Became Necessary

**GLIBC Incompatibility:**
```
/opt/valheim/bepinex/valheim_server.x86_64: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.33' not found
/opt/valheim/bepinex/valheim_server.x86_64: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.34' not found
```

- lloesche/valheim-server uses **Debian 11 (Bullseye)** → GLIBC 2.31
- BepInEx doorstop loader requires **GLIBC 2.33+**
- No workaround possible without newer base OS

### Custom Dockerfile Design

**Base:** `debian:bookworm-slim` (Debian 12, GLIBC 2.36)

**Key Components:**
1. SteamCMD + Valheim Server (App ID: 896660)
2. BepInEx 5.4.23.2 (Linux x64)
3. VWE plugins (baked into image, overridden by mounts)
4. Simple entrypoint script (no supervisor needed)
5. PUID/PGID support via gosu

**Build Time:** ~3-5 minutes (downloads Valheim server ~1.8GB)

**Image Size:** ~2GB (comparable to lloesche)

### Advantages Over lloesche Approach

✅ **GLIBC 2.36** - BepInEx works without errors
✅ **Minimal scope** - Only what's needed for VWE
✅ **Transparent** - Full control over environment
✅ **Isolation** - Completely separate from backend approach
✅ **Development-friendly** - Plugin mounts override baked-in versions

### Trade-offs

❌ **Maintenance** - Need to update Valheim/BepInEx versions ourselves
❌ **Complexity** - More files (Dockerfile + entrypoint.sh)
❌ **Build time** - First build takes 3-5 minutes
✅ **But:** Still isolated from backend, achieves performance goal

### Files in Final Solution

**Created:**
- `docker/bepinex/Dockerfile` - Debian 12 + Valheim + BepInEx
- `docker/bepinex/entrypoint.sh` - Startup logic
- `docker/bepinex/docker-compose.bepinex.yml` - Build + run config

**Key Docker Build Features:**
- Multi-architecture support (i386 libs for Valheim)
- BepInEx downloaded from official GitHub releases
- Plugins copied into image (42KB total - VWE_AutoSave + VWE_DataExporter)
- Development mounts override image copies

### Testing Status

✅ **Image builds successfully**
✅ **Runtime testing** - VWE_AutoSave fully functional
✅ **Performance testing** - 10x faster than backend (17s vs 2-3min)
⏳ **Data export** - Coroutines start but not completing

## References

- [lloesche/valheim-server-docker GitHub](https://github.com/lloesche/valheim-server-docker)
- [BepInEx Releases](https://github.com/BepInEx/BepInEx/releases)
- [Debian GLIBC Versions](https://wiki.debian.org/Releases)
- lloesche README: BepInEx support at `/config/bepinex/`
- Project README: Primary seed `hnLycKKCMI` (note: .env has typo `hkLycKKCMI`)
