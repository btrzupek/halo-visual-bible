# ComfyUI job history summary

Source: 1 snapshot pattern(s) (189 jobs; 0 excluded as errors or cache replays).

Window: 2026-09-24 20:43 to 2026-09-25 06:10 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 15 | 11.9 | 23.2 | 8.0 | 24.9 | 3.5 | 1.03 | 23.2 (n=4) |
| FLUX.2 [klein] 4B + reference image | 145 | 21.7 | 30.4 | 15.5 | 34.6 | 53.6 | 1.03 | 30.7 (n=24) |
| Qwen-Image-Edit 2511 (edit) | 29 | 91.6 | 99.9 | 61.2 | 106.5 | 41.9 | 1.06 | 91.6 (n=29) |

**Total GPU time: 99.0 minutes** across 189 jobs.

## Gaps and sessions

Longest gap between jobs: **6.59 h** (395 min), after `halo_klein_ref_00253_.png` and before `halo_edit_00079_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 09-24 20:43 | 171.4 | 188 | 98.0 | 57% |
| 2 | 09-25 06:09 | 1.0 | 1 | 1.0 | 100% |

Total session wall clock: **172 min**; GPU busy **99 min** (57%).

## Cross-check with the image folder

379 PNGs on disk; 189 matched to a history entry; 190 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 253 |
| Qwen-Image-Edit 2511 (edit) | 79 |
| FLUX.2 [klein] 4B, text only | 37 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |

## Book window

Images referenced by the viewer (scenes + cast portraits): 75; produced by jobs in history: 75.
From the first job whose image made it into the book (09-24 20:47) onward: **183 generations/edits**, **95.9 GPU-minutes**, 563 min wall clock (168 min excluding overnight/idle gaps > 30 min).
Generations per published image: **2.44**; by type: FLUX.2 [klein] 4B + reference image 143, Qwen-Image-Edit 2511 (edit) 28, FLUX.2 [klein] 4B, text only 12.
