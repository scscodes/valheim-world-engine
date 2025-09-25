## Contributing

### Principles
- Keep changes deterministic and testable.
- Prefer small, focused PRs linked to a phase checklist item.
- Document public APIs/schemas in the relevant doc.

### Workflow
1. Pick a phase task and open an issue describing your approach.
2. Implement with tests (where applicable).
3. Update docs if you change public contracts or workflows.
4. Submit a PR referencing the issue and phase task; include a brief summary and screenshots if UI.

### Coding standards
- Node.js/TypeScript recommended for new generator/export code.
- Use explicit types and avoid `any`.
- Log with structured levels; handle errors gracefully.
- Large artifacts go to Git LFS; avoid committing transient outputs.


