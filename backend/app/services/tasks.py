import os
import time
from rq import get_current_job
from app.core.config import settings


def simulate_pipeline(seed: str, seed_hash: str) -> dict:
	seed_dir = os.path.join(settings.data_dir, "seeds", seed_hash)
	raw_dir = os.path.join(seed_dir, "raw")
	extracted_dir = os.path.join(seed_dir, "extracted")
	processed_dir = os.path.join(seed_dir, "processed")
	renders_dir = os.path.join(seed_dir, "renders")
	for d in (raw_dir, extracted_dir, processed_dir, renders_dir):
		os.makedirs(d, exist_ok=True)
	# Simulate stages with progress updates
	job = get_current_job()
	stages = ["generation", "extraction", "processing", "rendering", "caching"]
	for i, stage in enumerate(stages, start=1):
		if job is not None:
			job.meta["current_stage"] = stage
			job.meta["progress"] = int(i * 100 / len(stages))
			job.save_meta()
		time.sleep(0.2)
	return {"seed": seed, "seed_hash": seed_hash, "status": "completed"}
