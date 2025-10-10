# Legacy VWE Components - Archived

**Archive Date:** 2025-01-27  
**Status:** ARCHIVED - Superseded by new ETL architecture  
**Reason:** Project overhaul to modular, self-contained ETL generators

## Archived Components

### `backend/` - FastAPI Backend Service
- **Status:** DEPRECATED
- **Replaced By:** New ETL generators in `etl/experimental/`
- **Key Features:** Redis job queue, Docker orchestration, API endpoints
- **Lessons Learned:** Complex orchestration replaced by direct integration

### `bepinex/` - BepInEx Plugin System  
- **Status:** PRODUCTION READY (but archived for new architecture)
- **Key Features:** VWE_AutoSave, VWE_DataExporter plugins
- **Performance:** 3x faster than Docker orchestration
- **Note:** Plugins validated and working, but approach superseded

### `data/` - Generated World Data
- **Status:** PRESERVED
- **Content:** Generated world data from seed `hkLycKKCMI`
- **Purpose:** Reference data for validation and testing
- **Note:** Data preserved for new ETL approaches to validate against

### `docker/` - Docker Orchestration
- **Status:** DEPRECATED  
- **Replaced By:** Self-contained Docker in new ETL generators
- **Key Features:** Docker Compose, warm containers, orchestration
- **Lessons Learned:** Complex orchestration replaced by simpler approaches

### `procedural-export/` - Procedural Metadata System
- **Status:** EXPERIMENTAL (archived for new architecture)
- **Key Features:** Browser visualization, Jupyter notebooks, metadata extraction
- **Note:** Approach superseded by new ETL generators

### `scripts/` - Utility Scripts
- **Status:** DEPRECATED
- **Replaced By:** Scripts in individual ETL generators
- **Key Features:** Log management, environment validation
- **Note:** Functionality moved to generator-specific scripts

## Migration Notes

### What's Preserved
- **Validation Data:** All generated data from seed `hkLycKKCMI` preserved
- **Lessons Learned:** Whitepapers document key insights and fixes
- **Working Code:** BepInEx plugins are production-ready if needed

### What's Replaced
- **Backend API:** Replaced by individual ETL generator APIs
- **Docker Orchestration:** Replaced by self-contained generator containers
- **Job Queue:** Replaced by direct generator execution
- **Complex Pipeline:** Replaced by simple, focused generators

### Key Lessons Applied to New Architecture
1. **Direct Integration Better:** BepInEx plugins eliminate orchestration complexity
2. **Self-Contained is Key:** Each approach should be independent
3. **Performance Matters:** 3x speed improvement justifies architectural change
4. **Simpler is Better:** Fewer moving parts = more reliable

## New Architecture

The new ETL architecture uses:
- **`etl/experimental/`** - New self-contained generators
- **`etl/stable/`** - Production-ready approaches  
- **`etl/archive/`** - This directory (legacy components)
- **`global/`** - Shared constants, generators, and utilities

## References

- **CLAUDE.md** - Project overview and architecture
- **Individual whitepapers** - Detailed analysis of each component
- **Validation data** - Reference data for new approaches
- **BepInEx plugins** - Working plugins if needed for reference

---

**Note:** This archive preserves the complete legacy system for reference. The new ETL architecture builds on lessons learned while providing a cleaner, more maintainable approach.
