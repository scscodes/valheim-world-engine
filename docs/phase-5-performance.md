## Phase 5 — Performance & Scaling

### Objectives
- Optimize generation and export throughput; introduce caching and parallelism.

### Key components (planned)
- Worker pool for tile generation; cache for intermediate rasters
- Streaming writers for tiles and manifests

### Deliverables
- Benchmarks and guidance for typical seeds and zoom ranges.
- Configurable concurrency and memory bounds.

### Acceptance criteria
- Meets target throughput on a modest server (document hardware).
- No nondeterminism introduced by parallelism.

### Checklist
- [ ] Introduce worker pool and task sharding.
- [ ] Add caches for repeated computations.
- [ ] Write benchmarks and document results.


