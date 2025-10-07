import os
from pydantic import BaseModel


class Settings(BaseModel):
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    data_dir: str = os.getenv("DATA_DIR", os.path.abspath(os.path.join(os.getcwd(), "data")))
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")

    valheim_image: str = os.getenv("VALHEIM_IMAGE", "lloesche/valheim-server:latest")
    valheim_branch: str = os.getenv("VALHEIM_BRANCH", "public")
    stage1_timeout_sec: int = int(os.getenv("STAGE1_TIMEOUT_SEC", "900"))
    stage1_stable_sec: int = int(os.getenv("STAGE1_STABLE_SEC", "10"))

    sqlite_path: str = os.getenv("SQLITE_PATH", os.path.join(os.getcwd(), "data", "valhem_dev.db"))
    rq_workers: int = int(os.getenv("RQ_WORKERS", "1"))

    # Mapping standards
    render_resolution_px: int = int(os.getenv("RENDER_RESOLUTION_PX", "2048"))
    world_size_meters: int = 21000
    meters_per_pixel: float = world_size_meters / render_resolution_px


settings = Settings()  # type: ignore[arg-type]
