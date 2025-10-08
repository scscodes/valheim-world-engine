import os
import sqlite3

DB_PATH = os.getenv("SQLITE_PATH", os.path.join(os.getcwd(), "data", "valheim_dev.db"))

DDL = """
CREATE TABLE IF NOT EXISTS seeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed_original TEXT NOT NULL,
    seed_hash TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    generation_duration_seconds INTEGER,
    file_size_mb REAL
);

CREATE TABLE IF NOT EXISTS layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed_id INTEGER NOT NULL,
    layer_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seed_id) REFERENCES seeds(id)
);

CREATE TABLE IF NOT EXISTS world_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed_id INTEGER NOT NULL,
    stat_key TEXT NOT NULL,
    stat_value TEXT NOT NULL,
    FOREIGN KEY (seed_id) REFERENCES seeds(id)
);

CREATE TABLE IF NOT EXISTS generation_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,
    seed_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    current_stage TEXT,
    progress INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_seed_hash ON seeds(seed_hash);
CREATE INDEX IF NOT EXISTS idx_seed_layer ON layers(seed_id, layer_type);
CREATE INDEX IF NOT EXISTS idx_seed_stats ON world_statistics(seed_id);
CREATE INDEX IF NOT EXISTS idx_job_id ON generation_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_status ON generation_jobs(status);
"""


def main() -> None:
	os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
	with sqlite3.connect(DB_PATH) as conn:
		conn.executescript(DDL)
		conn.commit()
	print(f"Initialized SQLite database at {DB_PATH}")


if __name__ == "__main__":
	main()
