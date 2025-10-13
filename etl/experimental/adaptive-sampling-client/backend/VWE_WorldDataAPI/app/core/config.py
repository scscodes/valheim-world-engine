"""
Configuration settings for VWE World Data API
"""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    """Application settings for VWE World Data API"""
    
    # Application
    SERVICE_NAME: str = "VWE_WorldDataAPI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Data paths - automatically resolve to bepinex-adaptive-sampling output
    # From config.py: parent x6 = experimental/, then append bepinex path
    DATA_ROOT: Path = Path(__file__).parent.parent.parent.parent.parent.parent / "bepinex-adaptive-sampling" / "output" / "world_data"
    
    # CORS configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # File limits
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from environment


# Global settings instance (singleton pattern)
_settings: Settings = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
