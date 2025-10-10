# Valheim Biome Reference

## **CRITICAL: Biome Enum Values**

Valheim uses **bit-flag enum values** (powers of 2), NOT sequential integers.

### **Correct Biome Enum Values:**

| Biome        | Enum Value | Binary     | Hex  |
|--------------|------------|------------|------|
| Meadows      | 1          | 0b00000001 | 0x01 |
| BlackForest  | 2          | 0b00000010 | 0x02 |
| Swamp        | 4          | 0b00000100 | 0x04 |
| Mountain     | 8          | 0b00001000 | 0x08 |
| Plains       | 16         | 0b00010000 | 0x10 |
| Ocean        | 32         | 0b00100000 | 0x20 |
| Mistlands    | 64         | 0b01000000 | 0x40 |
| DeepNorth    | 256        | 0b100000000| 0x100|
| Ashlands     | 512        | 0b1000000000| 0x200|

**Source:** `Heightmap.Biome` enum from Valheim's assembly (`assembly_valheim.dll`)

## **Biome Colors (Renderer)**

Standard colors used in `client/renderer.js`:

```javascript
const BIOMES = {
    1: { name: 'Meadows', color: [121, 179, 85] },      // #79B355
    2: { name: 'BlackForest', color: [64, 81, 50] },    // #405132
    4: { name: 'Swamp', color: [119, 108, 82] },        // #776C52
    8: { name: 'Mountain', color: [220, 225, 238] },    // #DCE1EE
    16: { name: 'Plains', color: [193, 181, 122] },     // #C1B57A
    32: { name: 'Ocean', color: [59, 103, 163] },       // #3B67A3
    64: { name: 'Mistlands', color: [78, 93, 107] },    // #4E5D6B
    256: { name: 'DeepNorth', color: [210, 230, 255] }, // #D2E6FF
    512: { name: 'Ashlands', color: [155, 75, 60] }     // #9B4B3C
};
```

## **Common Mistakes**

❌ **WRONG:** Using sequential indices (0, 1, 2, 3, 4, 5, 6, 7, 8)
❌ **WRONG:** Using different enum values like `Ashlands = 6`
❌ **WRONG:** Assuming missing values indicate errors

✅ **CORRECT:** Always use powers of 2 (1, 2, 4, 8, 16, 32, 64, 256, 512)
✅ **CORRECT:** Match C# `Heightmap.Biome` enum values exactly
✅ **CORRECT:** Handle "unknown" biomes gracefully (biome IDs not in the enum)

## **World Generation Constants**

- **World Diameter:** 20,000 meters (±10,000m from center)
- **Playable Radius:** ~10,500 meters from center
- **World Center:** (0, 0) in world coordinates
- **Ocean Boundary:** Starts around ~7,900m from center

### **Biome Distance Thresholds (Actual In-Game Values)**

⚠️ **Note:** Decompiled constants (12,000m) are OUTDATED. Actual thresholds are lower:

| Biome | Min Distance | Max Distance | Direction Bias |
|-------|--------------|--------------|----------------|
| Meadows | 0m | ~5,000m | Center |
| BlackForest | ~600m | ~6,000m | Mid-ring |
| Swamp | ~2,000m | ~6,000m | Mid-ring (wet areas) |
| Plains | ~3,000m | ~8,000m | Outer mid-ring |
| Mountain | ~1,000m | ~10,000m | High elevation anywhere |
| Mistlands | ~6,000m | ~10,000m | Outer ring |
| Ocean | ~7,900m | Edge | All directions |
| **DeepNorth** | **~7,140m** | Edge | **North (y+4000 offset)** |
| **Ashlands** | **~9,626m** | Edge | **South (y-4000 offset)** |

**Why DeepNorth/Ashlands appear so much:**
- These biomes fill the outer 30-40% of the world radius
- They have directional offsets (±4000m on Y-axis)
- This is INTENTIONAL Valheim design for end-game content placement

## **Sample Data Format**

Each sample in JSON export:

```json
{
  "X": -10000.0,
  "Z": -9980.469,
  "Biome": 32,
  "Height": -400.0
}
```

- **X, Z:** World coordinates in meters
- **Biome:** Enum value (power of 2)
- **Height:** Terrain height in meters

## **Validation**

To verify biome data integrity:

```bash
python3 -c "
import json
with open('output/samples/SEED-samples-512.json') as f:
    data = json.load(f)
    biomes = set(s['Biome'] for s in data['Samples'])
    print('Biome IDs found:', sorted(biomes))

    # Check all are powers of 2 or 0
    valid = all(b == 0 or (b & (b-1)) == 0 for b in biomes)
    print('All valid power-of-2 biome IDs:', valid)
"
```

## **References**

- C# Plugin: `procedural-export/src/VWE_ProceduralMetadata/OptimalSampler.cs:121-136`
- Renderer: `procedural-export/client/renderer.js:6-17`
- Python Validator: `procedural-export/scripts/validate_metadata.py:236-249`
