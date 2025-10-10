import rq
import redis
from typing import List
from rq.job import Job
from app.core.config import settings


def get_redis_connection() -> redis.Redis:
	return redis.from_url(settings.redis_url)


def get_queue(name: str = "vwe") -> rq.Queue:
	conn = get_redis_connection()
	return rq.Queue(name, connection=conn)


def set_seed_job(seed_hash: str, job_id: str, ttl_seconds: int = 7 * 24 * 3600) -> None:
	client = get_redis_connection()
	client.set(name=f"vwe:seed_job:{seed_hash}", value=job_id, ex=ttl_seconds)


def get_seed_job(seed_hash: str) -> str | None:
	client = get_redis_connection()
	val = client.get(f"vwe:seed_job:{seed_hash}")
	# Return decoded value, even if empty string
	return val.decode("utf-8") if val is not None else None


def fetch_job(job_id: str) -> Job:
	return Job.fetch(job_id, connection=get_redis_connection())


def ping_redis() -> bool:
	try:
		client = get_redis_connection()
		return bool(client.ping())
	except Exception:
		return False


def list_seed_job_keys(limit: int = 20) -> List[str]:
	"""Return up to `limit` seed_job keys for debugging purposes."""
	client = get_redis_connection()
	keys: List[str] = []
	cursor = 0
	pattern = "vwe:seed_job:*"
	while True:
		cursor, batch = client.scan(cursor=cursor, match=pattern, count=limit)
		for k in batch:
			keys.append(k.decode("utf-8"))
			if len(keys) >= limit:
				return keys
		if cursor == 0:
			break
	return keys


def debug_read_seed_job(seed_hash: str) -> dict:
	client = get_redis_connection()
	key = f"vwe:seed_job:{seed_hash}"
	val = client.get(key)
	decoded = val.decode("utf-8") if val is not None else None
	length = len(val) if val is not None else 0
	return {"key": key, "value": decoded, "length": length}
