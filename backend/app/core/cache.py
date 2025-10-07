import redis
from app.core.config import settings


def get_client() -> redis.Redis:
	return redis.from_url(settings.redis_url)
