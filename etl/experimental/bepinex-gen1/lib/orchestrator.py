#!/usr/bin/env python3
"""
BepInEx Gen1 - Docker Orchestrator
Handles Docker container lifecycle for world generation
"""

import os
import time
import json
import logging
import docker
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# Set up logger first
logger = logging.getLogger(__name__)

# Import warm container manager
import sys
warm_container_path = str(Path(__file__).parent.parent.parent.parent.parent / "global" / "docker")
if warm_container_path not in sys.path:
    sys.path.append(warm_container_path)

try:
    from warm_container_manager import WarmContainerManager
    logger.info(f"✓ WarmContainerManager imported successfully from {warm_container_path}")
except ImportError as e:
    # Fallback if warm container manager not available
    logger.warning(f"✗ Failed to import WarmContainerManager: {e}")
    WarmContainerManager = None


@dataclass
class GenerationPlan:
    """Plan for world generation execution"""
    seed: str
    seed_hash: str
    container_name: str
    image: str
    created_at: str
    environment: Dict[str, str]
    volumes: Dict[str, Dict[str, str]]
    command: Optional[List[str]]
    timeout_seconds: int
    readiness_indicators: List[str]


@dataclass
class GenerationResult:
    """Result of world generation"""
    success: bool
    duration_seconds: float
    logs: str
    files_found: Dict[str, bool]
    error_message: Optional[str] = None
    timeout: bool = False


class DockerOrchestrator:
    """Orchestrates Docker containers for world generation"""

    def __init__(
        self,
        generator_config: Dict[str, Any],
        global_configs: Dict[str, Any],
        repo_root: Path
    ):
        """
        Initialize Docker orchestrator

        Args:
            generator_config: Generator-specific configuration
            global_configs: Global YAML configurations
            repo_root: Path to repository root
        """
        self.generator_config = generator_config
        self.global_configs = global_configs
        self.repo_root = repo_root
        self.docker_client = docker.from_env()

        # Extract configurations
        self.docker_config = generator_config.get("docker", {})
        self.bepinex_config = generator_config.get("bepinex", {})
        self.generation_config = generator_config.get("generation", {})

        # Initialize warm container manager
        if WarmContainerManager is not None:
            try:
                self.warm_manager = WarmContainerManager(self.docker_client)
                # Check for existing warm containers first
                warm_containers = self._find_warm_containers()
                if warm_containers:
                    self.use_warm_containers = self.docker_config.get("use_warm_containers", True)
                    logger.info(f"Found {len(warm_containers)} warm containers: {warm_containers}")
                else:
                    # Try to get status from warm container manager
                    status = self.warm_manager.get_status()
                    if status['total_containers'] > 0:
                        self.use_warm_containers = self.docker_config.get("use_warm_containers", True)
                        logger.info(f"Warm container manager connected: {status['total_containers']} containers available")
                    else:
                        self.use_warm_containers = False
                        logger.warning("No warm containers available, using standard containers")
            except Exception as e:
                self.warm_manager = None
                self.use_warm_containers = False
                logger.warning(f"Warm container manager not available: {e}")
        else:
            self.warm_manager = None
            self.use_warm_containers = False
            logger.warning("Warm container manager not available, using standard containers")

        logger.info("Docker orchestrator initialized with warm container support")

    def _find_warm_containers(self) -> List[str]:
        """Find running universal warm containers directly"""
        try:
            containers = self.docker_client.containers.list(filters={"status": "running"})
            warm_containers = []
            for container in containers:
                if "vwe-warm-universal" in container.name and container.image.tags and "vwe-bepinex-gen1" in container.image.tags[0]:
                    warm_containers.append(container.name)
            return warm_containers
        except Exception as e:
            logger.warning(f"Error finding warm containers: {e}")
            return []

    def validate_configuration(self) -> bool:
        """Validate Docker configuration before generation"""
        logger.info("Validating Docker configuration...")
        
        try:
            # Validate Docker image exists
            image = self.docker_config.get("custom_image") or self.docker_config.get("image")
            if not self._image_exists(image):
                logger.error(f"Docker image not found: {image}")
                return False
            
            # Validate volume mount paths
            plugins_source = self.repo_root / self.docker_config["mounts"]["plugins_source"]
            if not plugins_source.exists():
                logger.error(f"BepInEx plugins directory not found: {plugins_source}")
                return False
            
            # Validate required plugins exist
            required_plugins = ["VWE_DataExporter.dll", "VWE_AutoSave.dll", "Newtonsoft.Json.dll"]
            missing_plugins = []
            for plugin in required_plugins:
                if not (plugins_source / plugin).exists():
                    missing_plugins.append(plugin)
            
            if missing_plugins:
                logger.error(f"Missing required plugins: {missing_plugins}")
                return False
            
            # Validate warm container configuration if enabled
            if self.use_warm_containers and self.warm_manager is not None:
                try:
                    status = self.warm_manager.get_status()
                    logger.info(f"Warm container status: {status['total_containers']} containers available")
                    
                    # Validate warm container environment
                    if status['total_containers'] > 0:
                        self._validate_warm_container_environment()
                except Exception as e:
                    logger.warning(f"Warm container validation failed: {e}")
                    self.use_warm_containers = False
            
            logger.info("✓ Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def _validate_warm_container_environment(self) -> bool:
        """Validate warm container environment and configuration"""
        try:
            # Get a warm container to inspect
            warm_container_name = self.warm_manager.get_available_container("universal-valheim")
            if not warm_container_name:
                logger.warning("No warm containers available for validation")
                return False
            
            warm_container = self.docker_client.containers.get(warm_container_name)
            
            # Check environment variables
            env_vars = warm_container.attrs['Config']['Env'] or []
            env_dict = {var.split('=')[0]: var.split('=')[1] for var in env_vars if '=' in var}
            
            required_env = ['BEPINEX', 'VWE_DATAEXPORT_ENABLED', 'VWE_AUTOSAVE_ENABLED']
            for env_var in required_env:
                if env_var not in env_dict:
                    logger.warning(f"✗ Missing environment variable in warm container: {env_var}")
                else:
                    logger.info(f"✓ Warm container has {env_var}={env_dict[env_var]}")
            
            # Check mounts
            mounts = warm_container.attrs['Mounts'] or []
            mount_destinations = [mount.get('Destination', '') for mount in mounts]
            
            required_mounts = ['/config', '/config/bepinex/plugins']
            for mount in required_mounts:
                if mount in mount_destinations:
                    logger.info(f"✓ Warm container has mount: {mount}")
                else:
                    logger.warning(f"✗ Missing mount in warm container: {mount}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate warm container environment: {e}")
            return False

    def generate_world(
        self,
        seed: str,
        seed_hash: str,
        directories: Dict[str, Path],
        resolution: int = 512
    ) -> Tuple[GenerationPlan, GenerationResult]:
        """
        Generate world using Docker container

        Args:
            seed: Seed string
            seed_hash: Hash of seed
            directories: Output directory structure
            resolution: Export resolution

        Returns:
            Tuple of (GenerationPlan, GenerationResult)
        """
        logger.info(f"Starting world generation for seed '{seed}' (resolution: {resolution})")

        # Validate configuration first
        if not self.validate_configuration():
            return GenerationPlan(
                seed=seed, seed_hash=seed_hash, container_name="", image="",
                created_at=datetime.utcnow().isoformat(), environment={},
                volumes={}, command=None, timeout_seconds=0, readiness_indicators=[]
            ), GenerationResult(
                success=False, duration_seconds=0, logs="", files_found={},
                error_message="Configuration validation failed"
            )

        # Execute with retry logic
        max_retries = self.docker_config.get("max_retries", 3)
        retry_delay = self.docker_config.get("retry_delay", 10)
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{max_retries-1} after {retry_delay}s delay")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

                # Create generation plan
                plan = self._create_generation_plan(seed, seed_hash, directories, resolution)

                # Save plan
                self._save_plan(plan, directories["extracted"])

                # Execute generation (with warm container support)
                result = self._execute_generation(plan, directories)

                # Save logs (with filtering)
                self._save_logs(result, directories["extracted"])

                # Check if successful
                if result.success:
                    logger.info(f"✓ Generation successful on attempt {attempt + 1}")
                    return plan, result
                else:
                    logger.warning(f"Generation failed on attempt {attempt + 1}: {result.error_message}")
                    
                    # Don't retry on configuration errors
                    if "Configuration validation failed" in result.error_message:
                        break
                    
                    # Don't retry on timeout (likely resource issue)
                    if result.timeout:
                        logger.error("Generation timed out - likely resource issue, not retrying")
                        break

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    # Last attempt failed
                    return GenerationPlan(
                        seed=seed, seed_hash=seed_hash, container_name="", image="",
                        created_at=datetime.utcnow().isoformat(), environment={},
                        volumes={}, command=None, timeout_seconds=0, readiness_indicators=[]
                    ), GenerationResult(
                        success=False, duration_seconds=0, logs="", files_found={},
                        error_message=f"All {max_retries} attempts failed: {e}"
                    )

        # All retries exhausted
        logger.error(f"All {max_retries} generation attempts failed")
        return GenerationPlan(
            seed=seed, seed_hash=seed_hash, container_name="", image="",
            created_at=datetime.utcnow().isoformat(), environment={},
            volumes={}, command=None, timeout_seconds=0, readiness_indicators=[]
        ), GenerationResult(
            success=False, duration_seconds=0, logs="", files_found={},
            error_message=f"All {max_retries} attempts failed"
        )

    def _create_generation_plan(
        self,
        seed: str,
        seed_hash: str,
        directories: Dict[str, Path],
        resolution: int
    ) -> GenerationPlan:
        """Create execution plan for world generation"""
        container_name = f"{self.docker_config['container_prefix']}-{seed_hash[:16]}"

        # Determine which image to use
        image = self.docker_config.get("custom_image")
        if not self._image_exists(image):
            logger.warning(f"Custom image '{image}' not found, using fallback")
            image = self.docker_config["image"]

        # Build environment variables
        environment = self._build_environment(seed, seed_hash, resolution)

        # Build volume mounts
        volumes = self._build_volumes(seed, seed_hash, directories)

        # Get command (if needed)
        command = None  # Use default container command

        # Get timeout
        timeout_seconds = self.docker_config["timeouts"]["generation"]

        # Get readiness indicators
        readiness_indicators = self.generation_config.get("readiness_indicators", [])

        plan = GenerationPlan(
            seed=seed,
            seed_hash=seed_hash,
            container_name=container_name,
            image=image,
            created_at=datetime.utcnow().isoformat(),
            environment=environment,
            volumes=volumes,
            command=command,
            timeout_seconds=timeout_seconds,
            readiness_indicators=readiness_indicators
        )

        logger.debug(f"Created generation plan: {container_name}")
        return plan

    def _build_environment(
        self,
        seed: str,
        seed_hash: str,
        resolution: int
    ) -> Dict[str, str]:
        """Build environment variables for container"""
        env = {
            "TZ": "UTC",
            "SERVER_PUBLIC": "0",
            "UPDATE_ON_START": "1",
            "WORLD_NAME": seed,
            "WORLD_SEED": seed,
            "VWE_SEED_HASH": seed_hash,
            "VWE_RESOLUTION": str(resolution),
        }

        # Add PUID/PGID for proper file ownership (lloesche/valheim-server support)
        env["PUID"] = str(os.getuid())
        env["PGID"] = str(os.getgid())

        # Add BepInEx configuration
        if self.bepinex_config.get("enabled"):
            env["BEPINEX"] = "1"
            # Export configuration
            env["VWE_DATAEXPORT_ENABLED"] = "true"
            env["VWE_DATAEXPORT_FORMAT"] = "both"  # json + npy
            env["VWE_DATAEXPORT_DIR"] = "/opt/valheim/world_data"  # Where to write exports
            # Resolution config (BepInEx plugins read from config, but we set env as fallback)
            env["VWE_BIOME_RESOLUTION"] = str(resolution)
            env["VWE_HEIGHTMAP_RESOLUTION"] = str(resolution)
            # Logging
            env["VWE_LOG_EXPORTS"] = "true"
            env["VWE_LOG_DEBUG"] = "true"
            # AutoSave configuration
            env["VWE_AUTOSAVE_ENABLED"] = "true"
            env["VWE_AUTOSAVE_DELAY"] = "2"

        logger.debug(f"Built environment with {len(env)} variables")
        return env

    def _build_volumes(
        self,
        seed: str,
        seed_hash: str,
        directories: Dict[str, Path]
    ) -> Dict[str, Dict[str, str]]:
        """Build volume mounts for container"""
        volumes = {}

        # Mount seed root directory to /config (lloesche pattern)
        # This allows Valheim to create worlds_local/ inside /config
        # BepInEx will also be installed here, and our plugins are pre-copied
        seed_root = directories["seed_root"]
        volumes[str(seed_root.absolute())] = {
            "bind": "/config",
            "mode": "rw"
        }

        # Mount extracted directory for BepInEx exports
        # BepInEx plugin resolves to /opt/valheim/world_data, so mount there
        extracted_dir = directories["extracted"]
        volumes[str(extracted_dir.absolute())] = {
            "bind": "/opt/valheim/world_data",
            "mode": "rw"
        }

        # NOTE: We no longer mount plugins separately - they're copied into /config before container starts
        # This avoids read-only mount conflicts with BepInEx installation

        logger.debug(f"Built {len(volumes)} volume mounts")
        return volumes

    def _execute_generation(
        self,
        plan: GenerationPlan,
        directories: Dict[str, Path]
    ) -> GenerationResult:
        """Execute world generation using Docker container (with warm container support)"""
        start_time = time.time()
        container = None
        logs = ""
        error_message = None
        timeout = False
        used_warm_container = False

        try:
            # Try to use warm container first
            if self.use_warm_containers and self.warm_manager is not None:
                try:
                    logger.info("Attempting to use warm container...")
                    # Clone universal warm container for this job with custom environment and volumes
                    job_id = f"job-{int(time.time())}"
                    job_container_name = self.warm_manager.clone_container_for_job(
                        "universal-valheim", 
                        plan.seed_hash, 
                        job_id,
                        environment=plan.environment,
                        volumes=plan.volumes,
                        seed_name=plan.seed
                    )
                    container = self.docker_client.containers.get(job_container_name)
                    
                    # Start the cloned container
                    container.start()
                    logger.info(f"Started warm container clone: {job_container_name}")
                    
                    # Wait for container to transition to running state
                    time.sleep(2)
                    container.reload()
                    logger.info(f"Warm container status after start: {container.status}")
                    
                    used_warm_container = True
                    logger.info(f"✓ Using warm container clone: {job_container_name}")
                except Exception as e:
                    logger.warning(f"Warm container failed, falling back to new container: {e}")
                    self.use_warm_containers = False

            # Create new container if warm container not available
            if not used_warm_container:
                logger.info(f"Creating new container: {plan.container_name}")
                container = self.docker_client.containers.create(
                    image=plan.image,
                    name=plan.container_name,
                    detach=True,
                    environment=plan.environment,
                    volumes=plan.volumes,
                    command=plan.command,
                    labels={
                        "vwe.type": "worldgen",
                        "vwe.generator": "bepinex-gen1",
                        "vwe.seed": plan.seed,
                        "vwe.seed_hash": plan.seed_hash,
                    }
                )

                # Start container
                logger.info(f"Starting container: {plan.container_name}")
                container.start()
                
                # Wait for container to transition to running state
                time.sleep(2)
                container.reload()
                logger.info(f"Container status after start: {container.status}")

            # Wait for generation to complete with real-time monitoring
            ready, timeout = self._wait_for_generation_with_monitoring(
                container,
                plan.readiness_indicators,
                plan.timeout_seconds
            )

            # Get logs
            logs = container.logs().decode('utf-8', errors='replace')

            # Fix permissions BEFORE validating files (Docker creates as root)
            self._fix_permissions(directories["seed_root"])

            # Validate output files
            files_found = self._validate_output_files(plan.seed, directories)

            # Check success
            success = ready and all(files_found.values()) and not timeout

            duration = time.time() - start_time

            if not success:
                if timeout:
                    error_message = f"Generation timed out after {plan.timeout_seconds}s"
                elif not ready:
                    error_message = "Container did not reach ready state"
                else:
                    missing_files = [k for k, v in files_found.items() if not v]
                    error_message = f"Missing output files: {missing_files}"

        except Exception as e:
            logger.error(f"Error during generation: {e}")
            error_message = str(e)
            duration = time.time() - start_time
            files_found = {}
            success = False

        finally:
            # Cleanup container
            if container:
                try:
                    if used_warm_container and self.warm_manager is not None:
                        # Use warm container manager cleanup for job containers
                        logger.info(f"Cleaning up job container: {container.name}")
                        self.warm_manager.cleanup_job_container(container.name)
                    else:
                        # Standard cleanup for new containers
                        logger.info(f"Stopping container: {container.name}")
                        container.stop(timeout=self.docker_config["timeouts"]["shutdown"])
                        container.remove()
                        logger.info(f"Container removed: {container.name}")
                except Exception as e:
                    logger.error(f"Error cleaning up container: {e}")

        return GenerationResult(
            success=success,
            duration_seconds=duration,
            logs=logs,
            files_found=files_found,
            error_message=error_message,
            timeout=timeout
        )

    def _wait_for_generation(
        self,
        container: docker.models.containers.Container,
        readiness_indicators: List[str],
        timeout_seconds: int
    ) -> Tuple[bool, bool]:
        """
        Wait for container to complete generation

        Returns:
            Tuple of (ready, timed_out)
        """
        start_time = time.time()
        logger.info(f"Waiting for generation (timeout: {timeout_seconds}s)")

        # Extended indicators for BepInEx export completion
        export_indicators = [
            "ALL EXPORTS COMPLETE",
            "VWE_DataExporter: ALL EXPORTS COMPLETE"
        ]

        server_ready = False
        exports_complete = False

        while time.time() - start_time < timeout_seconds:
            try:
                container.reload()

                # Check if container exited
                if container.status in ["exited", "dead"]:
                    exit_code = container.attrs.get("State", {}).get("ExitCode", -1)
                    logger.info(f"Container exited with code: {exit_code}")
                    return (exit_code == 0), False

                # Check logs for readiness indicators
                logs = container.logs().decode('utf-8', errors='replace')

                # Check for server readiness
                if not server_ready:
                    for indicator in readiness_indicators:
                        if indicator in logs:
                            logger.info(f"Found readiness indicator: '{indicator}'")
                            server_ready = True
                            break

                # Check for BepInEx export completion
                if server_ready and not exports_complete:
                    for export_indicator in export_indicators:
                        if export_indicator in logs:
                            logger.info(f"Found export completion: '{export_indicator}'")
                            exports_complete = True
                            return True, False

                # If server is ready but no BepInEx, consider it done after extra wait
                if server_ready and not self.bepinex_config.get("enabled"):
                    # No BepInEx, just wait for files to stabilize
                    time.sleep(10)
                    return True, False

                time.sleep(5)

            except Exception as e:
                logger.error(f"Error checking container status: {e}")
                time.sleep(5)

        logger.warning(f"Generation timed out after {timeout_seconds}s")
        return False, True

    def _wait_for_generation_with_monitoring(
        self,
        container: docker.models.containers.Container,
        readiness_indicators: List[str],
        timeout_seconds: int
    ) -> Tuple[bool, bool]:
        """Enhanced wait method with real-time monitoring and error detection"""
        start_time = time.time()
        logger.info(f"Waiting for generation with monitoring (timeout: {timeout_seconds}s)")

        # Extended indicators for BepInEx export completion
        export_indicators = [
            "ALL EXPORTS COMPLETE",
            "VWE_DataExporter: ALL EXPORTS COMPLETE"
        ]

        server_ready = False
        exports_complete = False
        error_count = 0
        max_errors = 10
        last_log_time = start_time

        while time.time() - start_time < timeout_seconds:
            try:
                container.reload()

                # Check if container exited
                if container.status in ["exited", "dead"]:
                    exit_code = container.attrs.get("State", {}).get("ExitCode", -1)
                    logger.error(f"Container exited unexpectedly with code: {exit_code}")
                    return (exit_code == 0), False

                # Get new logs since last check
                logs = container.logs(since=datetime.fromtimestamp(last_log_time)).decode('utf-8', errors='replace')
                last_log_time = time.time()

                # Check for critical errors
                if self._check_for_critical_errors(logs):
                    logger.error("Critical error detected in container logs")
                    return False, False

                # Check for server readiness
                if not server_ready:
                    for indicator in readiness_indicators:
                        if indicator in logs:
                            logger.info(f"Found readiness indicator: '{indicator}'")
                            server_ready = True
                            break

                # Check for BepInEx export completion
                if server_ready and not exports_complete:
                    for export_indicator in export_indicators:
                        if export_indicator in logs:
                            logger.info(f"Found export completion: '{export_indicator}'")
                            exports_complete = True
                            return True, False

                # If server is ready but no BepInEx, consider it done after extra wait
                if server_ready and not self.bepinex_config.get("enabled"):
                    # No BepInEx, just wait for files to stabilize
                    time.sleep(10)
                    return True, False

                # Log progress every 30 seconds with filtered logs
                if int(time.time() - start_time) % 30 == 0:
                    self._log_progress_update(logs, int(time.time() - start_time))

                time.sleep(5)

            except Exception as e:
                error_count += 1
                logger.warning(f"Error checking container status: {e}")
                if error_count >= max_errors:
                    logger.error("Too many errors, stopping monitoring")
                    return False, False
                time.sleep(5)

        logger.warning(f"Generation timed out after {timeout_seconds}s")
        return False, True

    def _check_for_critical_errors(self, logs: str) -> bool:
        """Check for critical errors in container logs"""
        critical_patterns = [
            "FATAL ERROR",
            "CRITICAL ERROR", 
            "Failed to start",
            "Permission denied",
            "No such file or directory",
            "Connection refused",
            "Bind: address already in use",
            "Cannot assign requested address",
            "SteamCMD failed",
            "Valheim server failed",
            "BepInEx failed"
        ]
        
        for pattern in critical_patterns:
            if pattern in logs:
                logger.error(f"Critical error detected: {pattern}")
                return True
        return False

    def _log_progress_update(self, logs: str, elapsed_seconds: int) -> None:
        """Log filtered progress updates"""
        # Filter out noise and show relevant progress
        relevant_lines = []
        for line in logs.split('\n'):
            line = line.strip()
            if any(keyword in line.lower() for keyword in [
                'server', 'game', 'world', 'export', 'bepinex', 'valheim', 
                'connected', 'started', 'complete', 'error', 'failed',
                'biome', 'heightmap', 'structure', 'samples'
            ]):
                relevant_lines.append(line)
        
        if relevant_lines:
            logger.info(f"Progress update ({elapsed_seconds}s): {relevant_lines[-3:]}")  # Show last 3 relevant lines
        else:
            logger.info(f"Generation in progress... ({elapsed_seconds}s elapsed)")

    def _log_progress_updates(self, log_text: str) -> None:
        """Log filtered progress updates from container"""
        lines = log_text.split('\n')
        for line in lines:
            # Log important progress indicators
            if any(keyword in line for keyword in [
                "BiomeExporter:", "HeightmapExporter:", "StructureExporter:",
                "complete (", "samples/sec", "Export", "COMPLETE"
            ]):
                # Filter out noise even from progress logs
                if not any(noise in line for noise in [
                    "ERROR: Shader", "WARNING: Shader", "The shader"
                ]):
                    logger.info(f"[Container] {line.strip()}")

    def _check_for_errors(self, log_text: str) -> bool:
        """Check for critical errors in container logs"""
        critical_errors = [
            "VWE DataExporter: Error finding",
            "BiomeExporter: Error",
            "HeightmapExporter: Error",
            "StructureExporter: Error"
        ]
        
        for error in critical_errors:
            if error in log_text:
                return True
        
        return False

    def _validate_output_files(
        self,
        seed: str,
        directories: Dict[str, Path]
    ) -> Dict[str, bool]:
        """Validate that expected output files exist"""
        required_files = self.generation_config.get("required_files", {})
        files_found = {}

        for dir_name, file_patterns in required_files.items():
            # Handle raw files (now in worlds_local subdirectory)
            if dir_name == "raw":
                worlds_local_dir = directories["seed_root"] / "worlds_local"
                if not worlds_local_dir.exists():
                    logger.warning(f"Raw directory does not exist: {worlds_local_dir}")
                    # Mark all raw files as missing
                    for pattern in file_patterns:
                        filename = pattern.format(seed=seed)
                        file_path = worlds_local_dir / filename
                        files_found[str(file_path)] = False
                        logger.warning(f"✗ Missing output file: {filename} (directory not found)")
                else:
                    for pattern in file_patterns:
                        filename = pattern.format(seed=seed)
                        file_path = worlds_local_dir / filename
                        exists = file_path.exists()
                        files_found[str(file_path)] = exists

                        if exists:
                            logger.debug(f"✓ Found output file: {filename}")
                        else:
                            logger.warning(f"✗ Missing output file: {filename}")

            # Handle extracted files (BepInEx exports)
            elif dir_name == "extracted":
                if dir_name not in directories:
                    continue

                dir_path = directories[dir_name]

                for pattern in file_patterns:
                    filename = pattern.format(seed=seed)
                    file_path = dir_path / filename
                    exists = file_path.exists()
                    files_found[str(file_path)] = exists

                    if exists:
                        logger.debug(f"✓ Found output file: {filename}")
                    else:
                        logger.warning(f"✗ Missing output file: {filename}")

        return files_found

    def _save_plan(self, plan: GenerationPlan, output_dir: Path) -> None:
        """Save generation plan to JSON"""
        plan_file = output_dir / "worldgen_plan.json"

        with open(plan_file, 'w') as f:
            json.dump(asdict(plan), f, indent=2)

        logger.debug(f"Saved generation plan: {plan_file}")

    def _save_logs(self, result: GenerationResult, output_dir: Path) -> None:
        """Save generation logs to file (with noise filtering)"""
        log_file = output_dir / "worldgen_logs.txt"

        # Filter out noise from logs
        filtered_logs = self._filter_log_noise(result.logs)

        with open(log_file, 'w') as f:
            f.write(filtered_logs)

        logger.debug(f"Saved filtered generation logs: {log_file}")

    def _filter_log_noise(self, logs: str) -> str:
        """Filter out irrelevant log noise (shader warnings, etc.)"""
        lines = logs.split('\n')
        filtered_lines = []
        
        # Patterns to filter out
        noise_patterns = [
            "ERROR: Shader",
            "WARNING: Shader",
            "The shader",
            "The image effect",
            "DllNotFoundException: party",
            "PlayFab.Party",
            "SteamInternal_SetMinidumpSteamID",
            "[S_API FAIL]",
            "AsyncResourceUpload failed",
            "The referenced script on this Behaviour",
            "OnGUI function detected",
            "Unloading",
            "Total:",
            "UnloadTime:",
            "HDR Render Texture not supported",
            "Unable to load player prefs",
            "Failed to open plugin:",
            "DLL Not Found:",
        ]
        
        for line in lines:
            # Keep VWE logs and important generation logs
            if any(keyword in line for keyword in [
                "[VWE]", "VWE_", "BepInEx", "Game server connected", 
                "Zonesystem", "Worldgenerator", "Console:", "World save",
                "Export", "BiomeExporter", "HeightmapExporter", "StructureExporter"
            ]):
                filtered_lines.append(line)
            # Filter out noise patterns
            elif not any(pattern in line for pattern in noise_patterns):
                # Keep other potentially useful logs
                if len(line.strip()) > 0 and not line.startswith("10/10/2025"):
                    filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

    def _image_exists(self, image_name: str) -> bool:
        """Check if Docker image exists locally"""
        if not image_name:
            return False

        try:
            self.docker_client.images.get(image_name)
            return True
        except docker.errors.ImageNotFound:
            return False
        except Exception as e:
            logger.warning(f"Error checking image existence: {e}")
            return False

    def _setup_bepinex_plugins(self, seed_dir: Path) -> None:
        """
        Copy VWE BepInEx plugins into /config/BepInEx/plugins AFTER container installs BepInEx

        The lloesche/valheim-server image installs BepInEx when BEPINEX=1.
        We need to let it install the framework first, then add only our custom VWE plugins.

        IMPORTANT: We only copy VWE_*.dll files and Newtonsoft.Json.dll (dependency).
        We do NOT copy BepInEx core files - the container installs those.

        Args:
            seed_dir: Root directory for seed data (maps to /config in container)
        """
        import shutil

        try:
            # Source plugins directory
            plugins_source = self.repo_root / self.docker_config["mounts"]["plugins_source"]

            if not plugins_source.exists():
                logger.warning(f"BepInEx plugins directory not found: {plugins_source}")
                return

            # Destination directory in seed_root
            # NOTE: Container will create this when BepInEx installs
            plugins_dest = seed_dir / "BepInEx" / "plugins"
            plugins_dest.mkdir(parents=True, exist_ok=True)

            # Copy ONLY VWE-specific plugin files (not BepInEx framework)
            vwe_patterns = [
                "VWE_*.dll",
                "VWE_*.pdb",
                "VWE_*.cfg",
                "Newtonsoft.Json.dll"  # Our plugin dependency
            ]

            copied_count = 0
            for pattern in vwe_patterns:
                for plugin_file in plugins_source.glob(pattern):
                    if plugin_file.is_file():
                        dest_file = plugins_dest / plugin_file.name
                        shutil.copy2(plugin_file, dest_file)
                        copied_count += 1
                        logger.debug(f"Copied VWE plugin: {plugin_file.name}")

            logger.info(f"Copied {copied_count} VWE plugin files to {plugins_dest}")

            if copied_count == 0:
                logger.warning("No VWE plugins found! Looking for VWE_*.dll files")

        except Exception as e:
            logger.error(f"Failed to setup BepInEx plugins: {e}")
            raise

    def _fix_permissions(self, seed_dir: Path) -> None:
        """
        Fix file ownership after Docker container creates files as root

        Args:
            seed_dir: Root directory for seed data
        """
        try:
            # Get current user's UID/GID
            uid = os.getuid()
            gid = os.getgid()

            logger.debug(f"Fixing permissions: uid={uid}, gid={gid}")

            # Recursively chown all files in seed directory
            for root, dirs, files in os.walk(seed_dir):
                for d in dirs:
                    path = os.path.join(root, d)
                    try:
                        os.chown(path, uid, gid)
                    except Exception:
                        pass
                for f in files:
                    path = os.path.join(root, f)
                    try:
                        os.chown(path, uid, gid)
                    except Exception:
                        pass

            # Fix root directory
            try:
                os.chown(seed_dir, uid, gid)
            except Exception:
                pass

            logger.info(f"Fixed permissions for {seed_dir}")

        except Exception as e:
            logger.warning(f"Failed to fix permissions: {e}")

    def cleanup_old_containers(self, max_age_hours: int = 24) -> int:
        """
        Cleanup old VWE containers

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of containers removed
        """
        logger.info(f"Cleaning up containers older than {max_age_hours}h")

        filters = {"label": "vwe.generator=bepinex-gen1"}
        containers = self.docker_client.containers.list(all=True, filters=filters)

        removed_count = 0

        for container in containers:
            try:
                created = datetime.fromisoformat(
                    container.attrs["Created"].rstrip("Z")
                )
                age_hours = (datetime.utcnow() - created).total_seconds() / 3600

                if age_hours > max_age_hours:
                    logger.info(f"Removing old container: {container.name}")
                    container.remove(force=True)
                    removed_count += 1

            except Exception as e:
                logger.error(f"Error cleaning up container {container.name}: {e}")

        logger.info(f"Removed {removed_count} old containers")
        return removed_count
