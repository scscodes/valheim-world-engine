#!/usr/bin/env python3
"""
Generate Comprehensive Water Level Renders
Generates water masks and height-aware biome maps at multiple water levels for comparison
"""

import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "etl/experimental/adaptive-sampling-client/backend/VWE_WorldDataAPI"
sys.path.insert(0, str(backend_path))

from app.services.image_generator import ImageGenerator
from app.models.world_data import BiomeMapResponse, HeightmapResponse

def main():
    print("="*80)
    print("Comprehensive Water Level Renders - Seed: hnLycKKCMI")
    print("="*80)

    # Paths
    data_root = Path("/home/steve/projects/valhem-world-engine/data/seeds")
    # Seed: hnLycKKCMI (not hkLycKKCMI!)
    seed_hash = "1723ef4f95a0499dd0c092f8c09183a415909343bfdee047ae98346f7a66f68c"
    seed_path = data_root / seed_hash / "world_data"
    output_dir = Path("/home/steve/projects/valhem-world-engine/etl/experimental/adaptive-sampling-client")

    print(f"\nInput: {seed_path}")
    print(f"Output Dir: {output_dir}")

    # Load data
    print("\n[1/3] Loading biome and heightmap data...")
    with open(seed_path / "biomes.json") as f:
        biome_json = json.load(f)
    with open(seed_path / "heightmap.json") as f:
        height_json = json.load(f)

    biome_data = BiomeMapResponse(
        resolution=biome_json['resolution'],
        world_radius=biome_json.get('world_radius', 10000.0),
        world_diameter=biome_json.get('world_diameter', 20000.0),
        biome_map=biome_json['biome_map']
    )

    heightmap_data = HeightmapResponse(
        resolution=height_json['resolution'],
        world_radius=height_json.get('world_radius', 10000.0),
        world_diameter=height_json.get('world_diameter', 20000.0),
        heightmap=height_json['height_map']
    )

    print(f"  ✓ Loaded {biome_data.resolution}×{biome_data.resolution} data")

    generator = ImageGenerator()
    target_res = 2048

    # Water levels: 10-40 in increments of 5
    water_levels = list(range(10, 45, 5))  # 10, 15, 20, 25, 30, 35, 40

    print(f"\n[2/3] Generating water masks...")
    print(f"  Resolution: {target_res}×{target_res}")
    print(f"  Water levels: {water_levels}")
    print(f"  Color scheme:")
    print(f"    Dark Blue  = Deep Ocean (Ocean biome underwater)")
    print(f"    Light Blue = Shallows (non-Ocean underwater)")
    print(f"    Green      = Land (above water level)")
    print(f"    Red/White  = Spawn location (0, 0)")
    print()

    for wl in water_levels:
        print(f"  Water level = {wl}m...", end=" ", flush=True)

        buffer = generator.generate_biome_image(
            biome_data,
            heightmap_data=heightmap_data,
            target_resolution=target_res,
            render_mode="nearest",
            visualization_mode="water_mask",
            water_level=wl
        )

        output_path = output_dir / f"water_mask_wl{int(wl)}.png"
        with open(output_path, 'wb') as f:
            f.write(buffer.read())

        print(f"✓ {output_path.name}")

    print(f"\n[3/3] Generating height-aware biome maps...")
    print(f"  Resolution: {target_res}×{target_res}")
    print(f"  Water levels: {water_levels}")
    print()

    for wl in water_levels:
        print(f"  Water level = {wl}m...", end=" ", flush=True)

        buffer = generator.generate_biome_image(
            biome_data,
            heightmap_data=heightmap_data,
            target_resolution=target_res,
            render_mode="nearest",
            visualization_mode="height_aware",
            water_level=wl
        )

        output_path = output_dir / f"biomes_height_aware_wl{int(wl)}.png"
        with open(output_path, 'wb') as f:
            f.write(buffer.read())

        print(f"✓ {output_path.name}")

    # Summary
    print(f"\n{'='*80}")
    print("Generated Files:")
    print("="*80)
    print(f"\nWater Masks (for threshold tuning):")
    for wl in water_levels:
        print(f"  {wl}m: water_mask_wl{wl}.png")

    print(f"\nHeight-Aware Biome Maps (realistic renders):")
    for wl in water_levels:
        print(f"  {wl}m: biomes_height_aware_wl{wl}.png")

    print(f"\n{'='*80}")
    print("Visual Comparison Guide:")
    print("="*80)
    print("""
Compare water masks to find the optimal water level:

1. **Ashlands (south/bottom):**
   - Should show land (green) areas at bottom
   - Southern hemisphere bias

2. **DeepNorth (north/top):**
   - Should show land (green) areas at top
   - Northern hemisphere bias

3. **Ocean Ring:**
   - Dark blue outer ring (Ocean biome underwater)
   - Should be consistent thickness around world edge

4. **Shallows (light blue):**
   - Should form rings/halos around all land masses
   - Represents submerged shoreline terrain

5. **Spawn Location (red/white dot):**
   - Always at world center (0, 0)
   - Helps verify orientation (Ashlands south, DeepNorth north)

6. **Water Level Sweet Spot:**
   - Too low (10m): Too much land visible
   - Just right (25-30m): Natural shoreline separation
   - Too high (35-40m): Islands become smaller

Compare against reference: docs/biomes_hnLycKKCMI.png
    """)

    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
