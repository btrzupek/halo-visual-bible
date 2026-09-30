# ComfyUI job history summary

Source: 1 snapshot pattern(s) (80 jobs; 0 excluded as errors or cache replays).

Window: 2026-09-29 21:08 to 2026-09-29 21:51 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 24 | 8.5 | 13.7 | 8.1 | 14.0 | 3.8 | 1.03 | 13.7 (n=5) |
| FLUX.2 [klein] 4B + reference image | 25 | 16.2 | 21.3 | 15.7 | 21.6 | 7.1 | 1.03 | 21.4 (n=4) |
| Qwen-Image-Edit 2511 (edit) | 31 | 39.2 | 56.2 | 37.1 | 57.2 | 22.8 | 1.06 | 55.7 (n=10) |

**Total GPU time: 33.7 minutes** across 80 jobs.

## Gaps and sessions

Longest gap between jobs: **0.02 h** (1 min), after `halo_edit_00442_.png` and before `halo_klein_00313_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 09-29 21:08 | 42.6 | 80 | 33.7 | 79% |

Total session wall clock: **43 min**; GPU busy **34 min** (79%).

## Cross-check with the image folder

1658 PNGs on disk; 80 matched to a history entry; 1578 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 870 |
| Qwen-Image-Edit 2511 (edit) | 455 |
| FLUX.2 [klein] 4B, text only | 323 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |
