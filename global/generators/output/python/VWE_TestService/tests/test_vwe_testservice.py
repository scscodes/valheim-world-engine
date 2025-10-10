"""
Tests for VWE_TestService
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.models.vwe_testservice_models import VWE_TestServiceRequest, VWE_TestServiceResponse


client = TestClient(app)


class TestVWE_TestServiceAPI:
    """Test cases for VWE_TestService API endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "VWE_TestService"
    
    def test_create_vwe_testservice_success(self):
        """Test successful vwe_testservice creation"""
        request_data = {
            "name": "Test VWE_TestService",
            "description": "Test description",
            "metadata": {"key": "value"}
        }
        
        with patch("app.api.routes.vwe_testservice.get_vwe_testservice_service") as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.create_vwe_testservice.return_value = VWE_TestServiceResponse(
                id="test-id",
                name="Test VWE_TestService",
                description="Test description",
                status="created",
                metadata={"key": "value"}
            )
            mock_service.return_value = mock_service_instance
            
            response = client.post("/api/v1/vwe_testservice/", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test VWE_TestService"
            assert data["status"] == "created"
    
    def test_get_vwe_testservice_not_found(self):
        """Test getting non-existent vwe_testservice"""
        with patch("app.api.routes.vwe_testservice.get_vwe_testservice_service") as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.get_vwe_testservice.return_value = None
            mock_service.return_value = mock_service_instance
            
            response = client.get("/api/v1/vwe_testservice/nonexistent-id")
            assert response.status_code == 404
    
    def test_list_vwe_testservices(self):
        """Test listing vwe_testservices"""
        with patch("app.api.routes.vwe_testservice.get_vwe_testservice_service") as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.list_vwe_testservices.return_value = []
            mock_service.return_value = mock_service_instance
            
            response = client.get("/api/v1/vwe_testservice/")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


class TestVWE_TestServiceService:
    """Test cases for VWE_TestService service layer"""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        from app.services.vwe_testservice_service import VWE_TestServiceService
        return VWE_TestServiceService()
    
    @pytest.mark.asyncio
    async def test_create_vwe_testservice(self, service):
        """Test vwe_testservice creation in service layer"""
        request = VWE_TestServiceRequest(
            name="Test VWE_TestService",
            description="Test description"
        )
        
        result = await service.create_vwe_testservice(request)
        assert result.name == "Test VWE_TestService"
        assert result.status == "created"
        assert result.id is not None
    
    @pytest.mark.asyncio
    async def test_get_vwe_testservice_not_found(self, service):
        """Test getting non-existent vwe_testservice in service layer"""
        result = await service.get_vwe_testservice("nonexistent-id")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_vwe_testservices(self, service):
        """Test listing vwe_testservices in service layer"""
        result = await service.list_vwe_testservices()
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_delete_vwe_testservice_not_found(self, service):
        """Test deleting non-existent vwe_testservice in service layer"""
        result = await service.delete_vwe_testservice("nonexistent-id")
        assert result is False
