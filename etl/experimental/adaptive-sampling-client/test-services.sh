#!/bin/bash
# Test script to validate both backend and frontend services

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "VWE Services Validation Test"
echo "========================================"
echo ""

# Check if backend is running
echo "1. Testing Backend API..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend API is running (port 8000)${NC}"
    
    # Test health endpoint
    HEALTH=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "error")
    if [ "$HEALTH" = "healthy" ]; then
        echo -e "${GREEN}✓ Health check passed${NC}"
    else
        echo -e "${YELLOW}⚠ Health check returned: $HEALTH${NC}"
    fi
else
    echo -e "${RED}✗ Backend API not accessible${NC}"
    echo "Start it with:"
    echo "  cd backend/VWE_WorldDataAPI"
    echo "  uvicorn app.main:app --reload"
fi
echo ""

# Check if frontend is running
echo "2. Testing Frontend..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running (port 3000)${NC}"
else
    echo -e "${RED}✗ Frontend not accessible${NC}"
    echo "Start it with:"
    echo "  cd frontend/VWE_MapViewer"
    echo "  npm run dev"
fi
echo ""

# Check for BepInEx data
echo "3. Checking for BepInEx data..."
DATA_PATH="../bepinex-adaptive-sampling/output/world_data"
if [ -f "$DATA_PATH/biomes.json" ] && [ -f "$DATA_PATH/heightmap.json" ]; then
    echo -e "${GREEN}✓ BepInEx data found${NC}"
    
    # Test world data endpoint if backend is up
    if curl -s http://localhost:8000/api/v1/worlds/ > /dev/null 2>&1; then
        WORLDS=$(curl -s http://localhost:8000/api/v1/worlds/ | jq '. | length' 2>/dev/null || echo "0")
        echo -e "${GREEN}✓ API can access $WORLDS world(s)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ BepInEx data not found${NC}"
    echo "Generate data with:"
    echo "  cd ../bepinex-adaptive-sampling"
    echo "  python tests/validate_performance.py --seed TestSeed"
fi
echo ""

echo "========================================"
echo "Test Summary"
echo "========================================"
echo ""
echo "To start services:"
echo "  Terminal 1: cd backend/VWE_WorldDataAPI && uvicorn app.main:app --reload"
echo "  Terminal 2: cd frontend/VWE_MapViewer && npm run dev"
echo ""
echo "Then access:"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo ""

