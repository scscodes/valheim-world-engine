## Phase 2 — Layers & Export

### Objectives
- Convert generator outputs into discrete layers and export to a tile pyramid with lightweight manifests.

### Key components (planned)
- `src/layers/*` — Height, biome, water, regions, POIs
- `src/export/cli.ts` — CLI to emit z0–6 tiles and layer manifests
- `schemas/legend.json` — Shared color palettes and legends

### Deliverables
- XYZ tiles for height (grayscale) and biomes (paletted) z0–6.
- JSON manifests with metadata, palette, and layer availability.

### Acceptance criteria
- Tiles load correctly in a local viewer and align across layers.
- Export is reproducible for the same seed/version.

### Checklist
- [ ] Define layer schemas and legends.
- [ ] Implement exporters for height/biome; stub water/POIs.
- [ ] Emit tiles and manifests to an `out/` directory.
- [ ] Smoke-test tiles in a simple HTML page.


