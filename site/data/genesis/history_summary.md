# ComfyUI job history summary

Source: 1 snapshot pattern(s) (153 jobs; 0 excluded as errors or cache replays).

Window: 2026-09-28 23:48 to 2026-09-29 01:04 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 48 | 8.6 | 12.9 | 8.2 | 16.2 | 7.4 | 1.03 | 13.2 (n=6) |
| FLUX.2 [klein] 4B + reference image | 81 | 16.7 | 21.4 | 16.2 | 21.9 | 23.6 | 1.03 | 21.5 (n=13) |
| Qwen-Image-Edit 2511 (edit) | 24 | 56.5 | 57.5 | 38.0 | 62.0 | 21.6 | 1.06 | 56.7 (n=20) |

**Total GPU time: 52.6 minutes** across 153 jobs.

## Gaps and sessions

Longest gap between jobs: **0.01 h** (1 min), after `halo_klein_ref_00650_.png` and before `halo_klein_ref_00651_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 09-28 23:48 | 76.1 | 153 | 52.6 | 69% |

Total session wall clock: **76 min**; GPU busy **53 min** (69%).

## Cross-check with the image folder

1237 PNGs on disk; 153 matched to a history entry; 1084 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 697 |
| Qwen-Image-Edit 2511 (edit) | 289 |
| FLUX.2 [klein] 4B, text only | 241 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |

## Book window

Images referenced by the viewer (scenes + cast portraits): 89; produced by jobs in history: 89.
From the first job whose image made it into the book (09-28 23:54) onward: **138 generations/edits**, **49.3 GPU-minutes**, 71 min wall clock (71 min excluding overnight/idle gaps > 30 min).
Generations per published image: **1.55**; by type: FLUX.2 [klein] 4B + reference image 81, FLUX.2 [klein] 4B, text only 34, Qwen-Image-Edit 2511 (edit) 23.
