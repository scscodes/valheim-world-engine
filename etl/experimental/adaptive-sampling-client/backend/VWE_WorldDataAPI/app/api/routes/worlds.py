"""
World Data API Routes
Endpoints for accessing and visualizing Valheim world data
"""

import logging
from pathlib import Path
from typing import Literal, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse

from ...models.world_data import BiomeMapResponse, HeightmapResponse, WorldDataInfo
from ...services.world_loader import WorldDataLoader
from ...services.image_generator import ImageGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/worlds", tags=["worlds"])

# Initialize services - will be set on startup
world_loader = None
image_generator = ImageGenerator()

def initialize_loader(data_root: Path):
    """Initialize the world loader with the correct data path"""
    global world_loader
    world_loader = WorldDataLoader(data_root)
    logger.info(f"Initialized world loader with data root: {data_root}")
    logger.info(f"Data root exists: {data_root.exists()}")


@router.get("/", response_model=list[WorldDataInfo])
async def list_worlds():
    """List all available world seeds with data"""
    if world_loader is None:
        raise HTTPException(
            status_code=503, 
            detail="World loader not initialized. Check server logs for data path issues."
        )
    try:
        worlds = world_loader.list_available_worlds()
        if not worlds:
            logger.info("No worlds found. Data directory may be empty or data not yet generated.")
        return worlds
    except Exception as e:
        logger.error(f"Error listing worlds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seed}/info", response_model=WorldDataInfo)
async def get_world_info(seed: str):
    """Get information about a specific world seed"""
    try:
        info = world_loader.get_world_info(seed)
        return info
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"World '{seed}' not found")
    except Exception as e:
        logger.error(f"Error getting world info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seed}/biomes", response_model=BiomeMapResponse)
async def get_biome_data(
    seed: str,
    format: Literal["json", "png"] = Query(default="json", description="Response format"),
    render_mode: Literal["nearest", "smooth"] = Query(
        default="nearest",
        description="Rendering mode: 'nearest' for fast/blocky, 'smooth' for interpolated boundaries"
    ),
    visualization_mode: Literal["terrain_only", "height_aware", "water_mask", "height_gradient"] = Query(
        default="terrain_only",
        description="Visualization mode: terrain_only (raw biomes), height_aware (apply water level), water_mask (debug), height_gradient (debug)"
    ),
    resolution: Optional[int] = Query(
        default=None,
        ge=256,
        le=4096,
        description="Target resolution for PNG output (e.g., 1024, 2048, 4096)"
    ),
    water_level: float = Query(
        default=30.0,
        ge=0.0,
        le=100.0,
        description="Water level threshold in meters (default 30m for Valheim)"
    )
):
    """
    Get biome data for a world seed with advanced rendering options

    - **seed**: World seed name
    - **format**: Response format (json or png)
    - **render_mode**: Rendering mode (nearest=fast/blocky, smooth=interpolated)
    - **visualization_mode**:
        - terrain_only: Raw terrain biomes (ignores water)
        - height_aware: Apply water level (Shallows for submerged areas) ⭐ RECOMMENDED
        - water_mask: Debug view (Blue=shallows, Green=land, Red=ocean)
        - height_gradient: Debug view (grayscale elevation)
    - **resolution**: Target output resolution for PNG (256-4096)
    - **water_level**: Water level in meters for height_aware mode (default 30m)

    Examples:
      - `/biomes?format=png&visualization_mode=height_aware` - Realistic water/land separation
      - `/biomes?format=png&render_mode=smooth&resolution=2048&visualization_mode=height_aware` - Best quality
      - `/biomes?format=png&visualization_mode=water_mask` - Debug water coverage
      - `/biomes?format=png&visualization_mode=height_aware&water_level=25` - Tune water level
    """
    try:
        biome_data = world_loader.load_biome_data(seed)

        if format == "png":
            # Load heightmap if needed for height-aware modes
            heightmap_data = None
            if visualization_mode in ["height_aware", "water_mask", "height_gradient"]:
                try:
                    heightmap_data = world_loader.load_heightmap_data(seed)
                except FileNotFoundError:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Heightmap data required for {visualization_mode} mode but not found for seed '{seed}'"
                    )

            # Generate PNG image with specified options
            image_buffer = image_generator.generate_biome_image(
                biome_data,
                heightmap_data=heightmap_data,
                target_resolution=resolution,
                render_mode=render_mode,
                visualization_mode=visualization_mode,
                water_level=water_level
            )

            filename = f"biomes_{seed}_{render_mode}_{visualization_mode}.png"
            return StreamingResponse(
                image_buffer,
                media_type="image/png",
                headers={"Content-Disposition": f"inline; filename={filename}"}
            )
        else:
            # Return JSON
            return biome_data

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting biome data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seed}/heightmap", response_model=HeightmapResponse)
async def get_heightmap_data(
    seed: str,
    format: Literal["json", "png"] = Query(default="json"),
    colormap: Literal["terrain", "grayscale"] = Query(default="terrain")
):
    """
    Get heightmap data for a world seed
    
    - **seed**: World seed name
    - **format**: Response format (json or png)
    - **colormap**: Color scheme for PNG (terrain or grayscale)
    """
    try:
        heightmap_data = world_loader.load_heightmap_data(seed)
        
        if format == "png":
            # Generate PNG image
            image_buffer = image_generator.generate_heightmap_image(
                heightmap_data, 
                colormap=colormap
            )
            return StreamingResponse(
                image_buffer,
                media_type="image/png",
                headers={"Content-Disposition": f"inline; filename=heightmap_{seed}.png"}
            )
        else:
            # Return JSON
            return heightmap_data
            
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Heightmap data for '{seed}' not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting heightmap data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{seed}/composite")
async def get_composite_image(
    seed: str,
    resolution: Optional[int] = Query(default=512, ge=256, le=2048),
    alpha: float = Query(default=0.5, ge=0.0, le=1.0, description="Heightmap overlay transparency")
):
    """
    Get composite image with biomes and heightmap overlay
    
    - **seed**: World seed name
    - **resolution**: Target image resolution
    - **alpha**: Transparency of heightmap overlay (0-1)
    """
    try:
        biome_data = world_loader.load_biome_data(seed)
        heightmap_data = world_loader.load_heightmap_data(seed)
        
        # Generate composite image
        image_buffer = image_generator.generate_composite_image(
            biome_data,
            heightmap_data,
            target_resolution=resolution,
            alpha=alpha
        )
        
        return StreamingResponse(
            image_buffer,
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=composite_{seed}.png"}
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating composite image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint with data availability status"""
    from ...core.config import get_settings
    settings = get_settings()
    
    data_available = settings.DATA_ROOT.exists()
    json_files = []
    if data_available:
        json_files = list(settings.DATA_ROOT.glob("*.json"))
    
    return {
        "status": "healthy",
        "service": "VWE World Data API",
        "data_root": str(settings.DATA_ROOT),
        "data_root_exists": data_available,
        "json_files_found": len(json_files),
        "ready_to_serve": data_available and len(json_files) > 0,
        "message": "Ready to serve worlds" if data_available else "No data available. Generate with: cd ../bepinex-adaptive-sampling && python tests/validate_performance.py --seed TestSeed"
    }

