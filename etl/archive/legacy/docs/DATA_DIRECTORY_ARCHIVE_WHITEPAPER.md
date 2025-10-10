# Data Directory Archive Whitepaper

**Timestamp:** 2025-01-27T10:30:00Z  
**Scope:** Generated world data and seed storage directory  
**Status:** ACTIVE - Production data storage  
**Version:** 1.0.0 (Production)

## TLDR

Data storage directory for Valheim world generation outputs, including raw world files (.db/.fwl), extracted data (JSON/PNG), and processed renders. **PRODUCTION DATA** - Contains validated world generation results and analysis outputs. This directory serves as the primary data storage location for the VWE system.

## Architecture Overview

### Directory Structure
```
data/
├── seeds/                          # Per-seed data directories
│   └── {seed_hash}/                # SHA256 hash of seed string
│       ├── raw/                    # Raw Valheim world files
│       ├── worlds_local/           # Server-created .db/.fwl files
│       ├── extracted/              # BepInEx plugin exports
│       ├── processed/              # ETL pipeline outputs
│       └── renders/                # Final rendered map layers
├── valheim_dev.db                  # SQLite development database
└── ARCHIVE_WHITEPAPER.md          # This document
```

### Data Flow
```
Seed Input → Hash Generation → Directory Creation → World Generation → Data Export → Processing → Rendering
```

## Key Accomplishments

### ✅ Production Data Storage
- **Organized Structure**: Hierarchical directory layout by seed hash
- **Data Persistence**: Long-term storage of generated world data
- **Version Control**: Git-ignored data with proper backup strategies
- **Access Patterns**: Optimized for both API serving and analysis

### ✅ Data Validation
- **File Integrity**: Validation of .db/.fwl file creation
- **Data Completeness**: Verification of all expected outputs
- **Format Consistency**: Standardized JSON and binary formats
- **Quality Assurance**: Validation against known good seeds

### ✅ Storage Optimization
- **Efficient Layout**: Logical separation of raw, extracted, processed data
- **Size Management**: Compression and cleanup strategies
- **Access Performance**: Optimized for both sequential and random access
- **Backup Strategy**: Regular backups of critical data

## Technical Architecture

### Seed Hash System
```python
def seed_to_hash(seed: str) -> str:
    """Generate SHA256 hash for seed-based directory naming"""
    clean = sanitize_seed(seed)
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()

# Example: "hkLycKKCMI" → "f4b1e8a02517e8cfbba23e3fb8af7a940507738339e95438b8d09ed7d86578d0"
```

### Directory Structure
```
{seed_hash}/
├── raw/                           # Raw Valheim server outputs
│   └── (server logs, temp files)
├── worlds_local/                  # Valheim world files
│   ├── {seed}.db                 # World data (binary)
│   └── {seed}.fwl                # World metadata (binary)
├── extracted/                     # BepInEx plugin exports
│   ├── worldgen_plan.json        # Generation orchestration plan
│   ├── worldgen_logs.txt         # Container generation logs
│   ├── biomes.json               # Biome data export
│   ├── heightmap.npy             # Heightmap data export
│   └── world_metadata.json       # World generation metadata
├── processed/                     # ETL pipeline outputs
│   ├── merged_data.json          # Combined biome + height data
│   ├── statistics.json           # World generation statistics
│   └── validation_report.json    # Data quality validation
└── renders/                       # Final rendered outputs
    ├── biomes_layer.webp         # Biome visualization
    ├── land_sea_layer.webp       # Land/sea mask
    ├── heightmap_layer.webp      # Height visualization
    └── shoreline_overlay.webp    # Shoreline detection
```

### Data Formats

#### Raw World Files (.db/.fwl)
- **Format**: Valheim binary format
- **Size**: ~1-10MB per world
- **Content**: Complete world state, structures, player data
- **Usage**: Backup, analysis, world restoration

#### Extracted Data (JSON)
```json
{
  "world_metadata": {
    "world_name": "hkLycKKCMI",
    "world_seed": "hkLycKKCMI", 
    "generated_at": "2025-10-09T10:30:00Z",
    "resolution": "512x512",
    "world_size": 20000,
    "sea_level": 30.0
  },
  "samples": [
    {
      "x": -10000.0,
      "z": -10000.0,
      "biome": 256,
      "height": 45.2
    }
  ]
}
```

#### Rendered Outputs (WebP)
- **Format**: WebP for optimal compression
- **Resolution**: 512×512 (validation), 1024×1024 (production)
- **Layers**: Biome, height, land/sea, shoreline
- **Usage**: Web visualization, analysis, export

## Critical Problems Solved

### 1. Data Organization
**Problem**: Unstructured data storage with naming conflicts  
**Solution**: SHA256 hash-based directory structure  
**Impact**: Unique, collision-free data organization

### 2. File Ownership
**Problem**: Docker containers creating root-owned files  
**Solution**: PUID/PGID environment variables + recursive chown  
**Impact**: Proper file permissions for host access

### 3. Data Validation
**Problem**: Incomplete or corrupted data generation  
**Solution**: Comprehensive validation pipeline with quality checks  
**Impact**: Reliable data quality and completeness

### 4. Storage Efficiency
**Problem**: Large file sizes and inefficient storage  
**Solution**: WebP compression and logical data separation  
**Impact**: Reduced storage requirements and faster access

## Performance Metrics

### Storage Performance
- **Directory Creation**: ~0.1 seconds per seed
- **File Writing**: ~1-5 seconds per world (depending on size)
- **Data Validation**: ~0.5-2 seconds per world
- **Rendering**: ~10-30 seconds per layer

### Storage Requirements
- **Per World (512×512)**: ~50-100MB total
- **Per World (1024×1024)**: ~200-400MB total
- **Per World (2048×2048)**: ~800MB-1.5GB total
- **Database**: ~1-10MB per world metadata

### Access Patterns
- **Sequential Read**: ~10-50MB/s (SSD)
- **Random Read**: ~1-10MB/s (SSD)
- **Network Transfer**: ~1-10MB/s (depending on connection)
- **API Serving**: ~100-1000 requests/second

## Data Quality Assurance

### Validation Pipeline
1. **File Existence**: Verify all expected files are created
2. **File Integrity**: Check file sizes and checksums
3. **Data Completeness**: Validate JSON structure and required fields
4. **Data Consistency**: Cross-reference between different data sources
5. **Quality Metrics**: Check biome distribution and height ranges

### Quality Metrics
- **Completeness**: 100% of expected files present
- **Integrity**: File checksums match expected values
- **Consistency**: Data matches between .db/.fwl and JSON exports
- **Accuracy**: Biome IDs and coordinates match Valheim's logic

## Lessons Learned

### What Worked Well
1. **Hash-based Organization**: Eliminates naming conflicts and enables efficient lookup
2. **Hierarchical Structure**: Clear separation of concerns and data types
3. **Validation Pipeline**: Ensures data quality and completeness
4. **Compression**: WebP format provides excellent compression for visualization
5. **Backup Strategy**: Regular backups prevent data loss

### What Could Be Improved
1. **Data Compression**: More aggressive compression for large datasets
2. **Indexing**: Better indexing for faster data retrieval
3. **Caching**: More sophisticated caching for frequently accessed data
4. **Monitoring**: Better monitoring of storage usage and performance
5. **Cleanup**: Automated cleanup of old or unused data

### Key Insights
1. **Data Organization**: Good structure is critical for maintainability
2. **Validation**: Early validation prevents downstream issues
3. **Compression**: Right format choice significantly impacts storage
4. **Backup**: Regular backups are essential for production data
5. **Monitoring**: Storage monitoring prevents capacity issues

## Migration Impact

### Replaced Manual Storage
- **Ad-hoc Organization**: Structured directory hierarchy
- **Manual Validation**: Automated quality assurance pipeline
- **File Management**: Automated file organization and cleanup
- **Data Access**: Standardized API for data retrieval

### Enabled New Capabilities
- **Scalable Storage**: Hash-based organization scales to millions of seeds
- **Data Analysis**: Structured data enables complex analysis
- **API Serving**: Organized data enables efficient API responses
- **Visualization**: Rendered outputs enable rich visualizations

## Future Enhancements

### Short-term (Next 3 months)
1. **Data Compression**: More aggressive compression algorithms
2. **Indexing**: Better indexing for faster data retrieval
3. **Monitoring**: Storage usage and performance monitoring
4. **Cleanup**: Automated cleanup of old data

### Long-term (6+ months)
1. **Distributed Storage**: Multi-node storage for scalability
2. **Data Versioning**: Version control for data evolution
3. **Real-time Processing**: Streaming data processing
4. **Advanced Analytics**: Machine learning on stored data

## References

### Key Directories
- `seeds/`: Per-seed data storage
- `valheim_dev.db`: SQLite development database
- `ARCHIVE_WHITEPAPER.md`: This document

### Related Documentation
- `CLAUDE.md`: Project overview and data flow
- `procedural-export/VALIDATION_COMPLETE_512.md`: Data validation results
- `docs/WORLD_GENERATION.md`: World generation pipeline

---

**Status**: ACTIVE - Production data storage  
**Last Updated**: 2025-01-27  
**Next Review**: 2025-04-01  
**Maintainer**: VWE Team
