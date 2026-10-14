# ComfyUI job history summary

Source: 1 snapshot pattern(s) (365 jobs; 0 excluded as errors or cache replays).

Window: 2026-10-11 17:27 to 2026-10-14 15:25 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 31 | 10.2 | 35.7 | 8.0 | 37.1 | 11.2 | 1.03 | 10.1 (n=6) |
| FLUX.2 [klein] 4B + reference image | 103 | 52.8 | 59.2 | 15.7 | 68.0 | 88.3 | 3.69 | 54.0 (n=37) |
| Qwen-Image-Edit 2511 (edit) | 91 | 40.3 | 60.6 | 35.8 | 73.6 | 64.7 | 1.05 | 41.1 (n=43) |
| Other | 140 | 7.1 | 15.7 | 6.5 | 2909.3 | 175.8 | - | 607.0 (n=5) |

**Total GPU time: 340.0 minutes** across 365 jobs.

## Gaps and sessions

Longest gap between jobs: **61.77 h** (3706 min), after `halo_edit_00961_.png` and before `halo_klein_00651_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 10-11 17:27 | 253.1 | 221 | 174.2 | 69% |
| 2 | 10-14 11:26 | 151.8 | 15 | 149.5 | 98% |
| 3 | 10-14 14:36 | 48.7 | 129 | 16.3 | 33% |

Total session wall clock: **454 min**; GPU busy **340 min** (75%).

## Cross-check with the image folder

3218 PNGs on disk; 225 matched to a history entry; 2993 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 1450 |
| Qwen-Image-Edit 2511 (edit) | 981 |
| FLUX.2 [klein] 4B, text only | 650 |
| Other | 127 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |
