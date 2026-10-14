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
    'M1': 'gentle opening, quiet and welcoming, sparse',
    'M2': 'warm and grateful, tender, a little lighter',
    'M3': 'tender and pleading, then searching and a little tense, emotional',
    'M4': 'resolute and steady, quietly building conviction',
    'M5': 'hopeful farewell, calm resolve, gently fading',
}
XF = 3.0


def ffmpeg():
    return subprocess.check_output([sys.executable, '-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                                   text=True).strip()


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
            tags = f'{st["base"]}, {MOODS[m["id"]]}'
            subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'ace_music.py'), '--tags', tags, '--seconds', str(length + 2),
                            '--bpm', str(st['bpm']), '--key', st['key'], '--seed', str(st['seed'] + i), '--out', f], check=True)
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
                      f'{fade_in},afade=t=out:st={length - XF}:d={XF},volume={a.music_gain},adelay={int(start * 1000)}:all=1[s{k}]')
    n = len(segs)
    total = M['duration'] + 2.5
    graph = ';'.join(chains) + ';' + ''.join(f'[s{k}]' for k in range(n)) + \
        f'amix=inputs={n}:normalize=0:duration=longest,apad=whole_dur={total}[mus];' + \
        f'[{n}:a]asplit=1[key];[mus][key]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=600,atrim=0:{total}[out]'
    dst = os.path.join(out_dir, 'audio'); os.makedirs(dst, exist_ok=True)
    out = os.path.join(dst, f'music-{a.style}.mp3')
    subprocess.run([ff, '-y', '-loglevel', 'error', *ins, '-i', narr, '-filter_complex', graph, '-map', '[out]',
                    '-b:a', '128k', out + '.tmp.mp3'], check=True)
    os.replace(out + '.tmp.mp3', out)
    print(out, f'{os.path.getsize(out) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
