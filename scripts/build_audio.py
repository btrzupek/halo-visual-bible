#!/usr/bin/env python3
"""Narrate a book for /read/<book>: one MP3 per scene plus a timing file the player syncs to.

Each verse is synthesized on its own (Kokoro on halo, through tts/speech.py), then joined with
short silences, so every verse's start time comes from real sample counts, not estimates.
Segments are cached by (text, voice, speed, lexicon), so a rerun only redoes what changed.

  python3 scripts/build_audio.py --book john --chapters 1-3
  python3 scripts/build_audio.py --book john --only 3:16 --force     # re-voice one scene

Writes site/audio/<book>/<book>-CC-VV.mp3 and site/<folder>/data/<book>-audio.js:
  VB.audio = {"3:16": {"src": "/audio/john/john-03-16.mp3?v=1a2b3c4d", "dur": 41.2, "t": [0.4, 6.1, ...]}}
"""
import argparse, hashlib, json, os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tts'))
import speech  # noqa: E402

BOOKS = {  # book (file prefix): (site folder, spoken title), canonical order
    'genesis': ('genesis', 'The First Book of Moses, called Genesis'),
    'joshua': ('joshua', 'The Book of Joshua'),
    'judges': ('judges', 'The Book of Judges'),
    'ruth': ('ruth', 'The Book of Ruth'),
    '1samuel': ('1samuel', 'The First Book of Samuel'),
    '2samuel': ('2samuel', 'The Second Book of Samuel'),
    '1kings': ('1kings', 'The First Book of the Kings'),
    '2kings': ('2kings', 'The Second Book of the Kings'),
    '1chronicles': ('1chronicles', 'The First Book of the Chronicles'),
    '2chronicles': ('2chronicles', 'The Second Book of the Chronicles'),
    'ezra': ('ezra', 'The Book of Ezra'),
    'nehemiah': ('nehemiah', 'The Book of Nehemiah'),
    'esther': ('esther', 'The Book of Esther'),
    'matthew': ('matthew', 'The Gospel according to Saint Matthew'),
    'mark': ('mark', 'The Gospel according to Saint Mark'),
    'luke': ('luke', 'The Gospel according to Saint Luke'),
    'john': ('bible', 'The Gospel according to Saint John'),
    'acts': ('acts', 'The Acts of the Apostles'),
}
ONES = ('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen '
        'sixteen seventeen eighteen nineteen').split()
TENS = {2: 'twenty', 3: 'thirty', 4: 'forty', 5: 'fifty'}
LEAD, VERSE_GAP, TITLE_GAP, TAIL = 0.35, 0.55, 0.9, 0.6


def number(n):
    return ONES[n] if n < 20 else TENS[n // 10] + ('-' + ONES[n % 10] if n % 10 else '')


def chapters(folder, book):
    out = {}
    d = os.path.join(ROOT, 'site', folder, 'data')
    for f in sorted(os.listdir(d)):
        m = re.fullmatch(book + r'-(\d\d)\.js', f)
        if m:
            s = open(os.path.join(d, f)).read()
            out[int(m.group(1))] = json.loads(s[s.index(',') + 1:s.rindex(')')])
    return out


def rng(spec):
    if not spec:
        return None
    a, _, b = spec.partition('-')
    return set(range(int(a), int(b or a) + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--book', default='john', choices=list(BOOKS) + ['all'])
    ap.add_argument('--voice', default='bm_george')
    ap.add_argument('--speed', type=float, default=1.0)
    ap.add_argument('--bitrate', default='64k')
    ap.add_argument('--chapters', help='e.g. 1-3')
    ap.add_argument('--only', help='comma-separated scene keys, e.g. 3:16,4:1')
    ap.add_argument('--force', action='store_true', help='rewrite MP3s even if present')
    ap.add_argument('--cache', default=os.path.expanduser('~/halo-audio/cache'))
    ap.add_argument('--log', default=os.path.expanduser('~/halo-images/visual-bible/audio/worklog.md'))
    a = ap.parse_args()
    for book in (list(BOOKS) if a.book == 'all' else [a.book]):
        a.book = book
        build(a)


def build(a):
    folder, title = BOOKS[a.book]
    chs, want_ch = chapters(folder, a.book), rng(a.chapters)
    only = set(a.only.split(',')) if a.only else None
    lex = speech.load_lexicon()
    out_dir = os.path.join(ROOT, 'site', 'audio', a.book)
    js_path = os.path.join(ROOT, 'site', folder, 'data', a.book + '-audio.js')
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.dirname(a.log), exist_ok=True)

    timing = {}
    if os.path.exists(js_path):  # keep scenes this run doesn't touch
        s = open(js_path).read()
        timing = json.loads(s[s.index('{'):s.rindex('}') + 1])
    print('server:', speech.health()['device'])

    t0, n, synth_total, audio_total = time.time(), 0, 0.0, 0.0
    log = []
    for c in sorted(chs):
        if want_ch and c not in want_ch:
            continue
        v = chs[c]['v']
        for i, sc in enumerate(chs[c]['scenes']):
            frm, to, key = sc[0], sc[1], f'{c}:{sc[0]}'
            if only and key not in only:
                continue
            name = f'{a.book}-{c:02d}-{frm:02d}.mp3'
            path = os.path.join(out_dir, name)
            if os.path.exists(path) and key in timing and not a.force and timing[key].get('voice') == a.voice:
                continue
            pcm, starts, syn = speech.silence(LEAD), [], 0.0
            if i == 0:  # a chapter opens with its title
                p, _, info = speech.cached_speak(f'{title}. Chapter {number(c)}.' if c == 1 else f'Chapter {number(c)}.',
                                                 a.voice, a.speed, lex, a.cache)
                pcm += p + speech.silence(TITLE_GAP); syn += info['synth']
            for k in range(frm, to + 1):
                starts.append(round(len(pcm) / 2 / speech.SR, 3))
                p, _, info = speech.cached_speak(v[k - 1], a.voice, a.speed, lex, a.cache)
                pcm += p + speech.silence(VERSE_GAP if k < to else TAIL); syn += info['synth']
            mp3 = speech.to_mp3(pcm, a.bitrate)
            tmp = path + '.tmp'
            open(tmp, 'wb').write(mp3); os.replace(tmp, path)
            dur = round(len(pcm) / 2 / speech.SR, 3)
            timing[key] = {'src': f'/audio/{a.book}/{name}', 'dur': dur, 't': starts, 'voice': a.voice}
            n += 1; synth_total += syn; audio_total += dur
            log.append(f'| {key} | {to - frm + 1} | {dur:.1f} | {syn:.1f} | {len(mp3) // 1024} |')
            print(f'{key:>6}  {to - frm + 1:3d} verses  {dur:6.1f}s audio  {syn:5.1f}s synth  {len(mp3) // 1024} KB', flush=True)

    # /audio/ is cached as immutable, so each URL carries a hash of its file: a re-voiced scene gets a new URL
    for k, e in timing.items():
        f = os.path.join(ROOT, 'site', e['src'].split('?')[0].lstrip('/'))
        if os.path.exists(f):
            e['src'] = e['src'].split('?')[0] + '?v=' + hashlib.sha1(open(f, 'rb').read()).hexdigest()[:8]
    keys = sorted(timing, key=lambda k: tuple(map(int, k.split(':'))))
    body = ',\n'.join(f'"{k}": ' + json.dumps(timing[k], separators=(',', ':')) for k in keys)
    tmp = js_path + '.tmp'
    open(tmp, 'w').write(f'// Narration for /read/{a.book}, built by scripts/build_audio.py. t = verse start times (s).\n'
                         f'VB.audio = {{\n{body}\n}};\n')
    os.replace(tmp, js_path)
    if n:
        with open(a.log, 'a') as f:
            f.write(f'\n## {a.book}, {time.strftime("%Y-%m-%d %H:%M")}, voice {a.voice}, speed {a.speed}, {a.bitrate}\n\n'
                    f'{n} scenes, {audio_total / 60:.1f} min audio, {synth_total:.0f} s synthesis '
                    f'(cache hits count 0), {time.time() - t0:.0f} s wall\n\n'
                    '| scene | verses | audio s | synth s | KB |\n|---|---|---|---|---|\n' + '\n'.join(log) + '\n')
    print(f'{n} scenes written, {audio_total / 60:.1f} min audio, {time.time() - t0:.0f} s; {len(timing)} scenes in {js_path}')


if __name__ == '__main__':
    main()
