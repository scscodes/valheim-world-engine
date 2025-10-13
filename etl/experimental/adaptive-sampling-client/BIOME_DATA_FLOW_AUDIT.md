# Biome Data Flow Audit - Complete Analysis

## Executive Summary

**Root Cause:** Frontend `BiomeNames` uses display names with spaces (`"Deep North"`, `"Black Forest"`) while backend returns camelCase names (`"DeepNorth"`, `"BlackForest"`). This causes legend lookup to fail and hide DeepNorth/BlackForest entries.

**Impact:** DeepNorth (31.7%) and BlackForest (misidentified as Mountain) are not visible in the legend despite being present in the data.

---

## Data Flow Trace

### 1. BepInEx Export → biomes.json
**Source:** `etl/experimental/bepinex-adaptive-sampling/src/VWE_DataExporter/DataExporters/BiomeExporter.cs`

**Canonical Biome Names (lines 178-189):**
```csharp
{
    { 1, "Meadows" },
    { 2, "BlackForest" },     // ✓ No space
    { 4, "Swamp" },
    { 8, "Mountain" },
    { 16, "Plains" },
    { 32, "Ocean" },
    { 64, "Mistlands" },
    { 256, "DeepNorth" },     // ✓ No space
    { 512, "Ashlands" }
}
```

**Export Format:**
```json
{
  "biome_map": [[1, 2, 4, ...]],
  "biome_names": {
    "1": "Meadows",
    "2": "BlackForest",
    "256": "DeepNorth",
    ...
  }
}
```

---

### 2. Backend Processing

#### A. world_loader.py → _get_biome_name()
**Status:** ✅ **CORRECT** (after fix)

```python
from ..models.world_data import Biome

biome_names = {
    Biome.MEADOWS: "Meadows",
    Biome.BLACK_FOREST: "BlackForest",     # ✓ Matches BepInEx
    Biome.DEEP_NORTH: "DeepNorth",         # ✓ Matches BepInEx
    ...
}
```

#### B. Backend API Response
**Endpoint:** `/api/v1/worlds/hkLycKKCMI/biomes?format=json`

**Actual Response:**
```json
{
  "metadata": {
    "biome_counts": {
      "Ocean": 11904,
      "DeepNorth": 20792,      // ✓ camelCase (31.7%)
      "Mountain": 6814,
      "Ashlands": 9716,        // ✓ Now shows correctly (14.8%)
      "Swamp": 1770,
      "Mistlands": 3567,
      "Plains": 7445,
      "BlackForest": 1484,     // ✓ camelCase (2.3%)
      "Meadows": 2044
    }
  }
}
```

---

### 3. Frontend Processing

#### A. TypeScript Biome Enum
**File:** `frontend/VWE_MapViewer/src/types/world-data.ts`

**Status:** ✅ **CORRECT**

```typescript
export enum Biome {
  None = 0,
  Meadows = 1,
  BlackForest = 2,       // ✓ ID correct
  Swamp = 4,
  Mountain = 8,
  Plains = 16,
  Ocean = 32,
  Mistlands = 64,
  DeepNorth = 256,       // ✓ ID correct
  Ashlands = 512,
}
```

#### B. BiomeNames Mapping
**File:** `frontend/VWE_MapViewer/src/types/world-data.ts` (lines 56-67)

**Status:** ❌ **INCORRECT** - Uses display names with spaces

```typescript
export const BiomeNames: Record<Biome, string> = {
  [Biome.None]: 'None',
  [Biome.Meadows]: 'Meadows',
  [Biome.Swamp]: 'Swamp',
  [Biome.Mountain]: 'Mountain',
  [Biome.BlackForest]: 'Black Forest',   // ✗ Space breaks API lookup
  [Biome.Plains]: 'Plains',
  [Biome.Ocean]: 'Ocean',
  [Biome.Mistlands]: 'Mistlands',
  [Biome.Ashlands]: 'Ashlands',
  [Biome.DeepNorth]: 'Deep North',       // ✗ Space breaks API lookup
};
```

#### C. Legend Rendering
**File:** `frontend/VWE_MapViewer/src/app/page.tsx` (lines 149-168)

**Problem Code:**
```typescript
{Object.entries(BiomeNames).map(([id, name]) => {
  const biomeId = parseInt(id) as Biome;
  const count = biomeData.metadata?.biome_counts?.[name] || 0;
  //                                                ^^^^
  // Looks for "Deep North" in biome_counts
  // But backend returns "DeepNorth"
  // Result: count = 0
  
  if (count === 0) return null;  // ← Entry hidden!
```

**Why It Fails:**
1. Frontend looks for `biome_counts["Deep North"]` → undefined → 0
2. Backend has `biome_counts["DeepNorth"]` = 20792
3. Legend entry is hidden due to `if (count === 0)`

---

## Global Standards Check

### Schema Location
- ✅ Schema exists: `global/schemas/valheim-world.schema.json`
- ❌ **No YAML data file found** in `global/` directory
- ⚠️ Templates exist but no source data to generate from

### Expected Global Structure
```
global/
├── data/
│   └── valheim-world.yml     ← MISSING! Should define canonical biome names
├── schemas/
│   └── valheim-world.schema.json  ← EXISTS
└── generators/
    ├── python_generator.py
    └── typescript_generator.py
```

### Recommendation
**Create `global/data/valheim-world.yml`** with canonical Valheim constants, including:
```yaml
biomes:
  Meadows:
    id: 1
    name: "Meadows"
    display_name: "Meadows"
    rgb: [121, 176, 81]
    hex: "#79B051"
  BlackForest:
    id: 2
    name: "BlackForest"          # ← API key
    display_name: "Black Forest" # ← UI display
    rgb: [45, 66, 40]
    hex: "#2D4228"
  # ...
```

---

## Biome Name Standard (Canonical)

Based on BepInEx source and Valheim game code:

| ID  | Canonical Name | Display Name | Backend Returns | Frontend Should Use |
|-----|----------------|--------------|-----------------|---------------------|
| 1   | Meadows        | Meadows      | "Meadows"       | ✅ "Meadows"       |
| 2   | BlackForest    | Black Forest | "BlackForest"   | ❌ "Black Forest"  |
| 4   | Swamp          | Swamp        | "Swamp"         | ✅ "Swamp"         |
| 8   | Mountain       | Mountain     | "Mountain"      | ✅ "Mountain"      |
| 16  | Plains         | Plains       | "Plains"        | ✅ "Plains"        |
| 32  | Ocean          | Ocean        | "Ocean"         | ✅ "Ocean"         |
| 64  | Mistlands      | Mistlands    | "Mistlands"     | ✅ "Mistlands"     |
| 256 | DeepNorth      | Deep North   | "DeepNorth"     | ❌ "Deep North"    |
| 512 | Ashlands       | Ashlands     | "Ashlands"      | ✅ "Ashlands"      |

---

## Issues Found

### 1. Name Mismatch (Critical)
- **Backend:** Returns camelCase (`"DeepNorth"`, `"BlackForest"`)
- **Frontend:** Looks for spaced names (`"Deep North"`, `"Black Forest"`)
- **Impact:** Legend entries hidden despite data being present

### 2. No Global Biome Constants
- No YAML source file in `global/data/`
- Project-specific definitions scattered across codebase
- Risk of inconsistency across experimental projects

### 3. Missing Display Name Separation
- BiomeNames serves dual purpose: API lookup + UI display
- Should have separate `BIOME_API_NAMES` and `BIOME_DISPLAY_NAMES`

---

## Fixes Required

### Immediate (Frontend)
1. Update `BiomeNames` to match backend API response
2. Add separate `BiomeDisplayNames` for UI

### Short-term (Backend)
1. Consider returning both `api_name` and `display_name` in metadata

### Long-term (Global Standards)
1. Create `global/data/valheim-world.yml` with canonical biome definitions
2. Generate constants for Python, TypeScript, C# from single source
3. Update adaptive-sampling-client to use generated constants

---

## Testing Checklist

After applying fixes:
- [ ] Backend restart shows all biome names in API response
- [ ] Frontend legend shows all 9 biomes
- [ ] DeepNorth: 31.7% visible
- [ ] BlackForest: 2.3% visible (not confused with Mountain)
- [ ] Ashlands: 14.8% visible
- [ ] No "Unknown_*" entries
- [ ] Biome colors match correctly on map

---

## Next Steps

1. **Fix frontend BiomeNames** (immediate)
2. **Document naming convention** (this doc)
3. **Create global biome constants** (follow-up)
4. **Update other experimental projects** to use standards

