"""
Data models for VWE_WorldDataAPI
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class VWE_WorldDataAPIStatus(str, Enum):
    """Status enumeration for VWE_WorldDataAPI"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VWE_WorldDataAPIRequest(BaseModel):
    """Request model for creating VWE_WorldDataAPI"""
    name: str = Field(..., description="Name of the vwe_worlddataapi")
    description: Optional[str] = Field(None, description="Description of the vwe_worlddataapi")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Example VWE_WorldDataAPI",
                "description": "An example vwe_worlddataapi for testing",
                "metadata": {"key": "value"}
            }
        }


class VWE_WorldDataAPIResponse(BaseModel):
    """Response model for VWE_WorldDataAPI"""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name of the vwe_worlddataapi")
    description: Optional[str] = Field(None, description="Description of the vwe_worlddataapi")
    status: VWE_WorldDataAPIStatus = Field(..., description="Current status")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Example VWE_WorldDataAPI",
                "description": "An example vwe_worlddataapi for testing",
                "status": "completed",
                "metadata": {"key": "value"},
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }


class VWE_WorldDataAPIListResponse(BaseModel):
    """Response model for listing VWE_WorldDataAPIs"""
    items: List[VWE_WorldDataAPIResponse] = Field(..., description="List of vwe_worlddataapis")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 0,
                "skip": 0,
                "limit": 100
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Resource not found",
                "detail": "The requested vwe_worlddataapi was not found",
                "code": "NOT_FOUND"
            }
        }
