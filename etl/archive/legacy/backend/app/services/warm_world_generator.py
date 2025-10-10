"""
Warm World Generator Service
Uses pre-warmed containers for instant world generation without startup delays
"""

import os
import time
import logging
import docker
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add global docker package to path
import sys
sys.path.append('/home/steve/projects/valheim-world-engine/global/docker')

from warm_container_manager import WarmContainerManager


class WarmWorldGenerator:
    """World generator using warm containers for instant deployment"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.warm_manager = WarmContainerManager(self.docker_client)
        self.logger = logging.getLogger(__name__)
        
        # Start warm container service
        self.warm_manager.start_warm_container_service()
    
    def generate_world_warm(self, seed: str, seed_hash: str, 
                          approach: str = "bepinex") -> Dict[str, Any]:
        """Generate world using warm container for instant deployment"""
        
        self.logger.info(f"Generating world with warm container: {seed} ({approach})")
        
        # Map approach to container config
        config_mapping = {
            "bepinex": "valheim-bepinex",
            "procedural": "valheim-procedural", 
            "worldgen": "worldgen-runner"
        }
        
        if approach not in config_mapping:
            raise ValueError(f"Unknown approach: {approach}. Available: {list(config_mapping.keys())}")
        
        config_name = config_mapping[approach]
        job_id = f"job-{int(time.time())}-{seed_hash[:8]}"
        
        try:
            # Clone warm container for this job
            job_container_name = self.warm_manager.clone_container_for_job(
                config_name, seed_hash, job_id
            )
            
            self.logger.info(f"Created job container: {job_container_name}")
            
            # Monitor the job
            result = self._monitor_world_generation(job_container_name, seed_hash)
            
            # Clean up job container
            self._cleanup_job_container(job_container_name)
            
            return result
            
        except Exception as e:
            self.logger.error(f"World generation failed: {e}")
            # Cleanup on error
            try:
                self._cleanup_job_container(job_container_name)
            except:
                pass
            raise
    
    def _monitor_world_generation(self, container_name: str, seed_hash: str) -> Dict[str, Any]:
        """Monitor world generation progress"""
        
        container = self.docker_client.containers.get(container_name)
        start_time = time.time()
        timeout = 300  # 5 minutes timeout
        
        self.logger.info(f"Monitoring world generation in {container_name}")
        
        # Wait for completion signals
        while time.time() - start_time < timeout:
            try:
                container.reload()
                
                if container.status != "running":
                    self.logger.warning(f"Container {container_name} stopped unexpectedly")
                    break
                
                # Check logs for completion signals
                logs = container.logs().decode('utf-8')
                
                if self._check_completion_signals(logs):
                    self.logger.info(f"World generation completed in {container_name}")
                    break
                
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error monitoring container {container_name}: {e}")
                time.sleep(5)
        
        # Check if generation completed successfully
        if time.time() - start_time >= timeout:
            self.logger.error(f"World generation timed out for {container_name}")
            return {"success": False, "error": "Generation timeout"}
        
        # Verify output files
        result = self._verify_output_files(seed_hash)
        
        return result
    
    def _check_completion_signals(self, logs: str) -> bool:
        """Check logs for world generation completion signals"""
        completion_signals = [
            "Game server connected",
            "Zonesystem Start", 
            "Export complete",
            "World generation complete",
            "VWE: Export finished"
        ]
        
        for signal in completion_signals:
            if signal in logs:
                return True
        
        return False
    
    def _verify_output_files(self, seed_hash: str) -> Dict[str, Any]:
        """Verify that required output files exist"""
        
        data_dir = Path(f"/home/steve/projects/valheim-world-engine/data/seeds/{seed_hash}")
        
        required_files = [
            "worlds_local",
            "extracted/biomes.json",
            "extracted/heightmap.npy"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = data_dir / file_path
            if not full_path.exists():
                missing_files.append(str(file_path))
        
        if missing_files:
            return {
                "success": False,
                "error": f"Missing required files: {missing_files}"
            }
        
        return {
            "success": True,
            "seed_hash": seed_hash,
            "output_dir": str(data_dir),
            "files": required_files
        }
    
    def _cleanup_job_container(self, container_name: str) -> None:
        """Clean up job container after completion"""
        try:
            container = self.docker_client.containers.get(container_name)
            container.stop()
            container.remove()
            self.logger.info(f"Cleaned up job container: {container_name}")
        except docker.errors.NotFound:
            self.logger.warning(f"Container {container_name} already removed")
        except Exception as e:
            self.logger.error(f"Failed to cleanup container {container_name}: {e}")
    
    def get_warm_container_status(self) -> Dict[str, Any]:
        """Get status of warm container service"""
        return self.warm_manager.get_status()
    
    def create_warm_containers(self, approaches: list = None) -> Dict[str, str]:
        """Create warm containers for specified approaches"""
        if approaches is None:
            approaches = ["bepinex", "procedural", "worldgen"]
        
        results = {}
        for approach in approaches:
            try:
                config_mapping = {
                    "bepinex": "valheim-bepinex",
                    "procedural": "valheim-procedural",
                    "worldgen": "worldgen-runner"
                }
                
                config_name = config_mapping[approach]
                container_name = self.warm_manager.create_warm_container(config_name)
                results[approach] = container_name
                self.logger.info(f"Created warm container for {approach}: {container_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to create warm container for {approach}: {e}")
                results[approach] = f"Error: {e}"
        
        return results


def main():
    """Example usage of warm world generator"""
    generator = WarmWorldGenerator()
    
    # Get status
    status = generator.get_warm_container_status()
    print("Warm Container Status:")
    print(f"Total containers: {status['total_containers']}")
    
    # Create warm containers
    results = generator.create_warm_containers()
    print("\\nCreated warm containers:")
    for approach, container in results.items():
        print(f"  {approach}: {container}")
    
    # Generate a test world
    try:
        result = generator.generate_world_warm("TestSeed", "test-hash-123", "bepinex")
        print(f"\\nWorld generation result: {result}")
    except Exception as e:
        print(f"\\nWorld generation failed: {e}")


if __name__ == "__main__":
    main()
