"""
Image Generation Service
Converts world data JSON to PNG visualizations

Rendering Modes:
  - NEAREST: Fast, blocky upscaling (preserves exact grid)
  - SMOOTH: Voronoi-based interpolation (smooth boundaries)

Visualization Modes:
  - TERRAIN_ONLY: Show raw terrain biomes (ignores water level)
  - HEIGHT_AWARE: Apply water level (Shallows for submerged areas)
  - WATER_MASK: Debug view showing land vs water
  - HEIGHT_GRADIENT: Show elevation as grayscale
"""

import logging
from io import BytesIO
from typing import Tuple, Optional, Literal
import numpy as np
from PIL import Image, ImageDraw
from scipy.interpolate import NearestNDInterpolator
from scipy.ndimage import generic_filter

from ..models.world_data import BiomeMapResponse, HeightmapResponse, BIOME_COLORS

logger = logging.getLogger(__name__)

# Valheim water level (meters)
DEFAULT_WATER_LEVEL = 30.0

# Shallows color (light blue - between land and deep ocean)
SHALLOWS_COLOR = (120, 180, 220)  # Light blue for submerged shoreline

# Spawn marker color (bright red for visibility)
SPAWN_MARKER_COLOR = (255, 0, 0)  # Red
SPAWN_MARKER_OUTLINE = (255, 255, 255)  # White outline


class ImageGenerator:
    """Service for generating PNG images from world data"""

    def _draw_spawn_marker(self, image: Image.Image, world_radius: float) -> Image.Image:
        """
        Draw spawn location marker at world center (0, 0).

        Args:
            image: PIL Image to draw on
            world_radius: World radius in meters (for coordinate conversion)

        Returns:
            Image with spawn marker drawn
        """
        width, height = image.size

        # Spawn is at world coordinates (0, 0)
        # After 90° rotation, center maps to (width/2, height/2)
        spawn_x = width // 2
        spawn_y = height // 2

        # Calculate marker size based on image resolution (0.5% of image size, minimum 3px)
        marker_radius = max(3, int(width * 0.005))

        # Draw spawn marker
        draw = ImageDraw.Draw(image)

        # Draw white outline (larger circle)
        outline_radius = marker_radius + 2
        draw.ellipse(
            [spawn_x - outline_radius, spawn_y - outline_radius,
             spawn_x + outline_radius, spawn_y + outline_radius],
            fill=SPAWN_MARKER_OUTLINE
        )

        # Draw red center dot
        draw.ellipse(
            [spawn_x - marker_radius, spawn_y - marker_radius,
             spawn_x + marker_radius, spawn_y + marker_radius],
            fill=SPAWN_MARKER_COLOR
        )

        return image

    def generate_biome_image(
        self,
        biome_data: BiomeMapResponse,
        heightmap_data: Optional[HeightmapResponse] = None,
        target_resolution: Optional[int] = None,
        render_mode: Literal["nearest", "smooth"] = "nearest",
        visualization_mode: Literal["terrain_only", "height_aware", "water_mask", "height_gradient"] = "terrain_only",
        water_level: float = DEFAULT_WATER_LEVEL
    ) -> BytesIO:
        """
        Generate a PNG image from biome map data

        Args:
            biome_data: Biome map data
            heightmap_data: Optional heightmap for height-aware rendering
            target_resolution: Target resolution for output image (upscales if needed)
            render_mode: "nearest" for blocky/fast, "smooth" for interpolated boundaries
            visualization_mode: Visualization style (terrain_only, height_aware, water_mask, height_gradient)
            water_level: Water level threshold in meters (default 30m)

        Returns:
            BytesIO buffer containing PNG image
        """
        logger.info(f"Generating biome image (resolution={biome_data.resolution}, render={render_mode}, viz={visualization_mode}, water_level={water_level}m)")

        # Special visualization modes
        if visualization_mode == "water_mask":
            return self._generate_water_mask(biome_data, heightmap_data, water_level, target_resolution)
        elif visualization_mode == "height_gradient":
            return self._generate_height_gradient(heightmap_data, target_resolution)

        # Standard biome rendering
        if render_mode == "smooth" and target_resolution:
            return self._generate_biome_image_smooth(biome_data, heightmap_data, target_resolution, visualization_mode, water_level)
        else:
            return self._generate_biome_image_nearest(biome_data, heightmap_data, target_resolution, visualization_mode, water_level)

    def _generate_biome_image_nearest(
        self,
        biome_data: BiomeMapResponse,
        heightmap_data: Optional[HeightmapResponse] = None,
        target_resolution: Optional[int] = None,
        visualization_mode: str = "terrain_only",
        water_level: float = DEFAULT_WATER_LEVEL
    ) -> BytesIO:
        """Generate biome image using NEAREST neighbor upscaling"""
        # Convert biome map to numpy array (uint16 to support biome IDs up to 512)
        biome_array = np.array(biome_data.biome_map, dtype=np.uint16)
        height, width = biome_array.shape

        # Create RGB image
        rgb_array = np.zeros((height, width, 3), dtype=np.uint8)

        # Apply height-aware coloring if requested
        if visualization_mode == "height_aware" and heightmap_data is not None:
            height_array = np.array(heightmap_data.heightmap, dtype=np.float32)

            # Apply water level logic
            for y in range(height):
                for x in range(width):
                    biome_id = biome_array[y, x]
                    elevation = height_array[y, x]

                    if elevation < water_level:
                        # Underwater
                        if biome_id == 32:  # Already Ocean
                            rgb_array[y, x] = BIOME_COLORS[32]  # Deep ocean
                        else:
                            rgb_array[y, x] = SHALLOWS_COLOR  # Submerged shoreline
                    else:
                        # Above water - show terrain biome
                        rgb_array[y, x] = BIOME_COLORS.get(biome_id, (128, 128, 128))
        else:
            # Terrain-only mode (legacy behavior)
            for biome_id, color in BIOME_COLORS.items():
                mask = biome_array == biome_id
                rgb_array[mask] = color

        # Create PIL Image
        image = Image.fromarray(rgb_array, mode='RGB')

        # Rotate 90 degrees counter-clockwise to align with Valheim coordinate system
        # (Ashlands south, DeepNorth north)
        image = image.rotate(90, expand=True)

        # Upscale if requested
        if target_resolution and target_resolution != biome_data.resolution:
            logger.info(f"Upscaling NEAREST: {biome_data.resolution} → {target_resolution}")
            image = image.resize(
                (target_resolution, target_resolution),
                Image.Resampling.NEAREST
            )

        # Draw spawn marker at world center
        image = self._draw_spawn_marker(image, biome_data.world_radius)

        # Save to buffer
        buffer = BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)

        logger.info(f"Generated biome PNG (NEAREST, {visualization_mode}) ({buffer.getbuffer().nbytes} bytes)")
        return buffer

    def _generate_biome_image_smooth(
        self,
        biome_data: BiomeMapResponse,
        heightmap_data: Optional[HeightmapResponse] = None,
        target_resolution: int = 1024,
        visualization_mode: str = "terrain_only",
        water_level: float = DEFAULT_WATER_LEVEL
    ) -> BytesIO:
        """
        Generate biome image using Voronoi interpolation for smooth boundaries.
        Mimics the smooth biome transitions players experience in-game.

        Process:
        1. Convert grid samples to world-space point cloud
        2. Interpolate to high resolution using Voronoi tessellation
        3. Apply mode filter for edge smoothing (preserves biome integrity)
        4. Map interpolated biome IDs to colors
        """
        logger.info(f"Generating smooth biome image: {biome_data.resolution} → {target_resolution}")

        # Convert biome map to numpy array
        biome_array = np.array(biome_data.biome_map, dtype=np.uint16)
        grid_resolution = biome_data.resolution

        # Extract sample points in world space
        points = []
        biome_ids = []

        for y in range(grid_resolution):
            for x in range(grid_resolution):
                biome_id = biome_array[y, x]

                # Convert grid coordinates to world space (-10240 to +10240 meters)
                world_x = (x / grid_resolution) * biome_data.world_diameter - biome_data.world_radius
                world_z = (y / grid_resolution) * biome_data.world_diameter - biome_data.world_radius

                points.append([world_x, world_z])
                biome_ids.append(biome_id)

        logger.info(f"Extracted {len(points)} sample points from {grid_resolution}×{grid_resolution} grid")

        # Create Voronoi interpolator
        points_array = np.array(points)
        biome_ids_array = np.array(biome_ids, dtype=np.uint16)
        interpolator = NearestNDInterpolator(points_array, biome_ids_array)

        # Generate high-resolution grid in world space
        world_min = -biome_data.world_radius
        world_max = biome_data.world_radius

        xi = np.linspace(world_min, world_max, target_resolution)
        zi = np.linspace(world_min, world_max, target_resolution)
        XI, ZI = np.meshgrid(xi, zi)

        # Interpolate biome IDs to high resolution
        logger.info(f"Interpolating to {target_resolution}×{target_resolution}...")
        biome_hires = interpolator(XI, ZI).astype(np.uint16)

        # Apply mode filter for edge smoothing (3×3 window)
        # This smooths edges while preserving biome identity
        def mode_filter_func(values):
            """Local mode filter - most common biome in 3×3 window"""
            unique, counts = np.unique(values, return_counts=True)
            return unique[np.argmax(counts)]

        logger.info("Applying edge smoothing (3×3 mode filter)...")
        biome_smoothed = generic_filter(
            biome_hires,
            mode_filter_func,
            size=3,
            mode='nearest'
        ).astype(np.uint16)

        # Map biome IDs to colors
        logger.info("Mapping biomes to colors...")
        rgb_array = np.zeros((target_resolution, target_resolution, 3), dtype=np.uint8)

        for biome_id, color in BIOME_COLORS.items():
            mask = biome_smoothed == biome_id
            rgb_array[mask] = color

        # Create PIL Image
        image = Image.fromarray(rgb_array, mode='RGB')

        # Rotate 90 degrees counter-clockwise to align with Valheim coordinate system
        image = image.rotate(90, expand=True)

        # Draw spawn marker at world center
        image = self._draw_spawn_marker(image, biome_data.world_radius)

        # Save to buffer
        buffer = BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)

        logger.info(f"Generated biome PNG (SMOOTH, {visualization_mode}) ({buffer.getbuffer().nbytes} bytes)")
        return buffer

    def _generate_water_mask(
        self,
        biome_data: BiomeMapResponse,
        heightmap_data: Optional[HeightmapResponse],
        water_level: float,
        target_resolution: Optional[int] = None
    ) -> BytesIO:
        """
        Generate enhanced debug visualization showing land vs water layers.

        Color scheme:
        - Dark Blue (0, 0, 139): Deep Ocean (Ocean biome underwater)
        - Light Blue (120, 180, 220): Shallows (non-Ocean, non-Ashlands underwater)
        - Red-Orange (200, 80, 40): Ashlands Water (Ashlands biome underwater)
        - Green (0, 200, 0): Land (above water level)
        """
        if heightmap_data is None:
            raise ValueError("Heightmap data required for water mask visualization")

        logger.info(f"Generating water mask (water_level={water_level}m)")

        biome_array = np.array(biome_data.biome_map, dtype=np.uint16)
        height_array = np.array(heightmap_data.heightmap, dtype=np.float32)
        height, width = biome_array.shape

        # Create debug visualization
        rgb_array = np.zeros((height, width, 3), dtype=np.uint8)

        for y in range(height):
            for x in range(width):
                biome_id = biome_array[y, x]
                elevation = height_array[y, x]

                if elevation < water_level:
                    if biome_id == 32:  # Ocean biome
                        rgb_array[y, x] = (0, 0, 139)  # Dark blue - Deep Ocean
                    elif biome_id == 512:  # Ashlands biome
                        rgb_array[y, x] = (200, 80, 40)  # Red-orange - Ashlands Water
                    else:
                        rgb_array[y, x] = (120, 180, 220)  # Light blue - Shallows
                else:
                    rgb_array[y, x] = (0, 200, 0)  # Green - Land

        # Rotate 90 degrees counter-clockwise to fix orientation
        # This aligns with Valheim's coordinate system (Ashlands south)
        image = Image.fromarray(rgb_array, mode='RGB')
        image = image.rotate(90, expand=True)

        if target_resolution and target_resolution != biome_data.resolution:
            image = image.resize((target_resolution, target_resolution), Image.Resampling.NEAREST)

        # Draw spawn marker at world center
        image = self._draw_spawn_marker(image, biome_data.world_radius)

        buffer = BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)

        logger.info(f"Generated water mask PNG ({buffer.getbuffer().nbytes} bytes)")
        return buffer

    def _generate_height_gradient(
        self,
        heightmap_data: Optional[HeightmapResponse],
        target_resolution: Optional[int] = None
    ) -> BytesIO:
        """Generate debug visualization showing elevation as grayscale"""
        if heightmap_data is None:
            raise ValueError("Heightmap data required for height gradient visualization")

        logger.info("Generating height gradient visualization")

        height_array = np.array(heightmap_data.heightmap, dtype=np.float32)

        # Normalize to 0-255 range
        min_h = height_array.min()
        max_h = height_array.max()

        if max_h > min_h:
            normalized = ((height_array - min_h) / (max_h - min_h) * 255).astype(np.uint8)
        else:
            normalized = np.zeros_like(height_array, dtype=np.uint8)

        # Create grayscale image
        rgb_array = np.stack([normalized] * 3, axis=-1)
        image = Image.fromarray(rgb_array, mode='RGB')

        if target_resolution and target_resolution != heightmap_data.resolution:
            image = image.resize((target_resolution, target_resolution), Image.Resampling.BICUBIC)

        buffer = BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)

        logger.info(f"Generated height gradient PNG ({buffer.getbuffer().nbytes} bytes)")
        return buffer

    def generate_heightmap_image(
        self, 
        heightmap_data: HeightmapResponse,
        target_resolution: Optional[int] = None,
        colormap: str = "terrain"
    ) -> BytesIO:
        """
        Generate a PNG image from heightmap data
        
        Args:
            heightmap_data: Heightmap data
            target_resolution: Target resolution for output image
            colormap: Color scheme ('terrain', 'grayscale', 'viridis')
            
        Returns:
            BytesIO buffer containing PNG image
        """
        logger.info(f"Generating heightmap image (resolution={heightmap_data.resolution})")
        
        # Convert heightmap to numpy array
        height_array = np.array(heightmap_data.heightmap, dtype=np.float32)
        
        # Normalize to 0-255 range
        min_h = height_array.min()
        max_h = height_array.max()
        
        if max_h > min_h:
            normalized = ((height_array - min_h) / (max_h - min_h) * 255).astype(np.uint8)
        else:
            normalized = np.zeros_like(height_array, dtype=np.uint8)
        
        # Apply colormap
        if colormap == "grayscale":
            rgb_array = np.stack([normalized] * 3, axis=-1)
        elif colormap == "terrain":
            rgb_array = self._apply_terrain_colormap(normalized, min_h, max_h)
        else:
            # Default to grayscale
            rgb_array = np.stack([normalized] * 3, axis=-1)
        
        # Create PIL Image
        image = Image.fromarray(rgb_array, mode='RGB')
        
        # Upscale if requested
        if target_resolution and target_resolution != heightmap_data.resolution:
            logger.info(f"Upscaling from {heightmap_data.resolution} to {target_resolution}")
            image = image.resize(
                (target_resolution, target_resolution), 
                Image.Resampling.BICUBIC
            )
        
        # Save to buffer
        buffer = BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        
        logger.info(f"Generated heightmap PNG ({buffer.getbuffer().nbytes} bytes)")
        return buffer
    
    def generate_composite_image(
        self,
        biome_data: BiomeMapResponse,
        heightmap_data: HeightmapResponse,
        target_resolution: Optional[int] = None,
        alpha: float = 0.5
    ) -> BytesIO:
        """
        Generate a composite image with biomes and heightmap overlay
        
        Args:
            biome_data: Biome map data
            heightmap_data: Heightmap data
            target_resolution: Target resolution
            alpha: Transparency of heightmap overlay (0-1)
            
        Returns:
            BytesIO buffer containing PNG image
        """
        logger.info("Generating composite image")
        
        # Generate both images
        biome_buffer = self.generate_biome_image(biome_data, target_resolution)
        heightmap_buffer = self.generate_heightmap_image(heightmap_data, target_resolution)
        
        # Load as PIL Images
        biome_img = Image.open(biome_buffer)
        heightmap_img = Image.open(heightmap_buffer)
        
        # Blend images
        composite = Image.blend(biome_img, heightmap_img, alpha)
        
        # Save to buffer
        buffer = BytesIO()
        composite.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        
        return buffer
    
    def _apply_terrain_colormap(self, normalized: np.ndarray, min_h: float, max_h: float) -> np.ndarray:
        """Apply terrain-style colormap to normalized heightmap"""
        height, width = normalized.shape
        rgb = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Deep water: dark blue (< 30)
        mask = normalized < 30
        rgb[mask] = [20, 40, 100]
        
        # Shallow water: blue (30-60)
        mask = (normalized >= 30) & (normalized < 60)
        rgb[mask] = [52, 97, 141]
        
        # Beach/shore: tan (60-80)
        mask = (normalized >= 60) & (normalized < 80)
        rgb[mask] = [194, 178, 128]
        
        # Low ground: green (80-140)
        mask = (normalized >= 80) & (normalized < 140)
        rgb[mask] = [121, 176, 81]
        
        # Hills: dark green (140-180)
        mask = (normalized >= 140) & (normalized < 180)
        rgb[mask] = [88, 129, 59]
        
        # Mountains: gray (180-220)
        mask = (normalized >= 180) & (normalized < 220)
        rgb[mask] = [150, 150, 150]
        
        # High mountains: light gray (>= 220)
        mask = normalized >= 220
        rgb[mask] = [209, 228, 237]
        
        return rgb

