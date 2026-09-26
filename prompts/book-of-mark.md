# Prompt: illustrate the Gospel of Mark and add it to the Visual Bible site

Paste everything below the line into a new Claude Code session opened in `~/code/halo-visual-bible`.

---

I want to extend my Visual Bible project with the **Gospel of Mark**, done the same way as the Gospel of John,
and add it to the existing website and repo. Read this whole brief first, then work in the phases below. Check in
with me at the points marked **STOP**.

## Where things are

- **Repo (source of truth):** `~/code/halo-visual-bible`. It's public on GitHub as `btrzupek/halo-visual-bible`,
  and pushing to `main` auto-deploys to Vercel at https://halo-visual-bible.vercel.app.
  - `site/`: static site with no build step. `site/bible/` is the John viewer (`index.html` +
    `data/john-NN.js`), plus `site/making-of/`, `site/under-the-hood/`, `site/infographic/`, and
    `site/index.html` (the story).
  - `site/images/full` and `site/images/thumb`: WebP versions of the images.
  - `scripts/build_site_assets.py`: converts images to WebP and builds `site/data/gallery.js` from ComfyUI's history.
  - `scripts/comfy_history_metrics.py`: job metrics.
  - `content/story.md` → `scripts/build_story.py` → `site/index.html`.
- **Image generation:** the `halo-imagegen` MCP tools (`halo_generate_image`, `halo_edit_image`,
  `halo_list_models`) drive ComfyUI on my AMD Ryzen AI Halo box. Outputs land in `~/halo-images/`. ComfyUI only
  runs while I'm logged into the halo desktop. If the tools are missing or failing, tell me; don't work around it.
- **The John working copy and notes:** `~/halo-images/visual-bible/`, including `metrics/metrics.md`, the
  per-chapter log and failure taxonomy that I'd like mirrored for Mark.

## What made John work (keep doing this)

- **Models:** FLUX.2 klein for scenes (`model: "flux2-klein"`, 1344x768, 4 steps defaults). Use
  `reference_image` for any scene with a recurring character. Qwen-Image-Edit (`halo_edit_image`) for targeted fixes.
- **Cast consistency: reuse John's portraits**, so the same Jesus appears across books:
  - Jesus: `~/halo-images/halo_klein_00006_.png`
  - John the Baptist: `~/halo-images/halo_klein_00007_.png` (Mark 1 and 6)
  - If Mark needs another recurring character (Peter is the obvious one), make **one** 896x1152 portrait
    first, in the same style as the existing portraits, show it to me, then use it as the reference.
- **Prompts:** cinematic, historically accurate first-century Judea and Galilee, photoreal film still. Say
  "the man from the reference image" for the referenced character, and say who else is in frame and what
  they're doing. Close every prompt with these constraints: *"First-century clothing and leather sandals; natural
  anatomy, each person with two arms and two hands. No modern objects, no text."*
- **QA every image before accepting it.** Look at it. These are the failures that actually happened in John:
  - **Modern intrusions:** wristwatches, electric lights and sconces, glass windows, glass-chimney "oil lamps",
    flags, modern skylines, utility poles and wires, drainpipes, trousers under robes, tattoos, modern door handles.
  - **Anatomy:** extra arms, hands or legs; two people fused into one; figures that aren't quite human; floating
    objects; duplicate Jesus look-alikes.
  - **The edit model is literal.** Asked to remove a rooster from a lamp, it removed the girl holding the lamp.
    Re-check the whole image after every edit, not just the part you asked about.
  - **If an edit fights you twice, regenerate** with a composition that avoids the problem.
- **Log as you go:** for each chapter, the scenes, generations, edits and approximate GPU time, plus
  notable failures, in `~/halo-images/visual-bible/mark/metrics.md`, in the same format as John's `metrics.md`.

## Phase 1: plan (STOP for my review)

1. **Get the King James text for Mark from a reliable public-domain source. Don't write it from memory.**
   Check the verse counts: Mark has 16 chapters and 678 verses. Mark 16:9–20 is included in the KJV.
2. **Propose a scene list:** each scene's verse range, a title, and a one-line subtitle, as in John. Mark is
   shorter and faster-paced than John, so aim for roughly 60 to 75 scenes. Note which scenes use which cast
   reference, and any new recurring character that needs a portrait.
3. **Propose the site changes** (see Phase 3). **STOP and show me both before generating anything.**

## Phase 2: generate (chapter by chapter)

- Work through the chapters in order. For each: generate, QA, fix or regenerate, then write
  `site/mark/data/mark-NN.js` in the same format as John:
  `VB.add(<chapter>, {"scenes": [[from, to, "<png filename>", "title", "subtitle", trim0or1], ...], "v": [<every verse>]})`.
  The first scene of chapter 1 becomes the hero image.
- **After every 2 to 3 chapters,** show me a contact sheet of the accepted images (a small grid with verse labels)
  so I can catch anything by eye, and update the metrics log.
- **ComfyUI keeps its job history in memory and loses it on restart,** and the gallery builder needs that history.
  After each chapter, save a snapshot: `curl -s 'http://127.0.0.1:8188/history?max_items=5000' >
  ~/halo-images/visual-bible/mark/history-<timestamp>.json`.

## Phase 3: add Mark to the site

- **A new book page at `/mark`:** `site/mark/index.html`, copied from `site/bible/index.html` and adapted.
  - Title, hero text and labels become "The Gospel of Mark", with 16 chapters.
  - The chapter scripts must use **absolute** paths: `/mark/data/mark-NN.js`. Vercel serves `/mark` with no
    trailing slash, and relative paths broke John once.
  - Keep the collapsed Contents, the "Text + images / Images only" toggle, the cast section and the lightbox.
- **Navigation:** the site nav's "The book" becomes the two books, e.g. "John" (`/bible`) and "Mark" (`/mark`).
  Keep `/bible` working, since it's already shared. Update every page's nav: the story (via
  `scripts/build_story.py`'s template), making-of, under-the-hood, infographic, and both book pages.
- **Making-of:**
  - Extend `scripts/build_site_assets.py` to accept several `--book` data folders and record which book each
    image belongs to.
  - In `site/making-of/index.html`, replace the hard-coded `'John '` label with the book name, and add a
    John / Mark filter.
  - Let it read the saved history snapshots as well as the live `/history`, so a ComfyUI restart doesn't lose
    Mark's prompts.
- **Under the hood:** add Mark's numbers next to John's (scenes, attempts, GPU minutes, attempts per image),
  using `scripts/comfy_history_metrics.py`.
- **Story (`content/story.md`):** add a short, clearly marked section about Mark (what was different, what went
  wrong, new numbers), **written in my voice**:
  - plain, personal, first person
  - **no em dashes or en dashes anywhere**
  - no "it's not X, it's Y" lines, no marketing tone

  Put `[Brian: ...]` notes where you need my input, and don't invent personal details.
- **Preview locally** (`python3 -m http.server 8090 --directory site`) and check:
  - both book pages at `/bible`, `/bible/`, `/mark` and `/mark/`
  - no console errors, all images loading
  - the view toggle, the Contents section, and the making-of filters

## Phase 4: publish (STOP before pushing)

0. Run `python3 scripts/build_verse_index.py` so the new book's scenes appear in `site/index/v1/` (Inscripture
   reads this index). Add the book's site folder to `BOOKS` in that script first if it's new.

1. Summarize what changed and show me the contact sheet of all Mark images and the new story section. **STOP**
   and wait for my OK.
2. **Commit and push:**
   - Commit in `~/code/halo-visual-bible`. It's already configured with my GitHub noreply email; end commit
     messages with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
   - Push as my `btrzupek` GitHub account without switching the active `gh` account:
     `GH_TOKEN=$(gh auth token -u btrzupek) git -c credential.helper= -c "credential.helper=!gh auth git-credential" push origin main`
3. **After Vercel redeploys** (about 20 seconds), verify the live site at https://halo-visual-bible.vercel.app:
   `/mark`, `/bible`, the nav on every page, the making-of filters, and a sample of image URLs returning 200.

## Ground rules

- Don't use sudo, and don't change anything on halo except through the image tools.
- Don't download new models without asking me.
- Don't delete or rewrite John's images, data or history snapshots.
- Report honestly: failed generations, how many rerolls, anything you weren't sure about.
