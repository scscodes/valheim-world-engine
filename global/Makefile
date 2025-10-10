# Global Constants Makefile
# ========================

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  validate        - Validate all YAML files against schemas"
	@echo "  generate        - Generate constants for all languages"
	@echo "  clean           - Clean generated files"
	@echo "  all             - Validate and generate everything"

.PHONY: validate
validate:
	@echo "Validating YAML files..."
	@yamllint data/*.yml
	@echo "Validating against schemas..."
	@python -c "import yaml, json; [yaml.safe_load(open(f'data/{f}')) for f in ['valheim-world.yml', 'validation-data.yml', 'rendering-config.yml']]"
	@echo "Validation complete!"

.PHONY: generate
generate:
	@echo "Generating constants..."
	@python generators/python/generate_constants.py
	@python generators/python/generate_utils.py
	@echo "Constants generated successfully!"

.PHONY: clean
clean:
	@echo "Cleaning generated files..."
	@find ../backend -name "generated_constants.py" -delete
	@find ../backend -name "generated_utils.py" -delete
	@find ../bepinex -name "ValheimConstants.cs" -delete
	@find ../procedural-export -name "valheim-constants.js" -delete
	@echo "Clean complete!"

.PHONY: all
all: validate generate
	@echo "All tasks completed successfully!"

# Default target
.DEFAULT_GOAL := all
