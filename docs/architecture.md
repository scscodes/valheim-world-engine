## Architecture Overview

### Goal
Generate a full world map deterministically from a Valheim seed, export discrete data layers and tiles, and render them in a web app. A companion analyzer inspects real world files to validate the generator.

### Modules (planned and current)
- Generator core (planned): Pure functions that reproduce worldgen from a seed.
  - Height function(s) and shoreline/water logic
  - Biome classification masks
  - Feature/POI placement stubs
- Layer producers (planned): Turn generator outputs into layer rasters and feature sets.
  - Height (float32), biome (uint8 indexed), water, regions, POIs
- Export & tiling (planned): Build tile pyramids and manifests for web rendering.
  - XYZ/quadkey tiles (PNG/WEBP), JSON legends, index manifests
- Web renderer (planned): Minimal client to layer tiles/overlays and navigate by seed.
  - Map library (Leaflet/MapLibre), layer toggles, legends
- Analyzer (current): Extracts artifacts from `.db`/`.fwl` to inform/validate generation.
  - Signature/decompression heuristics, terrain-like float scans, manifests
- Validation harness (planned): Compares generator layers against analyzer outputs for known seeds.
  - Metrics (RMSE for height, biome confusion, POI proximity)

### Data flow
seed → generator core → layer producers → tile/export pipeline → web renderer

Parallel: real world files (`seed.db`, `seed.fwl`) → analyzer → manifests/artifacts → validation harness (compare vs generator outputs)

### File and directory mapping
Current:
- `README.md` — Project overview and quick start
- `file_analyzer.js` — Analyzer implementation (Node.js)
- `extracted/seed.db/**` — Analyzer artifacts, manifests, and previews

Planned (proposed):
- `src/generator/**` — Deterministic worldgen primitives and APIs
- `src/layers/**` — Layer builders (height, biome, water, POIs)
- `src/export/**` — Tile/asset exporters and CLI
- `web/**` — Minimal viewer (static site)
- `tests/**` — Unit/integration and validation tests

### Contracts and schemas (initial)
- Height layer: float32 grid; metadata with bbox, resolution, seed, version
- Biome layer: uint8 grid; palette/legend JSON for web
- Water layer: bitmask/grid; sea level metadata
- POIs/features: JSON array with type, id, position, seed, version

### Non-functional
- Determinism: same seed and version yields identical outputs
- Performance: tile generation parallelized; caching of intermediate rasters
- Storage: large artifacts under Git LFS; exclude transient outputs in `.gitignore`


