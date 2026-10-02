#!/usr/bin/env bash
# Render the link-preview image (site/og/card.html -> site/og/home.jpg, 1200x630) with headless Chrome.
# Needs the site served locally:  python3 -m http.server 8090 --directory site
# Rerun after adding a book; the card reads the book list from the home page.
set -euo pipefail
cd "$(dirname "$0")/../site/og"
PORT="${1:-8090}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
  --virtual-time-budget=10000 --window-size=1200,630 --screenshot="$PWD/_og.png" "http://127.0.0.1:$PORT/og/card.html" >/dev/null 2>&1
/usr/bin/python3 -c "from PIL import Image; Image.open('_og.png').convert('RGB').save('home.jpg', quality=86, optimize=True, progressive=True)"
rm -f _og.png
ls -la home.jpg
