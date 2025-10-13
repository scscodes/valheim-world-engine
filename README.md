# Valheim World Engine - Modular ETL Architecture

## Executive Summary

A performant, accurate third-party mapping solution for Valheim using a modular ETL architecture. The system generates and processes world data through self-contained generators, with a modern web client for visualization.

**Primary Test Seed:** `hkLycKKCMI`  
**Architecture:** Modular ETL generators with global configuration system

---

## 1. Project Structure

```
valheim-world-engine/
├── etl/                          # ETL Pipeline Approaches
│   ├── experimental/             # New experimental generators
│   ├── stable/                   # Production-ready approaches
│   └── archive/                  # Legacy components (archived)
│       └── legacy/               # Previous generation work
│           ├── backend/          # FastAPI backend (archived)
│           ├── bepinex/          # BepInEx plugins (archived)
│           ├── data/             # Generated data (preserved)
│           ├── docker/           # Docker orchestration (archived)
│           ├── procedural-export/ # Procedural system (archived)
│           └── scripts/          # Utility scripts (archived)
├── global/                       # Global Configuration System
│   ├── data/                     # YAML configuration files
│   ├── generators/               # Code generators (C#, Python, TS)
│   ├── logging/                  # VWE logging system
│   └── docker/                   # Docker management
├── docs/                         # Documentation
└── README.md                     # This file
```

---

## 2. Architecture Overview

### 2.1 System Components

```
┌─────────────────┐
│   Next.js UI    │
│   (Frontend)    │
└────────┬────────┘
         │ REST/GraphQL
         ▼
┌─────────────────┐      ┌──────────────┐
│  ETL Generators │◄────►│   Global     │
│  (Self-contained)│     │  Constants   │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Generated Data │      │   Docker     │
│  (Per Generator)│      │  Containers  │
└─────────────────┘      └──────┬───────┘
                                 │
                         ┌───────┴────────┐
                         │                │
                    ┌────▼─────┐    ┌────▼─────┐
                    │ Valheim  │    │ BepInEx  │
                    │  Server  │    │ Plugins  │
                    └──────────┘    └──────────┘
```

### 2.2 Data Flow

```
User Input (Seed) → ETL Generator Selection → Self-contained Processing
                                        ↓
                    World Generation (Docker: valheim-server + BepInEx)
                                        ↓
                    Data Export (JSON, PNG, metadata)
                                        ↓
                    Validation & Quality Check
                                        ↓
                    ETL Processing (Python/FastAPI)
                                        ↓
                    Storage (SQLite + File System)
                                        ↓
                    Cache Population (Redis)
                                        ↓
                    API Response → Client Rendering
```

---

## 2. Technical Standards & Configuration

### 2.1 Mapping Standards (CRITICAL - No Drift)

Create a single `mapping_config.py` or `mapping_config.json` file that defines:

#### Coordinate System
- **Origin:** Valheim world center (0, 0)
- **Unit:** Meters (Valheim native units)
- **Coordinate Format:** `(x, y, z)` where:
  - `x`: East-West axis
  - `y`: Height/Elevation
  - `z`: North-South axis
- **Bounds:** -10500 to +10500 on both x and z axes
- **Normalization:** All coordinates stored in raw Valheim units

#### Biome Color Scheme
```python
BIOME_COLORS = {
    "Meadows": "#4CAF50",      # Green
    "BlackForest": "#1B5E20",  # Dark Green
    "Swamp": "#5D4037",        # Brown
    "Mountain": "#E0E0E0",     # Light Gray
    "Plains": "#FDD835",       # Yellow
    "Mistlands": "#9E9E9E",    # Gray
    "Ashlands": "#D32F2F",     # Red
    "DeepNorth": "#1E88E5",    # Blue
    "Ocean": "#0277BD",        # Dark Blue
}

# Shoreline detection and rendering
SHORELINE_CONFIG = {
    "detection_method": "heightmap_biome_intersection",
    "water_level": 30.0,  # Sea level in Valheim units ✓ CONFIRMED
    "shoreline_depth_threshold": -5.0,  # ⚠️ NEEDS VALIDATION - How far below water to consider shoreline
    
    # Visual representation: diagonal stripe pattern
    "pattern_type": "diagonal_stripes",  # Options: "diagonal_stripes", "dots", "crosshatch"
    "pattern_angle": 45,  # Degrees for stripe pattern
    "pattern_spacing": 4,  # ⚠️ NEEDS VALIDATION - Pixels between pattern elements (adjust based on rendering tests)
    "pattern_width": 2,   # ⚠️ NEEDS VALIDATION - Width of pattern lines in pixels (adjust based on rendering tests)
    
    # Color blending
    "ocean_color": "#0277BD",
    "blend_ratio": 0.5,  # ⚠️ NEEDS VALIDATION - 50% biome color, 50% ocean color in pattern (adjust for visibility)
    
    # Pattern rendering
    # For each biome's shoreline: alternate between biome_color and ocean_color
    # using the specified pattern type
}

# Shoreline detection logic:
# A cell is "shoreline" if:
# 1. Height < water_level (underwater)
# 2. Height > (water_level + shoreline_depth_threshold)
# 3. Biome != Ocean
# 4. At least one adjacent cell is Ocean OR height > water_level
```

#### Height Normalization
- **Sea Level:** 30.0 (Valheim units)
- **Min Rendered Height:** -50.0
- **Max Rendered Height:** 200.0
- **Gradient Steps:** 20 levels for heightmap visualization

#### Rasterization & Neighborhood
- **Default Render Resolution:** 2048×2048 (scalable via `RENDER_RESOLUTION_PX`)
- **World Size:** 21000 meters (diameter)
- **Meters per Pixel:** `METERS_PER_PIXEL = 21000 / RENDER_RESOLUTION_PX`
- **Adjacency:** 8-connected (use 8-neighbor for shoreline)
- **Performance:** All raster operations must be NumPy-vectorized; avoid Python per-pixel loops at ≥2048²

#### Tile Configuration (Future)
- **Zoom Levels:** ⚠️ NEEDS VALIDATION - 0-5 proposed (where 0 is full world view)
- **Tile Size:** ⚠️ NEEDS VALIDATION - 256x256 pixels standard but not confirmed as optimal
- **Format:** WebP for raster, GeoJSON for vector

### 2.2 Configuration Validation Status

Before proceeding to Phase 2, all configuration values must be validated and documented. The following checklist tracks validation status:

**✓ CONFIRMED Values** (from official game data/modding community):
- [x] World radius: 10500m (10000m + 500m edge)
- [x] Sea level: 30.0m
- [x] Coordinate system: (x=east/west, y=height, z=north/south)
- [x] Zone size: 64m x 64m
- [x] Units: meters
- [x] Storm wave range: 28-34m (±2-4m from sea level)
- [x] Terrain modification limits: ±8m from original height

**⚠️ REQUIRES VALIDATION** (must be determined from actual data):
- [ ] Min terrain height → Extract from primary seed world data
- [ ] Max terrain height → Extract from primary seed world data
- [ ] Shoreline depth threshold → Test multiple values (-3m, -5m, -8m) against reference
- [ ] Gradient steps for heightmap → Analyze height distribution from world data
- [ ] Pattern spacing/width for shoreline → Visual testing for optimal readability
- [ ] Tile size for future zoom levels → Rendering performance tests

**Validation Process:**
1. Generate primary seed (hnLycKKCMI) using docker container
2. Extract world metadata using MakeFwl (.fwl) and generate biomes/heightmap via BepInEx exporter; `.db` parsing deferred (entities only)
3. Analyze heightmap data to determine actual min/max terrain values
4. Calculate height distribution to determine optimal gradient steps
5. Test shoreline detection with multiple threshold values (-3m, -5m, -8m)
6. Compare rendered output against valheim-map.world reference images
7. Adjust pattern parameters based on visual clarity
8. Document all final values with data sources in `mapping_config.py`

**Critical Rule:** No estimated values may be committed to `mapping_config.py`. Each configuration parameter must include:
- The validated value
- Source of validation (e.g., "Extracted from seed hnLycKKCMI on 2025-10-07")
- Any alternative values tested and why they were rejected

### 2.3 File Structure Standards

```
data/
├── seeds/
│   └── {seed_hash}/
│       ├── raw/
│       │   ├── {seed_hash}.db       # Valheim world save (binary, not SQLite)
│       │   ├── {seed_hash}.fwl      # Valheim world metadata
│       │   ├── {seed_hash}.db.old   # Optional backup written by server
│       │   └── {seed_hash}.fwl.old  # Optional backup written by server
│       ├── extracted/
│       │   ├── makefwl_output.json  # MakeFwl extraction
│       │   ├── biomes.json          # Exported by BepInEx plugin (headless)
│       │   └── heightmap.npy        # Exported by BepInEx plugin (headless)
│       │   ├── worldgen_plan.json   # Stage 1: Orchestration plan (env, mounts, readiness)
│       │   └── worldgen_logs.txt    # Stage 1: Container stdout/stderr logs (for diagnostics)
│       ├── processed/
│       │   ├── biomes.json
│       │   ├── heightmap.json
│       │   ├── shoreline.json       # Shoreline detection grid
│       │   ├── locations.json       # Entities/dungeons/spawns
│       │   └── metadata.json
│       └── renders/
│           ├── base_layer.webp
│           ├── biomes_layer.webp
│           ├── land_sea_layer.webp
│           ├── heightmap_layer.webp
│           └── shoreline_overlay.webp  # Transparent overlay
```

---

## 3. MVP Feature Specification

### 3.1 Core Features

#### User Input
- Single text input field for seed string
- Submit button to trigger generation
- Loading indicator with status messages
- Error notification on failure

#### Map Display
- Fixed zoom level (full world bounds)
- Static pan (show entire 21km x 21km world)
- **Base Layer Selection** (radio buttons - select one):
  - **Biomes Layer** (colored regions)
  - **Land/Sea Layer** (binary visualization)
  - **Heightmap Gradient** (elevation visualization)
- **Overlay Toggle** (checkbox - independent of base layer):
  - **Shoreline Overlay** (diagonal stripe pattern showing underwater biome transitions)

**Layer Interaction:** The shoreline overlay can be toggled on/off regardless of which base layer is active. When enabled, it renders as a semi-transparent overlay showing the diagonal stripe pattern (alternating between appropriate biome color and ocean blue) on areas where terrain extends below the waterline but is not deep ocean.

#### Seed Caching
- Check if seed exists in database before generation
- Display cached results immediately if available
- Optional "Force Regenerate" button (future enhancement)

### 3.2 Out of Scope for MVP
- Zoom controls
- Interactive panning
- Coordinate search
- Entity markers (bosses, dungeons, resources)
- User accounts
- Seed sharing/permalinks
- Multiple simultaneous overlay layers (only shoreline overlay for MVP)

---

## 4. ETL Pipeline Design

### 4.0 Pipeline Organization

**Legacy ETL Approaches** (in root directory):
- **`bepinex/`** - BepInEx plugin-based dense sampling (production ready)
- **`procedural-export/`** - Procedural metadata extraction (experimental)

**New ETL Approaches** (in `etl/` directory):
- **`etl/stable/`** - New production-ready approaches (validated & deployed)
- **`etl/experimental/`** - New early-stage approaches (research & development)  
- **`etl/archive/`** - New deprecated approaches (historical reference)

See `etl/README.md` for detailed information about the new ETL maturity levels and migration paths.

### 4.1 Pipeline Stages

#### Stage 1: World Generation
**Trigger:** API request with new seed
**Process:**
1. Create job in Redis queue
2. Spin up docker container with `vwe/worldgen-runner:latest` (preinstalled Valheim) or fallback `lloesche/valheim-server` (BepInEx enabled)
3. Configure with seed-specific environment variables and mounts:
   - `WORLD_NAME={seed_hash}`, `WORLD_SEED={seed}`, `SERVER_PUBLIC=0`, `TZ=UTC`, `UPDATE_ON_START=1`
   - Mount `data/seeds/{seed_hash}/raw` → `/config/worlds_local`
   - Mount BepInEx exporter plugin to `/config/BepInEx/plugins`
4. Wait for readiness and export completion:
   - Watch logs for `Game server connected`, `Zonesystem Start`, or `Export complete`
   - Require `.fwl` and `.db` present and size-stable for 10s
   - Timeout after 15 minutes with logs captured
5. Ensure `{seed_hash}.db/.fwl` (or `.old` backups) are present under `raw/` and exporter artifacts (`biomes.json`, `heightmap.npy`) under `extracted/`. Persist container logs to `extracted/worldgen_logs.txt`.
6. Shutdown and cleanup container

**Output:** Raw world files in `data/seeds/{seed_hash}/raw/`

#### Stage 2: Metadata Extraction
**Trigger:** Completion of Stage 1
**Process:**
1. Execute MakeFwl binary on `.fwl` file
2. Parse MakeFwl JSON output
3. Store raw extraction in `extracted/` directory

**Output:** `makefwl_output.json`

#### Stage 3: Data Processing
**Trigger:** Completion of Stage 2
**Process:**
1. Parse world database (`.db` file) for location entities
2. Transform MakeFwl data into standardized format (using mapping_config)
3. Generate processed data files:
   - Biome grid data
   - Heightmap array
   - **Shoreline detection grid** (identify cells meeting shoreline criteria)
   - Location/entity list
4. Calculate world statistics (biome percentages, elevation stats, shoreline coverage)

**Output:** Processed JSON files in `processed/` directory

**Shoreline Detection Algorithm (vectorized, 8-neighbor):**
```python
# Masks
under = heightmap < water_level
shallow = heightmap > (water_level + threshold)
not_ocean = biome_map != OCEAN_ID

# 8-neighbor adjacency via 3x3 dilation
land_mask = heightmap >= water_level
ocean_mask = biome_map == OCEAN_ID
adjacent = dilate(land_mask | ocean_mask, kernel_3x3)

shoreline = under & shallow & not_ocean & adjacent
```

#### Stage 4: Render Generation
**Trigger:** Completion of Stage 3
**Process:**
1. Generate base layer images using processed data
2. Create biomes visualization (without shoreline)
3. Create land/sea binary map
4. Create heightmap gradient visualization
5. **Create standalone shoreline overlay with transparency**
6. Store as WebP format (with alpha channel for shoreline overlay)

**Output:** Rendered layer images in `renders/` directory

**Shoreline Overlay Rendering:**
```python
def render_shoreline_overlay(biome_grid, shoreline_grid, config):
    """
    Render standalone shoreline overlay as transparent PNG/WebP.
    Only shoreline areas are visible; everything else is transparent.
    """
    from PIL import Image
    import numpy as np
    
    # Create image with alpha channel (RGBA)
    height, width = biome_grid.shape
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))  # Transparent
    pixels = img.load()
    
    pattern_spacing = config['pattern_spacing']
    pattern_width = config['pattern_width']
    ocean_color = hex_to_rgb(config['ocean_color'])
    
    # Only render shoreline cells
    for y in range(height):
        for x in range(width):
            if shoreline_grid[y, x]:
                biome = biome_grid[y, x]
                biome_color = hex_to_rgb(BIOME_COLORS[biome])
                
                # Determine if this pixel should be ocean or biome color
                # based on diagonal stripe pattern
                if (x + y) % pattern_spacing < pattern_width:
                    # Ocean stripe with partial opacity
                    pixels[x, y] = ocean_color + (180,)  # 70% opacity
                else:
                    # Biome stripe with partial opacity
                    pixels[x, y] = biome_color + (180,)  # 70% opacity
    
    return img  # Returns RGBA image
```

#### Stage 5: Database & Cache Population
**Trigger:** Completion of Stage 4
**Process:**
1. Insert seed metadata into SQLite
2. Store file paths and statistics
3. Populate Redis cache with:
   - Seed lookup keys
   - Layer file paths
   - Quick-access metadata
4. Set cache expiration policies

**Output:** Database records and Redis cache entries

### 4.2 Job Queue Management

**Redis Queue Structure:**
```
Queue: world_generation_jobs
├── Pending
├── Processing
├── Completed
└── Failed
```

**Job Object:**
```json
{
  "job_id": "uuid",
  "seed": "hnLycKKCMI",
  "seed_hash": "sha256_hash",
  "status": "pending|processing|completed|failed",
  "created_at": "timestamp",
  "started_at": "timestamp",
  "completed_at": "timestamp",
  "current_stage": "generation|extraction|processing|rendering|caching",
  "progress": 0-100,
  "error": null
}
```
Framework: RQ for MVP. Worker: `rq worker --url $REDIS_URL vwe`. Retries: 3 with exponential backoff. Redis keys prefix: `vwe:{env}:jobs:*`.

---

## 5. API Design

### 5.1 Endpoints

#### POST /api/v1/seeds/generate
**Request:**
```json
{
  "seed": "hnLycKKCMI",
  "force_regenerate": false
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "seed_hash": "sha256_hash",
  "status": "pending|cached",
  "message": "World generation queued|Using cached data"
}
```

#### GET /api/v1/seeds/{seed_hash}/status
**Response:**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "current_stage": "extraction",
  "progress": 45,
  "estimated_completion": "timestamp",
  "generation_status": {
    "log_path": "/absolute/or/relative/path/to/worldgen_logs.txt",
    "timed_out": false,
    "lines_written": 1234,
    "log_match": true,
    "raw_present": true,
    "extracted_present": false
  }
}
```

#### GET /api/v1/seeds/{seed_hash}/data
**Response:**
```json
{
  "seed": "hnLycKKCMI",
  "seed_hash": "sha256_hash",
  "metadata": {
    "world_size": 21000,
    "sea_level": 30.0,
    "generated_at": "timestamp"
  },
  "layers": {
    "base_layers": {
      "biomes": "/static/seeds/{hash}/renders/biomes_layer.webp",
      "land_sea": "/static/seeds/{hash}/renders/land_sea_layer.webp",
      "heightmap": "/static/seeds/{hash}/renders/heightmap_layer.webp"
    },
    "overlays": {
      "shoreline": "/static/seeds/{hash}/renders/shoreline_overlay.webp"
    }
  },
  "statistics": {
    "biome_percentages": {...},
    "elevation_range": {...},
    "shoreline_coverage_km": 245.3
  }
}
```

---

## 6. Database Schema

### 6.1 SQLite Schema (Development)

```sql
-- Seeds table
CREATE TABLE seeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed_original TEXT NOT NULL,
    seed_hash TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    generation_duration_seconds INTEGER,
    file_size_mb REAL
);

-- Layers table
CREATE TABLE layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed_id INTEGER NOT NULL,
    layer_type TEXT NOT NULL, -- 'biomes', 'land_sea', 'heightmap', 'shoreline_overlay'
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seed_id) REFERENCES seeds(id)
);

-- Statistics table
CREATE TABLE world_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed_id INTEGER NOT NULL,
    stat_key TEXT NOT NULL,
    stat_value TEXT NOT NULL,
    FOREIGN KEY (seed_id) REFERENCES seeds(id)
);

-- Jobs table (can also be Redis-only)
CREATE TABLE generation_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,
    seed_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    current_stage TEXT,
    progress INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Indexes
CREATE INDEX idx_seed_hash ON seeds(seed_hash);
CREATE INDEX idx_seed_layer ON layers(seed_id, layer_type);
CREATE INDEX idx_seed_stats ON world_statistics(seed_id);
CREATE INDEX idx_job_id ON generation_jobs(job_id);
CREATE INDEX idx_status ON generation_jobs(status);
```

---

## 7. Development Phases

### Phase 1: Foundation (Week 1-2)
**Goal:** Establish core infrastructure and standards

**Tasks:**
- [ ] Create project repository structure
- [ ] Define `mapping_config.py` with all standards
- [ ] **Extract actual min/max height values from primary seed using MakeFwl/world data**
- [ ] **Validate and finalize all configuration values marked with ⚠️**
- [ ] **Test coordinate system matches game's pos command output**
- [ ] Setup docker-compose for local development
- [ ] Configure lloesche/valheim-server container
- [ ] Test MakeFwl execution on sample seed
- [ ] Validate MakeFwl output and exporter artifacts (defer `.db` parsing)
- [ ] **Analyze extracted data to determine optimal gradient steps for heightmap**
- [ ] Setup SQLite database with schema
- [ ] Setup Redis container

**Deliverable:** Working local environment that can generate a world + validated configuration file with no estimates

### Phase 2: ETL Pipeline (Week 2-3)
**Goal:** Build complete data processing pipeline

**Tasks:**
- [ ] Implement Stage 1: World Generation orchestration
- [ ] Implement Stage 2: MakeFwl integration
- [ ] Implement Stage 3: Data processing and transformation
- [ ] **Calculate actual terrain statistics from processed data (min/max heights, height distribution)**
- [ ] **Implement shoreline detection algorithm with configurable threshold**
- [ ] **Validate shoreline depth threshold against primary seed (test multiple values: -3m, -5m, -8m)**
- [ ] Implement Stage 4: Basic image rendering (biomes with shoreline patterns)
- [ ] **Test different pattern types and spacing values for optimal visibility**
- [ ] **Compare rendered output against valheim-map.world reference images**
- [ ] Implement Stage 5: Database population
- [ ] Add logging and error handling
- [ ] Create pipeline monitoring script

**Deliverable:** Command-line tool that generates all data for a seed with accurate shoreline rendering and validated configuration

### Phase 3: Backend API (Week 3-4)
**Goal:** Expose pipeline via FastAPI

**Tasks:**
- [ ] Setup FastAPI project structure
- [ ] Implement job queue system with Redis
- [ ] Implement `/seeds/generate` endpoint
- [ ] Implement `/seeds/{hash}/status` endpoint
- [ ] Implement `/seeds/{hash}/data` endpoint
- [ ] Add request validation and error handling
- [ ] Setup static file serving
- [ ] Write API tests

**Deliverable:** Working REST API for world generation

### Phase 4: Frontend MVP (Week 4-5)
**Goal:** Build minimal viable client

**Tasks:**
- [ ] Setup Next.js project
- [ ] Create seed input component
- [ ] Create base layer selection component (radio buttons)
- [ ] **Create shoreline overlay toggle component (checkbox)**
- [ ] Create map display component with layer compositing
- [ ] **Implement CSS/Canvas overlay rendering** (base layer + optional shoreline)
- [ ] Implement API integration
- [ ] Add loading states and error handling
- [ ] Style with Tailwind CSS
- [ ] Test with multiple seeds and layer combinations

**Deliverable:** Working web application with independent base layer selection and shoreline overlay toggle

### Phase 5: Optimization & Testing (Week 5-6)
**Goal:** Ensure performance and accuracy

**Tasks:**
- [ ] Optimize image rendering pipeline
- [ ] Implement Redis caching strategy
- [ ] Add cache invalidation logic
- [ ] Performance testing with multiple concurrent requests
- [ ] Accuracy validation against valheim-map.world
- [ ] Cross-browser testing
- [ ] Documentation

**Deliverable:** Production-ready MVP

---

## 8. Performance Considerations

### 8.1 Current Performance & Optimization Roadmap

**Current Baseline (BepInEx Approach):**
- **512×512 resolution:** ~3 minutes (~175 seconds)
- **2048×2048 resolution:** ~27 minutes
- **Method:** Docker orchestration + BepInEx plugins with immediate save triggers

**Proposed Optimization Strategies (2025-10-10):**

1. **Adaptive Resolution Sampling with Edge Refinement** (50-65% reduction → ~1-1.5 min)
   - Use 256×256 base sampling, detect biome boundaries, resample only at edges with higher density
   - Exploits finding that most detail is needed at transitions, not homogeneous regions

2. **Warm Container Pool with Pre-initialized Valheim State** (50-65% reduction → ~1-1.5 min sustained)
   - Extend warm_container_manager to keep Valheim servers already running (not just installed)
   - Send console command to load seed instead of full server restart (60-90s startup → 10-20s)
   - **Implementation target:** `etl/experimental/warm-pooling/`

3. **Parallel Chunk-Based Sampling** (70-80% reduction → ~45-60 sec)
   - Split world into 4-9 spatial chunks, generate in parallel Docker containers
   - Merge results after completion

See historical analysis in `*_whitepaper.md` files for validation data supporting these strategies.

### 8.2 Optimization Targets

**World Generation:**
- Target: < 5 minutes per seed
- Strategy: Pre-pull Docker images, optimize container resources

**Data Processing:**
- Target: < 30 seconds after world generation
- Strategy: Parallel processing where possible, efficient data structures

**Image Rendering:**
- Target: < 10 seconds per layer
- Strategy: Use optimized libraries (Pillow, NumPy), WebP compression

**API Response Time:**
- Cached data: < 200ms
- Status check: < 50ms

**Client Load Time:**
- Initial page load: < 2 seconds
- Layer switch: < 100ms (cached images)

### 8.2 Caching Strategy

**Redis Cache Layers:**
1. **L1 - Hot Cache (1 hour TTL):**
   - Recently accessed seed metadata
   - Layer file paths
   - Quick statistics

2. **L2 - Warm Cache (24 hour TTL):**
   - Full processed data
   - Job status information

3. **L3 - Cold Cache (7 day TTL):**
   - Historical job records
   - Access statistics

**File System Cache:**
- Keep rendered images indefinitely
- Implement LRU cleanup if storage exceeds threshold

---

## 9. Testing Strategy

### 9.1 Test Seeds
- **Primary:** `hnLycKKCMI` (has reference images)
- **Edge Cases:** 
  - Very short seeds (e.g., "a")
  - Very long seeds
  - Special characters
  - Numeric-only seeds

### 9.2 Accuracy Validation
1. Generate test seed with both systems
2. Compare biome locations at known coordinates
3. **Validate shoreline detection** by comparing sailing routes in-game
4. Validate heightmap values at sample points
5. Cross-reference location spawns
6. **Visual comparison:** Check that shoreline patterns match where players transition from ocean to biome while still in water

### 9.3 Performance Benchmarks
- Measure each pipeline stage duration
- Track memory usage during generation
- Monitor concurrent request handling
- Profile image rendering performance

---

## 10. Future Enhancements (Post-MVP)

### 10.1 Features
- Interactive zoom levels (0-5)
- Smooth panning controls
- Entity/location markers (bosses, dungeons, spawns)
- Resource node visualization
- Coordinate search and jump-to
- Seed comparison tool
- 3D terrain visualization
- **Multiple simultaneous overlays** (shoreline + entities + resources)

### 10.2 Technical Improvements
- Vector tile rendering for performance
- Progressive image loading
- WebSocket for real-time job updates
- User accounts and saved seeds
- API rate limiting
- PostgreSQL migration for production
- CDN integration for static assets
- **Overlay composition on-demand** (allow any combination of overlays)

### 10.3 Advanced Layers
- Terrain slope analysis
- Wind direction visualization
- Biome transition zones
- Resource density heatmaps
- Enemy spawn intensity
- Navigation pathfinding overlays
- **Additional overlays:** Fishing spots, boss altars, trader locations

---

## 11. Risk Mitigation

### 11.1 Known Risks

**Risk:** MakeFwl binary compatibility issues
- **Mitigation:** Test on target Linux environment early, containerize execution

**Risk:** World generation takes too long
- **Mitigation:** Implement timeout limits, job cancellation, clear user expectations

**Risk:** Shoreline detection inaccuracy
- **Mitigation:** Test against known sailing routes in reference seed, adjust depth threshold, validate with in-game exploration

**Risk:** Color scheme doesn't match Valheim aesthetics
- **Mitigation:** Use reference images from primary seed, user testing

**Risk:** Coordinate system misalignment
- **Mitigation:** Validate against known locations early, maintain strict standards

**Risk:** Storage costs for many seeds
- **Mitigation:** Implement cleanup policies, compress old data, LRU eviction

---

## 12. Success Metrics

### 12.1 MVP Success Criteria
- [ ] Generate accurate map for primary seed matching reference images
- [ ] **Shoreline overlay accurately represents underwater biome transitions**
- [ ] **Shoreline overlay works correctly with all three base layers**
- [ ] Complete world generation in < 5 minutes
- [ ] Serve cached results in < 500ms
- [ ] Support 3 base layers + 1 overlay with accurate rendering
- [ ] Handle at least 10 concurrent generation jobs
- [ ] Zero config drift across pipeline stages

### 12.2 User Experience Metrics
- Page load time < 2 seconds
- Layer toggle response < 100ms
- Clear loading indicators during generation
- Intuitive UI requiring no instructions

---

## 13. Development Environment Setup

### 13.1 Prerequisites
```bash
# Required
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- Redis
- Git

# Optional
- PostgreSQL (for production simulation)
```

### 13.2 Initial Setup Commands
```bash
# Clone repository
git clone <repo_url>
cd valhem-world-engine

# Setup Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup Node environment
cd frontend
npm install

# Build worldgen base image (first time)
docker compose --profile build-only build worldgen-runner

# Start Docker services
docker compose up -d --build

# Initialize database
python scripts/init_db.py

# Run tests
pytest tests/
```

---

## 14. Project Structure

```
valhem-world-engine/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── seeds.py
│   │   │   │   └── health.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── mapping_config.py    # SINGLE SOURCE OF TRUTH
│   │   │   └── cache.py
│   │   ├── services/
│   │   │   ├── world_generator.py
│   │   │   ├── extractor.py
│   │   │   ├── processor.py
│   │   │   ├── renderer.py
│   │   │   └── job_queue.py
│   │   ├── models/
│   │   │   ├── seed.py
│   │   │   └── job.py
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   │   ├── SeedInput.tsx
│   │   │   ├── MapDisplay.tsx
│   │   │   ├── BaseLayerSelector.tsx
│   │   │   └── ShorelineOverlayToggle.tsx
│   │   └── lib/
│   ├── public/
│   └── package.json
├── docker/
│   ├── docker-compose.yml
│   └── valheim-server/
├── data/                    # Git-ignored
│   └── seeds/
├── scripts/
│   ├── init_db.py
│   └── validate_seed.py
├── docs/
│   ├── REFERENCES.md
│   └── API.md
├── .env.example
├── .gitignore
└── README.md
```

---

## 15. Next Steps

1. **Review and approve this plan**
2. **Setup development environment** (Phase 1 tasks)
3. **Execute configuration validation process** (see Section 2.2):
   - Test MakeFwl with primary seed to understand exact output format
   - Extract and validate actual terrain values
   - Test shoreline detection threshold values
   - Finalize mapping_config.py with validated values only
4. **Document data sources** for each configuration value in code comments
5. **Begin Phase 1 implementation**

---

## Appendix: Reference Links

- [Valheim Dedicated Server Guide](https://www.valheimgame.com/support/a-guide-to-dedicated-servers/)
- [lloesche/valheim-server Docker Hub](https://hub.docker.com/r/lloesche/valheim-server)
- [lloesche/valheim-server GitHub](https://github.com/lloesche/valheim-server-docker)
- [MakeFwl GitHub](https://github.com/CrystalFerrai/MakeFwl)
- [valheim-map.world](https://valheim-map.world/) (competitor reference)
