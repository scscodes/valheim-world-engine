#!/usr/bin/env python3
"""
Generator Logging Manager for Valheim World Engine
Manages logging for code generators with structured output and progress tracking
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict

from .vwe_logger import VWELogger, LogConfig, LogLevel, LogFormat


@dataclass
class GeneratorLogConfig:
    """Generator-specific logging configuration"""
    log_dir: str = "/var/log/vwe/generators"
    max_log_size: int = 25 * 1024 * 1024  # 25MB
    max_log_files: int = 5
    log_retention_days: int = 14
    structured_logs: bool = True
    progress_tracking: bool = True
    operation_tracking: bool = True
    log_level: LogLevel = LogLevel.INFO


class GeneratorLogManager:
    """Manages logging for code generators with progress and operation tracking"""
    
    def __init__(self, generator_name: str, config: Optional[GeneratorLogConfig] = None):
        self.generator_name = generator_name
        self.config = config or GeneratorLogConfig()
        
        # Setup VWE logger
        self.logger = VWELogger(f"generator-{generator_name}", context={
            "component": "generator",
            "generator_name": generator_name,
            "log_dir": self.config.log_dir
        })
        
        # Create log directory structure
        self._setup_log_directories()
        
        # Track operations and progress
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.operation_history: List[Dict[str, Any]] = []
    
    def _setup_log_directories(self):
        """Setup generator log directory structure"""
        log_dir = Path(self.config.log_dir)
        
        # Create generator-specific directories
        directories = [
            "operations",      # Individual operation logs
            "progress",        # Progress tracking logs
            "errors",          # Error logs
            "performance",     # Performance metrics
            "archived"         # Archived logs
        ]
        
        for directory in directories:
            (log_dir / self.generator_name / directory).mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Generator log directories created", 
                        generator=self.generator_name,
                        directories=directories)
    
    def start_operation(self, operation_id: str, operation_type: str, 
                       parameters: Dict[str, Any] = None) -> bool:
        """Start tracking a generator operation"""
        try:
            operation = {
                "operation_id": operation_id,
                "operation_type": operation_type,
                "parameters": parameters or {},
                "started_at": datetime.utcnow().isoformat(),
                "status": "running",
                "progress": 0,
                "steps_completed": 0,
                "total_steps": 0,
                "errors": [],
                "warnings": [],
                "files_created": [],
                "performance_metrics": {}
            }
            
            self.active_operations[operation_id] = operation
            
            self.logger.info("Started generator operation", 
                           operation_id=operation_id,
                           operation_type=operation_type,
                           parameters=parameters)
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to start operation", 
                            operation_id=operation_id,
                            error=str(e))
            return False
    
    def update_progress(self, operation_id: str, progress: int, 
                       step_name: str = None, details: Dict[str, Any] = None):
        """Update progress for an operation"""
        try:
            if operation_id not in self.active_operations:
                self.logger.warn("Operation not found for progress update", 
                               operation_id=operation_id)
                return False
            
            operation = self.active_operations[operation_id]
            operation["progress"] = min(progress, 100)
            operation["steps_completed"] += 1
            
            if step_name:
                operation["current_step"] = step_name
            
            if details:
                operation["step_details"] = details
            
            # Log progress update
            self.logger.info("Operation progress updated", 
                           operation_id=operation_id,
                           progress=progress,
                           step_name=step_name,
                           details=details)
            
            # Write progress log
            self._write_progress_log(operation_id, operation)
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to update progress", 
                            operation_id=operation_id,
                            error=str(e))
            return False
    
    def log_file_created(self, operation_id: str, file_path: str, 
                        file_type: str = None, size: int = None):
        """Log a file creation event"""
        try:
            if operation_id not in self.active_operations:
                return False
            
            file_info = {
                "file_path": file_path,
                "file_type": file_type,
                "size": size,
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.active_operations[operation_id]["files_created"].append(file_info)
            
            self.logger.info("File created", 
                           operation_id=operation_id,
                           file_path=file_path,
                           file_type=file_type,
                           size=size)
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to log file creation", 
                            operation_id=operation_id,
                            error=str(e))
            return False
    
    def log_error(self, operation_id: str, error_message: str, 
                 error_type: str = None, error_code: str = None,
                 stack_trace: str = None):
        """Log an error for an operation"""
        try:
            error_info = {
                "message": error_message,
                "type": error_type,
                "code": error_code,
                "stack_trace": stack_trace,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if operation_id in self.active_operations:
                self.active_operations[operation_id]["errors"].append(error_info)
                self.active_operations[operation_id]["status"] = "error"
            
            # Write error log
            self._write_error_log(operation_id, error_info)
            
            self.logger.error("Operation error", 
                            operation_id=operation_id,
                            error_message=error_message,
                            error_type=error_type,
                            error_code=error_code)
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to log error", 
                            operation_id=operation_id,
                            error=str(e))
            return False
    
    def log_warning(self, operation_id: str, warning_message: str, 
                   warning_type: str = None):
        """Log a warning for an operation"""
        try:
            warning_info = {
                "message": warning_message,
                "type": warning_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if operation_id in self.active_operations:
                self.active_operations[operation_id]["warnings"].append(warning_info)
            
            self.logger.warn("Operation warning", 
                           operation_id=operation_id,
                           warning_message=warning_message,
                           warning_type=warning_type)
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to log warning", 
                            operation_id=operation_id,
                            error=str(e))
            return False
    
    def complete_operation(self, operation_id: str, 
                          success: bool = True, 
                          summary: Dict[str, Any] = None):
        """Complete an operation and archive its logs"""
        try:
            if operation_id not in self.active_operations:
                self.logger.warn("Operation not found for completion", 
                               operation_id=operation_id)
                return False
            
            operation = self.active_operations[operation_id]
            operation["status"] = "completed" if success else "failed"
            operation["completed_at"] = datetime.utcnow().isoformat()
            operation["summary"] = summary or {}
            
            # Calculate duration
            started_at = datetime.fromisoformat(operation["started_at"])
            completed_at = datetime.fromisoformat(operation["completed_at"])
            duration = (completed_at - started_at).total_seconds()
            operation["duration_seconds"] = duration
            
            # Archive operation
            self.operation_history.append(operation.copy())
            
            # Write completion log
            self._write_completion_log(operation_id, operation)
            
            # Remove from active operations
            del self.active_operations[operation_id]
            
            self.logger.info("Operation completed", 
                           operation_id=operation_id,
                           success=success,
                           duration=duration,
                           summary=summary)
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to complete operation", 
                            operation_id=operation_id,
                            error=str(e))
            return False
    
    def _write_progress_log(self, operation_id: str, operation: Dict[str, Any]):
        """Write progress log to file"""
        try:
            progress_file = Path(self.config.log_dir) / self.generator_name / "progress" / f"{operation_id}_progress.log"
            
            progress_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "operation_id": operation_id,
                "progress": operation["progress"],
                "current_step": operation.get("current_step"),
                "steps_completed": operation["steps_completed"],
                "total_steps": operation.get("total_steps", 0)
            }
            
            with open(progress_file, 'a') as f:
                f.write(json.dumps(progress_entry) + '\n')
                
        except Exception as e:
            self.logger.error("Failed to write progress log", 
                            operation_id=operation_id,
                            error=str(e))
    
    def _write_error_log(self, operation_id: str, error_info: Dict[str, Any]):
        """Write error log to file"""
        try:
            error_file = Path(self.config.log_dir) / self.generator_name / "errors" / f"{operation_id}_errors.log"
            
            with open(error_file, 'a') as f:
                f.write(json.dumps(error_info) + '\n')
                
        except Exception as e:
            self.logger.error("Failed to write error log", 
                            operation_id=operation_id,
                            error=str(e))
    
    def _write_completion_log(self, operation_id: str, operation: Dict[str, Any]):
        """Write completion log to file"""
        try:
            completion_file = Path(self.config.log_dir) / self.generator_name / "operations" / f"{operation_id}_completion.log"
            
            with open(completion_file, 'w') as f:
                json.dump(operation, f, indent=2)
                
        except Exception as e:
            self.logger.error("Failed to write completion log", 
                            operation_id=operation_id,
                            error=str(e))
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an operation"""
        return self.active_operations.get(operation_id)
    
    def get_operation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get operation history"""
        return self.operation_history[-limit:]
    
    def get_generator_stats(self) -> Dict[str, Any]:
        """Get generator statistics"""
        total_operations = len(self.operation_history)
        successful_operations = len([op for op in self.operation_history if op["status"] == "completed"])
        failed_operations = len([op for op in self.operation_history if op["status"] == "failed"])
        
        return {
            "generator_name": self.generator_name,
            "active_operations": len(self.active_operations),
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": (successful_operations / total_operations * 100) if total_operations > 0 else 0,
            "config": asdict(self.config)
        }


def main():
    """Example usage of generator log manager"""
    
    # Create generator log manager
    log_manager = GeneratorLogManager("csharp-generator")
    
    # Start an operation
    operation_id = "create-plugin-123"
    log_manager.start_operation(operation_id, "create_bepinex_plugin", {
        "plugin_name": "VWE_TestPlugin",
        "target_framework": "net48"
    })
    
    # Update progress
    log_manager.update_progress(operation_id, 25, "Creating project structure")
    log_manager.update_progress(operation_id, 50, "Generating source files")
    log_manager.update_progress(operation_id, 75, "Compiling plugin")
    
    # Log file creation
    log_manager.log_file_created(operation_id, "/path/to/VWE_TestPlugin.dll", "dll", 1024)
    
    # Complete operation
    log_manager.complete_operation(operation_id, True, {
        "files_created": 5,
        "compilation_successful": True
    })
    
    # Get stats
    stats = log_manager.get_generator_stats()
    print(f"Generator stats: {stats}")


if __name__ == "__main__":
    main()
