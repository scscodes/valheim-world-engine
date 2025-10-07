from fastapi import APIRouter
from pydantic import BaseModel
from rq.job import Job

from app.core.utils import seed_to_hash
from app.services.job_queue import (
	get_queue,
	get_redis_connection,
	set_seed_job,
	get_seed_job,
	fetch_job,
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
	job: Job = q.enqueue(simulate_pipeline, req.seed, seed_hash)
	set_seed_job(seed_hash, job.id)
	return {"job_id": job.id, "seed_hash": seed_hash, "status": "pending", "message": "queued"}


@router.get("/{seed_hash}/status")
async def seed_status(seed_hash: str) -> dict:
	job_id = get_seed_job(seed_hash)
	if not job_id:
		return {"job_id": None, "status": "not_found", "current_stage": None, "progress": 0}
	job = fetch_job(job_id)
	status = job.get_status(refresh=True)
	meta = job.meta or {}
	return {
		"job_id": job.id,
		"status": status,
		"current_stage": meta.get("current_stage"),
		"progress": meta.get("progress", 0),
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
