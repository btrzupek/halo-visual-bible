#!/usr/bin/env bash
# Rebuild an epistle film's animatic from whatever keyframes exist now (stand-ins for the rest), for a pacing check.
#   scripts/epistle_checkpoint.sh philemon
# Depth maps are made (on the Mac) only for parallax shots that have a keyframe but no depth.png yet.
# Writes site/watch/<book>/ (local only, nothing is committed) and <work>/checkpoint.jpg, a sheet of the keyframes so far.
set -euo pipefail
BOOK="${1:?book}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$HOME/halo-images/visual-bible/$BOOK"
cd "$ROOT"
todo=$(uv run -q --with pyyaml python - "$WORK" "$BOOK" <<'EOF'
import os, sys, yaml
work, book = sys.argv[1], sys.argv[2]
sb = yaml.safe_load(open(f'{work}/{book}_storyboard.yaml'))
for m in sb['movements']:
    for s in m['shots']:
        d = f"{work}/shots/{s['id']}"
        if s['type'] == 'parallax' and os.path.exists(f'{d}/keyframe.png') and not os.path.exists(f'{d}/depth.png'):
            print(f'{d}/keyframe.png')
EOF
)
if [ -n "$todo" ]; then
  # depth_map.py names its output <image>.depth.png; rename to depth.png in each shot folder
  echo "$todo" | xargs uv run -q --with torch --with transformers --with pillow --with numpy python scripts/depth_map.py 2>&1 | grep -v -i -E "warn|loading" || true
  for k in $todo; do d=$(dirname "$k"); [ -f "$d/keyframe.depth.png" ] && mv "$d/keyframe.depth.png" "$d/depth.png"; done
fi
uv run -q --with pyyaml --with pillow python scripts/build_epistle.py --book "$BOOK" --placeholders
/usr/bin/python3 - "$WORK" <<'EOF'
import os, sys, glob
from PIL import Image, ImageDraw, ImageFont
work = sys.argv[1]
shots = sorted(glob.glob(f'{work}/shots/*/keyframe.png'), key=lambda p: [int(x) if x.isdigit() else x for x in os.path.basename(os.path.dirname(p)).replace('M', '').replace('S', '.').split('.')])
if not shots: sys.exit()
W, H, cols = 480, 270, 4
rows = (len(shots) + cols - 1) // cols
sheet = Image.new('RGB', (cols * W, rows * (H + 28)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
f = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 18)
for i, p in enumerate(shots):
    x, y = (i % cols) * W, (i // cols) * (H + 28)
    sheet.paste(Image.open(p).convert('RGB').resize((W - 4, H - 4)), (x + 2, y + 2))
    d.text((x + 6, y + H + 2), os.path.basename(os.path.dirname(p)), fill=(235, 235, 235), font=f)
sheet.save(f'{work}/checkpoint.jpg', quality=82)
print(f'{work}/checkpoint.jpg', len(shots), 'keyframes')
EOF
