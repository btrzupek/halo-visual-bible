# ComfyUI job history summary

Source: 1 snapshot pattern(s) (266 jobs; 0 excluded as errors or cache replays).

Window: 2026-10-10 16:28 to 2026-10-10 19:01 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 81 | 8.5 | 10.4 | 8.0 | 13.8 | 12.4 | 1.03 | 10.2 (n=24) |
| FLUX.2 [klein] 4B + reference image | 107 | 17.2 | 19.3 | 15.6 | 23.6 | 31.1 | 1.03 | 17.7 (n=40) |
| Qwen-Image-Edit 2511 (edit) | 78 | 43.2 | 48.0 | 37.3 | 57.7 | 56.7 | 1.06 | 43.2 (n=65) |

**Total GPU time: 100.2 minutes** across 266 jobs.

## Gaps and sessions

Longest gap between jobs: **0.05 h** (3 min), after `halo_klein_00618_.png` and before `halo_klein_00619_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 10-10 16:28 | 153.6 | 266 | 100.2 | 65% |

Total session wall clock: **154 min**; GPU busy **100 min** (65%).

## Cross-check with the image folder

2845 PNGs on disk; 266 matched to a history entry; 2579 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 1344 |
| Qwen-Image-Edit 2511 (edit) | 872 |
| FLUX.2 [klein] 4B, text only | 619 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |

## Book window

Images referenced by the viewer (scenes + cast portraits): 77; produced by jobs in history: 77.
From the first job whose image made it into the book (10-10 16:36) onward: **252 generations/edits**, **96.0 GPU-minutes**, 146 min wall clock (146 min excluding overnight/idle gaps > 30 min).
Generations per published image: **3.27**; by type: FLUX.2 [klein] 4B + reference image 104, Qwen-Image-Edit 2511 (edit) 75, FLUX.2 [klein] 4B, text only 73.
