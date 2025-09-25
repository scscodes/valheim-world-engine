## Phase 0 — Setup & Analyzer Baseline

### Objectives
- Establish documentation and repo hygiene.
- Verify analyzer reproducibility on provided world files.
- Capture baseline artifacts/manifests to guide generator parity.

### Key components
- `file_analyzer.js`
- `extracted/seed.db/**`
- `README.md` quick start

### Deliverables
- Documented, repeatable analyzer run with logs.
- Checked-in baseline manifests (`index.json`, `clusters.json`).
- Clear instructions to clean/re-run.

### Acceptance criteria
- Running the analyzer yields the same manifest on repeated runs (same inputs).
- Logs stored and summarized in PR.

### Checklist
- [ ] Run analyzer against `seed.db` and `seed.fwl`.
- [ ] Verify artifacts and manifests exist and are readable.
- [ ] Summarize notable findings (e.g., terrain-like slices) in PR.
- [ ] Confirm `.gitignore` excludes transient large files as needed.


