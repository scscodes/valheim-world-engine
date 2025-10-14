#!/usr/bin/env python3
"""
Generate Refined Water Level Renders
Focused on water levels 20-30m with 1m increments for precise tuning
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
    print("Refined Water Level Renders - Seed: hnLycKKCMI")
    print("Focused Range: 20-30m (1m increments)")
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

    # Water levels: 20-30 in increments of 1
    water_levels = list(range(20, 31))  # 20, 21, 22, ..., 30

    print(f"\n[2/3] Generating enhanced water masks...")
    print(f"  Resolution: {target_res}×{target_res}")
    print(f"  Water levels: {water_levels[0]}m - {water_levels[-1]}m ({len(water_levels)} levels)")
    print(f"  Color scheme:")
    print(f"    Dark Blue    = Deep Ocean (Ocean biome underwater)")
    print(f"    Light Blue   = Shallows (other biomes underwater)")
    print(f"    Red-Orange   = Ashlands Water (Ashlands underwater)")
    print(f"    Green        = Land (above water level)")
    print(f"    Red/White    = Spawn location (0, 0) - 50% smaller")
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
    print(f"  Water levels: {water_levels[0]}m - {water_levels[-1]}m ({len(water_levels)} levels)")
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
    print(f"\nEnhanced Water Masks (11 files, wl 20-30):")
    for wl in water_levels:
        print(f"  {wl}m: water_mask_wl{wl}.png")

    print(f"\nHeight-Aware Biome Maps (11 files, wl 20-30):")
    for wl in water_levels:
        print(f"  {wl}m: biomes_height_aware_wl{wl}.png")

    print(f"\n{'='*80}")
    print("Refinements Applied:")
    print("="*80)
    print("""
1. ✓ Spawn marker reduced by 50% (now 0.5% of image size)
2. ✓ Ashlands water now distinct (red-orange vs light blue shallows)
3. ✓ Fine-grained water level steps (1m increments)
4. ✓ Focused range (20-30m) for precise threshold tuning

Color Legend:
- Dark Blue:   Ocean biome underwater
- Light Blue:  Shallows (non-Ocean, non-Ashlands underwater)
- Red-Orange:  Ashlands water (Ashlands biome underwater)
- Green:       Land (above water level)
- Red/White:   Spawn location at world center

Compare these renders against: docs/biomes_hnLycKKCMI.png
Look for the water level that best matches the land/water separation pattern.
    """)

    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
