# ComfyUI job history summary

Source: 1 snapshot pattern(s) (317 jobs; 0 excluded as errors or cache replays).

Window: 2026-10-01 08:59 to 2026-10-01 13:22 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 73 | 8.6 | 10.1 | 8.1 | 11.5 | 11.1 | 1.03 | 10.0 (n=29) |
| FLUX.2 [klein] 4B + reference image | 131 | 16.6 | 17.9 | 15.7 | 19.4 | 36.9 | 1.03 | 17.7 (n=49) |
| Qwen-Image-Edit 2511 (edit) | 113 | 42.6 | 43.9 | 38.5 | 70.4 | 80.7 | 1.06 | 42.9 (n=79) |

**Total GPU time: 128.6 minutes** across 317 jobs.

## Gaps and sessions

Longest gap between jobs: **0.55 h** (33 min), after `halo_klein_00327_.png` and before `halo_klein_00328_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 10-01 08:59 | 3.3 | 7 | 2.0 | 62% |
| 2 | 10-01 09:35 | 226.8 | 310 | 126.6 | 56% |

Total session wall clock: **230 min**; GPU busy **129 min** (56%).

## Cross-check with the image folder

1977 PNGs on disk; 317 matched to a history entry; 1660 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 1001 |
| Qwen-Image-Edit 2511 (edit) | 570 |
| FLUX.2 [klein] 4B, text only | 396 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |
