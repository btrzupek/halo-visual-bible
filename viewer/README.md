# Visual Bible viewer

A single static page (`index.html`, no build step, no framework) that turns per-chapter data
files plus a folder of images into a long-scroll illustrated book: hero image, sticky chapter
nav, table of contents, cast portraits, alternating image/text scenes, and a click-to-zoom
lightbox. Light and dark themes follow the OS.

```
viewer/
├── index.html        # the page; edit title, hero text, cast, footer
├── data/
│   └── john-01.js    # sample chapter (John 1, 9 scenes)
└── images/           # put the generated PNGs here (not committed)
```

Open `index.html` directly from disk or serve the folder (`python3 -m http.server`). Only
`data/john-01.js` is included; the other 20 `<script src="data/john-NN.js">` tags just 404
and are skipped. Images aren't included; copy your own into `images/` (the page expects the
filenames used in the data files, e.g. `halo_klein_ref_00006_.png`).

## Data file schema

Each chapter is a plain script that registers itself, so the page works from `file://`
without `fetch` or CORS issues:

```js
VB.add(1, {                      // chapter number
  "scenes": [
    // [firstVerse, lastVerse, imageFile, title, subtitle, trim]
    [1, 5, "halo_klein_00008_.png", "In the beginning was the Word",
     "The light shines in darkness, and the darkness does not overcome it.", 0],
    [6, 13, "halo_klein_ref_00006_.png", "A man sent from God",
     "John comes as a witness to the light, pointing beyond himself.", 0]
  ],
  "v": ["verse 1 text", "verse 2 text", "..."]   // every verse of the chapter, 1-based by position
});
```

| Field | Type | Meaning |
|---|---|---|
| `scenes[i][0]`, `[1]` | int | Verse range shown next to the image (inclusive) |
| `scenes[i][2]` | string | Image filename, resolved against `IMG` (`'images/'`) |
| `scenes[i][3]` | string | Scene title |
| `scenes[i][4]` | string | One-line subtitle (also used in the image `alt` text) |
| `scenes[i][5]` | 0/1 | `1` = slightly zoom the image (`.trim`) to crop edge artifacts |
| `v` | string[] | Chapter text; `v[n-1]` is verse `n` |

Conventions the page relies on:

- **Chapter 1, scene 0 is the hero**: its image fills the landing screen and its verses become
  the prologue; it isn't repeated in the body.
- Chapters render in numeric order; missing chapters are skipped; the nav and "Chapters one
  through …" lede adapt to the highest chapter present.
- All text from data files is HTML-escaped before insertion.

To reuse for another book: change the `<title>`, hero `h1`, the "John" labels, the cast
figures, the `<script src>` list, and the footer; keep the data format.
