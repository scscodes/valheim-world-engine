# Valheim World Engine
This project is the spiritual successor and functional evolution of the widely adopted, community-managed website `valheim-map.world`. The intent is to optimize performance and accuracy, and build a foundation for more advanced client-side features.

## Directory & Terminology
```
docs/
  - 4096x4096_Map_hnLycKKCMI.png    # Exported seed image from `valheim-map.world`
  - REFERENCES.md                   # Web links, resources for guidance
  - seed.db.analysis.txt            # Previous run of `file_analyzer` on hnLycKKCMI db
  - seed.fwl.analysis.txt           # Previous run of `file_analyzer` on hnLycKKCMI fwl
scripts/                            # Standalone, non-project files
  - file_analyzer.js
client/
  - src/
server/
  - database/
  - api/
  - src/
```

Normalized Terms:
- WE: acronym to describe THIS project (World Engine)
- Client: client-side, frontend, browser, user-facing
- Server: server-side, backend, data-intensive logic, inaccessible to users
- World | Seed: synonyms; case-sensitive string, the generated environment or its representation

## MVP Functionality
- Client accepts a seed as input (or creates one)
- Server data pipeline/ETL manages seed/world lifecycle
- Client fetches map layers, renders to scale

## Tech Stack
Assume latest, stable, compatible versions unless explicitly stated.

### General Purpose
- Docker compose
- Docker: Redis
- Docker: Valheim game server

### Server
- Python
- FastAPI; API, async-first
- Database; SQLite (MVP)

### Client
- Next.js