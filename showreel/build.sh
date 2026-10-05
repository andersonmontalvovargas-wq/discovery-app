#!/usr/bin/env bash
# Builds flowchat-ai-showreel.mp4: renders frames, synthesizes audio, muxes both.
set -euo pipefail
cd "$(dirname "$0")"
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
node render.cjs
python3 voiceover.py
python3 audio.py
ffmpeg -y -loglevel error -i build/video.mp4 -i build/audio.wav \
  -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart flowchat-ai-showreel.mp4
echo "-> $(pwd)/flowchat-ai-showreel.mp4"
