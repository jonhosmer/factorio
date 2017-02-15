#!/bin/sh -x

set -e

CONFIG=/factorio/config
SAVES=/factorio/saves
MODS=/factorio/mods

mkdir -p $CONFIG
mkdir -p $SAVES
mkdir -p $MODS

if [ ! -f $CONFIG/rconpw ]; then
    echo $(pwgen 15 1) > $CONFIG/rconpw
fi

if [ ! -f $CONFIG/server-settings.json ]; then
    cp /opt/factorio/data/server-settings.example.json $CONFIG/server-settings.json
fi

if [ ! -f $CONFIG/map-gen-settings.json ]; then
    cp /opt/factorio/data/map-gen-settings.example.json $CONFIG/map-gen-settings.json
fi

if ! find -L $SAVES -iname \*.zip -mindepth 1 -print | grep -q .; then
    /opt/factorio/bin/x64/factorio \
      --create $SAVES/_autosave1.zip  \
      --map-gen-settings $CONFIG/map-gen-settings.json
fi

exec /opt/factorio/bin/x64/factorio \
    --port 34197 \
    --start-server-load-latest \
    --server-settings $CONFIG/server-settings.json \
    --rcon-port 27015 \
    --rcon-password "$(cat $CONFIG/rconpw)"
