#!/usr/bin/env python3
"""Contact sheets of what a phone sees in /read/<book>: each scene's start and end view, as the
player frames them on a 390x844 portrait screen (the hard case; landscape shows far more).
Review every sheet before publishing: each view should land on a face or the subject, never on
empty sky or wall, and never close on a wound or a body. Fix bad scenes by hand under the
motion file's "// keep" line.

  /usr/bin/python3 scripts/read_review_sheets.py --out /tmp/sheets genesis acts   (needs PIL)
"""
import argparse, glob, json, os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = {'john': 'bible'}
W, H = 390, 844
PTOP = H - 74 - 388                      # top of the text sheet (present.css, phone layout)
CX, CY, FLOOR = W / 2, PTOP * 0.6, PTOP + (H - PTOP) * 0.3   # same rules as geometry() in present.js


def view(im, f, trim, tw):
    iw, ih = im.size
    k = max(W / iw, H / ih); dw, dh = iw * k, ih * k
    s = (1 + (f[2] - 1) / 2) * (1.03 if trim else 1)
    tx = min(0, max(W - s * dw, CX - s * f[0] * dw)); ty = min(0, max(FLOOR - s * dh, CY - s * f[1] * dh))
    box = ((-tx) / (s * k), (-ty) / (s * k), (W - tx) / (s * k), (PTOP - ty) / (s * k))
    return im.crop(tuple(int(v) for v in box)).resize((tw, int(tw * PTOP / W)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('books', nargs='+')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    scenes = []
    for b in a.books:
        fo = FOLDER.get(b, b)
        m = open(os.path.join(ROOT, 'site', fo, 'data', f'{b}-motion.js')).read()
        body = '\n'.join(l for l in m[m.index('{'):m.rindex('}') + 1].splitlines() if not l.startswith('//'))
        M = json.loads(body)
        for f in sorted(glob.glob(os.path.join(ROOT, 'site', fo, 'data', f'{b}-[0-9][0-9].js'))):
            t = open(f).read(); d = json.loads(t[t.index(',') + 1:t.rindex(')')]); c = int(f[-5:-3])
            for x in d['scenes']:
                scenes.append((b, f'{c}:{x[0]}', x[2], x[5], M.get(f'{c}:{x[0]}')))
    tw, per, rows = 100, 5, 10
    th = int(tw * PTOP / W)
    n = 0
    for start in range(0, len(scenes), per * rows):
        chunk = scenes[start:start + per * rows]
        R = (len(chunk) + per - 1) // per
        sheet = Image.new('RGB', (per * (2 * tw + 16), R * (th + 14)), 'black'); dr = ImageDraw.Draw(sheet)
        for i, (b, key, fn, trim, fr) in enumerate(chunk):
            x, y = (i % per) * (2 * tw + 16), (i // per) * (th + 14)
            dr.text((x + 2, y + 1), f'{b[:3]} {key}', fill='yellow' if fr else 'red')
            if not fr:
                continue
            im = Image.open(os.path.join(ROOT, 'site', 'images', 'full', fn.replace('.png', '.webp'))).convert('RGB')
            a1, b1 = (fr[2], fr[3]) if len(fr) == 4 else ([f[0], min(f[1], .42), f[2]] for f in fr[:2])
            sheet.paste(view(im, a1, trim, tw), (x, y + 13)); sheet.paste(view(im, b1, trim, tw), (x + tw + 2, y + 13))
        sheet.save(os.path.join(a.out, f'phone-{n:02d}.jpg'), quality=78); n += 1
    print(f'{n} sheets, {len(scenes)} scenes in {a.out}')


if __name__ == '__main__':
    main()
