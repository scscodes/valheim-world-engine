#!/usr/bin/env python3
"""
BepInEx Gen1 - Data Processor
Transforms extracted data into processed format using global config
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict


logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of data processing"""
    success: bool
    files_created: List[str]
    statistics: Dict[str, Any]
    error_message: Optional[str] = None


class DataProcessor:
    """Processes extracted world data into standard format"""

    def __init__(
        self,
        generator_config: Dict[str, Any],
        global_configs: Dict[str, Any]
    ):
        """
        Initialize data processor

        Args:
            generator_config: Generator-specific configuration
            global_configs: Global YAML configurations
        """
        self.generator_config = generator_config
        self.global_configs = global_configs

        # Extract relevant configs
        self.valheim_world = global_configs["valheim-world"]
        self.rendering_config = global_configs["rendering-config"]
        self.processing_config = generator_config.get("processing", {})

        # Build biome lookup maps from global config
        self._build_biome_maps()

        logger.info("Data processor initialized")

    def _build_biome_maps(self) -> None:
        """Build biome ID to name/color mappings from global config"""
        biomes = self.valheim_world.get("biomes", {})

        self.biome_id_to_name = {}
        self.biome_id_to_color = {}
        self.biome_name_to_id = {}

        for biome_name, biome_data in biomes.items():
            if biome_name == "defaults":
                continue

            biome_id = biome_data.get("id")
            if biome_id:
                self.biome_id_to_name[biome_id] = biome_name
                self.biome_name_to_id[biome_name] = biome_id

                # Get color (prefer hex, fallback to RGB)
                color = biome_data.get("hex") or self._rgb_to_hex(biome_data.get("rgb", [0, 0, 0]))
                self.biome_id_to_color[biome_id] = color

        logger.debug(f"Built biome maps for {len(self.biome_id_to_name)} biomes")

    def _rgb_to_hex(self, rgb: List[int]) -> str:
        """Convert RGB list to hex color"""
        return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])

    def process(
        self,
        seed: str,
        seed_hash: str,
        directories: Dict[str, Path]
    ) -> ProcessingResult:
        """
        Process extracted data into standard format

        Args:
            seed: Original seed string
            seed_hash: Hash of seed
            directories: Output directory structure

        Returns:
            ProcessingResult with success status and statistics
        """
        logger.info(f"Processing data for seed '{seed}'")

        files_created = []
        statistics = {}
        error_message = None

        try:
            # Load extracted data
            biomes_data = self._load_biomes(directories["extracted"])
            heightmap_data = self._load_heightmap(directories["extracted"])

            if biomes_data is None or heightmap_data is None:
                raise ValueError("Failed to load extracted data")

            # Process biomes
            processed_biomes = self._process_biomes(biomes_data)
            biomes_file = self._save_biomes(processed_biomes, directories["processed"])
            files_created.append(str(biomes_file))

            # Process heightmap
            processed_heightmap = self._process_heightmap(heightmap_data)
            heightmap_file = self._save_heightmap(processed_heightmap, directories["processed"])
            files_created.append(str(heightmap_file))

            # Calculate statistics
            statistics = self._calculate_statistics(
                processed_biomes,
                processed_heightmap,
                seed,
                seed_hash
            )
            stats_file = self._save_statistics(statistics, directories["processed"])
            files_created.append(str(stats_file))

            # Create metadata
            metadata = self._create_metadata(seed, seed_hash, statistics)
            metadata_file = self._save_metadata(metadata, directories["processed"])
            files_created.append(str(metadata_file))

            logger.info(f"Processing completed successfully: {len(files_created)} files created")
            success = True

        except Exception as e:
            logger.error(f"Error during processing: {e}")
            error_message = str(e)
            success = False

        return ProcessingResult(
            success=success,
            files_created=files_created,
            statistics=statistics,
            error_message=error_message
        )

    def _load_biomes(self, extracted_dir: Path) -> Optional[Dict[str, Any]]:
        """Load biomes data from extracted directory with adaptive format detection"""
        # Try multiple formats in order of preference
        formats_to_try = [
            ("JSON", extracted_dir / "biomes.json", self._load_biomes_json),
            ("PNG", extracted_dir / "biomes.png", self._load_biomes_png),
        ]
        
        for format_name, file_path, loader_func in formats_to_try:
            if file_path.exists():
                try:
                    data = loader_func(file_path)
                    if data is not None:
                        logger.info(f"✓ Loaded biomes from {format_name}")
                        return data
                except Exception as e:
                    logger.warning(f"Failed to load biomes from {format_name}: {e}")
                    continue
        
        logger.error("No valid biomes file found in any supported format")
        return None

    def _load_biomes_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load biomes from JSON format"""
        with open(file_path, 'r') as f:
            return json.load(f)

    def _load_biomes_png(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load biomes from PNG format (fallback)"""
        try:
            from PIL import Image
            img = Image.open(file_path)
            # Convert PNG to biome data structure
            # This is a simplified fallback - would need more sophisticated processing
            logger.warning("PNG biomes loaded - this is a fallback format, accuracy may be limited")
            return {
                "format_version": "1.0",
                "resolution": img.width,
                "biomes": {},  # Would need to extract biome data from PNG
                "note": "PNG fallback format - limited functionality"
            }
        except Exception as e:
            logger.error(f"Failed to load PNG biomes: {e}")
            return None

    def _load_heightmap(self, extracted_dir: Path) -> Optional[np.ndarray]:
        """Load heightmap data from extracted directory with adaptive format detection"""
        # Try multiple formats in order of preference
        formats_to_try = [
            ("NPY", extracted_dir / "heightmap.npy", self._load_heightmap_npy),
            ("JSON", extracted_dir / "heightmap.json", self._load_heightmap_json),
            ("PNG", extracted_dir / "heightmap.png", self._load_heightmap_png),
        ]
        
        for format_name, file_path, loader_func in formats_to_try:
            if file_path.exists():
                try:
                    data = loader_func(file_path)
                    if data is not None:
                        logger.info(f"✓ Loaded heightmap from {format_name}: shape={data.shape}, dtype={data.dtype}")
                        return data
                except Exception as e:
                    logger.warning(f"Failed to load heightmap from {format_name}: {e}")
                    continue
        
        logger.error("No valid heightmap file found in any supported format")
        return None

    def _load_heightmap_npy(self, file_path: Path) -> Optional[np.ndarray]:
        """Load heightmap from NPY format"""
        return np.load(file_path)

    def _load_heightmap_json(self, file_path: Path) -> Optional[np.ndarray]:
        """Load heightmap from JSON format"""
        with open(file_path, 'r') as f:
            json_data = json.load(f)
        
        # Extract height map array from JSON
        height_map = json_data.get("height_map", [])
        if not height_map:
            logger.error("No height_map data found in JSON")
            return None
        
        # Convert to numpy array
        return np.array(height_map, dtype=np.float32)

    def _load_heightmap_png(self, file_path: Path) -> Optional[np.ndarray]:
        """Load heightmap from PNG format (fallback)"""
        try:
            from PIL import Image
            img = Image.open(file_path)
            # Convert to grayscale and then to numpy array
            data = np.array(img.convert('L'), dtype=np.float32)
            logger.warning("PNG heightmap loaded - this is a fallback format, accuracy may be limited")
            return data
        except Exception as e:
            logger.error(f"Failed to load PNG heightmap: {e}")
            return None

    def _process_biomes(self, biomes_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process biomes data into standard format"""
        logger.debug("Processing biomes data")

        # Validate biome IDs if configured
        if self.processing_config.get("biomes", {}).get("validate_ids"):
            self._validate_biome_ids(biomes_data)

        # Transform to standard format
        processed = {
            "format_version": "1.0",
            "resolution": biomes_data.get("resolution", self.rendering_config["resolutions"]["default"]),
            "world_bounds": self.valheim_world["world"]["bounds"],
            "biomes": biomes_data.get("biomes", {}),
            "biome_metadata": {
                "id_to_name": self.biome_id_to_name,
                "id_to_color": self.biome_id_to_color,
            }
        }

        return processed

    def _process_heightmap(self, heightmap_data: np.ndarray) -> Dict[str, Any]:
        """Process heightmap data into standard format"""
        logger.debug("Processing heightmap data")

        # Normalize if configured
        if self.processing_config.get("heightmap", {}).get("normalize"):
            heightmap_data = self._normalize_heightmap(heightmap_data)

        # Calculate statistics
        height_stats = {
            "min": float(np.min(heightmap_data)),
            "max": float(np.max(heightmap_data)),
            "mean": float(np.mean(heightmap_data)),
            "median": float(np.median(heightmap_data)),
            "std": float(np.std(heightmap_data)),
        }

        # Get sea level from global config
        sea_level = self.valheim_world["height"]["sea_level"]

        processed = {
            "format_version": "1.0",
            "shape": list(heightmap_data.shape),
            "dtype": str(heightmap_data.dtype),
            "sea_level": sea_level,
            "height_multiplier": self.valheim_world["height"]["multiplier"],
            "statistics": height_stats,
            "data": heightmap_data.tolist()  # Convert to list for JSON
        }

        return processed

    def _normalize_heightmap(self, heightmap: np.ndarray) -> np.ndarray:
        """Normalize heightmap values"""
        # For now, just return as-is
        # Could add normalization logic here if needed
        return heightmap

    def _validate_biome_ids(self, biomes_data: Dict[str, Any]) -> None:
        """Validate that biome IDs match global config"""
        biome_grid = biomes_data.get("biomes", {})

        # Check if any unexpected biome IDs appear
        found_ids = set()
        for row in biome_grid.values():
            for biome_id in row.values():
                found_ids.add(biome_id)

        unknown_ids = found_ids - set(self.biome_id_to_name.keys())

        if unknown_ids:
            logger.warning(f"Found unknown biome IDs: {unknown_ids}")
        else:
            logger.debug("All biome IDs validated successfully")

    def _calculate_statistics(
        self,
        biomes: Dict[str, Any],
        heightmap: Dict[str, Any],
        seed: str,
        seed_hash: str
    ) -> Dict[str, Any]:
        """Calculate world statistics"""
        logger.debug("Calculating world statistics")

        # Calculate biome distribution
        biome_distribution = self._calculate_biome_distribution(biomes)

        # Get height statistics
        height_stats = heightmap.get("statistics", {})

        # Build statistics object
        statistics = {
            "seed": seed,
            "seed_hash": seed_hash,
            "resolution": biomes.get("resolution", self.rendering_config["resolutions"]["default"]),
            "world_bounds": self.valheim_world["world"]["bounds"],
            "biome_distribution": biome_distribution,
            "height_statistics": height_stats,
            "sea_level": heightmap.get("sea_level"),
        }

        return statistics

    def _calculate_biome_distribution(self, biomes: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate biome distribution percentages"""
        # Try different possible keys for biome data
        biome_grid = biomes.get("biomes", {}) or biomes.get("biome_map", [])

        # Count biome occurrences
        biome_counts = {}
        total_cells = 0

        # Handle both dict and list formats for biome grid
        if isinstance(biome_grid, dict):
            # Dict format: {"0": {"0": biome_id, "1": biome_id, ...}, "1": {...}}
            for row_key, row_data in biome_grid.items():
                if isinstance(row_data, dict):
                    for col_key, biome_id in row_data.items():
                        biome_counts[biome_id] = biome_counts.get(biome_id, 0) + 1
                        total_cells += 1
                elif isinstance(row_data, list):
                    # List format: [biome_id, biome_id, ...]
                    for biome_id in row_data:
                        biome_counts[biome_id] = biome_counts.get(biome_id, 0) + 1
                        total_cells += 1
        elif isinstance(biome_grid, list):
            # List format: [[biome_id, biome_id, ...], [biome_id, biome_id, ...], ...]
            for row in biome_grid:
                if isinstance(row, list):
                    for biome_id in row:
                        biome_counts[biome_id] = biome_counts.get(biome_id, 0) + 1
                        total_cells += 1

        logger.debug(f"Calculated biome distribution: {len(biome_counts)} unique biomes, {total_cells} total cells")

        # Calculate percentages
        biome_distribution = {}

        for biome_id, count in biome_counts.items():
            biome_name = self.biome_id_to_name.get(biome_id, f"Unknown_{biome_id}")
            percentage = (count / total_cells) * 100 if total_cells > 0 else 0

            biome_distribution[biome_name] = {
                "id": biome_id,
                "count": count,
                "percentage": round(percentage, 2),
                "color": self.biome_id_to_color.get(biome_id, "#000000")
            }

        return biome_distribution

    def _create_metadata(
        self,
        seed: str,
        seed_hash: str,
        statistics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create metadata file"""
        from datetime import datetime

        metadata = {
            "generator": {
                "name": "bepinex-gen1",
                "version": self.generator_config.get("metadata", {}).get("version", "0.1.0"),
                "status": "experimental"
            },
            "seed": {
                "original": seed,
                "hash": seed_hash,
            },
            "world": {
                "radius": self.valheim_world["world"]["radius"],
                "diameter": self.valheim_world["world"]["diameter"],
                "bounds": self.valheim_world["world"]["bounds"],
            },
            "generated_at": datetime.utcnow().isoformat(),
            "statistics": statistics,
        }

        return metadata

    def _save_biomes(self, data: Dict[str, Any], output_dir: Path) -> Path:
        """Save processed biomes to JSON"""
        output_file = output_dir / "biomes.json"

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved biomes: {output_file}")
        return output_file

    def _save_heightmap(self, data: Dict[str, Any], output_dir: Path) -> Path:
        """Save processed heightmap to JSON"""
        output_file = output_dir / "heightmap.json"

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved heightmap: {output_file}")
        return output_file

    def _save_statistics(self, data: Dict[str, Any], output_dir: Path) -> Path:
        """Save statistics to JSON"""
        output_file = output_dir / "statistics.json"

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved statistics: {output_file}")
        return output_file

    def _save_metadata(self, data: Dict[str, Any], output_dir: Path) -> Path:
        """Save metadata to JSON"""
        output_file = output_dir / "metadata.json"

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved metadata: {output_file}")
        return output_file
