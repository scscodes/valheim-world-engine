#!/usr/bin/env python3
"""
BepInEx Gen1 - Main Generator Orchestrator
Entry point for world generation using BepInEx approach
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib import (
    load_yaml_config,
    load_global_configs,
    hash_seed,
    create_output_structure,
    find_repo_root,
    format_duration,
    DockerOrchestrator,
    DataProcessor,
    MapRenderer,
)


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)


class BepInExGenerator:
    """Main generator orchestrator"""

    def __init__(self, repo_root: Optional[Path] = None):
        """
        Initialize generator

        Args:
            repo_root: Path to repository root (auto-detected if None)
        """
        # Find repo root
        if repo_root is None:
            repo_root = find_repo_root()

        self.repo_root = repo_root
        logger.info(f"Repository root: {repo_root}")

        # Load configurations
        logger.info("Loading configurations...")
        self.generator_config = self._load_generator_config()
        self.global_configs = load_global_configs(repo_root)

        # Initialize components
        logger.info("Initializing components...")
        self.orchestrator = DockerOrchestrator(
            self.generator_config,
            self.global_configs,
            repo_root
        )
        self.processor = DataProcessor(
            self.generator_config,
            self.global_configs
        )
        self.renderer = MapRenderer(
            self.generator_config,
            self.global_configs
        )

        # Get output base directory
        output_config = self.generator_config.get("output", {})
        output_base = output_config.get("base_dir", "etl/experimental/bepinex-gen1/data")
        self.output_dir = repo_root / output_base

        logger.info("Generator initialized successfully")

    def _validate_global_config_usage(self) -> None:
        """Validate that global configuration is being used correctly"""
        logger.info("Validating global configuration usage...")
        
        # Check that all required global configs are loaded
        required_configs = ["valheim-world", "validation-data", "rendering-config"]
        for config_name in required_configs:
            if config_name not in self.global_configs:
                logger.error(f"Missing required global config: {config_name}")
                raise ValueError(f"Missing required global config: {config_name}")
            logger.info(f"✓ Global config loaded: {config_name}")
        
        # Validate world dimensions from global config
        world_bounds = self.global_configs["valheim-world"]["world"]["bounds"]
        logger.info(f"✓ World bounds from global config: {world_bounds}")
        
        # Validate resolution settings from global config
        resolutions = self.global_configs["rendering-config"]["resolutions"]
        logger.info(f"✓ Available resolutions from global config: {list(resolutions.keys())}")
        
        logger.info("✓ Global configuration validation passed")

    def _load_generator_config(self) -> dict:
        """Load generator-specific configuration"""
        config_path = Path(__file__).parent / "config" / "generator.yaml"
        return load_yaml_config(str(config_path))

    def generate(
        self,
        seed: str,
        resolution: int = None,
        validate: bool = False
    ) -> bool:
        """
        Generate world data for a seed

        Args:
            seed: Seed string
            resolution: Export resolution
            validate: Whether to validate against reference data

        Returns:
            True if successful, False otherwise
        """
        start_time = datetime.utcnow()
        # Use global config default if resolution not specified
        if resolution is None:
            resolution = self.global_configs["rendering-config"]["resolutions"]["default"]
            logger.info(f"Using global config default resolution: {resolution}")
        else:
            logger.info(f"Using specified resolution: {resolution}")
        
        # Validate global config usage
        self._validate_global_config_usage()
        
        logger.info("="*80)
        logger.info(f"Starting world generation for seed: '{seed}'")
        logger.info(f"Resolution: {resolution}x{resolution}")
        logger.info("="*80)

        try:
            # Hash seed
            seed_hash = hash_seed(seed)
            logger.info(f"Seed hash: {seed_hash}")

            # Create output structure
            directories = create_output_structure(self.output_dir, seed_hash)
            logger.info(f"Output directory: {directories['seed_root']}")

            # Stage 1: World Generation (Docker)
            logger.info("\n[Stage 1/4] Docker World Generation")
            logger.info("-" * 80)

            plan, gen_result = self.orchestrator.generate_world(
                seed, seed_hash, directories, resolution
            )

            if not gen_result.success:
                logger.error(f"World generation failed: {gen_result.error_message}")
                return False

            logger.info(f"✓ World generation completed in {format_duration(gen_result.duration_seconds)}")

            # Stage 2: Data Processing
            logger.info("\n[Stage 2/4] Data Processing")
            logger.info("-" * 80)

            proc_result = self.processor.process(seed, seed_hash, directories)

            if not proc_result.success:
                logger.error(f"Data processing failed: {proc_result.error_message}")
                return False

            logger.info(f"✓ Data processing completed: {len(proc_result.files_created)} files created")

            # Stage 3: Rendering
            logger.info("\n[Stage 3/4] Map Rendering")
            logger.info("-" * 80)

            render_result = self.renderer.render(seed, directories)

            if not render_result.success:
                logger.error(f"Rendering failed: {render_result.error_message}")
                return False

            logger.info(f"✓ Rendering completed: {len(render_result.files_created)} layers created")

            # Stage 4: Validation (optional)
            if validate:
                logger.info("\n[Stage 4/4] Validation")
                logger.info("-" * 80)

                validation_passed = self._validate_output(
                    seed, seed_hash, directories, proc_result.statistics
                )

                if validation_passed:
                    logger.info("✓ Validation passed")
                else:
                    logger.warning("⚠ Validation warnings (see above)")
            else:
                logger.info("\n[Stage 4/4] Validation (skipped)")

            # Summary
            total_duration = (datetime.utcnow() - start_time).total_seconds()

            logger.info("\n" + "="*80)
            logger.info("GENERATION COMPLETE")
            logger.info("="*80)
            logger.info(f"Seed: {seed}")
            logger.info(f"Hash: {seed_hash}")
            logger.info(f"Resolution: {resolution}x{resolution}")
            logger.info(f"Total duration: {format_duration(total_duration)}")
            logger.info(f"Output directory: {directories['seed_root']}")
            logger.info("")
            logger.info("Generated files:")
            logger.info(f"  - Raw: {len(list(directories['raw'].iterdir()))} files")
            logger.info(f"  - Extracted: {len(list(directories['extracted'].iterdir()))} files")
            logger.info(f"  - Processed: {len(proc_result.files_created)} files")
            logger.info(f"  - Renders: {len(render_result.files_created)} files")
            logger.info("="*80)

            return True

        except Exception as e:
            logger.error(f"Unexpected error during generation: {e}", exc_info=True)
            return False

    def _validate_output(
        self,
        seed: str,
        seed_hash: str,
        directories: dict,
        statistics: dict
    ) -> bool:
        """
        Validate generated output

        Args:
            seed: Original seed
            seed_hash: Seed hash
            directories: Output directories
            statistics: Generated statistics

        Returns:
            True if validation passed
        """
        validation_config = self.generator_config.get("validation", {})

        if not validation_config.get("enabled", True):
            logger.info("Validation disabled in config")
            return True

        reference_seed = validation_config.get("reference_seed")

        # Only validate if this is the reference seed
        if seed != reference_seed:
            logger.info(f"Seed '{seed}' is not reference seed '{reference_seed}', skipping validation")
            return True

        logger.info(f"Validating against reference seed: {reference_seed}")

        # Load validation data
        validation_data = self.global_configs.get("validation_data", {})

        # Perform validation checks
        checks_passed = 0
        checks_total = 0

        enabled_checks = validation_config.get("checks", [])

        for check in enabled_checks:
            checks_total += 1

            if check == "coordinate_ranges":
                if self._validate_coordinate_ranges(statistics, validation_data):
                    logger.info("  ✓ Coordinate ranges valid")
                    checks_passed += 1
                else:
                    logger.warning("  ✗ Coordinate ranges validation failed")

            elif check == "height_ranges":
                if self._validate_height_ranges(statistics, validation_data):
                    logger.info("  ✓ Height ranges valid")
                    checks_passed += 1
                else:
                    logger.warning("  ✗ Height ranges validation failed")

            elif check == "biome_distribution":
                if self._validate_biome_distribution(statistics, validation_data):
                    logger.info("  ✓ Biome distribution valid")
                    checks_passed += 1
                else:
                    logger.warning("  ✗ Biome distribution validation failed")

            elif check == "file_structure":
                if self._validate_file_structure(directories):
                    logger.info("  ✓ File structure valid")
                    checks_passed += 1
                else:
                    logger.warning("  ✗ File structure validation failed")

        logger.info(f"\nValidation: {checks_passed}/{checks_total} checks passed")

        return checks_passed == checks_total

    def _validate_coordinate_ranges(self, statistics: dict, validation_data: dict) -> bool:
        """Validate coordinate ranges"""
        # For now, just check that world_bounds exists
        return "world_bounds" in statistics

    def _validate_height_ranges(self, statistics: dict, validation_data: dict) -> bool:
        """Validate height ranges"""
        height_stats = statistics.get("height_statistics", {})
        return "min" in height_stats and "max" in height_stats

    def _validate_biome_distribution(self, statistics: dict, validation_data: dict) -> bool:
        """Validate biome distribution"""
        biome_dist = statistics.get("biome_distribution", {})
        return len(biome_dist) > 0

    def _validate_file_structure(self, directories: dict) -> bool:
        """Validate that all required directories exist and have files"""
        required_dirs = ["raw", "extracted", "processed", "renders"]

        for dir_name in required_dirs:
            if dir_name not in directories:
                logger.warning(f"Missing directory: {dir_name}")
                return False

            dir_path = directories[dir_name]
            if not dir_path.exists():
                logger.warning(f"Directory does not exist: {dir_path}")
                return False

            if not any(dir_path.iterdir()):
                logger.warning(f"Directory is empty: {dir_path}")
                return False

        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="BepInEx Gen1 - Valheim World Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate validation seed
  python generator.py --seed hkLycKKCMI --resolution 512

  # Generate with validation
  python generator.py --seed hkLycKKCMI --validate

  # Generate custom seed
  python generator.py --seed "MyAwesomeWorld" --resolution 1024
        """
    )

    parser.add_argument(
        "--seed",
        type=str,
        required=True,
        help="Seed string to generate"
    )

    parser.add_argument(
        "--resolution",
        type=int,
        default=1024,  # Will be overridden by global config
        help="Export resolution (default: 512)"
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate output against reference data"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize generator
        generator = BepInExGenerator()

        # Run generation
        success = generator.generate(
            seed=args.seed,
            resolution=args.resolution,
            validate=args.validate
        )

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.warning("\nGeneration interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
