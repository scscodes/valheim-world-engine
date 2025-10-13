#!/bin/bash
# Setup script for VWE Adaptive Sampling Client
# Validates environment and installs dependencies

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "VWE Adaptive Sampling Client - Setup"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "Found Python $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
    echo -e "${RED}Error: Python 3.12 or higher required${NC}"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 13 ]; then
    echo -e "${GREEN}✓ Python $PYTHON_VERSION (excellent - all dependencies compatible)${NC}"
else
    echo -e "${GREEN}✓ Python $PYTHON_VERSION (compatible)${NC}"
fi
echo ""

# Check/Create virtual environment
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating project-specific virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created at ./$VENV_DIR${NC}"
    echo ""
fi

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
    echo ""
elif [ "$VIRTUAL_ENV" != "$(pwd)/$VENV_DIR" ]; then
    echo -e "${YELLOW}Warning: Different venv active: $VIRTUAL_ENV${NC}"
    echo "Switching to project venv..."
    deactivate 2>/dev/null || true
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}✓ Switched to project virtual environment${NC}"
    echo ""
else
    echo -e "${GREEN}✓ Project virtual environment active${NC}"
    echo ""
fi

# Check for BepInEx output data
echo "Checking for BepInEx adaptive sampling data..."
DATA_PATH="../bepinex-adaptive-sampling/output/world_data"
if [ -d "$DATA_PATH" ]; then
    if [ -f "$DATA_PATH/biomes.json" ] && [ -f "$DATA_PATH/heightmap.json" ]; then
        echo -e "${GREEN}✓ BepInEx output data found${NC}"
        echo "  - biomes.json: $(du -h "$DATA_PATH/biomes.json" | cut -f1)"
        echo "  - heightmap.json: $(du -h "$DATA_PATH/heightmap.json" | cut -f1)"
    else
        echo -e "${YELLOW}⚠ BepInEx output directory exists but missing data files${NC}"
        echo "Run adaptive sampling first:"
        echo "  cd ../bepinex-adaptive-sampling"
        echo "  python tests/validate_performance.py --seed TestSeed"
    fi
else
    echo -e "${YELLOW}⚠ BepInEx output data not found at: $DATA_PATH${NC}"
    echo "The API will start but won't have data to serve."
    echo "To generate data, run:"
    echo "  cd ../bepinex-adaptive-sampling"
    echo "  python tests/validate_performance.py --seed TestSeed"
fi
echo ""

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend/VWE_WorldDataAPI
if pip install -r requirements.txt; then
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    echo -e "${RED}✗ Failed to install backend dependencies${NC}"
    exit 1
fi
cd ../..
echo ""

# Check for Node.js
echo "Checking for Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js found: $NODE_VERSION${NC}"
    
    # Install frontend dependencies
    echo "Installing frontend dependencies..."
    cd frontend/VWE_MapViewer
    if npm install; then
        echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    else
        echo -e "${RED}✗ Failed to install frontend dependencies${NC}"
        exit 1
    fi
    cd ../..
else
    echo -e "${YELLOW}⚠ Node.js not found - skipping frontend setup${NC}"
    echo "Install Node.js 18+ to run the frontend:"
    echo "  https://nodejs.org/"
fi
echo ""

# Install test dependencies
echo "Installing test dependencies..."
if pip install pytest requests; then
    echo -e "${GREEN}✓ Test dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ Failed to install test dependencies${NC}"
fi
echo ""

echo "========================================"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Start the backend API:"
echo "   cd backend/VWE_WorldDataAPI"
echo "   uvicorn app.main:app --reload"
echo ""
echo "2. Start the frontend (in another terminal):"
echo "   cd frontend/VWE_MapViewer"
echo "   npm run dev"
echo ""
echo "3. Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "4. Run E2E tests (after starting services):"
echo "   pytest tests/e2e/test_full_pipeline.py -v"
echo ""
echo "Or use Docker Compose:"
echo "   make build && make up"
echo ""

