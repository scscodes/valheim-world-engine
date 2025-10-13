# BepInEx Gen1 - Makefile
# Quick commands for common operations

.PHONY: help setup test validate clean run-validation

help:
	@echo "BepInEx Gen1 - Available Commands"
	@echo "=================================="
	@echo "  make setup          - Install dependencies"
	@echo "  make test           - Run quick test generation"
	@echo "  make validate       - Generate and validate reference seed"
	@echo "  make test-integration - Run full integration test suite"
	@echo "  make test-quick     - Run quick integration test"
	@echo "  make test-performance - Run performance regression test"
	@echo "  make clean          - Clean generated data"
	@echo "  make clean-docker   - Clean up old Docker containers"
	@echo ""
	@echo "Examples:"
	@echo "  python generator.py --seed hkLycKKCMI --resolution 512"
	@echo "  python generator.py --seed TestWorld --validate"

setup:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

test:
	@echo "Running quick test generation..."
	python generator.py --seed "QuickTest" --resolution 256

validate:
	@echo "Generating and validating reference seed..."
	python generator.py --seed "hkLycKKCMI" --resolution 512 --validate

test-integration:
	@echo "Running integration tests..."
	python test_integration.py --verbose

test-quick:
	@echo "Running quick integration test..."
	python test_integration.py --verbose --config config/generator.yaml

test-performance:
	@echo "Running performance regression test..."
	python test_integration.py --verbose | grep -A 10 "Performance Regression"

run-validation: validate

clean:
	@echo "Cleaning generated data..."
	rm -rf data/seeds/*/
	@echo "Clean complete"

clean-docker:
	@echo "Cleaning up old Docker containers..."
	docker ps -a --filter "label=vwe.generator=bepinex-gen1" -q | xargs -r docker rm -f
	@echo "Docker cleanup complete"

clean-all: clean clean-docker
	@echo "Full cleanup complete"

# Development helpers
install-dev:
	pip install -r requirements.txt
	pip install black pylint mypy

lint:
	pylint lib/*.py generator.py

format:
	black lib/*.py generator.py

type-check:
	mypy lib/*.py generator.py
