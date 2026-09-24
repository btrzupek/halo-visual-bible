#!/usr/bin/env python3
"""
halo_benchmark.py — controlled ComfyUI benchmark with power/thermal telemetry.

Runs the same ComfyUI API-format workflows the MCP server uses (../workflows) with fixed
seeds, and — if --ssh-host is given — streams 1 Hz telemetry from the ComfyUI machine over
SSH (amdgpu sysfs + `amd-smi metric --power --json`; no root needed). For each run it records
wall time, ComfyUI execution time, peak/average socket power, energy, peak GPU memory (GTT)
and peak temperature, then summarizes per job type.

Default plan (the Visual Bible blog benchmark):
  idle baseline 20 s (models unloaded)
  FLUX.2 klein text-only 1344x768, 4 steps : 1 cold (after unloading models) + 5 warm
  FLUX.2 klein + reference image, 1344x768 : 5 warm
  Qwen-Image-Edit on an existing image     : 1 cold (right after klein = model swap) + 3 warm
  Qwen-Image 1328x1328, 4 steps            : 1 cold + 2 warm

Usage:
  python3 halo_benchmark.py --url http://127.0.0.1:8188 --ssh-host <halo-host> \
      --reference ~/halo-images/<portrait>.png --edit-image ~/halo-images/<scene>.png \
      --images-out ~/halo-images/benchmark --results ./results

Outputs: <results>/benchmark.csv (one row per run), benchmark_samples.csv (raw telemetry),
benchmark_summary.json (per-job-type aggregates). Stdlib only.
"""
import argparse, csv, json, os, statistics, subprocess, threading, time, urllib.parse, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))

SAMPLER = r'''
import glob, json, os, subprocess, time
card = "/sys/class/drm/card0/device"
hw = glob.glob(card + "/hwmon/hwmon*")[0]
k10 = next((h for h in glob.glob("/sys/class/hwmon/hwmon*") if open(h + "/name").read().strip() == "k10temp"), None)
rd = lambda p: open(p).read().strip()
while True:
    t0 = time.time()
    s = {"t": t0}
    try:
        s.update(ppt_w=int(rd(hw + "/power1_average")) / 1e6, edge_c=int(rd(hw + "/temp1_input")) / 1e3,
                 busy_pct=int(rd(card + "/gpu_busy_percent")), gtt_gb=int(rd(card + "/mem_info_gtt_used")) / 1e9,
                 sclk_mhz=int(rd(hw + "/freq1_input")) / 1e6)
        if k10:
            s["tctl_c"] = int(rd(k10 + "/temp1_input")) / 1e3
        p = json.loads(subprocess.run(["amd-smi", "metric", "--power", "--json"], capture_output=True, text=True,
                                      timeout=2).stdout)
        p = (p["gpu_data"][0] if isinstance(p, dict) else p[0])["power"]
        s.update(gfx_w=p["apu_average_gfx_power"]["value"], cores_w=p["apu_average_all_core_power"]["value"],
                 sys_w=p["apu_average_sys_power"]["value"])
    except Exception as e:
        s["err"] = str(e)[:80]
    print(json.dumps(s), flush=True)
    time.sleep(max(0.0, 1.0 - (time.time() - t0)))
'''

PROMPTS = [
    "A fishing boat on the Sea of Galilee at dawn, mist on the water, first-century fishermen hauling nets, cinematic",
    "A crowded first-century Jerusalem street market, stone arches, clay pots, afternoon light, cinematic",
    "An olive grove at night lit by torches, gnarled trees, a small group of men in robes, cinematic",
    "A stone courtyard with a charcoal fire at night, servants warming their hands, cinematic",
    "A dusty road through Samaria at noon, a stone well, a woman with a water jar, cinematic",
    "The Jordan river at golden hour, reeds, a crowd gathered on the bank, cinematic",
]
REF_PROMPTS = [
    "The man from the reference image teaching a crowd on a hillside by the Sea of Galilee, 1st century, cinematic",
    "The man from the reference image walking along a dusty road with his disciples at sunset, cinematic",
    "The man from the reference image seated at a long low table sharing bread, oil lamps, cinematic",
    "The man from the reference image standing in a stone synagogue reading from a scroll, cinematic",
    "The man from the reference image in a small fishing boat on a calm lake at dawn, cinematic",
]
EDITS = [
    "Make the lighting warm golden-hour sunlight",
    "Add a flock of birds in the sky",
    "Make it an overcast, moody day with soft light",
    "Add gentle morning mist near the ground",
]
QWEN_PROMPTS = [
    "An illuminated manuscript page with the words \"In the beginning was the Word\" in gold uncial lettering, vellum texture",
    "A carved stone lintel reading \"THE GOSPEL OF JOHN\" above an ancient doorway, afternoon sun",
    "A weathered wooden sign reading \"CANA\" at the edge of a village road, olive trees behind",
]


class Comfy:
    def __init__(self, url: str):
        self.url = url.rstrip("/")

    def get(self, path: str) -> bytes:
        with urllib.request.urlopen(self.url + path, timeout=60) as r:
            return r.read()

    def post(self, path: str, body: dict) -> dict:
        req = urllib.request.Request(self.url + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
        return json.loads(raw) if raw else {}

    def upload(self, path: str) -> str:
        name, boundary = f"bench_{uuid.uuid4().hex[:8]}_{os.path.basename(path)}", uuid.uuid4().hex
        data = open(path, "rb").read()
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{name}\"\r\nContent-Type: image/png\r\n\r\n").encode() \
            + data + f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(self.url + "/upload/image", data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())["name"]

    def free(self):
        self.post("/free", {"unload_models": True, "free_memory": True})

    def run(self, wf: dict, timeout=900) -> tuple[dict, float]:
        t0 = time.time()
        pid = self.post("/prompt", {"prompt": wf, "client_id": str(uuid.uuid4())})["prompt_id"]
        while time.time() - t0 < timeout:
            h = json.loads(self.get(f"/history/{pid}")).get(pid)
            if h and (h.get("outputs") or h.get("status", {}).get("status_str") == "error"):
                return h, time.time() - t0
            time.sleep(0.25)
        raise TimeoutError(pid)


def build(workflow_dir: str, name: str, p: dict, prefix: str) -> dict:
    text = open(os.path.join(workflow_dir, name)).read()
    for k in ("PROMPT", "NEGATIVE", "IMAGE"):
        text = text.replace("{{%s}}" % k, json.dumps(p.get(k.lower(), ""))[1:-1])
    for k in ("SEED", "WIDTH", "HEIGHT", "STEPS", "CFG"):
        text = text.replace('"{{%s}}"' % k, json.dumps(p.get(k.lower())))
    wf = json.loads(text)
    dead = {i for i, n in wf.items() if n["class_type"] == "LoadImage" and n["inputs"].get("image") == "{{IMAGE2}}"}
    for i in dead:
        del wf[i]
    for n in wf.values():
        for k in [k for k, v in n["inputs"].items() if isinstance(v, list) and v and v[0] in dead]:
            del n["inputs"][k]
        if n["class_type"] == "SaveImage":
            n["inputs"]["filename_prefix"] = prefix
    return wf


class Telemetry:
    def __init__(self, host: str | None):
        self.samples, self.proc = [], None
        if host:
            # the sampler goes over stdin: ssh joins argv into one remote shell string
            self.proc = subprocess.Popen(["ssh", "-o", "BatchMode=yes", host, "python3 -u -"],
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            self.proc.stdin.write(SAMPLER)
            self.proc.stdin.close()
            threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            try:
                s = json.loads(line)
                s["t_local"] = time.time()
                self.samples.append(s)
            except ValueError:
                pass

    def window(self, t0: float, t1: float) -> list[dict]:
        return [s for s in self.samples if t0 - 0.5 <= s["t_local"] <= t1 + 0.5 and "ppt_w" in s]

    def stop(self):
        if self.proc:
            self.proc.terminate()


def stats(samples: list[dict], seconds: float, idle_w: float | None) -> dict:
    if not samples:
        return {}
    ppt = [s["ppt_w"] for s in samples]
    avg = statistics.fmean(ppt)
    out = {"samples": len(samples), "avg_ppt_w": round(avg, 1), "peak_ppt_w": round(max(ppt), 1),
           "energy_wh": round(avg * seconds / 3600, 3), "peak_gtt_gb": round(max(s["gtt_gb"] for s in samples), 1),
           "peak_edge_c": round(max(s["edge_c"] for s in samples), 1), "avg_busy_pct": round(statistics.fmean(s["busy_pct"] for s in samples)),
           "peak_sclk_mhz": round(max(s["sclk_mhz"] for s in samples))}
    if any("tctl_c" in s for s in samples):
        out["peak_tctl_c"] = round(max(s.get("tctl_c", 0) for s in samples), 1)
    g = [s["gfx_w"] for s in samples if "gfx_w" in s]
    if g:
        out.update(avg_gfx_w=round(statistics.fmean(g), 1), peak_gfx_w=round(max(g), 1))
    sy = [s["sys_w"] for s in samples if "sys_w" in s]
    if sy:
        out.update(avg_sys_w=round(statistics.fmean(sy), 1), peak_sys_w=round(max(sy), 1))
    if idle_w is not None:
        out["energy_above_idle_wh"] = round(max(0.0, avg - idle_w) * seconds / 3600, 3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8188")
    ap.add_argument("--ssh-host", default="", help="ComfyUI machine for telemetry over SSH (omit to skip telemetry)")
    ap.add_argument("--workflows", default=os.path.join(HERE, "..", "workflows"))
    ap.add_argument("--reference", required=True, help="reference image for klein+reference runs")
    ap.add_argument("--edit-image", required=True, help="existing image for Qwen-Image-Edit runs")
    ap.add_argument("--images-out", default="./benchmark-images")
    ap.add_argument("--results", default="./results")
    ap.add_argument("--idle-seconds", type=int, default=20)
    a = ap.parse_args()
    for d in (a.images_out, a.results):
        os.makedirs(os.path.expanduser(d), exist_ok=True)
    c, tel = Comfy(a.url), Telemetry(a.ssh_host or None)
    ref, edit_src = c.upload(os.path.expanduser(a.reference)), c.upload(os.path.expanduser(a.edit_image))

    kl = {"width": 1344, "height": 768, "steps": 4, "cfg": 1.0, "negative": ""}
    plan = []  # (job_type, phase, workflow, params)
    plan += [("klein_text", "cold", "flux2-klein.json", {**kl, "prompt": PROMPTS[0], "seed": 1000})]
    plan += [("klein_text", "warm", "flux2-klein.json", {**kl, "prompt": PROMPTS[i], "seed": 1000 + i}) for i in range(1, 6)]
    plan += [("klein_ref", "warm", "flux2-klein-ref.json", {**kl, "prompt": REF_PROMPTS[i], "seed": 2000 + i, "image": ref}) for i in range(5)]
    plan += [("qwen_edit", "cold" if i == 0 else "warm", "qwen-image-edit.json",
              {"prompt": EDITS[i], "negative": "", "steps": 4, "cfg": 1.0, "seed": 3000 + i, "image": edit_src}) for i in range(4)]
    plan += [("qwen_image", "cold" if i == 0 else "warm", "qwen-image.json",
              {"prompt": QWEN_PROMPTS[i], "negative": "", "width": 1328, "height": 1328, "steps": 4, "cfg": 1.0, "seed": 4000 + i}) for i in range(3)]

    while True:  # never measure idle while someone else's job is running
        q = json.loads(c.get("/queue"))
        if not q["queue_running"] and not q["queue_pending"]:
            break
        print("waiting for ComfyUI queue to drain...", flush=True)
        time.sleep(3)
    print("unloading models; measuring idle baseline...", flush=True)
    c.free()
    time.sleep(3)
    t_idle = time.time()
    time.sleep(a.idle_seconds if tel.proc else 0)
    idle = stats(tel.window(t_idle, time.time()), a.idle_seconds, None)
    idle_w = idle.get("avg_ppt_w")
    print(f"idle: {idle}", flush=True)

    rows = []
    for n, (jt, phase, wfname, p) in enumerate(plan, 1):
        if jt == "klein_text" and phase == "cold":
            c.free()
            time.sleep(3)
        wf = build(a.workflows, wfname, p, f"bench/{jt}_{phase}")
        t0 = time.time()
        h, wall = c.run(wf)
        t1 = time.time()
        msgs = {m[0]: m[1] for m in h["status"]["messages"]}
        exec_s = (msgs.get("execution_success", msgs.get("execution_error", {})).get("timestamp", 0) - msgs["execution_start"]["timestamp"]) / 1000
        img = [i for node in h["outputs"].values() for i in node.get("images", []) if i.get("type") == "output"]
        fname = ""
        if img:
            q = urllib.parse.urlencode({"filename": img[0]["filename"], "subfolder": img[0].get("subfolder", ""), "type": "output"})
            fname = f"{n:02d}_{jt}_{phase}_seed{p['seed']}.png"
            with open(os.path.join(os.path.expanduser(a.images_out), fname), "wb") as f:
                f.write(c.get(f"/view?{q}"))
        time.sleep(1.2)  # let the last telemetry sample land
        st = stats(tel.window(t0, t1), wall, idle_w)
        row = {"run": n, "job_type": jt, "phase": phase, "workflow": wfname, "seed": p["seed"],
               "width": p.get("width", ""), "height": p.get("height", ""), "steps": p["steps"],
               "wall_s": round(wall, 2), "comfy_exec_s": round(exec_s, 2), "status": h["status"].get("status_str"),
               "image": fname, **st}
        rows.append(row)
        print(f"[{n:02d}/{len(plan)}] {jt:10s} {phase:4s} wall={wall:6.1f}s exec={exec_s:6.1f}s "
              f"avgW={st.get('avg_ppt_w')} peakW={st.get('peak_ppt_w')} Wh={st.get('energy_wh')} "
              f"GTT={st.get('peak_gtt_gb')}GB edge={st.get('peak_edge_c')}C", flush=True)
    tel.stop()

    keys = sorted({k for r in rows for k in r}, key=lambda k: list(rows[0]).index(k) if k in rows[0] else 99)
    with open(os.path.join(a.results, "benchmark.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    if tel.samples:
        sk = sorted({k for s in tel.samples for k in s})
        with open(os.path.join(a.results, "benchmark_samples.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=sk)
            w.writeheader()
            w.writerows(tel.samples)
    summary = {"idle": idle, "groups": {}}
    for jt in dict.fromkeys(r["job_type"] for r in rows):
        for phase in ("cold", "warm"):
            g = [r for r in rows if r["job_type"] == jt and r["phase"] == phase]
            if not g:
                continue
            agg = lambda k, fn=statistics.fmean: round(fn([r[k] for r in g if k in r]), 2) if any(k in r for r in g) else None
            summary["groups"][f"{jt}/{phase}"] = {
                "n": len(g), "wall_s_mean": agg("wall_s"), "wall_s_min": agg("wall_s", min), "wall_s_max": agg("wall_s", max),
                "comfy_exec_s_mean": agg("comfy_exec_s"), "avg_ppt_w": agg("avg_ppt_w"), "peak_ppt_w": agg("peak_ppt_w", max),
                "energy_wh_mean": agg("energy_wh"), "energy_above_idle_wh_mean": agg("energy_above_idle_wh"),
                "peak_gtt_gb": agg("peak_gtt_gb", max), "peak_edge_c": agg("peak_edge_c", max),
                "peak_tctl_c": agg("peak_tctl_c", max), "avg_gfx_w": agg("avg_gfx_w"), "avg_sys_w": agg("avg_sys_w"),
                "avg_busy_pct": agg("avg_busy_pct")}
    json.dump(summary, open(os.path.join(a.results, "benchmark_summary.json"), "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
