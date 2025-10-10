#!/usr/bin/env python3
"""
Generate Python constants from YAML configuration
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any

def load_yaml_config() -> Dict[str, Any]:
    """Load the YAML configuration file."""
    config_path = Path(__file__).parent.parent.parent / "data" / "valheim-world.yml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_validation_data() -> Dict[str, Any]:
    """Load validation data."""
    validation_path = Path(__file__).parent.parent.parent / "data" / "validation-data.yml"
    with open(validation_path, 'r') as f:
        return yaml.safe_load(f)

def load_rendering_config() -> Dict[str, Any]:
    """Load rendering configuration."""
    rendering_path = Path(__file__).parent.parent.parent / "data" / "rendering-config.yml"
    with open(rendering_path, 'r') as f:
        return yaml.safe_load(f)

def merge_biome_defaults(biomes: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Merge biome defaults with individual biome properties."""
    merged = {}
    for name, biome in biomes.items():
        if name == "defaults":
            continue
        
        # Start with defaults
        merged_biome = defaults.copy()
        
        # Override with biome-specific properties
        merged_biome.update(biome)
        
        merged[name] = merged_biome
    
    return merged

def generate_python_constants():
    """Generate Python constants file."""
    config = load_yaml_config()
    validation = load_validation_data()
    rendering = load_rendering_config()
    
    # Extract world constants
    world = config["world"]
    coordinates = config["coordinates"]
    height = config["height"]
    
    # Merge biome defaults
    biomes = merge_biome_defaults(config["biomes"], config["biomes"]["defaults"])
    
    # Generate Python file
    output_path = Path(__file__).parent.parent.parent.parent / "backend" / "app" / "core" / "generated_constants.py"
    
    with open(output_path, 'w') as f:
        f.write('"""\n')
        f.write('Generated Valheim Constants\n')
        f.write('==========================\n')
        f.write('DO NOT EDIT - Generated from global/data/*.yml\n')
        f.write(f'Generated: {config["metadata"]["last_updated"]}\n')
        f.write('"""\n\n')
        
        # World constants
        f.write('# World dimensions\n')
        f.write(f'WORLD_RADIUS = {world["radius"]}\n')
        f.write(f'WORLD_DIAMETER = {world["diameter"]}\n')
        f.write(f'WORLD_BOUNDS = {world["bounds"]}\n')
        f.write(f'WATER_EDGE = {world["water_edge"]}\n\n')
        
        # Coordinate system
        f.write('# Coordinate system\n')
        f.write(f'COORDINATE_ORIGIN = {coordinates["origin"]}\n')
        f.write(f'COORDINATE_UNIT = "{coordinates["unit"]}"\n')
        f.write(f'COORDINATE_AXES = {coordinates["axes"]}\n\n')
        
        # Height system
        f.write('# Height system\n')
        f.write(f'SEA_LEVEL = {height["sea_level"]}\n')
        f.write(f'HEIGHT_MULTIPLIER = {height["multiplier"]}\n')
        f.write(f'HEIGHT_RANGE = {height["range"]}\n')
        f.write(f'OCEAN_THRESHOLD = {height["ocean_threshold"]}\n')
        f.write(f'MOUNTAIN_THRESHOLD = {height["mountain_threshold"]}\n\n')
        
        # Biome constants
        f.write('# Biome system\n')
        f.write('BIOMES = {\n')
        for name, biome in biomes.items():
            f.write(f'    "{name}": {{\n')
            f.write(f'        "id": {biome["id"]},\n')
            f.write(f'        "rgb": {biome["rgb"]},\n')
            f.write(f'        "hex": "{biome["hex"]}",\n')
            f.write(f'        "height_range": {biome["height_range"]},\n')
            f.write(f'        "distance_range": {biome["distance_range"]},\n')
            f.write(f'        "noise_threshold": {biome["noise_threshold"]},\n')
            f.write(f'        "polar_offset": {biome["polar_offset"]},\n')
            if biome["fallback_distance"] is not None:
                f.write(f'        "fallback_distance": {biome["fallback_distance"]},\n')
            if biome["min_mountain_distance"] is not None:
                f.write(f'        "min_mountain_distance": {biome["min_mountain_distance"]},\n')
            f.write('    },\n')
        f.write('}\n\n')
        
        # Convenience lookups
        f.write('# Convenience lookups\n')
        f.write('BIOME_IDS = {name: data["id"] for name, data in BIOMES.items()}\n')
        f.write('BIOME_COLORS_RGB = {data["id"]: data["rgb"] for data in BIOMES.values()}\n')
        f.write('BIOME_COLORS_HEX = {data["id"]: data["hex"] for data in BIOMES.values()}\n')
        f.write('BIOME_NAMES = {data["id"]: name for name, data in BIOMES.items()}\n\n')
        
        # Validation data
        f.write('# Validation data\n')
        f.write('VALIDATION_DATA = {\n')
        f.write(f'    "coordinate_ranges": {validation["coordinate_ranges"]},\n')
        f.write(f'    "height_ranges": {validation["height_ranges"]},\n')
        f.write(f'    "biome_distribution": {validation["biome_distribution"]},\n')
        f.write(f'    "performance": {validation["performance"]},\n')
        f.write('}\n\n')
        
        # Rendering config
        f.write('# Rendering configuration\n')
        f.write('RENDERING_CONFIG = {\n')
        f.write(f'    "resolutions": {rendering["resolutions"]},\n')
        f.write(f'    "rendering": {rendering["rendering"]},\n')
        f.write(f'    "shoreline": {rendering["shoreline"]},\n')
        f.write(f'    "filters": {rendering["filters"]},\n')
        f.write(f'    "visualization": {rendering["visualization"]},\n')
        f.write('}\n')

if __name__ == "__main__":
    generate_python_constants()
    print("Python constants generated successfully!")
