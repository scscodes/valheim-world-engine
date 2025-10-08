FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    STEAMCMDDIR=/opt/steamcmd \
    VALHEIM_APPID=896660 \
    VALHEIM_DIR=/opt/valheim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl lib32gcc-s1 \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p ${STEAMCMDDIR} ${VALHEIM_DIR} \
 && curl -sL https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz | tar -xz -C ${STEAMCMDDIR}

# Pre-install Valheim dedicated server content
RUN ${STEAMCMDDIR}/steamcmd.sh +login anonymous \
    +force_install_dir ${VALHEIM_DIR} \
    +app_update ${VALHEIM_APPID} validate \
    +quit

# Provide a simple entrypoint to print installed version
CMD ["bash", "-lc", "ls -l ${VALHEIM_DIR} && echo 'Valheim preinstalled' && sleep infinity"]
