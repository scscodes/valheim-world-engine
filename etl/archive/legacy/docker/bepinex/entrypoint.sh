#!/bin/bash
set -e

echo "[VWE] Starting Valheim Server with BepInEx"

# Handle PUID/PGID for file ownership
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

if [ "$CURRENT_UID" = "0" ]; then
    echo "[VWE] Running as root, switching to PUID=$PUID PGID=$PGID"

    # Update valheim user to match host UID/GID
    groupmod -o -g "$PGID" valheim 2>/dev/null || true
    usermod -o -u "$PUID" valheim 2>/dev/null || true

    # Fix ownership of writable directories only (skip read-only mounts)
    # /config/bepinex has read-only mounts, so we only chown /config root and world_data
    chown "$PUID:$PGID" /config 2>/dev/null || true
    chown -R "$PUID:$PGID" /config/worlds_local 2>/dev/null || true
    chown -R "$PUID:$PGID" /config/world_data 2>/dev/null || true
    chown -R "$PUID:$PGID" /opt/valheim/BepInEx 2>/dev/null || true

    # Re-exec as valheim user (preserve PATH)
    exec gosu valheim env PATH="$PATH" "$0" "$@"
fi

echo "[VWE] Running as UID=$CURRENT_UID GID=$CURRENT_GID"

# Create necessary directories in /config (with proper permissions)
mkdir -p /config/worlds_local \
         /config/world_data \
         /config/bepinex/plugins \
         /config/bepinex 2>/dev/null || {
    echo "[VWE] Warning: Could not create directories in /config (may already exist)"
}

# Copy host-mounted plugins to BepInEx directory if they exist
if [ -d "/config/bepinex/plugins" ] && [ "$(ls -A /config/bepinex/plugins 2>/dev/null)" ]; then
    echo "[VWE] Copying plugins from /config/bepinex/plugins/ to BepInEx"
    cp -f /config/bepinex/plugins/*.dll /opt/valheim/BepInEx/plugins/ 2>/dev/null || true
fi

# Copy host-mounted configs to BepInEx directory if they exist
if [ -d "/config/bepinex" ]; then
    echo "[VWE] Copying configs from /config/bepinex/ to BepInEx"
    cp -f /config/bepinex/*.cfg /opt/valheim/BepInEx/config/ 2>/dev/null || true
fi

# Ensure export directory exists
mkdir -p "$VWE_DATAEXPORT_DIR" 2>/dev/null || {
    echo "[VWE] Warning: Could not create $VWE_DATAEXPORT_DIR"
}

# List loaded plugins
echo "[VWE] BepInEx plugins loaded:"
ls -lh /opt/valheim/BepInEx/plugins/*.dll 2>/dev/null || echo "  No plugins found"

# Export environment variables for VWE plugins
export VWE_AUTOSAVE_ENABLED
export VWE_AUTOSAVE_DELAY
export VWE_DATAEXPORT_ENABLED
export VWE_DATAEXPORT_FORMAT
export VWE_DATAEXPORT_DIR

echo "[VWE] Configuration:"
echo "  WORLD_NAME: $WORLD_NAME"
echo "  SERVER_NAME: $SERVER_NAME"
echo "  SERVER_PORT: $SERVER_PORT"
echo "  VWE_AUTOSAVE_ENABLED: $VWE_AUTOSAVE_ENABLED"
echo "  VWE_AUTOSAVE_DELAY: $VWE_AUTOSAVE_DELAY"
echo "  VWE_DATAEXPORT_ENABLED: $VWE_DATAEXPORT_ENABLED"
echo "  VWE_DATAEXPORT_DIR: $VWE_DATAEXPORT_DIR"

# Set environment variables for Valheim server
export SteamAppId=892970

# Configure BepInEx (BepInExPack_Valheim specific variables)
export DOORSTOP_ENABLED=1
export DOORSTOP_TARGET_ASSEMBLY=./BepInEx/core/BepInEx.Preloader.dll
export LD_LIBRARY_PATH="./doorstop_libs:./linux64:${LD_LIBRARY_PATH}"
export LD_PRELOAD="libdoorstop_x64.so:$LD_PRELOAD"

# Change to Valheim directory
cd /opt/valheim

echo "[VWE] Starting Valheim server with BepInEx..."
echo "[VWE] World will be saved to: /config/worlds_local/$WORLD_NAME.db"
echo "[VWE] Exported data will be saved to: $VWE_DATAEXPORT_DIR"

# Run Valheim server with BepInEx using the BepInExPack_Valheim launcher
echo "[VWE] Launching with BepInExPack_Valheim (doorstop enabled)..."

# Launch using the valheim_server executable directly with doorstop preloaded
exec ./valheim_server.x86_64 \
    -nographics \
    -batchmode \
    -name "$SERVER_NAME" \
    -port "$SERVER_PORT" \
    -world "$WORLD_NAME" \
    -password "$SERVER_PASS" \
    -public "$SERVER_PUBLIC" \
    -savedir "/config"
