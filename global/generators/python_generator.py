#!/usr/bin/env python3
"""
Python Generator for Valheim World Engine
Generates FastAPI backend services, data processors, and utility modules
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class PythonGenerator:
    """Generator for Python FastAPI services and backend components"""
    
    # Standardized VWE Python versions - DO NOT MODIFY WITHOUT UPDATING ALL SERVICES
    VWE_STANDARD_VERSIONS = {
        "fastapi": "0.104.1",
        "uvicorn": "0.24.0",
        "pydantic": "2.5.0",
        "pydantic-settings": "2.1.0",
        "sqlalchemy": "2.0.23",
        "alembic": "1.13.1",
        "redis": "5.0.1",
        "httpx": "0.25.2",
        "aiohttp": "3.9.1",
        "numpy": "1.24.3",
        "pandas": "2.0.3",
        "pillow": "10.1.0",
        "rq": "1.15.1",
        "celery": "5.3.4"
    }
    
    def __init__(self, base_path: str = ".", override_versions: Optional[Dict[str, str]] = None):
        self.base_path = Path(base_path)
        self.templates_dir = self.base_path / "templates" / "python"
        self.output_dir = self.base_path / "output" / "python"
        
        # Setup logging for override detection
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Handle version overrides with clear logging
        self.versions = self.VWE_STANDARD_VERSIONS.copy()
        if override_versions:
            self.logger.warning("=" * 60)
            self.logger.warning("⚠️  VERSION OVERRIDES DETECTED - NON-STANDARD CONFIGURATION")
            self.logger.warning("=" * 60)
            for package, version in override_versions.items():
                if package in self.versions:
                    old_version = self.versions[package]
                    self.versions[package] = version
                    self.logger.warning(f"OVERRIDE: {package} {old_version} → {version}")
                else:
                    self.versions[package] = version
                    self.logger.warning(f"ADDED: {package} {version}")
            self.logger.warning("=" * 60)
            self.logger.warning("⚠️  USING OVERRIDDEN VERSIONS - MAY CAUSE COMPATIBILITY ISSUES")
            self.logger.warning("=" * 60)
        
    def create_fastapi_service(self, service_name: str, description: str = "", 
                             version: str = "1.0.0", author: str = "VWE") -> Dict[str, str]:
        """Generate a complete FastAPI service structure"""
        
        self.logger.info(f"Creating FastAPI service: {service_name} v{version}")
        self.logger.info(f"Using VWE standardized dependency versions")
        
        # Create service directory structure
        service_dir = self.output_dir / service_name
        service_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (service_dir / "app").mkdir(exist_ok=True)
        (service_dir / "app" / "api").mkdir(exist_ok=True)
        (service_dir / "app" / "api" / "routes").mkdir(exist_ok=True)
        (service_dir / "app" / "core").mkdir(exist_ok=True)
        (service_dir / "app" / "services").mkdir(exist_ok=True)
        (service_dir / "app" / "models").mkdir(exist_ok=True)
        (service_dir / "tests").mkdir(exist_ok=True)
        
        files_created = {}
        
        # 1. Main application file
        main_content = self._generate_main_app(service_name, description)
        main_file = service_dir / "app" / "main.py"
        main_file.write_text(main_content)
        files_created["main_app"] = str(main_file)
        
        # 2. Core configuration
        config_content = self._generate_config(service_name)
        config_file = service_dir / "app" / "core" / "config.py"
        config_file.write_text(config_content)
        files_created["config"] = str(config_file)
        
        # 3. API routes
        routes_content = self._generate_routes(service_name)
        routes_file = service_dir / "app" / "api" / "routes" / f"{service_name.lower()}.py"
        routes_file.write_text(routes_content)
        files_created["routes"] = str(routes_file)
        
        # 4. Service layer
        service_content = self._generate_service_class(service_name)
        service_file = service_dir / "app" / "services" / f"{service_name.lower()}_service.py"
        service_file.write_text(service_content)
        files_created["service"] = str(service_file)
        
        # 5. Data models
        models_content = self._generate_models(service_name)
        models_file = service_dir / "app" / "models" / f"{service_name.lower()}_models.py"
        models_file.write_text(models_content)
        files_created["models"] = str(models_file)
        
        # 6. Requirements file
        requirements_content = self._generate_requirements()
        requirements_file = service_dir / "requirements.txt"
        requirements_file.write_text(requirements_content)
        files_created["requirements"] = str(requirements_file)
        
        # 7. Dockerfile
        dockerfile_content = self._generate_dockerfile(service_name)
        dockerfile_file = service_dir / "Dockerfile"
        dockerfile_file.write_text(dockerfile_content)
        files_created["dockerfile"] = str(dockerfile_file)
        
        # 8. README
        readme_content = self._generate_readme(service_name, description, version, author)
        readme_file = service_dir / "README.md"
        readme_file.write_text(readme_content)
        files_created["readme"] = str(readme_file)
        
        # 9. Test file
        test_content = self._generate_tests(service_name)
        test_file = service_dir / "tests" / f"test_{service_name.lower()}.py"
        test_file.write_text(test_content)
        files_created["tests"] = str(test_file)
        
        return files_created
    
    def _generate_main_app(self, service_name: str, description: str) -> str:
        """Generate the main FastAPI application"""
        return f'''"""
{service_name} - {description}
FastAPI service for Valheim World Engine
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.core.config import get_settings
from app.api.routes import {service_name.lower()}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logging.info(f"Starting {{service_name}} service...")
    yield
    # Shutdown
    logging.info(f"Shutting down {{service_name}} service...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="{service_name}",
        description="{description}",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(
        {service_name.lower()}.router,
        prefix="/api/v1/{service_name.lower()}",
        tags=["{service_name.lower()}"]
    )
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {{"status": "healthy", "service": "{service_name}"}}
    
    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
'''
    
    def _generate_config(self, service_name: str) -> str:
        """Generate configuration module"""
        return f'''"""
Configuration settings for {service_name}
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Service configuration
    SERVICE_NAME: str = "{service_name}"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Database configuration
    DATABASE_URL: str = "sqlite:///./{service_name.lower()}.db"
    
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
'''
    
    def _generate_routes(self, service_name: str) -> str:
        """Generate API routes"""
        return f'''"""
API routes for {service_name}
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
import logging

from app.models.{service_name.lower()}_models import {service_name}Request, {service_name}Response
from app.services.{service_name.lower()}_service import {service_name}Service
from app.core.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)


def get_{service_name.lower()}_service() -> {service_name}Service:
    """Dependency injection for {service_name} service"""
    return {service_name}Service()


@router.post("/", response_model={service_name}Response)
async def create_{service_name.lower()}(
    request: {service_name}Request,
    background_tasks: BackgroundTasks,
    service: {service_name}Service = Depends(get_{service_name.lower()}_service)
):
    """Create a new {service_name.lower()} resource"""
    try:
        logger.info(f"Creating {service_name.lower()}: {{request}}")
        result = await service.create_{service_name.lower()}(request)
        
        # Add background task if needed
        background_tasks.add_task(service.process_{service_name.lower()}, result.id)
        
        return result
    except Exception as e:
        logger.error(f"Error creating {service_name.lower()}: {{e}}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{{item_id}}", response_model={service_name}Response)
async def get_{service_name.lower()}(
    item_id: str,
    service: {service_name}Service = Depends(get_{service_name.lower()}_service)
):
    """Get a {service_name.lower()} resource by ID"""
    try:
        result = await service.get_{service_name.lower()}(item_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"{service_name} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting {service_name.lower()} {{item_id}}: {{e}}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[{service_name}Response])
async def list_{service_name.lower()}s(
    skip: int = 0,
    limit: int = 100,
    service: {service_name}Service = Depends(get_{service_name.lower()}_service)
):
    """List all {service_name.lower()} resources"""
    try:
        results = await service.list_{service_name.lower()}s(skip=skip, limit=limit)
        return results
    except Exception as e:
        logger.error(f"Error listing {service_name.lower()}s: {{e}}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{{item_id}}")
async def delete_{service_name.lower()}(
    item_id: str,
    service: {service_name}Service = Depends(get_{service_name.lower()}_service)
):
    """Delete a {service_name.lower()} resource"""
    try:
        success = await service.delete_{service_name.lower()}(item_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"{service_name} not found")
        return {{"message": f"{service_name} {{item_id}} deleted successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting {service_name.lower()} {{item_id}}: {{e}}")
        raise HTTPException(status_code=500, detail=str(e))
'''
    
    def _generate_service_class(self, service_name: str) -> str:
        """Generate service layer class"""
        return f'''"""
Service layer for {service_name}
"""

import uuid
from typing import List, Optional
from datetime import datetime
import logging

from app.models.{service_name.lower()}_models import {service_name}Request, {service_name}Response
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class {service_name}Service:
    """Service class for {service_name} operations"""
    
    def __init__(self):
        self.settings = get_settings()
        # Initialize any required dependencies here
        # e.g., database connections, external APIs, etc.
    
    async def create_{service_name.lower()}(self, request: {service_name}Request) -> {service_name}Response:
        """Create a new {service_name.lower()} resource"""
        try:
            # Generate unique ID
            item_id = str(uuid.uuid4())
            
            # Process the request
            logger.info(f"Processing {service_name.lower()} creation: {{item_id}}")
            
            # Here you would typically:
            # 1. Validate the request data
            # 2. Store in database
            # 3. Perform any business logic
            # 4. Return the created resource
            
            # For now, return a mock response
            response = {service_name}Response(
                id=item_id,
                name=request.name,
                description=request.description,
                status="created",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            logger.info(f"Successfully created {service_name.lower()}: {{item_id}}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating {service_name.lower()}: {{e}}")
            raise
    
    async def get_{service_name.lower()}(self, item_id: str) -> Optional[{service_name}Response]:
        """Get a {service_name.lower()} resource by ID"""
        try:
            logger.info(f"Retrieving {service_name.lower()}: {{item_id}}")
            
            # Here you would typically:
            # 1. Query the database
            # 2. Return the resource if found
            
            # For now, return None (not found)
            return None
            
        except Exception as e:
            logger.error(f"Error getting {service_name.lower()} {{item_id}}: {{e}}")
            raise
    
    async def list_{service_name.lower()}s(self, skip: int = 0, limit: int = 100) -> List[{service_name}Response]:
        """List {service_name.lower()} resources"""
        try:
            logger.info(f"Listing {service_name.lower()}s: skip={{skip}}, limit={{limit}}")
            
            # Here you would typically:
            # 1. Query the database with pagination
            # 2. Return the list of resources
            
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error listing {service_name.lower()}s: {{e}}")
            raise
    
    async def delete_{service_name.lower()}(self, item_id: str) -> bool:
        """Delete a {service_name.lower()} resource"""
        try:
            logger.info(f"Deleting {service_name.lower()}: {{item_id}}")
            
            # Here you would typically:
            # 1. Check if resource exists
            # 2. Delete from database
            # 3. Return success status
            
            # For now, return False (not found)
            return False
            
        except Exception as e:
            logger.error(f"Error deleting {service_name.lower()} {{item_id}}: {{e}}")
            raise
    
    async def process_{service_name.lower()}(self, item_id: str) -> None:
        """Background processing for {service_name.lower()}"""
        try:
            logger.info(f"Processing {service_name.lower()} in background: {{item_id}}")
            
            # Here you would typically:
            # 1. Perform long-running operations
            # 2. Update the resource status
            # 3. Send notifications if needed
            
            # Simulate some processing time
            import asyncio
            await asyncio.sleep(1)
            
            logger.info(f"Background processing completed for {service_name.lower()}: {{item_id}}")
            
        except Exception as e:
            logger.error(f"Error in background processing for {service_name.lower()} {{item_id}}: {{e}}")
            raise
'''
    
    def _generate_models(self, service_name: str) -> str:
        """Generate Pydantic models"""
        return f'''"""
Data models for {service_name}
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class {service_name}Status(str, Enum):
    """Status enumeration for {service_name}"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class {service_name}Request(BaseModel):
    """Request model for creating {service_name}"""
    name: str = Field(..., description="Name of the {service_name.lower()}")
    description: Optional[str] = Field(None, description="Description of the {service_name.lower()}")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {{
            "example": {{
                "name": "Example {service_name}",
                "description": "An example {service_name.lower()} for testing",
                "metadata": {{"key": "value"}}
            }}
        }}


class {service_name}Response(BaseModel):
    """Response model for {service_name}"""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name of the {service_name.lower()}")
    description: Optional[str] = Field(None, description="Description of the {service_name.lower()}")
    status: {service_name}Status = Field(..., description="Current status")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_schema_extra = {{
            "example": {{
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Example {service_name}",
                "description": "An example {service_name.lower()} for testing",
                "status": "completed",
                "metadata": {{"key": "value"}},
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }}
        }}


class {service_name}ListResponse(BaseModel):
    """Response model for listing {service_name}s"""
    items: List[{service_name}Response] = Field(..., description="List of {service_name.lower()}s")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")
    
    class Config:
        json_schema_extra = {{
            "example": {{
                "items": [],
                "total": 0,
                "skip": 0,
                "limit": 100
            }}
        }}


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")
    
    class Config:
        json_schema_extra = {{
            "example": {{
                "error": "Resource not found",
                "detail": "The requested {service_name.lower()} was not found",
                "code": "NOT_FOUND"
            }}
        }}
'''
    
    def _generate_requirements(self) -> str:
        """Generate requirements.txt file using VWE standardized versions"""
        self.logger.info(f"Generating requirements.txt with VWE standardized versions")
        
        # Log version usage
        self.logger.info(f"Using FastAPI {self.versions['fastapi']}, Pydantic {self.versions['pydantic']}, SQLAlchemy {self.versions['sqlalchemy']}")
        
        return f'''# FastAPI and web framework
fastapi=={self.versions['fastapi']}
uvicorn[standard]=={self.versions['uvicorn']}
pydantic=={self.versions['pydantic']}
pydantic-settings=={self.versions['pydantic-settings']}

# Database
sqlalchemy=={self.versions['sqlalchemy']}
alembic=={self.versions['alembic']}

# Redis
redis=={self.versions['redis']}
hiredis==2.2.3

# HTTP client
httpx=={self.versions['httpx']}
aiohttp=={self.versions['aiohttp']}

# Data processing
numpy=={self.versions['numpy']}
pandas=={self.versions['pandas']}
pillow=={self.versions['pillow']}

# Utilities
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
isort==5.12.0
flake8==6.1.0

# VWE specific
rq=={self.versions['rq']}
celery=={self.versions['celery']}
'''
    
    def _generate_dockerfile(self, service_name: str) -> str:
        """Generate Dockerfile"""
        return f'''FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    
    def _generate_readme(self, service_name: str, description: str, 
                        version: str, author: str) -> str:
        """Generate README for the service"""
        return f'''# {service_name}

{description or f"A FastAPI service for Valheim World Engine"}

## Version
{version}

## Author
{author}

## Description
This service was generated using the Valheim World Engine Python generator.

## Features
- FastAPI web framework
- Async/await support
- Pydantic data validation
- Automatic API documentation
- Docker support
- Health check endpoints
- CORS middleware
- Background task processing

## Installation

### Using pip
```bash
pip install -r requirements.txt
```

### Using Docker
```bash
docker build -t {service_name.lower()} .
docker run -p 8000:8000 {service_name.lower()}
```

## Usage

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API Documentation
Once the service is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration
The service uses environment variables for configuration. Create a `.env` file:

```env
DEBUG=false
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./{service_name.lower()}.db
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
```

## Testing
```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app tests/
```

## Generated Files
- `app/main.py` - Main FastAPI application
- `app/core/config.py` - Configuration settings
- `app/api/routes/{service_name.lower()}.py` - API routes
- `app/services/{service_name.lower()}_service.py` - Service layer
- `app/models/{service_name.lower()}_models.py` - Data models
- `requirements.txt` - Python dependencies
- `Dockerfile` - Docker configuration
- `tests/test_{service_name.lower()}.py` - Test cases
- `README.md` - This file

## License
Generated by Valheim World Engine - See project license for details.
'''
    
    def _generate_tests(self, service_name: str) -> str:
        """Generate test file"""
        return f'''"""
Tests for {service_name}
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.models.{service_name.lower()}_models import {service_name}Request, {service_name}Response


client = TestClient(app)


class Test{service_name}API:
    """Test cases for {service_name} API endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "{service_name}"
    
    def test_create_{service_name.lower()}_success(self):
        """Test successful {service_name.lower()} creation"""
        request_data = {{
            "name": "Test {service_name}",
            "description": "Test description",
            "metadata": {{"key": "value"}}
        }}
        
        with patch("app.api.routes.{service_name.lower()}.get_{service_name.lower()}_service") as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.create_{service_name.lower()}.return_value = {service_name}Response(
                id="test-id",
                name="Test {service_name}",
                description="Test description",
                status="created",
                metadata={{"key": "value"}}
            )
            mock_service.return_value = mock_service_instance
            
            response = client.post("/api/v1/{service_name.lower()}/", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test {service_name}"
            assert data["status"] == "created"
    
    def test_get_{service_name.lower()}_not_found(self):
        """Test getting non-existent {service_name.lower()}"""
        with patch("app.api.routes.{service_name.lower()}.get_{service_name.lower()}_service") as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.get_{service_name.lower()}.return_value = None
            mock_service.return_value = mock_service_instance
            
            response = client.get("/api/v1/{service_name.lower()}/nonexistent-id")
            assert response.status_code == 404
    
    def test_list_{service_name.lower()}s(self):
        """Test listing {service_name.lower()}s"""
        with patch("app.api.routes.{service_name.lower()}.get_{service_name.lower()}_service") as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.list_{service_name.lower()}s.return_value = []
            mock_service.return_value = mock_service_instance
            
            response = client.get("/api/v1/{service_name.lower()}/")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


class Test{service_name}Service:
    """Test cases for {service_name} service layer"""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        from app.services.{service_name.lower()}_service import {service_name}Service
        return {service_name}Service()
    
    @pytest.mark.asyncio
    async def test_create_{service_name.lower()}(self, service):
        """Test {service_name.lower()} creation in service layer"""
        request = {service_name}Request(
            name="Test {service_name}",
            description="Test description"
        )
        
        result = await service.create_{service_name.lower()}(request)
        assert result.name == "Test {service_name}"
        assert result.status == "created"
        assert result.id is not None
    
    @pytest.mark.asyncio
    async def test_get_{service_name.lower()}_not_found(self, service):
        """Test getting non-existent {service_name.lower()} in service layer"""
        result = await service.get_{service_name.lower()}("nonexistent-id")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_{service_name.lower()}s(self, service):
        """Test listing {service_name.lower()}s in service layer"""
        result = await service.list_{service_name.lower()}s()
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_delete_{service_name.lower()}_not_found(self, service):
        """Test deleting non-existent {service_name.lower()} in service layer"""
        result = await service.delete_{service_name.lower()}("nonexistent-id")
        assert result is False
'''
    
    def create_data_processor(self, processor_name: str = "DataProcessor") -> Dict[str, str]:
        """Generate a specialized data processor service"""
        return self.create_fastapi_service(
            service_name=processor_name,
            description="Processes Valheim world data for VWE",
            version="1.0.0",
            author="VWE"
        )
    
    def create_rendering_service(self, service_name: str = "RenderingService") -> Dict[str, str]:
        """Generate a specialized rendering service"""
        return self.create_fastapi_service(
            service_name=service_name,
            description="Renders Valheim world maps for VWE",
            version="1.0.0",
            author="VWE"
        )


def main():
    """Example usage of the Python generator"""
    generator = PythonGenerator()
    
    # Generate a basic service
    print("Generating basic FastAPI service...")
    files = generator.create_fastapi_service(
        service_name="VWE_ExampleService",
        description="Example service generated by VWE Python generator",
        version="1.0.0",
        author="VWE"
    )
    
    print("Generated files:")
    for file_type, file_path in files.items():
        print(f"  {file_type}: {file_path}")
    
    # Generate specialized services
    print("\\nGenerating data processor service...")
    generator.create_data_processor()
    
    print("\\nGenerating rendering service...")
    generator.create_rendering_service()
    
    print("\\nPython generator example complete!")


if __name__ == "__main__":
    main()
