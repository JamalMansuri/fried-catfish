#!/bin/bash
# Post-process the raw VHS capture into the published GIF: play the tournament through, then a
# cinematic push-in on the final "THE CALL" panel and a long hold. VHS records a fixed terminal
# viewport (no camera), so the zoom + hold are added here with ffmpeg.
#
# Usage:  bash demo/zoom.sh        (run from the repo root, or anywhere — it cd's itself)
# In/out: demo/_raw.gif  ->  demo/catfish.gif
set -euo pipefail
cd "$(dirname "$0")/.."

RAW=demo/_raw.gif
OUT=demo/catfish.gif
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

# Source size (VHS may pad, so read it rather than assume).
W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width  -of csv=p=0 "$RAW" | head -1)
H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$RAW" | head -1)

ZOOM="${DEMO_ZOOM:-1.10}"      # gentle push-in (report is tall — keep it readable)
HOLD="${DEMO_HOLD:-10.5}"      # seconds the zoomed panel rests (the "10s+ pause")

# 1. grab the last frame (the THE CALL panel)
ffmpeg -y -v error -sseof -0.3 -i "$RAW" -update 1 -frames:v 1 "$T/last.png"

# 2. push-in (~3.4s) then hold at full zoom; focal point ~upper third where the panel sits.
#    upscale 2x first so the magnified text stays crisp.
ffmpeg -y -v error -loop 1 -i "$T/last.png" -t "$HOLD" -r 25 \
  -vf "scale=${W}*2:-1,zoompan=z='min(1.0+0.0028*on\,${ZOOM})':d=1:x='iw/2-(iw/zoom/2)':y='ih*0.30-(ih/zoom)*0.30':s=${W}x${H}:fps=25,format=rgb24" \
  -an "$T/zoom.mp4"

# 3. raw capture -> mp4 at matching size/fps
ffmpeg -y -v error -i "$RAW" -vf "fps=25,scale=${W}:${H}:flags=lanczos,format=rgb24" -an "$T/raw.mp4"

# 4. concat process + zoom-and-hold
ffmpeg -y -v error -i "$T/raw.mp4" -i "$T/zoom.mp4" \
  -filter_complex "[0:v][1:v]concat=n=2:v=1[v]" -map "[v]" "$T/full.mp4"

# 5. palette GIF. Terminal output is flat solid colors, so few colors + dither=none keeps it small
#    and crisp; identical hold-frames then compress to almost nothing.
GIFW="${DEMO_WIDTH:-1000}"
ffmpeg -y -v error -i "$T/full.mp4" -vf "fps=15,scale=${GIFW}:-1:flags=lanczos,palettegen=max_colors=128:stats_mode=diff" "$T/pal.png"
ffmpeg -y -v error -i "$T/full.mp4" -i "$T/pal.png" \
  -lavfi "fps=15,scale=${GIFW}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=none" "$OUT"

echo "wrote $OUT  ($(du -h "$OUT" | cut -f1), source ${W}x${H}, zoom ${ZOOM}, hold ${HOLD}s)"
