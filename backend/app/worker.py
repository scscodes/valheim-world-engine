from rq import Worker
from app.services.job_queue import get_redis_connection


def main() -> None:
	conn = get_redis_connection()
	Worker(queues=["vwe"], connection=conn).work()


if __name__ == "__main__":
	main()
