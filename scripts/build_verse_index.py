#!/usr/bin/env python3
"""Build the public verse -> image index under site/index/v1/.

Reads every chapter file (site/<folder>/data/<book>-NN.js, the same data the viewer
loads) and writes:

  site/index/v1/books.json         which books are illustrated, and how far
  site/index/v1/<book-slug>.json   chapter -> scenes, each with verse range and image URLs

Other apps (e.g. Inscripture) fetch these to show the scenes that cover a passage.
Slugs match Inscripture's book slugs ("matthew", "1samuel"). Verse numbers are
KJV. A scene id ("matthew.5.13") is book + chapter + first verse, the same key as the
viewer's page anchor (/matthew#s5-13), so it stays stable when an image is replaced.
Scenes whose .webp isn't in site/images/full yet are left out, so the index never
points at a missing image.

Stdlib only. Run after build_site_assets.py, before committing:

  python3 scripts/build_verse_index.py [--base https://halo-visual-bible.vercel.app]
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import struct
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
SITE = os.path.join(ROOT, 'site')
OUT = os.path.join(SITE, 'index', 'v1')
SCHEMA_VERSION = 1

# site folder -> (slug, display name, viewer path). Order is canonical book order.
BOOKS = {
    'matthew': ('matthew', 'Matthew', '/matthew'),
    'mark': ('mark', 'Mark', '/mark'),
    'luke': ('luke', 'Luke', '/luke'),
    'bible': ('john', 'John', '/bible'),
    'acts': ('acts', 'Acts', '/acts'),
}
KINDS = {0: 'scene', 1: 'parable', 2: 'vision'}
CHAPTER_RE = re.compile(r'\s*VB\.add\(\s*(\d+)\s*,(.*)\)\s*;?\s*$', re.S)


def webp_size(path: str) -> tuple[int, int] | None:
    """Width/height from a WebP header (VP8, VP8L or VP8X), without decoding."""
    with open(path, 'rb') as f:
        head = f.read(30)
    if len(head) < 30 or head[:4] != b'RIFF' or head[8:12] != b'WEBP':
        return None
    chunk = head[12:16]
    if chunk == b'VP8X':
        w = int.from_bytes(head[24:27], 'little') + 1
        h = int.from_bytes(head[27:30], 'little') + 1
        return w, h
    if chunk == b'VP8 ':
        w, h = struct.unpack('<HH', head[26:30])
        return w & 0x3FFF, h & 0x3FFF
    if chunk == b'VP8L':
        b = int.from_bytes(head[21:25], 'little')
        return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    return None


def read_chapter(path: str) -> tuple[int, list]:
    m = CHAPTER_RE.match(open(path, encoding='utf-8').read())
    if not m:
        sys.exit(f'{path}: not a VB.add(n, {{...}}) chapter file')
    return int(m.group(1)), json.loads(m.group(2))['scenes']


def build_book(folder: str, base: str) -> dict | None:
    slug, name, page = BOOKS[folder]
    files = sorted(glob.glob(os.path.join(SITE, folder, 'data', '*-[0-9][0-9].js')))
    chapters: dict[str, list] = {}
    for path in files:
        ch, scenes = read_chapter(path)
        out = []
        for sc in scenes:
            start, end, png, title, subtitle = sc[:5]
            kind = KINDS.get(sc[6] if len(sc) > 6 else 0, 'scene')
            img = png[:-4] + '.webp' if png.endswith('.png') else png
            full = os.path.join(SITE, 'images', 'full', img)
            if not os.path.exists(full):
                continue
            size = webp_size(full) or (None, None)
            out.append({
                'id': f'{slug}.{ch}.{start}',
                'from': start,
                'to': end,
                'title': title,
                'subtitle': subtitle,
                'kind': kind,
                'full': f'{base}/images/full/{img}',
                'thumb': f'{base}/images/thumb/{img}',
                'w': size[0],
                'h': size[1],
                'page_url': f'{base}{page}#s{ch}-{start}',
            })
        if out:
            chapters[str(ch)] = sorted(out, key=lambda s: s['from'])
    if not chapters:
        return None
    return {
        'schema_version': SCHEMA_VERSION,
        'slug': slug,
        'name': name,
        'versification': 'KJV',
        'page_url': base + page,
        'chapters': dict(sorted(chapters.items(), key=lambda kv: int(kv[0]))),
    }


def write_json(path: str, data: dict) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        f.write('\n')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--base', default='https://halo-visual-bible.vercel.app',
                    help='public origin for image and page URLs')
    base = ap.parse_args().base.rstrip('/')

    os.makedirs(OUT, exist_ok=True)
    books = []
    for folder in BOOKS:
        book = build_book(folder, base)
        if not book:
            continue
        write_json(os.path.join(OUT, f"{book['slug']}.json"), book)
        count = sum(len(s) for s in book['chapters'].values())
        books.append({
            'slug': book['slug'],
            'name': book['name'],
            'chapters_available': [int(c) for c in book['chapters']],
            'scene_count': count,
            'page_url': book['page_url'],
            'index_url': f"{base}/index/v1/{book['slug']}.json",
        })
        print(f"{book['name']:8} {len(book['chapters']):3} chapters {count:4} scenes")

    write_json(os.path.join(OUT, 'books.json'), {
        'schema_version': SCHEMA_VERSION,
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'versification': 'KJV',
        'source': 'https://github.com/btrzupek/halo-visual-bible',
        'books': books,
    })


if __name__ == '__main__':
    main()
