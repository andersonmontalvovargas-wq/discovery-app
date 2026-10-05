#!/usr/bin/env bash
# Builds growthlab-showreel.mp4 (1080x1920, 60 fps, 20 s, H.264 + AAC, < 15 MB):
# renders frames, generates the voice-over, synthesizes the music, then muxes with a 2-pass encode.
set -euo pipefail
cd "$(dirname "$0")"
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
node render.cjs            # -> build/video.mp4 (high-quality master, silent)
python3 voiceover.py       # -> build/vo.npy
python3 audio.py           # -> build/audio.wav
VB="${VIDEO_KBPS:-5000}"   # 5 Mbps video + 256 kbps audio ~= 13.2 MB
cd build
ffmpeg -y -loglevel error -i video.mp4 -c:v libx264 -preset slow -b:v ${VB}k -maxrate $((VB * 2))k -bufsize $((VB * 2))k \
  -profile:v high -pix_fmt yuv420p -pass 1 -an -f mp4 /dev/null
# two-pass loudness normalisation (linear gain, no extra compression): -14 LUFS, true peak <= -1 dBTP
M=$(ffmpeg -hide_banner -i audio.wav -af loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
J() { python3 -c "import json,sys; print(json.loads(sys.stdin.read())['$1'])" <<<"$M"; }
LN="loudnorm=I=-14:TP=-1.0:LRA=11:measured_I=$(J input_i):measured_TP=$(J input_tp):measured_LRA=$(J input_lra):measured_thresh=$(J input_thresh):offset=$(J target_offset):linear=true"
ffmpeg -y -loglevel error -i video.mp4 -i audio.wav -c:v libx264 -preset slow -b:v ${VB}k -maxrate $((VB * 2))k -bufsize $((VB * 2))k \
  -profile:v high -pix_fmt yuv420p -pass 2 -af "$LN" -c:a aac -b:a 256k -ar 48000 -t 20 -movflags +faststart ../growthlab-showreel.mp4
rm -f ffmpeg2pass-*
cd ..
# share page assets (web/index.html): poster frame + a copy of the video next to the page
ffmpeg -y -loglevel error -ss 7.2 -i growthlab-showreel.mp4 -frames:v 1 -q:v 3 -vf scale=720:1280 web/poster.jpg
cp growthlab-showreel.mp4 web/
echo "-> $(pwd)/growthlab-showreel.mp4 ($(du -h growthlab-showreel.mp4 | cut -f1))"
