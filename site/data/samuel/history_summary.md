# ComfyUI job history summary

Source: 1 snapshot pattern(s) (238 jobs; 0 excluded as errors or cache replays).

Window: 2026-09-29 08:05 to 2026-09-29 21:00 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 35 | 8.6 | 13.6 | 8.0 | 13.8 | 5.7 | 1.03 | 13.6 (n=8) |
| FLUX.2 [klein] 4B + reference image | 108 | 16.8 | 21.6 | 13.7 | 22.1 | 32.9 | 1.03 | 21.5 (n=38) |
| Qwen-Image-Edit 2511 (edit) | 95 | 55.7 | 61.1 | 36.2 | 86.6 | 80.2 | 1.06 | 56.9 (n=46) |

**Total GPU time: 118.8 minutes** across 238 jobs.

## Gaps and sessions

Longest gap between jobs: **9.27 h** (556 min), after `halo_klein_ref_00801_.png` and before `halo_edit_00414_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 09-29 08:05 | 208.2 | 223 | 110.1 | 53% |
| 2 | 09-29 20:49 | 11.4 | 15 | 8.7 | 76% |

Total session wall clock: **220 min**; GPU busy **119 min** (54%).

## Cross-check with the image folder

1578 PNGs on disk; 238 matched to a history entry; 1340 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 845 |
| Qwen-Image-Edit 2511 (edit) | 424 |
| FLUX.2 [klein] 4B, text only | 299 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |
