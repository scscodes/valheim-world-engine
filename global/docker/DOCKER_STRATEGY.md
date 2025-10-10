u# VWE Docker Management Strategy

## Overview

This document outlines the comprehensive Docker management strategy for the Valheim World Engine project, ensuring consistency, scalability, and maintainability across all containerized services.

## Current VWE Docker Architecture

### Service Types
1. **Core Services** (Always Running)
   - `redis` - Cache and job queue
   - `backend` - FastAPI API server
   - `worker` - RQ background worker

2. **World Generation Services** (On-Demand)
   - `valheim-bepinex` - Valheim server with BepInEx plugins
   - `valheim-procedural` - Procedural metadata generation
   - `worldgen-runner` - Base image for world generation

3. **Utility Services** (As Needed)
   - `validator` - Environment validation
   - `dev-tools` - Development utilities

## VWE Docker Standards

### Base Images
```yaml
base_images:
  python: "python:3.11-slim"      # Python services
  node: "node:18-alpine"          # Frontend services  
  redis: "redis:7-alpine"         # Cache/queue
  ubuntu: "ubuntu:22.04"          # System utilities
  valheim: "lloesche/valheim-server:latest"  # Valheim server
```

### VWE Custom Images
```yaml
vwe_images:
  worldgen-runner: "vwe/worldgen-runner:latest"
  valheim-bepinex: "vwe/valheim-bepinex:latest"
  valheim-procedural: "vwe/valheim-procedural:latest"
  backend: "vwe/backend:latest"
  worker: "vwe/worker:latest"
```

### Port Standards
```yaml
ports:
  backend: 8000
  redis: 6379
  valheim: 2456
  valheim_query: 2457
```

### Volume Standards
```yaml
volumes:
  data: "/app/data"                    # Application data
  config: "/config"                    # Configuration files
  plugins: "/config/bepinex/plugins"   # BepInEx plugins
  worlds: "/config/worlds_local"       # Valheim world files
```

## Container Lifecycle Management

### 1. Short-Running Containers (World Generation)
**Use Case**: Generate Valheim worlds, process data
**Pattern**: Create → Run → Collect Results → Destroy

```python
# Example from world_generator.py
def run_world_generation(seed: str, seed_hash: str) -> dict:
    container_name = f"vwe-worldgen-{seed_hash}-{uuid.uuid4().hex[:8]}"
    
    # Create container with unique name
    container = docker_client.containers.run(
        image="vwe/valheim-bepinex:latest",
        name=container_name,
        detach=True,
        volumes={
            f"{host_data_dir}/seeds/{seed_hash}": {"bind": "/config", "mode": "rw"}
        },
        environment={
            "WORLD_NAME": seed,
            "VWE_DATAEXPORT_ENABLED": "true"
        }
    )
    
    # Monitor completion
    # Collect results
    # Clean up container
    container.remove()
```

**Key Principles**:
- Unique container names to avoid conflicts
- Automatic cleanup after completion
- Result collection before destruction
- Proper error handling and logging

### 2. Medium-Running Containers (Services)
**Use Case**: API servers, workers, background processes
**Pattern**: Start → Monitor → Restart on Failure → Stop

```yaml
# docker-compose.yml
services:
  backend:
    image: vwe/backend:latest
    restart: unless-stopped
    healthcheck:
      test: ["curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Key Principles**:
- Health checks for monitoring
- Restart policies for reliability
- Resource limits for stability
- Graceful shutdown handling

### 3. Long-Running Containers (Infrastructure)
**Use Case**: Redis, databases, persistent services
**Pattern**: Start → Persist Data → Monitor → Maintain

```yaml
services:
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: always
```

**Key Principles**:
- Data persistence with volumes
- Always restart policy
- Regular backups
- Monitoring and alerting

## Generator Integration

### Docker Generator Features
The `docker_generator.py` provides:

1. **Service Dockerfiles** - Generate optimized Dockerfiles for each service type
2. **Compose Configurations** - Create docker-compose files with VWE standards
3. **Health Checks** - Generate appropriate health check scripts
4. **Management Scripts** - Create start/stop/status scripts
5. **Environment Templates** - Generate .env templates

### Usage Examples

```python
from docker_generator import DockerGenerator

# Generate Python service Dockerfile
generator = DockerGenerator()
files = generator.create_service_dockerfile(
    service_name="VWE_DataProcessor",
    service_type="python",
    description="Data processing service"
)

# Generate complete VWE suite
suite = generator.create_vwe_compose_suite()
```

## Container Orchestration Patterns

### 1. Development Environment
```bash
# Start core services
docker compose up -d redis backend worker

# Start with Valheim server
docker compose --profile bepinex up -d

# Development with hot reload
docker compose -f docker-compose.dev.yml up
```

### 2. Production Environment
```bash
# Production deployment
docker compose -f docker-compose.prod.yml up -d

# With resource limits and monitoring
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. World Generation Workflow
```python
# 1. Start core services
docker compose up -d redis backend worker

# 2. Generate world (creates temporary container)
curl -X POST http://localhost:8000/api/v1/seeds/generate \
  -d '{"seed": "TestWorld"}'

# 3. Monitor progress
curl http://localhost:8000/api/v1/seeds/{hash}/status

# 4. Container automatically cleaned up after completion
```

## Resource Management

### Memory Limits
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

### CPU Limits
```yaml
services:
  worker:
    deploy:
      resources:
        limits:
          cpus: '1.0'
        reservations:
          cpus: '0.5'
```

### Storage Management
```yaml
volumes:
  redis_data:
    driver: local
  world_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/host/data
```

## Security Considerations

### 1. User Permissions
```dockerfile
# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
```

### 2. Network Isolation
```yaml
networks:
  vwe-internal:
    driver: bridge
    internal: true
  vwe-external:
    driver: bridge
```

### 3. Secret Management
```yaml
services:
  backend:
    environment:
      - REDIS_PASSWORD_FILE=/run/secrets/redis_password
    secrets:
      - redis_password
```

## Monitoring and Logging

### 1. Health Checks
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

### 2. Log Management
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 3. Metrics Collection
```yaml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

## Best Practices

### 1. Container Design
- **Single Responsibility**: One process per container
- **Stateless**: Containers should be stateless when possible
- **Immutable**: Don't modify running containers
- **Small Images**: Use multi-stage builds and alpine images

### 2. Data Management
- **Volumes for Persistence**: Use named volumes for data that needs to persist
- **Bind Mounts for Development**: Use bind mounts for development
- **Backup Strategy**: Regular backups of persistent data

### 3. Networking
- **Internal Networks**: Use internal networks for service communication
- **Port Management**: Expose only necessary ports
- **Service Discovery**: Use Docker's built-in DNS for service discovery

### 4. Security
- **Non-Root Users**: Run containers as non-root users
- **Image Scanning**: Regularly scan images for vulnerabilities
- **Secret Management**: Use Docker secrets for sensitive data

## Troubleshooting

### Common Issues

1. **Container Name Conflicts**
   ```bash
   # Solution: Use unique names with timestamps/UUIDs
   container_name = f"vwe-worldgen-{seed_hash}-{uuid.uuid4().hex[:8]}"
   ```

2. **Permission Issues**
   ```bash
   # Solution: Set proper PUID/PGID
   environment:
     - PUID=${HOST_UID:-1000}
     - PGID=${HOST_GID:-1000}
   ```

3. **Resource Exhaustion**
   ```bash
   # Solution: Set resource limits
   deploy:
     resources:
       limits:
         memory: 512M
   ```

4. **Network Connectivity**
   ```bash
   # Solution: Use Docker networks
   networks:
     - vwe-internal
   ```

### Debugging Commands
```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f service_name

# Execute commands in container
docker compose exec service_name bash

# Check resource usage
docker stats

# Clean up
docker system prune -a
```

## Future Enhancements

### 1. Kubernetes Migration
- Prepare for potential Kubernetes deployment
- Use Kubernetes-native patterns where possible
- Maintain Docker Compose for development

### 2. Service Mesh
- Consider Istio for advanced networking
- Implement circuit breakers and retries
- Add distributed tracing

### 3. CI/CD Integration
- Automated image building
- Security scanning in pipeline
- Automated deployment strategies

## Conclusion

This Docker management strategy ensures that VWE's containerized services are:
- **Consistent**: All services follow the same patterns
- **Scalable**: Can handle varying workloads
- **Maintainable**: Easy to update and modify
- **Reliable**: Proper error handling and recovery
- **Secure**: Following security best practices

The integration with the generator system ensures that new services automatically follow these standards, maintaining consistency across the entire VWE ecosystem.
