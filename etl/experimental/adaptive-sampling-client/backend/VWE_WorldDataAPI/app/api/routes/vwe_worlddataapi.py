"""
API routes for VWE_WorldDataAPI
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
import logging

from app.models.vwe_worlddataapi_models import VWE_WorldDataAPIRequest, VWE_WorldDataAPIResponse
from app.services.vwe_worlddataapi_service import VWE_WorldDataAPIService
from app.core.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)


def get_vwe_worlddataapi_service() -> VWE_WorldDataAPIService:
    """Dependency injection for VWE_WorldDataAPI service"""
    return VWE_WorldDataAPIService()


@router.post("/", response_model=VWE_WorldDataAPIResponse)
async def create_vwe_worlddataapi(
    request: VWE_WorldDataAPIRequest,
    background_tasks: BackgroundTasks,
    service: VWE_WorldDataAPIService = Depends(get_vwe_worlddataapi_service)
):
    """Create a new vwe_worlddataapi resource"""
    try:
        logger.info(f"Creating vwe_worlddataapi: {request}")
        result = await service.create_vwe_worlddataapi(request)
        
        # Add background task if needed
        background_tasks.add_task(service.process_vwe_worlddataapi, result.id)
        
        return result
    except Exception as e:
        logger.error(f"Error creating vwe_worlddataapi: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{item_id}", response_model=VWE_WorldDataAPIResponse)
async def get_vwe_worlddataapi(
    item_id: str,
    service: VWE_WorldDataAPIService = Depends(get_vwe_worlddataapi_service)
):
    """Get a vwe_worlddataapi resource by ID"""
    try:
        result = await service.get_vwe_worlddataapi(item_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"VWE_WorldDataAPI not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vwe_worlddataapi {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[VWE_WorldDataAPIResponse])
async def list_vwe_worlddataapis(
    skip: int = 0,
    limit: int = 100,
    service: VWE_WorldDataAPIService = Depends(get_vwe_worlddataapi_service)
):
    """List all vwe_worlddataapi resources"""
    try:
        results = await service.list_vwe_worlddataapis(skip=skip, limit=limit)
        return results
    except Exception as e:
        logger.error(f"Error listing vwe_worlddataapis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{item_id}")
async def delete_vwe_worlddataapi(
    item_id: str,
    service: VWE_WorldDataAPIService = Depends(get_vwe_worlddataapi_service)
):
    """Delete a vwe_worlddataapi resource"""
    try:
        success = await service.delete_vwe_worlddataapi(item_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"VWE_WorldDataAPI not found")
        return {"message": f"VWE_WorldDataAPI {item_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vwe_worlddataapi {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
