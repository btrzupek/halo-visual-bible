#!/usr/bin/env bash
# Render site/infographic/card.html to PNGs with headless Chrome.
# Needs the site served locally, e.g.:  python3 -m http.server 8090 --directory site
# Usage: scripts/render_infographic.sh <site-host> <repo-short> [port]
#   e.g. scripts/render_infographic.sh visual-bible.example.com github.com/you/halo-visual-bible
set -euo pipefail
cd "$(dirname "$0")/../site/infographic"
HOST="${1:?site host}"; REPO="${2:?repo short url}"; PORT="${3:-8090}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
esc() { printf '%s' "$1" | sed -e 's/[&|\\]/\\&/g'; }
sed -e "s|{{SITE_HOST}}|$(esc "$HOST")|" -e "s|{{REPO_SHORT}}|$(esc "$REPO")|" card.html > _render.html
trap 'rm -f _render.html' EXIT
shot() { "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
  --virtual-time-budget=8000 --window-size="$1" --screenshot="$PWD/$2" "http://127.0.0.1:$PORT/infographic/_render.html$3" >/dev/null 2>&1; }
shot 1080,1350 infographic.png ""
shot 1200,630 og.png "?og"
ls -la infographic.png og.png
