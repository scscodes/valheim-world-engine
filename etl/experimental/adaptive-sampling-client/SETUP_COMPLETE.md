# Project-Specific Virtual Environment - Setup Complete

## Summary
The project now uses a **project-specific virtual environment** at `./venv` for complete dependency isolation.

## What Changed

### 1. `setup.sh` (Automated Setup)
**Now automatically:**
- ✅ Creates `./venv` if it doesn't exist
- ✅ Activates the project venv
- ✅ Switches if a different venv is active
- ✅ Installs all dependencies into project venv

### 2. `Makefile` (Build Automation)
**New targets:**
- `make venv` - Creates project-specific venv
- `make install` - Installs deps (enforces venv requirement)
- `make test` - Uses venv's pytest

**Updated variables:**
```makefile
VENV_DIR := venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
PYTEST := $(VENV_DIR)/bin/pytest
```

### 3. `README.md` (Documentation)
**Updated with:**
- Virtual environment activation in Quick Start
- Clear note about project-specific venv usage
- Updated file references

### 4. New: `VENV_STANDARD.md`
**Comprehensive documentation covering:**
- Rationale for project-specific venv
- Directory structure
- Usage patterns (setup, daily workflow, testing)
- Makefile integration
- CI/CD considerations
- Troubleshooting
- Comparison with other workspace venv patterns

## Correct Usage Pattern

### Initial Setup
```bash
cd etl/experimental/adaptive-sampling-client

# Automated (recommended)
make setup

# This creates ./venv, activates it, installs deps
```

### Daily Workflow
```bash
# Always activate first
cd etl/experimental/adaptive-sampling-client
source venv/bin/activate

# Start backend
cd backend/VWE_WorldDataAPI
uvicorn app.main:app --reload

# In another terminal (activate again!)
cd etl/experimental/adaptive-sampling-client
source venv/bin/activate
cd frontend/VWE_MapViewer
npm run dev
```

### Testing
```bash
source venv/bin/activate
make test
```

## Biome ID Fixes Applied

Along with the venv setup, **critical biome ID mapping errors** were fixed:

**Corrected IDs:**
- `ASHLANDS = 512` (was 128) ← **This fixes missing Ashlands data!**
- `BLACK_FOREST = 2` (was 8)
- `SWAMP = 4` (was 2)
- `MOUNTAIN = 8` (was 4)

**Files updated:**
- `backend/VWE_WorldDataAPI/app/models/world_data.py`
- `frontend/VWE_MapViewer/src/types/world-data.ts`

**Expected biome distribution after restart:**
- Meadows: 3.1%
- BlackForest: 10.4%
- Swamp: 2.3%
- Mountain: 2.7%
- Plains: 11.4%
- Ocean: 18.2%
- Mistlands: 5.4%
- **DeepNorth: 31.7%** (largest biome)
- **Ashlands: 14.8%** (now visible!)

## Next Steps

### 1. Create Virtual Environment (if not done)
```bash
cd /home/steve/projects/valhem-world-engine/etl/experimental/adaptive-sampling-client
make setup
```

### 2. Start Services
**Backend:**
```bash
source venv/bin/activate
cd backend/VWE_WorldDataAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend/VWE_MapViewer
npm run dev
```

### 3. Verify Biome Data
- Open http://localhost:3000
- Check legend shows all 9 biomes
- Verify Ashlands (14.8%) and DeepNorth (31.7%) appear correctly
- Map colors should match biome distribution

## Verification Checklist

- [ ] `venv/` directory exists in project root
- [ ] Backend starts without errors
- [ ] Frontend builds and runs
- [ ] Legend shows all 9 biomes with correct percentages
- [ ] Ashlands data (14.8%) is visible
- [ ] DeepNorth data (31.7%) is visible
- [ ] Map colors match biome types

## Troubleshooting

### Backend won't start
```bash
# Verify venv activation
echo $VIRTUAL_ENV
# Should show: .../adaptive-sampling-client/venv

# Reinstall if needed
deactivate
make setup
```

### Wrong biome data showing
```bash
# Restart backend to load fixed biome mappings
# (Ctrl+C in backend terminal, then restart)
source venv/bin/activate
cd backend/VWE_WorldDataAPI
uvicorn app.main:app --reload
```

### Frontend build errors
```bash
# Reinstall frontend deps
cd frontend/VWE_MapViewer
rm -rf node_modules .next
npm install
npm run dev
```

## Files Modified

- ✅ `setup.sh` - Auto-creates and activates project venv
- ✅ `Makefile` - Enforces venv usage, new targets
- ✅ `README.md` - Updated with venv instructions
- ✅ `backend/.../world_data.py` - Fixed biome IDs
- ✅ `frontend/.../world-data.ts` - Fixed biome IDs
- ✅ `BIOME_ID_FIX.md` - Documents biome corrections
- 📝 `VENV_STANDARD.md` - NEW: Comprehensive venv docs
- 📝 `SETUP_COMPLETE.md` - NEW: This file

## Reference

For complete virtual environment documentation, see `VENV_STANDARD.md`.

