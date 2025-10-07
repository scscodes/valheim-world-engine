import hashlib
import re


def sanitize_seed(seed: str) -> str:
	# Limit to reasonable length and printable chars
	seed = seed.strip()
	return seed[:256]


def seed_to_hash(seed: str) -> str:
	clean = sanitize_seed(seed)
	return hashlib.sha256(clean.encode("utf-8")).hexdigest()
