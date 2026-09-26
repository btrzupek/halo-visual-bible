#!/usr/bin/env python3
"""
build_site_assets.py — prepare the website's images and "making of" data.

It reads ComfyUI's job history from the live /history endpoint and/or from saved snapshots
(--history; ComfyUI keeps history in memory and loses it on restart). It takes every job in the
book window (from the first job whose image is used in a book; jobs from snapshots are always
kept), and for each output image:
  - writes site/images/full/<name>.webp (original size) and site/images/thumb/<name>.webp
  - records prompt / edit instruction, model, job type, time, execution seconds, the source
    image of edits, the reference image of klein+reference jobs, and where it's used in which book
  - tags it with a book: the book it's used in, or else the book of the nearest used image in time
Entries already in site/data/gallery.js whose jobs are no longer in any history are kept as they are
(their book usage is refreshed), so a ComfyUI restart never drops an earlier book.
Output: site/data/gallery.js  (window.GALLERY = [...], in generation order)

Needs Pillow (for WebP). Usage:
  python3 build_site_assets.py --url http://127.0.0.1:8188 --images ~/halo-images \
      --book John=../site/bible/data --book Mark=../site/mark/data \
      --history '~/halo-images/visual-bible/mark/history-*.json' --site ../site
"""
import argparse, glob, json, os, re, urllib.request

from PIL import Image

PREFIX = re.compile(r"^halo_[0-9a-f]{8}_(.+)$")  # MCP server upload name -> original filename


def book_usage(book: str, book_dir: str, use: dict) -> dict:
    """filename -> list of {"book", "ch", "from", "to", "title"} from the viewer data files."""
    for f in sorted(glob.glob(os.path.join(book_dir, "*.js"))):
        text = open(f).read()
        ch = int(re.search(r"VB\.add\((\d+)", text).group(1))
        data = json.loads(text[text.index("{"): text.rindex("}") + 1])
        for s in data["scenes"]:
            use.setdefault(s[2], []).append({"book": book, "ch": ch, "from": s[0], "to": s[1], "title": s[3]})
    return use


def parse_book(arg: str) -> tuple[str, str]:
    """"Mark=site/mark/data" -> ("Mark", path); a bare path is named from its files (mark-01.js -> "Mark")."""
    if "=" in arg:
        name, path = arg.split("=", 1)
        return name, os.path.expanduser(path)
    path = os.path.expanduser(arg)
    first = sorted(glob.glob(os.path.join(path, "*-*.js")))
    return (os.path.basename(first[0]).split("-")[0].capitalize() if first else os.path.basename(path)), path


def load_history(url: str, patterns: list) -> tuple[dict, set]:
    """Merge the live /history (if reachable) with saved snapshot files. Returns (history, ids from snapshots)."""
    hist, snap = {}, set()
    for pat in patterns:
        for f in sorted(glob.glob(os.path.expanduser(pat))):
            h = json.load(open(f))
            hist.update(h)
            snap.update(h)
    if url:
        try:
            with urllib.request.urlopen(f"{url}/history?max_items=5000", timeout=120) as r:
                hist.update(json.loads(r.read()))
        except OSError as e:
            print(f"warning: live history at {url} not reachable ({e}); using snapshots only")
    return hist, snap


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
    ap.add_argument("--book", action="append", required=True,
                    help="Name=viewer data/ folder, e.g. John=site/bible/data (repeat for each book)")
    ap.add_argument("--history", action="append", default=[],
                    help="saved /history snapshot file(s) or glob (repeatable); pass --url '' to skip the live one")
    ap.add_argument("--cast", action="append",
                    default=["John=halo_klein_00006_.png,halo_klein_00007_.png",
                             "Mark=halo_klein_00026_.png,halo_edit_00051_.png",
                             "Luke=halo_klein_00039_.png",
                             "Matthew=halo_klein_00095_.png",
                             "Acts=halo_klein_00155_.png,halo_klein_00157_.png,halo_klein_00158_.png,halo_klein_00162_.png,halo_klein_00160_.png,halo_edit_00195_.png"],
                    help="Book=images used by that book's page itself (cast portraits)")
    ap.add_argument("--site", required=True)
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--thumb", type=int, default=480)
    a = ap.parse_args()
    images = os.path.expanduser(a.images)
    use = {}
    for b in a.book:
        book_usage(*parse_book(b), use)
    for c in a.cast:
        book, files = c.split("=", 1)
        for x in (x for x in files.split(",") if x):
            use.setdefault(x, []).append({"book": book, "cast": True})

    hist, snap = load_history(a.url, a.history)
    jobs = []
    for pid, h in hist.items():
        msgs = {m[0]: m[1] for m in h["status"].get("messages", [])}
        outs = [i for n in h.get("outputs", {}).values() for i in n.get("images", []) if i.get("type") == "output"]
        if not outs or "execution_start" not in msgs or "execution_success" not in msgs:
            continue
        start, end = msgs["execution_start"]["timestamp"], msgs["execution_success"]["timestamp"]
        if end - start < 500:  # cache replay of an identical request, not a new image
            continue
        jobs.append({"file": outs[0]["filename"], "t": start, "secs": round((end - start) / 1000, 1),
                     "snap": pid in snap, **describe(h["prompt"][2])})
    jobs.sort(key=lambda j: j["t"])
    first = min((j["t"] for j in jobs if j["file"] in use), default=0)
    jobs = [j for j in jobs if j["t"] >= first or j["snap"]]
    fresh = {j["file"].rsplit(".", 1)[0] + ".webp" for j in jobs}

    # keep earlier entries whose jobs are gone from ComfyUI's history (e.g. John, after a restart)
    kept = []
    gpath = os.path.join(a.site, "data", "gallery.js")
    if os.path.exists(gpath):
        old = open(gpath).read()
        for o in json.loads(old[old.index("["): old.rindex("]") + 1]):
            if o["f"] not in fresh:
                o["used"] = use.get(o["f"].rsplit(".", 1)[0] + ".png", [])
                kept.append(o)

    full, thumb = (os.path.join(a.site, "images", d) for d in ("full", "thumb"))
    os.makedirs(full, exist_ok=True)
    os.makedirs(thumb, exist_ok=True)
    out, total = list(kept), 0
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
    out.sort(key=lambda o: o["t"])
    # book of each entry: where it's used, else the book of the nearest used entry in time
    anchors = [(o["t"], o["used"][0]["book"]) for o in out if o["used"] and "book" in o["used"][0]]
    for o in out:
        o["book"] = (o["used"][0].get("book") if o["used"] else None) or \
            min(anchors, key=lambda x: abs(x[0] - o["t"]))[1] if anchors else ""
    os.makedirs(os.path.join(a.site, "data"), exist_ok=True)
    with open(os.path.join(a.site, "data", "gallery.js"), "w") as f:
        f.write("window.GALLERY = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    for book in sorted({o["book"] for o in out}):
        bo = [o for o in out if o["book"] == book]
        print(f"{book}: {len(bo)} images, {sum(1 for o in bo if o['used'])} used in the book")
    print(f"{len(out)} images ({len(kept)} kept from the previous gallery.js), "
          f"{total / 1e6:.1f} MB of new WebP -> {a.site}")


if __name__ == "__main__":
    main()
