#!/bin/bash
# T&R Gemini frame ingest
#
# Trigger : a new Gemini_Generated_Image_*.png lands in ~/Downloads
# Process : convert to a web-ready JPG, stage it in the site repo, archive the raw PNG
# Output  : images/_staging/gemini-<timestamp>-<hash>.jpg
#
# What it deliberately does NOT do: rename to a final slug, drop into images/,
# or touch git. Frame selection, naming, and the canon check stay human.

set -euo pipefail

WATCH_DIR="$HOME/Downloads/tr-frames"
REPO="$HOME/Documents/GitHub/throttle-and-rust-site"
STAGING="$REPO/images/_staging"
ARCHIVE="$WATCH_DIR/_gemini_raw"
LOG="$REPO/scripts/gemini-ingest.log"

mkdir -p "$STAGING" "$ARCHIVE"

shopt -s nullglob
for f in "$WATCH_DIR"/Gemini_Generated_Image_*.png; do
  base="$(basename "$f" .png)"

  # Skip partial downloads still in flight
  if [ -e "$WATCH_DIR/$base.png.crdownload" ] || [ -e "$WATCH_DIR/$base.crdownload" ]; then
    continue
  fi

  # Skip files written in the last 2 seconds (still landing on disk)
  now=$(date +%s)
  mtime=$(stat -f %m "$f")
  if [ $(( now - mtime )) -lt 2 ]; then
    continue
  fi

  ts="$(date +%Y%m%d-%H%M%S)"
  hash="${base##*_}"
  out="$STAGING/gemini-$ts-$hash.jpg"

  # sips is built into macOS — no Python/Pillow dependency
  sips -s format jpeg -s formatOptions high "$f" --out "$out" >/dev/null

  mv "$f" "$ARCHIVE/"
  echo "$(date '+%Y-%m-%d %H:%M:%S')  staged $(basename "$out")  <- $base.png" >> "$LOG"
done
