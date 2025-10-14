# Valheim Server with BepInEx - Adaptive Sampling (256×256)
# Experimental approach to validate performance claims

FROM debian:bookworm-slim AS base

# Install runtime dependencies
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        lib32gcc-s1 \
        lib32stdc++6 \
        libc6-i386 \
        libsdl2-2.0-0:i386 \
        libcurl4:i386 \
        locales \
        procps \
        netcat-openbsd \
        gosu \
        unzip \
        file \
        && \
    rm -rf /var/lib/apt/lists/*

# Set up locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# Create valheim user
RUN useradd -m -u 1000 -s /bin/bash valheim

# Install SteamCMD
RUN mkdir -p /opt/steamcmd && \
    cd /opt/steamcmd && \
    curl -fsSL 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz' | tar xzf - && \
    chown -R valheim:valheim /opt/steamcmd

# Install Valheim Server
RUN mkdir -p /opt/valheim && \
    chown -R valheim:valheim /opt/valheim

USER valheim
WORKDIR /opt/valheim

# Download and install Valheim dedicated server (App ID: 896660)
RUN for i in 1 2 3; do \
        /opt/steamcmd/steamcmd.sh \
            +force_install_dir /opt/valheim \
            +login anonymous \
            +app_update 896660 \
            +quit && break || sleep 5; \
    done

# Download and install BepInExPack_Valheim 5.4.2333
USER root
RUN cd /tmp && \
    curl -fsSL -o bepinex.zip \
        'https://thunderstore.io/package/download/denikson/BepInExPack_Valheim/5.4.2333/' && \
    unzip -q bepinex.zip -d /tmp/bepinex_pack && \
    cp -r /tmp/bepinex_pack/BepInExPack_Valheim/* /opt/valheim/ && \
    rm -rf /tmp/bepinex.zip /tmp/bepinex_pack && \
    chmod +x /opt/valheim/start_server_bepinex.sh 2>/dev/null || true && \
    chmod +x /opt/valheim/start_game_bepinex.sh 2>/dev/null || true && \
    chown -R valheim:valheim /opt/valheim

# Create BepInEx plugin and config directories
RUN mkdir -p /opt/valheim/BepInEx/plugins \
             /opt/valheim/BepInEx/config \
             /config/bepinex/plugins \
             /config/bepinex/config \
             /config/worlds_local \
             /config/world_data && \
    chown -R valheim:valheim /opt/valheim/BepInEx /config

# Copy VWE plugins and configs (will be overridden by volume mounts for development)
USER root
COPY plugins/VWE_AutoSave.dll /opt/valheim/BepInEx/plugins/
COPY plugins/VWE_DataExporter.dll /opt/valheim/BepInEx/plugins/
COPY plugins/VWE_WorldScreenshot.dll /opt/valheim/BepInEx/plugins/
COPY plugins/Newtonsoft.Json.dll /opt/valheim/BepInEx/plugins/
COPY config/VWE_AutoSave.cfg /opt/valheim/BepInEx/config/com.valheimworldengine.autosave.cfg
COPY config/VWE_DataExporter.cfg /opt/valheim/BepInEx/config/com.valheimworldengine.dataexporter.cfg
COPY config/VWE_WorldScreenshot.cfg /opt/valheim/BepInEx/config/com.vwe.worldscreenshot.cfg
RUN chown valheim:valheim /opt/valheim/BepInEx/plugins/*.dll && \
    chown valheim:valheim /opt/valheim/BepInEx/config/*.cfg

# Environment defaults
ENV WORLD_NAME=AdaptiveSamplingTest \
    SERVER_NAME="VWE Adaptive Sampling 256x256" \
    SERVER_PASS=secret \
    SERVER_PUBLIC=0 \
    SERVER_PORT=2456 \
    PUID=1000 \
    PGID=1000

# Expose game ports
EXPOSE 2456/udp 2457/udp 2458/udp

# Volume for world data and plugin configs
VOLUME ["/config"]

USER valheim
WORKDIR /opt/valheim

# Start Valheim server with BepInEx
CMD ["bash", "-c", "exec /opt/valheim/start_server_bepinex.sh -nographics -batchmode -name \"${SERVER_NAME}\" -port ${SERVER_PORT} -world \"${WORLD_NAME}\" -password \"${SERVER_PASS}\" -public ${SERVER_PUBLIC}"]
