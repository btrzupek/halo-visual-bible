# CLAUDE.md

Notes for Claude Code sessions in `halo-visual-bible`.

**New session? Read [`AGENTS.md`](AGENTS.md) first**: current state, where everything lives, and
links to the constitution (the rules), the architecture and the image playbook in [`docs/`](docs/).
The full brief for illustrating a book is [`prompts/book-of-mark.md`](prompts/book-of-mark.md);
this file covers the steps that are easy to miss.

## Adding a book

When a new book gets its own `site/<folder>/data/<book>-NN.js` chapter files, it must also be
registered in the verse index, or it won't appear in Inscripture (which reads `/index/v1/`).

1. **Register it in `BOOKS`** in [`scripts/build_verse_index.py`](scripts/build_verse_index.py):

   ```python
   BOOKS = {
       ...
       'acts': ('acts', 'Acts', '/acts'),
       'romans': ('romans', 'Romans', '/romans'),   # site folder: (slug, display name, viewer path)
   }
   ```

   - **Key:** the folder under `site/` (John's is `bible`, since `/bible` was already shared).
   - **Slug:** must match Inscripture's `BIBLE_BOOKS[].slug`: the English book name, lowercased, with
     spaces removed (`romans`, `1corinthians`, `songofsolomon`). A wrong slug means the book never
     matches a study.
   - **Viewer path:** the book page URL, used for the scene deep links (`/romans#s8-28`).
   - Keep the entries in canonical book order.

2. **Build the WebPs first** (`scripts/build_site_assets.py`). The index skips any scene whose
   image isn't in `site/images/full/` yet.

3. **Rebuild the index:** `python3 scripts/build_verse_index.py`. It prints the chapter and scene
   counts per book; check that the new book's numbers look right. It exits with an error if a book
   folder has chapter files but no `BOOKS` entry.

4. **Commit `site/index/v1/`** with the book's data and images. After Vercel redeploys, check
   `https://halo-visual-bible.vercel.app/index/v1/books.json` lists the book, then open a study
   for one of its passages in Inscripture's Illustrations section.

Rerun step 3 whenever chapters, picks or scene ranges change, not only for new books.

## Adding a book to Read (the home page)

1. Add it to `BOOKS` in `scripts/build_audio.py` (spoken title) and `scripts/build_read_pages.py`
   (slug, folder, names, testament), in canonical order.
2. Camera paths: run `scripts/find_focus.swift` over the book's images (see `scripts/build_motion.py`),
   then `python3 scripts/build_motion.py --focus ... --book <book>`. Render phone views and fix bad
   ones by hand under the file's `// keep` line (they survive reruns). Pull back on deaths and the
   Passion; never zoom onto wounds.
3. Narration: `python3 scripts/build_audio.py --book <book> --bitrate 48k` (needs the halo TTS tunnel).
4. `python3 scripts/build_read_pages.py`, then check `/read/<book>` locally and in the iOS Simulator.
5. When you change `present.js` or `present.css`, bump `ASSET_V` in `build_read_pages.py` and rerun it.
6. Add the book's slug and name to `BOOKS` in [`api/report.js`](api/report.js), or its reader reports are refused.

**Site nav:** books are in the `Books` menu (`<details class="books">`) in every page's `sitenav`, grouped
by testament in canonical order. **Every Books link opens the reader, `/read/<slug>`** (John: `/read/john`).
The scrolling `/<folder>` page is called **All scenes**: readers reach it from the reader's "Browse all scenes"
button and its top-left book name, and its bar has "▶ Read and listen" plus one "Show text" switch (off by
default, so it opens as the picture grid; `?view=scripture` opens with text). Every page but home gets a **Back** button at the left of the nav bar, added by `site/assets/nav.js`
(the reader has the same in its top bar, `present.js`): it returns to the previous page on this site, else goes up
(All scenes to its reader, everything else home). New pages need nothing beyond the usual `nav.js?v=` script tag.

**Link preview:** shared links show `site/og/home.jpg` (1200x630), a collage of book cards made from
`site/og/card.html`, which reads the book list from the home page. After adding a book and rebuilding the home page,
rerun `scripts/render_og.sh` (site served on port 8090) and commit the new `home.jpg`. The story and the infographic
keep the infographic card (`/infographic/og.png`). Add the new book's link in each
`site/*/index.html`, in `scripts/build_story.py` (then rebuild the story), and mark it `aria-current="page"` plus
`class="books current"` with the book name as the `<summary>` on the book's own page. When you change
`site/assets/site.css`, bump the `?v=` on its `<link>` in every page so browsers fetch the new file.

## Reader reports

Every scene on a book page, and the flag button in the reader's top bar, opens a "Report a problem" dialog
(`site/assets/report.js`). It posts to `/api/report` ([`api/report.js`](api/report.js), a Vercel function),
which files an issue in the private repo `btrzupek/halo-visual-bible-reports`, or adds a comment when the same
scene, kind and reason is already open. Nothing personal is collected. Spam checks: a hidden honeypot field,
a minimum time on the form, strict field checks, and five reports per IP per ten minutes (in memory only).

- Every book page carries the same line after `nav.js`: `<script src="/assets/report.js?v=1" defer></script>`.
  New book pages copied from an existing one get it for free. When `report.js` changes, bump `REPORT_V` in
  `build_read_pages.py`, rerun it, and bump the `?v=` on that line in every `site/<book>/index.html`.
- Vercel env vars: `REPORTS_TOKEN` (fine-grained token, Issues read and write on the reports repo only) and
  optionally `REPORTS_REPO`. Without a token the API answers 503 and the dialog says it could not send.
- Tests: `node scripts/test_report_api.js` (fake GitHub, no network). `python3 -m http.server` has no API, so
  sending fails there by design; set `REPORTS_DRY_RUN=1` under `vercel dev` to see the issue it would file.

## Rules for the index

- Scene ids are `<slug>.<chapter>.<first verse>` and match the viewer anchors. Don't change a
  scene's first verse casually: it changes the id.
- The schema is versioned by path. Adding fields is fine in `v1`; renaming or removing fields
  means a new `/index/v2/`, with `v1` kept until Inscripture has moved over.
- Verse numbers are KJV.

## Pushing

The active `gh` account (`btrzupek-dc`) can't push here. Push as `btrzupek` without switching:

```bash
GH_TOKEN=$(gh auth token -u btrzupek) git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push origin main
```

Keep the single quotes: in an interactive zsh, `!gh` inside double quotes is history-expanded
(for example to your last `gh auth ...` command) and git then fails with `credential-gh is not a git command`.
