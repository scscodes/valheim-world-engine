#!/usr/bin/env python3
"""
Orchestrator for Warm Engine Pool Strategy

This module provides a high-level interface for world generation using
the warm engine pool approach, integrating with the VWE ETL pipeline.
"""

import sys
import json
import time
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

from warm_engine_pool_manager import WarmEnginePoolManager, EngineState


class WarmPoolOrchestrator:
    """
    Orchestrator for warm engine pool world generation.

    Provides a simple interface for generating worlds using pre-initialized
    Valheim servers, with automatic data management and ETL integration.
    """

    def __init__(self, data_root: Path = None):
        """
        Initialize the orchestrator.

        Args:
            data_root: Root directory for data storage (default: ./data)
        """
        self.logger = logging.getLogger(__name__)

        # Setup data directory
        if data_root is None:
            data_root = Path(__file__).parent / "data"
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)

        # Initialize warm engine pool
        self.pool_manager = WarmEnginePoolManager()

        self.logger.info(f"Orchestrator initialized with data root: {self.data_root}")

    def generate_world(self, seed: str, force: bool = False) -> Dict[str, Any]:
        """
        Generate a world map from a seed string.

        Args:
            seed: The world seed string
            force: Force regeneration even if cached

        Returns:
            Dictionary with generation results and file paths
        """
        # Compute seed hash for file naming
        seed_hash = self._compute_seed_hash(seed)
        job_id = f"job-{seed_hash[:8]}-{int(time.time())}"

        self.logger.info(f"Generating world for seed: {seed} (hash: {seed_hash})")

        # Setup data directories
        seed_dir = self.data_root / "seeds" / seed_hash
        raw_dir = seed_dir / "raw"
        extracted_dir = seed_dir / "extracted"
        processed_dir = seed_dir / "processed"
        renders_dir = seed_dir / "renders"

        for dir_path in [raw_dir, extracted_dir, processed_dir, renders_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Check if already generated
        if not force and self._is_world_cached(seed_hash):
            self.logger.info(f"World {seed} already cached, skipping generation")
            return {
                "success": True,
                "cached": True,
                "seed": seed,
                "seed_hash": seed_hash,
                "data_dir": str(seed_dir)
            }

        try:
            # Generate world using warm engine pool
            self.logger.info(f"Requesting world generation from warm engine pool...")
            result = self.pool_manager.generate_world(
                seed=seed,
                seed_hash=seed_hash,
                job_id=job_id,
                data_dir=self.data_root  # Pass data root for volume mounting
            )

            if not result["success"]:
                raise RuntimeError(f"World generation failed: {result}")

            # Data is already extracted to the mounted volume
            self.logger.info(f"✓ World files generated")
            self.logger.info(f"✓ Data exported via BepInEx")

            # Organize files into ETL structure
            self._organize_generated_files(seed, seed_hash, seed_dir)

            self.logger.info(f"World generation complete in {result['total_time']:.1f}s")

            return {
                "success": True,
                "cached": False,
                "seed": seed,
                "seed_hash": seed_hash,
                "job_id": job_id,
                "engine_id": result["engine_id"],
                "restart_time": result.get("restart_time", 0),
                "generation_time": result.get("generation_time", 0),
                "total_time": result["total_time"],
                "data_dir": str(seed_dir),
                "raw_dir": str(raw_dir),
                "extracted_dir": str(extracted_dir),
                "processed_dir": str(processed_dir),
                "renders_dir": str(renders_dir)
            }

        except Exception as e:
            self.logger.error(f"World generation failed for {seed}: {e}")
            return {
                "success": False,
                "error": str(e),
                "seed": seed,
                "seed_hash": seed_hash
            }

    def _organize_generated_files(self, seed: str, seed_hash: str, seed_dir: Path) -> None:
        """
        Organize generated files into ETL structure.

        Files are generated in:
        - seeds/{hash}/worlds_local/ - Valheim world files (.db, .fwl)
        - seeds/{hash}/world_data/ - BepInEx exported data (.json)

        Need to move to:
        - seeds/{hash}/raw/ - World files
        - seeds/{hash}/extracted/ - Exported data
        """
        import shutil

        worlds_local = seed_dir / "worlds_local"
        world_data = seed_dir / "world_data"
        raw_dir = seed_dir / "raw"
        extracted_dir = seed_dir / "extracted"

        # Move world files to raw/
        if worlds_local.exists():
            for file in worlds_local.glob("*"):
                if file.is_file():
                    dest = raw_dir / file.name
                    shutil.move(str(file), str(dest))
                    self.logger.debug(f"Moved {file.name} to raw/")

        # Move exported data to extracted/
        if world_data.exists():
            for file in world_data.glob("*"):
                if file.is_file():
                    dest = extracted_dir / file.name
                    shutil.move(str(file), str(dest))
                    self.logger.debug(f"Moved {file.name} to extracted/")

        # Clean up empty directories
        if worlds_local.exists() and not any(worlds_local.iterdir()):
            worlds_local.rmdir()
        if world_data.exists() and not any(world_data.iterdir()):
            world_data.rmdir()

    def _compute_seed_hash(self, seed: str) -> str:
        """Compute deterministic hash for a seed"""
        return hashlib.sha256(seed.encode('utf-8')).hexdigest()

    def _is_world_cached(self, seed_hash: str) -> bool:
        """Check if a world has already been generated"""
        seed_dir = self.data_root / "seeds" / seed_hash
        raw_dir = seed_dir / "raw"
        extracted_dir = seed_dir / "extracted"

        # Check for world database file
        if not raw_dir.exists():
            return False

        db_files = list(raw_dir.glob("*.db"))
        if not db_files:
            return False

        # Check for extracted data
        if not extracted_dir.exists():
            return False

        json_files = list(extracted_dir.glob("*.json"))
        if not json_files:
            return False

        return True

    def get_pool_status(self) -> Dict[str, Any]:
        """Get status of the warm engine pool"""
        return self.pool_manager.get_status()

    def initialize_pool(self, pool_size: int = 3) -> None:
        """
        Initialize the warm engine pool with a specific number of engines.

        Args:
            pool_size: Number of warm engines to create
        """
        self.logger.info(f"Initializing warm engine pool with {pool_size} engines...")

        for i in range(pool_size):
            try:
                engine_id = self.pool_manager.create_warm_engine(f"engine-{i}")
                self.logger.info(f"Created warm engine {i+1}/{pool_size}: {engine_id}")
            except Exception as e:
                self.logger.error(f"Failed to create warm engine {i+1}: {e}")

        status = self.get_pool_status()
        self.logger.info(f"Warm engine pool initialized: {status['pool_size']} engines ready")

    def shutdown(self) -> None:
        """Shutdown all warm engines"""
        self.logger.info("Shutting down warm engine pool...")
        count = self.pool_manager.shutdown_all_engines()
        self.logger.info(f"Shut down {count} warm engines")


def main():
    """Example usage"""
    import time

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create orchestrator
    orchestrator = WarmPoolOrchestrator()

    # Initialize pool
    print("Initializing warm engine pool...")
    orchestrator.initialize_pool(pool_size=2)

    # Get status
    status = orchestrator.get_pool_status()
    print("\nPool Status:")
    print(json.dumps(status, indent=2, default=str))

    # Generate a world
    print("\nGenerating test world...")
    result = orchestrator.generate_world("TestSeed123")
    print("\nGeneration Result:")
    print(json.dumps(result, indent=2, default=str))

    # Shutdown
    print("\nShutting down...")
    orchestrator.shutdown()


if __name__ == "__main__":
    main()
