# Brief: add a book to the Visual Bible (images, book page, Read, narration)

The current, complete brief for adding a book. It supersedes the phase list in
[`book-of-mark.md`](book-of-mark.md), which is kept for history (its craft notes still apply).
Read first: [`AGENTS.md`](../AGENTS.md), [`docs/constitution.md`](../docs/constitution.md) (the rules),
[`docs/image-playbook.md`](../docs/image-playbook.md) (prompting and QA), and [`CLAUDE.md`](../CLAUDE.md)
(wiring checklists and the push command).

A book is done when it has: a book page at `/<book>`, its verse index entry, Making of and Under the
hood entries, a story Part, **and** a narrated full-window reader at `/read/<book>` on the home page.

## Phase 1: plan (STOP for Brian's review)

1. KJV text from `scrollmapper/bible_databases` (`formats/json/KJV.json`), never from memory. Check verse
   counts per chapter.
2. Scene list (verse ranges covering every verse, KJV-phrase titles, one-line subtitles), cast plan, and
   the site changes. Copy the newest working folder kit (`~/halo-images/visual-bible/kings/`).
3. **STOP** and show Brian. Then generate the new cast portraits and show them.

## Phase 2: generate (chapter by chapter)

As in the playbook: generate, QA zoomed in, fix or regenerate, log every attempt in `worklog.md`, write
`site/<book>/data/<book>-NN.js` with the kit's `write_chapter.py`, save a ComfyUI history snapshot after
each chapter, and show a contact sheet every 2 or 3 chapters.

## Phase 3: the book page and site wiring

Follow AGENTS.md "Common tasks, Add a book": copy the newest book page, Books menu on every page (and in
`scripts/build_story.py`, whose output is now `site/story/index.html`), `--cast` in
`build_site_assets.py`, Making of filter, Under the hood column, `BOOKS` in `build_verse_index.py`,
per-job numbers, story Part. Build order: assets, verse index, numbers, story.

## Phase 4: Read and narration

Checklist in CLAUDE.md, "Adding a book to Read". In short:

1. Add the book to `BOOKS` in `scripts/build_audio.py` (spoken KJV title, e.g. "The First Book of
   Moses, called Genesis") and `scripts/build_read_pages.py` (canonical order, testament).
2. **Camera paths:** `scripts/find_focus.swift` over the book's images, then
   `scripts/build_motion.py --book <book>`. Render phone views with
   `/usr/bin/python3 scripts/read_review_sheets.py --out <dir> <book>` and look at **every** sheet. Fix
   bad scenes by hand under the motion file's `// keep` line: empty sky or wall, a face cut off, and
   anything violent. Deaths, wounds and executions pull back to a wide view; never zoom onto a body.
3. **Narration:** `python3 scripts/build_audio.py --book <book> --bitrate 48k` (Kokoro on halo, voice
   `bm_george`, about 10x real time; needs the `com.halo.tts-tunnel` socket, see `tts/README.md`). It
   prints one line per scene and appends to `~/halo-images/visual-bible/audio/worklog.md`.
4. **Pronunciation:** names Kokoro gets wrong go in `tts/lexicon.json` (misaki phonemes); audition with
   the `halo-tts` MCP tools (`halo_tts_speak`), then re-voice only those scenes:
   `build_audio.py --book <book> --only 3:16,4:1 --force`. Brian listens; the agent cannot.
5. `python3 scripts/build_read_pages.py`, then check `/read/<book>` locally and in the **iOS Simulator**
   (Xcode is installed; the iPhone SE simulator has Safari's text zoom). Chrome emulation in a hidden
   browser pane runs no animation frames and gives false results for motion and verse following.
6. Coverage: `build_read_pages.py` prints `complete` per book, or lists every scene missing motion or
   audio, or whose audio has the wrong number of verse timestamps. Fix until every book says `complete`.

## Phase 5: publish (STOP before pushing)

Contact sheets, the story Part and a sample of `/read/<book>` scenes to Brian; push only on his OK
(command in CLAUDE.md). `main` deploys to production in about a minute; then verify the live site.

## Working in parallel (agents)

Halo has **one GPU**, shared by ComfyUI (images) and Kokoro (narration). Plan around it:

- **Serial, one at a time:** image generation and edits (one ComfyUI job at a time). Narration is short
  (a book is 15 to 30 minutes of GPU) but slows image jobs while it runs, so run it between image
  sessions or after a book's images are final. Its inputs are the text and scene ranges only, so it can
  run any time after the plan is approved; scene ranges must not change afterwards (or re-voice them).
- **Safe to fan out:** KJV text prep and scene planning for the next book; contact-sheet and phone-view
  review; camera paths (`find_focus` runs on the Mac, not halo); site wiring; metrics, Under the hood
  and story drafts.
- **Never in parallel:** two agents writing the same files (`site/data/gallery.js`, the Books menus,
  `build_read_pages.py`, `BOOKS` lists), or two pushes to `main`. Have one agent do the shared wiring
  for all books in the batch at the end.
- One worktree per agent if they edit the repo at the same time, merged by one coordinator.
