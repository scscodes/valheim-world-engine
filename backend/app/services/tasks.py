import os
import time
from rq import get_current_job
from rq.timeouts import JobTimeoutException
from app.core.config import settings
from app.services.world_generator import plan_world_generation, run_world_generation


def simulate_pipeline(seed: str, seed_hash: str) -> dict:
    job = get_current_job()
    seed_dir = os.path.join(settings.data_dir, "seeds", seed_hash)
    raw_dir = os.path.join(seed_dir, "raw")
    extracted_dir = os.path.join(seed_dir, "extracted")
    processed_dir = os.path.join(seed_dir, "processed")
    renders_dir = os.path.join(seed_dir, "renders")
    for d in (raw_dir, extracted_dir, processed_dir, renders_dir):
        os.makedirs(d, exist_ok=True)

    # Stage 1: plan + generation with robust error handling
    try:
        plan_world_generation(seed, seed_hash)
        if job is not None:
            job.meta["current_stage"] = "generation"
            job.meta["progress"] = 10
            job.save_meta()

        gen_status = run_world_generation(seed, seed_hash)
        if job is not None:
            job.meta["generation_status"] = gen_status
            job.save_meta()
    except JobTimeoutException as e:
        os.makedirs(extracted_dir, exist_ok=True)
        log_path = os.path.join(extracted_dir, "worldgen_logs.txt")
        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(f"Pipeline timeout: {e}\n")
        if job is not None:
            job.meta["generation_status"] = {
                "log_match": False,
                "raw_present": False,
                "extracted_present": False,
                "log_path": log_path,
                "timed_out": True,
                "lines_written": 1,
            }
            job.save_meta()
        raise
    except Exception as e:
        # Always leave a breadcrumb log file and meta
        os.makedirs(extracted_dir, exist_ok=True)
        log_path = os.path.join(extracted_dir, "worldgen_logs.txt")
        with open(log_path, "w", encoding="utf-8") as lf:
            lf.write(f"Stage 1 error: {e}\n")
        if job is not None:
            job.meta["generation_status"] = {
                "log_match": False,
                "raw_present": False,
                "extracted_present": False,
                "log_path": log_path,
                "timed_out": False,
                "lines_written": 1,
            }
            job.save_meta()

    # Simulate remaining stages with progress updates
    stages = ["generation", "extraction", "processing", "rendering", "caching"]
    for i, stage in enumerate(stages, start=1):
        if job is not None:
            job.meta["current_stage"] = stage
            job.meta["progress"] = int(i * 100 / len(stages))
            job.save_meta()
        time.sleep(0.2)
    return {"seed": seed, "seed_hash": seed_hash, "status": "completed"}
