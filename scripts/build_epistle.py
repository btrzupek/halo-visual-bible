#!/usr/bin/env python3
"""Build an epistle-mode film (the "Watch" player) from a storyboard, the narration timing and the shot assets.

  uv run --with pyyaml --with pillow python scripts/build_epistle.py --book philemon

Reads  ~/halo-images/visual-bible/<book>/<book>_storyboard.yaml   (shot list; see docs in that folder's HANDOFF.md)
       site/<book>/data/<book>-audio.js and <book>-01.js            (narration per /read scene, with verse start times)
       ~/halo-images/visual-bible/<book>/shots/<id>/keyframe.png, depth.png, video.mp4 (whatever exists)
Writes site/watch/<book>/manifest.json, img/<id>.webp, depth/<id>.png, video/<id>.mp4, and index.html.

Timing: the clock is the narration. Each shot covers its verse range; shots that share a range split it by `weight`;
a `cue` (a word or phrase in the verse) moves the cut to where that word falls, estimated from its character position
in the verse (no word-level alignment yet). Unnarrated shots (verses: null) follow the narration for `duration_sec`.
A video shot without its video.mp4 yet plays as its keyframe with a slow push-in (the animatic).
"""
import argparse, html, json, os, re, shutil, time
import yaml
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
WORK = os.path.expanduser('~/halo-images/visual-bible')
IMG_W = 2048          # keyframes are 2560x1440; 2048 keeps room for pans and parallax at a phone-friendly size
DEPTH_W = 1024
DEPTH_V = 2          # bump when the depth preprocessing changes, so every depth map is rebuilt
MIN_SHOT = 1.2        # seconds; cues never squeeze a shot shorter than this


def jsdata(path, var):
    s = open(path).read()
    if var == 'audio':
        return json.loads(s[s.index('{', s.index('VB.audio')):s.rindex('}') + 1])
    return json.loads(s[s.index(',') + 1:s.rindex(')')])


STAMPS = {}   # site file -> "source path:mtime" it was built from; kept in the working folder, not the site


def stale(dst, src):
    """True when dst was not built from this exact source file."""
    return not os.path.exists(dst) or STAMPS.get(os.path.relpath(dst, SITE)) != f'{src}:{int(os.path.getmtime(src))}:{DEPTH_V}'


def mark(dst, src):
    STAMPS[os.path.relpath(dst, SITE)] = f'{src}:{int(os.path.getmtime(src))}:{DEPTH_V}'


def save_atomic(im, out, **kw):
    tmp = out + '.tmp'
    im.save(tmp, format=kw.pop('format'), **kw)
    os.replace(tmp, out)


def verse_range(spec):
    if spec is None:
        return None
    a, _, b = str(spec).partition('-')
    return int(a), int(b or a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--book', required=True)
    ap.add_argument('--chapter', type=int, default=1)
    ap.add_argument('--placeholders', action='store_true',
                    help='stand in the location image (and its depth) for shots without a keyframe yet, for testing')
    a = ap.parse_args()
    book, work = a.book, os.path.join(WORK, a.book)
    sb = yaml.safe_load(open(os.path.join(work, f'{book}_storyboard.yaml')))
    ch = jsdata(os.path.join(SITE, book, 'data', f'{book}-{a.chapter:02d}.js'), 'chapter')
    audio = jsdata(os.path.join(SITE, book, 'data', f'{book}-audio.js'), 'audio')
    text = ch['v']

    # narration segments in scene order, and absolute verse start/end times
    segs, vstart, vend, t0 = [], {}, {}, 0.0
    for sc in ch['scenes']:
        first, last = sc[0], sc[1]
        au = audio[f'{a.chapter}:{first}']
        segs.append({'src': au['src'], 'start': round(t0, 3), 'dur': au['dur'], 'first': first, 'last': last})
        for i, v in enumerate(range(first, last + 1)):
            vstart[v] = t0 + au['t'][i]
            vend[v] = t0 + (au['t'][i + 1] if i + 1 < len(au['t']) else au['dur'])
        t0 += au['dur']
    narr_end = t0

    def cue_time(v, cue):
        s = text[v - 1]
        i = s.lower().find(cue.lower())
        if i < 0:
            raise SystemExit(f'cue {cue!r} not found in verse {v}')
        return vstart[v] + (vend[v] - vstart[v]) * i / max(1, len(s)) - 0.15

    shots, movements = [], []
    for m in sb['movements']:
        vr = verse_range(m.get('verses'))
        mstart = (min(s['start'] for s in segs if s['first'] <= vr[0] <= s['last']) if vr else narr_end)
        movements.append({'id': m['id'], 'title': m['title'], 'start': round(mstart, 3)})
        ms = m['shots']
        if not vr:                                   # unnarrated: fixed durations after the narration
            t = narr_end
            for s in ms:
                d = float(s.get('duration_sec', 5))
                shots.append(dict(s, _start=t, _end=t + d)); t += d
            continue
        # group consecutive shots with the same verse spec
        groups = []
        for s in ms:
            if groups and groups[-1][0] == str(s['verses']):
                groups[-1][1].append(s)
            else:
                groups.append((str(s['verses']), [s]))
        gstarts = []
        for gi, (spec, gs) in enumerate(groups):
            va, vb = verse_range(spec)
            st = mstart if gi == 0 else vstart[va]
            if gs[0].get('cue'):
                st = max(st, cue_time(va, gs[0]['cue'])) if gi else st
            gstarts.append(st)
        mend = max(s['start'] + s['dur'] for s in segs if s['first'] <= vr[1] <= s['last'])
        for gi, (spec, gs) in enumerate(groups):
            st = gstarts[gi]
            en = gstarts[gi + 1] if gi + 1 < len(groups) else mend
            wsum = sum(float(s.get('weight', 1)) for s in gs)
            t = st
            starts = []
            for s in gs:
                starts.append(t); t += (en - st) * float(s.get('weight', 1)) / wsum
            va = verse_range(spec)[0]
            for k, s in enumerate(gs):
                if k and s.get('cue'):
                    starts[k] = cue_time(va, s['cue'])
            for k in range(1, len(starts)):           # keep cuts in order and shots watchable
                starts[k] = max(starts[k], starts[k - 1] + MIN_SHOT)
            for k, s in enumerate(gs):
                shots.append(dict(s, _start=starts[k], _end=starts[k + 1] if k + 1 < len(gs) else en))
    for i in range(len(shots) - 1):                   # contiguous: each shot ends where the next begins
        if shots[i]['_end'] > shots[i + 1]['_start'] or shots[i + 1]['_start'] - shots[i]['_end'] < 0.05:
            shots[i]['_end'] = shots[i + 1]['_start']

    out = os.path.join(SITE, 'watch', book)
    stamp_file = os.path.join(work, 'build-stamps.json')
    if os.path.exists(stamp_file):
        STAMPS.update(json.load(open(stamp_file)))
    for sub in ('img', 'depth', 'video'):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
    res, missing = [], []
    for s in shots:
        sid = s['id']; d = os.path.join(work, 'shots', sid)
        kf, dp, vid, lf = (os.path.join(d, f) for f in ('keyframe.png', 'depth.png', 'video.mp4', 'lastframe.png'))
        rec = {'id': sid, 'type': s['type'], 'start': round(s['_start'], 3), 'end': round(s['_end'], 3),
               'verses': s.get('verses'), 'motion': s.get('motion'), 'grade': s.get('grade'),
               'reading_room': 'READING ROOM' in (s.get('prompt') or s.get('first_frame_prompt') or '')}
        if not os.path.exists(kf) and a.placeholders:
            cast = json.load(open(os.path.join(work, 'cast.json')))
            kf = os.path.join(os.path.expanduser('~/halo-images'), cast['locations'][s['location']])
            loc_depth = os.path.join(work, 'refs', os.path.splitext(cast['locations'][s['location']])[0] + '.depth.png')
            if os.path.exists(loc_depth):
                dp = loc_depth
            rec['placeholder'] = True
        if os.path.exists(kf):
            dst = os.path.join(out, 'img', f'{sid}.webp')
            if stale(dst, kf):
                im = Image.open(kf).convert('RGB')
                if im.width > IMG_W:
                    im = im.resize((IMG_W, round(im.height * IMG_W / im.width)), Image.LANCZOS)
                save_atomic(im, dst, format='WEBP', quality=80, method=6); mark(dst, kf)
            rec['img'] = f'img/{sid}.webp?v={int(os.path.getmtime(kf))}'
        else:
            missing.append(sid)
        if s['type'] == 'parallax' and os.path.exists(dp):
            dst = os.path.join(out, 'depth', f'{sid}.png')
            if stale(dst, dp):
                im = Image.open(dp)
                im = im.point(lambda x: x / 256).convert('L') if im.mode.startswith('I') else im.convert('L')
                im = im.resize((DEPTH_W, round(im.height * DEPTH_W / im.width)), Image.BICUBIC)
                # grow near objects a few pixels past their edges, then soften: the parallax shader then moves a
                # person's whole outline with them instead of leaving a ghost edge on the background
                im = im.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(3))
                save_atomic(im, dst, format='PNG', optimize=True); mark(dst, dp)
            rec['depth'] = f'depth/{sid}.png?v={int(os.path.getmtime(dp))}{DEPTH_V}'
        if s['type'] == 'video' and os.path.exists(vid):
            dst = os.path.join(out, 'video', f'{sid}.mp4')
            if stale(dst, vid):
                shutil.copyfile(vid, dst); mark(dst, vid)
            rec['video'] = f'video/{sid}.mp4?v={int(os.path.getmtime(vid))}'
        res.append(rec)
    end = max(r['end'] for r in res)
    manifest = {
        'mode': 'epistle', 'book': book, 'title': sb['meta'].get('title') or 'The Epistle of Paul to Philemon',
        'short': sb['meta']['book'], 'duration': round(end, 3), 'narration_end': round(narr_end, 3),
        'audio': [{'src': s['src'], 'start': s['start'], 'dur': s['dur']} for s in segs],
        'verses': [{'n': v, 'start': round(vstart[v], 3), 'end': round(vend[v], 3), 'text': text[v - 1]} for v in sorted(vstart)],
        'movements': movements, 'shots': res,
        'end_card': {'hold_black': 2.0},
        'review': bool(a.placeholders),   # review builds show each shot's ID on screen (?ids=0/1 overrides)
    }
    with open(os.path.join(out, 'manifest.json.tmp'), 'w') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    os.replace(os.path.join(out, 'manifest.json.tmp'), os.path.join(out, 'manifest.json'))
    write_page(out, manifest)
    json.dump(STAMPS, open(stamp_file, 'w'), indent=0)
    print(f'{book}: {len(res)} shots, {len(movements)} movements, {end:.1f} s '
          f'(narration {narr_end:.1f} s); keyframes missing: {len(missing)}'
          + (f' ({", ".join(missing)})' if missing else ''))


def write_page(out, m):
    title = m['title']
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Watch {html.escape(m['short'])}: a visual Bible</title>
<meta name="description" content="{html.escape(title)} in the King James Version, read aloud as a short film: stills, camera moves and narration, made on one AMD Ryzen AI Halo box.">
<meta name="theme-color" content="#05060a">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Visual Bible">
<meta property="og:title" content="Watch {html.escape(m['short'])}: a visual Bible">
<meta property="og:image" content="https://halo-visual-bible.vercel.app/og/home.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Spectral:ital,wght@0,300;0,400;0,500;1,300;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/watch.css?v=4">
</head>
<body>
<noscript><p style="padding:2rem">This page needs JavaScript. <a href="/read/{m['book']}" style="color:#d4b066">Read {html.escape(m['short'])}</a>.</p></noscript>
<script>window.WATCH={json.dumps({'book': m['book'], 'manifest': 'manifest.json?v=' + str(int(time.time()))})};</script>
<script src="/assets/watch.js?v=4"></script>
</body>
</html>
'''
    with open(os.path.join(out, 'index.html'), 'w') as f:
        f.write(page)


if __name__ == '__main__':
    main()
