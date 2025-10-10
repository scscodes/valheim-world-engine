# Valheim World Engine - Root Makefile
# ====================================

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  global          - Generate global constants"
	@echo "  backend         - Build backend"
	@echo "  bepinex         - Build BepInEx plugins"
	@echo "  procedural      - Build procedural export"
	@echo "  all             - Build everything"
	@echo "  clean           - Clean all build artifacts"

.PHONY: global
global:
	@echo "Generating global constants..."
	@cd global && make all

.PHONY: backend
backend: global
	@echo "Building backend..."
	@cd backend && make build

.PHONY: bepinex
bepinex: global
	@echo "Building BepInEx plugins..."
	@cd bepinex && make build

.PHONY: procedural
procedural: global
	@echo "Building procedural export..."
	@cd procedural-export && make build

.PHONY: all
all: global backend bepinex procedural
	@echo "All projects built successfully!"

.PHONY: clean
clean:
	@echo "Cleaning all projects..."
	@cd global && make clean
	@cd backend && make clean
	@cd bepinex && make clean
	@cd procedural-export && make clean
	@echo "Clean complete!"

# Default target
.DEFAULT_GOAL := all
