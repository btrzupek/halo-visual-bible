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

## Part six: the Book of Genesis

Then I went back to the beginning. Genesis is 50 chapters, 1,533 verses and 89 scenes, from the first light to
Joseph's death in Egypt. This one I handed off completely: I answered a few questions, told Claude to publish it when
it was done, and went to bed. It ran on the box overnight and was live by the morning. You can [read it here](/genesis).

<p class="cta"><a class="primary" href="/genesis">Open Genesis</a><a href="/making-of?book=Genesis">See every attempt</a></p>

**A new cast.** None of the Gospel faces belong in Genesis, so it got eleven portraits of its own: Adam, Eve, Noah,
Abraham, Sarah, Isaac, Rebekah, Jacob, Esau, Rachel and Joseph. Eight of them came out right on the first try.

**The questions I answered before bed.** How to show Adam and Eve, how to handle the hard chapters (Lot's daughters, Dinah, Tamar,
Potiphar's wife, all shown with nothing sexual in the picture). And how to show God. The answer was light only,
never a figure: a shaft of light over the deep, a glow moving through the garden, a column of light beside Hagar at
the spring. The three men at Mamre and the man who wrestles Jacob are shown as men, because that is what the text
calls them.

**Then I changed my mind about Eden.** Before bed I had picked the option that kept Adam and Eve clothed the whole way
through, and when I looked at the result it was wrong. The text makes a point of it: they were naked and not ashamed, then after the
fall they hid and sewed fig leaves, and only then did God make them coats of skins. That progression is the story,
so the pictures need to show it. Now they are unclothed silhouettes on the first morning, a figure seen from behind
in the garden, Eve at the tree with her hair falling over her, the two of them hiding behind a tree with fig leaves,
and finally simple skin wraps as they leave. Each of the five fixes was an edit of the published picture, and every
one worked on the first try.

<div class="pair">
<img src="/images/full/halo_edit_00290_.webp" alt="Two small unclothed silhouettes of a man and a woman on a hill against a vast sunrise over an untouched valley">
<img src="/images/full/halo_klein_ref_00658_.webp" alt="Jacob asleep on a stone as a stairway of light rises into the sky with figures ascending and descending">
<figcaption>Left: Genesis 1:26-31, the first try gave me a modern couple in khakis. Right: 28:1-22, Jacob's ladder, which gets the dream edge as a vision.</figcaption>
</div>

**It was the easiest book yet.** 57 of the 89 scenes were keepers on the first try, and it took 1.53 attempts per
published image, the lowest of any book. The whole thing was 53 minutes of GPU time. Part of that is Genesis
itself: a lot of it is sky, sea and animals, and the model draws a flood or a rainbow or a sky full of stars without
anything to get wrong. The rest is the list of lessons from the other five books, which every prompt now starts from.

<figure>
<img src="/images/full/halo_edit_00282_.webp" alt="Jacob wrestling with a stranger on the river stones at dawn">
<figcaption>Genesis 32:22-32, Jacob wrestles until the breaking of the day.</figcaption>
</figure>

### What went wrong this time

- Babies, again. Twice a baby came out with two heads, and once there were two babies where the text has one. The fix is the same as in Luke: lay the baby down.
- The same person drawn twice, facing themselves. It happened to Hagar and to Jacob. "Only one man in the frame" fixed it.
- The cherubim guarding Eden came out as nude statues, and Adam was wearing jeans.
- Sodom came out as a modern city skyline on fire. Keeping the city out of the shot fixed it, same as in every Gospel.
- An elephant crossed with a giraffe walking up the ramp into the ark, and a stovepipe chimney on the ark's roof.
- In the first try at Genesis 41, Joseph was putting the gold chain on Pharaoh instead of the other way around.

<div class="pair">
<img src="/images/full/halo_klein_00216_.webp" alt="A failed image: the cherubim at Eden drawn as nude statues">
<img src="/images/full/halo_edit_00294_.webp" alt="Adam and Eve in simple hide wraps walking out of Eden as two cherubim of light and a flaming sword guard the gate">
<figcaption>Genesis 3:14-24. Left: the first try. Right: the version in the book.</figcaption>
</div>

### Genesis by the numbers

| | Genesis | Acts | Matthew | Mark | Luke | John |
|---|---|---|---|---|---|---|
| Scenes | 89 | 98 | 111 | 75 | 103 | 88 |
| New portraits | 11 | 6 | 1 | 2 | 1 | 2 |
| Total attempts | 153 | 234 | 217 | 189 | 254 | 168 |
| Attempts per published image | 1.53 | 2.25 | 1.94 | 2.45 | 2.44 | 1.87 |
| Kept on the first try | 57 | 13 | 38 | 10 | 20 | about half |
| GPU time | 53 min | 115 min | 91 min | 99 min | 108 min | 68 min |

## Part seven: 1 and 2 Samuel

Next came 1 and 2 Samuel, and this time I asked for one person to grow old on the page. They are two books on the site,
55 chapters and 78 scenes between them, and they follow David from the shepherd boy Samuel anoints to the old king
buying a threshing floor for an altar. You can read [1 Samuel](/1samuel) and [2 Samuel](/2samuel).

<p class="cta"><a class="primary" href="/1samuel">Open 1 Samuel</a><a href="/2samuel">Open 2 Samuel</a><a href="/making-of?book=1%20Samuel">See every attempt</a></p>

**David at four ages.** A single portrait would not work for a man who is a boy in one chapter and an old king forty
years later. So David has four: the shepherd, the young man on the run from Saul, the king, and the old king. The
first try at aging him was an edit of the boy's portrait, and it failed. His eyes turned blue and he started to look
like the Jesus portrait from John. What worked was generating each age with the one before it as the reference
image, so the face grows older instead of turning into someone else. The king and the old king both came out right
on the first try that way. Samuel, Saul, Jonathan, Joab and Absalom each have one portrait.

<div class="pair">
<img src="/images/full/halo_klein_00244_.webp" alt="Portrait of David as a shepherd youth">
<img src="/images/full/halo_klein_ref_00700_.webp" alt="Portrait of David as an old king">
<figcaption>The first and last of David's four portraits. Each one was generated from the one before it.</figcaption>
</div>

**The ark became a cast member.** The ark of the covenant shows up in a lot of these chapters, and the first pass drew it
differently almost every time. I asked for it to get a reference image like the people do, and I looked at that
reference before anything else was redone. Then I added a rule: nobody touches the ark. The text is clear about
this (it is why Uzzah dies in 2 Samuel 6), so the only hands on it in either book are his, and the Levites carrying
it by the poles.

**This time I reviewed before it went live.** For Genesis I let it publish on its own. For these two I asked Claude to
stop before pushing, and I went through 1 Samuel on my own machine while the 2 Samuel pictures were still being made.
My first list had about a dozen things on it; the second round found more. Hands that were too long, two right arms
on one man, a robe draped over two people at once, Samuel standing too close to the ark, and priests with two heads.
The two headed priests never did get fixed by edit. In the end they were replaced with the robes and spears they left
behind on the field. A third pass, after both books were done, still found extra arms on four people, a giant with two
heads, and a hand with three fingers.

### What went wrong this time

- Instruments. The model draws "lyre" as a mandolin, a lute or a banjo nearly every time. Describing the frame in words (two curved arms, a crossbar, no neck, no frets) fixed it, or an edit did.
- A chariot for Absalom that looked like a golf cart with a canopy, with a fedora and pith helmets in the crowd.
- Eyeglasses on two of David's men, and an asphalt road with a white line down the middle for Joab.
- An angel of the LORD holding a sword in each hand when the text gives him one.
- Dagon needed to read as a rigid stone statue. He is one now, face down before the ark with his head broken off on the threshold.

<div class="pair">
<img src="/images/full/halo_klein_ref_00781_.webp" alt="A failed image: Absalom in a canopied chariot that looks like a golf cart, with a fedora and pith helmets in the crowd">
<img src="/images/full/halo_edit_00363_.webp" alt="Absalom in a chariot with horses and runners before him">
<figcaption>2 Samuel 15:1-12. Left: the first try. Right: the version in the book.</figcaption>
</div>

### Samuel by the numbers

| | 1 Samuel | 2 Samuel | Genesis | Acts |
|---|---|---|---|---|
| Scenes | 41 | 37 | 89 | 98 |
| New portraits | 9 | 2 | 11 | 6 |
| Total attempts | 140 | 98 | 153 | 234 |
| Attempts per published image | 2.80 | 2.51 | 1.53 | 2.25 |
| Kept on the first try | 8 | 7 | 57 | 13 |
| GPU time | 68 min | 51 min | 53 min | 115 min |

1 Samuel took the most attempts per image of any book so far, and most of that was the two review rounds.

## Part eight: 1 Kings

After Samuel I asked for the Kings, one book at a time, each reviewed before it goes live. 1 Kings is 22 chapters and
37 scenes, from David's last days to Ahab dying in his chariot at Ramothgilead. You can [read it here](/1kings).

<p class="cta"><a class="primary" href="/1kings">Open 1 Kings</a><a href="/making-of?book=1%20Kings">See every attempt</a></p>

**The cast.** David carries over as the old king for the first two chapters. Solomon has two portraits, young and
old, the second made from the first the same way David aged across Samuel. Then Jeroboam, Ahab, Jezebel, and the
two prophets, Elijah and Elisha. Elisha is bald, because 2 Kings says so.

**Ark scenes need a moment of rest.** The ark comes into Solomon's temple in chapter 8, and every attempt to show the
priests carrying it put someone's hands on the chest. The text gives another moment: the priests set it down under
the wings of the cherubim and then could not stand to minister because the cloud filled the house. That is the
picture now, with the priests backing away and nobody near the ark.

<div class="pair">
<img src="/images/full/halo_klein_ref_00815_.webp" alt="The ark of the covenant at rest beneath two great golden cherubim as the cloud fills the room and priests back away bowing">
<img src="/images/full/halo_edit_00405_.webp" alt="Fire falling from heaven onto Elijah's altar on Mount Carmel as the people fall on their faces">
<figcaption>Left: 1 Kings 8:1-11, the cloud fills the house. Right: 18:21-40, the fire of the LORD falls on Carmel.</figcaption>
</div>

### What went wrong this time

- The model cannot draw an Iron Age chariot. It drew a handcart, a buggy with a seat, and a covered wagon. Ahab's last scene is framed so only the chariot's front rail shows.
- The great cherubim in the temple came out as nude Greek statues until I described them in long robes.
- A factory with two smokestacks on the hill behind Solomon's idol altar, and ceiling downlights over his ivory throne.
- Men at Bethel holding phones and little books while they bowed to the golden calf.
- Every prophet at Ahab's gate wore a Viking horned helmet. The text gives iron horns to one of them.

### 1 Kings by the numbers

| | 1 Kings | 2 Samuel | 1 Samuel |
|---|---|---|---|
| Scenes | 37 | 37 | 41 |
| New portraits | 7 | 2 | 9 |
| Total attempts | 96 | 98 | 140 |
| Attempts per published image | 2.18 | 2.51 | 2.80 |
| Kept on the first try | 6 | 7 | 8 |
| GPU time | 41 min | 51 min | 68 min |

## Part nine: 2 Kings

2 Kings is 25 chapters and 36 scenes, from Elijah taken up in the whirlwind to the temple burning and a captive king
eating at the table of the king of Babylon. You can [read it here](/2kings).

<p class="cta"><a class="primary" href="/2kings">Open 2 Kings</a><a href="/making-of?book=2%20Kings">See every attempt</a></p>

**The cast.** Elijah and Elisha carry over from 1 Kings, and Elisha gets an older portrait made from his younger one,
since he is an old man on his deathbed by chapter 13. The new faces are Jehu, Hezekiah and Josiah.

**Castles everywhere.** The model has one idea of an ancient city seen from a distance, and it is a medieval castle
with towers and a flag. When an edit took the castle out, it often put a hillside town with red tile roofs in its
place. Most of the fixes in this book were pulling cities out of the background, or reframing so the city was a
single plain wall.

<div class="pair">
<img src="/images/full/halo_klein_ref_00848_.webp" alt="Elijah taken up in a whirlwind of fire with horses of fire as Elisha cries out below">
<img src="/images/full/halo_edit_00454_.webp" alt="The temple in Jerusalem burning at night as captives are led away">
<figcaption>Left: 2 Kings 2:1-11, the chariot of fire, kept on the first try. Right: 25:1-21, the house of the LORD burnt.</figcaption>
</div>

### What went wrong this time

- The parting of the Jordan came out as a gravel spit, then as a corridor of glass cylinders. The version in the book is from above, with the water heaped up where Elisha walks.
- The first temple on fire was the Parthenon, with apartment blocks behind it.
- A cross stood on the wall of the temple court while Manasseh worshipped the stars, and his priests were holding sparklers.
- The word "AHEAVZ" carved over the dial of Ahaz, and Hezekiah drawn twice.
- The floating axe head was first a wooden block and then a machine part.

### 2 Kings by the numbers

| | 2 Kings | 1 Kings | 2 Samuel | 1 Samuel |
|---|---|---|---|---|
| Scenes | 36 | 37 | 37 | 41 |
| New portraits | 4 | 7 | 2 | 9 |
| Total attempts | 80 | 96 | 98 | 140 |
| Attempts per published image | 2.22 | 2.18 | 2.51 | 2.80 |
| Kept on the first try | 8 | 6 | 7 | 8 |
| GPU time | 34 min | 41 min | 51 min | 68 min |

## Part ten: 1 and 2 Chronicles

Chronicles tells Israel's story a second time, from Adam to the decree of Cyrus. It is two books on the site, 65
chapters and 89 scenes, and both have a narrated reader like the rest. You can read
[1 Chronicles](/1chronicles) and [2 Chronicles](/2chronicles).

<p class="cta"><a class="primary" href="/read/1chronicles">Read 1 Chronicles</a><a href="/read/2chronicles">Read 2 Chronicles</a><a href="/making-of?book=1%20Chronicles">See every attempt</a></p>

**Split across agents.** This time I asked Claude to run it as a workflow. Two agents planned the two books at
the same time. Images were made one job at a time, a few chapters per agent, because halo has one GPU. While
the second book was being drawn, another agent worked out the camera moves for the first book's reader on the
Mac, and the narration ran only after every image was final. Each agent that changed the repo worked in its own
copy, and one coordinator merged them. Before the images started I restarted halo to pick up an update from AMD,
and other coding agents were using the box for the first half hour.

**The genealogies.** The first nine chapters of 1 Chronicles are mostly names. Each one got a picture of a moment
those names mention: Nimrod, Jabez praying, warriors crying to God in battle, the singers before the tabernacle,
the porters opening the gates every morning.

**The cast.** David, Solomon, Hezekiah and Josiah keep their faces from Samuel and Kings. Two calls were mine: the
water from the well of Bethlehem uses young David, since it happened at Adullam before he was king, and Asaph, the
chief of the singers, gets his own portrait. Rehoboam's portrait first came out looking about 25, because it was
made from young Solomon; made from old Solomon instead, he looks his age. Asa and Jehoshaphat are new.

<div class="pair">
<img src="/images/full/halo_klein_ref_00931_.webp" alt="The angel with a drawn sword over Jerusalem as David and the elders in sackcloth fall on their faces">
<img src="/images/full/halo_klein_ref_00947_.webp" alt="Fire coming down from heaven onto the altar in Solomon's temple as all Israel bows to the ground">
<figcaption>Left: 1 Chronicles 21:14-17, the angel over Jerusalem. Right: 2 Chronicles 7:1-10, the fire came down from heaven.</figcaption>
</div>

**The hardest books yet.** About three and a half attempts for every published image, and three images kept on the
first try out of 89. Much of that is counting. The model drew six sons of Jesse, then five, then six again, never
seven, and three oxen pulling the ark's cart instead of two. Carrying the ark on the Levites' shoulders failed three
different ways, so 15:1 shows the ark set down with the Levites ready to lift it.

### What went wrong this time

- Men and pack animals merged: a man with a donkey's head for a torso, a camel with an ox's head, and two men and two donkeys drawn as centaurs.
- Temple music: valved trumpets, lyres played with bows like violins, and frame drums drawn as snare drums on stands.
- The golden lampstand came out as a European candelabra with wax candles.
- A gold cross pendant on Ahab's chest, and eyeglasses on the elders listening to the Levites teach.
- The hidden baby Joash came out with two heads, twice. The version in the book has one.

<div class="pair">
<img src="/images/full/halo_klein_00350_.webp" alt="A failed image: men and donkeys merged into centaur-like figures">
<img src="/images/full/halo_klein_ref_00894_.webp" alt="Bread, fig cakes and wine laid out on a mat as men rest by their donkeys and a camel">
<figcaption>1 Chronicles 12:23-40. Left: one of the tries. Right: the version in the book, the moment after they arrive.</figcaption>
</div>

### Chronicles by the numbers

| | 1 Chronicles | 2 Chronicles | 2 Kings | 1 Kings |
|---|---|---|---|---|
| Scenes | 43 | 46 | 36 | 37 |
| New portraits | 1 | 3 | 4 | 7 |
| Total attempts | 151 | 166 | 80 | 96 |
| Attempts per published image | 3.51 | 3.61 | 2.22 | 2.18 |
| Kept on the first try | 2 | 1 | 8 | 6 |
| GPU time | 62 min | 67 min | 34 min | 41 min |
| Narration | 138 min of audio | 161 min of audio | | |

## Part eleven: Ezra

Ezra is short: 10 chapters and 19 scenes, covering two returns from Babylon about eighty years apart. You can
[read it here](/ezra), or listen to it in the [reader](/read/ezra).

<p class="cta"><a class="primary" href="/read/ezra">Read Ezra</a><a href="/making-of?book=Ezra">See every attempt</a></p>

**The cast.** Three new portraits: Zerubbabel and Jeshua the high priest, who rebuild the altar and the temple,
and Ezra the scribe, who comes later with the law. Two of the three first came out with a buttoned shirt placket
under their robes, which one edit fixed each time.

**One planner this time.** For a single short book Claude wrote the plan directly instead of splitting it across agents. The rest ran
the same way as Chronicles: images one job at a time in two batches, then the camera paths and the narration side
by side once every image was final. The whole book took under an hour.

**Care with chapter 10.** Ezra ends with the men agreeing to put away their foreign wives and children. The picture
for it shows only the priests giving their hands in pledge and the ram offered for their trespass.

<div class="pair">
<img src="/images/full/halo_edit_00577_.webp" alt="The foundation of the second temple laid as young men shout and old men weep">
<img src="/images/full/halo_edit_00593_.webp" alt="Ezra sitting stunned with his robe torn at the evening sacrifice">
<figcaption>Left: Ezra 3:8-13, the noise of the shout of joy and the weeping. Right: 9:1-15, Ezra sat down astonied.</figcaption>
</div>

### What went wrong this time

- Hats. Berets, knitted beanies, pointed caps and a fedora, scene after scene.
- A clipboard, eyeglasses, and a security camera on the roof of the temple.
- An edit asked to remove a woman's glasses kept the glasses and added a new person.
- The camp at the river Ahava came out with modern tents and prayer rugs.
- The rain assembly in chapter 10 stood in front of a modern town with lamp posts and utility poles.

### Ezra by the numbers

| | Ezra | 2 Chronicles | 1 Chronicles |
|---|---|---|---|
| Scenes | 19 | 46 | 43 |
| New portraits | 3 | 3 | 1 |
| Total attempts | 68 | 166 | 151 |
| Attempts per published image | 3.58 | 3.61 | 3.51 |
| Kept on the first try | 2 | 1 | 2 |
| GPU time | 30 min | 67 min | 62 min |
| Narration | 48 min of audio | 161 min | 138 min |

## Part twelve: Nehemiah

Nehemiah is 13 chapters and 20 scenes: the king's cupbearer hears that Jerusalem's wall is broken down, gets leave
to go, and rebuilds it in fifty-two days. You can [read it here](/nehemiah), or listen in the [reader](/read/nehemiah).

<p class="cta"><a class="primary" href="/read/nehemiah">Read Nehemiah</a><a href="/making-of?book=Nehemiah">See every attempt</a></p>

**Hands off.** After I approved the plan and Nehemiah's portrait, Claude ran the rest on its own: images one job at
a time, then the camera paths and the narration side by side, and stopped for me to review. His portrait first came
out in a black knit beanie; an edit for a Persian court hat made a chef's hat, so he wears a wrapped linen headcloth.
Ezra keeps his face from the book of Ezra for the reading of the law in chapter 8.

**Care with chapter 13.** The book ends with Nehemiah contending with the men who married foreign wives, striking
some and pulling out their hair. The picture shows only Nehemiah at prayer: remember me, O my God, for good.

<div class="pair">
<img src="/images/full/halo_edit_00612_.webp" alt="Builders laying stones on the wall with swords girded at their sides">
<img src="/images/full/halo_klein_ref_01044_.webp" alt="Ezra reading the law at the water gate as the people lift their hands">
<figcaption>Left: Nehemiah 4:13-23, every one had his sword girded by his side, and so builded. Right: 8:1-12, Ezra reads the law.</figcaption>
</div>

### What went wrong this time

- Trousers under the robes again, in four scenes, and modern towns or castles behind the wall in five.
- The builders' swords took seven tries, and still have medieval crossguards.
- One edit erased Nehemiah from his own scene; another turned a street into sand dunes.
- The trumpets at the dedication of the wall came out as modern valved brass, so the picture leaves them out.

### Nehemiah by the numbers

| | Nehemiah | Ezra | 2 Chronicles |
|---|---|---|---|
| Scenes | 20 | 19 | 46 |
| New portraits | 1 | 3 | 3 |
| Total attempts | 65 | 68 | 166 |
| Attempts per published image | 3.25 | 3.58 | 3.61 |
| Kept on the first try | 3 | 2 | 1 |
| GPU time | 28 min | 30 min | 67 min |
| Narration | 68 min of audio | 48 min | 161 min |

## Try it

Everything is on [GitHub](https://github.com/btrzupek/halo-visual-bible): the MCP server, the ComfyUI workflows, the tunnel setup, the book viewer,
and the scripts that pulled these numbers. The [under the hood](/under-the-hood) page has the full hardware and
benchmark breakdown, and [making of](/making-of) has every single attempt with the exact prompt, including all
the wristwatches.

Next up will be integrating this into my agentic coding workflows.

IF you made it this far! You are amazing. Thanks for the read. I will keep you posted on my next test and workflow. This box is incredible, thank you @AMD!
