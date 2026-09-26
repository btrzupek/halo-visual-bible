---
title: I illustrated the Gospel of John* on a box on my desk
description: 88 scenes over one evening and a morning, all generated locally on an AMD Ryzen AI Halo box and driven from a chat with Claude.
hero: halo_edit_00014_.webp
hero_caption: John 6:19. The fixed version. The first try had a third arm.
---

# I illustrated the Gospel of John\* on a box on my desk

<p class="byline">*And then I couldn't stop, so the rest of the Gospels+ are rolling out now too...</p>

<p class="byline">Brian Trzupek · September 2026</p>

I got my hands on one of AMD's Ryzen AI Halo boxes and wanted to see what it could actually do. Not a benchmark
first. A real project. So I picked something big enough to be a stress test and personal enough that I'd care how it
came out: a fully illustrated Gospel of John. All 21 chapters, every verse, with a picture for every scene.

It ended up being 88 scenes plus two character portraits, and every image was made on the box sitting on my desk.
No cloud image API, no credits, no upload of anything. I did it in one evening and finished it the next
morning. You can [read the whole book here](/bible).

<p class="cta"><a class="primary" href="/bible">Open the Visual Bible</a><a href="/making-of">See every attempt</a><a href="/under-the-hood">Code and numbers</a></p>

## The box

The Halo is AMD's developer platform for the Ryzen AI Max+ 395. 16 Zen 5 cores, a Radeon 8060S GPU with 40 compute
units, an NPU, and 128 GB of memory. Mine came with ComfyUI, ROCm, vLLM and Lemonade already installed, which
saved me a lot of setup.

For this kind of work the spec that matters most is the memory. The GPU only has 512 MB carved out as
"real" VRAM, but it can map about 94 GB of the system's memory. So a 20 billion parameter image editing model just...
loads. On an integrated GPU. Most desktop graphics cards can't do that.

## How I drove it

I don't want to sit in a node graph for hours. I want to talk to it. So the setup is:

- Claude on my Mac (Desktop and Claude Code)
- a small MCP server I had Claude Code build, so Claude can call tools like `halo_generate_image` and `halo_edit_image`
- an SSH tunnel to the box, because ComfyUI only listens locally over there
- ComfyUI on the Halo doing the actual work

In practice that means I say "give me John the Baptist at the Jordan, pointing at Jesus walking toward him" and a
picture shows up in the chat about 15 seconds later. If something's off, I say "fix his hand" and it does.

Getting the plumbing right took a few rounds. The fun ones:

- The latest version of the MCP Python library renamed the class the server was built on, so the first install just
  broke. Pinned it and moved on.
- My first tunnel was a normal `ssh -L` kept alive by launchd. macOS decided it wasn't important enough to restart
  when it dropped. The fix was to let launchd own the port and start a fresh `ssh -W` for every connection. It's been
  solid since.
- The box only came with one image model. Claude went and found the right model files straight out of ComfyUI's own
  templates on the box, and pulled down about 60 GB of them, checksummed, while I got on with other stuff.

## Keeping the faces straight

Making one pretty picture is easy now. Getting the same guy to show up in 88 of them is the hard part.

What worked was simple. First I had two portraits generated, one of Jesus and one of John the Baptist. Then every
scene with either of them used that portrait as a reference image. FLUX.2 klein can take a reference and put the
same face in a completely new scene, no training required. It costs about twice as long per image (15 seconds
instead of 8), and it's worth it.

<div class="pair">
<img src="/images/full/halo_klein_00006_.webp" alt="Portrait of Jesus used as the reference image">
<img src="/images/full/halo_klein_00007_.webp" alt="Portrait of John the Baptist used as the reference image">
<figcaption>The two reference portraits. Every scene with either of them started from one of these.</figcaption>
</div>

## The stuff AI gets wrong about the first century

This was the funniest part. The models are great at "cinematic ancient Jerusalem at dusk". They are bad at
remembering that nobody in AD 30 had a wristwatch.

Claude checked every image before showing it to me and rerolled or edited anything off. It caught most things.
The running tally of what got fixed:

- wristwatches (about 10 of them)
- electric lights and wall sconces (8)
- trousers under the robes (8)
- glass windows, modern skylines, a utility pole, drainpipes, and three flags
- a tattoo on a disciple's forearm
- extra arms and hands (5), one figure with three legs, and a couple of floating objects
- a spiky glowing halo where there should have been a crown of thorns
- and my favorite: "oil lamp" kept coming back as a glass-chimney kerosene lamp. Three times.

<figure class="pair">
<img src="/images/full/halo_klein_ref_00044_.webp" alt="First attempt: the figure walking on the water has three arms">
<img src="/images/full/halo_edit_00014_.webp" alt="After one edit: two arms">
<figcaption>John 6:19, walking on the water. Left: the first try, with a bonus arm. Right: one edit later, 53 seconds.</figcaption>
</figure>

The edits were done with Qwen-Image-Edit. You just tell it what to change in plain English. "The man walking on the
water must have exactly two arms." "Remove the wristwatches from the two men on the right." It's scary good at
that. It is also very literal. In Peter's denial scene there was a rooster sitting on top of the servant girl's
lamp. I asked it to take the rooster off the lamp. It removed the girl. That one I ended up regenerating from
scratch, and she's back in the book now.

<figure class="pair">
<img src="/images/full/halo_klein_00020_.webp" alt="Before: a rooster perched on the servant girl's lamp">
<img src="/images/full/halo_edit_00049_.webp" alt="After: the girl is gone and the rooster moved to a wall">
<figcaption>John 18. I asked it to remove the rooster. It removed the girl and kept the rooster.</figcaption>
</figure>

Claude's checks caught most of it, but not everything. A couple I caught just by looking at the pages. In the
arrest in the garden, one of the soldiers knocked to the ground wasn't really a person. Some armor, a face, and
then... something else. And in the scourging, Jesus had three legs. On a phone you'd scroll right past both. On a
big screen they jump out at you. Each one took a single edit to fix, under a minute apiece.

<figure class="pair">
<img src="/images/full/halo_klein_ref_00088_.webp" alt="Before: one of the fallen soldiers on the right is not quite human">
<img src="/images/full/halo_edit_00039_.webp" alt="After: two normal fallen Roman soldiers">
<figcaption>John 18:6, "they went backward, and fell to the ground." Left: the soldier on the right is not a person. Right: fixed.</figcaption>
</figure>

Chapters 19 and 20 were the hardest. Anatomy under strain is where these models fall apart, and the crucifixion
scenes needed the most passes. Thomas and the wounds took four edits and a fresh start, because the edit model kept
moving the nail wound onto Thomas's hand instead of Jesus's. Lesson learned: if an edit fights you twice, regenerate
with a composition that avoids the problem.

## The numbers

I had Claude go back through ComfyUI's own job history and then run a proper benchmark with power sampling, because
I wanted real numbers.

| | |
|---|---|
| Images in the book | 88 scenes + 2 portraits |
| Total attempts | 168 (103 reference shots, 18 plain, 47 edits) |
| Attempts per published image | 1.87 |
| GPU time for the whole book | 68 minutes |
| One scene (klein, 1344x768, 4 steps) | 8.6 s, or 15.7 s with a reference face |
| One edit (Qwen-Image-Edit) | 32 s warm, 54 s right after switching models |
| Power | 31 W idle, about 156 W flat out |
| Energy per scene | about 0.3 to 0.6 Wh |
| Electricity for the entire book | about 0.18 kWh. Call it 3 cents. |

A few things jumped out at me:

**The GPU was busy less than half the time.** 68 minutes of GPU work over about two and a half hours of actual
session. The rest was writing prompts, looking at pictures, and me deciding what I actually wanted.

**Switching models is the real tax.** Every time I went from generating to editing and back, ComfyUI had to load the
other model. Each one got loaded 27 times. A warm edit is 32 seconds. An edit right after a generate is 54.

**It runs hot and it doesn't care.** Back to back edits pushed the GPU to 100 °C and the package sat at about
156 W. The clock speed dropped less than 1%. It hits its power limit and just sits there.

**The cloud would've been cheap too.** The same 240 or so calls on hosted image APIs would run somewhere between $7
and $32 depending on the model. So for me the win wasn't the money. I could reroll as much as I wanted
without watching a meter, nothing left my house, and I kept every full resolution file.

## Part two: the Gospel of Mark

The next evening I did the Gospel of Mark the same way. 16 chapters, 678 verses, 75 scenes. Mark is shorter than
John and it moves fast, so the scenes do too. You can [read it here](/mark).

<p class="cta"><a class="primary" href="/mark">Open Mark</a><a href="/making-of">See every attempt</a></p>

A few things were different this time.

**The box had other work to do.** Mark ran under a harder test than John. The whole time it was running, I had a
separate workflow going on the same box with three AI coding agents working at once. So the image models were
sharing the machine with them from the first picture to the last.

**Same Jesus, two new faces.** I reused the Jesus and John the Baptist portraits from John, so it's the same Jesus
in both books. Mark leans hard on Peter, and it ends with Mary Magdalene at the cross, at the tomb and in the
garden. So I had Claude make one portrait of each and use them as the reference in the scenes where they're the
main figure.

<div class="pair">
<img src="/images/full/halo_klein_00026_.webp" alt="Portrait of Simon Peter used as a reference image">
<img src="/images/full/halo_edit_00051_.webp" alt="Portrait of Mary Magdalene used as a reference image">
<figcaption>The two new portraits for Mark: Peter and Mary Magdalene.</figcaption>
</div>

**The text got checked first.** Claude pulled the King James text from two separate public domain datasets and
compared them verse by verse before anything got drawn. All 678 verses matched word for word.

**I mostly let it run.** I approved the scene list up front, and then Claude generated, checked, fixed, and sent me
a contact sheet every few chapters.

### What went wrong this time

The checking was a lot stricter on Mark. Instead of looking at the whole picture, Claude zoomed into every image a
piece at a time. That caught a lot more. Only 10 of the 75 scenes were keepers on the very first try. On John it was
closer to half.

The new ones I hadn't seen before:

- **A subtitle.** Claude put a line of dialogue in a prompt ("whose is this image?") and the model burned it into
  the bottom of the picture like a movie caption. Misspelled. Lesson: never put spoken lines in a prompt.
- **Modern cities in the distance.** Any prompt with a town in the background got a modern one. The triumphal
  entry came back with today's Jerusalem skyline, gold Dome of the Rock and apartment blocks included. Gethsemane
  got electric city lights across the valley. The fix every time was to frame the shot so there's no distance to
  fill.
- **Counting.** Ask for seven baskets, get four. Ask for three crosses, get two. For the baskets Claude just renamed
  the scene instead of fighting it.
- **Sunglasses.** One prompt asked for phylacteries on a Pharisee's forehead. The model gave him sunglasses.
- And the usual suspects: lots of trousers, eyeglasses in a crowd, a briefcase, a light switch, an asphalt road with
  a painted center line, and a man lying on a mat with a head at each end.

<figure class="pair">
<img src="/images/full/halo_klein_ref_00215_.webp" alt="Before: a garbled subtitle burned into the bottom of the image">
<img src="/images/full/halo_edit_00070_.webp" alt="After: the subtitle removed">
<figcaption>Mark 12:13-17. Left: the prompt had a line of dialogue in it, so the model added a subtitle. Right: one edit later.</figcaption>
</figure>

<figure class="pair">
<img src="/images/full/halo_klein_ref_00205_.webp" alt="Before: the triumphal entry with the modern Jerusalem skyline behind">
<img src="/images/full/halo_klein_ref_00206_.webp" alt="After: the same scene on a country road with no city in view">
<figcaption>Mark 11:1-11. Left: the Dome of the Rock and apartment blocks. Right: take the city out of the shot.</figcaption>
</figure>

The edit model is still very literal. Asked to swap a fedora for a head cloth on one man far in the background, it
put the head cloth on a Pharisee in the front and made the fedora sharper. Six of the 28 edits on Mark made things
worse and got thrown out.

And one got past everybody until I looked at the live site myself. In Mark 3 the man whose withered hand has just
been healed is holding it up for everyone to see, and it only had four fingers. Of all the hands to get wrong. One
edit fixed it.

<figure class="pair">
<img src="/images/full/halo_klein_ref_00139_.webp" alt="Before: the healed hand has a thumb and only three fingers">
<img src="/images/full/halo_edit_00079_.webp" alt="After: the healed hand has a thumb and four fingers">
<figcaption>Mark 3:1-6, "stretch forth thine hand." Left: four fingers, counting the thumb. Right: five.</figcaption>
</figure>

One new annoyance on the plumbing side: every single edit timed out on the Mac end, even though it finished fine
on the box. Claude worked around it by pulling the finished image straight from ComfyUI. The cause was on the MCP
side: the client gives up on a request after about a minute, and when it gave up, the server stopped watching the
job, so the picture never made it back to my Mac. That's fixed now. Every job gets watched in the background until
its image is saved, and a call that runs long comes back with a job id that Claude picks up a moment later.

### Mark by the numbers

| | John | Mark |
|---|---|---|
| Scenes | 88 | 75 |
| New portraits | 2 | 2 |
| Total attempts | 168 | 189 (160 generations, 29 edits) |
| Attempts per published image | 1.87 | 2.45 |
| GPU time | 68 minutes | 99 minutes |
| Session length | about 2.5 hours | about 2.9 hours |

Mark took more attempts per picture than John even though it's the shorter book. Most of that is the stricter
checking. Each picture was also slower. A typical scene took 22 seconds instead of 16, and a typical edit took 92
seconds instead of 53. Most likely that's the three coding agents sharing the box. Given that, I think Mark went
really well.

## Part three: the Gospel of Luke

Then Luke. 24 chapters, 1,151 verses, 103 scenes. It's the longest one yet, and at this point I want to do all four
Gospels. You can [read it here](/luke).

<p class="cta"><a class="primary" href="/luke">Open Luke</a><a href="/making-of?book=Luke">See every attempt</a></p>

This time the box had nothing else to do. I had just rebooted it to clear out dozens of orphaned Chromium sessions
that were eating memory, and no coding agents were running. That made Luke a good control for Mark. A typical scene
took 17 seconds, right back near John's 16, and a typical edit took 57 seconds instead of Mark's 92. So the slowdown
on Mark really was the three agents sharing the box.

One housekeeping note from the box itself. The orphaned Chromium processes didn't come back this run. But a python3
process that belongs to ComfyUI hung around after I closed ComfyUI properly, still holding onto 2.4 GB of memory. The
only way I've found to get the machine back to a clean state for the next run, whatever I'm doing next, is a full
restart.

**The timeout is fixed.** On Mark every single edit "timed out" on my Mac even though it finished on the box. Before
starting Luke, Claude rewrote that part of the MCP server so each job is watched in the background until its image
is saved, and a call that runs long comes back with a job id instead of an error. Luke had 60 edits. Not one of them
timed out.

**One new face.** Luke opens with two chapters of birth stories, so Mary, the mother of Jesus, got her own portrait.
Jesus, John the Baptist, Peter and Mary Magdalene carried over from John and Mark.

<div class="pair">
<img src="/images/full/halo_klein_00039_.webp" alt="Portrait of Mary, the mother of Jesus, used as a reference image">
<img src="/images/full/halo_edit_00080_.webp" alt="Luke writing on a scroll by the light of a small clay oil lamp">
<figcaption>Left: the new reference portrait of Mary. Right: the opening of Luke. The first try gave him a yellow pencil.</figcaption>
</div>

**Parables look different now.** Luke is full of parables: the Good Samaritan, the prodigal son, the lost sheep,
Lazarus at the rich man's gate. Those are stories Jesus tells, not things that happened in front of the disciples,
and I wanted the pictures to say so. So parable scenes get a soft, blurry edge, the way a movie shows a dream or a
flashback, plus a small "A parable" label. It's done in the page itself, not baked into the images, so it can be
tuned later. Mark's two parable scenes got it too.

<figure>
<img src="/images/full/halo_klein_00077_.webp" alt="The prodigal son's father embracing his returning son">
<figcaption>Luke 15:11-24, the prodigal son. On the book page this one has the soft parable edge.</figcaption>
</figure>

### What went wrong this time

Same story as Mark: 20 of 103 scenes were keepers on the first try. The new ones:

- Luke's reed pen came back as a **yellow pencil**.
- "A well-dressed publican" got a **modern overcoat and a necktie**. Describe the actual clothes, never "well-dressed".
- Jesus at Emmaus had a **wedding ring**, and in another scene a **wristwatch**. Again.
- Babies are trouble. Every time someone held a baby, somebody grew a third hand.
- Every scene with Jerusalem in the distance came back with modern apartment blocks. The fix is still the same: keep the city out of the shot.
- The crucifixion was the hardest. With the Jesus portrait as the reference, the model kept standing him in front of
  the cross, fully dressed, chatting with the thief. It only worked with no reference at all and the three crosses in
  silhouette.
- My favorite edit fail: asked to swap an old man's flat cap for a prayer shawl, it gave him a **blue baseball cap** instead.

### Luke by the numbers

| | Mark | Luke | John |
|---|---|---|---|
| Scenes | 75 | 103 | 88 |
| Total attempts | 189 | 254 (194 generations, 60 edits) | 168 |
| Attempts per published image | 2.45 | 2.44 | 1.87 |
| Typical scene | 22 s | 17 s | 16 s |
| Typical edit | 92 s | 57 s | 53 s |
| GPU time | 99 minutes | 108 minutes | 68 minutes |
| Other work on the box | three coding agents | none | none |

## Part four: the Gospel of Matthew

And now Matthew. 28 chapters, 1,071 verses, 111 scenes, which makes it the biggest book so far. With Matthew done,
all four Gospels are up. You can [read it here](/matthew).

<p class="cta"><a class="primary" href="/matthew">Open Matthew</a><a href="/making-of?book=Matthew">See every attempt</a></p>

Before starting, the box was checked and came back clean: only ComfyUI running, no language model loaded, half a
gigabyte of GPU memory in use, and no coding agents. So Matthew is a second quiet run to compare with Luke, and the
numbers lined up almost exactly. A typical scene took 16.7 seconds (Luke 16.8) and a typical edit took 57.0 seconds
(Luke 57.0). The whole book took 91 minutes of GPU time over about two and a half hours.

**It got easier.** 38 of the 111 scenes were keepers on the very first try, against 20 of 103 for Luke and 10 of 75
for Mark. Matthew needed 1.94 attempts per published image, the best since John. Nothing about the box changed. The
prompts did. By now there is a long list of things that don't work (no quoted speech, no distant cities, never
"well-dressed", keep babies out of people's arms) and every prompt started from it.

**One new face.** Matthew's first two chapters follow Joseph, so he got his own portrait. It came out right on the
first try, and he carries the dream, the flight into Egypt and the move to Nazareth.

<div class="pair">
<img src="/images/full/halo_klein_00095_.webp" alt="Portrait of Joseph, used as a reference image">
<img src="/images/full/halo_edit_00141_.webp" alt="Joseph asleep as the angel of the Lord speaks to him in a dream">
<figcaption>Left: the new reference portrait of Joseph. Right: Matthew 1:18-25, the dream. The first try gave him a grey sock and a pillow that looked like a roll of paper towels.</figcaption>
</div>

**More parables.** Matthew has 14 parable scenes, and they all get the soft dream edge from Luke. I also marked the
sheep and the goats in chapter 25 as a parable. It's more of a picture of the judgment than a story, but it's told
the same way the others are, so it gets the same treatment.

<figure>
<img src="/images/full/halo_klein_00144_.webp" alt="A shepherd standing between a flock of sheep and a herd of goats">
<figcaption>Matthew 25:31-46, the sheep and the goats. Kept on the first try.</figcaption>
</figure>

### What went wrong this time

- **Eyeglasses.** A scribe, a face in a crowd, the elder paying off the guards, and one of the disciples at the very
  last scene. When I asked the edit model to take that last pair off, it took off the man's whole head. The second
  try put glasses on a different man. Rerolling the same seed with "weathered bare faces" in the prompt finally fixed it.
- The wristwatches are back: on Jesus, on Matthew at the tax booth, on a wedding guest, and on Judas.
- The bridegroom in the parable of the ten virgins showed up in a **black suit**. And there were six virgins, not ten.
- The wedding feast "in the days of Noah" came with **electric string lights** over the tables.
- Golgotha means "the place of a skull", and the model drew a **giant skull** on the hill.
- I slipped and put a spoken line ("thou hast said") in a prompt, and it came back burned into the picture as a
  subtitle again: "Thn Ihestsid".

<div class="pair">
<img src="/images/full/halo_edit_00192_.webp" alt="A failed edit: the disciple whose glasses were to be removed has no head">
<img src="/images/full/halo_klein_ref_00494_.webp" alt="The risen Jesus on a mountaintop at sunrise with his arms outstretched over his kneeling disciples">
<figcaption>Matthew 28:16-20, the last scene of the book. Left: the edit that removed a pair of glasses by removing the head. Right: the reroll that made it in.</figcaption>
</div>

### Matthew by the numbers

| | Matthew | Mark | Luke | John |
|---|---|---|---|---|
| Scenes | 111 | 75 | 103 | 88 |
| Total attempts | 217 (163 generations, 54 edits) | 189 | 254 | 168 |
| Attempts per published image | 1.94 | 2.45 | 2.44 | 1.87 |
| Kept on the first try | 38 | 10 | 20 | about half |
| Typical scene | 17 s | 22 s | 17 s | 16 s |
| Typical edit | 57 s | 92 s | 57 s | 53 s |
| GPU time | 91 minutes | 99 minutes | 108 minutes | 68 minutes |
| Other work on the box | none | three coding agents | none | none |

## Part five: the Acts of the Apostles

After the four Gospels I kept going into Acts. 28 chapters, 1,007 verses, 98 scenes. It's a different kind of book:
the story moves from Jerusalem out to Samaria, Damascus, Antioch, Athens, Ephesus, a shipwreck and finally Rome, and
most of it follows one man. You can [read it here](/acts).

<p class="cta"><a class="primary" href="/acts">Open Acts</a><a href="/making-of?book=Acts">See every attempt</a></p>

Because it's long, I had Claude work through it in four chunks (chapters 1 to 7, 8 to 12, 13 to 20 and 21 to 28)
and post a contact sheet after each one. On the site it's still one book.

**The cast came first.** Before a single scene, Claude read through the whole book to work out who comes back, so the
faces wouldn't drift. Paul is in 45 of the 98 scenes, from the young man holding the coats at Stephen's stoning to the
house in Rome. So Paul got a portrait, and so did John, Stephen, Barnabas, Silas and Philip. Peter, Mary and Jesus
carried over from the Gospels. The box was quiet again for this run, nothing else on it.

<div class="pair">
<img src="/images/full/halo_klein_00155_.webp" alt="Portrait of Paul, used as a reference image">
<img src="/images/full/halo_edit_00212_.webp" alt="Saul fallen on the road to Damascus in a blinding light from heaven">
<figcaption>Left: the new reference portrait of Paul. Right: Acts 9:1-9, the road to Damascus. The first try put everyone in cargo shorts and hiking boots.</figcaption>
</div>

**Two new tricks.** The image model can only take one reference portrait at a time, which is a problem when Paul and
Barnabas are in the same scene. It turns out the edit model can take a second image. So when a face drifted, Claude
ran an edit that said, in effect, make this man look like the man in the portrait. That fixed Paul's face in three
scenes. The other trick was about windows. On every book so far, asking the edit model to change a window made it
worse. Asking it to paint over the window with plain wall worked every time.

<div class="pair">
<img src="/images/full/halo_klein_ref_00539_.webp" alt="Barnabas bringing Saul to the apostles, with Saul's face not matching his portrait">
<img src="/images/full/halo_edit_00215_.webp" alt="The same scene after an edit that used Paul's portrait to fix his face">
<figcaption>Acts 9:26-31, Barnabas brings Saul to the apostles. Left: the man in the middle doesn't look like Paul. Right: the same image after an edit with Paul's portrait as a second image.</figcaption>
</div>

**Visions get the dream edge.** Acts has no parables, but it has visions: Peter's sheet full of animals, the man of
Macedonia, and the Lord standing by Paul at night in Corinth. Those three get the same soft edge as the parables,
labeled "A vision".

<figure>
<img src="/images/full/halo_klein_ref_00544_.webp" alt="Peter kneeling on a rooftop as a great sheet full of animals comes down from the sky">
<figcaption>Acts 10:9-16, Peter's vision on the housetop. The first try printed the animals on the sheet like fabric.</figcaption>
</figure>

### What went wrong this time

- The wristwatches never stop. Agabus, Demetrius the silversmith, Julius the centurion and a guard all had one. Paul got a gold ring.
- Bernice, sitting next to King Agrippa, came out as a bearded man.
- The tongues of fire on the disciples at Ephesus turned into candles sticking out of their heads. Pentecost's flames in chapter 2 worked the first time.
- When Eutychus falls from the window, the model fused him and Paul into one body with a head at each end.
- The shipwreck ship came out as a 17th-century galleon, so the final picture shows only the wreckage in the surf.
- The model can't draw the stocks at Philippi. It tried posts, then had the men sitting on the beam, then had their feet resting on top of it. So that scene is retitled with the slave girl's words, "These men are the servants of the most high God".

<div class="pair">
<img src="/images/full/halo_klein_ref_00606_.webp" alt="Paul before King Agrippa, with Bernice drawn as a bearded man">
<img src="/images/full/halo_edit_00258_.webp" alt="The same scene after an edit, with Bernice as a woman">
<figcaption>Acts 26:1-23, Paul before Agrippa. Left: Bernice, center, as drawn. Right: after one edit.</figcaption>
</div>

### Acts by the numbers

| | Acts | Matthew | Mark | Luke | John |
|---|---|---|---|---|---|
| Scenes | 98 | 111 | 75 | 103 | 88 |
| New portraits | 6 | 1 | 2 | 1 | 2 |
| Total attempts | 234 (162 generations, 72 edits) | 217 | 189 | 254 | 168 |
| Attempts per published image | 2.25 | 1.94 | 2.45 | 2.44 | 1.87 |
| Typical scene | 17 s | 17 s | 22 s | 17 s | 16 s |
| Typical edit | 57 s | 57 s | 92 s | 57 s | 53 s |
| GPU time | 115 minutes | 91 minutes | 99 minutes | 108 minutes | 68 minutes |
| Other work on the box | none | none | three coding agents | none | none |

## Try it

Everything is on [GitHub](https://github.com/btrzupek/halo-visual-bible): the MCP server, the ComfyUI workflows, the tunnel setup, the book viewer,
and the scripts that pulled these numbers. The [under the hood](/under-the-hood) page has the full hardware and
benchmark breakdown, and [making of](/making-of) has every single attempt with the exact prompt, including all
the wristwatches.

Next up will be integrating this into my agentic coding workflows.

IF you made it this far! You are amazing. Thanks for the read. I will keep you posted on my next test and workflow. This box is incredible, thank you @AMD!
