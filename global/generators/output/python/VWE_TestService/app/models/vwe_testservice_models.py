"""
Data models for VWE_TestService
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class VWE_TestServiceStatus(str, Enum):
    """Status enumeration for VWE_TestService"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VWE_TestServiceRequest(BaseModel):
    """Request model for creating VWE_TestService"""
    name: str = Field(..., description="Name of the vwe_testservice")
    description: Optional[str] = Field(None, description="Description of the vwe_testservice")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Example VWE_TestService",
                "description": "An example vwe_testservice for testing",
                "metadata": {"key": "value"}
            }
        }


class VWE_TestServiceResponse(BaseModel):
    """Response model for VWE_TestService"""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name of the vwe_testservice")
    description: Optional[str] = Field(None, description="Description of the vwe_testservice")
    status: VWE_TestServiceStatus = Field(..., description="Current status")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Example VWE_TestService",
                "description": "An example vwe_testservice for testing",
                "status": "completed",
                "metadata": {"key": "value"},
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }


class VWE_TestServiceListResponse(BaseModel):
    """Response model for listing VWE_TestServices"""
    items: List[VWE_TestServiceResponse] = Field(..., description="List of vwe_testservices")
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
                "detail": "The requested vwe_testservice was not found",
                "code": "NOT_FOUND"
            }
        }
