#!/usr/bin/with-contenv bashio
set -e

mkdir -p /data/audio_ads/music
mkdir -p /data/audio_ads/sfx
mkdir -p /data/audio_ads/outputs
mkdir -p /data/audio_ads/projects

python3 /app/generate_assets.py || bashio::log.warning "Impossibile generare la libreria starter"

bashio::log.info "Avvio Audio Ads Studio sulla porta 8099"
exec python3 /app/app.py
