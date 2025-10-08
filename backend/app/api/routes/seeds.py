from fastapi import APIRouter
from pydantic import BaseModel
from rq.job import Job

from app.core.utils import seed_to_hash
from app.core.config import settings
from app.services.job_queue import (
	get_queue,
	get_redis_connection,
	set_seed_job,
	get_seed_job,
	fetch_job,
	ping_redis,
	list_seed_job_keys,
	debug_read_seed_job,
)
from app.services.tasks import simulate_pipeline

router = APIRouter(prefix="/seeds")


class GenerateRequest(BaseModel):
	seed: str
	force_regenerate: bool = False


@router.post("/generate")
async def generate_seed(req: GenerateRequest) -> dict:
	seed_hash = seed_to_hash(req.seed)
	q = get_queue()
	job: Job = q.enqueue(simulate_pipeline, req.seed, seed_hash, job_timeout=settings.pipeline_timeout_sec)
	job_id = getattr(job, "id", None) or job.get_id()
	set_seed_job(seed_hash, job_id)
	# Optional: immediate read-back to confirm write
	debug = debug_read_seed_job(seed_hash)
	return {"job_id": job_id, "seed_hash": seed_hash, "status": "pending", "message": "queued", "debug_value": debug}


@router.get("/{seed_hash}/status")
async def seed_status(seed_hash: str) -> dict:
	# Quick connectivity signal
	redis_ok = ping_redis()
	job_id = get_seed_job(seed_hash)
	if not job_id:
		return {
			"job_id": None,
			"status": "not_found",
			"current_stage": None,
			"progress": 0,
			"redis_ok": redis_ok,
			"debug_keys": list_seed_job_keys(5) if redis_ok else [],
			"debug_value": debug_read_seed_job(seed_hash) if redis_ok else {},
		}
	job = fetch_job(job_id)
	status = job.get_status(refresh=True)
	meta = job.meta or {}
	return {
		"job_id": job.id,
		"status": status,
		"current_stage": meta.get("current_stage"),
		"progress": meta.get("progress", 0),
		"generation_status": meta.get("generation_status"),
	}


@router.get("/{seed_hash}/data")
async def seed_data(seed_hash: str) -> dict:
	return {
		"seed": "stub",
		"seed_hash": seed_hash,
		"metadata": {"world_size": 21000, "sea_level": 30.0, "generated_at": None},
		"layers": {
			"base_layers": {
				"biomes": f"/static/seeds/{seed_hash}/renders/biomes_layer.webp",
				"land_sea": f"/static/seeds/{seed_hash}/renders/land_sea_layer.webp",
				"heightmap": f"/static/seeds/{seed_hash}/renders/heightmap_layer.webp",
			},
			"overlays": {"shoreline": f"/static/seeds/{seed_hash}/renders/shoreline_overlay.webp"},
		},
		"statistics": {},
	}
