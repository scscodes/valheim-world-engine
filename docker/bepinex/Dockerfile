# Valheim Server with BepInEx for VWE
# Based on Debian 12 (Bookworm) for GLIBC 2.36+ compatibility with BepInEx doorstop loader

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
# Note: Removed 'validate' flag to speed up builds
# Retry up to 3 times in case of Steam API timeouts
RUN for i in 1 2 3; do \
        /opt/steamcmd/steamcmd.sh \
            +force_install_dir /opt/valheim \
            +login anonymous \
            +app_update 896660 \
            +quit && break || sleep 5; \
    done

# Download and install BepInEx 5.4.23.2 (Linux x64)
USER root
RUN cd /tmp && \
    curl -fsSL -o bepinex.zip \
        'https://github.com/BepInEx/BepInEx/releases/download/v5.4.23.2/BepInEx_linux_x64_5.4.23.2.zip' && \
    unzip -q bepinex.zip -d /opt/valheim && \
    rm bepinex.zip && \
    chmod +x /opt/valheim/run_bepinex.sh 2>/dev/null || true && \
    chown -R valheim:valheim /opt/valheim

# Create BepInEx plugin and config directories
RUN mkdir -p /opt/valheim/BepInEx/plugins \
             /opt/valheim/BepInEx/config \
             /config/bepinex/plugins \
             /config/bepinex \
             /config/worlds_local \
             /config/world_data && \
    chown -R valheim:valheim /opt/valheim/BepInEx /config

# Copy VWE plugins into image (will also mount from host for development)
COPY bepinex/plugins/VWE_AutoSave.dll /opt/valheim/BepInEx/plugins/
COPY bepinex/plugins/VWE_DataExporter.dll /opt/valheim/BepInEx/plugins/
RUN chown valheim:valheim /opt/valheim/BepInEx/plugins/VWE_*.dll

# Copy entrypoint script
COPY docker/bepinex/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Environment defaults
ENV WORLD_NAME=Dedicated \
    SERVER_NAME="VWE BepInEx Server" \
    SERVER_PASS=secret \
    SERVER_PUBLIC=0 \
    SERVER_PORT=2456 \
    PUID=1000 \
    PGID=1000 \
    VWE_AUTOSAVE_ENABLED=true \
    VWE_AUTOSAVE_DELAY=2 \
    VWE_DATAEXPORT_ENABLED=true \
    VWE_DATAEXPORT_FORMAT=both \
    VWE_DATAEXPORT_DIR=/config/world_data

# Expose game ports
EXPOSE 2456/udp 2457/udp 2458/udp

# Volume for world data and plugin configs
VOLUME ["/config"]

USER valheim
WORKDIR /opt/valheim

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
