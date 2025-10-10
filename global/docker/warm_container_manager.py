#!/usr/bin/env python3
"""
Warm Container Manager for Valheim World Engine
Manages pre-warmed containers to eliminate startup delays
"""

import os
import json
import time
import logging
import docker
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict


@dataclass
class WarmContainerConfig:
    """Configuration for warm container management"""
    base_image: str
    container_name_prefix: str
    max_warm_containers: int = 3
    container_ttl_minutes: int = 30
    preload_volumes: bool = True
    preload_environment: bool = True
    auto_cleanup: bool = True


class WarmContainerManager:
    """Manages warm containers for instant deployment"""
    
    def __init__(self, docker_client: docker.DockerClient = None):
        self.docker_client = docker_client or docker.from_env()
        self.logger = logging.getLogger(__name__)
        
        # Warm container configurations
        self.configs = {
            "valheim-bepinex": WarmContainerConfig(
                base_image="vwe/valheim-bepinex:latest",
                container_name_prefix="vwe-warm-bepinex",
                max_warm_containers=2,
                container_ttl_minutes=45
            ),
            "valheim-procedural": WarmContainerConfig(
                base_image="vwe/valheim-procedural:latest", 
                container_name_prefix="vwe-warm-procedural",
                max_warm_containers=1,
                container_ttl_minutes=30
            ),
            "worldgen-runner": WarmContainerConfig(
                base_image="vwe/worldgen-runner:latest",
                container_name_prefix="vwe-warm-runner",
                max_warm_containers=3,
                container_ttl_minutes=60
            )
        }
        
        # Track warm containers
        self.warm_containers: Dict[str, List[str]] = {
            config_name: [] for config_name in self.configs.keys()
        }
        
        # Container metadata
        self.container_metadata: Dict[str, Dict[str, Any]] = {}
    
    def create_warm_container(self, config_name: str, seed_hash: str = None) -> str:
        """Create a new warm container ready for instant deployment"""
        if config_name not in self.configs:
            raise ValueError(f"Unknown config: {config_name}")
        
        config = self.configs[config_name]
        
        # Check if we already have enough warm containers
        if len(self.warm_containers[config_name]) >= config.max_warm_containers:
            self.logger.info(f"Max warm containers reached for {config_name}")
            return self.get_available_container(config_name)
        
        # Generate unique container name
        container_name = f"{config.container_name_prefix}-{int(time.time())}-{seed_hash or 'generic'}"
        
        self.logger.info(f"Creating warm container: {container_name}")
        
        try:
            # Create container with pre-warmed configuration
            container = self.docker_client.containers.create(
                image=config.base_image,
                name=container_name,
                detach=True,
                environment=self._get_preload_environment(config_name),
                volumes=self._get_preload_volumes(config_name),
                command=["sleep", "infinity"],  # Keep container alive
                labels={
                    "vwe.type": "warm-container",
                    "vwe.config": config_name,
                    "vwe.created": datetime.utcnow().isoformat(),
                    "vwe.status": "warming"
                }
            )
            
            # Start the container
            container.start()
            
            # Wait for container to be ready
            self._wait_for_container_ready(container)
            
            # Pre-warm the container
            self._prewarm_container(container, config_name)
            
            # Track the container
            self.warm_containers[config_name].append(container_name)
            self.container_metadata[container_name] = {
                "config_name": config_name,
                "created_at": datetime.utcnow().isoformat(),
                "last_used": datetime.utcnow().isoformat(),
                "status": "ready"
            }
            
            self.logger.info(f"Warm container ready: {container_name}")
            return container_name
            
        except Exception as e:
            self.logger.error(f"Failed to create warm container {container_name}: {e}")
            # Cleanup on failure
            try:
                container.remove(force=True)
            except:
                pass
            raise
    
    def get_available_container(self, config_name: str) -> Optional[str]:
        """Get an available warm container for immediate use"""
        if not self.warm_containers[config_name]:
            self.logger.info(f"No warm containers available for {config_name}, creating new one")
            return self.create_warm_container(config_name)
        
        # Find the oldest available container
        available_containers = []
        for container_name in self.warm_containers[config_name]:
            try:
                container = self.docker_client.containers.get(container_name)
                if container.status == "running":
                    available_containers.append((container_name, container.attrs['Created']))
            except docker.errors.NotFound:
                # Container was removed, clean up tracking
                self.warm_containers[config_name].remove(container_name)
                if container_name in self.container_metadata:
                    del self.container_metadata[container_name]
        
        if not available_containers:
            return self.create_warm_container(config_name)
        
        # Return the oldest container
        available_containers.sort(key=lambda x: x[1])
        container_name = available_containers[0][0]
        
        # Update last used time
        if container_name in self.container_metadata:
            self.container_metadata[container_name]["last_used"] = datetime.utcnow().isoformat()
        
        return container_name
    
    def clone_container_for_job(self, config_name: str, seed_hash: str, job_id: str) -> str:
        """Clone a warm container for a specific job"""
        warm_container_name = self.get_available_container(config_name)
        
        # Create job-specific container name
        job_container_name = f"vwe-job-{job_id}-{seed_hash}"
        
        self.logger.info(f"Cloning warm container {warm_container_name} to {job_container_name}")
        
        try:
            # Get the warm container
            warm_container = self.docker_client.containers.get(warm_container_name)
            
            # Create new container from the same image with job-specific config
            job_container = self.docker_client.containers.create(
                image=warm_container.image,
                name=job_container_name,
                detach=True,
                environment=self._get_job_environment(config_name, seed_hash, job_id),
                volumes=self._get_job_volumes(config_name, seed_hash),
                command=self._get_job_command(config_name, seed_hash),
                labels={
                    "vwe.type": "job-container",
                    "vwe.config": config_name,
                    "vwe.seed_hash": seed_hash,
                    "vwe.job_id": job_id,
                    "vwe.cloned_from": warm_container_name,
                    "vwe.created": datetime.utcnow().isoformat()
                }
            )
            
            # Start the job container
            job_container.start()
            
            self.logger.info(f"Job container started: {job_container_name}")
            return job_container_name
            
        except Exception as e:
            self.logger.error(f"Failed to clone container for job {job_id}: {e}")
            raise
    
    def _get_preload_environment(self, config_name: str) -> Dict[str, str]:
        """Get environment variables for preloading containers"""
        base_env = {
            "TZ": "UTC",
            "VWE_WARM_CONTAINER": "true",
            "VWE_PRELOADED": "true"
        }
        
        if config_name == "valheim-bepinex":
            return {
                **base_env,
                "BEPINEX": "1",
                "VWE_AUTOSAVE_ENABLED": "true",
                "VWE_DATAEXPORT_ENABLED": "true",
                "SERVER_PUBLIC": "0",
                "UPDATE_ON_START": "0"  # Skip updates in warm containers
            }
        elif config_name == "valheim-procedural":
            return {
                **base_env,
                "VWE_PROCEDURAL_ENABLED": "true",
                "BEPINEX": "1",
                "SERVER_PUBLIC": "0",
                "UPDATE_ON_START": "0"
            }
        elif config_name == "worldgen-runner":
            return {
                **base_env,
                "VALHEIM_APPID": "896660",
                "UPDATE_ON_START": "0"
            }
        
        return base_env
    
    def _get_preload_volumes(self, config_name: str) -> Dict[str, Dict[str, str]]:
        """Get volumes for preloading containers"""
        # Create temporary directories for preloading
        temp_dir = Path("/tmp/vwe-warm-containers")
        temp_dir.mkdir(exist_ok=True)
        
        volumes = {
            str(temp_dir / "warm"): {"bind": "/config", "mode": "rw"}
        }
        
        if config_name in ["valheim-bepinex", "valheim-procedural"]:
            # Mount plugin directories for preloading
            volumes.update({
                "/tmp/vwe-warm-plugins": {"bind": "/config/bepinex/plugins", "mode": "ro"}
            })
        
        return volumes
    
    def _get_job_environment(self, config_name: str, seed_hash: str, job_id: str) -> Dict[str, str]:
        """Get environment variables for job containers"""
        base_env = self._get_preload_environment(config_name)
        
        # Override with job-specific values
        job_env = {
            **base_env,
            "VWE_WARM_CONTAINER": "false",
            "VWE_JOB_ID": job_id,
            "WORLD_NAME": seed_hash,
            "WORLD_SEED": seed_hash,  # Assuming seed_hash is the actual seed
            "UPDATE_ON_START": "1"  # Enable updates for job containers
        }
        
        return job_env
    
    def _get_job_volumes(self, config_name: str, seed_hash: str) -> Dict[str, Dict[str, str]]:
        """Get volumes for job containers"""
        data_dir = Path(f"/home/steve/projects/valheim-world-engine/data/seeds/{seed_hash}")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        volumes = {
            str(data_dir): {"bind": "/config", "mode": "rw"}
        }
        
        if config_name in ["valheim-bepinex", "valheim-procedural"]:
            # Mount actual plugin directories
            plugin_dir = Path("/home/steve/projects/valheim-world-engine/etl/stable/bepinex/plugins")
            if plugin_dir.exists():
                volumes[str(plugin_dir)] = {"bind": "/config/bepinex/plugins", "mode": "ro"}
        
        return volumes
    
    def _get_job_command(self, config_name: str, seed_hash: str) -> List[str]:
        """Get command for job containers"""
        if config_name in ["valheim-bepinex", "valheim-procedural"]:
            return ["valheim-server"]
        elif config_name == "worldgen-runner":
            return ["bash", "-c", "echo 'Worldgen runner ready' && sleep infinity"]
        
        return ["sleep", "infinity"]
    
    def _wait_for_container_ready(self, container, timeout: int = 60) -> None:
        """Wait for container to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                container.reload()
                if container.status == "running":
                    # Check if container is actually ready
                    logs = container.logs().decode('utf-8')
                    if "ready" in logs.lower() or "started" in logs.lower():
                        return
                time.sleep(1)
            except Exception as e:
                self.logger.warning(f"Error checking container readiness: {e}")
                time.sleep(1)
        
        self.logger.warning(f"Container {container.name} may not be fully ready after {timeout}s")
    
    def _prewarm_container(self, container, config_name: str) -> None:
        """Pre-warm the container by running initialization commands"""
        try:
            if config_name in ["valheim-bepinex", "valheim-procedural"]:
                # Pre-warm Valheim server
                container.exec_run("echo 'Pre-warming Valheim server...'")
                # Could add more pre-warming commands here
                
            elif config_name == "worldgen-runner":
                # Pre-warm worldgen runner
                container.exec_run("echo 'Pre-warming worldgen runner...'")
                
        except Exception as e:
            self.logger.warning(f"Pre-warming failed for {container.name}: {e}")
    
    def cleanup_expired_containers(self) -> None:
        """Clean up expired warm containers"""
        current_time = datetime.utcnow()
        
        for config_name, container_names in self.warm_containers.items():
            config = self.configs[config_name]
            containers_to_remove = []
            
            for container_name in container_names:
                if container_name not in self.container_metadata:
                    containers_to_remove.append(container_name)
                    continue
                
                metadata = self.container_metadata[container_name]
                created_at = datetime.fromisoformat(metadata["created_at"])
                age_minutes = (current_time - created_at).total_seconds() / 60
                
                if age_minutes > config.container_ttl_minutes:
                    containers_to_remove.append(container_name)
            
            # Remove expired containers
            for container_name in containers_to_remove:
                try:
                    container = self.docker_client.containers.get(container_name)
                    container.stop()
                    container.remove()
                    self.logger.info(f"Cleaned up expired warm container: {container_name}")
                except docker.errors.NotFound:
                    pass
                except Exception as e:
                    self.logger.error(f"Failed to cleanup container {container_name}: {e}")
                
                # Remove from tracking
                if container_name in self.warm_containers[config_name]:
                    self.warm_containers[config_name].remove(container_name)
                if container_name in self.container_metadata:
                    del self.container_metadata[container_name]
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of warm container manager"""
        status = {
            "warm_containers": {},
            "total_containers": 0,
            "configs": {}
        }
        
        for config_name, container_names in self.warm_containers.items():
            config = self.configs[config_name]
            running_containers = []
            
            for container_name in container_names:
                try:
                    container = self.docker_client.containers.get(container_name)
                    if container.status == "running":
                        running_containers.append({
                            "name": container_name,
                            "status": container.status,
                            "created": container.attrs['Created'],
                            "metadata": self.container_metadata.get(container_name, {})
                        })
                except docker.errors.NotFound:
                    pass
            
            status["warm_containers"][config_name] = {
                "running": running_containers,
                "count": len(running_containers),
                "max_allowed": config.max_warm_containers
            }
            status["total_containers"] += len(running_containers)
        
        # Add config information
        for config_name, config in self.configs.items():
            status["configs"][config_name] = asdict(config)
        
        return status
    
    def start_warm_container_service(self) -> None:
        """Start the warm container service (background maintenance)"""
        self.logger.info("Starting warm container service")
        
        # Create initial warm containers
        for config_name in self.configs.keys():
            try:
                self.create_warm_container(config_name)
                self.logger.info(f"Created initial warm container for {config_name}")
            except Exception as e:
                self.logger.error(f"Failed to create initial warm container for {config_name}: {e}")
        
        # Start cleanup loop
        import threading
        
        def cleanup_loop():
            while True:
                try:
                    self.cleanup_expired_containers()
                    time.sleep(300)  # Cleanup every 5 minutes
                except Exception as e:
                    self.logger.error(f"Error in cleanup loop: {e}")
                    time.sleep(60)
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        
        self.logger.info("Warm container service started")


def main():
    """Example usage of warm container manager"""
    manager = WarmContainerManager()
    
    # Start the service
    manager.start_warm_container_service()
    
    # Get status
    status = manager.get_status()
    print("Warm Container Status:")
    print(json.dumps(status, indent=2, default=str))
    
    # Example: Clone container for a job
    job_container = manager.clone_container_for_job("valheim-bepinex", "test-seed-123", "job-456")
    print(f"Created job container: {job_container}")


if __name__ == "__main__":
    main()
