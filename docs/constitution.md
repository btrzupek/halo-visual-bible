# Project constitution

The rules every contributor, human or agent, follows in this repo. When a request conflicts with one
of these, say so and ask Brian before going ahead. Most of these were set by Brian directly or came
out of a mistake that had to be undone.

## 1. Scripture

1. **King James Version only**, taken from a public-domain source (the recent books came from
   `scrollmapper/bible_databases`, `formats/json/KJV.json`), never typed from memory. Strip the space before
   punctuation that source has. Check verse counts per chapter against the source.
2. **Every verse is shown.** A book's scenes cover every verse of every chapter with no gaps or
   overlaps. `write_chapter.py` asserts this.
3. Verse numbers and scene ranges are KJV versification. Scene ids depend on a scene's first verse
   (`<slug>.<chapter>.<first verse>`); don't move a scene's first verse without a reason.
4. Scene titles are KJV phrases from the passage. Subtitles are one short plain line.

## 2. What the images may show

1. **God is shown only as light.** Never a figure, face or hand. A shaft, a glow, a cloud, a column
   of light. Angels and "the three men" appear as the text describes them (as men, or with a soft
   radiance, no wings unless the text gives them).
2. **Nobody touches the ark of the covenant**, except Uzzah (2 Samuel 6:6) and priests or Levites
   carrying it by the poles, hands only on the poles. Every ark scene is generated with the ark
   reference (`halo_klein_00274_.png`). If carrying keeps putting hands on the chest, show the ark
   at rest instead.
3. **Violence is non-graphic.** No blood, no gore, no bodies in the fire. Show the moment before or
   after (Jezebel at the window, not the fall; an empty silent camp, not the dead).
4. **Modesty.** Women fully and modestly dressed; sexual episodes (Bathsheba, Tamar, Potiphar's wife,
   Lot's daughters, Dinah) shown with nothing sexual in the frame. Adam and Eve before the fall are
   tasteful unclothed silhouettes or turned away, then fig leaves, then simple skin wraps.
5. **Historically plausible.** Iron Age dress for the Old Testament, first-century Judea for the New.
   No modern objects of any kind (see the playbook's list). Biblical accuracy wins over drama: if
   the text doesn't say it (laughter, a crowd, a second sword), don't draw it.
6. **Parables and visions are labelled.** The 7th scene field is `1` (parable) or `2` (vision); the
   viewer draws a dream edge and a label. Use it for stories told (the thistle and the cedar) and
   visions (Jacob's ladder, the chariots of fire at Dothan), not for events.
7. **Babies are laid down**, never held (babies in arms come out two-headed or with extra hands).

## 3. Process

1. **Plan, then stop.** For a new book: scene list with verse ranges, cast plan and site changes go
   to Brian first. Generate the cast portraits next and show them.
2. **QA every image zoomed in**, region by region, before accepting it. Full-frame looks miss
   watches, glasses, light switches and extra fingers.
3. **Log everything.** Every attempt goes in the book's `worklog.md` with the job name
   (`klein NNNNN`, `ref NNNNN`, `edit_NNNNN`), what was wrong, and `ACCEPT` or `REJECT`. Minor flaws
   left in are marked `: minor` so they can be reported.
4. **Review before publish.** Build contact sheets and the local page, send them to Brian, and push
   only when he approves (unless he explicitly said to publish without review).
5. **Report honestly.** Say what failed, what was left imperfect, and what you couldn't do. Numbers
   on the site are computed from ComfyUI history, not estimated. If a number changes after a fix,
   update it everywhere it was published (under-the-hood table, story tables).
6. **Keep history.** Save a ComfyUI `/history` snapshot after each chapter or fix session.

## 4. Things never to do

- Delete or overwrite another book's images, chapter data or history snapshots.
- Change anything on the halo box except through the `halo-imagegen` MCP tools. No `sudo`, no
  package installs, no model downloads without asking.
- Work around a missing or failing MCP tool. Report it.
- Push with the wrong GitHub account or switch the active `gh` account (see CLAUDE.md).
- Rename or remove fields in `site/index/v1/`. Breaking changes go to `/index/v2/`.
- Add a build step to the site. It is plain static HTML served as-is.

## 5. Voice for the story and site text

The story (`content/story.md`) and site copy are in Brian's voice, first person.

- No em dashes or en dashes anywhere. Use commas, colons, full stops or parentheses.
- No "it's not X, it's Y" constructions. No marketing tone, no hype words.
- Don't invent personal details, opinions or feelings for Brian. State what happened.
- Plain, specific, a little dry. Short paragraphs. Concrete failures are the interesting part.
- Each book gets a story Part: what it is, the cast, what was hard, a "What went wrong this time"
  list, and a small numbers table.

## 6. Engineering

- The site has no build step and no framework. Pages share `site/assets/site.css` and `nav.js`.
  Each book page is a copy of the previous one with its own inline styles and script.
- The Making of gallery (`site/data/gallery.js`) is the only surviving record of some old jobs; the
  asset build keeps existing entries. Never regenerate it from scratch.
- Asset writes are atomic (temp file then rename) so a page loaded mid-build never caches an empty image.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` when an
  agent wrote the change.
