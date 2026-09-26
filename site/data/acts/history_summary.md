# ComfyUI job history summary

Source: 1 snapshot pattern(s) (234 jobs; 0 excluded as errors or cache replays).

Window: 2026-09-26 05:53 to 2026-09-26 08:54 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 40 | 8.7 | 13.9 | 8.1 | 14.2 | 7.0 | 1.03 | 13.7 (n=15) |
| FLUX.2 [klein] 4B + reference image | 122 | 16.8 | 22.0 | 15.8 | 22.4 | 38.3 | 1.03 | 21.8 (n=53) |
| Qwen-Image-Edit 2511 (edit) | 72 | 57.0 | 58.0 | 38.7 | 86.8 | 69.4 | 1.06 | 57.1 (n=69) |

**Total GPU time: 114.7 minutes** across 234 jobs.

## Gaps and sessions

Longest gap between jobs: **0.07 h** (4 min), after `halo_edit_00238_.png` and before `halo_klein_ref_00567_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 09-26 05:53 | 181.5 | 234 | 114.7 | 63% |

Total session wall clock: **182 min**; GPU busy **115 min** (63%).

## Cross-check with the image folder

1084 PNGs on disk; 234 matched to a history entry; 850 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 616 |
| Qwen-Image-Edit 2511 (edit) | 265 |
| FLUX.2 [klein] 4B, text only | 193 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |

## Book window

Images referenced by the viewer (scenes + cast portraits): 98; produced by jobs in history: 98.
From the first job whose image made it into the book (09-26 05:58) onward: **221 generations/edits**, **110.9 GPU-minutes**, 176 min wall clock (176 min excluding overnight/idle gaps > 30 min).
Generations per published image: **2.26**; by type: FLUX.2 [klein] 4B + reference image 120, Qwen-Image-Edit 2511 (edit) 70, FLUX.2 [klein] 4B, text only 31.
