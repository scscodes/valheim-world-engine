"""
Image Generation Service
Converts world data JSON to PNG visualizations
"""

import logging
from io import BytesIO
from typing import Tuple, Optional
import numpy as np
from PIL import Image

from ..models.world_data import BiomeMapResponse, HeightmapResponse, BIOME_COLORS

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Service for generating PNG images from world data"""
    
    def generate_biome_image(
        self, 
        biome_data: BiomeMapResponse, 
        target_resolution: Optional[int] = None
    ) -> BytesIO:
        """
        Generate a PNG image from biome map data
        
        Args:
            biome_data: Biome map data
            target_resolution: Target resolution for output image (upscales if needed)
            
        Returns:
            BytesIO buffer containing PNG image
        """
        logger.info(f"Generating biome image (resolution={biome_data.resolution})")
        
        # Convert biome map to numpy array
        biome_array = np.array(biome_data.biome_map, dtype=np.uint8)
        height, width = biome_array.shape
        
        # Create RGB image
        rgb_array = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Map biome IDs to colors
        for biome_id, color in BIOME_COLORS.items():
            mask = biome_array == biome_id
            rgb_array[mask] = color
        
        # Create PIL Image
        image = Image.fromarray(rgb_array, mode='RGB')
        
        # Upscale if requested
        if target_resolution and target_resolution != biome_data.resolution:
            logger.info(f"Upscaling from {biome_data.resolution} to {target_resolution}")
            image = image.resize(
                (target_resolution, target_resolution), 
                Image.Resampling.BICUBIC
            )
        
        # Save to buffer
        buffer = BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        
        logger.info(f"Generated biome PNG ({buffer.getbuffer().nbytes} bytes)")
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

