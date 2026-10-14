#!/usr/bin/env python3
"""Score an epistle film: one ACE-Step piece per narrated movement, stitched and ducked under the narration.

  python3 scripts/build_music.py --book philemon --style lyre
  python3 scripts/build_music.py --book philemon --style oud

Reads site/watch/<book>/manifest.json (movement start times, narration files) and writes
site/watch/<book>/audio/music-<style>.mp3, the whole film long. Each movement's piece starts 1.5 s before its
movement and crossfades 3 s with the next; the music fades out before the unnarrated epilogue; a sidechain
compressor dips it under the narration. Pieces are cached in ~/halo-images/visual-bible/<book>/music/.
Needs halo's ComfyUI (scripts/ace_music.py) and ffmpeg from imageio-ffmpeg.
"""
import argparse, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLES = {
    'lyre': {'base': 'instrumental, ancient Mediterranean, solo plucked lyre, low sustained drone, soft frame drum, warm reverb, '
                     'film score underscore, no vocals', 'key': 'D minor', 'bpm': 60, 'seed': 7},
    'oud': {'base': 'instrumental, Middle Eastern ancient, oud and ney flute, slow modal melody, soft hand drum, dusty and warm, '
                    'film score underscore, no vocals', 'key': 'D minor', 'bpm': 64, 'seed': 21},
}
MOODS = {   # by movement id; the epilogue (unnarrated) is left silent
    'M1': 'gentle opening, warm and welcoming, continuous flowing melody',
    'M2': 'warm and grateful, tender, a little lighter',
    'M3': 'tender and pleading, then searching and a little tense, emotional',
    'M4': 'resolute and steady, quietly building conviction',
    'M5': 'hopeful farewell, calm resolve, continuous flowing melody',
}
XF = 3.0
PIECE_LUFS = -20        # every movement's piece is levelled to this before mixing, so movements match
# Ducking: a slow, gentle dip that settles under the narration rather than pumping on each word
DUCK = 'sidechaincompress=threshold=0.05:ratio=3:attack=300:release=2500:knee=6'


def ffmpeg():
    return subprocess.check_output([sys.executable, '-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                                   text=True).strip()


CHUNK = 30.0      # ACE-Step pieces longer than this tend to contain long silent stretches; 30 s ones are continuous
TAIL = 4.0        # extra seconds generated per section and cut off, so ACE-Step's own ending fade never reaches the mix
TRIES = 10


def silent_gaps(path, floor=-50.0, window=1.5):
    """Seconds of the longest stretch quieter than `floor` dB (RMS over `window` s) in the first CHUNK seconds."""
    import numpy as np
    raw = subprocess.run([ffmpeg(), '-loglevel', 'error', '-i', path, '-ac', '1', '-ar', '8000', '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float) / 32768
    hop = 800; w = int(window * 8000)
    x = x[:int(CHUNK * 8000)]
    rms = [20 * np.log10(np.sqrt(np.mean(x[k:k + w] ** 2)) + 1e-9) for k in range(0, max(1, len(x) - w), hop)]
    run = best = 0
    for v in rms:
        run = run + 1 if v < floor else 0; best = max(best, run)
    return best * hop / 8000


def build_piece(out, tags, length, st, seed_base, work):
    """A movement's music: 30 s ACE-Step sections, each checked for silent gaps (regenerated with a new seed if it has
    one; the quietest-gap take is kept if none is clean), levelled, and chained with 3 s crossfades to cover
    `length` seconds."""
    n = max(1, int(-(-(length - XF) // (CHUNK - XF))))
    parts = []
    for c in range(n):
        p = out.replace('.mp3', f'.part{c}.mp3')
        best = None
        for attempt in range(TRIES):
            seed = st['seed'] + seed_base + 37 * c + 101 * attempt
            take = p.replace('.mp3', f'.t{attempt}.mp3')
            subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'ace_music.py'), '--tags', tags,
                            '--seconds', str(CHUNK + TAIL), '--bpm', str(st['bpm']), '--key', st['key'], '--seed', str(seed),
                            '--out', take], check=True, stdout=subprocess.DEVNULL)
            gap = silent_gaps(take)
            if best is None or gap < best[0]:
                best = (gap, take)
            if gap < 1.0:
                break
            print(f'  {os.path.basename(out)} section {c}: {gap:.1f} s silent gap, new seed', flush=True)
        if best[0] >= 1.0:
            print(f'  {os.path.basename(out)} section {c}: no clean take in {TRIES}, kept the best ({best[0]:.1f} s gap)', flush=True)
        subprocess.run([ffmpeg(), '-y', '-loglevel', 'error', '-i', best[1], '-t', str(CHUNK), '-b:a', '192k', p], check=True)
        for t in range(TRIES):
            q = p.replace('.mp3', f'.t{t}.mp3')
            if os.path.exists(q):
                os.remove(q)
        parts.append(p)
    if n == 1:
        os.replace(parts[0], out); return
    ins = sum((['-i', p] for p in parts), [])
    norm = ''.join(f'[{k}:a]loudnorm=I={PIECE_LUFS}:TP=-2:LRA=7,aresample=48000[n{k}];' for k in range(n))
    chain, last = norm, 'n0'
    for k in range(1, n):
        chain += f'[{last}][n{k}]acrossfade=d={XF}:c1=tri:c2=tri[x{k}];'; last = f'x{k}'
    subprocess.run([ffmpeg(), '-y', '-loglevel', 'error', *ins, '-filter_complex', chain.rstrip(';'), '-map', f'[{last}]',
                    '-b:a', '192k', out], check=True)
    for p in parts:
        os.remove(p)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--book', required=True); ap.add_argument('--style', required=True, choices=STYLES)
    ap.add_argument('--music-gain', type=float, default=0.55); ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    out_dir = os.path.join(ROOT, 'site', 'watch', a.book)
    M = json.load(open(os.path.join(out_dir, 'manifest.json')))
    work = os.path.expanduser(f'~/halo-images/visual-bible/{a.book}/music'); os.makedirs(work, exist_ok=True)
    st = STYLES[a.style]
    moves = [m for m in M['movements'] if m['id'] in MOODS]
    ends = [m2['start'] for m2 in M['movements'][1:]] + [M['duration']]
    segs = []
    for i, m in enumerate(M['movements']):
        if m['id'] not in MOODS:
            continue
        start = max(0.0, m['start'] - (1.5 if i else 0))
        end = min(ends[i], M['narration_end']) + (1.5 if ends[i] < M['narration_end'] else 2.5)
        length = round(end - start, 1)
        f = os.path.join(work, f'{a.style}-{m["id"]}.mp3')
        if a.force or not os.path.exists(f):
            build_piece(f, f'{st["base"]}, {MOODS[m["id"]]}, steady presence throughout', length, st, 1000 * i, work)
        segs.append((f, start, length))
        print(f'{a.style} {m["id"]} {start:.1f}+{length:.1f}s', flush=True)
    ff = ffmpeg()
    narr = os.path.join(work, 'narration.wav')        # the narration, back to back, as the sidechain key
    lst = os.path.join(work, 'narr.txt')
    with open(lst, 'w') as fh:
        for au in M['audio']:
            fh.write(f"file '{os.path.join(ROOT, 'site', au['src'].lstrip('/').split('?')[0])}'\n")
    subprocess.run([ff, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-ar', '48000', '-ac', '2', narr], check=True)
    ins, chains = [], []
    for k, (f, start, length) in enumerate(segs):
        ins += ['-i', f]
        fade_in = 'afade=t=in:d=2' if k == 0 else f'afade=t=in:d={XF}'
        chains.append(f'[{k}:a]atrim=0:{length},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,'
                      f'loudnorm=I={PIECE_LUFS}:TP=-2:LRA=7,aresample=48000,'
                      f'{fade_in},afade=t=out:st={length - XF}:d={XF},volume={a.music_gain},adelay={int(start * 1000)}:all=1[s{k}]')
    n = len(segs)
    total = M['duration'] + 2.5
    graph = ';'.join(chains) + ';' + ''.join(f'[s{k}]' for k in range(n)) + \
        f'amix=inputs={n}:normalize=0:duration=longest,apad=whole_dur={total}[mus];' + \
        f'[{n}:a]asplit=1[key];[mus][key]{DUCK},atrim=0:{total}[out]'
    dst = os.path.join(out_dir, 'audio'); os.makedirs(dst, exist_ok=True)
    out = os.path.join(dst, f'music-{a.style}.mp3')
    subprocess.run([ff, '-y', '-loglevel', 'error', *ins, '-i', narr, '-filter_complex', graph, '-map', '[out]',
                    '-b:a', '128k', out + '.tmp.mp3'], check=True)
    os.replace(out + '.tmp.mp3', out)
    print(out, f'{os.path.getsize(out) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
