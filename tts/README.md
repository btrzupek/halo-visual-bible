# tts: narration on the halo box

Kokoro-82M (Apache 2.0) runs on halo's Radeon 8060S in a rootless Podman container and speaks
the visual Bible's text. The Mac reaches it through a launchd socket tunnel, the same way it
reaches ComfyUI.

| File | What it is |
|---|---|
| `Containerfile` | Python 3.12 + AMD TheRock gfx1151 PyTorch nightly + kokoro + espeak-ng + ffmpeg |
| `tts_server.py` | FastAPI: `POST /speak` (text to WAV), `POST /mp3` (WAV to MP3), `GET /health` |
| `halo-tts.service` | systemd user unit on halo; listens on `127.0.0.1:8880` only |
| `speech.py` | The one client everything uses: `speak`, a segment cache, lexicon, MP3 encoding |
| `tts.py` | CLI: a text or Markdown file to one WAV or MP3 |
| `lexicon.json` | Forced pronunciations (misaki phonemes), applied to every request |
| `../mcp-server/halo_tts.py` | MCP server: `halo_tts_status`, `halo_tts_speak`, `halo_tts_sample` |
| `../scripts/build_audio.py` | Narrates a book for `/read/<book>`: one MP3 per scene + verse timings |
| `../setup/com.halo.tts-tunnel.plist` | Mac launchd socket for `127.0.0.1:8880` |

## Install (done 2026-09-30)

```bash
# on halo
mkdir -p ~/halo-tts/cache && cd ~/halo-tts      # copy Containerfile, tts_server.py, halo-tts.service here
podman build -t halo-tts:latest -f Containerfile .
cp halo-tts.service ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable --now halo-tts
curl -s 127.0.0.1:8880/health

# on the Mac
sed "s/__USER__/$(whoami)/" setup/com.halo.tts-tunnel.plist > ~/Library/LaunchAgents/com.halo.tts-tunnel.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.halo.tts-tunnel.plist
curl -s 127.0.0.1:8880/health
```

Model weights download on first start into `~/halo-tts/cache/hf` (kept across rebuilds).

## What was verified, and what was not

Verified on halo (ROCm 7.14 host, Radeon 8060S, gfx1151):

- `/health` reports `device: cuda`, torch `2.10.0+rocm7.13` (TheRock nightly), the GPU by name.
- Speed: John 1:1-2 (8.1 s of audio) in 0.94 s on the GPU vs 25 s on the container's CPU.
  Whole scenes run at about 10x real time; John's 21 chapters take about 15 minutes.
- **MIOpen's LSTM fails on gfx1151** (`miopenStatusUnknownError`), so the server sets
  `torch.backends.cudnn.enabled = False` and uses PyTorch's own GPU kernels. That also makes the
  `MIOPEN_FIND_MODE=2` advice moot for now; it is still set in case MIOpen is re-enabled
  (`TTS_MIOPEN=1`). The startup warm-up still runs a spread of lengths (13 s).
- The stock `python:3.12-slim` image lacks `libatomic1`, which the spaCy chain needs.

Not done or assumed:

- Kokoro-FastAPI PR #431 (gfx1151) was closed unmerged, so this is a small server of our own instead.
- Chatterbox (voice cloning) is not installed. `tts.py --engine chatterbox` exits with a message.
  It needs a 10 to 20 s reference clip whose speaker has agreed to be cloned.
- No `rocm-smi` capture yet; GPU use is inferred from the device report and the 25x speed gap.
