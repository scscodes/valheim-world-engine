# Makefile for VWE BepInEx plugins

.PHONY: setup build clean docker-build docker-run help

# Default target
all: setup build

# Setup BepInEx development environment
setup:
	@echo "Setting up BepInEx development environment..."
	@./setup.sh

# Build all plugins
build: setup
	@echo "Building VWE BepInEx plugins..."
	@./build.sh

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf plugins/*.dll
	@rm -rf src/*/bin/
	@rm -rf src/*/obj/
	@echo "Clean completed"

# Build Docker image
docker-build: build
	@echo "Building Docker image..."
	@cd docker && docker build -t vwe/valheim-server-bepinex:latest .
	@echo "Docker image built successfully"

# Run Docker container for testing
docker-run:
	@echo "Running Docker container for testing..."
	@cd docker && docker-compose -f docker-compose.override.yml up --build

# Show help
help:
	@echo "Available targets:"
	@echo "  setup        - Setup BepInEx development environment"
	@echo "  build        - Build all BepInEx plugins"
	@echo "  clean        - Clean build artifacts"
	@echo "  docker-build - Build Docker image with plugins"
	@echo "  docker-run   - Run Docker container for testing"
	@echo "  help         - Show this help message"
