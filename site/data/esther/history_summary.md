# ComfyUI job history summary

Source: 1 snapshot pattern(s) (71 jobs; 0 excluded as errors or cache replays).

Window: 2026-10-02 10:58 to 2026-10-02 11:47 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 9 | 8.3 | 9.9 | 8.0 | 10.0 | 1.3 | 1.03 | 9.9 (n=2) |
| FLUX.2 [klein] 4B + reference image | 33 | 16.0 | 17.2 | 15.7 | 17.4 | 9.1 | 1.03 | 17.2 (n=16) |
| Qwen-Image-Edit 2511 (edit) | 29 | 42.2 | 43.0 | 37.3 | 43.7 | 19.8 | 1.06 | 42.5 (n=19) |

**Total GPU time: 30.1 minutes** across 71 jobs.

## Gaps and sessions

Longest gap between jobs: **0.02 h** (1 min), after `halo_edit_00630_.png` and before `halo_klein_ref_01055_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 10-02 10:58 | 48.4 | 71 | 30.1 | 62% |

Total session wall clock: **48 min**; GPU busy **30 min** (62%).

## Cross-check with the image folder

2181 PNGs on disk; 71 matched to a history entry; 2110 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 1087 |
| Qwen-Image-Edit 2511 (edit) | 657 |
| FLUX.2 [klein] 4B, text only | 427 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |
