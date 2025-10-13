"""
World Data Models for Valheim Adaptive Sampling
Pydantic models for biomes, heightmaps, and validation
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any
from datetime import datetime
from enum import IntEnum


class Biome(IntEnum):
    """Valheim biome types (bit flags) - MUST match Heightmap.Biome enum"""
    NONE = 0
    MEADOWS = 1
    BLACK_FOREST = 2
    SWAMP = 4
    MOUNTAIN = 8
    PLAINS = 16
    OCEAN = 32
    MISTLANDS = 64
    DEEP_NORTH = 256
    ASHLANDS = 512


# Biome color mapping for visualization
BIOME_COLORS = {
    Biome.NONE: (0, 0, 0),           # Black
    Biome.MEADOWS: (121, 176, 81),   # Green
    Biome.SWAMP: (98, 89, 71),       # Brown-gray
    Biome.MOUNTAIN: (209, 228, 237), # Light blue-gray
    Biome.BLACK_FOREST: (45, 66, 40), # Dark green
    Biome.PLAINS: (246, 222, 145),   # Yellow-tan
    Biome.OCEAN: (52, 97, 141),      # Blue
    Biome.MISTLANDS: (105, 105, 120), # Purple-gray
    Biome.ASHLANDS: (120, 70, 50),   # Red-brown
    Biome.DEEP_NORTH: (240, 248, 255), # White-blue
}


class BiomeMapMetadata(BaseModel):
    """Metadata for biome map"""
    sample_spacing_meters: float
    biome_counts: Dict[str, int]
    generation_time: Optional[datetime] = None


class BiomeMapResponse(BaseModel):
    """Response model for biome map data"""
    resolution: int = Field(..., ge=128, le=2048, description="Map resolution (NxN)")
    world_radius: float = Field(default=10000.0, description="World radius in meters")
    world_diameter: float = Field(default=20000.0, description="World diameter in meters")
    biome_map: List[List[int]] = Field(..., description="2D array of biome IDs")
    metadata: Optional[BiomeMapMetadata] = None


class HeightmapMetadata(BaseModel):
    """Metadata for heightmap"""
    min_height: float
    max_height: float
    sample_spacing_meters: float


class HeightmapResponse(BaseModel):
    """Response model for heightmap data"""
    resolution: int = Field(..., ge=128, le=2048)
    world_radius: float = Field(default=10000.0)
    world_diameter: float = Field(default=20000.0)
    heightmap: List[List[float]] = Field(..., description="2D array of height values", alias="height_map")
    metadata: Optional[HeightmapMetadata] = None
    
    class Config:
        populate_by_name = True  # Allow both heightmap and height_map


class ValidationCheck(BaseModel):
    """Individual validation check result"""
    check_name: str
    status: Literal["passed", "failed", "warning"]
    details: str
    expected: Optional[str] = None
    actual: Optional[str] = None


class ValidationReport(BaseModel):
    """Complete validation report for world data"""
    seed: str
    status: Literal["passed", "failed", "warning"]
    checks: List[ValidationCheck]
    summary: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class WorldDataInfo(BaseModel):
    """Basic info about available world data"""
    seed: str
    has_biomes: bool
    has_heightmap: bool
    has_structures: bool
    resolution: Optional[int] = None
    file_sizes: Dict[str, int] = Field(default_factory=dict)


class UpscaleRequest(BaseModel):
    """Request to upscale world data"""
    target_resolution: int = Field(..., ge=256, le=4096)
    interpolation_method: Literal["nearest", "bilinear", "bicubic"] = "bicubic"

