#!/usr/bin/env python3
"""
build_story.py — render content/story.md into site/index.html (the blog post).

Front matter (between --- lines): title, description, hero (a file in site/images/full),
hero_caption. Lines starting with "[Brian:" are editor notes: they render as highlighted
boxes so they're easy to spot in review, and the build refuses to run with --final while
any remain.

Usage (needs the "markdown" package):
  uv run --with markdown python3 scripts/build_story.py [--final]
"""
import argparse, html, os, re, sys

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="/infographic/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Spectral:ital,wght@0,300;0,400;0,500;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
<style>.todo{{background:#fff3c4;color:#5a4300;border:1px dashed #c9a227;padding:.6rem .9rem;border-radius:4px;font-family:var(--mono);font-size:.85rem}}</style>
</head>
<body>
<nav class="sitenav" aria-label="Site">
  <a class="brand" href="/">halo <b>·</b> Visual Bible</a>
  <a class="link" href="/" aria-current="page">The story</a>
  <a class="link" href="/matthew">Matthew</a>
  <a class="link" href="/mark">Mark</a>
  <a class="link" href="/luke">Luke</a>
  <a class="link" href="/bible">John</a>
  <a class="link" href="/acts">Acts</a>
  <a class="link" href="/making-of">Making of</a>
  <a class="link" href="/under-the-hood">Under the hood</a>
  <a class="link" href="https://github.com/btrzupek/halo-visual-bible">GitHub</a>
</nav>
<figure class="post-hero"><img src="/images/full/{hero}" alt="{hero_caption}"><figcaption>{hero_caption}</figcaption></figure>
<article class="post">
{body}
</article>
<footer class="site"><div>
  <p>Images generated locally on an AMD Ryzen AI Halo box. Scripture is the King James Version. Code is MIT licensed on <a href="https://github.com/btrzupek/halo-visual-bible">GitHub</a>.</p>
</div></footer>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(ROOT, "content", "story.md"))
    ap.add_argument("--out", default=os.path.join(ROOT, "site", "index.html"))
    ap.add_argument("--final", action="store_true", help="fail if editor notes remain")
    a = ap.parse_args()
    text = open(a.src).read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta = dict(line.split(": ", 1) for line in m.group(1).splitlines() if ": " in line)
    body = text[m.end():]
    notes = re.findall(r"^\[Brian:.*?\]$", body, re.S | re.M)
    if a.final and notes:
        sys.exit(f"{len(notes)} editor note(s) left in {a.src}")
    body = re.sub(r"^\[Brian:(.*?)\]$", lambda n: f'<p class="todo">Brian: {html.escape(" ".join(n.group(1).split()))}</p>',
                  body, flags=re.S | re.M)
    rendered = markdown.markdown(body, extensions=["tables", "fenced_code", "md_in_html"])
    for bad in ("—", "–"):
        if bad in rendered:
            print(f"warning: found {bad!r} in the post", file=sys.stderr)
    page = PAGE.format(title=html.escape(meta["title"]), description=html.escape(meta["description"]),
                       hero=meta["hero"], hero_caption=html.escape(meta.get("hero_caption", "")), body=rendered)
    open(a.out, "w").write(page)
    print(f"wrote {a.out} ({len(notes)} editor note(s) remaining)")


if __name__ == "__main__":
    main()
