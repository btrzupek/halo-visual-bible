"""Client for the Kokoro speech server on halo (tts/tts_server.py), shared by the halo-tts MCP
server, tts.py and scripts/build_audio.py so every path synthesizes the same way.

TTS_URL (default http://127.0.0.1:8880) is the Mac end of the com.halo.tts-tunnel launchd socket.
"""
import hashlib, io, json, os, re, urllib.request, wave

TTS_URL = os.environ.get('TTS_URL', 'http://127.0.0.1:8880').rstrip('/')
SR = 24000
HERE = os.path.dirname(os.path.abspath(__file__))


def health(timeout=10):
    with urllib.request.urlopen(TTS_URL + '/health', timeout=timeout) as r:
        return json.load(r)


def load_lexicon(path=None):
    """{"Cephas": "sˈifəs", ...}: forced pronunciations, in misaki's phoneme alphabet."""
    path = path or os.path.join(HERE, 'lexicon.json')
    if not os.path.exists(path):
        return {}
    return {k: v for k, v in json.load(open(path)).items() if not k.startswith('_')}


def apply_lexicon(text, lexicon):
    for word, ph in lexicon.items():
        text = re.sub(r'(?<![\w\[])' + re.escape(word) + r'(?![\w\]])', '[' + word + '](/' + ph + '/)', text)
    return text


def clean(text):
    """KJV verse text to speech text."""
    text = text.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    return re.sub(r'\s+', ' ', text).strip()


def speak(text, voice='bm_george', speed=1.0, lexicon=None, timeout=600):
    """Returns (pcm16 bytes at 24 kHz mono, seconds of audio, info dict)."""
    body = json.dumps({'text': apply_lexicon(clean(text), lexicon or {}), 'voice': voice, 'speed': speed}).encode()
    req = urllib.request.Request(TTS_URL + '/speak', body, {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data, h = r.read(), r.headers
    with wave.open(io.BytesIO(data)) as w:
        pcm = w.readframes(w.getnframes())
    return pcm, len(pcm) / 2 / SR, {'synth': float(h.get('X-Synth-Seconds', 0)), 'device': h.get('X-Device')}


def cached_speak(text, voice, speed, lexicon, cache_dir):
    """speak() with an on-disk cache keyed by everything that changes the audio."""
    key = hashlib.sha256(json.dumps([apply_lexicon(clean(text), lexicon), voice, speed]).encode()).hexdigest()[:24]
    path = os.path.join(cache_dir, key + '.pcm')
    if os.path.exists(path):
        pcm = open(path, 'rb').read()
        return pcm, len(pcm) / 2 / SR, {'synth': 0.0, 'device': 'cache'}
    pcm, secs, info = speak(text, voice, speed, lexicon)
    os.makedirs(cache_dir, exist_ok=True)
    tmp = path + '.tmp'
    open(tmp, 'wb').write(pcm)
    os.replace(tmp, path)
    return pcm, secs, info


def silence(seconds):
    return b'\x00\x00' * int(round(seconds * SR))


def wav_bytes(pcm):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm)
    return buf.getvalue()


def to_mp3(pcm, bitrate='64k', timeout=300):
    """Encode on halo (the container has ffmpeg), so the Mac needs nothing extra."""
    req = urllib.request.Request(TTS_URL + '/mp3?bitrate=' + bitrate, wav_bytes(pcm), {'Content-Type': 'audio/wav'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()
