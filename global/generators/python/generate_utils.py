#!/usr/bin/env python3
"""
Generate Python utility functions from YAML configuration
"""

import yaml
from pathlib import Path
from typing import Dict, Any

def load_yaml_config() -> Dict[str, Any]:
    """Load the YAML configuration file."""
    config_path = Path(__file__).parent.parent.parent / "data" / "valheim-world.yml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def generate_python_utils():
    """Generate Python utility functions file."""
    config = load_yaml_config()
    
    # Extract constants
    world = config["world"]
    coordinates = config["coordinates"]
    height = config["height"]
    biomes = config["biomes"]
    
    # Generate Python file
    output_path = Path(__file__).parent.parent.parent.parent / "backend" / "app" / "core" / "generated_utils.py"
    
    with open(output_path, 'w') as f:
        f.write('"""\n')
        f.write('Generated Valheim Utility Functions\n')
        f.write('==================================\n')
        f.write('DO NOT EDIT - Generated from global/data/*.yml\n')
        f.write(f'Generated: {config["metadata"]["last_updated"]}\n')
        f.write('"""\n\n')
        
        f.write('import math\n')
        f.write('from typing import Tuple, Optional, Dict, Any\n\n')
        
        # Coordinate utilities
        f.write('def world_to_pixel(world_x: float, world_z: float, resolution: int) -> Tuple[int, int]:\n')
        f.write('    """Convert world coordinates to pixel coordinates."""\n')
        f.write(f'    world_radius = {world["radius"]}\n')
        f.write('    pixel_x = int((world_x + world_radius) * resolution / (world_radius * 2))\n')
        f.write('    pixel_z = int((world_z + world_radius) * resolution / (world_radius * 2))\n')
        f.write('    return pixel_x, pixel_z\n\n')
        
        f.write('def pixel_to_world(pixel_x: int, pixel_z: int, resolution: int) -> Tuple[float, float]:\n')
        f.write('    """Convert pixel coordinates to world coordinates."""\n')
        f.write(f'    world_radius = {world["radius"]}\n')
        f.write('    world_x = (pixel_x * world_radius * 2 / resolution) - world_radius\n')
        f.write('    world_z = (pixel_z * world_radius * 2 / resolution) - world_radius\n')
        f.write('    return world_x, world_z\n\n')
        
        f.write('def is_within_world_bounds(x: float, z: float) -> bool:\n')
        f.write('    """Check if coordinates are within world bounds."""\n')
        f.write(f'    world_radius = {world["radius"]}\n')
        f.write('    return abs(x) <= world_radius and abs(z) <= world_radius\n\n')
        
        f.write('def distance_from_center(x: float, z: float) -> float:\n')
        f.write('    """Calculate distance from world center."""\n')
        f.write('    return math.sqrt(x**2 + z**2)\n\n')
        
        # Biome utilities
        f.write('def get_biome_name(biome_id: int) -> str:\n')
        f.write('    """Get biome name from ID."""\n')
        f.write('    from .generated_constants import BIOME_NAMES\n')
        f.write('    return BIOME_NAMES.get(biome_id, f"Unknown({biome_id})")\n\n')
        
        f.write('def get_biome_color_rgb(biome_id: int) -> Tuple[int, int, int]:\n')
        f.write('    """Get biome color as RGB tuple."""\n')
        f.write('    from .generated_constants import BIOME_COLORS_RGB\n')
        f.write('    return BIOME_COLORS_RGB.get(biome_id, (255, 0, 255))  # Magenta for unknown\n\n')
        
        f.write('def get_biome_color_hex(biome_id: int) -> str:\n')
        f.write('    """Get biome color as hex string."""\n')
        f.write('    from .generated_constants import BIOME_COLORS_HEX\n')
        f.write('    return BIOME_COLORS_HEX.get(biome_id, "#FF00FF")  # Magenta for unknown\n\n')
        
        f.write('def is_valid_biome_id(biome_id: int) -> bool:\n')
        f.write('    """Check if biome ID is valid (power of 2)."""\n')
        f.write('    return biome_id != 0 and (biome_id & (biome_id - 1)) == 0\n\n')
        
        f.write('def get_all_biome_ids() -> list[int]:\n')
        f.write('    """Get list of all valid biome IDs."""\n')
        f.write('    from .generated_constants import BIOME_IDS\n')
        f.write('    return list(BIOME_IDS.values())\n\n')
        
        # Height utilities
        f.write('def normalize_height(height_meters: float) -> float:\n')
        f.write('    """Convert height in meters to normalized baseHeight."""\n')
        f.write(f'    return height_meters / {height["multiplier"]}\n\n')
        
        f.write('def baseheight_to_meters(baseheight: float) -> float:\n')
        f.write('    """Convert normalized baseHeight to meters."""\n')
        f.write(f'    return baseheight * {height["multiplier"]}\n\n')
        
        f.write('def is_underwater(height: float) -> bool:\n')
        f.write('    """Check if height is underwater."""\n')
        f.write(f'    return height < {height["sea_level"]}\n\n')
        
        f.write('def is_mountain_height(height: float) -> bool:\n')
        f.write('    """Check if height qualifies as mountain."""\n')
        f.write(f'    return height >= {height["mountain_threshold"] * height["multiplier"]}\n\n')

if __name__ == "__main__":
    generate_python_utils()
    print("Python utilities generated successfully!")
