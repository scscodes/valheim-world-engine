from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.routes.health import router as health_router
from app.api.routes.seeds import router as seeds_router

app = FastAPI(title="Valhem World Engine")

app.add_middleware(
	CORSMiddleware,
	allow_origins=[o.strip() for o in settings.allowed_origins.split(",")],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Mount static data directory for rendered assets
app.mount(
	"/static/seeds",
	StaticFiles(directory=f"{settings.data_dir}/seeds"),
	name="seeds-static",
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(seeds_router, prefix="/api/v1")
