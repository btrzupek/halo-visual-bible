#!/usr/bin/env python3
"""Ken Burns frames for /read/<book>, from faces and salient regions found by macOS Vision.

  swiftc -O scripts/find_focus.swift -o /tmp/find_focus
  /tmp/find_focus site/images/full/*.webp > ~/halo-images/visual-bible/read/focus.json
  python3 scripts/build_motion.py --focus ~/halo-images/visual-bible/read/focus.json --book genesis

Writes site/<folder>/data/<book>-motion.js in the format present.js reads:
  "chapter:verse": [[x, y, zoom] start, [x, y, zoom] end, portrait start, portrait end]
Rules: the camera ends on the largest face (the main figure) and starts on a second face if
there is one far enough away, else on the picture's salient region; scenes without faces move
over the salient region; every third face-only scene pulls back instead of pushing in. Portrait
frames (phones see a quarter of the width) stay on faces. Entries in --keep (hand-tuned scenes,
listed in the book's motion file under "// keep") are never overwritten.
"""
import argparse, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = {'genesis': 'genesis', '1samuel': '1samuel', '2samuel': '2samuel', '1kings': '1kings', '2kings': '2kings', '1chronicles': '1chronicles', '2chronicles': '2chronicles',
           'matthew': 'matthew', 'mark': 'mark', 'luke': 'luke', 'acts': 'acts', 'john': 'bible'}


def r(v):
    return round(min(1, max(0, v)), 2)


def frames(info, k):
    faces = [f for f in info['faces'] if f[3] > 0.025]          # ignore specks
    sal = info['salient'][0] if info['salient'] else [0.2, 0.2, 0.6, 0.6]
    sx, sy = sal[0] + sal[2] / 2, sal[1] + sal[3] * 0.4          # upper part of the salient box
    if faces:
        f = faces[0]
        fx, fy, fh = f[0] + f[2] / 2, f[1] + f[3] / 2, f[3]
        zoom = min(1.35, max(1.1, 1.42 - fh * 2.2))               # small faces get more zoom
        end = [r(fx), r(fy + fh * 1.1), round(zoom, 2)]           # a little below the face: head and shoulders
        other = next((g for g in faces[1:] if abs(g[0] + g[2] / 2 - fx) > 0.15), None)
        if other:
            start = [r(other[0] + other[2] / 2), r(other[1] + other[3] / 2 + other[3]), 1.1]
        elif k % 3 == 2:                                          # pull back: start close, end wide
            start, end = end, [r((fx + sx) / 2), r(min(fy + fh, 0.5)), 1.0]
        else:
            start = [r(sx), r(sy), 1.0]
        # portrait: a narrow slice, so stay with people
        pe = [r(fx), r(fy + fh * 0.9), round(min(1.3, zoom), 2)]
        ps = [r(other[0] + other[2] / 2), r(other[1] + other[3] / 2 + other[3] * 0.8), 1.1] if other else [r(fx), r(fy + fh * 0.9), 1.0]
        return [start, end, ps, pe]
    end = [r(sx), r(sy), 1.2]
    start = [0.5, 0.5, 1.0]
    if k % 2:
        start, end = end, start
    return [start, end]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--focus', required=True)
    ap.add_argument('--book', required=True, choices=FOLDERS)
    a = ap.parse_args()
    focus = json.load(open(os.path.expanduser(a.focus)))
    data = os.path.join(ROOT, 'site', FOLDERS[a.book], 'data')
    out = os.path.join(data, a.book + '-motion.js')
    keep = {}
    if os.path.exists(out):  # hand-tuned lines after "// keep" survive regeneration
        s = open(out).read()
        if '// keep' in s:
            for m in re.finditer(r'^"(\d+:\d+)": (\[.*\]),?$', s.split('// keep', 1)[1], re.M):
                keep[m.group(1)] = m.group(2)
    lines, k = [], 0
    for f in sorted(os.listdir(data)):
        m = re.fullmatch(re.escape(a.book) + r'-(\d\d)\.js', f)
        if not m:
            continue
        t = open(os.path.join(data, f)).read()
        for sc in json.loads(t[t.index(',') + 1:t.rindex(')')])['scenes']:
            key = f'{int(m.group(1))}:{sc[0]}'
            if key not in keep:
                info = focus.get(sc[2].replace('.png', '.webp'))
                if info:
                    lines.append(f'"{key}": ' + json.dumps(frames(info, k), separators=(', ', ',')) + ',')
            k += 1
    body = '\n'.join(lines)
    if keep:
        body += '\n// keep (hand-tuned; build_motion.py leaves these alone)\n' + '\n'.join(f'"{k}": {v},' for k, v in keep.items())
    tmp = out + '.tmp'
    open(tmp, 'w').write('// Ken Burns frames for /read, made by scripts/build_motion.py from macOS Vision faces and\n'
                         '// salient regions: "chapter:verse": [start, end, portrait start, portrait end], each [x, y, zoom].\n'
                         'VB.motion = {\n' + body.rstrip(',') + '\n};\n')
    os.replace(tmp, out)
    print(f'{a.book}: {len(lines)} generated, {len(keep)} kept')


if __name__ == '__main__':
    main()
