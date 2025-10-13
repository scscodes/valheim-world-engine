#!/usr/bin/env python3
"""
Warm Engine Pool Manager for Valheim World Engine
Strategy 2: Pre-initialized Valheim State

Instead of pre-warming containers with installed software,
this manager keeps Valheim server engines RUNNING and ready.
When a job arrives, we send console commands to load the new seed
instead of restarting the entire server (60-90s startup → 10-20s).

Expected Performance Improvement: 50-65% reduction (3min → 1-1.5min sustained)
"""

import os
import sys
import json
import time
import logging
import hashlib
import docker
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum


class EngineState(Enum):
    """States of a warm engine"""
    STARTING = "starting"          # Engine is booting up
    READY = "ready"                # Engine is idle and ready for jobs
    GENERATING = "generating"      # Engine is processing a world generation job
    EXPORTING = "exporting"        # Engine is exporting data via BepInEx
    RESETTING = "resetting"        # Engine is cleaning up after a job
    ERROR = "error"                # Engine encountered an error


@dataclass
class WarmEngineConfig:
    """Extended configuration for warm engine management"""
    base_image: str = "vwe-bepinex-gen1:latest"  # Docker image to use
    container_name_prefix: str = "vwe-warm-engine"  # Prefix for container names
    max_warm_containers: int = 3              # Maximum number of warm engines in the pool
    container_ttl_minutes: int = 120          # Time-to-live for idle containers (minutes)
    engine_startup_timeout: int = 120         # Max time to wait for Valheim engine to start (seconds)
    world_gen_timeout: int = 300              # Max time for world generation (5 minutes)
    keep_alive_check_interval: int = 30       # How often to check engine health (seconds)
    auto_reset_after_job: bool = True         # Automatically reset engine after job completion
    max_jobs_per_engine: int = 10             # Reset engine after N jobs to prevent memory leaks


@dataclass
class EngineMetadata:
    """Metadata for a warm engine"""
    engine_id: str
    state: EngineState
    container_name: str
    created_at: str
    last_used: str
    jobs_processed: int = 0
    current_job_id: Optional[str] = None
    current_seed: Optional[str] = None
    health_status: str = "healthy"


class WarmEnginePoolManager:
    """
    Manages a pool of pre-initialized Valheim servers ready for instant world generation.

    Key Innovation:
    - Traditional approach: spin up container → start server (60-90s) → generate → shutdown
    - Warm pool approach: keep servers running → send console command (10-20s) → extract → reset

    This eliminates the majority of the startup time by keeping the Valheim game engine
    already loaded and initialized.
    """

    def __init__(self, docker_client: docker.DockerClient = None):
        self.docker_client = docker_client or docker.from_env()
        self.logger = logging.getLogger(__name__)

        # Configuration for warm engines
        self.engine_config = WarmEngineConfig(
            base_image="vwe-bepinex-gen1:latest",
            container_name_prefix="vwe-warm-engine",
            max_warm_containers=3,              # Pool size: 3 engines for parallel jobs
            container_ttl_minutes=120,          # Keep engines alive for 2 hours
            engine_startup_timeout=120,
            world_gen_timeout=300,
            keep_alive_check_interval=30,
            auto_reset_after_job=True,
            max_jobs_per_engine=10
        )

        # Track warm engines
        self.engines: Dict[str, EngineMetadata] = {}

        # Discover existing warm engines
        self._discover_existing_engines()

    def create_warm_engine(self, engine_id: Optional[str] = None) -> str:
        """
        Create a new warm engine with Valheim server pre-initialized.

        Returns:
            engine_id: Unique identifier for the warm engine
        """
        if engine_id is None:
            engine_id = f"engine-{int(time.time())}"

        container_name = f"{self.engine_config.container_name_prefix}-{engine_id}"

        # Check if we're at capacity
        active_engines = [e for e in self.engines.values() if e.state != EngineState.ERROR]
        if len(active_engines) >= self.engine_config.max_warm_containers:
            self.logger.warning(f"Max warm engines reached ({self.engine_config.max_warm_containers})")
            # Return least recently used engine
            lru_engine = sorted(active_engines, key=lambda e: e.last_used)[0]
            return lru_engine.engine_id

        self.logger.info(f"Creating warm engine: {engine_id}")

        try:
            # Create container with Valheim server command (not sleep!)
            container = self.docker_client.containers.create(
                image=self.engine_config.base_image,
                name=container_name,
                detach=True,
                environment=self._get_engine_environment(),
                volumes=self._get_engine_volumes(),
                command=self._get_engine_command(),  # Starts Valheim server
                labels={
                    "vwe.type": "warm-engine",
                    "vwe.engine_id": engine_id,
                    "vwe.created": datetime.utcnow().isoformat(),
                    "vwe.state": EngineState.STARTING.value
                },
                # Add resource limits to prevent runaway memory usage
                mem_limit="4g",
                memswap_limit="4g"
            )

            # Start the container
            container.start()

            # Track the engine
            self.engines[engine_id] = EngineMetadata(
                engine_id=engine_id,
                state=EngineState.STARTING,
                container_name=container_name,
                created_at=datetime.utcnow().isoformat(),
                last_used=datetime.utcnow().isoformat(),
                jobs_processed=0
            )

            # Wait for Valheim server to be ready
            if self._wait_for_engine_ready(engine_id):
                self.engines[engine_id].state = EngineState.READY
                self.logger.info(f"Warm engine ready: {engine_id}")
                return engine_id
            else:
                self.engines[engine_id].state = EngineState.ERROR
                raise RuntimeError(f"Engine {engine_id} failed to become ready")

        except Exception as e:
            self.logger.error(f"Failed to create warm engine {engine_id}: {e}")
            if engine_id in self.engines:
                self.engines[engine_id].state = EngineState.ERROR
            raise

    def generate_world(self, seed: str, seed_hash: str, job_id: str,
                      data_dir: Path, engine_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a world using a warm engine with fast container restart.

        Option B: Fast Container Restart
        - Warm engine has Valheim/BepInEx pre-installed
        - Restart container with new seed environment (30-45s)
        - Wait for world generation and export
        - Extract data from container volumes
        - Reset engine to ready state

        Args:
            seed: The world seed string
            seed_hash: Hash of the seed for file naming
            job_id: Unique job identifier
            data_dir: Path to store generated data
            engine_id: Specific engine to use (optional, will auto-select if None)

        Returns:
            Dictionary with generation results
        """
        # Get or select an available engine
        if engine_id is None:
            engine_id = self._get_available_engine()

        if engine_id not in self.engines:
            raise ValueError(f"Engine {engine_id} not found")

        engine = self.engines[engine_id]

        # Verify engine is ready
        if engine.state != EngineState.READY:
            raise RuntimeError(f"Engine {engine_id} is not ready (state: {engine.state})")

        self.logger.info(f"Generating world '{seed}' on engine {engine_id} (fast restart)")

        # Update engine state
        engine.state = EngineState.GENERATING
        engine.current_job_id = job_id
        engine.current_seed = seed
        engine.last_used = datetime.utcnow().isoformat()

        start_time = time.time()

        try:
            # Get container
            container = self.docker_client.containers.get(engine.container_name)

            # Update container environment and restart with new seed
            # This is MUCH faster than cold start (30-45s vs 90s)
            restart_result = self._restart_with_new_seed(container, seed, seed_hash, data_dir)

            if not restart_result["success"]:
                raise RuntimeError(f"Container restart failed: {restart_result.get('error')}")

            # Update container reference to the new container
            container = restart_result["container"]
            restart_time = restart_result.get("restart_time", 0)

            # Wait for world generation to complete
            engine.state = EngineState.EXPORTING
            export_result = self._wait_for_generation_complete(container, seed)

            if not export_result["success"]:
                raise RuntimeError(f"World generation failed: {export_result.get('error')}")

            generation_time = export_result.get("generation_time", 0)

            # Extract data from container to local directory
            extract_result = self._extract_data_from_container(container, seed, data_dir)

            if not extract_result["success"]:
                raise RuntimeError(f"Data extraction failed: {extract_result.get('error')}")

            total_time = time.time() - start_time

            # Update metadata
            engine.jobs_processed += 1
            engine.current_job_id = None
            engine.current_seed = None

            # Reset engine if max jobs reached
            if engine.jobs_processed >= self.engine_config.max_jobs_per_engine:
                self.logger.info(f"Engine {engine_id} reached max jobs, will reset")
                self._reset_engine(engine_id)
            else:
                engine.state = EngineState.READY

            self.logger.info(f"World generation complete on engine {engine_id} in {total_time:.1f}s")

            return {
                "success": True,
                "engine_id": engine_id,
                "seed": seed,
                "seed_hash": seed_hash,
                "job_id": job_id,
                "restart_time": restart_time,
                "generation_time": generation_time,
                "total_time": total_time
            }

        except Exception as e:
            self.logger.error(f"World generation failed on engine {engine_id}: {e}")
            engine.state = EngineState.ERROR
            engine.health_status = f"error: {str(e)}"
            raise

    def _get_available_engine(self) -> str:
        """Get an available warm engine, creating one if needed"""
        # Find ready engines
        ready_engines = [
            (eid, e) for eid, e in self.engines.items()
            if e.state == EngineState.READY
        ]

        if ready_engines:
            # Return least recently used ready engine
            ready_engines.sort(key=lambda x: x[1].last_used)
            return ready_engines[0][0]

        # No ready engines, create a new one
        return self.create_warm_engine()

    def _restart_with_new_seed(self, container, seed: str, seed_hash: str,
                               data_dir: Path) -> Dict[str, Any]:
        """
        Restart container with new seed environment.

        Option B: Fast restart leveraging pre-installed Valheim/BepInEx
        - Stop container
        - Update environment variables with new seed
        - Restart container
        - Wait for Valheim to start

        Much faster than cold start (30-45s vs 90s) because Valheim/BepInEx
        are already installed, no SteamCMD download needed.
        """
        start_time = time.time()

        self.logger.info(f"Restarting container with seed: {seed}")

        try:
            # Stop container
            self.logger.info("Stopping container...")
            container.stop(timeout=10)

            # Prepare new volumes for this seed
            seed_data_dir = data_dir / "seeds" / seed_hash
            seed_data_dir.mkdir(parents=True, exist_ok=True)

            worlds_local = seed_data_dir / "worlds_local"
            worlds_local.mkdir(parents=True, exist_ok=True)

            world_data = seed_data_dir / "world_data"
            world_data.mkdir(parents=True, exist_ok=True)

            # Get plugins directory
            plugins_dir = Path(__file__).parent.parent / "bepinex-gen1" / "plugins"

            # Update container with new volumes
            # Note: Docker doesn't allow updating volumes on stopped containers,
            # so we need to remove and recreate
            container_config = container.attrs
            image = container.image

            # Remove old container
            container.remove()

            # Create new container with updated config
            new_container = self.docker_client.containers.create(
                image=image,
                name=container.name,
                detach=True,
                environment={
                    "TZ": "UTC",
                    "VWE_WARM_ENGINE": "false",  # Now running a real job
                    "BEPINEX": "1",
                    "SERVER_PUBLIC": "0",
                    "WORLD_NAME": seed,
                    "WORLD_SEED": seed,
                    "SERVER_NAME": f"VWE Generator - {seed}",
                    "SERVER_PASS": "vwe",
                    "VWE_AUTOSAVE_ENABLED": "true",
                    "VWE_AUTOSAVE_DELAY": "2",
                    "VWE_DATAEXPORT_ENABLED": "true",
                    "VWE_DATAEXPORT_FORMAT": "both",
                    "VWE_DATAEXPORT_DIR": "/config/world_data"
                },
                volumes={
                    str(seed_data_dir): {"bind": "/config", "mode": "rw"},
                    str(plugins_dir): {"bind": "/config/bepinex/plugins", "mode": "ro"}
                },
                labels=container_config.get("Config", {}).get("Labels", {}),
                mem_limit="4g",
                memswap_limit="4g"
            )

            # Start the new container
            self.logger.info("Starting container with new seed...")
            new_container.start()

            # Update our reference to the container
            container = new_container

            restart_time = time.time() - start_time
            self.logger.info(f"Container restarted in {restart_time:.1f}s")

            return {
                "success": True,
                "restart_time": restart_time,
                "container": new_container
            }

        except Exception as e:
            self.logger.error(f"Failed to restart container: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _wait_for_generation_complete(self, container, seed: str,
                                      timeout: int = None) -> Dict[str, Any]:
        """
        Wait for world generation and export to complete.

        Monitors logs for:
        1. World generation start
        2. Zone system initialization
        3. Data export completion
        """
        timeout = timeout or self.engine_config.world_gen_timeout
        start_time = time.time()

        self.logger.info(f"Waiting for world generation to complete (timeout: {timeout}s)")

        generation_started = False
        export_started = False

        while time.time() - start_time < timeout:
            try:
                # Get recent logs
                logs = container.logs(tail=100).decode('utf-8', errors='ignore')

                # Check for generation start
                if not generation_started and ("Generating locations" in logs or "Zonesystem Awake" in logs):
                    generation_started = True
                    self.logger.info("World generation started")

                # Check for export completion
                if generation_started and ("VWE_DataExporter" in logs or "Export complete" in logs):
                    export_started = True
                    self.logger.info("Data export detected")

                # Check for world files
                result = container.exec_run(f"ls -la /config/worlds_local/{seed}.db 2>/dev/null")
                has_db_file = result.exit_code == 0

                # Check for exported data (BepInEx exports to /opt/valheim/world_data)
                result = container.exec_run("ls -la /opt/valheim/world_data/*.json 2>/dev/null")
                has_export_files = result.exit_code == 0

                if has_db_file and has_export_files:
                    generation_time = time.time() - start_time
                    self.logger.info(f"World generation complete in {generation_time:.1f}s")

                    # Copy export files to mounted volume
                    container.exec_run("mkdir -p /config/world_data")
                    container.exec_run("cp /opt/valheim/world_data/*.json /config/world_data/")
                    container.exec_run("cp /opt/valheim/world_data/*.png /config/world_data/")

                    return {
                        "success": True,
                        "generation_time": generation_time
                    }

                time.sleep(3)

            except Exception as e:
                self.logger.warning(f"Error checking generation status: {e}")
                time.sleep(3)

        return {
            "success": False,
            "error": f"Generation timeout after {timeout}s"
        }

    def _extract_data_from_container(self, container, seed: str,
                                    data_dir: Path) -> Dict[str, Any]:
        """
        Extract generated data from container to local filesystem.

        The data is already in the mounted volume, so this is mostly
        a verification step.
        """
        try:
            self.logger.info("Verifying extracted data...")

            # Since we mounted the volume directly, data should already be there
            # Just verify the files exist

            seed_hash = hashlib.sha256(seed.encode('utf-8')).hexdigest()
            seed_data_dir = data_dir / "seeds" / seed_hash

            worlds_local = seed_data_dir / "worlds_local"
            world_data = seed_data_dir / "world_data"

            # Check for world files
            db_file = worlds_local / f"{seed}.db"
            fwl_file = worlds_local / f"{seed}.fwl"

            if not db_file.exists():
                return {
                    "success": False,
                    "error": f"World database not found: {db_file}"
                }

            # Check for exported data
            export_files = list(world_data.glob("*.json"))
            if not export_files:
                return {
                    "success": False,
                    "error": f"No exported data found in {world_data}"
                }

            self.logger.info(f"✓ World files verified: {db_file.name}")
            self.logger.info(f"✓ Export files verified: {len(export_files)} files")

            return {
                "success": True,
                "files": {
                    "db": str(db_file),
                    "fwl": str(fwl_file) if fwl_file.exists() else None,
                    "exports": [str(f) for f in export_files]
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to extract data: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _wait_for_engine_ready(self, engine_id: str, timeout: int = None) -> bool:
        """Wait for Valheim engine to be fully initialized and ready"""
        timeout = timeout or self.engine_config.engine_startup_timeout
        start_time = time.time()

        engine = self.engines[engine_id]
        container_name = engine.container_name

        self.logger.info(f"Waiting for engine {engine_id} to be ready (timeout: {timeout}s)")

        while time.time() - start_time < timeout:
            try:
                container = self.docker_client.containers.get(container_name)

                # Check container status
                if container.status != "running":
                    self.logger.warning(f"Container {container_name} is not running")
                    time.sleep(2)
                    continue

                # Check logs for readiness indicators
                logs = container.logs(tail=100).decode('utf-8', errors='ignore')

                # Look for Valheim server ready messages
                ready_indicators = [
                    "Game server connected",
                    "DungeonDB Start",
                    "Zonesystem Awake",
                    "Server ready"
                ]

                if any(indicator in logs for indicator in ready_indicators):
                    self.logger.info(f"Engine {engine_id} is ready!")
                    return True

                time.sleep(2)

            except docker.errors.NotFound:
                self.logger.error(f"Container {container_name} not found")
                return False
            except Exception as e:
                self.logger.warning(f"Error checking engine readiness: {e}")
                time.sleep(2)

        self.logger.error(f"Engine {engine_id} did not become ready within {timeout}s")
        return False

    def _reset_engine(self, engine_id: str) -> bool:
        """Reset an engine to ready state after job completion"""
        if engine_id not in self.engines:
            return False

        engine = self.engines[engine_id]
        engine.state = EngineState.RESETTING

        self.logger.info(f"Resetting engine {engine_id}")

        try:
            container = self.docker_client.containers.get(engine.container_name)

            # Clean up world data
            container.exec_run("rm -rf /config/worlds_local/*")

            # Clear any temporary files
            container.exec_run("rm -f /tmp/vwe_commands.txt /config/vwe_reload_env.txt")

            # If engine has processed max jobs, restart it
            if engine.jobs_processed >= self.engine_config.max_jobs_per_engine:
                self.logger.info(f"Engine {engine_id} reached max jobs, restarting...")
                container.restart(timeout=30)

                # Wait for it to be ready again
                if self._wait_for_engine_ready(engine_id):
                    engine.jobs_processed = 0
                else:
                    engine.state = EngineState.ERROR
                    return False

            engine.state = EngineState.READY
            self.logger.info(f"Engine {engine_id} reset complete")
            return True

        except Exception as e:
            self.logger.error(f"Failed to reset engine {engine_id}: {e}")
            engine.state = EngineState.ERROR
            return False

    def _discover_existing_engines(self) -> None:
        """Discover existing warm engines from previous runs"""
        try:
            containers = self.docker_client.containers.list(
                filters={"label": "vwe.type=warm-engine", "status": "running"}
            )

            for container in containers:
                engine_id = container.labels.get("vwe.engine_id")
                if engine_id and engine_id not in self.engines:
                    self.engines[engine_id] = EngineMetadata(
                        engine_id=engine_id,
                        state=EngineState.READY,  # Assume ready (will be validated on use)
                        container_name=container.name,
                        created_at=container.labels.get("vwe.created", datetime.utcnow().isoformat()),
                        last_used=container.labels.get("vwe.created", datetime.utcnow().isoformat()),
                        jobs_processed=0
                    )
                    self.logger.info(f"Discovered existing warm engine: {engine_id}")

        except Exception as e:
            self.logger.warning(f"Error discovering existing engines: {e}")

    def _get_engine_environment(self) -> Dict[str, str]:
        """Get environment variables for warm engines"""
        return {
            "TZ": "UTC",
            "VWE_WARM_ENGINE": "true",
            "BEPINEX": "1",
            "SERVER_PUBLIC": "0",
            "UPDATE_ON_START": "0",  # No updates in warm engines
            "WORLD_NAME": "WarmEngine",  # Default world
            "SERVER_NAME": "VWE Warm Engine Pool",
            "VWE_AUTOSAVE_ENABLED": "true",
            "VWE_DATAEXPORT_ENABLED": "true"
        }

    def _get_engine_volumes(self) -> Dict[str, Dict[str, str]]:
        """Get volumes for warm engines"""
        # Use temporary directory for warm engines
        warm_dir = Path("/tmp/vwe-warm-engines")
        warm_dir.mkdir(exist_ok=True)

        # Mount plugins from bepinex-gen1 directory (read-only)
        plugins_dir = Path(__file__).parent.parent / "bepinex-gen1" / "plugins"

        volumes = {
            str(warm_dir): {"bind": "/config", "mode": "rw"}
        }

        # Only mount plugins if directory exists
        if plugins_dir.exists():
            volumes[str(plugins_dir)] = {"bind": "/config/bepinex/plugins", "mode": "ro"}
            self.logger.info(f"Mounting plugins from: {plugins_dir}")

        return volumes

    def _get_engine_command(self) -> List[str]:
        """Get command to start Valheim server in warm engines"""
        return ["valheim-server"]  # Not sleep - actual server!

    def get_status(self) -> Dict[str, Any]:
        """Get status of all warm engines"""
        return {
            "pool_size": len(self.engines),
            "max_pool_size": self.engine_config.max_warm_containers,
            "engines": {
                eid: {
                    "state": e.state.value,
                    "container": e.container_name,
                    "jobs_processed": e.jobs_processed,
                    "current_job": e.current_job_id,
                    "current_seed": e.current_seed,
                    "health": e.health_status,
                    "created_at": e.created_at,
                    "last_used": e.last_used
                }
                for eid, e in self.engines.items()
            },
            "config": asdict(self.engine_config)
        }

    def shutdown_engine(self, engine_id: str) -> bool:
        """Shutdown a specific warm engine"""
        if engine_id not in self.engines:
            return False

        engine = self.engines[engine_id]

        try:
            container = self.docker_client.containers.get(engine.container_name)
            container.stop(timeout=30)
            container.remove(force=True)
            del self.engines[engine_id]
            self.logger.info(f"Shut down engine {engine_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown engine {engine_id}: {e}")
            return False

    def shutdown_all_engines(self) -> int:
        """Shutdown all warm engines"""
        count = 0
        for engine_id in list(self.engines.keys()):
            if self.shutdown_engine(engine_id):
                count += 1
        return count


def main():
    """Example usage of warm engine pool manager"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    manager = WarmEnginePoolManager()

    # Create initial warm engines
    print("Creating warm engine pool...")
    engine1 = manager.create_warm_engine()
    print(f"Created engine: {engine1}")

    # Get status
    status = manager.get_status()
    print("\nWarm Engine Pool Status:")
    print(json.dumps(status, indent=2, default=str))

    # Example: Generate a world
    # result = manager.generate_world("TestSeed", "test-hash-123", "job-001")
    # print(f"\nGeneration result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
