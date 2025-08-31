#!/usr/bin/env bash
# Simple macOS/Linux helper to record a demo GIF for the app.
# Requires: ffmpeg, imagemagick (for converting mp4 to gif optionally)
# Usage:
# 1) Start backend (port 8000) and frontend (port 5173)
# 2) Run this script to record a screen region for ~2 minutes
# 3) The output GIF will be saved at docs/demo.gif

set -euo pipefail

DURATION=${DURATION:-120}
OUT=${OUT:-docs/demo.gif}
TMP_MP4=${TMP_MP4:-docs/demo.mp4}

echo "Recording screen for ${DURATION}s... (CTRL+C to cancel)"

if [[ "$(uname)" == "Darwin" ]]; then
  # macOS: capture default screen (might require permissions)
  ffmpeg -f avfoundation -framerate 30 -i 1 -t "$DURATION" -pix_fmt yuv420p "$TMP_MP4"
else
  # Linux (X11): capture root screen, adjust :0.0 and size as needed
  ffmpeg -video_size 1280x720 -framerate 30 -f x11grab -i :0.0 -t "$DURATION" -pix_fmt yuv420p "$TMP_MP4"
fi

echo "Converting to GIF..."
ffmpeg -i "$TMP_MP4" -vf "fps=10,scale=960:-1:flags=lanczos" -loop 0 "$OUT"

echo "Saved demo to $OUT"

