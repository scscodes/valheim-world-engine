# VWE Adaptive Sampling Client

**Complete end-to-end visualization system for Valheim world data**

> **Note:** Uses project-specific virtual environment at `./venv` for dependency isolation.

---

## Quick Start

```bash
# 1. Setup (creates venv, installs dependencies, validates environment)
make setup
# OR: ./setup.sh

# 2. Activate project virtual environment
source venv/bin/activate

# 3. Start Backend (Terminal 1 - with venv activated)
cd backend/VWE_WorldDataAPI
uvicorn app.main:app --reload

# 4. Start Frontend (Terminal 2)
cd frontend/VWE_MapViewer
npm run dev

# 5. Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

---

## What You Get

- **Backend API** (FastAPI) - Processes world data, generates PNGs
- **Frontend Viewer** (Next.js 14) - Interactive Canvas-based map
- **E2E Tests** - Validates complete pipeline
- **Docker Support** - `make build && make up`

---

## Requirements

- **Python 3.12 or 3.13** (earlier versions not supported)
- Node.js 18+
- BepInEx adaptive sampling output (optional for testing)

**Virtual Environment:** This project uses a project-specific venv at `./venv` for complete dependency isolation from other workspace projects.

---

## Architecture

```
Frontend (Next.js) → API (FastAPI) → BepInEx Data
   Port 3000           Port 8000        File System
```

---

## All Fixed Issues

✅ **Python 3.13 compatibility** - Updated NumPy, Pillow, all deps  
✅ **Pydantic type hints** - Fixed `any` → `Any`  
✅ **Settings config** - Added ENVIRONMENT, DATA_ROOT attributes  
✅ **CSS import paths** - Corrected frontend imports  
✅ **Next.js config** - Removed deprecated flags  
✅ **World loader init** - Proper startup sequence

---

## Files

**Essential:**
- `setup.sh` - Automated setup (creates venv, installs deps)
- `Makefile` - Build commands (`make help` for all options)
- `venv/` - Project-specific virtual environment (created by setup)

**Documentation:**
- `README.md` - This file (complete guide)
- `VENV_STANDARD.md` - Virtual environment setup and usage patterns
- `FIXES_APPLIED.md` - Technical details of all fixes
- `BIOME_ID_FIX.md` - Biome mapping corrections

**Advanced:**
- `docker-compose.yml` - Container orchestration
- `tests/e2e/` - End-to-end test suite

---

## Troubleshooting

### Backend won't start?
```bash
# Check Python version
python3 --version  # Must be 3.12+

# Reinstall
cd backend/VWE_WorldDataAPI
pip install -r requirements.txt
```

### Frontend won't start?
```bash
# Reinstall
cd frontend/VWE_MapViewer
rm -rf node_modules
npm install
```

### No data?
```bash
# Generate test data
cd ../bepinex-adaptive-sampling
python tests/validate_performance.py --seed TestSeed
```

---

## Docker Alternative

```bash
make build
make up

# Access same URLs
# Frontend: http://localhost:3000
# API: http://localhost:8000/docs
```

---

## Project Structure

```
adaptive-sampling-client/
├── backend/VWE_WorldDataAPI/    # Python FastAPI
├── frontend/VWE_MapViewer/      # Next.js TypeScript
├── tests/e2e/                   # E2E validation
├── setup.sh                     # Automated setup
├── test-services.sh             # Service validator
└── README_CONSOLIDATED.md       # This file
```

---

## API Endpoints

- `GET /api/v1/worlds/` - List worlds
- `GET /api/v1/worlds/{seed}/biomes` - Biome data (JSON/PNG)
- `GET /api/v1/worlds/{seed}/heightmap` - Heightmap (JSON/PNG)
- `GET /api/v1/worlds/{seed}/composite` - Composite image
- `GET /health` - Health check

---

## Status

✅ **All systems stable and functional**

- Backend starts successfully
- Frontend starts successfully
- All runtime errors resolved
- Documentation consolidated
- Ready for testing with BepInEx data

---

For technical details, see `FIXES_APPLIED.md`

