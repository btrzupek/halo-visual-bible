# Scripts

Both are stdlib-only Python 3.10+ and talk to ComfyUI over HTTP (by default the SSH-tunnel
endpoint `http://127.0.0.1:8188`).

## `comfy_history_metrics.py`

Pulls `/history` and writes `comfy_history.csv` (one row per job) and `history_summary.md`
(per-job-type count / median / p90 / min / max / GPU-minutes, time right after a model swap,
longest idle gap, sessions and GPU-busy %, cross-check against the local image folder, and
book-window stats if you point it at the viewer's `data/`).

```bash
python3 comfy_history_metrics.py --url http://127.0.0.1:8188 \
  --images ~/halo-images --book ../viewer/data --out ./metrics
```

ComfyUI keeps history in memory: it only covers jobs since ComfyUI last started (up to
`--max-items`). Fully cached replays (identical re-submissions) are excluded from timings.
Save a snapshot after each working session so a restart doesn't lose it, and pass the
snapshots back in with `--history` (`--url ''` uses the snapshots alone):

```bash
curl -s 'http://127.0.0.1:8188/history?max_items=5000' > history-$(date +%Y%m%d-%H%M%S).json
python3 comfy_history_metrics.py --url '' --history 'history-*.json' \
  --images ~/halo-images --book ../site/mark/data --out ../site/data/mark
```

## `halo_benchmark.py`

Controlled benchmark with fixed seeds, using the workflows in `../workflows`. With
`--ssh-host`, it streams 1 Hz telemetry from the ComfyUI machine (no root): amdgpu hwmon
socket power (PPT), edge temperature, GPU busy %, GTT memory, shader clock, CPU Tctl, and
`amd-smi metric --power --json` (GFX, cores, "system" power).

```bash
python3 halo_benchmark.py --url http://127.0.0.1:8188 --ssh-host <halo-host> \
  --reference ~/halo-images/<portrait>.png --edit-image ~/halo-images/<scene>.png \
  --images-out ~/halo-images/benchmark --results ./results
```

Plan: idle baseline (models unloaded) → FLUX.2 klein 1344×768 ×(1 cold + 5 warm) →
klein + reference ×5 → Qwen-Image-Edit ×(1 cold after klein + 3 warm) → Qwen-Image 1328² ×(1 cold + 2 warm).
It calls ComfyUI's `/free` to unload models before the cold klein run and waits for an empty queue before
measuring idle.

Outputs: `benchmark.csv` (per run: wall and ComfyUI execution time, avg/peak socket power,
energy in Wh total and above idle, peak GTT, peak temperatures, avg GPU busy),
`benchmark_samples.csv` (raw samples) and `benchmark_summary.json` (per job type and phase).
Energy is socket (APU package) energy, not wall-plug energy.

## `build_site_assets.py`

Converts every attempt to WebP (`site/images/full`, `site/images/thumb`) and writes
`site/data/gallery.js` for the Making of page, tagging each image with its book. Pass one
`--book Name=folder` per book, plus any history snapshots. Entries already in `gallery.js`
whose jobs are no longer in ComfyUI's history are kept, so a restart never drops a book.

```bash
python3 build_site_assets.py --url http://127.0.0.1:8188 --images ~/halo-images \
  --book John=../site/bible/data --book Mark=../site/mark/data \
  --history '~/halo-images/visual-bible/mark/history-*.json' --site ../site
```

## `build_verse_index.py`

Writes the public verse → image index that other apps (e.g. Inscripture) read:
`site/index/v1/books.json` lists the illustrated books and chapters, and
`site/index/v1/<book>.json` maps each chapter to its scenes (verse range, title, subtitle,
kind, full/thumb WebP URLs, size, and a deep link into the viewer). Scene ids are
`<book>.<chapter>.<first verse>`, matching the viewer anchors (`/matthew#s5-13`), so they stay
stable when an image is swapped. Verse numbers are KJV. Scenes whose WebP isn't in
`site/images/full` yet are skipped. Run it after `build_site_assets.py`, then commit the output:

```bash
python3 build_verse_index.py
```
