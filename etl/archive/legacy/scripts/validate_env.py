import os
import sys
import json
import socket

try:
	import docker  # type: ignore
except Exception as e:
	docker = None


REQUIRED_ENV = [
	"REDIS_URL",
	"DATA_DIR",
	"HOST_DATA_DIR",
	"VALHEIM_IMAGE",
]


def check_env() -> dict:
	missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
	return {"missing": missing, "values": {k: os.getenv(k) for k in REQUIRED_ENV}}


def can_connect_docker() -> tuple[bool, str]:
	if docker is None:
		return False, "docker SDK not importable"
	try:
		client = docker.from_env()
		v = client.version()
		return True, json.dumps({"ApiVersion": v.get("ApiVersion"), "Version": v.get("Version")})
	except Exception as e:
		return False, str(e)


def main() -> None:
	ok, msg = can_connect_docker()
	env = check_env()
	print("Docker:", "ok" if ok else "fail", msg)
	print("Env missing:", env["missing"])  # type: ignore[index]
	for k, v in env["values"].items():  # type: ignore[index]
		print(f"{k}={v}")


if __name__ == "__main__":
	main()
