## Phase 1 — Generator Core

### Objectives
- Implement deterministic primitives to reproduce world height and biome classification from a seed.
- Expose a typed API consumed by later phases.

### Key components (planned)
- `src/generator/noise/*` — Perlin/simplex/octaves, domain warping, seeding
- `src/generator/height.ts` — Height function and shoreline/water logic
- `src/generator/biome.ts` — Biome masks/classifier
- `tests/generator/*` — Unit tests for determinism and ranges

### Deliverables
- Deterministic height and biome functions with tests.
- Minimal CLI to sample a small grid for a given seed.

### Acceptance criteria
- Fixed outputs for a given seed/version across runs.
- Height values and biome distribution are plausible vs analyzer observations.

### Checklist
- [ ] Implement seeded noise primitives and helpers.
- [ ] Height function: sea level, shore shaping, cliffs smoothing.
- [ ] Biome classifier: start with Meadows/Black Forest/Plains.
- [ ] CLI to export a preview CSV/PNG of a small grid.
- [ ] Tests for determinism and bounds.


