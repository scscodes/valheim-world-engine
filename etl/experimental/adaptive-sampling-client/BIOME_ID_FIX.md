# Biome ID Fix - Critical Data Quality Issue

## Root Cause
**Multiple biome IDs were incorrectly mapped**, causing Ashlands and other biomes to be unrecognized or misrepresented.

## Errors Found

### Backend Python (`app/models/world_data.py`)
**Before:**
```python
MEADOWS = 1       # ✓ Correct
SWAMP = 2         # ✗ Should be 4
MOUNTAIN = 4      # ✗ Should be 8
BLACK_FOREST = 8  # ✗ Should be 2
PLAINS = 16       # ✓ Correct
OCEAN = 32        # ✓ Correct
MISTLANDS = 64    # ✓ Correct
ASHLANDS = 128    # ✗ Should be 512
DEEP_NORTH = 256  # ✓ Correct
```

### Frontend TypeScript (`src/types/world-data.ts`)
**Before:**
```typescript
Swamp = 2        # ✗ Should be 4
Mountain = 4     # ✗ Should be 8
BlackForest = 8  # ✗ Should be 2
Ashlands = 128   # ✗ Should be 512
```

## Correct Valheim Biome IDs
Based on `Heightmap.Biome` enum from Valheim game code (BepInEx source):

| ID  | Biome Name   | Hex   |
|-----|--------------|-------|
| 1   | Meadows      | 0x001 |
| 2   | BlackForest  | 0x002 |
| 4   | Swamp        | 0x004 |
| 8   | Mountain     | 0x008 |
| 16  | Plains       | 0x010 |
| 32  | Ocean        | 0x020 |
| 64  | Mistlands    | 0x040 |
| 256 | DeepNorth    | 0x100 |
| 512 | Ashlands     | 0x200 |

**Note:** These are bit flags, not sequential integers. There is no biome ID 128 in Valheim.

## Impact
- **Ashlands** (ID 512): 9,716 samples (14.8%) - Was shown as "Unknown_512"
- **DeepNorth** (ID 256): 20,792 samples (31.7%) - Was correct but mislabeled in some contexts
- **Swamp, Mountain, BlackForest**: Potentially miscolored or miscounted due to ID confusion

## Fix Applied
Both backend and frontend now use the correct Valheim biome IDs matching the BepInEx `Heightmap.Biome` enum.

**After:**
```python
# Backend
NONE = 0
MEADOWS = 1
BLACK_FOREST = 2
SWAMP = 4
MOUNTAIN = 8
PLAINS = 16
OCEAN = 32
MISTLANDS = 64
DEEP_NORTH = 256
ASHLANDS = 512
```

```typescript
// Frontend
None = 0,
Meadows = 1,
BlackForest = 2,
Swamp = 4,
Mountain = 8,
Plains = 16,
Ocean = 32,
Mistlands = 64,
DeepNorth = 256,
Ashlands = 512,
```

## Validation Required
1. **Activate project venv**: `source venv/bin/activate`
2. **Restart backend server** to load updated biome mappings
3. **Refresh frontend** to load updated TypeScript definitions
4. **Verify legend** shows all 9 biomes with correct percentages
5. **Verify map colors** match the correct biomes

## Expected Results After Restart
```json
{
  "biome_counts": {
    "Ocean": 11904,      // 18.2%
    "DeepNorth": 20792,  // 31.7%
    "BlackForest": 6814, // 10.4%
    "Ashlands": 9716,    // 14.8%  ← Now correctly labeled!
    "Mountain": 1770,    // 2.7%
    "Mistlands": 3567,   // 5.4%
    "Plains": 7445,      // 11.4%
    "Swamp": 1484,       // 2.3%
    "Meadows": 2044      // 3.1%
  }
}
```

## Additional Issue: Name Mismatch (Discovered Later)

### Problem
Frontend `BiomeNames` used display names with spaces while backend returned camelCase:
- Backend: `"DeepNorth"`, `"BlackForest"`
- Frontend: `"Deep North"`, `"Black Forest"`

This caused legend lookup to fail → entries hidden despite data being present.

### Solution
- Separated API names (`BiomeNames`) from display names (`BiomeDisplayNames`)
- `BiomeNames` now matches backend/BepInEx camelCase format
- Legend uses `BiomeNames` for lookup, `BiomeDisplayNames` for UI

### Files Updated
- `frontend/VWE_MapViewer/src/types/world-data.ts` - Added `BiomeDisplayNames`
- `frontend/VWE_MapViewer/src/app/page.tsx` - Updated legend to use both mappings

## Lessons Learned
- **Always validate biome IDs against canonical Valheim source** (e.g., BepInEx decompiled code)
- **Biome IDs are bit flags**, not sequential integers
- **Data contract alignment is critical** - backend, frontend, and export must agree on ID mappings AND naming conventions
- **Separate API contracts from UI display** - API names should match backend, display names can be user-friendly
- **Add integration tests** to catch ID mismatches and name mismatches early
- **Check both IDs and names** when debugging data flow issues

