import json
import os
import re
import time
from datetime import datetime
from typing import Iterable

import docker
import uuid
from rq import get_current_job
from app.core.config import settings


LOG_PATTERNS = [
	re.compile(r"Game server connected", re.IGNORECASE),
	re.compile(r"Zonesystem Start", re.IGNORECASE),
	re.compile(r"Export complete", re.IGNORECASE),
]


def build_worldgen_plan(seed: str, seed_hash: str) -> dict:
	seed_dir = os.path.join(settings.data_dir, "seeds", seed_hash)
	raw_dir = os.path.join(seed_dir, "raw")
	extracted_dir = os.path.join(seed_dir, "extracted")
	plugins_host = settings.plugins_host_dir

	# Host paths for Docker volume mounts (must be absolute on the host)
	host_seed_dir = os.path.join(settings.host_data_dir, "seeds", seed_hash)
	host_raw_dir = os.path.join(host_seed_dir, "raw")

	container_worlds = "/config/worlds_local"
	container_plugins = "/config/BepInEx/plugins"

	return {
		"generated_at": datetime.utcnow().isoformat() + "Z",
		"image": settings.worldgen_runner_image or settings.valheim_image,
		"env": {
			"WORLD_NAME": seed_hash,
			"WORLD_SEED": seed,
			"SERVER_PUBLIC": "0",
			"TZ": "UTC",
			"UPDATE_ON_START": "1",
			"SERVER_NAME": settings.server_name,
			"SERVER_PASS": settings.server_pass,
			# Enable BepInEx if supported by the image (no-op if not)
			"BEPINEX": "1",
		},
		"volumes": {
			host_raw_dir: container_worlds,
			plugins_host: container_plugins,
		},
		"readiness": {
			"log_regex": [
				"Game server connected",
				"Zonesystem Start",
				"Export complete",
			],
			"stable_seconds": settings.stage1_stable_sec,
			"timeout_seconds": settings.stage1_timeout_sec,
		},
		"expected_outputs": {
			"raw": [
				os.path.join(raw_dir, f"{seed_hash}.db"),
				os.path.join(raw_dir, f"{seed_hash}.fwl"),
			],
			"extracted": [
				os.path.join(extracted_dir, "biomes.json"),
				os.path.join(extracted_dir, "heightmap.npy"),
			],
		},
	}


def write_plan_file(seed: str, seed_hash: str) -> str:
	seed_dir = os.path.join(settings.data_dir, "seeds", seed_hash)
	extracted_dir = os.path.join(seed_dir, "extracted")
	os.makedirs(extracted_dir, exist_ok=True)
	plan = build_worldgen_plan(seed, seed_hash)
	path = os.path.join(extracted_dir, "worldgen_plan.json")
	with open(path, "w", encoding="utf-8") as f:
		json.dump(plan, f, indent=2)
	return path


def _files_stable(paths: Iterable[str], stable_seconds: int) -> bool:
	latest_mtime = 0.0
	for p in paths:
		if not os.path.exists(p):
			return False
		latest_mtime = max(latest_mtime, os.path.getmtime(p))
	return (time.time() - latest_mtime) >= stable_seconds


def _choose_present_files(base_paths: list[str]) -> list[str]:
	"""For each base path, prefer the base file if it exists, else consider a `.old` backup variant."""
	chosen: list[str] = []
	for p in base_paths:
		if os.path.exists(p):
			chosen.append(p)
			continue
		alt = p + ".old"
		if os.path.exists(alt):
			chosen.append(alt)
	return chosen


def _chown_recursive(root: str, uid: int, gid: int) -> None:
	for dirpath, dirnames, filenames in os.walk(root):
		for d in dirnames:
			p = os.path.join(dirpath, d)
			try:
				os.chown(p, uid, gid)
			except Exception:
				pass
		for f in filenames:
			p = os.path.join(dirpath, f)
			try:
				os.chown(p, uid, gid)
			except Exception:
				pass
	try:
		os.chown(root, uid, gid)
	except Exception:
		pass


def run_world_generation(seed: str, seed_hash: str) -> dict:
	plan = build_worldgen_plan(seed, seed_hash)
	seed_dir = os.path.join(settings.data_dir, "seeds", seed_hash)
	raw_dir = os.path.join(seed_dir, "raw")
	extracted_dir = os.path.join(seed_dir, "extracted")
	os.makedirs(raw_dir, exist_ok=True)
	os.makedirs(extracted_dir, exist_ok=True)
	log_path = os.path.join(extracted_dir, "worldgen_logs.txt")

	# Initialize docker client safely
	try:
		client = docker.from_env()
	except Exception as e:
		with open(log_path, "w", encoding="utf-8") as lf:
			lf.write(f"Docker client error: {e}\n")
		return {
			"log_match": False,
			"raw_present": False,
			"extracted_present": False,
			"log_path": log_path,
			"timed_out": False,
			"lines_written": 1,
		}

	volumes = {}
	for host_path, container_path in plan["volumes"].items():
		os.makedirs(host_path, exist_ok=True)
		volumes[host_path] = {"bind": container_path, "mode": "rw"}

	# Create container; if this fails (e.g., docker.sock permissions), capture error to logs
	container = None
	try:
		# Ensure no stale container with the base name exists
		base_name = f"vwe-worldgen-{seed_hash[:12]}"
		try:
			stale = client.containers.get(base_name)
			stale.remove(force=True)
		except Exception:
			pass
		# Use a unique name per run to avoid 409 conflicts
		unique_name = f"{base_name}-{uuid.uuid4().hex[:6]}"
		container = client.containers.run(
			image=plan["image"],
			environment=plan["env"],
			volumes=volumes,
			detach=True,
			tty=False,
			name=unique_name,
			remove=True,
		)
	except Exception as e:
		with open(log_path, "w", encoding="utf-8") as lf:
			lf.write(f"Docker run error: {e}\n")
		return {
			"log_match": False,
			"raw_present": False,
			"extracted_present": False,
			"log_path": log_path,
			"timed_out": False,
			"lines_written": 1,
		}

	deadline = time.time() + plan["readiness"]["timeout_seconds"]
	log_match = False
	lines_written = 0
	timed_out = False
	job = None
	try:
		job = get_current_job()
	except Exception:
		job = None
	try:
		# Stream combined stdout/stderr without TTY to get full lines
		log_stream = container.logs(stream=True, follow=True, stdout=True, stderr=True, timestamps=False)
		line_buffer = ""
		with open(log_path, "w", encoding="utf-8") as lf:
			for chunk in log_stream:
				text = chunk.decode("utf-8", errors="ignore")
				line_buffer += text
				while "\n" in line_buffer:
					line, line_buffer = line_buffer.split("\n", 1)
					lf.write(line + "\n")
					lines_written += 1
					# Heuristic progress detection for SteamCMD states
					if job is not None:
						# Downloading/Updating percentages
						m = re.search(r"(\d{1,3})%", line)
						if m:
							pct = int(m.group(1))
							job.meta["current_stage"] = "generation"
							job.meta["progress"] = max(5, min(90, pct))
							job.save_meta()
						elif "Validating" in line or "validating" in line:
							job.meta["current_stage"] = "generation"
							job.meta["progress"] = max(job.meta.get("progress", 10), 75)
							job.save_meta()
						elif "Success! App" in line and "installed" in line:
							job.meta["current_stage"] = "generation"
							job.meta["progress"] = max(job.meta.get("progress", 10), 90)
							job.save_meta()

					for pat in LOG_PATTERNS:
						if pat.search(line):
							log_match = True
							break
					# Check for output files presence and stability (allow without log readiness)
					present = _choose_present_files(plan["expected_outputs"]["raw"]) 
					if len(present) == len(plan["expected_outputs"]["raw"]) and _files_stable(present, plan["readiness"]["stable_seconds"]):
						if job is not None:
							job.meta["current_stage"] = "generation"
							job.meta["progress"] = max(job.meta.get("progress", 10), 95)
							job.save_meta()
						break
					if time.time() > deadline:
						timed_out = True
						break
		# Flush any remaining buffered text
		if line_buffer:
			with open(log_path, "a", encoding="utf-8") as lf:
				lf.write(line_buffer)
	finally:
		# Stop the container; exporter should have emitted artifacts by now.
		try:
			container.stop(timeout=10)
		except Exception:
			pass

	present = _choose_present_files(plan["expected_outputs"]["raw"]) 
	status = {
		"log_match": log_match,
		"raw_present": len(present) == len(plan["expected_outputs"]["raw"]),
		"extracted_present": all(os.path.exists(p) for p in plan["expected_outputs"]["extracted"]),
		"log_path": log_path,
		"timed_out": timed_out,
		"lines_written": lines_written,
	}

	# Reassign ownership on host to avoid root-owned artifacts
	if settings.host_uid is not None and settings.host_gid is not None:
		try:
			_chown_recursive(seed_dir, settings.host_uid, settings.host_gid)
		except Exception:
			pass
	return status


def plan_world_generation(seed: str, seed_hash: str) -> dict:
	"""
	Stage 1 stub: write a docker run plan and readiness checklist to disk.
	"""
	path = write_plan_file(seed, seed_hash)
	return {"plan_path": path}
