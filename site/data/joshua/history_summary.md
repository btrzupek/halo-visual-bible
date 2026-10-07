# ComfyUI job history summary

Source: 1 snapshot pattern(s) (162 jobs; 0 excluded as errors or cache replays).

Window: 2026-10-06 18:20 to 2026-10-06 20:25 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 37 | 9.7 | 11.8 | 8.1 | 13.7 | 6.1 | 1.03 | 10.6 (n=12) |
| FLUX.2 [klein] 4B + reference image | 69 | 17.6 | 20.7 | 15.8 | 25.8 | 20.5 | 1.03 | 17.9 (n=27) |
| Qwen-Image-Edit 2511 (edit) | 56 | 43.1 | 51.1 | 37.8 | 58.4 | 41.5 | 1.06 | 43.9 (n=40) |

**Total GPU time: 68.1 minutes** across 162 jobs.

## Gaps and sessions

Longest gap between jobs: **0.23 h** (14 min), after `halo_klein_00466_.png` and before `halo_klein_00467_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 10-06 18:20 | 125.8 | 162 | 68.1 | 54% |

Total session wall clock: **126 min**; GPU busy **68 min** (54%).

## Cross-check with the image folder

2374 PNGs on disk; 162 matched to a history entry; 2212 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 1174 |
| Qwen-Image-Edit 2511 (edit) | 723 |
| FLUX.2 [klein] 4B, text only | 467 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |

## Book window

Images referenced by the viewer (scenes + cast portraits): 47; produced by jobs in history: 47.
From the first job whose image made it into the book (10-06 18:33) onward: **151 generations/edits**, **64.8 GPU-minutes**, 112 min wall clock (112 min excluding overnight/idle gaps > 30 min).
Generations per published image: **3.21**; by type: FLUX.2 [klein] 4B + reference image 66, Qwen-Image-Edit 2511 (edit) 54, FLUX.2 [klein] 4B, text only 31.
