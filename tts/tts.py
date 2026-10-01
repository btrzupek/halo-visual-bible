#!/usr/bin/env python3
"""Text or Markdown file to speech, using the Kokoro server on halo (see README.md).

  python3 tts/tts.py notes.md -o notes.mp3
  python3 tts/tts.py chapter.txt --voice bm_george --speed 0.95 -o chapter.wav

Markdown is stripped to plain speech (code blocks, URLs, heading and list markers, emphasis).
Text is split into paragraphs, then sentences; each is synthesized in turn and joined with short
pauses (longer between paragraphs). .mp3 output is encoded on halo, so the Mac needs no ffmpeg.
--engine chatterbox is reserved for voice cloning and is not installed yet.
"""
import argparse, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import speech  # noqa: E402

SENTENCE_GAP, PARAGRAPH_GAP, MAX_CHARS = 0.35, 0.8, 400


def strip_markdown(md):
    md = re.sub(r'```.*?```|~~~.*?~~~', ' ', md, flags=re.S)        # fenced code
    md = re.sub(r'`[^`]*`', ' ', md)                                  # inline code
    md = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', md)                     # images
    md = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', md)                  # links keep their text
    md = re.sub(r'https?://\S+', ' ', md)                             # bare URLs
    md = re.sub(r'^\s{0,3}(#{1,6}|>|[-*+]|\d+\.)\s+', '', md, flags=re.M)  # headings, quotes, lists
    md = re.sub(r'^\s*([-*_]\s*){3,}$', '', md, flags=re.M)           # rules
    md = re.sub(r'(\*\*|__|\*|_)(\S.*?\S|\S)\1', r'\2', md)           # emphasis
    md = re.sub(r'<[^>]+>', ' ', md)                                  # html tags
    md = re.sub(r'^\s*\|.*\|\s*$', '', md, flags=re.M)                # tables
    return re.sub(r'[ \t]+([.,;:!?])', r'\1', md)                 # space left before punctuation


def chunks(text):
    """[[sentence-sized chunks of paragraph 1], [paragraph 2], ...]"""
    out = []
    for para in re.split(r'\n\s*\n', text):
        para = ' '.join(para.split())
        if not para:
            continue
        parts, cur = [], ''
        for s in re.split(r'(?<=[.!?;:])\s+', para):
            if cur and len(cur) + len(s) > MAX_CHARS:
                parts.append(cur); cur = s
            else:
                cur = (cur + ' ' + s).strip()
        if cur:
            parts.append(cur)
        out.append(parts)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('input')
    ap.add_argument('-o', '--output', help='.wav or .mp3 (default: input name + .mp3)')
    ap.add_argument('--engine', default='kokoro', choices=['kokoro', 'chatterbox'])
    ap.add_argument('--voice', default='bm_george')
    ap.add_argument('--reference', help='chatterbox: 10 to 20 s voice clip (not available yet)')
    ap.add_argument('--speed', type=float, default=1.0)
    ap.add_argument('--bitrate', default='96k')
    a = ap.parse_args()
    if a.engine == 'chatterbox':
        sys.exit('chatterbox is not installed on halo yet; use --engine kokoro')

    text = open(a.input, encoding='utf-8').read()
    if a.input.lower().endswith(('.md', '.markdown')):
        text = strip_markdown(text)
    out = a.output or os.path.splitext(a.input)[0] + '.mp3'
    lex, pcm, t0, syn = speech.load_lexicon(), b'', time.time(), 0.0
    paras = chunks(text)
    for i, para in enumerate(paras):
        for j, c in enumerate(para):
            p, _, info = speech.speak(c, a.voice, a.speed, lex)
            pcm += p + speech.silence(SENTENCE_GAP if j < len(para) - 1 else (PARAGRAPH_GAP if i < len(paras) - 1 else 0))
            syn += info['synth']
        print(f'paragraph {i + 1}/{len(paras)}', file=sys.stderr, flush=True)
    data = speech.to_mp3(pcm, a.bitrate) if out.lower().endswith('.mp3') else speech.wav_bytes(pcm)
    open(out, 'wb').write(data)
    print(f'{out}: {len(pcm) / 2 / speech.SR:.1f} s audio, {syn:.1f} s synthesis, {time.time() - t0:.1f} s wall')


if __name__ == '__main__':
    main()
