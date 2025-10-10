import os
from pydantic import BaseModel


class Settings(BaseModel):
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    data_dir: str = os.getenv("DATA_DIR", os.path.abspath(os.path.join(os.getcwd(), "data")))
    host_data_dir: str = os.getenv("HOST_DATA_DIR", os.getenv("DATA_DIR", os.path.abspath(os.path.join(os.getcwd(), "data"))))
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")

    valheim_image: str = os.getenv("VALHEIM_IMAGE", "lloesche/valheim-server:latest")
    worldgen_runner_image: str = os.getenv("WORLDGEN_RUNNER_IMAGE", "vwe/worldgen-runner:latest")
    valheim_branch: str = os.getenv("VALHEIM_BRANCH", "public")
    server_name: str = os.getenv("SERVER_NAME", "Valheim World Engine")
    server_pass: str = os.getenv("SERVER_PASS", "secret12345")
    valheim_install_cache_dir: str = os.getenv(
        "VALHEIM_INSTALL_CACHE_DIR",
        os.path.join(os.getenv("REPO_ROOT", "/workspace"), ".cache", "valheim-install"),
    )
    steamcmd_cache_dir: str = os.getenv(
        "STEAMCMD_CACHE_DIR",
        os.path.join(os.getenv("REPO_ROOT", "/workspace"), ".cache", "steamcmd"),
    )
    stage1_timeout_sec: int = int(os.getenv("STAGE1_TIMEOUT_SEC", "300"))  # 5 minutes with graceful shutdown
    stage1_stable_sec: int = int(os.getenv("STAGE1_STABLE_SEC", "30"))
    pipeline_timeout_sec: int = int(os.getenv("PIPELINE_TIMEOUT_SEC", "1800"))

    sqlite_path: str = os.getenv("SQLITE_PATH", os.path.join(os.getcwd(), "data", "valheim_dev.db"))
    rq_workers: int = int(os.getenv("RQ_WORKERS", "1"))
    try:
        host_uid: int | None = int(os.getenv("HOST_UID")) if os.getenv("HOST_UID") else None
    except Exception:
        host_uid = None
    try:
        host_gid: int | None = int(os.getenv("HOST_GID")) if os.getenv("HOST_GID") else None
    except Exception:
        host_gid = None

    # Mapping standards
    render_resolution_px: int = int(os.getenv("RENDER_RESOLUTION_PX", "2048"))
    world_size_meters: int = 21000
    meters_per_pixel: float = world_size_meters / render_resolution_px

    # Host repo paths for container orchestration
    repo_root: str = os.getenv("REPO_ROOT", "/workspace")
    plugins_host_dir: str = os.getenv("PLUGINS_HOST_DIR", os.path.join(os.getenv("REPO_ROOT", "/workspace"), "docker", "valheim-server", "plugins"))


settings = Settings()  # type: ignore[arg-type]
