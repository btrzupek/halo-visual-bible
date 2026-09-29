# ComfyUI job history summary

Source: 1 snapshot pattern(s) (223 jobs; 0 excluded as errors or cache replays).

Window: 2026-09-29 08:05 to 2026-09-29 11:33 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 35 | 8.6 | 13.6 | 8.0 | 13.8 | 5.7 | 1.03 | 13.6 (n=8) |
| FLUX.2 [klein] 4B + reference image | 104 | 16.8 | 21.7 | 14.1 | 22.1 | 31.8 | 1.03 | 21.6 (n=37) |
| Qwen-Image-Edit 2511 (edit) | 84 | 56.4 | 64.2 | 38.4 | 86.6 | 72.6 | 1.06 | 57.0 (n=45) |

**Total GPU time: 110.1 minutes** across 223 jobs.

## Gaps and sessions

Longest gap between jobs: **0.42 h** (25 min), after `halo_edit_00375_.png` and before `halo_klein_ref_00798_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 09-29 08:05 | 208.2 | 223 | 110.1 | 53% |

Total session wall clock: **208 min**; GPU busy **110 min** (53%).

## Cross-check with the image folder

1467 PNGs on disk; 223 matched to a history entry; 1244 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 801 |
| Qwen-Image-Edit 2511 (edit) | 380 |
| FLUX.2 [klein] 4B, text only | 276 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |
