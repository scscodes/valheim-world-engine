# VWE ETL Pipeline Strategies

This directory contains all ETL (Extract, Transform, Load) pipeline approaches for the Valheim World Engine, organized by maturity level.

## Directory Structure

```
etl/
├── archive/           # Deprecated approaches (no longer developed)
├── stable/           # Production-ready approaches (validated & deployed)
└── experimental/     # Early-stage approaches (research & development)
```

## Maturity Levels

### 📁 **Archive** - Deprecated Approaches
- **Purpose**: Preserve historical approaches and lessons learned
- **Status**: No longer developed or maintained
- **Usage**: Reference only, do not use for new development
- **Examples**: Legacy implementations, failed experiments

### 🏭 **Stable** - Production-Ready Approaches  
- **Purpose**: Validated, tested, and ready for production use
- **Status**: Actively maintained and deployed
- **Usage**: Use for production workloads
- **Examples**: BepInEx dense sampling, validated pipelines

### 🧪 **Experimental** - Early-Stage Approaches
- **Purpose**: Research, development, and proof-of-concept work
- **Status**: In active development, not production-ready
- **Usage**: Development and testing only
- **Examples**: Procedural metadata extraction, new algorithms

## Current Approaches

### Legacy Approaches (Moved to Root)
- **`../bepinex/`** - BepInEx plugin-based dense sampling
  - Status: ✅ Production ready
  - Performance: ~3 minutes, 512×512 resolution
  - Coverage: Full world (±10km)
  - Validation: Complete

- **`../procedural-export/`** - Procedural metadata extraction
  - Status: 🧪 Early development
  - Performance: <1 second metadata + ~25s adaptive sampling
  - Coverage: Full world via procedural parameters
  - Validation: In progress

### New ETL Approaches (This Directory)
- **`stable/`** - New production-ready approaches (empty, ready for new implementations)
- **`experimental/`** - New experimental approaches (empty, ready for research)
- **`archive/`** - Deprecated new approaches (empty, ready for historical approaches)

## Migration Path

```
Experimental → Stable → Archive
     ↓            ↓        ↓
   Research → Production → Deprecated
```

### Moving Between Levels

**Experimental → Stable:**
1. Complete comprehensive testing
2. Document performance benchmarks
3. Add error handling and recovery
4. Create production documentation
5. Move directory to `stable/`

**Stable → Archive:**
1. Identify replacement approach
2. Create migration guide
3. Update all references
4. Move directory to `archive/`
5. Add deprecation notice

## Development Guidelines

### For Experimental Approaches
- Use clear, descriptive naming
- Document hypothesis and approach
- Include performance benchmarks
- Test with small datasets first
- Document findings and lessons learned

### For Stable Approaches
- Follow VWE standards and conventions
- Maintain comprehensive documentation
- Include proper error handling
- Keep performance benchmarks updated
- Version all changes

### For Archive Approaches
- Document why deprecated
- Include migration notes
- Preserve historical context
- Do not modify without approval

## Quick Reference

| Level | Use For | Modify | Deploy | Examples |
|-------|---------|--------|--------|----------|
| **Experimental** | Research, POCs | ✅ Yes | ❌ No | New algorithms, untested ideas |
| **Stable** | Production | ✅ Yes | ✅ Yes | Validated approaches, core features |
| **Archive** | Reference | ❌ No | ❌ No | Deprecated, legacy, failed experiments |

## Integration

All ETL approaches integrate with:
- VWE Docker orchestration
- Global configuration standards
- Generator system for code generation
- Backend API for job management
- Warm container system for instant deployment
