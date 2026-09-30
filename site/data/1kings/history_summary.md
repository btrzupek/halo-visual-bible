# ComfyUI job history summary

Source: 1 snapshot pattern(s) (96 jobs; 0 excluded as errors or cache replays).

Window: 2026-09-29 18:30 to 2026-09-29 19:24 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 23 | 8.5 | 11.8 | 8.1 | 13.5 | 3.5 | 1.03 | 13.5 (n=3) |
| FLUX.2 [klein] 4B + reference image | 40 | 16.8 | 21.9 | 14.2 | 22.0 | 11.9 | 1.03 | 21.7 (n=10) |
| Qwen-Image-Edit 2511 (edit) | 33 | 40.5 | 57.3 | 38.7 | 57.8 | 25.5 | 1.06 | 56.8 (n=13) |

**Total GPU time: 40.9 minutes** across 96 jobs.

## Gaps and sessions

Longest gap between jobs: **0.02 h** (1 min), after `halo_klein_ref_00822_.png` and before `halo_klein_ref_00823_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 09-29 18:30 | 54.0 | 96 | 40.9 | 76% |

Total session wall clock: **54 min**; GPU busy **41 min** (76%).

## Cross-check with the image folder

1563 PNGs on disk; 96 matched to a history entry; 1467 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 841 |
| Qwen-Image-Edit 2511 (edit) | 413 |
| FLUX.2 [klein] 4B, text only | 299 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |
