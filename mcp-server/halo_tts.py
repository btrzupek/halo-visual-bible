#!/usr/bin/env python3
"""
halo-tts: MCP server for the Kokoro speech server on the halo box (../tts/tts_server.py).

Claude uses it to audition voices, check a pronunciation, or re-voice one passage. Bulk narration
of a book runs through scripts/build_audio.py instead, which calls the same client (../tts/speech.py)
so both paths sound identical.

  TTS_URL=http://127.0.0.1:8880 python halo_tts.py      (stdio, Claude Desktop / Claude Code)

Env vars:
  TTS_URL        speech server (default http://127.0.0.1:8880, the com.halo.tts-tunnel socket)
  HALO_AUDIO_DIR where clips are saved (default ~/halo-audio)

Requires: pip install "mcp[cli]<2"
"""
import os, sys, time

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tts'))
import speech  # noqa: E402

OUT_DIR = os.path.expanduser(os.environ.get('HALO_AUDIO_DIR', '~/halo-audio'))
MAX_CHARS = 4000  # keeps one call well under the ~60 s MCP client timeout

mcp = FastMCP('halo-tts')


def _save(pcm: bytes, name: str, fmt: str) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f'{name}-{time.strftime("%Y%m%d-%H%M%S")}.{fmt}')
    data = speech.to_mp3(pcm, '96k') if fmt == 'mp3' else speech.wav_bytes(pcm)
    open(path, 'wb').write(data)
    return path


@mcp.tool()
def halo_tts_status() -> dict:
    """Speech server status on halo: device (cuda = Radeon GPU, or cpu), versions, available voices."""
    return speech.health()


@mcp.tool()
def halo_tts_speak(text: str, voice: str = 'bm_george', speed: float = 1.0, use_lexicon: bool = True,
                   format: str = 'mp3') -> dict:
    """Speak text with Kokoro on halo and save it under ~/halo-audio. Returns the file path, audio
    seconds and synthesis seconds. Force a pronunciation inline with [Word](/phonemes/), or add it
    to tts/lexicon.json (applied when use_lexicon is true). Voices: bm_george, bm_lewis, bm_fable,
    bm_daniel (British male), bf_emma, bf_isabella, am_michael, am_onyx."""
    if len(text) > MAX_CHARS:
        return {'error': f'text is {len(text)} characters; the limit per call is {MAX_CHARS}'}
    pcm, secs, info = speech.speak(text, voice, speed, speech.load_lexicon() if use_lexicon else {})
    return {'path': _save(pcm, voice, format), 'audio_seconds': round(secs, 2),
            'synth_seconds': round(info['synth'], 2), 'device': info['device']}


@mcp.tool()
def halo_tts_sample(text: str, voices: list[str] | None = None, speed: float = 1.0) -> list[dict]:
    """Render the same text in several voices for a side-by-side audition (mp3 files in ~/halo-audio)."""
    voices = voices or ['bm_george', 'bm_lewis', 'bm_fable', 'bm_daniel']
    if len(text) * len(voices) > MAX_CHARS:
        return [{'error': 'too much text for one call; shorten it or pass fewer voices'}]
    lex = speech.load_lexicon()
    out = []
    for v in voices:
        pcm, secs, info = speech.speak(text, v, speed, lex)
        out.append({'voice': v, 'path': _save(pcm, 'sample-' + v, 'mp3'), 'audio_seconds': round(secs, 2),
                    'synth_seconds': round(info['synth'], 2)})
    return out


if __name__ == '__main__':
    mcp.run()
