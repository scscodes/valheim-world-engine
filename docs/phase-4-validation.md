## Phase 4 — Validation & QA

### Objectives
- Systematically compare generator outputs to analyzer findings for known seeds.

### Key components (planned)
- `tests/validation/*` — Scripts and fixtures
- Analyzer manifests — `extracted/**/index.json`, `clusters.json`

### Deliverables
- Validation report with metrics per seed and layer.
- Baseline thresholds and regression tests.

### Acceptance criteria
- Metrics within agreed tolerances (e.g., height RMSE, biome confusion).
- CI or repeatable scripts produce the same report.

### Checklist
- [ ] Select reference seeds and collect analyzer outputs.
- [ ] Implement metrics and reporting.
- [ ] Add regression tests to CI.


