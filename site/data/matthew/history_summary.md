# ComfyUI job history summary

Source: 1 snapshot pattern(s) (217 jobs; 0 excluded as errors or cache replays).

Window: 2026-09-25 21:58 to 2026-09-26 00:34 (local time of the machine running this script).

## Execution time per job type (seconds, ComfyUI execution_start to execution_success)

| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |
|---|---|---|---|---|---|---|---|---|
| FLUX.2 [klein] 4B, text only | 60 | 8.8 | 13.9 | 7.9 | 16.6 | 10.7 | 1.03 | 13.7 (n=25) |
| FLUX.2 [klein] 4B + reference image | 103 | 16.7 | 21.7 | 15.9 | 22.3 | 30.5 | 1.03 | 21.7 (n=23) |
| Qwen-Image-Edit 2511 (edit) | 54 | 57.0 | 57.8 | 38.7 | 63.1 | 49.7 | 1.06 | 57.1 (n=48) |

**Total GPU time: 90.9 minutes** across 217 jobs.

## Gaps and sessions

Longest gap between jobs: **0.03 h** (2 min), after `halo_klein_ref_00493_.png` and before `halo_edit_00190_.png`.

Sessions (split at idle gaps > 30 min):

| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |
|---|---|---|---|---|---|
| 1 | 09-25 21:58 | 156.4 | 217 | 90.9 | 58% |

Total session wall clock: **156 min**; GPU busy **91 min** (58%).

## Cross-check with the image folder

850 PNGs on disk; 217 matched to a history entry; 633 not in history (claude_00002_.png, claude_00003_.png, claude_00004_.png, claude_00005_.png, claude_00006_.png, halo_edit_00001_.png, halo_edit_00002_.png, halo_edit_00003_.png, halo_edit_00004_.png, halo_edit_00005_.png, halo_edit_00006_.png, halo_edit_00007_.png …).

| Job type (by filename) | Files on disk |
|---|---|
| FLUX.2 [klein] 4B + reference image | 494 |
| Qwen-Image-Edit 2511 (edit) | 193 |
| FLUX.2 [klein] 4B, text only | 153 |
| Z-Image Turbo | 8 |
| Qwen-Image 2512 | 1 |
| Qwen-Image-Edit 2511 as reference generator | 1 |

## Book window

Images referenced by the viewer (scenes + cast portraits): 111; produced by jobs in history: 111.
From the first job whose image made it into the book (09-25 21:59) onward: **214 generations/edits**, **90.3 GPU-minutes**, 155 min wall clock (155 min excluding overnight/idle gaps > 30 min).
Generations per published image: **1.93**; by type: FLUX.2 [klein] 4B + reference image 103, FLUX.2 [klein] 4B, text only 57, Qwen-Image-Edit 2511 (edit) 54.
