"""
Tests for VWE_WorldDataAPI
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.models.vwe_worlddataapi_models import VWE_WorldDataAPIRequest, VWE_WorldDataAPIResponse


client = TestClient(app)


class TestVWE_WorldDataAPIAPI:
    """Test cases for VWE_WorldDataAPI API endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "VWE_WorldDataAPI"
    
    def test_create_vwe_worlddataapi_success(self):
        """Test successful vwe_worlddataapi creation"""
        request_data = {
            "name": "Test VWE_WorldDataAPI",
            "description": "Test description",
            "metadata": {"key": "value"}
        }
        
        with patch("app.api.routes.vwe_worlddataapi.get_vwe_worlddataapi_service") as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.create_vwe_worlddataapi.return_value = VWE_WorldDataAPIResponse(
                id="test-id",
                name="Test VWE_WorldDataAPI",
                description="Test description",
                status="created",
                metadata={"key": "value"}
            )
            mock_service.return_value = mock_service_instance
            
            response = client.post("/api/v1/vwe_worlddataapi/", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test VWE_WorldDataAPI"
            assert data["status"] == "created"
    
    def test_get_vwe_worlddataapi_not_found(self):
        """Test getting non-existent vwe_worlddataapi"""
        with patch("app.api.routes.vwe_worlddataapi.get_vwe_worlddataapi_service") as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.get_vwe_worlddataapi.return_value = None
            mock_service.return_value = mock_service_instance
            
            response = client.get("/api/v1/vwe_worlddataapi/nonexistent-id")
            assert response.status_code == 404
    
    def test_list_vwe_worlddataapis(self):
        """Test listing vwe_worlddataapis"""
        with patch("app.api.routes.vwe_worlddataapi.get_vwe_worlddataapi_service") as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.list_vwe_worlddataapis.return_value = []
            mock_service.return_value = mock_service_instance
            
            response = client.get("/api/v1/vwe_worlddataapi/")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


class TestVWE_WorldDataAPIService:
    """Test cases for VWE_WorldDataAPI service layer"""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        from app.services.vwe_worlddataapi_service import VWE_WorldDataAPIService
        return VWE_WorldDataAPIService()
    
    @pytest.mark.asyncio
    async def test_create_vwe_worlddataapi(self, service):
        """Test vwe_worlddataapi creation in service layer"""
        request = VWE_WorldDataAPIRequest(
            name="Test VWE_WorldDataAPI",
            description="Test description"
        )
        
        result = await service.create_vwe_worlddataapi(request)
        assert result.name == "Test VWE_WorldDataAPI"
        assert result.status == "created"
        assert result.id is not None
    
    @pytest.mark.asyncio
    async def test_get_vwe_worlddataapi_not_found(self, service):
        """Test getting non-existent vwe_worlddataapi in service layer"""
        result = await service.get_vwe_worlddataapi("nonexistent-id")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_vwe_worlddataapis(self, service):
        """Test listing vwe_worlddataapis in service layer"""
        result = await service.list_vwe_worlddataapis()
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_delete_vwe_worlddataapi_not_found(self, service):
        """Test deleting non-existent vwe_worlddataapi in service layer"""
        result = await service.delete_vwe_worlddataapi("nonexistent-id")
        assert result is False
