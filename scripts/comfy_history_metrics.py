#!/usr/bin/env python3
"""
comfy_history_metrics.py — turn ComfyUI's /history into per-job metrics.

For every prompt in ComfyUI's history it records: prompt_id, start/end timestamps,
execution time (execution_start -> execution_success status messages), job type,
diffusion model, resolution, steps, whether a reference image was used, whether it was an
edit, whether the model had to be (re)loaded (previous job used a different model), and the
output filename. Output resolution is read from the PNG header when the image exists
locally, else from the latent node.

Writes:
  <out>/comfy_history.csv
  <out>/history_summary.md   (count / median / p90 / min / max / GPU-minutes per job type,
                              longest idle gap, sessions, cross-check against the image folder)

Usage:
  python3 comfy_history_metrics.py --url http://127.0.0.1:8188 \
      --images ~/halo-images --book ~/halo-images/visual-bible/data --out ./metrics

Stdlib only. ComfyUI keeps history in memory, so it only covers jobs since ComfyUI last
started; the image-folder cross-check shows what is missing. Pass --history with saved
snapshots (curl .../history > history-<time>.json) to include jobs from before a restart,
and --url '' to use the snapshots alone.
"""
import argparse, csv, datetime as dt, glob, json, os, re, statistics, struct, urllib.request

JOB_TYPES = {  # filename prefix -> job type (SaveImage filename_prefix used by the MCP server)
    "halo_klein_ref": "klein_ref", "halo_klein": "klein", "halo_edit": "qwen_edit",
    "halo_qwen_ref": "qwen_ref", "halo_qwen": "qwen_image", "halo_zimage": "zimage", "claude": "zimage",
}
LABELS = {
    "klein": "FLUX.2 [klein] 4B, text only", "klein_ref": "FLUX.2 [klein] 4B + reference image",
    "qwen_edit": "Qwen-Image-Edit 2511 (edit)", "qwen_image": "Qwen-Image 2512",
    "qwen_ref": "Qwen-Image-Edit 2511 as reference generator", "zimage": "Z-Image Turbo",
    "lora_training": "LoRA training (TrainLoraNode)", "benchmark": "Benchmark runs (halo_benchmark.py)", "other": "Other",
}


def fetch_history(url: str, max_items: int) -> dict:
    with urllib.request.urlopen(f"{url.rstrip('/')}/history?max_items={max_items}", timeout=120) as r:
        return json.loads(r.read())


def png_size(path: str) -> tuple[int, int] | None:
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
    except OSError:
        pass
    return None


def classify(graph: dict, filename: str) -> str:
    types = {n.get("class_type") for n in graph.values()}
    if "TrainLoraNode" in types:
        return "lora_training"
    for prefix, jt in sorted(JOB_TYPES.items(), key=lambda kv: -len(kv[0])):
        if filename.startswith(prefix + "_"):
            return jt
    if "TextEncodeQwenImageEditPlus" in types:
        return "qwen_edit"
    if "ReferenceLatent" in types:
        return "klein_ref"
    return "other"


def job_row(pid: str, h: dict, images_dir: str) -> dict | None:
    msgs = {m[0]: m[1] for m in h.get("status", {}).get("messages", [])}
    start = msgs.get("execution_start", {}).get("timestamp")
    end = (msgs.get("execution_success") or msgs.get("execution_error") or msgs.get("execution_interrupted") or {}).get("timestamp")
    if not start or not end:
        return None
    graph = h["prompt"][2]
    outs = [i for node in h.get("outputs", {}).values() for i in node.get("images", []) if i.get("type") == "output"]
    fname = outs[0]["filename"] if outs else ""
    bench = bool(outs) and outs[0].get("subfolder", "").startswith("bench")  # halo_benchmark.py saves to bench/
    by_type = {}
    for n in graph.values():
        by_type.setdefault(n.get("class_type"), []).append(n.get("inputs", {}))
    unet = next((i.get("unet_name") for i in by_type.get("UNETLoader", [])), "") or \
        next((i.get("ckpt_name") for i in by_type.get("CheckpointLoaderSimple", [])), "")
    loras = [i.get("lora_name") for i in by_type.get("LoraLoaderModelOnly", [])]
    steps = next((i.get("steps") for t in ("KSampler", "Flux2Scheduler", "TrainLoraNode") for i in by_type.get(t, [])
                  if isinstance(i.get("steps"), int)), "")
    latent = next((i for t in ("EmptyFlux2LatentImage", "EmptySD3LatentImage", "EmptyLatentImage") for i in by_type.get(t, [])), {})
    size = png_size(os.path.join(images_dir, fname)) if fname else None
    w, h_px = size if size else (latent.get("width", ""), latent.get("height", ""))
    cached = len(msgs.get("execution_cached", {}).get("nodes", []))
    replay = cached >= len(graph) or (end - start) < 500  # every node served from cache: not a real generation
    return {
        "prompt_id": pid, "job_type": "benchmark" if bench else classify(graph, fname), "status": h["status"].get("status_str"),
        "start_utc": dt.datetime.fromtimestamp(start / 1000, dt.timezone.utc).isoformat(timespec="milliseconds"),
        "end_utc": dt.datetime.fromtimestamp(end / 1000, dt.timezone.utc).isoformat(timespec="milliseconds"),
        "exec_seconds": round((end - start) / 1000, 2), "model": unet, "loras": ";".join(l for l in loras if l),
        "width": w, "height": h_px, "megapixels": round(w * h_px / 1e6, 2) if isinstance(w, int) and isinstance(h_px, int) else "",
        "steps": steps, "reference_image": bool(by_type.get("ReferenceLatent")) or "LoadImage" in by_type and "TextEncodeQwenImageEditPlus" not in by_type,
        "edit": "TextEncodeQwenImageEditPlus" in by_type and "VAEEncode" in by_type and not by_type.get("EmptySD3LatentImage"),
        "cached_nodes": cached, "cache_replay": replay, "output_file": fname, "_start": start, "_end": end,
    }


def pct(values: list[float], p: float) -> float:
    s = sorted(values)
    if not s:
        return float("nan")
    k = (len(s) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8188", help="ComfyUI base URL")
    ap.add_argument("--images", default="~/halo-images", help="local folder with the generated PNGs")
    ap.add_argument("--book", default="", help="optional: viewer data/ folder, to flag images used in the book")
    ap.add_argument("--out", default=".", help="output folder")
    ap.add_argument("--history", action="append", default=[], help="saved /history snapshot file(s) or glob (repeatable)")
    ap.add_argument("--max-items", type=int, default=2000)
    ap.add_argument("--session-gap-min", type=float, default=30, help="idle gap that splits sessions")
    a = ap.parse_args()
    images = os.path.expanduser(a.images)
    os.makedirs(os.path.expanduser(a.out), exist_ok=True)
    out = os.path.expanduser(a.out)

    hist = {}
    for pat in a.history:
        for f in sorted(glob.glob(os.path.expanduser(pat))):
            hist.update(json.load(open(f)))
    if a.url:
        hist.update(fetch_history(a.url, a.max_items))
    rows = [r for pid, h in hist.items() if (r := job_row(pid, h, images))]
    rows.sort(key=lambda r: r["_start"])
    prev_model = None
    for r in rows:  # model_swap: this job's diffusion model differs from the previous real job's
        if r["cache_replay"]:
            r["model_swap"] = False
            continue
        r["model_swap"] = prev_model is not None and r["model"] != prev_model
        prev_model = r["model"] or prev_model

    book = set()
    if a.book:
        bdir = os.path.expanduser(a.book)  # data/*.js plus the viewer's index.html one level up (cast portraits)
        for f in glob.glob(os.path.join(bdir, "*.js")) + glob.glob(os.path.join(bdir, "..", "index.html")):
            book |= set(re.findall(r'([A-Za-z0-9_]+_\d{5}_\.png)', open(f).read()))
    for r in rows:
        r["in_book"] = r["output_file"] in book if book else ""

    fields = ["prompt_id", "job_type", "status", "start_utc", "end_utc", "exec_seconds", "model", "loras", "width", "height",
              "megapixels", "steps", "reference_image", "edit", "model_swap", "cached_nodes", "cache_replay", "output_file", "in_book"]
    with open(os.path.join(out, "comfy_history.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # ---- summary
    ok = [r for r in rows if r["status"] == "success" and not r["cache_replay"]]
    lines = ["# ComfyUI job history summary", "",
             f"Source: {f'`{a.url}/history`' if a.url else ''}{' + ' if a.url and a.history else ''}"
             f"{f'{len(a.history)} snapshot pattern(s)' if a.history else ''} ({len(rows)} jobs; {len(rows) - len(ok)} excluded as errors or cache replays).", ""]
    if rows:
        t0 = dt.datetime.fromtimestamp(rows[0]["_start"] / 1000)
        t1 = dt.datetime.fromtimestamp(rows[-1]["_end"] / 1000)
        lines += [f"Window: {t0:%Y-%m-%d %H:%M} to {t1:%Y-%m-%d %H:%M} (local time of the machine running this script).", ""]
    lines += ["## Execution time per job type (seconds, ComfyUI execution_start to execution_success)", "",
              "| Job type | Count | Median | p90 | Min | Max | GPU-minutes | Median MP | Right after a model swap (median) |",
              "|---|---|---|---|---|---|---|---|---|"]
    total_gpu = 0.0
    for jt in LABELS:
        xs = [r for r in ok if r["job_type"] == jt]
        if not xs:
            continue
        secs = [r["exec_seconds"] for r in xs]
        swap = [r["exec_seconds"] for r in xs if r["model_swap"]]
        mps = [r["megapixels"] for r in xs if isinstance(r["megapixels"], float)]
        total_gpu += sum(secs)
        lines.append(f"| {LABELS[jt]} | {len(xs)} | {statistics.median(secs):.1f} | {pct(secs, .9):.1f} | {min(secs):.1f} | "
                     f"{max(secs):.1f} | {sum(secs) / 60:.1f} | {statistics.median(mps) if mps else '-'} | "
                     f"{f'{statistics.median(swap):.1f} (n={len(swap)})' if swap else '-'} |")
    lines += ["", f"**Total GPU time: {total_gpu / 60:.1f} minutes** across {len(ok)} jobs.", ""]

    gaps = [((b["_start"] - a_["_end"]) / 1000, a_, b) for a_, b in zip(rows, rows[1:])]
    if gaps:
        g, before, after = max(gaps, key=lambda x: x[0])
        lines += ["## Gaps and sessions", "",
                  f"Longest gap between jobs: **{g / 3600:.2f} h** ({g / 60:.0f} min), after `{before['output_file'] or before['job_type']}` "
                  f"and before `{after['output_file'] or after['job_type']}`.", ""]
        sessions, cur = [], [rows[0]]
        for gap, _, b in gaps:
            if gap > a.session_gap_min * 60:
                sessions.append(cur)
                cur = []
            cur.append(b)
        sessions.append(cur)
        lines += [f"Sessions (split at idle gaps > {a.session_gap_min:.0f} min):", "",
                  "| # | Start | Wall clock (min) | Jobs | GPU busy (min) | GPU busy % |", "|---|---|---|---|---|---|"]
        wall_total = busy_total = 0.0
        for i, s in enumerate(sessions, 1):
            wall = (s[-1]["_end"] - s[0]["_start"]) / 60000
            busy = sum(r["exec_seconds"] for r in s) / 60
            wall_total += wall
            busy_total += busy
            lines.append(f"| {i} | {dt.datetime.fromtimestamp(s[0]['_start'] / 1000):%m-%d %H:%M} | {wall:.1f} | {len(s)} | "
                         f"{busy:.1f} | {100 * busy / wall if wall else 0:.0f}% |")
        lines += ["", f"Total session wall clock: **{wall_total:.0f} min**; GPU busy **{busy_total:.0f} min** "
                      f"({100 * busy_total / wall_total if wall_total else 0:.0f}%).", ""]

    # ---- cross-check with the image folder
    on_disk = sorted(os.path.basename(p) for p in glob.glob(os.path.join(images, "*.png")))
    in_hist = {r["output_file"] for r in rows if r["output_file"]}
    missing = [f for f in on_disk if f not in in_hist]
    counts = {}
    for f in on_disk:
        jt = classify({}, f)
        counts[jt] = counts.get(jt, 0) + 1
    lines += ["## Cross-check with the image folder", "",
              f"{len(on_disk)} PNGs on disk; {len(on_disk) - len(missing)} matched to a history entry; "
              f"{len(missing)} not in history" + (f" ({', '.join(missing[:12])}{' …' if len(missing) > 12 else ''})" if missing else "") + ".", "",
              "| Job type (by filename) | Files on disk |", "|---|---|"]
    lines += [f"| {LABELS.get(k, k)} | {v} |" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]
    if book:
        used = [r for r in ok if r["in_book"]]
        first = min(r["_start"] for r in used) if used else None
        win = [r for r in ok if first and r["_start"] >= first and r["job_type"] not in ("lora_training", "benchmark")]
        wall = (win[-1]["_end"] - win[0]["_start"]) / 60000 if win else 0
        idle = sum(max(0, (b["_start"] - x["_end"]) / 60000) for x, b in zip(win, win[1:]) if b["_start"] - x["_end"] > a.session_gap_min * 60000)
        lines += ["", "## Book window", "",
                  f"Images referenced by the viewer (scenes + cast portraits): {len(book)}; produced by jobs in history: {len(used)}.",
                  f"From the first job whose image made it into the book "
                  f"({dt.datetime.fromtimestamp(first / 1000):%m-%d %H:%M}) onward: **{len(win)} generations/edits**, "
                  f"**{sum(r['exec_seconds'] for r in win) / 60:.1f} GPU-minutes**, "
                  f"{wall:.0f} min wall clock ({wall - idle:.0f} min excluding overnight/idle gaps > {a.session_gap_min:.0f} min).",
                  f"Generations per published image: **{len(win) / len(book):.2f}**; "
                  f"by type: " + ", ".join(f"{LABELS[t]} {n}" for t, n in sorted(
                      {t: sum(1 for r in win if r['job_type'] == t) for t in LABELS}.items(), key=lambda kv: -kv[1]) if n) + "."]
    with open(os.path.join(out, "history_summary.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {len(rows)} rows to {out}/comfy_history.csv and {out}/history_summary.md")


if __name__ == "__main__":
    main()
