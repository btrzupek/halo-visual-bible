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
