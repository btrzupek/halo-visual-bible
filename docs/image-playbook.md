# Image playbook

How to get a usable scene out of FLUX.2 [klein] and Qwen-Image-Edit, and every failure that has
actually happened across ten books. Book-level detail is in each working folder's `worklog.md`.

## Prompt recipe

1. Start with `Cinematic film still` + place + time of day + light.
2. For a cast member: "The man from the reference image, <name>, <age and look>, in <clothing>" and
   pass the portrait as `reference_image`. Describe the look anyway; the reference drifts.
3. Say who else is in frame, how many, and what each is doing. Give every crowd member an action
   (bowing, hands raised); idle crowds invent phones and books in their hands.
4. Close with: `Shot on 35mm anamorphic lens, muted <tone> color grade, photorealistic, Iron Age
   clothing. Natural anatomy, each person with exactly two arms and two hands. No <the specific
   anachronisms this scene invites>, no modern objects, no text.`
5. Useful guards: "Only one king", "only one man in the foreground" (stops duplicates), "no one is
   near the chest", "bare feet in leather sandals".
6. Never put spoken dialogue in a prompt (it renders as subtitles). Never "well-dressed".

Portraits: 896x1152, chest-up, plain dark background, soft side light. For a character who ages,
generate each age with the previous portrait as the reference; an edit changes the face.

## QA checklist (zoom in, region by region)

- **Modern objects:** wristwatches, wristbands, eyeglasses, light switches, sconces, bulbs, downlights,
  glass windows and grilles, glass jars and bottles, glass-chimney lamps, candles, metal buckets and
  mugs, zippers, buttons, belt buckles, knitwear and sweaters, trousers under tunics, boots and socks,
  pens and paper, printed boxes, drainpipes, wires and utility poles, flags and banners, crosses.
- **Buildings:** distant cities become medieval castles or modern towns with tiled roofs; temples
  become Greek colonnades or the Parthenon. Keep cities to one plain wall or out of frame.
- **Text:** carved lettering on walls, altars and pedestals, often a misspelled place name.
- **Anatomy:** extra arms, a third hand, two right arms, three fingers, two heads, duplicate people,
  a person drawn twice facing themselves, two arks, two swords.
- **Objects the model can't draw:** Iron Age chariots (draws carts, buggies, covered wagons: frame
  so only the front rail shows, or keep it tiny); lyres (draws mandolins, lutes, banjos: describe
  "a flat frame of two curved arms and a crossbar, vertical strings, no neck, no frets"); stocks;
  a floating axe head (draws a block); parted water (draws a gravel spit or glass).
- **Rules from the constitution:** hands on the ark, a figure for God, blood, immodesty.

## Fixing

- One problem per edit. Asking for three things at once can erase the main subject (an edit
  removing two men and some poles erased David).
- The edit model is literal and has side effects: re-check the whole image after every edit.
- "Paint over the window with plain wall" works; "change the window" makes it worse.
- To fix a drifted face: `halo_edit_image(image=scene, reference_image=portrait,
  instruction="make the man in image 1 look like the man in image 2 ...")`.
- Qwen edits leave a pale strip on the bottom or right edge. Use `trim=1` in the pick. If a chain
  of edits has softened the image or left a wide strip, re-render: generate with klein using the
  edited image as `reference_image` and a prompt describing the same composition.
- If an edit fails twice, stop editing and regenerate with a composition that avoids the problem
  (change the moment in the text, the framing, or the camera height).
- Embraces: show as few hands as possible (one man seen from behind, the other's hands on his back).

## Throughput

- Submit a few jobs in parallel; long MCP waits are queue time, GPU time per job is unchanged.
- A generate batch of 4 to 6 plus one edit round per chapter group keeps the GPU busy about 75%.
- Expect roughly 2.2 attempts per published image on an Old Testament book, 1.5 when the book is
  mostly landscape and animals.
