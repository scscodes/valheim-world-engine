# Custom Valheim server with BepInEx for VWE
FROM lloesche/valheim-server:latest

# Set environment variables for BepInEx
ENV BEPINEX_ENABLED=true
ENV BEPINEX_LOG_LEVEL=Info
ENV BEPINEX_LOG_CONSOLE=true
ENV BEPINEX_LOG_FILE=true

# Set VWE plugin environment variables
ENV VWE_AUTOSAVE_ENABLED=true
ENV VWE_AUTOSAVE_DELAY=2
ENV VWE_DATAEXPORT_ENABLED=true
ENV VWE_DATAEXPORT_FORMAT=both
ENV VWE_DATAEXPORT_DIR=./world_data

# Create directories for BepInEx and VWE plugins
RUN mkdir -p /valheim/BepInEx/plugins \
    && mkdir -p /valheim/BepInEx/config \
    && mkdir -p /valheim/world_data

# Copy VWE plugins
COPY ../plugins/VWE_AutoSave.dll /valheim/BepInEx/plugins/
COPY ../plugins/VWE_DataExporter.dll /valheim/BepInEx/plugins/

# Copy BepInEx configuration
COPY ../config/BepInEx.cfg /valheim/BepInEx/config/
COPY ../config/VWE_DataExporter.cfg /valheim/BepInEx/config/

# Set permissions
RUN chown -R 1000:1000 /valheim/BepInEx \
    && chown -R 1000:1000 /valheim/world_data \
    && chmod -R 755 /valheim/BepInEx \
    && chmod -R 755 /valheim/world_data

# Health check to verify BepInEx and plugins are loaded
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD test -f /valheim/BepInEx/plugins/VWE_AutoSave.dll && \
        test -f /valheim/BepInEx/plugins/VWE_DataExporter.dll && \
        echo "BepInEx and VWE plugins are loaded" || exit 1

# Expose additional port for BepInEx logs (if needed)
EXPOSE 8080

# Labels for identification
LABEL maintainer="Valheim World Engine"
LABEL description="Valheim server with BepInEx and VWE plugins for optimized world generation"
LABEL version="1.0.0"
