# Starting Services - Quick Reference

## One-Time Setup

```bash
cd /home/steve/projects/valhem-world-engine/etl/experimental/adaptive-sampling-client
make setup
```

This creates `./venv` and installs all dependencies.

---

## Starting Backend (with Corrected Biome IDs)

**Terminal 1:**
```bash
cd /home/steve/projects/valhem-world-engine/etl/experimental/adaptive-sampling-client
source venv/bin/activate
cd backend/VWE_WorldDataAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Verify backend:**
```bash
curl http://localhost:8000/health
```

Expected: Shows `data_root_exists: true` and JSON file counts.

---

## Starting Frontend

**Terminal 2:**
```bash
cd /home/steve/projects/valhem-world-engine/etl/experimental/adaptive-sampling-client/frontend/VWE_MapViewer
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## Expected Results

### Legend (All 9 Biomes)
- Meadows: 3.1%
- BlackForest: 10.4%
- Swamp: 2.3%
- Mountain: 2.7%
- Plains: 11.4%
- Ocean: 18.2%
- Mistlands: 5.4%
- **DeepNorth: 31.7%** ← Should be visible (was always correct)
- **Ashlands: 14.8%** ← Should NOW be visible (was missing due to ID mismatch)

### What Was Fixed
**Backend & Frontend biome ID mappings now match BepInEx export:**
- `ASHLANDS = 512` (was incorrectly 128)
- `BLACK_FOREST = 2` (was incorrectly 8)
- `SWAMP = 4` (was incorrectly 2)
- `MOUNTAIN = 8` (was incorrectly 4)

---

## Troubleshooting

### "ModuleNotFoundError" or "Command not found"
```bash
# Ensure venv is activated
echo $VIRTUAL_ENV
# Should show: .../adaptive-sampling-client/venv

# If not activated:
cd /home/steve/projects/valhem-world-engine/etl/experimental/adaptive-sampling-client
source venv/bin/activate
```

### Biomes still showing incorrectly
```bash
# Backend must be restarted to load fixed biome models
# Stop backend (Ctrl+C), then restart:
source venv/bin/activate
cd backend/VWE_WorldDataAPI
uvicorn app.main:app --reload
```

### Frontend still has old types
```bash
# Rebuild frontend
cd frontend/VWE_MapViewer
rm -rf .next
npm run dev
```

---

## Files Changed (Summary)

**Biome ID Fixes:**
- `backend/VWE_WorldDataAPI/app/models/world_data.py` - Corrected all biome enum values
- `frontend/VWE_MapViewer/src/types/world-data.ts` - Corrected all biome enum values

**Virtual Environment Standard:**
- `setup.sh` - Now creates and activates `./venv`
- `Makefile` - Enforces venv usage
- `README.md` - Documents venv workflow

**Documentation:**
- `BIOME_ID_FIX.md` - Details the biome ID corrections
- `VENV_STANDARD.md` - Complete venv documentation
- `SETUP_COMPLETE.md` - What changed and why
- `START_SERVICES.md` - This file (quick reference)

---

## Quick Commands

```bash
# Setup (first time only)
make setup

# Activate venv (every terminal session)
source venv/bin/activate

# Start backend (Terminal 1)
cd backend/VWE_WorldDataAPI && uvicorn app.main:app --reload

# Start frontend (Terminal 2)
cd frontend/VWE_MapViewer && npm run dev

# Run tests
make test
```

