# Valheim World Generation Pipeline

## Overview
Automated pipeline for generating Valheim worlds using Docker containers with lloesche/valheim-server image. Generates both `.db` (world data) and `.fwl` (metadata) files in ~2-3 minutes.

## Architecture

### Components
- **Backend:** FastAPI server with Redis job queue
- **Worker:** RQ worker processing generation jobs
- **Valheim Server:** lloesche/valheim-server Docker container
- **Storage:** SQLite database + file system

### Data Flow
1. API receives seed request → Job queued in Redis
2. Worker picks up job → Starts Valheim container
3. Container generates world → Graceful shutdown triggers save
4. Both `.db` and `.fwl` files created → Job complete

## Key Implementation Details

### Graceful Shutdown Approach
Uses lloesche's built-in `PRE_SERVER_SHUTDOWN_HOOK` to trigger save before container shutdown:

```python
"PRE_SERVER_SHUTDOWN_HOOK": "echo 'save' | nc -U /tmp/valheim-console 2>/dev/null || supervisorctl signal USR1 valheim-server || echo 'save' > /proc/$(pgrep -f valheim_server)/fd/0 2>/dev/null || true"
```

### Workflow
1. **World generation:** ~60-90 seconds
2. **Graceful shutdown + save:** ~10-30 seconds  
3. **File stability check:** ~5 seconds
4. **Total time:** ~2-3 minutes

### Mount Structure
```yaml
volumes:
  {seed_dir}: /config  # Server creates worlds_local/ inside
```

Files created at: `{seed_dir}/worlds_local/{seed}.db|.fwl`

### Environment Variables
- `WORLD_NAME`: Seed string (Valheim uses this as the seed)
- `SERVER_PUBLIC`: "0" (private server)
- `BEPINEX`: "1" (enabled for future plugins)
- `PUID`/`PGID`: File ownership (1000/1000)
- `PRE_SERVER_SHUTDOWN_HOOK`: Save trigger command

## Configuration

### Timeouts
- **Generation timeout:** 300s (5 minutes)
- **Graceful shutdown:** 10s (no users)
- **Force stop fallback:** 5s

### File Detection
- Monitors logs for "Failed to place all" (world generation complete)
- Triggers graceful shutdown immediately
- Checks for both `.db` and `.fwl` files with stability timeout

## Testing

```bash
# Start services
docker compose -f docker/docker-compose.yml up -d

# Trigger generation
curl -X POST http://localhost:8000/api/v1/seeds/generate \
  -H "Content-Type: application/json" \
  -d '{"seed": "TestWorld"}'

# Monitor logs
tail -f data/seeds/*/extracted/worldgen_logs.txt
```

## Success Criteria
- ✅ Both `.db` and `.fwl` files created
- ✅ Total time < 3 minutes
- ✅ Clean container shutdown
- ✅ No data corruption

## Troubleshooting

### No .db file created
- Check graceful shutdown logs for "VWE: Graceful shutdown initiated"
- Verify `PRE_SERVER_SHUTDOWN_HOOK` is set
- Check file permissions (PUID/PGID)

### Container timeouts
- Increase `STAGE1_TIMEOUT_SEC` if needed
- Check for stuck containers: `docker ps | grep vwe-worldgen`

### File ownership issues
- Ensure `HOST_UID` and `HOST_GID` are set correctly
- Check container logs for permission errors

## References
- [lloesche/valheim-server-docker](https://github.com/lloesche/valheim-server-docker)
- [Valheim Dedicated Server Guide](https://www.valheimgame.com/support/a-guide-to-dedicated-servers/)
- [MakeFwl Tool](https://github.com/CrystalFerrai/MakeFwl)
