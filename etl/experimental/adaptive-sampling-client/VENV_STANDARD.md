# Virtual Environment Standard

## Overview
This project uses a **project-specific virtual environment** located at `./venv` for complete dependency isolation.

## Rationale
- **Isolation**: Prevents conflicts with other experimental projects in the monorepo
- **Reproducibility**: Ensures consistent dependency versions across environments
- **Testing**: Allows validation of exact dependency requirements without interference
- **Portability**: Self-contained setup can be easily moved or replicated

## Structure

```
adaptive-sampling-client/
├── venv/                    # Project-specific Python virtual environment
│   ├── bin/
│   │   ├── activate         # Activation script
│   │   ├── python           # Python interpreter
│   │   ├── pip              # Package installer
│   │   └── uvicorn          # Backend server
│   ├── lib/
│   └── pyvenv.cfg
├── backend/
│   └── VWE_WorldDataAPI/
│       ├── requirements.txt # Python dependencies
│       └── ...
├── frontend/
│   └── VWE_MapViewer/
│       ├── node_modules/    # Node.js dependencies (project-local)
│       └── ...
└── setup.sh                 # Automated setup (creates venv)
```

## Usage Patterns

### Initial Setup
```bash
cd etl/experimental/adaptive-sampling-client

# Option 1: Automated (recommended)
make setup

# Option 2: Manual
make venv
source venv/bin/activate
make install
```

### Daily Workflow
```bash
# Always activate before working
cd etl/experimental/adaptive-sampling-client
source venv/bin/activate

# Start backend
cd backend/VWE_WorldDataAPI
uvicorn app.main:app --reload

# In another terminal, activate again for frontend
cd etl/experimental/adaptive-sampling-client
source venv/bin/activate
cd frontend/VWE_MapViewer
npm run dev
```

### Running Tests
```bash
source venv/bin/activate
make test

# Or directly
pytest tests/e2e/ -v
```

### Deactivation
```bash
deactivate
```

## Makefile Integration

The Makefile enforces the project venv pattern:
- `make venv` - Creates the virtual environment
- `make install` - Installs dependencies (requires venv)
- `make test` - Runs tests using venv's pytest
- `make clean` - Cleans up (preserves venv)

All Python commands in the Makefile use `$(VENV_DIR)/bin/python` and `$(VENV_DIR)/bin/pip`.

## CI/CD Considerations

For automated environments:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/VWE_WorldDataAPI/requirements.txt
pip install pytest requests
pytest tests/e2e/
```

## Troubleshooting

### "Command not found" after activation
```bash
# Verify activation
echo $VIRTUAL_ENV
# Should show: /home/steve/projects/valhem-world-engine/etl/experimental/adaptive-sampling-client/venv

# Re-activate if needed
deactivate
source venv/bin/activate
```

### Wrong venv active
```bash
# Check which venv is active
echo $VIRTUAL_ENV

# Switch to project venv
deactivate
cd /home/steve/projects/valhem-world-engine/etl/experimental/adaptive-sampling-client
source venv/bin/activate
```

### Dependency conflicts
```bash
# Recreate venv from scratch
rm -rf venv
make venv
source venv/bin/activate
make install
```

## Comparison with Other Project Patterns

### Root-level `.venv/` (other projects)
- **Use case**: Shared dependencies across entire monorepo
- **Location**: `/home/steve/projects/valhem-world-engine/.venv`
- **When to use**: General utilities, shared tooling

### Project-level `venv/` (this project)
- **Use case**: Experimental features with specific dependency versions
- **Location**: `etl/experimental/adaptive-sampling-client/venv`
- **When to use**: Testing, isolation, version validation

### Subproject-level `venv/` (procedural-export)
- **Use case**: Jupyter notebooks with scientific computing stack
- **Location**: `procedural-export/notebooks/.venv`
- **When to use**: Data science, analysis, visualization

## Git Ignore

The `.gitignore` excludes virtual environments:
```gitignore
.venv/
venv/
env/
```

Virtual environments should **never** be committed to version control.

