#!/usr/bin/env python3
"""
halo-imagegen — MCP server that sends image prompts from Claude to ComfyUI
on the Ryzen AI Halo box and returns the generated image into the chat.

Two ways to run it:
  stdio (Claude Desktop / Claude Code on your laptop):
      COMFY_URL=http://127.0.0.1:8188 python halo_imagegen.py
  streamable HTTP (on the Halo box, behind a tunnel, for claude.ai web/mobile):
      python halo_imagegen.py --http --port 8765 --secret <long-random-string>

Models come from a registry JSON (models.json next to this script, or HALO_MODELS):
  {"default": "<name>", "default_edit": "<name>",
   "models": {"<name>": {"kind": "generate"|"edit", "workflow": "workflows/x.json",
                         "description": "...", "width": 1024, "height": 1024,
                         "steps": 8, "cfg": 1.0, "files": ["model files it needs"]}}}
Each workflow is an API-format ComfyUI graph ("Export (API)") with placeholders:
  "{{PROMPT}}" "{{NEGATIVE}}" "{{SEED}}" "{{WIDTH}}" "{{HEIGHT}}" "{{STEPS}}" "{{CFG}}"
  "{{CHECKPOINT}}" (from the entry's "checkpoint"), and for edits "{{IMAGE}}" "{{IMAGE2}}".
A LoadImage node left as "{{IMAGE2}}" is dropped (with its links) when there's no 2nd image.
Optional per-model keys: "reference_workflow" (+ "reference_files") for generating a new
scene around a reference photo, and "train": {"unet","clip","clip_type","vae","options"}
for LoRA training with ComfyUI's built-in TrainLoraNode.

LoRA training state lives in loras.json beside models.json. Trained files are written by
SaveLoRA to ComfyUI's output/loras; on halo, models/loras/trained must be a symlink to it
(ln -s ../../output/loras ~/.local/share/ComfyUI/models/loras/trained) so loaders see them.

Env vars:
  COMFY_URL     ComfyUI base URL (default http://127.0.0.1:8188)
  HALO_MODELS   model registry path (default models.json beside this file)
  HALO_OUT_DIR  where copies of images are saved (default ~/halo-images)
  HALO_TOOL_WAIT_S  how long one tool call waits for a job before returning "still running"
                (default 50; MCP clients commonly abandon a request after 60 s)

Long jobs: every job is watched by a background task that saves the finished image to
HALO_OUT_DIR even if the caller gives up or cancels. A call that outlives HALO_TOOL_WAIT_S
returns the prompt_id instead of an image; collect it with halo_wait_for_job(prompt_id).

Requires: pip install "mcp[cli]<2"   (FastMCP API is v1-only; Pillow optional — shrinks images to JPEG)
"""
import argparse, asyncio, io, json, mimetypes, os, random, time, uuid, urllib.parse, urllib.request

from mcp.server.fastmcp import Context, FastMCP, Image

HERE = os.path.dirname(os.path.abspath(__file__))
COMFY = os.environ.get("COMFY_URL", "http://127.0.0.1:8188").rstrip("/")
MODELS_FILE = os.path.expanduser(os.environ.get("HALO_MODELS", os.path.join(HERE, "models.json")))
OUT_DIR = os.path.expanduser(os.environ.get("HALO_OUT_DIR", "~/halo-images"))
LORAS_FILE = os.path.join(os.path.dirname(MODELS_FILE), "loras.json")  # trained-LoRA jobs/state
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
PHOTO_EXTS = IMAGE_EXTS + (".heic", ".heif", ".tif", ".tiff")
# trained LoRAs are saved to ComfyUI's output/loras; on halo, models/loras/trained is a symlink to it
TRAINED_LORA_DIR = "trained"
TOOL_WAIT_S = float(os.environ.get("HALO_TOOL_WAIT_S", "50"))
_JOBS: dict[str, dict] = {}  # prompt_id -> {"task", "start", "kind", "summary"} for jobs this process started

mcp = FastMCP("halo-imagegen")


def _registry() -> dict:
    # re-read every call so edits to models.json apply without restarting the client
    with open(MODELS_FILE) as f:
        return json.load(f)


def _model(name: str, kind: str) -> tuple[str, dict]:
    reg = _registry()
    name = name or reg.get("default_edit" if kind == "edit" else "default", "")
    m = reg["models"].get(name)
    if not m:
        names = [n for n, e in reg["models"].items() if e.get("kind", "generate") == kind]
        raise ValueError(f"Unknown model {name!r}. {kind} models: {', '.join(names)}")
    if m.get("kind", "generate") != kind:
        raise ValueError(f"Model {name!r} is a {m.get('kind')} model; use the matching tool.")
    return name, m


def _get(path: str) -> bytes:
    with urllib.request.urlopen(f"{COMFY}{path}", timeout=30) as r:
        return r.read()


def _post(path: str, body: dict) -> dict:
    req = urllib.request.Request(f"{COMFY}{path}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"ComfyUI rejected the workflow: {e.read().decode()[:1500]}")


def _upload(path: str, subfolder: str = "", name: str = "", data: bytes | None = None) -> str:
    """Upload a file into ComfyUI's input folder (any type: /upload/image doesn't check);
    returns the name LoadImage wants."""
    name = name or f"halo_{uuid.uuid4().hex[:8]}_{os.path.basename(path)}"
    boundary = uuid.uuid4().hex
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    if data is None:
        with open(path, "rb") as f:
            data = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{name}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + data + (
            f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"type\"\r\n\r\ninput"
            f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"subfolder\"\r\n\r\n{subfolder}"
            f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue"
            f"\r\n--{boundary}--\r\n").encode()
    req = urllib.request.Request(f"{COMFY}/upload/image", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        info = json.loads(r.read())
    return f"{info['subfolder']}/{info['name']}" if info.get("subfolder") else info["name"]


def _combo(node: str, field: str) -> list[str]:
    info = json.loads(_get(f"/object_info/{node}"))
    spec = info[node]["input"]["required"][field]
    # older ComfyUI: [[names...]]; newer: ["COMBO", {"options": [...]}]
    return spec[0] if isinstance(spec[0], list) else spec[1].get("options", [])


def _installed_files() -> set[str]:
    loaders = [("CheckpointLoaderSimple", "ckpt_name"), ("UNETLoader", "unet_name"),
               ("CLIPLoader", "clip_name"), ("VAELoader", "vae_name"), ("LoraLoaderModelOnly", "lora_name")]
    return {f for node, field in loaders for f in _combo(node, field)}


def _resolve_image(path: str) -> str:
    """Local path, a filename in HALO_OUT_DIR, or blank for the most recent image there."""
    if not path:
        imgs = [os.path.join(OUT_DIR, f) for f in os.listdir(OUT_DIR) if f.lower().endswith(IMAGE_EXTS)] \
            if os.path.isdir(OUT_DIR) else []
        if not imgs:
            raise FileNotFoundError(f"No images in {OUT_DIR} yet; pass an image path.")
        return max(imgs, key=os.path.getmtime)
    for cand in (os.path.expanduser(path), os.path.join(OUT_DIR, path)):
        if os.path.isfile(cand):
            return cand
    raise FileNotFoundError(f"Image not found: {path} (also looked in {OUT_DIR})")


def _build_workflow(workflow: str, p: dict) -> dict:
    with open(os.path.join(os.path.dirname(MODELS_FILE), workflow)) as f:
        text = f.read()
    for key in ("PROMPT", "NEGATIVE", "CHECKPOINT", "IMAGE", "IMAGE2"):
        if key == "IMAGE2" and not p.get("image2"):
            continue  # left in place so the node gets pruned below
        text = text.replace("{{%s}}" % key, json.dumps(p.get(key.lower(), ""))[1:-1])
    for key in ("SEED", "WIDTH", "HEIGHT", "STEPS", "CFG"):
        text = text.replace('"{{%s}}"' % key, json.dumps(p.get(key.lower())))
    wf = json.loads(text)
    # no second image: drop its LoadImage node and any inputs wired to it
    dead = {nid for nid, n in wf.items()
            if n["class_type"] == "LoadImage" and n["inputs"].get("image") == "{{IMAGE2}}"}
    for nid in dead:
        del wf[nid]
    for n in wf.values():
        for k in [k for k, v in n["inputs"].items() if isinstance(v, list) and v and v[0] in dead]:
            del n["inputs"][k]
    return wf


def _inject_lora(wf: dict, lora_file: str, strength: float) -> dict:
    """Insert a LoraLoaderModelOnly right after the UNETLoader and rewire its consumers."""
    unet = next(nid for nid, n in wf.items() if n["class_type"] in ("UNETLoader", "CheckpointLoaderSimple"))
    for n in wf.values():
        for k, v in n["inputs"].items():
            if v == [unet, 0]:
                n["inputs"][k] = ["user_lora", 0]
    wf["user_lora"] = {"class_type": "LoraLoaderModelOnly", "inputs": {
        "lora_name": lora_file, "strength_model": strength, "model": [unet, 0]}}
    return wf


def _loras() -> dict:
    try:
        with open(LORAS_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _save_loras(state: dict) -> None:
    tmp = LORAS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, LORAS_FILE)


def _prep_photo(path: str, side: int) -> bytes:
    """EXIF-rotate, convert to RGB and resize to ~side*side pixels (dims multiple of 16), as JPEG."""
    import subprocess, tempfile
    from PIL import Image as PILImage, ImageOps
    if path.lower().endswith((".heic", ".heif")):  # Pillow can't read HEIC; macOS sips can
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name
        subprocess.run(["sips", "-s", "format", "jpeg", path, "--out", tmp], check=True, capture_output=True)
        path = tmp
    im = ImageOps.exif_transpose(PILImage.open(path)).convert("RGB")
    scale = (side * side / (im.width * im.height)) ** 0.5
    w, h = max(16, round(im.width * scale / 16) * 16), max(16, round(im.height * scale / 16) * 16)
    buf = io.BytesIO()
    im.resize((w, h), PILImage.LANCZOS).save(buf, "JPEG", quality=95)
    return buf.getvalue()


def _train_graph(t: dict, folder: str, prefix: str, steps: int, lr: float, rank: int, seed: int) -> dict:
    opts = {"batch_size": 1, "grad_accumulation_steps": 1, "optimizer": "AdamW", "loss_function": "MSE",
            "training_dtype": "bf16", "lora_dtype": "bf16", "quantized_backward": False, "algorithm": "LoRA",
            "gradient_checkpointing": True, "checkpoint_depth": 1, "offloading": False,
            "existing_lora": "[None]", "bucket_mode": False, "bypass_mode": False, **t.get("options", {})}
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": t["unet"], "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": t["clip"], "type": t["clip_type"], "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": t["vae"]}},
        "4": {"class_type": "LoadImageTextDataSetFromFolder", "inputs": {"folder": folder}},
        "5": {"class_type": "MakeTrainingDataset", "inputs": {"images": ["4", 0], "texts": ["4", 1],
                                                               "vae": ["3", 0], "clip": ["2", 0]}},
        "6": {"class_type": "TrainLoraNode", "inputs": {"model": ["1", 0], "latents": ["5", 0], "positive": ["5", 1],
                                                         "steps": steps, "learning_rate": lr, "rank": rank,
                                                         "seed": seed, **opts}},
        "7": {"class_type": "SaveLoRA", "inputs": {"lora": ["6", 0], "prefix": f"loras/{prefix}", "steps": ["6", 2]}},
        "8": {"class_type": "LossGraphNode", "inputs": {"loss": ["6", 1], "filename_prefix": f"loras/{prefix}_loss"}},
    }


async def _ws_progress(client_id: str, prompt_id: str, wait: float = 4.0) -> dict | None:
    """Peek at ComfyUI's websocket (as the job's client) for its latest step progress."""
    import websockets
    url = COMFY.replace("http", "ws", 1) + f"/ws?clientId={client_id}"
    last, end = None, time.time() + wait
    try:
        async with websockets.connect(url, open_timeout=5, max_size=None) as ws:
            while time.time() < end:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=max(0.1, end - time.time()))
                except asyncio.TimeoutError:
                    break
                if isinstance(msg, bytes):
                    continue  # binary preview frames
                m = json.loads(msg)
                if m.get("type") == "progress" and m["data"].get("prompt_id") == prompt_id:
                    last = {"step": m["data"]["value"], "of": m["data"]["max"], "node": m["data"].get("node")}
    except Exception:
        pass
    return last


def _shrink(png: bytes) -> tuple[bytes, str]:
    try:
        from PIL import Image as PILImage
        buf = io.BytesIO()
        PILImage.open(io.BytesIO(png)).convert("RGB").save(buf, "JPEG", quality=88)
        return buf.getvalue(), "jpeg"
    except Exception:
        return png, "png"


def _fetch_output(pid: str, hist: dict) -> tuple[bytes, str]:
    """Download a finished job's first image and save a copy in OUT_DIR."""
    imgs = [i for node in hist["outputs"].values() for i in node.get("images", [])]
    if not imgs:
        raise RuntimeError("Workflow finished but produced no images (is there a SaveImage node?).")
    meta = imgs[0]
    q = urllib.parse.urlencode({"filename": meta["filename"], "subfolder": meta.get("subfolder", ""),
                                "type": meta.get("type", "output")})
    png = _get(f"/view?{q}")
    os.makedirs(OUT_DIR, exist_ok=True)
    saved = os.path.join(OUT_DIR, meta["filename"])
    with open(saved, "wb") as f:
        f.write(png)
    return png, saved


async def _watch(pid: str, timeout_s: int) -> tuple[bytes, str]:
    """Poll ComfyUI until the job finishes, then save its image. Runs as its own task, so a
    caller that times out or cancels never stops the image from being saved."""
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            hist = json.loads(await asyncio.to_thread(_get, f"/history/{pid}")).get(pid)
        except OSError:  # tunnel hiccup: keep trying until the hard timeout
            hist = None
        if hist and hist.get("outputs"):
            return await asyncio.to_thread(_fetch_output, pid, hist)
        if hist and hist.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"ComfyUI error: {json.dumps(hist['status'])[:1500]}")
        await asyncio.sleep(1.0)
    raise TimeoutError(f"No image after {timeout_s}s (prompt_id {pid}); check the ComfyUI queue.")


def _queue_position(pid: str) -> str:
    try:
        q = json.loads(_get("/queue"))
    except OSError:
        return ""
    if any(item[1] == pid for item in q.get("queue_running", [])):
        return "running now"
    pending = [item[1] for item in sorted(q.get("queue_pending", []), key=lambda i: i[0])]
    return f"queued, {pending.index(pid) + 1} of {len(pending)} waiting" if pid in pending else ""


async def _await_job(pid: str, ctx: Context | None, wait_s: float) -> tuple[bytes, str] | None:
    """Wait up to wait_s for a job this process is watching; None if it's still running."""
    job = _JOBS[pid]
    end = time.time() + wait_s
    while not job["task"].done() and time.time() < end:
        if ctx:  # lets clients that honour progress keep the request alive
            await ctx.report_progress(time.time() - job["start"], message="generating on halo")
        await asyncio.wait({job["task"]}, timeout=min(2.0, max(0.05, end - time.time())))
    if not job["task"].done():
        return None
    return job["task"].result()  # re-raises a ComfyUI error or the hard timeout


async def _run(wf: dict, timeout_s: int, ctx: Context | None, kind: str, summary: str):
    """Submit a workflow and wait for it; returns (png, saved) or a "still running" message."""
    pid = _post("/prompt", {"prompt": wf, "client_id": str(uuid.uuid4())})["prompt_id"]
    task = asyncio.get_running_loop().create_task(_watch(pid, timeout_s))
    task.add_done_callback(lambda t: t.cancelled() or t.exception())  # never "exception was never retrieved"
    _JOBS[pid] = {"task": task, "start": time.time(), "kind": kind, "summary": summary}
    done = await _await_job(pid, ctx, TOOL_WAIT_S)
    return (pid, done)


def _pending_message(pid: str) -> str:
    job = _JOBS[pid]
    where = _queue_position(pid)
    return (f"STILL RUNNING on halo after {time.time() - job['start']:.0f}s ({job['kind']}"
            f"{', ' + where if where else ''}). prompt_id={pid}\n"
            f"The image is saved to {OUT_DIR} automatically when it finishes. "
            f'Call halo_wait_for_job(prompt_id="{pid}") to get it. {job["summary"]}')


@mcp.tool()
def halo_list_models() -> list[dict]:
    """List the image models on the Halo box: name, kind (generate/edit), description,
    default settings, and whether all of its model files are installed."""
    reg, have = _registry(), _installed_files()
    out = []
    for name, m in reg["models"].items():
        missing = [f for f in m.get("files", []) if f not in have]
        ref_missing = [f for f in m.get("reference_files", []) if f not in have]
        train_missing = [f for f in (m["train"]["unet"],) if f not in have] if "train" in m else []
        out.append({"name": name, "kind": m.get("kind", "generate"), "description": m.get("description", ""),
                    "is_default": name in (reg.get("default"), reg.get("default_edit")),
                    "defaults": {k: m[k] for k in ("width", "height", "steps", "cfg") if k in m},
                    "installed": not missing, **({"missing_files": missing} if missing else {}),
                    "supports_reference_image": "reference_workflow" in m and not ref_missing,
                    "can_train_lora": "train" in m and not train_missing,
                    **({"lora_training_needs": train_missing} if train_missing else {})})
    for name, j in _loras().items():
        out.append({"name": name, "kind": "lora", "base_model": j["base_model"], "trigger": j["trigger"],
                    "status": j["status"], "use_with": f'halo_generate_image(lora="{name}")'})
    return out


@mcp.tool()
async def halo_generate_image(prompt: str, model: str = "", negative_prompt: str = "",
                              width: int = 0, height: int = 0, steps: int = 0, cfg: float = 0,
                              seed: int = -1, reference_image: str = "", lora: str = "",
                              lora_strength: float = 1.0, timeout_s: int = 900, ctx: Context = None):
    """Generate an image locally on the Halo box via ComfyUI and return it.
    model: a generate model from halo_list_models (blank = default). Use "qwen-image" for
    legible text/lettering or maximum detail, "flux2-klein" for tight prompt adherence,
    "z-image-turbo" for fast photoreal.
    reference_image: optional photo of a person/pet/product (path on this computer, or a
    filename in ~/halo-images) to feature in a NEW scene described by the prompt, e.g.
    prompt "the man from the reference photo hiking in Patagonia". Quick, no training;
    likeness is good but not perfect. Uses flux2-klein unless model is "qwen-image".
    lora: name of a trained LoRA (see halo_list_models / halo_train_lora) for a consistent
    person or style; its base model and trigger word are applied automatically.
    width/height/steps/cfg: 0 = the model's tuned default. Keep width/height multiples of 64
    and around 1-1.8 megapixels. seed=-1 picks a random seed; reuse a seed to iterate.
    negative_prompt has no effect on these distilled models at cfg 1."""
    reg, lora_job = _registry(), None
    if lora:
        lora_job = _loras().get(lora)
        if not lora_job or lora_job.get("status") != "ready":
            raise ValueError(f"LoRA {lora!r} isn't ready ({lora_job['status'] if lora_job else 'unknown'}); "
                             "check halo_training_status.")
        if model and model != lora_job["base_model"]:
            raise ValueError(f"LoRA {lora!r} was trained on {lora_job['base_model']}; it only works with that model.")
        model = lora_job["base_model"]
        if lora_job["trigger"].lower() not in prompt.lower():
            prompt = f"{lora_job['trigger']}, {prompt}"
    if reference_image and not model:
        model = reg.get("default_reference", "flux2-klein")
    name, m = _model(model, "generate")
    workflow = m["workflow"]
    p = {"prompt": prompt, "negative": negative_prompt, "checkpoint": m.get("checkpoint", ""),
         "width": width or m.get("width", 1024), "height": height or m.get("height", 1024),
         "steps": steps or m.get("steps", 20), "cfg": cfg or m.get("cfg", 1.0),
         "seed": random.randint(0, 2**32 - 1) if seed < 0 else seed}
    if reference_image:
        if "reference_workflow" not in m:
            refs = [n for n, e in reg["models"].items() if "reference_workflow" in e]
            raise ValueError(f"{name} can't use a reference image; use one of: {', '.join(refs)}")
        workflow = m["reference_workflow"]
        reference_image = _resolve_image(reference_image)
        p["image"] = _upload(reference_image)
    wf = _build_workflow(workflow, p)
    if lora_job:
        wf = _inject_lora(wf, lora_job["file"], lora_strength)
    summary = (f"model={name} seed={p['seed']} {p['width']}x{p['height']} steps={p['steps']} cfg={p['cfg']}"
               f"{' reference=' + reference_image if reference_image else ''}"
               f"{f' lora={lora}@{lora_strength}' if lora else ''}")
    pid, done = await _run(wf, timeout_s, ctx, "generate", summary)
    return _result(pid, done)


@mcp.tool()
async def halo_edit_image(instruction: str, image: str = "", reference_image: str = "",
                          model: str = "", steps: int = 0, cfg: float = 0, seed: int = -1,
                          timeout_s: int = 900, ctx: Context = None):
    """Edit an existing image on the Halo box from a plain-language instruction
    (e.g. "make the lighting warmer", "add a silver pendant that says HALO",
    "replace the background with a beach") and return the edited image.
    image: path to an image on this computer, or a filename in ~/halo-images.
    Blank = the most recently generated/edited image, so edits can be chained.
    reference_image: optional second image the instruction can call "image 2"
    (e.g. "put the jacket from image 2 on the person in image 1").
    Output keeps roughly the input's aspect ratio at ~1 megapixel.
    steps/cfg: 0 = model default. seed=-1 picks a random seed."""
    name, m = _model(model, "edit")
    src = _resolve_image(image)
    ref = _resolve_image(reference_image) if reference_image else ""
    p = {"prompt": instruction, "negative": "", "image": _upload(src), "image2": _upload(ref) if ref else "",
         "steps": steps or m.get("steps", 4), "cfg": cfg or m.get("cfg", 1.0),
         "seed": random.randint(0, 2**32 - 1) if seed < 0 else seed}
    summary = (f"model={name} source={src}{' reference=' + ref if ref else ''} seed={p['seed']} "
               f"steps={p['steps']} cfg={p['cfg']}")
    pid, done = await _run(_build_workflow(m["workflow"], p), timeout_s, ctx, "edit", summary)
    return _result(pid, done)


def _result(pid: str, done):
    if done is None:
        return _pending_message(pid)
    png, saved = done
    job = _JOBS[pid]
    data, fmt = _shrink(png)
    return [Image(data=data, format=fmt),
            f"{job['summary']} time={time.time() - job['start']:.1f}s saved={saved} prompt_id={pid}"]


@mcp.tool()
async def halo_wait_for_job(prompt_id: str, max_wait_s: int = 0, ctx: Context = None):
    """Collect the image from a halo_generate_image / halo_edit_image call that returned
    "STILL RUNNING" (long jobs such as edits, first model loads, or a busy queue). Waits up to
    max_wait_s (0 = the default, about 50 s) and returns the image, or "STILL RUNNING" again
    if it needs longer: just call it again. Also works for any ComfyUI prompt_id that has
    already finished, e.g. after the MCP server was restarted."""
    wait = min(max_wait_s or TOOL_WAIT_S, TOOL_WAIT_S)
    if prompt_id not in _JOBS:  # not ours (or server restarted): look it up in ComfyUI's history
        end = time.time() + wait
        while True:
            hist = json.loads(_get(f"/history/{prompt_id}")).get(prompt_id)
            if hist and hist.get("outputs"):
                png, saved = _fetch_output(prompt_id, hist)
                data, fmt = _shrink(png)
                return [Image(data=data, format=fmt), f"saved={saved} prompt_id={prompt_id}"]
            if hist and hist.get("status", {}).get("status_str") == "error":
                raise RuntimeError(f"ComfyUI error: {json.dumps(hist['status'])[:1500]}")
            if time.time() >= end:
                where = _queue_position(prompt_id)
                if not where and not hist:
                    raise ValueError(f"prompt_id {prompt_id} isn't queued, running or in ComfyUI's history.")
                return f"STILL RUNNING ({where or 'running'}). prompt_id={prompt_id}. Call halo_wait_for_job again."
            await asyncio.sleep(1.0)
    return _result(prompt_id, await _await_job(prompt_id, ctx, wait))


@mcp.tool()
def halo_train_lora(name: str, images_folder: str, trigger: str = "", base_model: str = "z-image-turbo",
                    steps: int = 0, rank: int = 16, learning_rate: float = 0.0002, resolution: int = 768,
                    seed: int = 42) -> str:
    """Train a LoRA on halo so a model learns a specific person, pet, product or style, then
    use it with halo_generate_image(lora=name). Runs in the background (roughly 5 s/step at
    512px and ~10 s/step at 768px on z-image-turbo, so 1-4 hours);
    ComfyUI can't generate images while it runs. Returns immediately; poll halo_training_status.
    name: short id, e.g. "brian". Re-using a name replaces that LoRA when training finishes.
    images_folder: folder on this computer with 10-30 varied photos (jpg/png/webp/heic) of
    the subject: different angles, lighting, outfits, backgrounds; no other people.
    An optional "<photo>.txt" beside a photo adds a caption for it (the trigger is always prepended).
    trigger: rare token that invokes the subject in prompts (default "<name>_subject");
    it's added to prompts automatically when generating with this LoRA.
    base_model: which model to train for (see halo_list_models can_train_lora).
    steps: 0 = auto (50 per photo, 500-1500). resolution: training side length in pixels."""
    if not name.replace("-", "").replace("_", "").isalnum():
        raise ValueError("name must be letters/digits/-/_ only")
    reg = _registry()
    m = reg["models"].get(base_model)
    if not m or "train" not in m:
        raise ValueError(f"{base_model!r} can't be trained; see halo_list_models can_train_lora.")
    if m["train"]["unet"] not in _installed_files():
        raise ValueError(f"Training {base_model} needs {m['train']['unet']} on halo; it isn't installed.")
    for n, j in _loras().items():
        if j["status"] in ("queued", "training"):
            raise RuntimeError(f"LoRA {n!r} is still training; wait for it or halo_cancel_training.")
    folder = os.path.expanduser(images_folder)
    photos = sorted(f for f in os.listdir(folder) if f.lower().endswith(PHOTO_EXTS) and not f.startswith("."))
    if len(photos) < 4:
        raise ValueError(f"Found {len(photos)} photos in {folder}; use at least 10 (4 minimum).")
    trigger = trigger or f"{name.lower()}_subject"
    steps = steps or max(500, min(1500, 50 * len(photos)))

    run = f"{name}_{time.strftime('%Y%m%d_%H%M%S')}"
    subfolder = f"halo_lora_{run}"
    for i, f in enumerate(photos):
        src = os.path.join(folder, f)
        stem = f"{i:03d}"
        _upload(src, subfolder, f"{stem}.jpg", _prep_photo(src, resolution))
        cap_path = os.path.splitext(src)[0] + ".txt"
        extra = open(cap_path).read().strip() if os.path.isfile(cap_path) else ""
        _upload("", subfolder, f"{stem}.txt", (f"{trigger}, {extra}" if extra else trigger).encode())

    client_id = str(uuid.uuid4())
    graph = _train_graph(m["train"], subfolder, f"halo_{run}", steps, learning_rate, rank, seed)
    pid = _post("/prompt", {"prompt": graph, "client_id": client_id})["prompt_id"]
    state = _loras()
    state[name] = {"status": "queued", "base_model": base_model, "trigger": trigger, "prompt_id": pid,
                   "client_id": client_id, "run": run, "photos": len(photos), "steps": steps, "rank": rank,
                   "learning_rate": learning_rate, "resolution": resolution, "started": time.time(),
                   **({"previous_file": state[name]["file"]} if state.get(name, {}).get("file") else {})}
    _save_loras(state)
    return (f"Training LoRA {name!r} on {base_model}: {len(photos)} photos, {steps} steps, trigger "
            f"{trigger!r}. Queued as {pid}. Check progress with halo_training_status(name={name!r}).")


@mcp.tool()
async def halo_training_status(name: str = ""):
    """Progress of LoRA training jobs (all of them if name is blank): state, current step,
    elapsed time and ETA. When a job finishes it's marked ready and its loss graph is returned."""
    state, out, images = _loras(), [], []
    if name and name not in state:
        raise ValueError(f"No LoRA named {name!r}. Known: {', '.join(state) or 'none'}")
    queue = json.loads(_get("/queue"))
    running = {q[1] for q in queue.get("queue_running", [])}
    pending = {q[1] for q in queue.get("queue_pending", [])}
    for n, j in state.items():
        if name and n != name:
            continue
        info = {"name": n, "base_model": j["base_model"], "trigger": j["trigger"], "steps": j["steps"],
                "photos": j["photos"]}
        if j["status"] in ("queued", "training"):
            pid = j["prompt_id"]
            hist = json.loads(_get(f"/history/{pid}")).get(pid)
            elapsed = time.time() - j["started"]
            if hist and hist.get("status", {}).get("status_str") == "error":
                j["status"] = "failed"
                msgs = [m[1] for m in hist["status"].get("messages", []) if m[0] == "execution_error"]
                j["error"] = (msgs[0].get("exception_message", "") if msgs else "unknown error")[:800]
            elif hist and hist.get("status", {}).get("completed"):
                prefix = f"{TRAINED_LORA_DIR}/halo_{j['run']}_"
                files = [f for f in _combo("LoraLoaderModelOnly", "lora_name") if f.startswith(prefix)]
                if files:
                    j.update(status="ready", file=sorted(files)[-1], finished=time.time())
                    j.pop("previous_file", None)
                else:
                    j.update(status="failed", error="Training finished but the LoRA file isn't visible "
                             f"under models/loras/{TRAINED_LORA_DIR} on halo (is the symlink there?).")
                for node in hist.get("outputs", {}).values():
                    for im in node.get("images", []):
                        q = urllib.parse.urlencode({"filename": im["filename"], "subfolder": im.get("subfolder", ""),
                                                    "type": im.get("type", "output")})
                        images.append(Image(data=_get(f"/view?{q}"), format="png"))
            elif pid in running:
                j["status"] = "training"
                prog = await _ws_progress(j["client_id"], pid)
                if prog and prog["of"] == j["steps"]:  # a TrainLoraNode step, not dataset prep
                    j.setdefault("first_obs", [prog["step"], time.time()])
                    j["last_obs"] = [prog["step"], time.time()]
                info["progress"] = (f"step {prog['step']}/{prog['of']}" if prog
                                    else "preparing dataset / loading model (or between progress updates)")
                (s0, t0), (s1, t1) = j.get("first_obs", [0, 0]), j.get("last_obs", [0, 0])
                if s1 > s0:
                    info["sec_per_step"] = round((t1 - t0) / (s1 - s0), 1)
                    info["eta_minutes"] = round((t1 - t0) / (s1 - s0) * (j["steps"] - s1) / 60)
                elif prog:
                    info["eta"] = "ask again in a minute for an estimate"
            elif pid in pending:
                info["queue_position"] = sorted(pending).index(pid) + 1
            info["elapsed_minutes"] = round(elapsed / 60)
        info["status"] = j["status"]
        for k in ("file", "error"):
            if k in j:
                info[k] = j[k]
        if j["status"] == "ready":
            info["use_with"] = f'halo_generate_image(lora="{n}", prompt="{j["trigger"]}, ...")'
        out.append(info)
    _save_loras(state)
    return [json.dumps(out, indent=2), *images]


@mcp.tool()
def halo_cancel_training(name: str) -> str:
    """Cancel a queued or running LoRA training job (frees halo for image generation)."""
    state = _loras()
    j = state.get(name)
    if not j or j["status"] not in ("queued", "training"):
        raise ValueError(f"No active training job named {name!r}.")
    queue = json.loads(_get("/queue"))
    if j["prompt_id"] in {q[1] for q in queue.get("queue_running", [])}:
        _post("/interrupt", {"prompt_id": j["prompt_id"]})
    else:
        _post("/queue", {"delete": [j["prompt_id"]]})
    if j.get("previous_file"):  # keep using the last good version
        j.update(status="ready", file=j.pop("previous_file"))
    else:
        j["status"] = "cancelled"
    _save_loras(state)
    return f"Cancelled training for {name!r}."


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--http", action="store_true", help="serve streamable HTTP instead of stdio")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--secret", default="", help="unguessable path segment: /<secret>/mcp")
    a = ap.parse_args()
    if not a.http:
        mcp.run()
    else:
        mcp.settings.host, mcp.settings.port = a.host, a.port
        mcp.settings.streamable_http_path = f"/{a.secret}/mcp" if a.secret else "/mcp"
        try:  # tunnel sends a public Host header; localhost-only host checks would reject it
            from mcp.server.transport_security import TransportSecuritySettings
            mcp.settings.transport_security = TransportSecuritySettings(
                enable_dns_rebinding_protection=False)
        except ImportError:
            pass
        mcp.run(transport="streamable-http")
