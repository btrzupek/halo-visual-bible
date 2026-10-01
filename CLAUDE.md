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

**Site nav:** books are in the `Books` menu (`<details class="books">`) in every page's `sitenav`, grouped
by testament in canonical order. Add the new book's link there in each `site/*/index.html`, in
`scripts/build_story.py` (then rebuild the story), and mark it `aria-current="page"` plus
`class="books current"` with the book name as the `<summary>` on the book's own page. When you change
`site/assets/site.css`, bump the `?v=` on its `<link>` in every page so browsers fetch the new file.

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
