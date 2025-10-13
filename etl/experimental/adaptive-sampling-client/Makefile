.PHONY: help setup install build up down logs test clean check-python venv

# Project-specific venv
VENV_DIR := venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
PYTEST := $(VENV_DIR)/bin/pytest

help:
	@echo "VWE Adaptive Sampling Client - Available Commands"
	@echo ""
	@echo "  make setup      - Run automated setup script (recommended)"
	@echo "  make venv       - Create project-specific virtual environment"
	@echo "  make install    - Install dependencies (requires venv)"
	@echo "  make build      - Build Docker containers"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make logs       - View logs"
	@echo "  make test       - Run E2E tests"
	@echo "  make clean      - Clean up containers and volumes"
	@echo ""
	@echo "Note: Run 'source venv/bin/activate' before starting services manually"
	@echo ""

setup:
	@echo "Running automated setup..."
	@bash ./setup.sh

venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating project-specific virtual environment..."; \
		python3 -m venv $(VENV_DIR); \
		echo "✓ Virtual environment created at ./$(VENV_DIR)"; \
		echo ""; \
		echo "Activate with: source $(VENV_DIR)/bin/activate"; \
	else \
		echo "Virtual environment already exists at ./$(VENV_DIR)"; \
	fi

check-python:
	@echo "Checking Python version..."
	@python3 -c "import sys; ver=sys.version_info; exit(0 if ver.major==3 and ver.minor>=12 else 1)" || \
		(echo "Error: Python 3.12+ required. Current: $$(python3 --version)" && exit 1)
	@echo "✓ Python version OK"

install: venv
	@if [ ! -f "$(VENV_DIR)/bin/activate" ]; then \
		echo "Error: Virtual environment not found. Run 'make venv' first."; \
		exit 1; \
	fi
	@echo "Installing backend dependencies..."
	@$(PIP) install -r backend/VWE_WorldDataAPI/requirements.txt
	@echo "Installing frontend dependencies..."
	@cd frontend/VWE_MapViewer && npm install
	@echo "Installing test dependencies..."
	@$(PIP) install pytest requests
	@echo ""
	@echo "✓ Installation complete!"
	@echo "Activate venv with: source $(VENV_DIR)/bin/activate"

build:
	@echo "Building Docker containers..."
	docker-compose build

up:
	@echo "Starting services..."
	docker-compose up -d
	@echo "Services started!"
	@echo "  - API: http://localhost:8000"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - API Docs: http://localhost:8000/docs"

down:
	@echo "Stopping services..."
	docker-compose down

logs:
	docker-compose logs -f

test:
	@echo "Running E2E tests..."
	@echo "Ensure services are running (make up)"
	@if [ -f "$(PYTEST)" ]; then \
		$(PYTEST) tests/e2e/ -v; \
	else \
		echo "Error: pytest not found. Run 'make install' first."; \
		exit 1; \
	fi

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete!"

