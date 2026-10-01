"""Kokoro-82M speech server for halo. One request at a time; WAV out.

POST /speak {"text", "voice"="bm_george", "speed"=1.0} -> audio/wav (24 kHz mono)
  headers: X-Duration (audio seconds), X-Synth-Seconds (wall time), X-Device
GET /health -> device, versions, voices
POST /mp3?bitrate=64k (body: WAV) -> audio/mpeg, mono, via ffmpeg
Pronunciations can be forced inline with misaki's syntax: [Cephas](/sˈifəs/).
"""
import io, os, subprocess, threading, time
import numpy as np, soundfile as sf, torch
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from kokoro import KPipeline

# MIOpen's LSTM fails on gfx1151 (miopenStatusUnknownError, TheRock torch, Sept 2026). PyTorch's own
# GPU kernels work and run ~8x real time, so MIOpen is switched off. TTS_MIOPEN=1 turns it back on.
if os.environ.get('TTS_MIOPEN') != '1':
    torch.backends.cudnn.enabled = False
FORCE_CPU = os.environ.get('TTS_DEVICE') == 'cpu'
DEVICE = 'cuda' if torch.cuda.is_available() and not FORCE_CPU else 'cpu'
VOICES = ['bm_george', 'bm_lewis', 'bm_fable', 'bm_daniel', 'bf_emma', 'bf_isabella', 'am_michael', 'am_onyx']
SR = 24000
lock = threading.Lock()
pipes = {}

def pipe(lang):
    if lang not in pipes:
        pipes[lang] = KPipeline(lang_code=lang, repo_id='hexgrad/Kokoro-82M', device=DEVICE)
    return pipes[lang]

def synth(text, voice, speed):
    p = pipe(voice[0])
    parts = [a.numpy() if hasattr(a, 'numpy') else np.asarray(a)
             for _, _, a in p(text, voice=voice, speed=speed, split_pattern=r'\n+') if a is not None]
    return np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)

app = FastAPI()

@app.on_event('startup')
def warm():
    # MIOpen tunes kernels per input shape; run a spread of lengths once so real requests don't stall.
    t = time.time()
    words = ('In the beginning was the Word, and the Word was with God, and the Word was God. '
             'The same was in the beginning with God. All things were made by him. ' * 4).split()
    for n in (2, 5, 9, 14, 20, 28, 40, 55):
        synth(' '.join(words[:n]), 'bm_george', 1.0)
    print(f'warm-up on {DEVICE}: {time.time() - t:.1f}s', flush=True)

class Speak(BaseModel):
    text: str
    voice: str = 'bm_george'
    speed: float = 1.0

@app.get('/health')
def health():
    return {'device': DEVICE, 'torch': torch.__version__, 'hip': getattr(torch.version, 'hip', None),
            'gpu': torch.cuda.get_device_name(0) if DEVICE == 'cuda' else None, 'voices': VOICES, 'sample_rate': SR}

@app.post('/speak')
def speak(req: Speak):
    if req.voice not in VOICES:
        raise HTTPException(400, f'unknown voice {req.voice}')
    if not req.text.strip():
        raise HTTPException(400, 'empty text')
    with lock:
        t = time.time()
        audio = synth(req.text, req.voice, req.speed)
        secs = time.time() - t
    buf = io.BytesIO()
    sf.write(buf, audio, SR, format='WAV', subtype='PCM_16')
    return Response(buf.getvalue(), media_type='audio/wav', headers={
        'X-Duration': f'{len(audio) / SR:.3f}', 'X-Synth-Seconds': f'{secs:.3f}', 'X-Device': DEVICE})


@app.post('/mp3')
async def mp3(request: Request, bitrate: str = '64k'):
    wav = await request.body()
    r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'wav', '-i', 'pipe:0',
                        '-ac', '1', '-codec:a', 'libmp3lame', '-b:a', bitrate, '-f', 'mp3', 'pipe:1'],
                       input=wav, capture_output=True)
    if r.returncode:
        raise HTTPException(500, r.stderr.decode()[-500:])
    return Response(r.stdout, media_type='audio/mpeg')
