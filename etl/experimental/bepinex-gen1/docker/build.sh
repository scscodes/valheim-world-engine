#!/bin/bash
# Build custom VWE BepInEx Gen1 Docker image

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

IMAGE_NAME="vwe-bepinex-gen1"
IMAGE_TAG="latest"

echo "Building $IMAGE_NAME:$IMAGE_TAG..."
echo "Using plugins from: $PROJECT_ROOT/plugins"

# Build the image
cd "$SCRIPT_DIR"
docker build \
    --tag "$IMAGE_NAME:$IMAGE_TAG" \
    --file Dockerfile \
    "$PROJECT_ROOT"

echo ""
echo "✅ Image built successfully: $IMAGE_NAME:$IMAGE_TAG"
echo ""
echo "To test the image:"
echo "  docker run --rm $IMAGE_NAME:$IMAGE_TAG"
