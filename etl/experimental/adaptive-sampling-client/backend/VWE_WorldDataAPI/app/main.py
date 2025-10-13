"""
VWE World Data API
FastAPI application for serving Valheim world data from adaptive sampling
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import worlds
from .core.config import get_settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load settings (singleton)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    logger.info("Starting VWE World Data API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Data root: {settings.DATA_ROOT}")
    logger.info(f"Data root exists: {settings.DATA_ROOT.exists()}")
    
    # Initialize world loader with correct data path
    from .api.routes.worlds import initialize_loader
    initialize_loader(settings.DATA_ROOT)
    
    yield
    logger.info("Shutting down VWE World Data API...")


# Create FastAPI app
app = FastAPI(
    title="VWE World Data API",
    description="API for accessing and visualizing Valheim world data from adaptive sampling",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(worlds.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "VWE World Data API",
        "version": "1.0.0",
        "description": "API for Valheim world data visualization",
        "endpoints": {
            "docs": "/docs",
            "worlds": "/api/v1/worlds",
            "health": "/api/v1/worlds/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "VWE World Data API",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
