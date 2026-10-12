#!/usr/bin/env bash
# Thumbnails for the Speaking section (public/yt/).
#
#   scripts/thumbnails.sh fetch <youtube-id>...        download YouTube's still (maxres, falling back to hq)
#   scripts/thumbnails.sh card <out-name> "<event>" "<title>" "<date line>"
#                                                      render a 1280x720 card in the site's style with headless Chrome,
#                                                      for talks whose YouTube art is stock imagery
#
# Examples:
#   scripts/thumbnails.sh fetch XaosRsgGSX8 MzsmDlQe9S8
#   scripts/thumbnails.sh card bsides-2025 "BSides Pittsburgh · 2025" "How I learned to stop worrying and love vibe coding: security edition" "JULY 11, 2025 · PITTSBURGH, PA"
# Then reference /yt/<name> from src/data/featured.ts.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
OUT=public/yt
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
mkdir -p "$OUT"

case "${1:-}" in
  fetch)
    shift
    for id in "$@"; do
      if curl -sfL "https://i.ytimg.com/vi/$id/maxresdefault.jpg" -o "$OUT/$id.jpg" && [ "$(wc -c <"$OUT/$id.jpg")" -gt 5000 ]; then echo "maxres $id"
      else curl -sfL "https://i.ytimg.com/vi/$id/hqdefault.jpg" -o "$OUT/$id.jpg"; echo "hq     $id"; fi
    done ;;
  card)
    name=$2; event=$3; title=$4; dateline=$5
    tmp=$(mktemp -d)
    cp public/img/jon_zeolla.png "$tmp/headshot.png"
    sed -e "s|{{EVENT}}|$event|" -e "s|{{TITLE}}|$title|" -e "s|{{DATE}}|$dateline|" scripts/thumbnails/card.html > "$tmp/card.html"
    "$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1280,720 --virtual-time-budget=6000 \
      --screenshot="$OUT/$name.png" "file://$tmp/card.html" 2>/dev/null
    rm -rf "$tmp"; echo "rendered $OUT/$name.png" ;;
  *) sed -n '2,13p' "$0"; exit 2 ;;
esac
