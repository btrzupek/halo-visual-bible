# ComfyUI job history summary

Source: 1 snapshot pattern(s) (254 jobs; 0 excluded as errors or cache replays).

Window: 2026-09-25 06:34 to 2026-09-25 09:42 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 56 | 8.6 | 13.5 | 7.9 | 16.4 | 9.0 | 1.03 | 13.4 (n=12) |
| FLUX.2 [klein] 4B + reference image | 138 | 16.8 | 21.6 | 16.0 | 22.1 | 42.0 | 1.03 | 21.5 (n=47) |
| Qwen-Image-Edit 2511 (edit) | 60 | 57.0 | 57.8 | 38.5 | 59.2 | 56.8 | 1.06 | 57.1 (n=59) |

**Total GPU time: 107.8 minutes** across 254 jobs.

## Gaps and sessions

Longest gap between jobs: **0.02 h** (1 min), after `halo_edit_00089_.png` and before `halo_klein_ref_00278_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 09-25 06:34 | 188.0 | 254 | 107.8 | 57% |

Total session wall clock: **188 min**; GPU busy **108 min** (57%).

## Cross-check with the image folder

633 PNGs on disk; 254 matched to a history entry; 379 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 391 |
| Qwen-Image-Edit 2511 (edit) | 139 |
| FLUX.2 [klein] 4B, text only | 93 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |

## Book window

Images referenced by the viewer (scenes + cast portraits): 103; produced by jobs in history: 103.
From the first job whose image made it into the book (09-25 06:35) onward: **252 generations/edits**, **107.4 GPU-minutes**, 187 min wall clock (187 min excluding overnight/idle gaps > 30 min).
Generations per published image: **2.45**; by type: FLUX.2 [klein] 4B + reference image 138, Qwen-Image-Edit 2511 (edit) 60, FLUX.2 [klein] 4B, text only 54.
