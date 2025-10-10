"""
API routes for VWE_TestService
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
import logging

from app.models.vwe_testservice_models import VWE_TestServiceRequest, VWE_TestServiceResponse
from app.services.vwe_testservice_service import VWE_TestServiceService
from app.core.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)


def get_vwe_testservice_service() -> VWE_TestServiceService:
    """Dependency injection for VWE_TestService service"""
    return VWE_TestServiceService()


@router.post("/", response_model=VWE_TestServiceResponse)
async def create_vwe_testservice(
    request: VWE_TestServiceRequest,
    background_tasks: BackgroundTasks,
    service: VWE_TestServiceService = Depends(get_vwe_testservice_service)
):
    """Create a new vwe_testservice resource"""
    try:
        logger.info(f"Creating vwe_testservice: {request}")
        result = await service.create_vwe_testservice(request)
        
        # Add background task if needed
        background_tasks.add_task(service.process_vwe_testservice, result.id)
        
        return result
    except Exception as e:
        logger.error(f"Error creating vwe_testservice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{item_id}", response_model=VWE_TestServiceResponse)
async def get_vwe_testservice(
    item_id: str,
    service: VWE_TestServiceService = Depends(get_vwe_testservice_service)
):
    """Get a vwe_testservice resource by ID"""
    try:
        result = await service.get_vwe_testservice(item_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"VWE_TestService not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vwe_testservice {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[VWE_TestServiceResponse])
async def list_vwe_testservices(
    skip: int = 0,
    limit: int = 100,
    service: VWE_TestServiceService = Depends(get_vwe_testservice_service)
):
    """List all vwe_testservice resources"""
    try:
        results = await service.list_vwe_testservices(skip=skip, limit=limit)
        return results
    except Exception as e:
        logger.error(f"Error listing vwe_testservices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{item_id}")
async def delete_vwe_testservice(
    item_id: str,
    service: VWE_TestServiceService = Depends(get_vwe_testservice_service)
):
    """Delete a vwe_testservice resource"""
    try:
        success = await service.delete_vwe_testservice(item_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"VWE_TestService not found")
        return {"message": f"VWE_TestService {item_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vwe_testservice {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
