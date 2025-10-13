#!/usr/bin/env python3
"""
BepInEx Gen1 - Map Renderer
Generates WebP image layers from processed data using global config
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from PIL import Image, ImageDraw


logger = logging.getLogger(__name__)


@dataclass
class RenderingResult:
    """Result of rendering operation"""
    success: bool
    files_created: List[str]
    error_message: Optional[str] = None


class MapRenderer:
    """Renders map layers from processed data"""

    def __init__(
        self,
        generator_config: Dict[str, Any],
        global_configs: Dict[str, Any]
    ):
        """
        Initialize map renderer

        Args:
            generator_config: Generator-specific configuration
            global_configs: Global YAML configurations
        """
        self.generator_config = generator_config
        self.global_configs = global_configs

        # Extract relevant configs
        self.valheim_world = global_configs["valheim-world"]
        self.rendering_config = global_configs["rendering-config"]
        self.generator_rendering = generator_config.get("rendering", {})

        # Build color maps
        self._build_color_maps()

        logger.info("Map renderer initialized")

    def _build_color_maps(self) -> None:
        """Build biome color maps from global config"""
        biomes = self.valheim_world.get("biomes", {})

        self.biome_colors = {}

        for biome_name, biome_data in biomes.items():
            if biome_name == "defaults":
                continue

            biome_id = biome_data.get("id")
            color_hex = biome_data.get("hex")

            if biome_id and color_hex:
                # Convert hex to RGB tuple
                rgb = self._hex_to_rgb(color_hex)
                self.biome_colors[biome_id] = rgb

        logger.debug(f"Built color maps for {len(self.biome_colors)} biomes")

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def render(
        self,
        seed: str,
        directories: Dict[str, Path]
    ) -> RenderingResult:
        """
        Render map layers from processed data

        Args:
            seed: Original seed string
            directories: Output directory structure

        Returns:
            RenderingResult with success status and files created
        """
        logger.info(f"Rendering map layers for seed '{seed}'")

        files_created = []
        error_message = None

        try:
            # Load processed data
            biomes_data = self._load_processed_biomes(directories["processed"])
            heightmap_data = self._load_processed_heightmap(directories["processed"])

            if biomes_data is None or heightmap_data is None:
                raise ValueError("Failed to load processed data")

            # Get enabled layers from config
            enabled_layers = [
                layer for layer in self.generator_rendering.get("layers", [])
                if layer.get("enabled", True)
            ]

            # Render each layer
            for layer_config in enabled_layers:
                layer_name = layer_config.get("name")
                layer_type = layer_config.get("type")

                logger.info(f"Rendering layer: {layer_name} (type: {layer_type})")

                output_file = self._render_layer(
                    layer_name,
                    layer_type,
                    biomes_data,
                    heightmap_data,
                    directories["renders"]
                )

                if output_file:
                    files_created.append(str(output_file))

            logger.info(f"Rendering completed: {len(files_created)} files created")
            success = True

        except Exception as e:
            logger.error(f"Error during rendering: {e}")
            error_message = str(e)
            success = False

        return RenderingResult(
            success=success,
            files_created=files_created,
            error_message=error_message
        )

    def _render_layer(
        self,
        layer_name: str,
        layer_type: str,
        biomes_data: Dict[str, Any],
        heightmap_data: Dict[str, Any],
        output_dir: Path
    ) -> Optional[Path]:
        """Render a single layer"""
        try:
            if layer_type == "biomes":
                return self._render_biomes_layer(layer_name, biomes_data, output_dir)
            elif layer_type == "binary":
                return self._render_land_sea_layer(layer_name, heightmap_data, output_dir)
            elif layer_type == "gradient":
                return self._render_heightmap_layer(layer_name, heightmap_data, output_dir)
            elif layer_type == "overlay":
                return self._render_shoreline_overlay(
                    layer_name, biomes_data, heightmap_data, output_dir
                )
            else:
                logger.warning(f"Unknown layer type: {layer_type}")
                return None

        except Exception as e:
            logger.error(f"Error rendering layer {layer_name}: {e}")
            return None

    def _render_biomes_layer(
        self,
        layer_name: str,
        biomes_data: Dict[str, Any],
        output_dir: Path
    ) -> Path:
        """Render biomes layer"""
        logger.debug(f"Rendering biomes layer: {layer_name}")

        resolution = biomes_data.get("resolution", self.rendering_config["resolutions"]["default"])
        biome_grid = biomes_data.get("biomes", {})

        # Create image
        img = Image.new('RGB', (resolution, resolution), (0, 0, 0))
        pixels = img.load()

        # Fill with biome colors
        for y in range(resolution):
            row_key = str(y)
            if row_key not in biome_grid:
                continue

            for x in range(resolution):
                col_key = str(x)
                if col_key not in biome_grid[row_key]:
                    continue

                biome_id = biome_grid[row_key][col_key]
                color = self.biome_colors.get(biome_id, (0, 0, 0))
                pixels[x, y] = color

        # Save as WebP
        output_file = output_dir / f"{layer_name}.webp"
        quality = self.generator_rendering.get("quality", 85)
        img.save(output_file, "WebP", quality=quality)

        logger.debug(f"Saved biomes layer: {output_file}")
        return output_file

    def _render_land_sea_layer(
        self,
        layer_name: str,
        heightmap_data: Dict[str, Any],
        output_dir: Path
    ) -> Path:
        """Render land/sea binary layer"""
        logger.debug(f"Rendering land/sea layer: {layer_name}")

        # Get heightmap array
        heightmap_array = np.array(heightmap_data.get("data", []))
        if len(heightmap_array.shape) != 2:
            raise ValueError(f"Invalid heightmap shape: {heightmap_array.shape}")

        height, width = heightmap_array.shape
        sea_level = heightmap_data.get("sea_level", 30.0)

        # Create binary image (land=white, sea=blue)
        img = Image.new('RGB', (width, height), (0, 0, 0))
        pixels = img.load()

        land_color = (220, 220, 220)  # Light gray
        sea_color = self._hex_to_rgb(self.rendering_config.get("shoreline", {}).get("ocean_color", "#3B67A3"))

        for y in range(height):
            for x in range(width):
                if heightmap_array[y, x] >= sea_level:
                    pixels[x, y] = land_color
                else:
                    pixels[x, y] = sea_color

        # Save as WebP
        output_file = output_dir / f"{layer_name}.webp"
        quality = self.generator_rendering.get("quality", 85)
        img.save(output_file, "WebP", quality=quality)

        logger.debug(f"Saved land/sea layer: {output_file}")
        return output_file

    def _render_heightmap_layer(
        self,
        layer_name: str,
        heightmap_data: Dict[str, Any],
        output_dir: Path
    ) -> Path:
        """Render heightmap gradient layer"""
        logger.debug(f"Rendering heightmap layer: {layer_name}")

        # Get heightmap array
        heightmap_array = np.array(heightmap_data.get("data", []))
        if len(heightmap_array.shape) != 2:
            raise ValueError(f"Invalid heightmap shape: {heightmap_array.shape}")

        height, width = heightmap_array.shape

        # Normalize to 0-255 range
        min_height = np.min(heightmap_array)
        max_height = np.max(heightmap_array)
        normalized = ((heightmap_array - min_height) / (max_height - min_height) * 255).astype(np.uint8)

        # Create grayscale image
        img = Image.fromarray(normalized, mode='L')

        # Convert to RGB with color gradient (blue-green-yellow-red)
        img_rgb = self._apply_height_gradient(img)

        # Save as WebP
        output_file = output_dir / f"{layer_name}.webp"
        quality = self.generator_rendering.get("quality", 85)
        img_rgb.save(output_file, "WebP", quality=quality)

        logger.debug(f"Saved heightmap layer: {output_file}")
        return output_file

    def _apply_height_gradient(self, grayscale_img: Image.Image) -> Image.Image:
        """Apply color gradient to grayscale heightmap"""
        # Simple gradient: low=blue, mid=green, high=red
        img_array = np.array(grayscale_img)
        height, width = img_array.shape

        rgb_array = np.zeros((height, width, 3), dtype=np.uint8)

        for y in range(height):
            for x in range(width):
                value = img_array[y, x]

                if value < 85:  # Low (blue)
                    rgb_array[y, x] = [0, 0, int(value * 3)]
                elif value < 170:  # Mid (green)
                    rgb_array[y, x] = [0, int((value - 85) * 3), 0]
                else:  # High (red)
                    rgb_array[y, x] = [int((value - 170) * 3), 0, 0]

        return Image.fromarray(rgb_array, mode='RGB')

    def _render_shoreline_overlay(
        self,
        layer_name: str,
        biomes_data: Dict[str, Any],
        heightmap_data: Dict[str, Any],
        output_dir: Path
    ) -> Path:
        """Render shoreline overlay (transparent)"""
        logger.debug(f"Rendering shoreline overlay: {layer_name}")

        # Get configuration
        shoreline_config = self.rendering_config.get("shoreline", {})
        water_level = shoreline_config.get("water_level", 30.0)
        depth_threshold = shoreline_config.get("shoreline_depth_threshold", -5.0)

        # Get data
        heightmap_array = np.array(heightmap_data.get("data", []))
        resolution = biomes_data.get("resolution", self.rendering_config["resolutions"]["default"])

        # Create transparent image
        img = Image.new('RGBA', (resolution, resolution), (0, 0, 0, 0))
        pixels = img.load()

        # Detect shoreline areas (simplified - just show shallow water)
        ocean_color = self._hex_to_rgb(shoreline_config.get("ocean_color", "#3B67A3"))

        for y in range(resolution):
            for x in range(resolution):
                if y < len(heightmap_array) and x < len(heightmap_array[0]):
                    height = heightmap_array[y, x]

                    # Shoreline: underwater but not too deep
                    if height < water_level and height > (water_level + depth_threshold):
                        # Add semi-transparent overlay
                        pixels[x, y] = ocean_color + (128,)  # 50% opacity

        # Save as WebP
        output_file = output_dir / f"{layer_name}.webp"
        quality = self.generator_rendering.get("quality", 85)
        img.save(output_file, "WebP", quality=quality)

        logger.debug(f"Saved shoreline overlay: {output_file}")
        return output_file

    def _load_processed_biomes(self, processed_dir: Path) -> Optional[Dict[str, Any]]:
        """Load processed biomes data"""
        biomes_file = processed_dir / "biomes.json"

        if not biomes_file.exists():
            logger.error(f"Processed biomes file not found: {biomes_file}")
            return None

        try:
            with open(biomes_file, 'r') as f:
                data = json.load(f)
            logger.debug(f"Loaded processed biomes from {biomes_file}")
            return data
        except Exception as e:
            logger.error(f"Error loading processed biomes: {e}")
            return None

    def _load_processed_heightmap(self, processed_dir: Path) -> Optional[Dict[str, Any]]:
        """Load processed heightmap data"""
        heightmap_file = processed_dir / "heightmap.json"

        if not heightmap_file.exists():
            logger.error(f"Processed heightmap file not found: {heightmap_file}")
            return None

        try:
            with open(heightmap_file, 'r') as f:
                data = json.load(f)
            logger.debug(f"Loaded processed heightmap from {heightmap_file}")
            return data
        except Exception as e:
            logger.error(f"Error loading processed heightmap: {e}")
            return None
