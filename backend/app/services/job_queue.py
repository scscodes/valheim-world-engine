import rq
import redis
from rq.job import Job
from app.core.config import settings


def get_redis_connection() -> redis.Redis:
	return redis.from_url(settings.redis_url)


def get_queue(name: str = "vwe") -> rq.Queue:
	conn = get_redis_connection()
	return rq.Queue(name, connection=conn)


def set_seed_job(seed_hash: str, job_id: str, ttl_seconds: int = 7 * 24 * 3600) -> None:
	client = get_redis_connection()
	client.set(f"vwe:seed_job:{seed_hash}", job_id, ex=ttl_seconds)


def get_seed_job(seed_hash: str) -> str | None:
	client = get_redis_connection()
	val = client.get(f"vwe:seed_job:{seed_hash}")
	return val.decode("utf-8") if val else None


def fetch_job(job_id: str) -> Job:
	return Job.fetch(job_id, connection=get_redis_connection())
