from rq import Worker
from app.services.job_queue import get_redis_connection
from app.services.job_queue import get_redis_connection


def main() -> None:
	conn = get_redis_connection()
	Worker(
		queues=["vwe"],
		connection=conn,
		default_worker_ttl=600,
		job_monitoring_interval=5,
	).work()


if __name__ == "__main__":
	main()
