# Docker Directory Whitepaper

**Directory:** `docker/`  
**Status:** ACTIVE - Production Configuration  
**Date:** 2025-01-27  
**Purpose:** Comprehensive documentation of Docker orchestration configurations for Valheim World Engine

## Overview

The `docker/` directory contains the **current production Docker Compose configurations** and Dockerfiles for orchestrating the Valheim World Engine's containerized services. This directory is **actively used** in production and development workflows as documented in `CLAUDE.md`.

## Directory Structure

```
docker/
├── bepinex/
│   ├── docker-compose.bepinex.yml    # BepInEx-specific orchestration
│   ├── Dockerfile                    # Custom Valheim + BepInEx image
│   └── entrypoint.sh                 # Container startup script
├── docker-compose.yml                # Main production orchestration
├── docker-compose.procedural.yml     # Procedural export approach
├── docker-compose.procedural.yml.bak # Backup of procedural config
├── valheim-server/
│   └── plugins/                      # Empty directory
└── worldgen-runner/
    └── Dockerfile                    # Base Valheim server image
```

## File Analysis

### 1. Main Production Configuration (`docker-compose.yml`)

**Purpose:** Primary Docker Compose configuration for the VWE stack  
**Status:** ACTIVE - Current Production Configuration  
**Key Services:**
- `redis`: Redis 7 Alpine for job queue and caching
- `backend`: FastAPI application server
- `worker`: RQ background job processor
- `worldgen-runner`: Base Valheim server image (build-only profile)
- `validator`: Environment validation service

**Notable Features:**
- Worker runs as root (`user: "0:0"`) for Docker socket access
- Volume mounts for development hot-reloading
- Environment variable configuration via `.env` file
- Docker socket mounting for container orchestration

### 2. BepInEx Configuration (`bepinex/docker-compose.bepinex.yml`)

**Purpose:** BepInEx-specific Valheim server orchestration  
**Status:** ACTIVE - Referenced in ETL workflows  
**Key Features:**
- Custom VWE plugins (VWE_AutoSave, VWE_DataExporter)
- BepInExPack_Valheim 5.4.2333 integration
- Plugin mounting from host filesystem
- Graceful shutdown with extended timeout (120s)

**Environment Variables:**
- `VWE_AUTOSAVE_ENABLED=true`
- `VWE_AUTOSAVE_DELAY=2`
- `VWE_DATAEXPORT_ENABLED=true`
- `VWE_DATAEXPORT_FORMAT=both`
- `VWE_DATAEXPORT_DIR=/config/world_data`

### 3. Procedural Export Configuration (`docker-compose.procedural.yml`)

**Purpose:** Procedural metadata extraction approach  
**Status:** ACTIVE - Referenced in ETL workflows  
**Key Features:**
- VWE_ProceduralMetadata plugin integration
- Optimal sampling configuration
- 512x512 resolution for debugging
- Extended stop grace period (300s)

**Environment Variables:**
- `VWE_PROCEDURAL_ENABLED=true`
- `VWE_PROCEDURAL_EXPORT_DIR=/config/procedural_metadata`
- `VWE_PROCEDURAL_OPTIMAL_SAMPLING=true`
- `VWE_PROCEDURAL_RESOLUTION=512`

### 4. BepInEx Dockerfile (`bepinex/Dockerfile`)

**Purpose:** Custom Valheim server image with BepInEx integration  
**Status:** ACTIVE - Used by both BepInEx and Procedural configurations  
**Base Image:** Debian 12 (Bookworm) for GLIBC 2.36+ compatibility  
**Key Features:**
- SteamCMD installation and Valheim server download
- BepInExPack_Valheim 5.4.2333 integration
- VWE custom plugins pre-installed
- Proper file ownership and permissions
- Multi-stage build with valheim user

**Dependencies:**
- SteamCMD for Valheim server installation
- BepInExPack_Valheim for plugin framework
- VWE_AutoSave.dll, VWE_DataExporter.dll, Newtonsoft.Json.dll

### 5. Entrypoint Script (`bepinex/entrypoint.sh`)

**Purpose:** Container startup and user management  
**Status:** ACTIVE - Used by BepInEx Dockerfile  
**Key Features:**
- PUID/PGID handling for file ownership
- Plugin copying from mounted volumes
- BepInEx configuration and environment setup
- Valheim server launch with doorstop preloading

**Critical Functions:**
- User switching from root to valheim user
- Plugin mounting and copying
- Environment variable export for VWE plugins
- BepInEx doorstop configuration

### 6. Worldgen Runner Dockerfile (`worldgen-runner/Dockerfile`)

**Purpose:** Base Valheim server image for world generation  
**Status:** ACTIVE - Referenced in main docker-compose.yml  
**Base Image:** Ubuntu 22.04  
**Key Features:**
- SteamCMD installation
- Valheim dedicated server pre-installation
- Simple entrypoint for testing

### 7. Backup Configuration (`docker-compose.procedural.yml.bak`)

**Purpose:** Backup of procedural configuration with 1024x1024 resolution  
**Status:** ARCHIVED  
**Key Difference:** Full-scale 1024x1024 sampling vs 512x512 in main config

## Technical Details

### Container Orchestration

The Docker configurations supported multiple approaches:

1. **Production Stack**: Redis + FastAPI + RQ Worker
2. **BepInEx Approach**: Custom Valheim server with BepInEx plugins
3. **Procedural Approach**: Metadata extraction without full world generation

### File Ownership Management

Critical for Docker volume mounting:
- `PUID`/`PGID` environment variables
- `gosu` for user switching
- Proper ownership of `/config` directories
- Host UID/GID mapping

### Plugin Integration

BepInEx plugins were integrated through:
- Host volume mounting for development
- Image copying for production
- Configuration file mounting
- Environment variable passing

### Network Configuration

- UDP ports 2456, 2457, 2458 for Valheim server
- Redis on port 6379
- FastAPI on port 8000

## Current Usage

This directory is **actively used** in the current production system:

1. **Main Production Stack** (`docker-compose.yml`) - Referenced in `CLAUDE.md`
2. **BepInEx Workflows** (`bepinex/docker-compose.bepinex.yml`) - Used in ETL processes
3. **Procedural Export** (`docker-compose.procedural.yml`) - Referenced in ETL workflows
4. **World Generation** (`worldgen-runner/Dockerfile`) - Used by main compose file

## Validation Results

### ✅ Files Analyzed
- All Docker Compose configurations reviewed
- All Dockerfiles examined
- All shell scripts analyzed
- Directory structure documented

### ✅ Dependencies Mapped
- SteamCMD integration
- BepInEx framework
- VWE custom plugins
- File ownership management
- Network port configuration

### ✅ Status Confirmed
- Main configuration is **ACTIVE** and referenced in `CLAUDE.md`
- BepInEx configurations are **ACTIVE** and used in ETL workflows
- All Dockerfiles are **ACTIVE** and referenced by compose files
- Directory is **NOT** safe for purge - contains active production code

## Purge Readiness

**Status:** ❌ NOT READY FOR PURGE

**Justification:**
1. Main `docker-compose.yml` is **ACTIVE** and referenced in `CLAUDE.md`
2. BepInEx configurations are **ACTIVE** and used in ETL workflows
3. All Dockerfiles are **ACTIVE** and referenced by compose files
4. Directory contains **CURRENT PRODUCTION CODE**

**Impact Assessment:**
- **HIGH IMPACT** on current functionality if purged
- **HIGH IMPACT** on production systems if purged
- **HIGH IMPACT** on development workflow if purged
- **NEGATIVE IMPACT** on codebase functionality if purged

## Recommendations

1. **DO NOT PURGE**: This directory contains active production configurations
2. **DOCUMENTATION**: This whitepaper should be moved to `docs/` for reference
3. **MAINTENANCE**: Continue maintaining these configurations as they are actively used
4. **VALIDATION**: Verify all references are correct and up-to-date

## Conclusion

The `docker/` directory contains the **current production Docker orchestration configurations** that are actively used by the Valheim World Engine system. The main `docker-compose.yml` file is referenced in `CLAUDE.md` as the primary way to start the VWE stack, and the BepInEx configurations are used in ETL workflows.

**This directory is NOT ready for purge and contains essential production code.**
