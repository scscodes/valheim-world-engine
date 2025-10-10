"""
VWE Logging Standards Package
Centralized logging configuration and utilities for Valheim World Engine
"""

from .vwe_logger import VWELogger, LogLevel, LogFormat
from .docker_logging import DockerLogManager
from .generator_logging import GeneratorLogManager
from .log_rotation import LogRotationManager
from .log_monitoring import LogMonitor

__version__ = "1.0.0"
__author__ = "VWE"

__all__ = [
    "VWELogger",
    "LogLevel", 
    "LogFormat",
    "DockerLogManager",
    "GeneratorLogManager", 
    "LogRotationManager",
    "LogMonitor",
]
