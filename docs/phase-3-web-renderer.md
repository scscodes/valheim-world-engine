## Phase 3 — Web Renderer

### Objectives
- Build a minimal web app to visualize exported tiles and overlays for any seed.

### Key components (planned)
- `web/` — Static site served via any HTTP server
- Tile sources — XYZ tiles generated in Phase 2
- Legends/palettes — Shared JSON to colorize biomes

### Deliverables
- Seed entry UI, permalink support, layer toggles, and a legend.
- Smooth pan/zoom for z0–6; graceful fallback when tiles are missing.

### Acceptance criteria
- Tiles align across layers; interactions are responsive on desktop.
- No framework lock-in; deployable as static assets.

### Checklist
- [ ] Minimal viewer with Leaflet or MapLibre.
- [ ] Layer toggles (height/biome/water/POIs).
- [ ] Legend rendering from shared JSON.
- [ ] Seed permalink and shallow routing.


