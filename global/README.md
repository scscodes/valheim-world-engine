# Global Constants - Valheim World Engine

This directory contains the global constants and configuration for the Valheim World Engine project. All constants are defined in YAML format and automatically generated for each target language.

## Structure

```
global/
├── data/                           # YAML configuration files
│   ├── valheim-world.yml          # Core game constants
│   ├── validation-data.yml        # Validation metrics
│   └── rendering-config.yml       # Rendering settings
├── schemas/                        # JSON Schema validation
│   ├── valheim-world.schema.json
│   ├── validation-data.schema.json
│   └── rendering-config.schema.json
├── generators/                     # Language-specific generators
│   ├── python/
│   ├── csharp/
│   └── javascript/
└── Makefile                       # Build automation
```

## Usage

### Generate Constants

```bash
# Generate constants for all languages
make generate

# Or from the root directory
make global
```

### Validate Configuration

```bash
# Validate YAML files against schemas
make validate
```

### Clean Generated Files

```bash
# Remove all generated files
make clean
```

## Configuration Files

### `data/valheim-world.yml`

Core Valheim game constants including:
- World dimensions (radius, diameter, bounds)
- Coordinate system definitions
- Height system constants
- Biome definitions with IDs, colors, and properties

### `data/validation-data.yml`

Validation metrics and test data from seed `hkLycKKCMI`:
- Coordinate ranges and coverage
- Height ranges and thresholds
- Biome distribution percentages
- Performance metrics

### `data/rendering-config.yml`

Rendering and visualization settings:
- Resolution presets
- Rendering parameters
- Shoreline detection settings
- Filter thresholds

## Generated Files

The generators create language-specific constant files:

- **Python**: `backend/app/core/generated_constants.py` and `generated_utils.py`
- **C#**: `bepinex/src/VWE_DataExporter/ValheimConstants.cs`
- **JavaScript**: `procedural-export/client/valheim-constants.js`

## Adding New Constants

1. Add the constant to the appropriate YAML file in `data/`
2. Update the corresponding schema in `schemas/`
3. Update the generators to include the new constant
4. Run `make generate` to regenerate all language files

## Validation

All YAML files are validated against JSON Schema to ensure:
- Required fields are present
- Data types are correct
- Values are within expected ranges
- Biome IDs are valid Valheim enum values

## Dependencies

- `yamllint` - YAML linting
- `PyYAML` - Python YAML parsing
- `js-yaml` - JavaScript YAML parsing (for Node.js generators)
- `YamlDotNet` - C# YAML parsing
