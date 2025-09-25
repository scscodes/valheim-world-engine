## Project Documentation

This directory organizes the project’s planning and guidance as we evolve from world file analysis to a full seed-to-map generator with a web renderer.

### How to use these docs
- Start with the architecture overview to understand modules and data flow.
- Pick the current phase document and contribute against its objectives and checklist.
- When a phase is completed, remove its phase doc in the same PR and summarize outcomes in the PR description and release notes.

### Contents
- `architecture.md` — High-level modules, data flow, and mapping to source files and assets.
- `phase-0-setup-analysis.md` — Groundwork and analyzer baseline.
- `phase-1-generator-core.md` — Core deterministic world generation by seed (height/biome).
- `phase-2-layers-export.md` — Layer production and tile/asset export.
- `phase-3-web-renderer.md` — Minimal web viewer to visualize tiles and overlays.
- `phase-4-validation.md` — Cross-checks, metrics, regression tests.
- `phase-5-performance.md` — Performance, scaling, caching.
- `contributing.md` — Practical guidance for proposals and PRs.

### Status conventions
- Each phase doc contains: objectives, key components, deliverables, acceptance criteria, and a living checklist.
- Keep docs concise; link to code, issues, and PRs rather than duplicating details.


