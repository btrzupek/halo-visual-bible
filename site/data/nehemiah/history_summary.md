# ComfyUI job history summary

Source: 1 snapshot pattern(s) (65 jobs; 0 excluded as errors or cache replays).

Window: 2026-10-02 05:50 to 2026-10-02 06:37 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 12 | 8.3 | 10.0 | 7.9 | 10.0 | 1.7 | 1.03 | 9.9 (n=4) |
| FLUX.2 [klein] 4B + reference image | 25 | 17.1 | 17.3 | 15.6 | 17.4 | 6.9 | 1.03 | 17.2 (n=13) |
| Qwen-Image-Edit 2511 (edit) | 28 | 42.0 | 42.8 | 37.0 | 46.1 | 19.0 | 1.06 | 42.3 (n=18) |

**Total GPU time: 27.7 minutes** across 65 jobs.

## Gaps and sessions

Longest gap between jobs: **0.02 h** (1 min), after `halo_edit_00617_.png` and before `halo_klein_ref_01041_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 10-02 05:50 | 46.6 | 65 | 27.7 | 59% |

Total session wall clock: **47 min**; GPU busy **28 min** (59%).

## Cross-check with the image folder

2110 PNGs on disk; 65 matched to a history entry; 2045 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 1054 |
| Qwen-Image-Edit 2511 (edit) | 628 |
| FLUX.2 [klein] 4B, text only | 418 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |
