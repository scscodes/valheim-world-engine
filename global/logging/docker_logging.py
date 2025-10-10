#!/usr/bin/env python3
"""
Docker Logging Manager for Valheim World Engine
Manages Docker container logs with proper rotation, monitoring, and hygiene
"""

import os
import json
import time
import docker
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .vwe_logger import VWELogger, LogConfig, LogLevel, LogFormat


@dataclass
class DockerLogConfig:
    """Docker-specific logging configuration"""
    log_dir: str = "/var/log/vwe/docker"
    max_log_size: int = 50 * 1024 * 1024  # 50MB
    max_log_files: int = 10
    log_retention_days: int = 30
    real_time_logging: bool = True
    structured_logs: bool = True
    include_container_metadata: bool = True
    log_level: LogLevel = LogLevel.INFO


class DockerLogManager:
    """Manages Docker container logging with proper hygiene and monitoring"""
    
    def __init__(self, docker_client: docker.DockerClient = None, 
                 config: Optional[DockerLogConfig] = None):
        self.docker_client = docker_client or docker.from_env()
        self.config = config or DockerLogConfig()
        
        # Setup VWE logger
        self.logger = VWELogger("docker-log-manager", context={
            "component": "docker-logging",
            "log_dir": self.config.log_dir
        })
        
        # Create log directory structure
        self._setup_log_directories()
        
        # Track active log streams
        self.active_streams: Dict[str, Any] = {}
        self.container_metadata: Dict[str, Dict[str, Any]] = {}
    
    def _setup_log_directories(self):
        """Setup Docker log directory structure"""
        log_dir = Path(self.config.log_dir)
        
        # Create main directories
        directories = [
            "containers",      # Individual container logs
            "services",        # Service-level logs
            "orchestration",   # Orchestration logs
            "warm-containers", # Warm container logs
            "archived"         # Archived/rotated logs
        ]
        
        for directory in directories:
            (log_dir / directory).mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Docker log directories created", directories=directories)
    
    def start_container_logging(self, container_name: str, 
                              service_type: str = "unknown") -> bool:
        """Start logging for a specific container"""
        try:
            container = self.docker_client.containers.get(container_name)
            
            # Get container metadata
            metadata = self._get_container_metadata(container)
            self.container_metadata[container_name] = metadata
            
            # Create log file path
            log_file = self._get_container_log_path(container_name, service_type)
            
            # Start log stream
            log_stream = container.logs(
                stream=True,
                follow=True,
                timestamps=True,
                tail=0
            )
            
            # Store stream info
            self.active_streams[container_name] = {
                "stream": log_stream,
                "log_file": log_file,
                "service_type": service_type,
                "started_at": datetime.utcnow().isoformat(),
                "metadata": metadata
            }
            
            # Start background logging thread
            import threading
            log_thread = threading.Thread(
                target=self._log_container_stream,
                args=(container_name, log_stream, log_file),
                daemon=True
            )
            log_thread.start()
            
            self.logger.info("Started container logging", 
                           container_name=container_name,
                           service_type=service_type,
                           log_file=str(log_file))
            
            return True
            
        except docker.errors.NotFound:
            self.logger.error("Container not found", container_name=container_name)
            return False
        except Exception as e:
            self.logger.error("Failed to start container logging", 
                            container_name=container_name, error=str(e))
            return False
    
    def stop_container_logging(self, container_name: str) -> bool:
        """Stop logging for a specific container"""
        try:
            if container_name in self.active_streams:
                stream_info = self.active_streams[container_name]
                
                # Close the stream
                if hasattr(stream_info["stream"], 'close'):
                    stream_info["stream"].close()
                
                # Remove from active streams
                del self.active_streams[container_name]
                
                # Archive the log file
                self._archive_container_log(container_name, stream_info["log_file"])
                
                self.logger.info("Stopped container logging", container_name=container_name)
                return True
            else:
                self.logger.warn("Container not being logged", container_name=container_name)
                return False
                
        except Exception as e:
            self.logger.error("Failed to stop container logging", 
                            container_name=container_name, error=str(e))
            return False
    
    def _log_container_stream(self, container_name: str, stream, log_file: Path):
        """Background thread to process container log stream"""
        try:
            with open(log_file, 'w') as f:
                for line in stream:
                    if line:
                        # Decode and process log line
                        log_line = line.decode('utf-8').strip()
                        
                        if self.config.structured_logs:
                            # Create structured log entry
                            structured_log = self._create_structured_log_entry(
                                container_name, log_line
                            )
                            f.write(json.dumps(structured_log) + '\n')
                        else:
                            # Write raw log line
                            f.write(f"{datetime.utcnow().isoformat()} | {log_line}\n")
                        
                        f.flush()
                        
                        # Check for log rotation
                        if log_file.stat().st_size > self.config.max_log_size:
                            self._rotate_container_log(container_name, log_file)
                            
        except Exception as e:
            self.logger.error("Error in container log stream", 
                            container_name=container_name, error=str(e))
    
    def _create_structured_log_entry(self, container_name: str, log_line: str) -> Dict[str, Any]:
        """Create structured log entry for container log"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "container_name": container_name,
            "log_line": log_line,
            "service_type": self.active_streams.get(container_name, {}).get("service_type", "unknown")
        }
        
        # Add container metadata if available
        if container_name in self.container_metadata:
            entry["container_metadata"] = self.container_metadata[container_name]
        
        # Parse Docker log format if possible
        if " | " in log_line:
            parts = log_line.split(" | ", 1)
            if len(parts) == 2:
                entry["docker_timestamp"] = parts[0]
                entry["message"] = parts[1]
            else:
                entry["message"] = log_line
        else:
            entry["message"] = log_line
        
        return entry
    
    def _get_container_metadata(self, container) -> Dict[str, Any]:
        """Extract metadata from container"""
        try:
            attrs = container.attrs
            return {
                "id": attrs.get("Id", ""),
                "image": attrs.get("Config", {}).get("Image", ""),
                "created": attrs.get("Created", ""),
                "status": attrs.get("State", {}).get("Status", ""),
                "labels": attrs.get("Config", {}).get("Labels", {}),
                "environment": attrs.get("Config", {}).get("Env", []),
                "ports": attrs.get("NetworkSettings", {}).get("Ports", {}),
                "mounts": attrs.get("Mounts", [])
            }
        except Exception as e:
            self.logger.warn("Failed to extract container metadata", error=str(e))
            return {"id": container.id, "error": str(e)}
    
    def _get_container_log_path(self, container_name: str, service_type: str) -> Path:
        """Get log file path for container"""
        log_dir = Path(self.config.log_dir)
        
        # Create service-specific directory
        service_dir = log_dir / "containers" / service_type
        service_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        log_file = service_dir / f"{container_name}_{timestamp}.log"
        
        return log_file
    
    def _rotate_container_log(self, container_name: str, log_file: Path):
        """Rotate container log file when it gets too large"""
        try:
            # Create rotated filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            rotated_file = log_file.parent / f"{log_file.stem}_rotated_{timestamp}.log"
            
            # Move current log to rotated file
            log_file.rename(rotated_file)
            
            # Create new log file
            new_log_file = log_file.parent / f"{container_name}_{timestamp}.log"
            new_log_file.touch()
            
            # Update active stream
            if container_name in self.active_streams:
                self.active_streams[container_name]["log_file"] = new_log_file
            
            self.logger.info("Rotated container log", 
                           container_name=container_name,
                           old_file=str(rotated_file),
                           new_file=str(new_log_file))
            
        except Exception as e:
            self.logger.error("Failed to rotate container log", 
                            container_name=container_name, error=str(e))
    
    def _archive_container_log(self, container_name: str, log_file: Path):
        """Archive container log when logging stops"""
        try:
            if not log_file.exists():
                return
            
            # Create archive directory
            archive_dir = Path(self.config.log_dir) / "archived" / container_name
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Move log file to archive
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            archived_file = archive_dir / f"{log_file.name}_{timestamp}.log"
            log_file.rename(archived_file)
            
            self.logger.info("Archived container log", 
                           container_name=container_name,
                           archived_file=str(archived_file))
            
        except Exception as e:
            self.logger.error("Failed to archive container log", 
                            container_name=container_name, error=str(e))
    
    def get_container_logs(self, container_name: str, 
                          lines: int = 100, 
                          since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get recent logs for a container"""
        try:
            container = self.docker_client.containers.get(container_name)
            
            # Get logs from Docker
            logs = container.logs(
                timestamps=True,
                tail=lines,
                since=since
            )
            
            # Parse logs
            parsed_logs = []
            for line in logs.decode('utf-8').split('\n'):
                if line.strip():
                    if self.config.structured_logs:
                        try:
                            log_entry = json.loads(line)
                            parsed_logs.append(log_entry)
                        except json.JSONDecodeError:
                            # Fallback to simple parsing
                            parsed_logs.append({
                                "timestamp": datetime.utcnow().isoformat(),
                                "message": line,
                                "container_name": container_name
                            })
                    else:
                        parsed_logs.append({
                            "timestamp": datetime.utcnow().isoformat(),
                            "message": line,
                            "container_name": container_name
                        })
            
            return parsed_logs
            
        except Exception as e:
            self.logger.error("Failed to get container logs", 
                            container_name=container_name, error=str(e))
            return []
    
    def cleanup_old_logs(self):
        """Clean up old log files based on retention policy"""
        try:
            log_dir = Path(self.config.log_dir)
            cutoff_date = datetime.utcnow() - timedelta(days=self.config.log_retention_days)
            
            cleaned_files = 0
            cleaned_size = 0
            
            # Clean up archived logs
            for archived_file in log_dir.rglob("*.log"):
                if archived_file.stat().st_mtime < cutoff_date.timestamp():
                    file_size = archived_file.stat().st_size
                    archived_file.unlink()
                    cleaned_files += 1
                    cleaned_size += file_size
            
            self.logger.info("Cleaned up old logs", 
                           files_removed=cleaned_files,
                           size_freed=cleaned_size)
            
        except Exception as e:
            self.logger.error("Failed to cleanup old logs", error=str(e))
    
    def get_logging_status(self) -> Dict[str, Any]:
        """Get status of Docker logging system"""
        return {
            "active_streams": len(self.active_streams),
            "containers": list(self.active_streams.keys()),
            "log_directory": self.config.log_dir,
            "config": asdict(self.config),
            "total_log_files": len(list(Path(self.config.log_dir).rglob("*.log")))
        }


def main():
    """Example usage of Docker log manager"""
    
    # Create Docker log manager
    log_manager = DockerLogManager()
    
    # Start logging for a container
    container_name = "vwe-valheim-bepinex"
    success = log_manager.start_container_logging(container_name, "valheim-server")
    
    if success:
        print(f"Started logging for {container_name}")
        
        # Wait a bit for logs
        time.sleep(5)
        
        # Get recent logs
        logs = log_manager.get_container_logs(container_name, lines=10)
        print(f"Recent logs: {len(logs)} entries")
        
        # Stop logging
        log_manager.stop_container_logging(container_name)
        print(f"Stopped logging for {container_name}")
    
    # Get status
    status = log_manager.get_logging_status()
    print(f"Logging status: {status}")


if __name__ == "__main__":
    main()
