# VWE Code Generators Makefile
# Provides convenient commands for using the generators

.PHONY: help install test clean example csharp python typescript all

# Default target
help:
	@echo "VWE Code Generators"
	@echo "=================="
	@echo ""
	@echo "Available targets:"
	@echo "  install     - Install Python dependencies"
	@echo "  test        - Run generator tests"
	@echo "  clean       - Clean generated output files"
	@echo "  example     - Run example usage demonstration"
	@echo "  csharp      - Generate C# BepInEx plugin example"
	@echo "  python      - Generate Python FastAPI service example"
	@echo "  typescript  - Generate TypeScript Next.js app example"
	@echo "  all         - Generate examples for all technologies"
	@echo ""

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests (placeholder - add actual tests)
test:
	@echo "Running generator tests..."
	python -m pytest tests/ -v || echo "No tests found - add tests to tests/ directory"

# Clean generated files
clean:
	@echo "Cleaning generated output files..."
	rm -rf output/
	@echo "Clean complete!"

# Run example usage
example:
	@echo "Running VWE generators example..."
	python example_usage.py

# Generate C# example
csharp:
	@echo "Generating C# BepInEx plugin example..."
	python csharp_generator.py

# Generate Python example
python:
	@echo "Generating Python FastAPI service example..."
	python python_generator.py

# Generate TypeScript example
typescript:
	@echo "Generating TypeScript Next.js app example..."
	python typescript_generator.py

# Generate all examples
all: csharp python typescript
	@echo "All generator examples completed!"

# Development targets
dev-install: install
	@echo "Development installation complete!"

# Quick start - install and run example
quickstart: install example
	@echo "Quick start complete! Check the output/ directory for generated files."
