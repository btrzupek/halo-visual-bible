# ComfyUI job history summary

Source: 1 snapshot pattern(s) (31 jobs; 0 excluded as errors or cache replays).

Window: 2026-10-02 12:35 to 2026-10-02 12:55 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 3 | 8.3 | 9.5 | 8.2 | 9.8 | 0.4 | 1.03 | - |
| FLUX.2 [klein] 4B + reference image | 18 | 15.9 | 17.3 | 15.6 | 17.5 | 4.9 | 1.03 | 17.3 (n=7) |
| Qwen-Image-Edit 2511 (edit) | 10 | 42.3 | 43.1 | 37.8 | 43.2 | 6.9 | 1.06 | 42.5 (n=8) |

**Total GPU time: 12.3 minutes** across 31 jobs.

## Gaps and sessions

Longest gap between jobs: **0.02 h** (1 min), after `halo_edit_00658_.png` and before `halo_klein_ref_01088_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 10-02 12:35 | 20.4 | 31 | 12.3 | 60% |

Total session wall clock: **20 min**; GPU busy **12 min** (60%).

## Cross-check with the image folder

2212 PNGs on disk; 31 matched to a history entry; 2181 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 1105 |
| Qwen-Image-Edit 2511 (edit) | 667 |
| FLUX.2 [klein] 4B, text only | 430 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |
