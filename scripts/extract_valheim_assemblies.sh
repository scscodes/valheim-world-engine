#!/usr/bin/env bash

# One-time extractor for Valheim server assemblies and (optionally) BepInEx core DLLs
# - Prefer extracting from a running container (e.g. lloesche/valheim-server)
# - Falls back to spinning up the image to copy files out, if no container provided
#
# Usage:
#   scripts/extract_valheim_assemblies.sh \
#     [--container <name-or-id> | --image <image>] \
#     [--output <abs-dir>] [--include-bepinex]
#
# Defaults:
#   --image lloesche/valheim-server:latest
#   --output <repo>/bepinex/plugins

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)
DEFAULT_OUTPUT="${REPO_ROOT}/bepinex/plugins"

CONTAINER_NAME=""
IMAGE_NAME="lloesche/valheim-server:latest"
OUTPUT_DIR="${DEFAULT_OUTPUT}"
INCLUDE_BEPINEX=false

usage() {
    echo "Usage: $0 [--container <name-or-id> | --image <image>] [--output <abs-dir>] [--include-bepinex]" >&2
    echo "\nOptions:" >&2
    echo "  --container <id>    Extract from a running container (preferred)" >&2
    echo "  --image <image>     Use this image if no container is provided (default: ${IMAGE_NAME})" >&2
    echo "  --output <dir>      Destination directory on host (default: ${DEFAULT_OUTPUT})" >&2
    echo "  --include-bepinex   Also extract BepInEx core DLLs if present in container/image" >&2
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Error: required command '$1' not found in PATH" >&2
        exit 1
    fi
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --container)
            CONTAINER_NAME="${2:-}"; shift 2;;
        --image)
            IMAGE_NAME="${2:-}"; shift 2;;
        --output)
            OUTPUT_DIR="${2:-}"; shift 2;;
        --include-bepinex)
            INCLUDE_BEPINEX=true; shift;;
        -h|--help)
            usage; exit 0;;
        *)
            echo "Unknown argument: $1" >&2
            usage; exit 1;;
    esac
done

# Sanity checks
require_cmd docker
require_cmd tar

# Create output directory
mkdir -p "${OUTPUT_DIR}"

echo "Output directory: ${OUTPUT_DIR}"

# Resolve valheim root dir inside container (supports multiple paths)
detect_valheim_root_in_container() {
    local cname="$1"
    local root=""
    # Try different possible locations
    if docker exec "$cname" sh -lc 'test -d /opt/valheim/server/valheim_server_Data/Managed'; then
        root="/opt/valheim/server"
    elif docker exec "$cname" sh -lc 'test -d /opt/valheim/valheim_server_Data/Managed'; then
        root="/opt/valheim"
    elif docker exec "$cname" sh -lc 'test -d /valheim/valheim_server_Data/Managed'; then
        root="/valheim"
    fi
    echo "$root"
}

copy_from_running_container() {
    local cname="$1"
    local vroot
    vroot=$(detect_valheim_root_in_container "$cname")
    if [[ -z "$vroot" ]]; then
        echo "Error: could not locate Valheim root inside container '${cname}'" >&2
        exit 1
    fi

    local managed_dir="${vroot}/valheim_server_Data/Managed"
    local bepinex_core_dir="${vroot}/BepInEx/core"

    echo "Detected Valheim root in container: ${vroot}"
    echo "Copying game assemblies from: ${managed_dir}"

    # Determine main game assembly filename (assembly_valheim.dll vs Assembly-CSharp.dll)
    local main_asm=""
    if docker exec "$cname" sh -lc "test -f '${managed_dir}/assembly_valheim.dll'"; then
        main_asm="assembly_valheim.dll"
    elif docker exec "$cname" sh -lc "test -f '${managed_dir}/Assembly-CSharp.dll'"; then
        main_asm="Assembly-CSharp.dll"
    fi

    if [[ -z "$main_asm" ]]; then
        echo "Warning: main game assembly not found (assembly_valheim.dll or Assembly-CSharp.dll)" >&2
    else
        docker cp "${cname}:${managed_dir}/${main_asm}" "${OUTPUT_DIR}/${main_asm}"
        echo "Copied ${main_asm}"
    fi

    # Copy UnityEngine*.dll via tar stream to support globs
    if docker exec "$cname" sh -lc "ls '${managed_dir}'/UnityEngine*.dll >/dev/null 2>&1"; then
        docker exec "$cname" sh -lc "cd '${managed_dir}' && tar -cf - UnityEngine*.dll" | tar -C "${OUTPUT_DIR}" -xf -
        echo "Copied UnityEngine*.dll"
    else
        echo "Note: No UnityEngine*.dll files found to copy"
    fi

    # Optionally copy BepInEx core dlls
    if [[ "${INCLUDE_BEPINEX}" == true ]] && docker exec "$cname" sh -lc "test -d '${bepinex_core_dir}'"; then
        if docker exec "$cname" sh -lc "ls '${bepinex_core_dir}'/BepInEx*.dll >/dev/null 2>&1"; then
            docker exec "$cname" sh -lc "cd '${bepinex_core_dir}' && tar -cf - BepInEx*.dll" | tar -C "${OUTPUT_DIR}" -xf -
            echo "Copied BepInEx core DLLs"
        else
            echo "Note: No BepInEx core DLLs found to copy"
        fi
    fi

    echo "Extraction from running container completed."
}

copy_from_image() {
    local image="$1"
    echo "No container specified. Falling back to image: ${image}"
    echo "Starting ephemeral container to copy files..."

    docker run --rm \
        -e INCLUDE_BEPINEX="${INCLUDE_BEPINEX}" \
        -v "${OUTPUT_DIR}:/output" \
        "${image}" \
        sh -lc '
            set -e
            # Detect valheim root
            if [ -d /opt/valheim/valheim_server_Data/Managed ]; then ROOT=/opt/valheim; elif [ -d /valheim/valheim_server_Data/Managed ]; then ROOT=/valheim; else ROOT=""; fi
            if [ -z "$ROOT" ]; then echo "Valheim root not found in image" >&2; exit 1; fi
            MANAGED="$ROOT/valheim_server_Data/Managed"

            # Main assembly (try assembly_valheim.dll then Assembly-CSharp.dll)
            if [ -f "$MANAGED/assembly_valheim.dll" ]; then cp -f "$MANAGED/assembly_valheim.dll" /output/; fi
            if [ -f "$MANAGED/Assembly-CSharp.dll" ]; then cp -f "$MANAGED/Assembly-CSharp.dll" /output/; fi

            # UnityEngine modules (best-effort)
            cp -f "$MANAGED"/UnityEngine*.dll /output/ 2>/dev/null || true

            # Optional: BepInEx core
            if [ "${INCLUDE_BEPINEX}" = "true" ] && [ -d "$ROOT/BepInEx/core" ]; then
                cp -f "$ROOT/BepInEx/core"/BepInEx*.dll /output/ 2>/dev/null || true
            fi
        '

    echo "Extraction from image completed."
}

if [[ -n "${CONTAINER_NAME}" ]]; then
    # Ensure container exists
    if ! docker ps -a --format '{{.Names}}' | grep -Fxq "${CONTAINER_NAME}"; then
        echo "Error: container '${CONTAINER_NAME}' not found" >&2
        exit 1
    fi
    copy_from_running_container "${CONTAINER_NAME}"
else
    copy_from_image "${IMAGE_NAME}"
fi

echo "\nDone. Files now in: ${OUTPUT_DIR}"
echo "Typical required files:"
echo "  - assembly_valheim.dll or Assembly-CSharp.dll"
echo "  - UnityEngine.CoreModule.dll (plus other UnityEngine*.dll)"
if [[ "${INCLUDE_BEPINEX}" == true ]]; then
    echo "  - BepInEx.dll, BepInEx.Harmony.dll, BepInEx.MonoMod.dll (if present)"
fi



