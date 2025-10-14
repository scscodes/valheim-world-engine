#!/usr/bin/env python3
"""
Regenerate Biome PNG with NEAREST neighbor interpolation
Uses the fixed image_generator.py from adaptive-sampling-client
"""

import sys
import json
from pathlib import Path

# Add the backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "etl/experimental/adaptive-sampling-client/backend/VWE_WorldDataAPI"))

from app.services.image_generator import ImageGenerator
from app.models.world_data import BiomeMapResponse


def regenerate_png(json_path: Path, output_path: Path, target_resolution: int = 4096):
    """Regenerate PNG from JSON with NEAREST interpolation"""

    print(f"Loading biome data from: {json_path}")

    # Load JSON
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Create BiomeMapResponse
    biome_response = BiomeMapResponse(
        seed=data.get('seed', 'unknown'),
        resolution=data['resolution'],
        biome_map=data['biome_map'],
        world_size=data.get('world_size', 10000.0),
        pixel_to_world_scale=data.get('pixel_to_world_scale', None)
    )

    print(f"Source resolution: {biome_response.resolution}x{biome_response.resolution}")
    print(f"Target resolution: {target_resolution}x{target_resolution}")
    print(f"Upscale method: NEAREST neighbor (no interpolation)")

    # Generate PNG
    generator = ImageGenerator()
    buffer = generator.generate_biome_image(biome_response, target_resolution=target_resolution)

    # Write to file
    print(f"Writing PNG to: {output_path}")
    with open(output_path, 'wb') as f:
        f.write(buffer.getvalue())

    print(f"✅ PNG generated successfully!")
    print(f"   File size: {output_path.stat().st_size:,} bytes")


def main():
    if len(sys.argv) < 3:
        print("Usage: python regenerate_biome_png.py <input_json> <output_png> [target_resolution]")
        print("\nExample:")
        print("  python regenerate_biome_png.py \\")
        print("    etl/experimental/bepinex-adaptive-sampling/output/world_data/biomes.json \\")
        print("    /tmp/biomes_nearest_4096.png \\")
        print("    4096")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    target_resolution = int(sys.argv[3]) if len(sys.argv) > 3 else 4096

    if not json_path.exists():
        print(f"ERROR: JSON file not found: {json_path}")
        sys.exit(1)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    regenerate_png(json_path, output_path, target_resolution)


if __name__ == '__main__':
    main()
