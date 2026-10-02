# ComfyUI job history summary

Source: 1 snapshot pattern(s) (68 jobs; 0 excluded as errors or cache replays).

Window: 2026-10-01 17:12 to 2026-10-01 18:47 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 10 | 9.9 | 10.3 | 8.0 | 10.4 | 1.6 | 1.03 | 10.1 (n=5) |
| FLUX.2 [klein] 4B + reference image | 28 | 16.0 | 17.4 | 15.4 | 17.5 | 7.7 | 1.03 | 17.3 (n=13) |
| Qwen-Image-Edit 2511 (edit) | 30 | 41.9 | 43.9 | 36.0 | 48.4 | 20.4 | 1.06 | 42.8 (n=18) |

**Total GPU time: 29.6 minutes** across 68 jobs.

## Gaps and sessions

Longest gap between jobs: **0.77 h** (46 min), after `halo_edit_00572_.png` and before `halo_klein_00401_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 10-01 17:12 | 2.6 | 5 | 1.9 | 72% |
| 2 | 10-01 18:01 | 45.5 | 63 | 27.7 | 61% |

Total session wall clock: **48 min**; GPU busy **30 min** (62%).

## Cross-check with the image folder

2045 PNGs on disk; 68 matched to a history entry; 1977 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 1029 |
| Qwen-Image-Edit 2511 (edit) | 600 |
| FLUX.2 [klein] 4B, text only | 406 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |
