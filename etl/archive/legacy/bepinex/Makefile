# Makefile for VWE BepInEx plugins

.PHONY: setup build clean test run stop logs help

# Default target
all: build

# Setup BepInEx development environment (only needed for plugin development)
setup:
	@echo "Setting up BepInEx development environment..."
	@./setup.sh

# Build all plugins
build:
	@echo "Building VWE BepInEx plugins..."
	@./build.sh
	@echo "Plugins built successfully in plugins/ directory"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf src/*/bin/
	@rm -rf src/*/obj/
	@echo "Clean completed (keeping compiled DLLs in plugins/)"

# Run BepInEx approach (isolated container)
run:
	@echo "Starting BepInEx container (isolated from backend)..."
	@cd ../docker/bepinex && docker compose -f docker-compose.bepinex.yml --profile bepinex up -d
	@echo "Container started. Use 'make logs' to monitor."

# Stop BepInEx container
stop:
	@echo "Stopping BepInEx container..."
	@cd ../docker/bepinex && docker compose -f docker-compose.bepinex.yml down
	@echo "Container stopped."

# View container logs
logs:
	@docker logs -f vwe-valheim-bepinex

# Test BepInEx approach end-to-end
test: build run
	@echo "Testing BepInEx approach..."
	@echo "Monitoring logs (Ctrl+C to stop)..."
	@docker logs -f vwe-valheim-bepinex | grep -E "(VWE|BepInEx|World saved|Export)"

# Show help
help:
	@echo "VWE BepInEx Plugin Makefile"
	@echo ""
	@echo "Quick Start (no build needed):"
	@echo "  make run     - Run BepInEx container with pre-compiled plugins"
	@echo "  make logs    - View container logs"
	@echo "  make stop    - Stop BepInEx container"
	@echo ""
	@echo "Plugin Development:"
	@echo "  make setup   - Setup development environment (one-time)"
	@echo "  make build   - Rebuild plugins from source"
	@echo "  make clean   - Clean build artifacts"
	@echo "  make test    - Build + run + monitor logs"
	@echo ""
	@echo "Note: Pre-compiled plugins are in plugins/ and ready to use."
