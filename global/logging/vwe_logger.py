#!/usr/bin/env python3
"""
VWE Logger - Standardized logging for Valheim World Engine
Provides consistent, structured logging across all VWE components
"""

import os
import sys
import json
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict


class LogLevel(Enum):
    """VWE standardized log levels"""
    TRACE = "TRACE"      # Very detailed debugging
    DEBUG = "DEBUG"      # Detailed debugging
    INFO = "INFO"        # General information
    WARN = "WARN"        # Warning messages
    ERROR = "ERROR"      # Error messages
    CRITICAL = "CRITICAL" # Critical errors


class LogFormat(Enum):
    """VWE standardized log formats"""
    JSON = "json"        # Structured JSON logging
    TEXT = "text"        # Human-readable text
    COMPACT = "compact"  # Compact single-line format


@dataclass
class LogConfig:
    """VWE logging configuration"""
    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.JSON
    output_dir: str = "/var/log/vwe"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_output: bool = True
    file_output: bool = True
    structured: bool = True
    include_timestamp: bool = True
    include_context: bool = True


class VWELogger:
    """Standardized VWE logger with structured output and proper hygiene"""
    
    def __init__(self, name: str, config: Optional[LogConfig] = None, 
                 context: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or LogConfig()
        self.context = context or {}
        
        # Create logger
        self.logger = logging.getLogger(f"vwe.{name}")
        self.logger.setLevel(getattr(logging, self.config.level.value))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_handlers()
        
        # Add context to all log records
        if self.config.include_context:
            self._add_context_filter()
    
    def _setup_handlers(self):
        """Setup console and file handlers based on configuration"""
        
        # Console handler
        if self.config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.logger.level)
            console_handler.setFormatter(self._get_formatter(console=True))
            self.logger.addHandler(console_handler)
        
        # File handler
        if self.config.file_output:
            # Ensure log directory exists
            log_dir = Path(self.config.output_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create rotating file handler
            log_file = log_dir / f"{self.name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count
            )
            file_handler.setLevel(self.logger.level)
            file_handler.setFormatter(self._get_formatter(console=False))
            self.logger.addHandler(file_handler)
    
    def _get_formatter(self, console: bool = False) -> logging.Formatter:
        """Get appropriate formatter based on configuration"""
        
        if self.config.format == LogFormat.JSON:
            return VWEJSONFormatter(console=console)
        elif self.config.format == LogFormat.COMPACT:
            return VWECompactFormatter(console=console)
        else:  # TEXT
            return VWETextFormatter(console=console)
    
    def _add_context_filter(self):
        """Add context information to all log records"""
        context_filter = VWEContextFilter(self.context)
        for handler in self.logger.handlers:
            handler.addFilter(context_filter)
    
    def trace(self, message: str, **kwargs):
        """Log trace level message"""
        self._log(logging.DEBUG - 1, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug level message"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info level message"""
        self._log(logging.INFO, message, **kwargs)
    
    def warn(self, message: str, **kwargs):
        """Log warning level message"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error level message"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical level message"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with structured data"""
        extra = {
            'vwe_component': self.name,
            'vwe_timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.log(level, message, extra=extra)
    
    def set_context(self, **context):
        """Update logger context"""
        self.context.update(context)
        # Update context filter
        for handler in self.logger.handlers:
            for filter_obj in handler.filters:
                if isinstance(filter_obj, VWEContextFilter):
                    filter_obj.update_context(context)
    
    def get_log_file_path(self) -> Optional[str]:
        """Get the current log file path"""
        for handler in self.logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                return handler.baseFilename
        return None


class VWEJSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self, console: bool = False):
        super().__init__()
        self.console = console
    
    def format(self, record):
        """Format log record as JSON"""
        log_data = {
            'timestamp': record.vwe_timestamp if hasattr(record, 'vwe_timestamp') else datetime.utcnow().isoformat(),
            'level': record.levelname,
            'component': getattr(record, 'vwe_component', 'unknown'),
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key.startswith('vwe_') and key not in ['vwe_timestamp', 'vwe_component']:
                log_data[key[4:]] = value  # Remove 'vwe_' prefix
        
        # Add context if available
        if hasattr(record, 'vwe_context'):
            log_data['context'] = record.vwe_context
        
        if self.console:
            return json.dumps(log_data, indent=2)
        else:
            return json.dumps(log_data)


class VWETextFormatter(logging.Formatter):
    """Human-readable text formatter"""
    
    def __init__(self, console: bool = False):
        if console:
            fmt = '%(asctime)s | %(levelname)-8s | %(vwe_component)s | %(message)s'
        else:
            fmt = '%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s'
        
        super().__init__(fmt, datefmt='%Y-%m-%d %H:%M:%S')
        self.console = console
    
    def format(self, record):
        """Format log record as text"""
        # Add default context if not present
        if not hasattr(record, 'vwe_component'):
            record.vwe_component = 'unknown'
        
        return super().format(record)


class VWECompactFormatter(logging.Formatter):
    """Compact single-line formatter"""
    
    def __init__(self, console: bool = False):
        fmt = '%(asctime)s|%(levelname)s|%(vwe_component)s|%(message)s'
        super().__init__(fmt, datefmt='%H:%M:%S')
        self.console = console
    
    def format(self, record):
        """Format log record as compact text"""
        if not hasattr(record, 'vwe_component'):
            record.vwe_component = 'unknown'
        
        return super().format(record)


class VWEContextFilter(logging.Filter):
    """Filter to add context information to log records"""
    
    def __init__(self, context: Dict[str, Any]):
        super().__init__()
        self.context = context
    
    def filter(self, record):
        """Add context to log record"""
        record.vwe_context = self.context.copy()
        return True
    
    def update_context(self, new_context: Dict[str, Any]):
        """Update context information"""
        self.context.update(new_context)


def get_vwe_logger(name: str, config: Optional[LogConfig] = None, 
                  context: Optional[Dict[str, Any]] = None) -> VWELogger:
    """Get a VWE logger instance"""
    return VWELogger(name, config, context)


def setup_vwe_logging(level: LogLevel = LogLevel.INFO, 
                     format: LogFormat = LogFormat.JSON,
                     output_dir: str = "/var/log/vwe") -> None:
    """Setup global VWE logging configuration"""
    
    # Create log directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.value))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create VWE config
    config = LogConfig(
        level=level,
        format=format,
        output_dir=output_dir
    )
    
    # Setup handlers
    logger = VWELogger("root", config)
    
    # Set as root logger
    root_logger.handlers = logger.logger.handlers


def main():
    """Example usage of VWE logger"""
    
    # Setup global logging
    setup_vwe_logging(LogLevel.DEBUG, LogFormat.JSON)
    
    # Create component loggers
    generator_logger = get_vwe_logger("generator", context={"component": "csharp"})
    docker_logger = get_vwe_logger("docker", context={"service": "valheim-bepinex"})
    
    # Example logging
    generator_logger.info("Starting C# generator", operation="create_plugin", plugin_name="VWE_Test")
    docker_logger.warn("Container startup taking longer than expected", container_id="abc123", duration=30)
    generator_logger.error("Plugin compilation failed", error_code="CS0103", line=42)
    
    # Update context
    generator_logger.set_context(plugin_version="1.0.0", build_id="build-123")
    generator_logger.info("Plugin build completed")


if __name__ == "__main__":
    main()
