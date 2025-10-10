#!/usr/bin/env python3
"""
Docker Generator for Valheim World Engine
Generates Docker configurations, compose files, and container orchestration
"""

import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Add global logging to path
sys.path.append(str(Path(__file__).parent.parent / "logging"))
from generator_logging import GeneratorLogManager


class DockerGenerator:
    """Generator for Docker configurations and container orchestration"""
    
    # Standardized VWE Docker versions and configurations
    VWE_DOCKER_STANDARDS = {
        "base_images": {
            "python": "python:3.11-slim",
            "node": "node:18-alpine", 
            "redis": "redis:7-alpine",
            "ubuntu": "ubuntu:22.04",
            "valheim": "lloesche/valheim-server:latest"
        },
        "vwe_images": {
            "worldgen-runner": "vwe/worldgen-runner:latest",
            "valheim-bepinex": "vwe/valheim-bepinex:latest",
            "valheim-procedural": "vwe/valheim-procedural:latest",
            "backend": "vwe/backend:latest",
            "worker": "vwe/worker:latest"
        },
        "ports": {
            "backend": 8000,
            "redis": 6379,
            "valheim": 2456,
            "valheim_query": 2457
        },
        "volumes": {
            "data": "/app/data",
            "config": "/config",
            "plugins": "/config/bepinex/plugins",
            "worlds": "/config/worlds_local"
        },
        "environment": {
            "data_dir": "/app/data",
            "redis_url": "redis://redis:6379/0",
            "timezone": "UTC"
        }
    }
    
    def __init__(self, base_path: str = ".", override_config: Optional[Dict[str, Any]] = None):
        self.base_path = Path(base_path)
        self.templates_dir = self.base_path / "templates" / "docker"
        self.output_dir = self.base_path / "output" / "docker"
        
        # Setup enhanced logging
        self.log_manager = GeneratorLogManager("docker-generator")
        self.logger = self.log_manager.logger
        
        # Handle configuration overrides with clear logging
        self.config = self.VWE_DOCKER_STANDARDS.copy()
        if override_config:
            self.logger.warning("=" * 60)
            self.logger.warning("⚠️  DOCKER CONFIG OVERRIDES DETECTED - NON-STANDARD CONFIGURATION")
            self.logger.warning("=" * 60)
            for section, overrides in override_config.items():
                if section in self.config:
                    for key, value in overrides.items():
                        if key in self.config[section]:
                            old_value = self.config[section][key]
                            self.config[section][key] = value
                            self.logger.warning(f"OVERRIDE: {section}.{key} {old_value} → {value}")
                        else:
                            self.config[section][key] = value
                            self.logger.warning(f"ADDED: {section}.{key} {value}")
                else:
                    self.config[section] = overrides
                    self.logger.warning(f"NEW SECTION: {section} {overrides}")
            self.logger.warning("=" * 60)
            self.logger.warning("⚠️  USING OVERRIDDEN DOCKER CONFIG - MAY CAUSE COMPATIBILITY ISSUES")
            self.logger.warning("=" * 60)
    
    def create_service_dockerfile(self, service_name: str, service_type: str = "python", 
                                description: str = "", version: str = "1.0.0") -> Dict[str, str]:
        """Generate Dockerfile for a VWE service"""
        
        self.logger.info(f"Creating Dockerfile for {service_type} service: {service_name}")
        
        service_dir = self.output_dir / service_name
        service_dir.mkdir(parents=True, exist_ok=True)
        
        files_created = {}
        
        # Generate Dockerfile based on service type
        if service_type == "python":
            dockerfile_content = self._generate_python_dockerfile(service_name, version)
        elif service_type == "node":
            dockerfile_content = self._generate_node_dockerfile(service_name, version)
        elif service_type == "valheim":
            dockerfile_content = self._generate_valheim_dockerfile(service_name, version)
        else:
            raise ValueError(f"Unsupported service type: {service_type}")
        
        dockerfile_file = service_dir / "Dockerfile"
        dockerfile_file.write_text(dockerfile_content)
        files_created["dockerfile"] = str(dockerfile_file)
        
        # Generate .dockerignore
        dockerignore_content = self._generate_dockerignore(service_type)
        dockerignore_file = service_dir / ".dockerignore"
        dockerignore_file.write_text(dockerignore_content)
        files_created["dockerignore"] = str(dockerignore_file)
        
        # Generate docker-compose override
        compose_content = self._generate_service_compose(service_name, service_type)
        compose_file = service_dir / "docker-compose.override.yml"
        compose_file.write_text(compose_content)
        files_created["compose_override"] = str(compose_file)
        
        # Generate health check script
        healthcheck_content = self._generate_healthcheck(service_name, service_type)
        healthcheck_file = service_dir / "healthcheck.sh"
        healthcheck_file.write_text(healthcheck_content)
        healthcheck_file.chmod(0o755)
        files_created["healthcheck"] = str(healthcheck_file)
        
        # Generate README
        readme_content = self._generate_docker_readme(service_name, service_type, description, version)
        readme_file = service_dir / "README.md"
        readme_file.write_text(readme_content)
        files_created["readme"] = str(readme_file)
        
        return files_created
    
    def _generate_python_dockerfile(self, service_name: str, version: str) -> str:
        """Generate Python service Dockerfile"""
        base_image = self.config["base_images"]["python"]
        
        return f'''FROM {base_image}

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose port
EXPOSE {self.config["ports"]["backend"]}

# Health check
COPY healthcheck.sh /usr/local/bin/healthcheck.sh
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD /usr/local/bin/healthcheck.sh

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    
    def _generate_node_dockerfile(self, service_name: str, version: str) -> str:
        """Generate Node.js service Dockerfile"""
        base_image = self.config["base_images"]["node"]
        
        return f'''FROM {base_image}

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --system --gid 1001 nodejs \\
    && adduser --system --uid 1001 nextjs

# Change ownership
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 3000

# Health check
COPY healthcheck.sh /usr/local/bin/healthcheck.sh
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD /usr/local/bin/healthcheck.sh

# Run the application
CMD ["npm", "start"]
'''
    
    def _generate_valheim_dockerfile(self, service_name: str, version: str) -> str:
        """Generate Valheim server Dockerfile"""
        base_image = self.config["base_images"]["valheim"]
        
        return f'''FROM {base_image}

# VWE Valheim Server with BepInEx Support
LABEL maintainer="VWE Team"
LABEL version="{version}"
LABEL description="Valheim server with VWE BepInEx plugins"

# Install additional dependencies for VWE
RUN apt-get update && apt-get install -y \\
    curl \\
    jq \\
    && rm -rf /var/lib/apt/lists/*

# Create VWE directories
RUN mkdir -p /config/bepinex/plugins \\
    /config/world_data \\
    /config/logs

# Copy VWE entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set environment variables
ENV BEPINEX=1
ENV VWE_ENABLED=true
ENV VWE_DATA_DIR=/config/world_data
ENV VWE_LOG_DIR=/config/logs

# Expose Valheim ports
EXPOSE {self.config["ports"]["valheim"]}/udp
EXPOSE {self.config["ports"]["valheim_query"]}/udp

# Health check
COPY healthcheck.sh /usr/local/bin/healthcheck.sh
HEALTHCHECK --interval=60s --timeout=30s --start-period=30s --retries=3 \\
    CMD /usr/local/bin/healthcheck.sh

# Use VWE entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["valheim-server"]
'''
    
    def _generate_dockerignore(self, service_type: str) -> str:
        """Generate .dockerignore file"""
        if service_type == "python":
            return '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Git
.git/
.gitignore

# Docker
Dockerfile
.dockerignore

# Logs
*.log
logs/

# Data
data/
*.db
*.sqlite

# Test
tests/
test_*
*_test.py

# Documentation
README.md
docs/
*.md
'''
        elif service_type == "node":
            return '''# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Next.js
.next/
out/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Git
.git/
.gitignore

# Docker
Dockerfile
.dockerignore

# Logs
*.log
logs/

# Data
data/
*.db
*.sqlite

# Test
tests/
test_*
*_test.*

# Documentation
README.md
docs/
*.md
'''
        else:
            return '''# General
*.log
logs/
data/
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Git
.git/
.gitignore

# Docker
Dockerfile
.dockerignore

# Documentation
README.md
docs/
*.md
'''
    
    def _generate_service_compose(self, service_name: str, service_type: str) -> str:
        """Generate docker-compose override for service"""
        port = self.config["ports"].get(service_type, 8000)
        
        return f'''version: '3.8'

services:
  {service_name}:
    build:
      context: .
      dockerfile: Dockerfile
    image: vwe/{service_name}:latest
    container_name: vwe-{service_name}
    ports:
      - "{port}:{port}"
    environment:
      - NODE_ENV=production
      - DATA_DIR={self.config["volumes"]["data"]}
      - REDIS_URL={self.config["environment"]["redis_url"]}
      - TZ={self.config["environment"]["timezone"]}
    volumes:
      - ../data:{self.config["volumes"]["data"]}
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["/usr/local/bin/healthcheck.sh"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: {self.config["base_images"]["redis"]}
    container_name: vwe-redis
    ports:
      - "{self.config["ports"]["redis"]}:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
'''
    
    def _generate_healthcheck(self, service_name: str, service_type: str) -> str:
        """Generate health check script"""
        if service_type == "python":
            return f'''#!/bin/bash
# Health check for {service_name}

# Check if the service is responding
curl -f http://localhost:8000/health > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Health check passed"
    exit 0
else
    echo "Health check failed"
    exit 1
fi
'''
        elif service_type == "node":
            return f'''#!/bin/bash
# Health check for {service_name}

# Check if the service is responding
curl -f http://localhost:3000/api/health > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Health check passed"
    exit 0
else
    echo "Health check failed"
    exit 1
fi
'''
        elif service_type == "valheim":
            return f'''#!/bin/bash
# Health check for {service_name}

# Check if Valheim server is running
pgrep -f "valheim_server.x86_64" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Valheim server is running"
    exit 0
else
    echo "Valheim server is not running"
    exit 1
fi
'''
        else:
            return f'''#!/bin/bash
# Health check for {service_name}

# Basic process check
pgrep -f "{service_name}" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Service is running"
    exit 0
else
    echo "Service is not running"
    exit 1
fi
'''
    
    def _generate_docker_readme(self, service_name: str, service_type: str, 
                               description: str, version: str) -> str:
        """Generate README for Docker service"""
        return f'''# {service_name} Docker Service

{description or f"Docker configuration for {service_name} service"}

## Version
{version}

## Service Type
{service_type.title()}

## Description
This Docker configuration was generated by the VWE Docker generator and follows VWE standards for containerization.

## Quick Start

### Build and Run
```bash
# Build the image
docker build -t vwe/{service_name}:latest .

# Run the container
docker run -d --name vwe-{service_name} -p {self.config["ports"].get(service_type, 8000)}:{self.config["ports"].get(service_type, 8000)} vwe/{service_name}:latest
```

### Using Docker Compose
```bash
# Start the service with dependencies
docker compose -f docker-compose.override.yml up -d

# View logs
docker compose -f docker-compose.override.yml logs -f {service_name}

# Stop the service
docker compose -f docker-compose.override.yml down
```

## Configuration

### Environment Variables
- `DATA_DIR`: Data directory path (default: {self.config["volumes"]["data"]})
- `REDIS_URL`: Redis connection URL (default: {self.config["environment"]["redis_url"]})
- `TZ`: Timezone (default: {self.config["environment"]["timezone"]})

### Volumes
- `../data:{self.config["volumes"]["data"]}`: Data persistence
- `redis_data:/data`: Redis data persistence

### Ports
- `{self.config["ports"].get(service_type, 8000)}:{self.config["ports"].get(service_type, 8000)}`: Service port

## Health Checks
The container includes a health check script that verifies the service is responding correctly.

## VWE Integration
This service is designed to work within the VWE ecosystem:
- Uses VWE standardized base images
- Follows VWE naming conventions
- Includes VWE-specific environment variables
- Compatible with VWE orchestration patterns

## Development
For development, you can mount the source code as a volume:
```bash
docker run -d --name vwe-{service_name}-dev \\
  -p {self.config["ports"].get(service_type, 8000)}:{self.config["ports"].get(service_type, 8000)} \\
  -v $(pwd):/app \\
  vwe/{service_name}:latest
```

## License
Generated by Valheim World Engine - See project license for details.
'''
    
    def create_warm_container_config(self, service_name: str, base_image: str) -> Dict[str, str]:
        """Generate warm container configuration for instant deployment"""
        
        self.logger.info(f"Creating warm container config for {service_name}")
        
        config_dir = self.output_dir / f"{service_name}-warm"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        files_created = {}
        
        # Warm container Dockerfile
        warm_dockerfile = self._generate_warm_dockerfile(service_name, base_image)
        dockerfile_file = config_dir / "Dockerfile.warm"
        dockerfile_file.write_text(warm_dockerfile)
        files_created["warm_dockerfile"] = str(dockerfile_file)
        
        # Warm container compose
        warm_compose = self._generate_warm_compose(service_name, base_image)
        compose_file = config_dir / "docker-compose.warm.yml"
        compose_file.write_text(warm_compose)
        files_created["warm_compose"] = str(compose_file)
        
        # Warm container manager script
        manager_script = self._generate_warm_manager_script(service_name)
        script_file = config_dir / "manage_warm_containers.py"
        script_file.write_text(manager_script)
        script_file.chmod(0o755)
        files_created["manager_script"] = str(script_file)
        
        # Warm container README
        readme_content = self._generate_warm_readme(service_name, base_image)
        readme_file = config_dir / "README.md"
        readme_file.write_text(readme_content)
        files_created["readme"] = str(readme_file)
        
        return files_created
    
    def _generate_warm_dockerfile(self, service_name: str, base_image: str) -> str:
        """Generate Dockerfile optimized for warm containers"""
        return f'''FROM {base_image}

# VWE Warm Container for {service_name}
LABEL maintainer="VWE Team"
LABEL description="Pre-warmed container for instant deployment"

# Install warm container dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    jq \\
    && rm -rf /var/lib/apt/lists/*

# Create warm container directories
RUN mkdir -p /config/warm \\
    /config/logs \\
    /config/cache

# Copy warm container initialization script
COPY warm_init.sh /usr/local/bin/warm_init.sh
RUN chmod +x /usr/local/bin/warm_init.sh

# Set warm container environment
ENV VWE_WARM_CONTAINER=true
ENV VWE_PRELOADED=true
ENV TZ=UTC

# Pre-warm the container
RUN /usr/local/bin/warm_init.sh

# Keep container alive
CMD ["sleep", "infinity"]
'''
    
    def _generate_warm_compose(self, service_name: str, base_image: str) -> str:
        """Generate docker-compose for warm containers"""
        return f'''version: '3.8'

services:
  {service_name}-warm:
    build:
      context: .
      dockerfile: Dockerfile.warm
    image: vwe/{service_name}-warm:latest
    container_name: vwe-{service_name}-warm
    environment:
      - VWE_WARM_CONTAINER=true
      - VWE_PRELOADED=true
      - TZ=UTC
    volumes:
      - warm_data:/config/warm
      - warm_logs:/config/logs
    restart: unless-stopped
    labels:
      - "vwe.type=warm-container"
      - "vwe.service={service_name}"

  warm-manager:
    build:
      context: .
      dockerfile: Dockerfile.warm
    image: vwe/warm-manager:latest
    container_name: vwe-warm-manager
    command: python manage_warm_containers.py
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - warm_data:/config/warm
    environment:
      - DOCKER_HOST=unix:///var/run/docker.sock
    restart: unless-stopped

volumes:
  warm_data:
    driver: local
  warm_logs:
    driver: local
'''
    
    def _generate_warm_manager_script(self, service_name: str) -> str:
        """Generate warm container management script"""
        return f'''#!/usr/bin/env python3
"""
Warm Container Manager for {service_name}
Manages pre-warmed containers for instant deployment
"""

import sys
import os
sys.path.append('/home/steve/projects/valheim-world-engine/global/docker')

from warm_container_manager import WarmContainerManager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Start warm container management for {service_name}"""
    logger.info(f"Starting warm container manager for {service_name}")
    
    manager = WarmContainerManager()
    
    # Start the service
    manager.start_warm_container_service()
    
    # Keep running
    import time
    try:
        while True:
            status = manager.get_status()
            logger.info(f"Warm containers: {{status['total_containers']}}")
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down warm container manager")

if __name__ == "__main__":
    main()
'''
    
    def _generate_warm_readme(self, service_name: str, base_image: str) -> str:
        """Generate README for warm container setup"""
        return f'''# {service_name} Warm Container Setup

Pre-warmed container configuration for instant deployment without startup delays.

## Overview

This setup eliminates the wait times associated with:
- Container startup
- SteamCMD downloads
- Valheim server initialization
- Plugin loading

## Quick Start

### Build Warm Container
```bash
# Build the warm container image
docker build -f Dockerfile.warm -t vwe/{service_name}-warm:latest .

# Start warm container service
docker compose -f docker-compose.warm.yml up -d
```

### Use Warm Container
```bash
# Clone warm container for instant job deployment
python manage_warm_containers.py

# Or use the warm container manager directly
from warm_container_manager import WarmContainerManager
manager = WarmContainerManager()
job_container = manager.clone_container_for_job("{service_name}", "seed-123", "job-456")
```

## Benefits

- **Instant Deployment**: No startup delays
- **Pre-warmed Environment**: All dependencies ready
- **Resource Efficient**: Shared base containers
- **Auto-cleanup**: Expired containers removed automatically

## Configuration

The warm container is configured with:
- Base image: {base_image}
- Pre-loaded volumes and environment
- Automatic cleanup after TTL
- Health monitoring

## Management

```bash
# Check warm container status
docker ps | grep warm

# View warm container logs
docker logs vwe-{service_name}-warm

# Clean up warm containers
docker system prune -f
```

## Integration

This warm container integrates with:
- VWE job queue system
- Docker orchestration
- Container cloning for jobs
- Automatic resource management
'''
    
    def create_vwe_compose_suite(self) -> Dict[str, str]:
        """Generate complete VWE Docker Compose suite"""
        self.logger.info("Creating VWE Docker Compose suite")
        
        suite_dir = self.output_dir / "vwe-suite"
        suite_dir.mkdir(parents=True, exist_ok=True)
        
        files_created = {}
        
        # Main compose file
        main_compose = self._generate_main_compose()
        main_file = suite_dir / "docker-compose.yml"
        main_file.write_text(main_compose)
        files_created["main_compose"] = str(main_file)
        
        # Development override
        dev_compose = self._generate_dev_compose()
        dev_file = suite_dir / "docker-compose.dev.yml"
        dev_file.write_text(dev_compose)
        files_created["dev_compose"] = str(dev_file)
        
        # Production override
        prod_compose = self._generate_prod_compose()
        prod_file = suite_dir / "docker-compose.prod.yml"
        prod_file.write_text(prod_compose)
        files_created["prod_compose"] = str(prod_file)
        
        # Environment template
        env_template = self._generate_env_template()
        env_file = suite_dir / ".env.template"
        env_file.write_text(env_template)
        files_created["env_template"] = str(env_file)
        
        # Management scripts
        scripts = self._generate_management_scripts()
        for script_name, script_content in scripts.items():
            script_file = suite_dir / script_name
            script_file.write_text(script_content)
            script_file.chmod(0o755)
            files_created[script_name] = str(script_file)
        
        return files_created
    
    def _generate_main_compose(self) -> str:
        """Generate main VWE Docker Compose file"""
        return f'''version: '3.8'

services:
  # Redis cache and job queue
  redis:
    image: {self.config["base_images"]["redis"]}
    container_name: vwe-redis
    ports:
      - "{self.config["ports"]["redis"]}:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Backend API service
  backend:
    build:
      context: ../../backend
      dockerfile: Dockerfile
    image: {self.config["vwe_images"]["backend"]}
    container_name: vwe-backend
    ports:
      - "{self.config["ports"]["backend"]}:8000"
    environment:
      - REDIS_URL={self.config["environment"]["redis_url"]}
      - DATA_DIR={self.config["volumes"]["data"]}
      - HOST_DATA_DIR=${{HOST_DATA_DIR:-${{PWD}}/data}}
      - REPO_ROOT=${{PWD}}
    volumes:
      - ../../backend:/app
      - ../../data:{self.config["volumes"]["data"]}
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Background worker service
  worker:
    build:
      context: ../../backend
      dockerfile: Dockerfile
    image: {self.config["vwe_images"]["worker"]}
    container_name: vwe-worker
    command: python -m app.worker
    user: "0:0"  # Root for Docker socket access
    environment:
      - REDIS_URL={self.config["environment"]["redis_url"]}
      - DATA_DIR={self.config["volumes"]["data"]}
      - HOST_DATA_DIR=${{HOST_DATA_DIR:-${{PWD}}/data}}
      - REPO_ROOT=${{PWD}}
    volumes:
      - ../../backend:/app
      - ../../data:{self.config["volumes"]["data"]}
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped

  # Valheim server with BepInEx (optional)
  valheim-bepinex:
    build:
      context: ../../
      dockerfile: docker/bepinex/Dockerfile
    image: {self.config["vwe_images"]["valheim-bepinex"]}
    container_name: vwe-valheim-bepinex
    profiles: ["bepinex"]
    user: "0:0"
    environment:
      - VWE_AUTOSAVE_ENABLED=true
      - VWE_DATAEXPORT_ENABLED=true
      - VWE_DATAEXPORT_DIR={self.config["volumes"]["worlds"]}
      - SERVER_NAME=${{SERVER_NAME:-Valheim World Engine}}
      - WORLD_NAME=${{WORLD_NAME:-TestWorld}}
      - SERVER_PASS=${{SERVER_PASS:-secret12345}}
      - SERVER_PORT={self.config["ports"]["valheim"]}
      - PUID=${{HOST_UID:-1000}}
      - PGID=${{HOST_GID:-1000}}
    volumes:
      - ../../data/seeds/${{WORLD_NAME:-TestWorld}}:/config
      - ../../bepinex/plugins:/config/bepinex/plugins:ro
    ports:
      - "{self.config["ports"]["valheim"]}:{self.config["ports"]["valheim"]}/udp"
      - "{self.config["ports"]["valheim_query"]}:{self.config["ports"]["valheim_query"]}/udp"
    restart: unless-stopped

volumes:
  redis_data:
    driver: local
'''
    
    def _generate_dev_compose(self) -> str:
        """Generate development override"""
        return f'''version: '3.8'

services:
  backend:
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ../../backend:/app
      - ../../data:{self.config["volumes"]["data"]}
      - /var/run/docker.sock:/var/run/docker.sock

  worker:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ../../backend:/app
      - ../../data:{self.config["volumes"]["data"]}
      - /var/run/docker.sock:/var/run/docker.sock

  # Development tools
  dev-tools:
    image: {self.config["base_images"]["python"]}
    container_name: vwe-dev-tools
    profiles: ["dev"]
    volumes:
      - ../../:/workspace
    working_dir: /workspace
    command: tail -f /dev/null
'''
    
    def _generate_prod_compose(self) -> str:
        """Generate production override"""
        return f'''version: '3.8'

services:
  backend:
    restart: always
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  worker:
    restart: always
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  redis:
    restart: always
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
'''
    
    def _generate_env_template(self) -> str:
        """Generate environment template"""
        return f'''# VWE Docker Environment Configuration
# Copy this file to .env and customize for your environment

# Data directories
HOST_DATA_DIR=/path/to/your/data
REPO_ROOT=/path/to/valheim-world-engine

# Valheim server configuration
SERVER_NAME=Valheim World Engine
WORLD_NAME=TestWorld
SERVER_PASS=your_secure_password_here
SERVER_PORT={self.config["ports"]["valheim"]}

# User/Group IDs (for file ownership)
HOST_UID=1000
HOST_GID=1000

# Redis configuration
REDIS_URL={self.config["environment"]["redis_url"]}

# Timezone
TZ={self.config["environment"]["timezone"]}

# VWE Plugin configuration
VWE_AUTOSAVE_ENABLED=true
VWE_AUTOSAVE_DELAY=2
VWE_DATAEXPORT_ENABLED=true
VWE_DATAEXPORT_FORMAT=both
VWE_DATAEXPORT_DIR=/config/world_data

# BepInEx configuration
BEPINEX=1
'''
    
    def _generate_management_scripts(self) -> Dict[str, str]:
        """Generate management scripts"""
        return {
            "start.sh": f'''#!/bin/bash
# Start VWE services

echo "Starting VWE services..."

# Start core services
docker compose up -d redis backend worker

echo "Core services started. Use 'docker compose --profile bepinex up -d' to start Valheim server."
''',
            "stop.sh": f'''#!/bin/bash
# Stop VWE services

echo "Stopping VWE services..."

docker compose down

echo "All services stopped."
''',
            "restart.sh": f'''#!/bin/bash
# Restart VWE services

echo "Restarting VWE services..."

docker compose restart

echo "Services restarted."
''',
            "logs.sh": f'''#!/bin/bash
# View VWE service logs

if [ -z "$1" ]; then
    echo "Usage: $0 <service_name>"
    echo "Available services: redis, backend, worker, valheim-bepinex"
    exit 1
fi

docker compose logs -f "$1"
''',
            "clean.sh": f'''#!/bin/bash
# Clean up VWE containers and volumes

echo "Cleaning up VWE containers..."

# Stop and remove containers
docker compose down

# Remove unused images
docker image prune -f

# Remove unused volumes (be careful!)
read -p "Remove unused volumes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker volume prune -f
fi

echo "Cleanup complete."
''',
            "status.sh": f'''#!/bin/bash
# Check VWE service status

echo "VWE Service Status:"
echo "==================="

# Check if services are running
for service in redis backend worker; do
    if docker compose ps "$service" | grep -q "Up"; then
        echo "✓ $service: Running"
    else
        echo "✗ $service: Stopped"
    fi
done

# Check Valheim server if running
if docker compose ps valheim-bepinex | grep -q "Up"; then
    echo "✓ valheim-bepinex: Running"
else
    echo "○ valheim-bepinex: Not started (use --profile bepinex)"
fi

echo ""
echo "Use './logs.sh <service>' to view logs"
'''
        }


def main():
    """Example usage of the Docker generator"""
    generator = DockerGenerator()
    
    # Generate individual service Dockerfiles
    print("Generating Docker configurations...")
    
    # Python service
    files = generator.create_service_dockerfile("VWE_DataProcessor", "python", "Data processing service")
    print(f"Generated Python service: {len(files)} files")
    
    # Node service  
    files = generator.create_service_dockerfile("VWE_MapViewer", "node", "Map visualization service")
    print(f"Generated Node service: {len(files)} files")
    
    # Valheim service
    files = generator.create_service_dockerfile("VWE_ValheimServer", "valheim", "Valheim server with BepInEx")
    print(f"Generated Valheim service: {len(files)} files")
    
    # Complete VWE suite
    files = generator.create_vwe_compose_suite()
    print(f"Generated VWE suite: {len(files)} files")
    
    print("\\nDocker generator example complete!")


if __name__ == "__main__":
    main()
