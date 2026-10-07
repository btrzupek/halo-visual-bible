# ComfyUI job history summary

Source: 1 snapshot pattern(s) (205 jobs; 0 excluded as errors or cache replays).

Window: 2026-10-07 04:11 to 2026-10-07 06:46 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 71 | 9.5 | 11.0 | 7.9 | 14.9 | 11.4 | 1.03 | 10.2 (n=28) |
| FLUX.2 [klein] 4B + reference image | 63 | 16.5 | 17.8 | 15.6 | 20.3 | 17.7 | 1.03 | 17.5 (n=22) |
| Qwen-Image-Edit 2511 (edit) | 71 | 42.8 | 47.8 | 37.2 | 61.6 | 51.1 | 1.06 | 43.3 (n=51) |

**Total GPU time: 80.2 minutes** across 205 jobs.

## Gaps and sessions

Longest gap between jobs: **0.40 h** (24 min), after `halo_klein_00474_.png` and before `halo_klein_00475_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 10-07 04:11 | 154.8 | 205 | 80.2 | 52% |

Total session wall clock: **155 min**; GPU busy **80 min** (52%).

## Cross-check with the image folder

2579 PNGs on disk; 205 matched to a history entry; 2374 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 1237 |
| Qwen-Image-Edit 2511 (edit) | 794 |
| FLUX.2 [klein] 4B, text only | 538 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |

## Book window

Images referenced by the viewer (scenes + cast portraits): 52; produced by jobs in history: 52.
From the first job whose image made it into the book (10-07 04:38) onward: **196 generations/edits**, **77.7 GPU-minutes**, 128 min wall clock (128 min excluding overnight/idle gaps > 30 min).
Generations per published image: **3.77**; by type: Qwen-Image-Edit 2511 (edit) 69, FLUX.2 [klein] 4B, text only 64, FLUX.2 [klein] 4B + reference image 63.
