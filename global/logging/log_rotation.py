#!/usr/bin/env python3
"""
Log Rotation Manager for Valheim World Engine
Manages log rotation, cleanup, and archival with proper hygiene
"""

import os
import gzip
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .vwe_logger import VWELogger, LogLevel


@dataclass
class RotationConfig:
    """Log rotation configuration"""
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    max_files: int = 10
    retention_days: int = 30
    compress_old_logs: bool = True
    archive_old_logs: bool = True
    archive_dir: str = "/var/log/vwe/archived"
    cleanup_schedule: str = "daily"  # daily, weekly, hourly


class LogRotationManager:
    """Manages log rotation, compression, and cleanup"""
    
    def __init__(self, config: Optional[RotationConfig] = None):
        self.config = config or RotationConfig()
        
        # Setup VWE logger
        self.logger = VWELogger("log-rotation-manager", context={
            "component": "log-rotation",
            "config": asdict(self.config)
        })
        
        # Create archive directory
        Path(self.config.archive_dir).mkdir(parents=True, exist_ok=True)
    
    def rotate_log_file(self, log_file_path: str) -> bool:
        """Rotate a specific log file"""
        try:
            log_file = Path(log_file_path)
            
            if not log_file.exists():
                self.logger.warn("Log file does not exist", file_path=log_file_path)
                return False
            
            # Check if rotation is needed
            if log_file.stat().st_size < self.config.max_file_size:
                return False
            
            # Create rotated filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            rotated_file = log_file.parent / f"{log_file.stem}_{timestamp}.log"
            
            # Move current log to rotated file
            shutil.move(str(log_file), str(rotated_file))
            
            # Create new empty log file
            log_file.touch()
            
            # Compress if configured
            if self.config.compress_old_logs:
                self._compress_log_file(rotated_file)
            
            self.logger.info("Rotated log file", 
                           original_file=log_file_path,
                           rotated_file=str(rotated_file),
                           size=rotated_file.stat().st_size)
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to rotate log file", 
                            file_path=log_file_path,
                            error=str(e))
            return False
    
    def _compress_log_file(self, log_file: Path):
        """Compress a log file with gzip"""
        try:
            compressed_file = log_file.with_suffix('.log.gz')
            
            with open(log_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            log_file.unlink()
            
            self.logger.info("Compressed log file", 
                           original=str(log_file),
                           compressed=str(compressed_file))
            
        except Exception as e:
            self.logger.error("Failed to compress log file", 
                            file_path=str(log_file),
                            error=str(e))
    
    def cleanup_old_logs(self, log_directory: str) -> Dict[str, Any]:
        """Clean up old log files based on retention policy"""
        try:
            log_dir = Path(log_directory)
            cutoff_date = datetime.utcnow() - timedelta(days=self.config.retention_days)
            
            stats = {
                "files_removed": 0,
                "size_freed": 0,
                "files_archived": 0,
                "errors": []
            }
            
            # Find all log files
            log_files = list(log_dir.rglob("*.log")) + list(log_dir.rglob("*.log.gz"))
            
            for log_file in log_files:
                try:
                    # Check if file is old enough to clean up
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    
                    if file_mtime < cutoff_date:
                        file_size = log_file.stat().st_size
                        
                        if self.config.archive_old_logs:
                            # Archive the file
                            self._archive_log_file(log_file)
                            stats["files_archived"] += 1
                        else:
                            # Remove the file
                            log_file.unlink()
                            stats["files_removed"] += 1
                        
                        stats["size_freed"] += file_size
                        
                except Exception as e:
                    error_msg = f"Failed to process {log_file}: {e}"
                    stats["errors"].append(error_msg)
                    self.logger.error("Error processing log file", 
                                    file_path=str(log_file),
                                    error=str(e))
            
            self.logger.info("Cleaned up old logs", 
                           directory=log_directory,
                           files_removed=stats["files_removed"],
                           files_archived=stats["files_archived"],
                           size_freed=stats["size_freed"])
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to cleanup old logs", 
                            directory=log_directory,
                            error=str(e))
            return {"error": str(e)}
    
    def _archive_log_file(self, log_file: Path):
        """Archive a log file to the archive directory"""
        try:
            # Create archive subdirectory by date
            archive_date = datetime.fromtimestamp(log_file.stat().st_mtime).strftime("%Y/%m/%d")
            archive_subdir = Path(self.config.archive_dir) / archive_date
            archive_subdir.mkdir(parents=True, exist_ok=True)
            
            # Move file to archive
            archive_file = archive_subdir / log_file.name
            shutil.move(str(log_file), str(archive_file))
            
            self.logger.info("Archived log file", 
                           original=str(log_file),
                           archived=str(archive_file))
            
        except Exception as e:
            self.logger.error("Failed to archive log file", 
                            file_path=str(log_file),
                            error=str(e))
    
    def get_log_statistics(self, log_directory: str) -> Dict[str, Any]:
        """Get statistics about log files in a directory"""
        try:
            log_dir = Path(log_directory)
            
            stats = {
                "total_files": 0,
                "total_size": 0,
                "compressed_files": 0,
                "uncompressed_files": 0,
                "oldest_file": None,
                "newest_file": None,
                "file_types": {}
            }
            
            # Find all log files
            log_files = list(log_dir.rglob("*.log")) + list(log_dir.rglob("*.log.gz"))
            
            for log_file in log_files:
                try:
                    file_size = log_file.stat().st_size
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    
                    stats["total_files"] += 1
                    stats["total_size"] += file_size
                    
                    # Track file types
                    file_type = "compressed" if log_file.suffix == ".gz" else "uncompressed"
                    stats["file_types"][file_type] = stats["file_types"].get(file_type, 0) + 1
                    
                    if file_type == "compressed":
                        stats["compressed_files"] += 1
                    else:
                        stats["uncompressed_files"] += 1
                    
                    # Track oldest and newest files
                    if stats["oldest_file"] is None or file_mtime < stats["oldest_file"]:
                        stats["oldest_file"] = file_mtime.isoformat()
                    
                    if stats["newest_file"] is None or file_mtime > stats["newest_file"]:
                        stats["newest_file"] = file_mtime.isoformat()
                        
                except Exception as e:
                    self.logger.warn("Failed to process log file for stats", 
                                   file_path=str(log_file),
                                   error=str(e))
            
            # Convert sizes to human readable
            stats["total_size_mb"] = round(stats["total_size"] / (1024 * 1024), 2)
            stats["total_size_gb"] = round(stats["total_size"] / (1024 * 1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get log statistics", 
                            directory=log_directory,
                            error=str(e))
            return {"error": str(e)}
    
    def schedule_cleanup(self, log_directories: List[str]):
        """Schedule cleanup for multiple log directories"""
        try:
            total_stats = {
                "directories_processed": 0,
                "total_files_removed": 0,
                "total_files_archived": 0,
                "total_size_freed": 0,
                "errors": []
            }
            
            for log_dir in log_directories:
                try:
                    stats = self.cleanup_old_logs(log_dir)
                    
                    if "error" in stats:
                        total_stats["errors"].append(f"{log_dir}: {stats['error']}")
                    else:
                        total_stats["directories_processed"] += 1
                        total_stats["total_files_removed"] += stats["files_removed"]
                        total_stats["total_files_archived"] += stats["files_archived"]
                        total_stats["total_size_freed"] += stats["size_freed"]
                        
                except Exception as e:
                    error_msg = f"{log_dir}: {e}"
                    total_stats["errors"].append(error_msg)
                    self.logger.error("Failed to cleanup directory", 
                                    directory=log_dir,
                                    error=str(e))
            
            self.logger.info("Scheduled cleanup completed", 
                           directories_processed=total_stats["directories_processed"],
                           total_files_removed=total_stats["total_files_removed"],
                           total_files_archived=total_stats["total_files_archived"],
                           total_size_freed=total_stats["total_size_freed"])
            
            return total_stats
            
        except Exception as e:
            self.logger.error("Failed to schedule cleanup", error=str(e))
            return {"error": str(e)}


def main():
    """Example usage of log rotation manager"""
    
    # Create rotation manager
    rotation_manager = LogRotationManager()
    
    # Get log statistics
    stats = rotation_manager.get_log_statistics("/var/log/vwe")
    print(f"Log statistics: {stats}")
    
    # Cleanup old logs
    cleanup_stats = rotation_manager.cleanup_old_logs("/var/log/vwe")
    print(f"Cleanup results: {cleanup_stats}")
    
    # Schedule cleanup for multiple directories
    directories = ["/var/log/vwe/docker", "/var/log/vwe/generators", "/var/log/vwe/backend"]
    scheduled_stats = rotation_manager.schedule_cleanup(directories)
    print(f"Scheduled cleanup results: {scheduled_stats}")


if __name__ == "__main__":
    main()
