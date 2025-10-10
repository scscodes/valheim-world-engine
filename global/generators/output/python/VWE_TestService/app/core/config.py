"""
Configuration settings for VWE_TestService
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Service configuration
    SERVICE_NAME: str = "VWE_TestService"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Database configuration
    DATABASE_URL: str = "sqlite:///./vwe_testservice.db"
    
    # Redis configuration
    REDIS_URL: str = "redis://localhost:6379"
    
    # Logging configuration
    LOG_LEVEL: str = "INFO"
    
    # VWE specific settings
    DATA_DIR: str = "/app/data"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
_settings: Settings = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
