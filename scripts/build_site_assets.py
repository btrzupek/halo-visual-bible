#!/usr/bin/env python3
"""
build_site_assets.py — prepare the website's images and "making of" data.

From ComfyUI's /history it takes every job in the book window (from the first job whose image
is used in the book), and for each output image:
  - writes site/images/full/<name>.webp (original size) and site/images/thumb/<name>.webp
  - records prompt / edit instruction, model, job type, time, execution seconds, the source
    image of edits, the reference image of klein+reference jobs, and where it's used in the book
Output: site/data/gallery.js  (window.GALLERY = [...], in generation order)

Needs Pillow (for WebP). Usage:
  python3 build_site_assets.py --url http://127.0.0.1:8188 --images ~/halo-images \
      --book ../site/bible/data --site ../site
"""
import argparse, glob, json, os, re, urllib.request

from PIL import Image

PREFIX = re.compile(r"^halo_[0-9a-f]{8}_(.+)$")  # MCP server upload name -> original filename


def book_usage(book_dir: str) -> dict:
    """filename -> list of {"ch", "from", "to", "title"} from the viewer data files."""
    use = {}
    for f in sorted(glob.glob(os.path.join(book_dir, "*.js"))):
        text = open(f).read()
        ch = int(re.search(r"VB\.add\((\d+)", text).group(1))
        data = json.loads(text[text.index("{"): text.rindex("}") + 1])
        for s in data["scenes"]:
            use.setdefault(s[2], []).append({"ch": ch, "from": s[0], "to": s[1], "title": s[3]})
    return use


def describe(graph: dict) -> dict:
    by = {}
    for n in graph.values():
        by.setdefault(n["class_type"], []).append(n["inputs"])
    kind = ("edit" if "TextEncodeQwenImageEditPlus" in by and "VAEEncode" in by else
            "klein_ref" if "ReferenceLatent" in by else "klein" if "Flux2Scheduler" in by else "other")
    prompt = next((i["prompt"] for i in by.get("TextEncodeQwenImageEditPlus", []) if i.get("prompt")), "") or \
        next((i["text"] for i in by.get("CLIPTextEncode", []) if isinstance(i.get("text"), str) and i["text"]), "")
    loads = [i["image"] for i in by.get("LoadImage", [])]
    src = [(PREFIX.match(x).group(1) if PREFIX.match(x) else x) for x in loads]
    steps = next((i.get("steps") for t in ("KSampler", "Flux2Scheduler") for i in by.get(t, []) if isinstance(i.get("steps"), int)), None)
    seed = next((i.get(k) for t, k in (("KSampler", "seed"), ("RandomNoise", "noise_seed")) for i in by.get(t, []) if isinstance(i.get(k), int)), None)
    return {"kind": kind, "prompt": prompt, "source": src, "steps": steps, "seed": seed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8188")
    ap.add_argument("--images", default="~/halo-images")
    ap.add_argument("--book", required=True, help="viewer data/ folder (john-NN.js)")
    ap.add_argument("--extra-book-files", default="halo_klein_00006_.png,halo_klein_00007_.png",
                    help="images used by the page itself (cast portraits)")
    ap.add_argument("--site", required=True)
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--thumb", type=int, default=480)
    a = ap.parse_args()
    images = os.path.expanduser(a.images)
    use = book_usage(os.path.expanduser(a.book))
    cast = [x for x in a.extra_book_files.split(",") if x]
    for x in cast:
        use.setdefault(x, []).append({"cast": True})

    with urllib.request.urlopen(f"{a.url}/history?max_items=5000", timeout=120) as r:
        hist = json.loads(r.read())
    jobs = []
    for pid, h in hist.items():
        msgs = {m[0]: m[1] for m in h["status"].get("messages", [])}
        outs = [i for n in h.get("outputs", {}).values() for i in n.get("images", []) if i.get("type") == "output"]
        if not outs or "execution_start" not in msgs or "execution_success" not in msgs:
            continue
        start, end = msgs["execution_start"]["timestamp"], msgs["execution_success"]["timestamp"]
        if end - start < 500:  # cache replay of an identical request, not a new image
            continue
        jobs.append({"file": outs[0]["filename"], "t": start, "secs": round((end - start) / 1000, 1), **describe(h["prompt"][2])})
    jobs.sort(key=lambda j: j["t"])
    first = min(j["t"] for j in jobs if j["file"] in use)
    jobs = [j for j in jobs if j["t"] >= first]

    full, thumb = (os.path.join(a.site, "images", d) for d in ("full", "thumb"))
    os.makedirs(full, exist_ok=True)
    os.makedirs(thumb, exist_ok=True)
    out, total = [], 0
    for j in jobs:
        src = os.path.join(images, j["file"])
        if not os.path.exists(src):
            continue
        name = j["file"].rsplit(".", 1)[0] + ".webp"
        im = Image.open(src).convert("RGB")
        im.save(os.path.join(full, name), "WEBP", quality=a.quality, method=6)
        t = im.copy()
        t.thumbnail((a.thumb, a.thumb * 2))
        t.save(os.path.join(thumb, name), "WEBP", quality=75, method=6)
        total += os.path.getsize(os.path.join(full, name)) + os.path.getsize(os.path.join(thumb, name))
        out.append({"f": name, "w": im.width, "h": im.height, "t": j["t"], "secs": j["secs"], "kind": j["kind"],
                    "prompt": j["prompt"], "source": [s.rsplit(".", 1)[0] + ".webp" for s in j["source"]],
                    "seed": j["seed"], "steps": j["steps"], "used": use.get(j["file"], [])})
    os.makedirs(os.path.join(a.site, "data"), exist_ok=True)
    with open(os.path.join(a.site, "data", "gallery.js"), "w") as f:
        f.write("window.GALLERY = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    used = sum(1 for o in out if o["used"])
    print(f"{len(out)} images ({used} used in the book), {total / 1e6:.1f} MB of WebP -> {a.site}")


if __name__ == "__main__":
    main()
