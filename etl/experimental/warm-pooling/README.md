# Warm Engine Pooling - Strategy 2

**Status:** Experimental
**Created:** 2025-10-10
**Expected Performance:** 50-65% reduction (3min → 1-1.5min sustained)

## Overview

This experimental ETL approach implements **Strategy 2: Warm Container Pool with Pre-initialized Valheim State** as identified in the 2025-10-10 optimization analysis.

### The Problem

Traditional world generation follows this flow:
```
Request → Spin up container (10s) → Start Valheim server (60-90s) → Generate world (60s) → Export (20s) → Shutdown (5s)
Total: ~3 minutes (175 seconds)
```

**Bottleneck:** The Valheim server startup (60-90 seconds) happens for EVERY world generation.

### The Solution

Keep Valheim servers **already running** in a pool of warm engines:
```
Request → Get warm engine (instant) → Send console command (10-20s) → Generate world (60s) → Export (20s) → Reset (5s)
Total: ~1-1.5 minutes (70-90 seconds sustained)
```

**Key Innovation:** Eliminate the 60-90 second server startup by keeping engines pre-initialized.

## Architecture

### Components

1. **`warm_engine_pool_manager.py`**
   - Manages a pool of pre-initialized Valheim servers
   - Handles engine lifecycle (creation, allocation, reset, shutdown)
   - Monitors engine health and state transitions
   - Supports parallel job processing with multiple engines

2. **`orchestrator.py`**
   - High-level interface for world generation
   - Integrates with VWE ETL pipeline
   - Manages data directories and file organization
   - Handles caching and result validation

3. **`data/`** (auto-created)
   - Standard VWE data structure per seed
   - `seeds/{seed_hash}/raw/`, `extracted/`, `processed/`, `renders/`

## Engine States

Each warm engine transitions through these states:

```
STARTING → READY → GENERATING → EXPORTING → RESETTING → READY
                        ↓
                     ERROR
```

- **STARTING:** Valheim server is booting up
- **READY:** Engine is idle and ready to accept jobs
- **GENERATING:** Processing a world generation job
- **EXPORTING:** BepInEx is exporting biome/heightmap data
- **RESETTING:** Cleaning up after job completion
- **ERROR:** Engine encountered an error and needs manual intervention

## Configuration

Default configuration in `WarmEngineConfig`:

```python
base_image = "vwe-bepinex-gen1:latest"
max_warm_containers = 3              # Pool size: 3 engines for parallel jobs
container_ttl_minutes = 120          # Keep engines alive for 2 hours
engine_startup_timeout = 120         # Max wait for Valheim to start (seconds)
world_gen_timeout = 300              # Max wait for world generation (5 minutes)
auto_reset_after_job = True          # Automatically reset engine after each job
max_jobs_per_engine = 10             # Restart engine after N jobs (prevent memory leaks)
```

## Usage

### Basic Usage

```python
from orchestrator import WarmPoolOrchestrator

# Create orchestrator
orchestrator = WarmPoolOrchestrator()

# Initialize warm engine pool (do this once at startup)
orchestrator.initialize_pool(pool_size=3)

# Generate worlds (near-instant allocation)
result = orchestrator.generate_world("MySeedName")

# Check result
if result["success"]:
    print(f"Generated in {result['total_time']:.1f}s")
    print(f"Data directory: {result['data_dir']}")
```

### Advanced Usage

```python
from warm_engine_pool_manager import WarmEnginePoolManager

# Create manager
manager = WarmEnginePoolManager()

# Create specific warm engines
engine1 = manager.create_warm_engine("engine-primary")
engine2 = manager.create_warm_engine("engine-secondary")

# Generate world on specific engine
result = manager.generate_world(
    seed="TestSeed",
    seed_hash="abc123...",
    job_id="job-001",
    engine_id="engine-primary"  # Use specific engine
)

# Get pool status
status = manager.get_status()
print(f"Pool has {status['pool_size']} engines")
for engine_id, engine_info in status['engines'].items():
    print(f"  {engine_id}: {engine_info['state']} ({engine_info['jobs_processed']} jobs)")
```

## Performance Characteristics

### First World Generation
- **Time:** ~3 minutes (same as traditional approach)
- **Reason:** Warm engine pool needs to be initialized

### Subsequent Generations
- **Time:** ~1-1.5 minutes (50-65% reduction)
- **Reason:** Engines are already running, no server startup needed

### Parallel Processing
- With 3 warm engines, can process 3 worlds simultaneously
- Effective throughput: ~3-5 worlds per minute (vs. ~0.33 worlds/min traditional)

## Implementation Details

### Dynamic World Loading

The core innovation is loading new worlds without restarting the server. Current implementation uses two approaches:

**Approach 1: Console Commands**
```python
# Send console command to running server
container.exec_run("echo 'load_world {seed}' > /tmp/vwe_commands.txt")
```

**Approach 2: Signal-based Reload**
```python
# Write new environment to file
container.exec_run(f"echo 'WORLD_NAME={seed}' > /config/vwe_reload_env.txt")
# Send signal to trigger reload
container.exec_run("pkill -SIGUSR1 valheim_server")
```

**Note:** Both approaches may require a custom BepInEx plugin to handle runtime world changes, as standard Valheim servers typically need to restart to change worlds. This is the main area for future development.

### Health Monitoring

Engines are monitored for:
- Container status (running/stopped)
- Log output (error detection)
- Job completion (timeout detection)
- Memory usage (via Docker resource limits)

### Automatic Reset

After each job, engines are automatically reset:
1. Clean up world data: `rm -rf /config/worlds_local/*`
2. Clear temporary files
3. If max jobs reached, restart container to prevent memory leaks
4. Transition back to READY state

## Known Limitations

### Current Limitations

1. **Dynamic World Loading:** Requires custom plugin or server modification
   - Standard Valheim servers need restart to change worlds
   - May need RCON-like interface or custom console handler
   - **Mitigation:** Fast container restart (~30s) still better than full startup

2. **Memory Leaks:** Long-running servers may accumulate memory
   - **Mitigation:** Automatic restart after N jobs (configurable)
   - **Mitigation:** Container memory limits (4GB default)

3. **Resource Usage:** Warm engines consume resources while idle
   - **Mitigation:** Configurable TTL (2 hours default)
   - **Mitigation:** Automatic cleanup of expired engines

4. **Concurrent Jobs:** Limited by pool size
   - **Mitigation:** Configurable pool size (default: 3)
   - **Mitigation:** Auto-scaling could be added in future

### Future Improvements

1. **Custom World Loader Plugin:** BepInEx plugin that accepts runtime world changes
2. **RCON Integration:** Use RCON protocol for world loading commands
3. **Auto-scaling:** Dynamically adjust pool size based on demand
4. **Persistent Pool:** Keep pool alive across orchestrator restarts
5. **Metrics & Monitoring:** Prometheus metrics for pool performance

## Comparison to Other Strategies

| Strategy | First Gen | Sustained | Complexity | Parallel |
|----------|-----------|-----------|------------|----------|
| **Traditional** | 3 min | 3 min | Low | No |
| **Warm Pooling (this)** | 3 min | 1-1.5 min | Medium | Yes (3x) |
| **Adaptive Sampling** | 1-1.5 min | 1-1.5 min | Medium | No |
| **Parallel Chunks** | 45-60 sec | 45-60 sec | High | Yes (4-9x) |

**Advantages:**
- Excellent sustained performance for multiple generations
- Parallel processing capability
- Builds on existing Docker infrastructure
- Lower complexity than parallel chunks

**Disadvantages:**
- First generation still takes full time (pool initialization)
- Requires custom plugin for optimal performance
- Higher resource usage while idle

## Testing & Validation

### Unit Tests
```bash
# TODO: Add unit tests
python -m pytest tests/
```

### Integration Tests
```bash
# Test warm engine creation
python warm_engine_pool_manager.py

# Test full orchestration
python orchestrator.py
```

### Performance Benchmarks
```bash
# TODO: Add benchmark script
# Should compare:
# - Traditional vs warm pool performance
# - First generation vs sustained generation
# - Single vs parallel processing
```

## Migration Path

This is an **experimental** approach. To promote to stable:

1. ✅ Implement core warm engine pool manager
2. ✅ Implement orchestrator integration
3. ⏳ Develop custom BepInEx plugin for runtime world loading
4. ⏳ Validate performance improvements with real data
5. ⏳ Comprehensive testing with multiple seeds
6. ⏳ Documentation of edge cases and failure modes
7. ⏳ Production hardening (error recovery, monitoring)

## References

- **Historical Analysis:** `etl/archive/legacy/BEPINEX_OPTIMIZATION_ANALYSIS.md`
- **Docker Strategy:** `global/docker/DOCKER_STRATEGY.md`
- **Warm Container Manager:** `global/docker/warm_container_manager.py`
- **Optimization Roadmap:** `README.md` § 8.1

## Contributing

This is an experimental approach. Contributions welcome:

1. Test with different seeds and document results
2. Develop custom BepInEx plugin for runtime world loading
3. Implement missing TODOs in orchestrator.py
4. Add performance benchmarks
5. Improve error handling and recovery

## License

Same as parent project (Valheim World Engine)
