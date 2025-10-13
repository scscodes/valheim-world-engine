#!/usr/bin/env python3
"""
Warm Container Service Startup Script
Starts persistent warm containers for development session
"""

import sys
import time
import signal
import logging
from pathlib import Path

# Add global docker to path
sys.path.append(str(Path(__file__).parent.parent / "global" / "docker"))

from warm_container_manager import WarmContainerManager
import docker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WarmContainerService:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.warm_manager = WarmContainerManager(self.docker_client)
        self.running = False
        
    def start(self):
        """Start the warm container service"""
        logger.info("Starting Warm Container Service...")
        
        try:
            # Start the warm container service
            self.warm_manager.start_warm_container_service()
            
            # Wait for containers to be ready
            logger.info("Waiting for warm containers to be ready...")
            time.sleep(10)
            
            # Check status
            status = self.warm_manager.get_status()
            logger.info(f"Warm container service started successfully!")
            logger.info(f"Total containers: {status['total_containers']}")
            
            for config_name, config_status in status['warm_containers'].items():
                logger.info(f"  {config_name}: {config_status['count']} containers")
                for container in config_status['running']:
                    logger.info(f"    - {container['name']} ({container['status']})")
            
            self.running = True
            
            # Keep service running
            logger.info("Warm container service is running. Press Ctrl+C to stop.")
            while self.running:
                time.sleep(30)
                # Periodic health check
                try:
                    status = self.warm_manager.get_status()
                    if status['total_containers'] == 0:
                        logger.warning("No warm containers available, restarting service...")
                        self.warm_manager.start_warm_container_service()
                        time.sleep(10)
                except Exception as e:
                    logger.error(f"Health check failed: {e}")
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Failed to start warm container service: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the warm container service"""
        logger.info("Stopping Warm Container Service...")
        self.running = False
        
        try:
            # Clean up job containers
            self.warm_manager.cleanup_all_job_containers()
            logger.info("Warm container service stopped")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    logger.info("Received signal, shutting down...")
    sys.exit(0)

def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the service
    service = WarmContainerService()
    service.start()

if __name__ == "__main__":
    main()
