# Global Constants Recommendation

## Current State

### What Exists
- ✅ **Schema**: `global/schemas/valheim-world.schema.json` - Defines expected structure
- ✅ **Templates**: C#, JavaScript/TypeScript templates for generating constants
- ✅ **Generators**: Python scripts to generate language-specific constants
- ❌ **Source Data**: No YAML file in `global/data/` to generate from

### What's Missing
```
global/
├── data/
│   └── valheim-world.yml        ← MISSING! Should be canonical source
```

---

## Problem

**Each project defines its own biome constants**, leading to:
1. Duplicate definitions across projects
2. Risk of inconsistency (ID mismatches, name differences)
3. No single source of truth
4. Harder to maintain as game updates

**Example of duplication:**
- `adaptive-sampling-client/backend/models/world_data.py` - Python Biome enum
- `adaptive-sampling-client/frontend/types/world-data.ts` - TypeScript Biome enum
- `bepinex-adaptive-sampling/src/.../BiomeExporter.cs` - C# biome names
- All manually maintained!

---

## Recommended Solution

### 1. Create Global Source File

**File**: `global/data/valheim-world.yml`

```yaml
metadata:
  version: "1.0.0"
  last_updated: "2025-01-15"
  validation_seed: "hkLycKKCMI"
  sources:
    - "Valheim game files (decompiled)"
    - "BepInEx Heightmap.Biome enum"
    - "VWE validation data"

world:
  radius: 10000.0
  diameter: 20000.0
  bounds: [-10000, 10000]
  water_edge: 10500.0

coordinates:
  origin: [0, 0]
  unit: "meters"
  axes:
    x: "east_west"
    y: "height"
    z: "north_south"

height:
  sea_level: 30.0
  multiplier: 200.0
  range: [-100, 100]
  ocean_threshold: 0.05
  mountain_threshold: 0.4

biomes:
  defaults:
    noise_threshold: 0.4
    height_range: [0, 100]
    distance_range: [0, 10000]
    polar_offset: 0
    fallback_distance: null
    min_mountain_distance: null

  Meadows:
    id: 1
    name: "Meadows"           # API/code identifier (no spaces)
    display_name: "Meadows"   # UI display name
    rgb: [121, 176, 81]
    hex: "#79B051"
    height_range: [0.0, 0.4]
    distance_range: [0, 1500]
    noise_threshold: 0.4
    polar_offset: 0

  BlackForest:
    id: 2
    name: "BlackForest"
    display_name: "Black Forest"
    rgb: [45, 66, 40]
    hex: "#2D4228"
    height_range: [0.0, 0.4]
    distance_range: [600, 6000]
    noise_threshold: 0.4
    polar_offset: 0

  Swamp:
    id: 4
    name: "Swamp"
    display_name: "Swamp"
    rgb: [98, 89, 71]
    hex: "#625947"
    height_range: [0.05, 0.25]
    distance_range: [3000, 6000]
    noise_threshold: 0.6
    polar_offset: 0

  Mountain:
    id: 8
    name: "Mountain"
    display_name: "Mountain"
    rgb: [209, 228, 237]
    hex: "#D1E4ED"
    height_range: [0.4, 1.0]
    distance_range: [1500, 10000]
    noise_threshold: 0.0
    polar_offset: 0
    min_mountain_distance: 300

  Plains:
    id: 16
    name: "Plains"
    display_name: "Plains"
    rgb: [246, 222, 145]
    hex: "#F6DE91"
    height_range: [0.05, 0.4]
    distance_range: [2000, 8000]
    noise_threshold: 0.4
    polar_offset: 0

  Ocean:
    id: 32
    name: "Ocean"
    display_name: "Ocean"
    rgb: [52, 97, 141]
    hex: "#34618D"
    height_range: [-1.0, 0.05]
    distance_range: [0, 10000]
    noise_threshold: 0.0
    polar_offset: 0

  Mistlands:
    id: 64
    name: "Mistlands"
    display_name: "Mistlands"
    rgb: [105, 105, 120]
    hex: "#696978"
    height_range: [0.0, 0.4]
    distance_range: [1000, 5000]
    noise_threshold: 0.5
    polar_offset: 0

  DeepNorth:
    id: 256
    name: "DeepNorth"
    display_name: "Deep North"
    rgb: [240, 248, 255]
    hex: "#F0F8FF"
    height_range: [0.0, 1.0]
    distance_range: [5000, 10000]
    noise_threshold: 0.0
    polar_offset: 0.075

  Ashlands:
    id: 512
    name: "Ashlands"
    display_name: "Ashlands"
    rgb: [120, 70, 50]
    hex: "#784632"
    height_range: [0.0, 1.0]
    distance_range: [5000, 10000]
    noise_threshold: 0.0
    polar_offset: -0.075
```

---

### 2. Generate Constants for Each Language

**Python** (FastAPI backend):
```bash
cd global/generators
python python_generator.py --input ../data/valheim-world.yml --output ../../etl/experimental/adaptive-sampling-client/backend/VWE_WorldDataAPI/app/core/valheim_constants.py
```

**Output**: `valheim_constants.py`
```python
from enum import IntEnum

class Biome(IntEnum):
    MEADOWS = 1
    BLACK_FOREST = 2
    SWAMP = 4
    MOUNTAIN = 8
    PLAINS = 16
    OCEAN = 32
    MISTLANDS = 64
    DEEP_NORTH = 256
    ASHLANDS = 512

BIOME_NAMES = {
    1: "Meadows",
    2: "BlackForest",
    4: "Swamp",
    8: "Mountain",
    16: "Plains",
    32: "Ocean",
    64: "Mistlands",
    256: "DeepNorth",
    512: "Ashlands",
}

BIOME_DISPLAY_NAMES = {
    1: "Meadows",
    2: "Black Forest",
    4: "Swamp",
    8: "Mountain",
    16: "Plains",
    32: "Ocean",
    64: "Mistlands",
    256: "Deep North",
    512: "Ashlands",
}

BIOME_COLORS_HEX = {
    1: "#79B051",
    2: "#2D4228",
    4: "#625947",
    8: "#D1E4ED",
    16: "#F6DE91",
    32: "#34618D",
    64: "#696978",
    256: "#F0F8FF",
    512: "#784632",
}
```

**TypeScript** (Next.js frontend):
```bash
cd global/generators
node typescript_generator.js --input ../data/valheim-world.yml --output ../../etl/experimental/adaptive-sampling-client/frontend/VWE_MapViewer/src/lib/valheim-constants.ts
```

**Output**: `valheim-constants.ts`
```typescript
export enum Biome {
  Meadows = 1,
  BlackForest = 2,
  Swamp = 4,
  Mountain = 8,
  Plains = 16,
  Ocean = 32,
  Mistlands = 64,
  DeepNorth = 256,
  Ashlands = 512,
}

export const BiomeNames: Record<Biome, string> = {
  [Biome.Meadows]: 'Meadows',
  [Biome.BlackForest]: 'BlackForest',
  [Biome.Swamp]: 'Swamp',
  [Biome.Mountain]: 'Mountain',
  [Biome.Plains]: 'Plains',
  [Biome.Ocean]: 'Ocean',
  [Biome.Mistlands]: 'Mistlands',
  [Biome.DeepNorth]: 'DeepNorth',
  [Biome.Ashlands]: 'Ashlands',
};

export const BiomeDisplayNames: Record<Biome, string> = {
  [Biome.Meadows]: 'Meadows',
  [Biome.BlackForest]: 'Black Forest',
  [Biome.Swamp]: 'Swamp',
  [Biome.Mountain]: 'Mountain',
  [Biome.Plains]: 'Plains',
  [Biome.Ocean]: 'Ocean',
  [Biome.Mistlands]: 'Mistlands',
  [Biome.DeepNorth]: 'Deep North',
  [Biome.Ashlands]: 'Ashlands',
};

export const BiomeColorsHex: Record<Biome, string> = {
  [Biome.Meadows]: '#79B051',
  [Biome.BlackForest]: '#2D4228',
  [Biome.Swamp]: '#625947',
  [Biome.Mountain]: '#D1E4ED',
  [Biome.Plains]: '#F6DE91',
  [Biome.Ocean]: '#34618D',
  [Biome.Mistlands]: '#696978',
  [Biome.DeepNorth]: '#F0F8FF',
  [Biome.Ashlands]: '#784632',
};
```

**C#** (BepInEx plugins):
```bash
cd global/generators
dotnet run generate-constants --input ../data/valheim-world.yml --output ../../etl/experimental/bepinex-adaptive-sampling/src/VWE_DataExporter/ValheimConstants.cs
```

---

### 3. Update Projects to Import Generated Constants

**Backend**:
```python
from app.core.valheim_constants import Biome, BIOME_NAMES, BIOME_DISPLAY_NAMES
```

**Frontend**:
```typescript
import { Biome, BiomeNames, BiomeDisplayNames, BiomeColorsHex } from '@/lib/valheim-constants';
```

**BepInEx**:
```csharp
using VWE_DataExporter.Constants;
// Use ValheimConstants.BIOME_NAMES
```

---

## Benefits

1. **Single Source of Truth**: One YAML file defines all constants
2. **Consistency**: Generated code guaranteed to match across languages
3. **Type Safety**: Enums and types generated for each language
4. **Maintainability**: Update once, regenerate everywhere
5. **Documentation**: YAML file serves as canonical reference
6. **Validation**: Schema validates YAML before generation
7. **Versioning**: Track changes to game constants over time

---

## Implementation Steps

1. ✅ Create `global/data/valheim-world.yml` (using schema as guide)
2. ✅ Validate YAML against schema
3. ✅ Test generators with new YAML file
4. ✅ Update `adaptive-sampling-client` to use generated constants
5. ⬜ Update other experimental projects
6. ⬜ Add CI/CD step to regenerate on YAML changes
7. ⬜ Document in global/README.md

---

## Notes

- **Templates already exist** in `global/generators/`
- **Schema already defined** in `global/schemas/`
- Only missing piece is the **source YAML data file**
- Generators may need minor updates to handle `name` vs `display_name` separation
- Consider adding `make generate-constants` to project Makefiles

---

## Future Enhancements

1. Add validation data from test seeds
2. Include structure/prefab constants
3. Generate API documentation from YAML
4. Auto-generate OpenAPI schemas
5. Create visualization of biome distribution
6. Version constants per game version (e.g., Mistlands update, Ashlands update)

