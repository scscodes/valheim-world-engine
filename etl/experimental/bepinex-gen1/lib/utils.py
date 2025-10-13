#!/usr/bin/env python3
"""
BepInEx Gen1 - Utility Functions
Helper functions for configuration, file handling, and validation
"""

import os
import time
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional


logger = logging.getLogger(__name__)


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load and parse YAML configuration file

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Dictionary containing configuration data

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    logger.debug(f"Loading config from {config_path}")

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    logger.info(f"Loaded config: {config_file.name}")
    return config


def load_global_configs(repo_root: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load all global YAML configurations

    Args:
        repo_root: Path to repository root

    Returns:
        Dictionary with keys: valheim_world, validation_data, rendering_config
    """
    global_data_dir = repo_root / "global" / "data"

    configs = {
        "valheim-world": load_yaml_config(global_data_dir / "valheim-world.yml"),
        "validation-data": load_yaml_config(global_data_dir / "validation-data.yml"),
        "rendering-config": load_yaml_config(global_data_dir / "rendering-config.yml"),
    }

    logger.info("Loaded all global configurations")
    return configs


def hash_seed(seed: str, algorithm: str = "sha256") -> str:
    """
    Generate hash from seed string

    Args:
        seed: Input seed string
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal hash string
    """
    hasher = hashlib.new(algorithm)
    hasher.update(seed.encode('utf-8'))
    hash_value = hasher.hexdigest()

    logger.debug(f"Hashed seed '{seed}' -> {hash_value[:16]}...")
    return hash_value


def create_output_structure(base_dir: Path, seed_hash: str) -> Dict[str, Path]:
    """
    Create standard output directory structure for a seed

    Args:
        base_dir: Base output directory
        seed_hash: Hash of the seed

    Returns:
        Dictionary of created directory paths
    """
    seed_dir = base_dir / "seeds" / seed_hash

    directories = {
        "seed_root": seed_dir,
        "raw": seed_dir / "raw",
        "extracted": seed_dir / "extracted",
        "processed": seed_dir / "processed",
        "renders": seed_dir / "renders",
    }

    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {name} -> {path}")

    logger.info(f"Created output structure for seed {seed_hash[:16]}...")
    return directories


def validate_file_exists(file_path: Path, timeout: int = 0) -> bool:
    """
    Validate that a file exists (with optional timeout)

    Args:
        file_path: Path to file
        timeout: Seconds to wait for file to appear (0 = no wait)

    Returns:
        True if file exists, False otherwise
    """
    start_time = time.time()

    while True:
        if file_path.exists():
            logger.debug(f"File exists: {file_path}")
            return True

        if timeout == 0 or time.time() - start_time >= timeout:
            logger.warning(f"File not found: {file_path}")
            return False

        time.sleep(1)


def wait_for_file_stability(file_path: Path, stability_seconds: int = 10) -> bool:
    """
    Wait for file size to remain stable (indicates write completion)

    Args:
        file_path: Path to file
        stability_seconds: Seconds file size must remain unchanged

    Returns:
        True if stable, False if file doesn't exist
    """
    if not file_path.exists():
        logger.warning(f"File does not exist: {file_path}")
        return False

    logger.debug(f"Waiting for file stability: {file_path}")

    last_size = file_path.stat().st_size
    stable_count = 0

    while stable_count < stability_seconds:
        time.sleep(1)

        if not file_path.exists():
            logger.warning(f"File disappeared: {file_path}")
            return False

        current_size = file_path.stat().st_size

        if current_size == last_size:
            stable_count += 1
        else:
            logger.debug(f"File size changed: {last_size} -> {current_size}")
            last_size = current_size
            stable_count = 0

    logger.info(f"File stable at {last_size} bytes: {file_path.name}")
    return True


def validate_required_files(
    directories: Dict[str, Path],
    required_files: Dict[str, List[str]],
    seed: str
) -> Dict[str, bool]:
    """
    Validate that all required files exist

    Args:
        directories: Dictionary of directory paths
        required_files: Dict mapping directory names to required file patterns
        seed: Seed string (for filename substitution)

    Returns:
        Dictionary mapping file paths to existence status
    """
    results = {}

    for dir_name, file_patterns in required_files.items():
        if dir_name not in directories:
            logger.error(f"Unknown directory: {dir_name}")
            continue

        dir_path = directories[dir_name]

        for pattern in file_patterns:
            # Substitute seed into pattern
            filename = pattern.format(seed=seed)
            file_path = dir_path / filename

            exists = file_path.exists()
            results[str(file_path)] = exists

            if exists:
                logger.debug(f"✓ Found required file: {filename}")
            else:
                logger.warning(f"✗ Missing required file: {filename}")

    return results


def find_repo_root(start_path: Optional[Path] = None) -> Path:
    """
    Find repository root by looking for marker files

    Args:
        start_path: Path to start search from (default: current directory)

    Returns:
        Path to repository root

    Raises:
        RuntimeError: If repository root cannot be found
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()
    # Look for CLAUDE.md which is at repo root specifically
    marker_files = ["CLAUDE.md"]

    while current != current.parent:
        # Check for CLAUDE.md and global/ directory to confirm repo root
        if (current / "CLAUDE.md").exists() and (current / "global").exists():
            logger.debug(f"Found repo root: {current}")
            return current
        current = current.parent

    raise RuntimeError(f"Could not find repository root from {start_path}")


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def get_file_size_mb(file_path: Path) -> float:
    """
    Get file size in megabytes

    Args:
        file_path: Path to file

    Returns:
        File size in MB
    """
    if not file_path.exists():
        return 0.0

    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    return round(size_mb, 2)
