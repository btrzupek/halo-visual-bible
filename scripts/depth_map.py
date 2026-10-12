#!/usr/bin/env python3
"""Depth maps for parallax shots, with Depth Anything V2 Large, on the Mac (MPS or CPU). Nothing runs on halo.

  uv run --with torch --with transformers --with pillow python scripts/depth_map.py IMAGE.png [IMAGE2.png ...] [--out DIR]

Writes <name>.depth.png next to each image (or into --out): 16-bit grayscale at the image's size, near = white.
The first run downloads the model (~1.3 GB) into the Hugging Face cache.
"""
import argparse, os, sys
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

MODEL = 'depth-anything/Depth-Anything-V2-Large-hf'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('images', nargs='+'); ap.add_argument('--out')
    a = ap.parse_args()
    dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
    proc = AutoImageProcessor.from_pretrained(MODEL)
    model = AutoModelForDepthEstimation.from_pretrained(MODEL).to(dev).eval()
    for p in a.images:
        im = Image.open(os.path.expanduser(p)).convert('RGB')
        with torch.no_grad():
            pred = model(**{k: v.to(dev) for k, v in proc(images=im, return_tensors='pt').items()}).predicted_depth
        d = torch.nn.functional.interpolate(pred.unsqueeze(1), size=im.size[::-1], mode='bicubic', align_corners=False)
        d = d.squeeze().float().cpu().numpy()
        d = (d - d.min()) / max(1e-6, d.max() - d.min())          # relative inverse depth: near = 1
        out = os.path.join(a.out or os.path.dirname(os.path.expanduser(p)),
                           os.path.splitext(os.path.basename(p))[0] + '.depth.png')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        Image.fromarray((d * 65535).astype(np.uint16)).save(out)
        print(out, im.size, dev, flush=True)


if __name__ == '__main__':
    main()
