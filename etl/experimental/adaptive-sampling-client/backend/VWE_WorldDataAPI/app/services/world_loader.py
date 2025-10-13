"""
World Data Loader Service
Loads and processes world data from BepInEx adaptive sampling output
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

from ..models.world_data import Biome, BiomeMapResponse, HeightmapResponse, BiomeMapMetadata, HeightmapMetadata, WorldDataInfo

logger = logging.getLogger(__name__)


class WorldDataLoader:
    """Service for loading world data from file system"""
    
    def __init__(self, data_root: Path):
        """
        Initialize loader with data root directory
        
        Args:
            data_root: Root directory containing world data (e.g., ../bepinex-adaptive-sampling/output/world_data/)
        """
        self.data_root = Path(data_root)
        if not self.data_root.exists():
            logger.warning(f"Data root does not exist: {self.data_root}")
            logger.info(f"To generate data: cd {self.data_root.parent.parent} && python tests/validate_performance.py --seed TestSeed")
        else:
            logger.info(f"Data root found with {len(list(self.data_root.glob('*.json')))} JSON files")
    
    def list_available_worlds(self) -> list[WorldDataInfo]:
        """List all available world seeds with data"""
        worlds = []
        
        # For now, check the default output location
        # In future, could scan multiple seed directories
        if (self.data_root / "biomes.json").exists():
            worlds.append(self.get_world_info("default"))
        
        return worlds
    
    def get_world_info(self, seed: str) -> WorldDataInfo:
        """Get information about a world seed"""
        biomes_path = self.data_root / "biomes.json"
        heightmap_path = self.data_root / "heightmap.json"
        structures_path = self.data_root / "structures.json"
        
        info = WorldDataInfo(
            seed=seed,
            has_biomes=biomes_path.exists(),
            has_heightmap=heightmap_path.exists(),
            has_structures=structures_path.exists(),
        )
        
        # Get file sizes
        if info.has_biomes:
            info.file_sizes["biomes"] = biomes_path.stat().st_size
        if info.has_heightmap:
            info.file_sizes["heightmap"] = heightmap_path.stat().st_size
        if info.has_structures:
            info.file_sizes["structures"] = structures_path.stat().st_size
        
        # Try to get resolution from biomes file
        if info.has_biomes:
            try:
                with open(biomes_path) as f:
                    data = json.load(f)
                    info.resolution = data.get("resolution")
            except Exception as e:
                logger.error(f"Error reading biomes file: {e}")
        
        return info
    
    def load_biome_data(self, seed: str = "default") -> BiomeMapResponse:
        """
        Load biome map data for a seed
        
        Args:
            seed: World seed name
            
        Returns:
            BiomeMapResponse with biome data
            
        Raises:
            FileNotFoundError: If biome data doesn't exist
            ValueError: If data format is invalid
        """
        biomes_path = self.data_root / "biomes.json"
        
        if not biomes_path.exists():
            raise FileNotFoundError(f"Biome data not found: {biomes_path}")
        
        logger.info(f"Loading biome data from {biomes_path}")
        
        try:
            with open(biomes_path) as f:
                data = json.load(f)
            
            # Validate required fields
            if "resolution" not in data:
                raise ValueError("Missing 'resolution' field")
            if "biome_map" not in data:
                raise ValueError("Missing 'biome_map' field")
            
            # Calculate metadata
            resolution = data["resolution"]
            world_diameter = data.get("world_diameter", 20000.0)
            sample_spacing = world_diameter / resolution
            
            # Count biomes
            biome_counts = self._count_biomes(data["biome_map"])
            
            metadata = BiomeMapMetadata(
                sample_spacing_meters=sample_spacing,
                biome_counts=biome_counts,
                generation_time=None  # Could parse from logs
            )
            
            return BiomeMapResponse(
                resolution=data["resolution"],
                world_radius=data.get("world_radius", 10000.0),
                world_diameter=data.get("world_diameter", 20000.0),
                biome_map=data["biome_map"],
                metadata=metadata
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in biome data: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            logger.error(f"Error loading biome data: {e}")
            raise
    
    def load_heightmap_data(self, seed: str = "default") -> HeightmapResponse:
        """
        Load heightmap data for a seed
        
        Args:
            seed: World seed name
            
        Returns:
            HeightmapResponse with height data
        """
        heightmap_path = self.data_root / "heightmap.json"
        
        if not heightmap_path.exists():
            raise FileNotFoundError(f"Heightmap data not found: {heightmap_path}")
        
        logger.info(f"Loading heightmap data from {heightmap_path}")
        
        try:
            with open(heightmap_path) as f:
                data = json.load(f)
            
            # Validate required fields
            if "resolution" not in data:
                raise ValueError("Missing 'resolution' field")
            
            # Handle both field names (height_map from BepInEx, heightmap for compatibility)
            if "heightmap" not in data and "height_map" not in data:
                raise ValueError("Missing 'heightmap' or 'height_map' field")
            
            # Normalize field name
            if "height_map" in data and "heightmap" not in data:
                data["heightmap"] = data["height_map"]
            
            # Calculate metadata
            resolution = data["resolution"]
            world_diameter = data.get("world_diameter", 20000.0)
            sample_spacing = world_diameter / resolution
            
            heights = [h for row in data["heightmap"] for h in row]
            min_height = min(heights) if heights else 0.0
            max_height = max(heights) if heights else 0.0
            
            metadata = HeightmapMetadata(
                min_height=min_height,
                max_height=max_height,
                sample_spacing_meters=sample_spacing
            )
            
            return HeightmapResponse(
                resolution=data["resolution"],
                world_radius=data.get("world_radius", 10000.0),
                world_diameter=data.get("world_diameter", 20000.0),
                heightmap=data["heightmap"],
                metadata=metadata
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in heightmap data: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            logger.error(f"Error loading heightmap data: {e}")
            raise
    
    def _count_biomes(self, biome_map: list[list[int]]) -> Dict[str, int]:
        """Count occurrences of each biome type"""
        counts = {}
        for row in biome_map:
            for biome_id in row:
                biome_name = self._get_biome_name(biome_id)
                counts[biome_name] = counts.get(biome_name, 0) + 1
        return counts
    
    def _get_biome_name(self, biome_id: int) -> str:
        """Get biome name from ID using canonical Biome enum"""
        # Map Biome enum values to readable names
        # Using Biome enum ensures consistency with model definitions
        biome_names = {
            Biome.NONE: "None",
            Biome.MEADOWS: "Meadows",
            Biome.BLACK_FOREST: "BlackForest",
            Biome.SWAMP: "Swamp",
            Biome.MOUNTAIN: "Mountain",
            Biome.PLAINS: "Plains",
            Biome.OCEAN: "Ocean",
            Biome.MISTLANDS: "Mistlands",
            Biome.DEEP_NORTH: "DeepNorth",
            Biome.ASHLANDS: "Ashlands"
        }
        return biome_names.get(biome_id, f"Unknown_{biome_id}")

